from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from services.session_service import SESSION_KIND_IMAGE_CONVERSATION, SessionService


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


if __name__ == "__main__":
    unittest.main()
