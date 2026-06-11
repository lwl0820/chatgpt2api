from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import FastAPI
from fastapi.testclient import TestClient

import api.sessions as sessions_module
from services.session_service import SESSION_KIND_IMAGE_CONVERSATION, SESSION_KIND_IMAGE_SELECTION, SessionService


def fake_identity(authorization: str | None):
    token = str(authorization or "").removeprefix("Bearer ").strip()
    if token == "alice":
        return {"id": "alice", "role": "user"}
    if token == "bob":
        return {"id": "bob", "role": "user"}
    from fastapi import HTTPException

    raise HTTPException(status_code=401, detail={"error": "unauthorized"})


class SessionsApiTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.service = SessionService(Path(self.temp_dir.name) / "sessions.json")
        self.service_patcher = mock.patch.object(sessions_module, "session_service", self.service)
        self.identity_patcher = mock.patch.object(sessions_module, "require_identity", fake_identity)
        self.service_patcher.start()
        self.identity_patcher.start()
        self.addCleanup(self.service_patcher.stop)
        self.addCleanup(self.identity_patcher.stop)
        app = FastAPI()
        app.include_router(sessions_module.create_router())
        self.client = TestClient(app)

    def test_create_list_get_and_delete_session(self):
        response = self.client.post(
            "/api/sessions",
            headers={"Authorization": "Bearer alice"},
            json={"kind": SESSION_KIND_IMAGE_CONVERSATION, "item": {"title": "Cat", "turns": []}},
        )

        self.assertEqual(response.status_code, 200, response.text)
        item = response.json()["item"]
        session_id = item["id"]
        self.assertEqual(item["title"], "Cat")

        response = self.client.get(
            f"/api/sessions?kind={SESSION_KIND_IMAGE_CONVERSATION}",
            headers={"Authorization": "Bearer alice"},
        )
        self.assertEqual([session["id"] for session in response.json()["items"]], [session_id])

        response = self.client.get(
            f"/api/sessions/{SESSION_KIND_IMAGE_CONVERSATION}/{session_id}",
            headers={"Authorization": "Bearer alice"},
        )
        self.assertEqual(response.json()["item"]["id"], session_id)

        response = self.client.delete(
            f"/api/sessions/{SESSION_KIND_IMAGE_CONVERSATION}/{session_id}",
            headers={"Authorization": "Bearer alice"},
        )
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json(), {"ok": True})

    def test_other_owner_cannot_read_session(self):
        response = self.client.post(
            "/api/sessions",
            headers={"Authorization": "Bearer alice"},
            json={"kind": SESSION_KIND_IMAGE_CONVERSATION, "item": {"id": "owned", "title": "Secret"}},
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.get(
            f"/api/sessions/{SESSION_KIND_IMAGE_CONVERSATION}/owned",
            headers={"Authorization": "Bearer bob"},
        )
        self.assertEqual(response.status_code, 404, response.text)

    def test_unauthenticated_access_is_rejected(self):
        response = self.client.get(f"/api/sessions?kind={SESSION_KIND_IMAGE_CONVERSATION}")

        self.assertEqual(response.status_code, 401, response.text)

    def test_image_selection_session_list_is_lightweight(self):
        response = self.client.post(
            "/api/sessions",
            headers={"Authorization": "Bearer alice"},
            json={
                "kind": SESSION_KIND_IMAGE_SELECTION,
                "item": {
                    "id": "selection-1",
                    "title": "Selection",
                    "candidates": [
                        {"id": "candidate-1", "status": "ready", "createdAt": "2026-01-01T00:00:00"},
                        {"id": "candidate-2", "status": "loading", "createdAt": "2026-01-01T00:01:00"},
                    ],
                },
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.get(
            f"/api/sessions?kind={SESSION_KIND_IMAGE_SELECTION}",
            headers={"Authorization": "Bearer alice"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        item = response.json()["items"][0]
        self.assertEqual(item["id"], "selection-1")
        self.assertEqual(item["candidateCount"], 2)
        self.assertNotIn("candidates", item)

    def test_get_session_candidates_is_paginated(self):
        response = self.client.post(
            "/api/sessions",
            headers={"Authorization": "Bearer alice"},
            json={
                "kind": SESSION_KIND_IMAGE_SELECTION,
                "item": {
                    "id": "selection-1",
                    "title": "Selection",
                    "candidates": [
                        {"id": "candidate-1", "status": "ready", "createdAt": "2026-01-01T00:00:00"},
                        {"id": "candidate-2", "status": "ready", "createdAt": "2026-01-01T00:01:00"},
                        {"id": "candidate-3", "status": "ready", "createdAt": "2026-01-01T00:02:00"},
                    ],
                },
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.get(
            f"/api/sessions/{SESSION_KIND_IMAGE_SELECTION}/selection-1/candidates?offset=1&limit=1",
            headers={"Authorization": "Bearer alice"},
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual([item["id"] for item in response.json()["items"]], ["candidate-2"])
        self.assertEqual(response.json()["total"], 3)
        self.assertEqual(response.json()["offset"], 1)
        self.assertEqual(response.json()["limit"], 1)
        self.assertTrue(response.json()["has_more"])

    def test_other_owner_cannot_read_session_candidates(self):
        response = self.client.post(
            "/api/sessions",
            headers={"Authorization": "Bearer alice"},
            json={
                "kind": SESSION_KIND_IMAGE_SELECTION,
                "item": {"id": "selection-1", "candidates": [{"id": "candidate-1"}]},
            },
        )
        self.assertEqual(response.status_code, 200, response.text)

        response = self.client.get(
            f"/api/sessions/{SESSION_KIND_IMAGE_SELECTION}/selection-1/candidates",
            headers={"Authorization": "Bearer bob"},
        )

        self.assertEqual(response.status_code, 404, response.text)


if __name__ == "__main__":
    unittest.main()
