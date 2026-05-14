from __future__ import annotations

import json
import queue
import threading
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from services.config import DATA_DIR

SESSION_KIND_IMAGE_CONVERSATION = "image-conversation"
SESSION_KIND_IMAGE_SELECTION = "image-selection-session"
SESSION_KINDS = {SESSION_KIND_IMAGE_CONVERSATION, SESSION_KIND_IMAGE_SELECTION}


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="milliseconds")


def _clean(value: object, default: str = "") -> str:
    return str(value or default).strip()


def _owner_id(identity: dict[str, object]) -> str:
    return _clean(identity.get("id")) or "anonymous"


def _timestamp(value: object) -> float:
    if not isinstance(value, str) or not value.strip():
        return 0.0
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp()
    except Exception:
        return 0.0


def _session_key(owner_id: str, kind: str, session_id: str) -> str:
    return f"{owner_id}:{kind}:{session_id}"


def session_timestamp(value: object) -> float:
    return _timestamp(value)


class SessionService:
    def __init__(self, path: Path):
        self.path = path
        self._lock = threading.RLock()
        self._sessions: dict[str, dict[str, Any]] = {}
        self._subscribers: dict[str, list[queue.Queue[dict[str, Any]]]] = {}
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._lock:
            self._sessions = self._load_locked()

    def list_sessions(self, identity: dict[str, object], kind: str | None = None) -> dict[str, Any]:
        owner = _owner_id(identity)
        normalized_kind = self._normalize_kind(kind) if kind else None
        with self._lock:
            items = [
                self._public_session(session)
                for session in self._sessions.values()
                if session.get("owner_id") == owner and (normalized_kind is None or session.get("kind") == normalized_kind)
            ]
        items.sort(key=lambda item: str(item.get("updatedAt") or ""), reverse=True)
        return {"items": items}

    def get_session(self, identity: dict[str, object], kind: str, session_id: str) -> dict[str, Any] | None:
        owner = _owner_id(identity)
        normalized_kind = self._normalize_kind(kind)
        normalized_id = self._normalize_id(session_id, allow_generate=False)
        with self._lock:
            session = self._sessions.get(_session_key(owner, normalized_kind, normalized_id))
            return self._public_session(session) if session is not None else None

    def save_session(self, identity: dict[str, object], kind: str, item: dict[str, Any]) -> dict[str, Any]:
        owner = _owner_id(identity)
        session = self._normalize_session(owner, kind, item)
        with self._lock:
            self._sessions[_session_key(owner, session["kind"], session["id"])] = session
            self._save_locked()
            item = self._public_session(session)
        self._publish(owner, session["kind"], session["id"], {"event": "session", "item": item})
        return item

    def delete_session(self, identity: dict[str, object], kind: str, session_id: str) -> bool:
        owner = _owner_id(identity)
        normalized_kind = self._normalize_kind(kind)
        normalized_id = self._normalize_id(session_id, allow_generate=False)
        with self._lock:
            removed = self._sessions.pop(_session_key(owner, normalized_kind, normalized_id), None) is not None
            if removed:
                self._save_locked()
        if removed:
            self._publish(owner, normalized_kind, normalized_id, {"event": "deleted", "id": normalized_id})
        return removed

    def list_all_sessions(self, kind: str) -> list[dict[str, Any]]:
        normalized_kind = self._normalize_kind(kind)
        with self._lock:
            return [
                {"owner_id": session.get("owner_id"), "item": self._public_session(session)}
                for session in self._sessions.values()
                if session.get("kind") == normalized_kind
            ]

    def save_owner_session(self, owner_id: str, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        owner = _clean(owner_id) or "anonymous"
        session = self._normalize_session(owner, kind, item)
        with self._lock:
            self._sessions[_session_key(owner, session["kind"], session["id"])] = session
            self._save_locked()
            item = self._public_session(session)
        self._publish(owner, session["kind"], session["id"], {"event": "session", "item": item})
        return item

    def subscribe(self, owner_id: str, kind: str, session_id: str) -> queue.Queue[dict[str, Any]]:
        owner = _clean(owner_id) or "anonymous"
        normalized_kind = self._normalize_kind(kind)
        normalized_id = self._normalize_id(session_id, allow_generate=False)
        subscriber: queue.Queue[dict[str, Any]] = queue.Queue(maxsize=20)
        key = _session_key(owner, normalized_kind, normalized_id)
        with self._lock:
            self._subscribers.setdefault(key, []).append(subscriber)
        return subscriber

    def unsubscribe(self, owner_id: str, kind: str, session_id: str, subscriber: queue.Queue[dict[str, Any]]) -> None:
        owner = _clean(owner_id) or "anonymous"
        normalized_kind = self._normalize_kind(kind)
        normalized_id = self._normalize_id(session_id, allow_generate=False)
        key = _session_key(owner, normalized_kind, normalized_id)
        with self._lock:
            subscribers = self._subscribers.get(key)
            if not subscribers:
                return
            self._subscribers[key] = [item for item in subscribers if item is not subscriber]
            if not self._subscribers[key]:
                self._subscribers.pop(key, None)

    def _publish(self, owner_id: str, kind: str, session_id: str, event: dict[str, Any]) -> None:
        key = _session_key(owner_id, kind, session_id)
        with self._lock:
            subscribers = list(self._subscribers.get(key, []))
        for subscriber in subscribers:
            try:
                if subscriber.full():
                    subscriber.get_nowait()
                subscriber.put_nowait(dict(event))
            except Exception:
                pass

    def _normalize_session(self, owner: str, kind: str, item: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise ValueError("session item must be an object")
        normalized_kind = self._normalize_kind(kind or item.get("kind"))
        now = _now_iso()
        session_id = self._normalize_id(item.get("id"), allow_generate=True)
        existing = self._sessions.get(_session_key(owner, normalized_kind, session_id))
        created_at = _clean(item.get("createdAt")) or _clean(existing.get("created_at") if existing else "") or now
        updated_at = _clean(item.get("updatedAt")) or now
        payload = dict(item)
        payload["id"] = session_id
        payload["createdAt"] = created_at
        payload["updatedAt"] = updated_at
        return {
            "id": session_id,
            "owner_id": owner,
            "kind": normalized_kind,
            "created_at": created_at,
            "updated_at": updated_at,
            "payload": payload,
        }

    def _normalize_kind(self, kind: object) -> str:
        normalized = _clean(kind)
        if normalized not in SESSION_KINDS:
            raise ValueError("invalid session kind")
        return normalized

    def _normalize_id(self, value: object, *, allow_generate: bool) -> str:
        session_id = _clean(value)
        if session_id:
            return session_id
        if allow_generate:
            return uuid.uuid4().hex
        raise ValueError("session id is required")

    def _public_session(self, session: dict[str, Any]) -> dict[str, Any]:
        payload = dict(session.get("payload") if isinstance(session.get("payload"), dict) else {})
        payload["id"] = session.get("id")
        payload["kind"] = session.get("kind")
        payload["createdAt"] = payload.get("createdAt") or session.get("created_at")
        payload["updatedAt"] = payload.get("updatedAt") or session.get("updated_at")
        return payload

    def _load_locked(self) -> dict[str, dict[str, Any]]:
        if not self.path.exists():
            return {}
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(data, dict):
            return {}
        items = data.get("items")
        if not isinstance(items, list):
            return {}
        sessions: dict[str, dict[str, Any]] = {}
        for item in items:
            if not isinstance(item, dict):
                continue
            owner = _clean(item.get("owner_id"))
            kind = _clean(item.get("kind"))
            session_id = _clean(item.get("id"))
            if not owner or kind not in SESSION_KINDS or not session_id:
                continue
            sessions[_session_key(owner, kind, session_id)] = item
        return sessions

    def _save_locked(self) -> None:
        items = sorted(
            self._sessions.values(),
            key=lambda item: (_clean(item.get("owner_id")), _clean(item.get("kind")), -_timestamp(item.get("updated_at"))),
        )
        self.path.write_text(json.dumps({"items": items}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


session_service = SessionService(DATA_DIR / "sessions.json")
