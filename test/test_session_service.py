from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.session_service import SESSION_KIND_IMAGE_CONVERSATION, SESSION_KIND_IMAGE_SELECTION, SessionService


class SessionServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.service = SessionService(Path(self.temp_dir.name) / "sessions.json")
        self.alice = {"id": "alice", "role": "user"}
        self.bob = {"id": "bob", "role": "user"}

    def test_save_list_get_and_delete_session(self):
        saved = self.service.save_session(
            self.alice,
            SESSION_KIND_IMAGE_CONVERSATION,
            {"title": "Cat", "turns": [], "createdAt": "2026-01-01T00:00:00", "updatedAt": "2026-01-01T00:00:00"},
        )

        self.assertTrue(saved["id"])
        self.assertEqual(saved["kind"], SESSION_KIND_IMAGE_CONVERSATION)
        listed = self.service.list_sessions(self.alice, SESSION_KIND_IMAGE_CONVERSATION)["items"]
        self.assertEqual([item["id"] for item in listed], [saved["id"]])
        self.assertEqual(self.service.get_session(self.alice, SESSION_KIND_IMAGE_CONVERSATION, saved["id"])["title"], "Cat")

        self.assertTrue(self.service.delete_session(self.alice, SESSION_KIND_IMAGE_CONVERSATION, saved["id"]))
        self.assertEqual(self.service.list_sessions(self.alice, SESSION_KIND_IMAGE_CONVERSATION)["items"], [])

    def test_sessions_are_owner_scoped(self):
        saved = self.service.save_session(
            self.alice,
            SESSION_KIND_IMAGE_CONVERSATION,
            {"id": "shared-id", "title": "Alice", "turns": []},
        )

        self.assertEqual(saved["id"], "shared-id")
        self.assertIsNone(self.service.get_session(self.bob, SESSION_KIND_IMAGE_CONVERSATION, "shared-id"))
        self.assertFalse(self.service.delete_session(self.bob, SESSION_KIND_IMAGE_CONVERSATION, "shared-id"))
        self.assertIsNotNone(self.service.get_session(self.alice, SESSION_KIND_IMAGE_CONVERSATION, "shared-id"))

    def test_invalid_kind_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.save_session(self.alice, "invalid", {"title": "Bad"})

    def test_save_and_delete_publish_session_events(self):
        subscriber = self.service.subscribe("alice", SESSION_KIND_IMAGE_CONVERSATION, "session-1")

        self.service.save_session(
            self.alice,
            SESSION_KIND_IMAGE_CONVERSATION,
            {"id": "session-1", "title": "Cat", "turns": []},
        )
        saved_event = subscriber.get_nowait()
        self.assertEqual(saved_event["event"], "session")
        self.assertEqual(saved_event["item"]["id"], "session-1")

        self.service.delete_session(self.alice, SESSION_KIND_IMAGE_CONVERSATION, "session-1")
        deleted_event = subscriber.get_nowait()
        self.assertEqual(deleted_event, {"event": "deleted", "id": "session-1"})

        self.service.unsubscribe("alice", SESSION_KIND_IMAGE_CONVERSATION, "session-1", subscriber)

    def test_list_sessions_sorts_by_parsed_updated_at(self):
        self.service.save_session(
            self.alice,
            SESSION_KIND_IMAGE_SELECTION,
            {
                "id": "older",
                "title": "Older",
                "updatedAt": "2026-01-01T01:00:00+01:00",
                "createdAt": "2026-01-01T01:00:00+01:00",
            },
        )
        self.service.save_session(
            self.alice,
            SESSION_KIND_IMAGE_SELECTION,
            {
                "id": "newer",
                "title": "Newer",
                "updatedAt": "2026-01-01T00:30:00Z",
                "createdAt": "2026-01-01T00:30:00Z",
            },
        )

        listed = self.service.list_sessions(self.alice, SESSION_KIND_IMAGE_SELECTION)["items"]

        self.assertEqual([item["id"] for item in listed], ["newer", "older"])

    def test_existing_session_save_publishes_delta(self):
        self.service.save_session(
            self.alice,
            SESSION_KIND_IMAGE_SELECTION,
            {
                "id": "session-1",
                "title": "Cat",
                "prompt": "cat",
                "candidates": [{"id": "candidate-1", "status": "loading", "createdAt": "now"}],
                "updatedAt": "2026-01-01T00:00:00",
            },
        )
        subscriber = self.service.subscribe("alice", SESSION_KIND_IMAGE_SELECTION, "session-1")

        self.service.save_session(
            self.alice,
            SESSION_KIND_IMAGE_SELECTION,
            {
                "id": "session-1",
                "title": "Cat",
                "prompt": "cat",
                "candidates": [{"id": "candidate-1", "status": "ready", "url": "/images/cat.png", "createdAt": "now"}],
                "updatedAt": "2026-01-01T00:00:01",
            },
        )

        event = subscriber.get_nowait()
        self.assertEqual(event["event"], "session-delta")
        self.assertEqual(event["delta"]["id"], "session-1")
        self.assertEqual(event["delta"]["updatedAt"], "2026-01-01T00:00:01")
        self.assertEqual(event["delta"]["candidates"]["upsert"][0]["id"], "candidate-1")
        self.assertNotIn("title", event["delta"].get("fields", {}))


if __name__ == "__main__":
    unittest.main()
