from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

import services.image_selection_queue_service as queue_module
from services.image_selection_queue_service import ImageSelectionQueueService
from services.session_service import SESSION_KIND_IMAGE_SELECTION, SessionService


class FakeImageTaskService:
    def __init__(self):
        self.submitted = []
        self.tasks = {}

    def submit_generation(self, identity, **kwargs):
        self.submitted.append((identity, kwargs))
        task = {
            "id": kwargs["client_task_id"],
            "status": "running",
            "mode": "generate",
            "created_at": "2026-01-01 00:00:00",
            "updated_at": "2026-01-01 00:00:00",
        }
        self.tasks[kwargs["client_task_id"]] = task
        return task

    def list_tasks(self, _identity, ids):
        return {
            "items": [self.tasks[task_id] for task_id in ids if task_id in self.tasks],
            "missing_ids": [task_id for task_id in ids if task_id not in self.tasks],
        }


class ImageSelectionQueueServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.session_service = SessionService(Path(self.temp_dir.name) / "sessions.json")
        self.task_service = FakeImageTaskService()
        self.session_patcher = mock.patch.object(queue_module, "session_service", self.session_service)
        self.task_patcher = mock.patch.object(queue_module, "image_task_service", self.task_service)
        self.session_patcher.start()
        self.task_patcher.start()
        self.addCleanup(self.session_patcher.stop)
        self.addCleanup(self.task_patcher.stop)
        self.service = ImageSelectionQueueService(interval_seconds=0.01)

    def save_selection(self, item):
        return self.session_service.save_owner_session("alice", SESSION_KIND_IMAGE_SELECTION, item)

    def get_selection(self, session_id="session-1"):
        return self.session_service.get_session({"id": "alice"}, SESSION_KIND_IMAGE_SELECTION, session_id)

    def test_fills_running_session_queue(self):
        self.save_selection({
            "id": "session-1",
            "status": "running",
            "prompt": "cat",
            "size": "1:1",
            "queueLimit": 2,
            "failureLimit": 5,
            "candidates": [],
        })

        self.service.run_once()

        session = self.get_selection()
        self.assertEqual(len(session["candidates"]), 2)
        self.assertEqual(len(self.task_service.submitted), 2)
        self.assertTrue(all(candidate["status"] == "loading" for candidate in session["candidates"]))

    def test_syncs_completed_task_result(self):
        self.save_selection({
            "id": "session-1",
            "status": "running",
            "prompt": "cat",
            "queueLimit": 1,
            "failureLimit": 5,
            "candidates": [{"id": "candidate-1", "taskId": "task-1", "status": "loading", "createdAt": "now"}],
        })
        self.task_service.tasks["task-1"] = {
            "id": "task-1",
            "status": "success",
            "data": [{"url": "/images/2026/01/01/cat.png", "revised_prompt": "cat"}],
        }

        self.service.run_once()

        candidate = self.get_selection()["candidates"][0]
        self.assertEqual(candidate["status"], "ready")
        self.assertEqual(candidate["url"], "/images/2026/01/01/cat.png")
        self.assertEqual(candidate["rel"], "2026/01/01/cat.png")

    def test_pauses_after_failure_limit(self):
        self.save_selection({
            "id": "session-1",
            "status": "running",
            "prompt": "cat",
            "queueLimit": 1,
            "failureLimit": 1,
            "candidates": [{"id": "candidate-1", "taskId": "task-1", "status": "loading", "createdAt": "now"}],
        })
        self.task_service.tasks["task-1"] = {"id": "task-1", "status": "error", "error": "boom"}

        self.service.run_once()

        session = self.get_selection()
        self.assertEqual(session["status"], "paused")
        self.assertEqual(session["lastError"], "连续生成失败，已暂停选图")

    def test_syncs_loading_candidates_after_session_paused(self):
        self.save_selection({
            "id": "session-1",
            "status": "paused",
            "prompt": "cat",
            "queueLimit": 1,
            "failureLimit": 5,
            "candidates": [{"id": "candidate-1", "taskId": "task-1", "status": "loading", "createdAt": "now"}],
        })
        self.task_service.tasks["task-1"] = {"id": "task-1", "status": "error", "error": "boom"}

        self.service.run_once()

        session = self.get_selection()
        self.assertEqual(session["status"], "paused")
        self.assertEqual(session["candidates"][0]["status"], "error")
        self.assertEqual(session["candidates"][0]["error"], "boom")
        self.assertEqual(len(self.task_service.submitted), 0)

    def test_worker_does_not_overwrite_user_decisions_from_stale_snapshot(self):
        stale = self.save_selection({
            "id": "session-1",
            "status": "running",
            "prompt": "cat",
            "queueLimit": 2,
            "failureLimit": 5,
            "candidates": [
                {"id": "candidate-1", "taskId": "task-1", "status": "ready", "url": "/images/old.png", "createdAt": "now"},
                {"id": "candidate-2", "taskId": "task-2", "status": "loading", "createdAt": "now"},
            ],
        })
        self.save_selection({
            **stale,
            "candidates": [
                {"id": "candidate-1", "taskId": "task-1", "status": "discarded", "url": "/images/old.png", "createdAt": "now"},
                {"id": "candidate-2", "taskId": "task-2", "status": "loading", "createdAt": "now"},
            ],
        })

        updated = self.service._save_candidates("alice", stale, [
            {"id": "candidate-1", "taskId": "task-1", "status": "ready", "url": "/images/old.png", "createdAt": "now"},
            {"id": "candidate-2", "taskId": "task-2", "status": "error", "error": "boom", "createdAt": "now"},
        ])

        self.assertEqual(updated["candidates"][0]["status"], "discarded")
        self.assertEqual(updated["candidates"][1]["status"], "error")


if __name__ == "__main__":
    unittest.main()
