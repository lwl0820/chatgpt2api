from __future__ import annotations

import threading
from datetime import datetime
from typing import Any
from urllib.parse import urlparse, unquote
from uuid import uuid4

from services.image_task_service import image_task_service
from services.session_service import SESSION_KIND_IMAGE_SELECTION, session_service


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def _clean(value: object, default: str = "") -> str:
    return str(value or default).strip()


def _int(value: object, default: int, minimum: int = 1) -> int:
    try:
        normalized = int(value)
    except (TypeError, ValueError):
        normalized = default
    return max(minimum, normalized)


def _extract_managed_image_rel(url: str) -> str:
    value = _clean(url)
    if not value:
        return ""
    marker = "/images/"
    try:
        path = urlparse(value).path
        index = path.find(marker)
        if index >= 0:
            return unquote(path[index + len(marker):])
    except Exception:
        pass
    index = value.find(marker)
    if index >= 0:
        return unquote(value[index + len(marker):].split("?", 1)[0].split("#", 1)[0])
    return ""


def _task_to_candidate(candidate: dict[str, Any], task: dict[str, Any]) -> dict[str, Any]:
    status = task.get("status")
    if status == "success":
        data = task.get("data") if isinstance(task.get("data"), list) else []
        first = data[0] if data and isinstance(data[0], dict) else {}
        url = _clean(first.get("url"))
        b64_json = _clean(first.get("b64_json"))
        if not url and not b64_json:
            return {**candidate, "taskId": task.get("id"), "status": "error", "error": "未返回图片数据"}
        image_url = url or f"data:image/png;base64,{b64_json}"
        return {
            **candidate,
            "taskId": task.get("id"),
            "status": "ready",
            "url": image_url,
            "rel": _extract_managed_image_rel(image_url),
            "revised_prompt": first.get("revised_prompt"),
            "error": None,
        }
    if status == "error":
        return {**candidate, "taskId": task.get("id"), "status": "error", "error": task.get("error") or "生成失败"}
    return {**candidate, "taskId": task.get("id"), "status": "loading", "error": None}


def _count_trailing_errors(candidates: list[dict[str, Any]]) -> int:
    count = 0
    for candidate in reversed(candidates):
        if candidate.get("status") == "loading":
            break
        if candidate.get("status") != "error":
            break
        count += 1
    return count


def _active_count(candidates: list[dict[str, Any]]) -> int:
    return sum(1 for candidate in candidates if candidate.get("status") in {"loading", "ready"})


class ImageSelectionQueueService:
    def __init__(self, *, interval_seconds: float = 2.0):
        self.interval_seconds = interval_seconds
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._running_lock = threading.Lock()

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, name="image-selection-queue", daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1)

    def run_once(self) -> None:
        if not self._running_lock.acquire(blocking=False):
            return
        try:
            for record in session_service.list_all_sessions(SESSION_KIND_IMAGE_SELECTION):
                owner_id = _clean(record.get("owner_id"))
                item = record.get("item")
                if owner_id and isinstance(item, dict):
                    self._process_session(owner_id, item)
        finally:
            self._running_lock.release()

    def _run(self) -> None:
        while not self._stop_event.is_set():
            try:
                self.run_once()
            except Exception:
                pass
            self._stop_event.wait(self.interval_seconds)

    def _process_session(self, owner_id: str, session: dict[str, Any]) -> None:
        identity = {"id": owner_id, "name": owner_id, "role": "user"}
        session = self._sync_loading_candidates(identity, owner_id, session)
        if session.get("status") != "running":
            return
        candidates = [candidate for candidate in session.get("candidates", []) if isinstance(candidate, dict)]
        slots = max(0, _int(session.get("queueLimit"), 6) - _active_count(candidates))
        for _ in range(slots):
            session = self._submit_candidate(identity, owner_id, session)
            if session.get("status") != "running":
                break

    def _sync_loading_candidates(self, identity: dict[str, object], owner_id: str, session: dict[str, Any]) -> dict[str, Any]:
        candidates = [candidate for candidate in session.get("candidates", []) if isinstance(candidate, dict)]
        loading_ids = [_clean(candidate.get("taskId")) for candidate in candidates if candidate.get("status") == "loading" and _clean(candidate.get("taskId"))]
        if not loading_ids:
            return session
        task_list = image_task_service.list_tasks(identity, loading_ids)
        tasks = {task.get("id"): task for task in task_list.get("items", []) if isinstance(task, dict)}
        missing_ids = set(task_list.get("missing_ids", []))
        changed = False
        next_candidates = []
        for candidate in candidates:
            task_id = _clean(candidate.get("taskId"))
            next_candidate = candidate
            if candidate.get("status") == "loading" and task_id in missing_ids:
                next_candidate = {**candidate, "status": "error", "error": "任务已丢失"}
            elif candidate.get("status") == "loading" and task_id in tasks:
                next_candidate = _task_to_candidate(candidate, tasks[task_id])
            changed = changed or next_candidate != candidate
            next_candidates.append(next_candidate)
        if not changed:
            return session
        return self._save_candidates(owner_id, session, next_candidates)

    def _submit_candidate(self, identity: dict[str, object], owner_id: str, session: dict[str, Any]) -> dict[str, Any]:
        now = _now_iso()
        candidate_id = uuid4().hex
        prompt = _clean(session.get("prompt"))
        candidates = [candidate for candidate in session.get("candidates", []) if isinstance(candidate, dict)]
        loading_candidate = {"id": candidate_id, "taskId": candidate_id, "status": "loading", "prompt": prompt, "createdAt": now}
        session = self._save_candidates(owner_id, session, [*candidates, loading_candidate], now=now)
        try:
            task = image_task_service.submit_generation(
                identity,
                client_task_id=candidate_id,
                prompt=prompt,
                model="gpt-image-2",
                size=_clean(session.get("size")) or None,
                base_url="",
            )
            candidates = [candidate for candidate in session.get("candidates", []) if isinstance(candidate, dict)]
            next_candidates = [
                _task_to_candidate(candidate, task) if candidate.get("id") == candidate_id else candidate
                for candidate in candidates
            ]
            return self._save_candidates(owner_id, session, next_candidates)
        except Exception as exc:
            candidates = [candidate for candidate in session.get("candidates", []) if isinstance(candidate, dict)]
            next_candidates = [
                {**candidate, "status": "error", "error": str(exc) or "提交生成任务失败"}
                if candidate.get("id") == candidate_id else candidate
                for candidate in candidates
            ]
            return self._save_candidates(owner_id, session, next_candidates, last_error=str(exc) or "提交生成任务失败")

    def _save_candidates(
        self,
        owner_id: str,
        session: dict[str, Any],
        candidates: list[dict[str, Any]],
        *,
        now: str | None = None,
        last_error: str | None = None,
    ) -> dict[str, Any]:
        latest = session_service.get_session({"id": owner_id}, SESSION_KIND_IMAGE_SELECTION, _clean(session.get("id"))) or session
        candidates = self._merge_candidates(latest, candidates)
        failures = _count_trailing_errors(candidates)
        failure_limit = _int(latest.get("failureLimit"), 5)
        should_pause = failures >= failure_limit
        next_session = {
            **latest,
            "candidates": candidates,
            "consecutiveFailures": failures,
            "status": "paused" if should_pause else latest.get("status", "running"),
        }
        if should_pause:
            next_session["lastError"] = "连续生成失败，已暂停选图"
        elif last_error:
            next_session["lastError"] = last_error
        return session_service.save_owner_session(owner_id, SESSION_KIND_IMAGE_SELECTION, next_session)

    def _merge_candidates(self, latest_session: dict[str, Any], next_candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        latest_candidates = [candidate for candidate in latest_session.get("candidates", []) if isinstance(candidate, dict)]
        next_by_id = {_clean(candidate.get("id")): candidate for candidate in next_candidates if _clean(candidate.get("id"))}
        merged: list[dict[str, Any]] = []
        seen_ids: set[str] = set()
        for candidate in latest_candidates:
            candidate_id = _clean(candidate.get("id"))
            next_candidate = next_by_id.get(candidate_id)
            if not next_candidate:
                merged.append(candidate)
            elif candidate.get("status") in {"kept", "discarded"}:
                merged.append(candidate)
            else:
                merged.append(next_candidate)
            if candidate_id:
                seen_ids.add(candidate_id)
        for candidate in next_candidates:
            candidate_id = _clean(candidate.get("id"))
            if candidate_id and candidate_id not in seen_ids:
                merged.append(candidate)
        return merged


image_selection_queue_service = ImageSelectionQueueService()
