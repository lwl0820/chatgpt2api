from __future__ import annotations

import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class FrontendBackendSessionTests(unittest.TestCase):
    def test_image_session_stores_use_backend_apis_not_localforage(self):
        for relative_path in (
            "web/src/store/image-conversations.ts",
            "web/src/store/image-selection-sessions.ts",
        ):
            source = (ROOT / relative_path).read_text(encoding="utf-8")
            self.assertIn("fetchBackendSessions", source)
            self.assertIn("saveBackendSession", source)
            self.assertIn("deleteBackendSession", source)
            self.assertNotIn("localforage", source)
            self.assertNotIn("createInstance", source)
            self.assertNotIn("getItem", source)
            self.assertNotIn("setItem", source)

    def test_frontend_api_exposes_session_crud(self):
        source = (ROOT / "web/src/lib/api.ts").read_text(encoding="utf-8")

        self.assertIn("export async function fetchBackendSessions", source)
        self.assertIn("export async function fetchBackendSession", source)
        self.assertIn("export async function fetchBackendSessionCandidates", source)
        self.assertIn("export async function saveBackendSession", source)
        self.assertIn("export async function deleteBackendSession", source)
        self.assertIn("/api/sessions", source)

    def test_image_selection_store_uses_candidate_pagination_api(self):
        source = (ROOT / "web/src/store/image-selection-sessions.ts").read_text(encoding="utf-8")

        self.assertIn("fetchBackendSessionCandidates", source)
        self.assertIn("listImageSelectionSessionCandidates", source)


if __name__ == "__main__":
    unittest.main()
