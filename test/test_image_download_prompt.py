import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from fastapi.responses import FileResponse, Response


ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_CONFIG_FILE = ROOT_DIR / "config.json"


class ImageDownloadPromptTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._created_root_config = False
        if not ROOT_CONFIG_FILE.exists():
            ROOT_CONFIG_FILE.write_text(json.dumps({"auth-key": "test-auth"}), encoding="utf-8")
            cls._created_root_config = True

        from services import config as config_module
        from services import image_service as image_module
        from services import session_service as session_module

        cls.config_module = config_module
        cls.image_module = image_module
        cls.session_module = session_module

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._created_root_config and ROOT_CONFIG_FILE.exists():
            ROOT_CONFIG_FILE.unlink()

    def _with_temp_services(self, data: dict[str, object] | None = None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        base_dir = Path(temp_dir.name)
        config_path = base_dir / "config.json"
        config_path.write_text(json.dumps({"auth-key": "test-auth", **(data or {})}), encoding="utf-8")

        old_data_dir = self.config_module.DATA_DIR
        old_config = self.config_module.config
        old_image_config = self.image_module.config
        old_session_service = self.session_module.session_service
        self.config_module.DATA_DIR = base_dir / "data"
        store = self.config_module.ConfigStore(config_path)
        self.config_module.config = store
        self.image_module.config = store
        self.session_module.session_service = self.session_module.SessionService(store.images_dir.parent / "sessions.json")
        self.addCleanup(lambda: setattr(self.config_module, "DATA_DIR", old_data_dir))
        self.addCleanup(lambda: setattr(self.config_module, "config", old_config))
        self.addCleanup(lambda: setattr(self.image_module, "config", old_image_config))
        self.addCleanup(lambda: setattr(self.session_module, "session_service", old_session_service))
        return store

    def _write_image(self, store, rel: str, data: bytes = b"image") -> None:
        path = store.images_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)

    def _save_image_conversation(self, rel: str, prompt: str) -> None:
        self.session_module.session_service.save_session(
            {"id": "alice"},
            self.session_module.SESSION_KIND_IMAGE_CONVERSATION,
            {
                "id": "conversation-1",
                "turns": [
                    {
                        "id": "turn-1",
                        "prompt": prompt,
                        "images": [{"id": "image-1", "status": "success", "url": f"/images/{rel}"}],
                    },
                ],
            },
        )

    def _save_image_selection(self, rel: str, session_prompt: str, candidate_prompt: str | None = None) -> None:
        candidate = {"id": "candidate-1", "status": "kept", "url": f"/images/{rel}"}
        if candidate_prompt is not None:
            candidate["prompt"] = candidate_prompt
        self.session_module.session_service.save_session(
            {"id": "alice"},
            self.session_module.SESSION_KIND_IMAGE_SELECTION,
            {
                "id": "selection-1",
                "prompt": session_prompt,
                "candidates": [candidate],
            },
        )

    def test_single_download_appends_prompt_when_enabled(self) -> None:
        store = self._with_temp_services({"image_download_append_prompt": True})
        rel = "2026/01/01/cat.png"
        self._write_image(store, rel)
        self._save_image_conversation(rel, "orange cat")

        response = self.image_module.get_image_download_response(rel)

        self.assertIsInstance(response, Response)
        self.assertTrue(response.body.endswith(b"orange cat\n-- end chatgpt2api prompt --\n"))

    def test_single_download_uses_file_response_when_disabled(self) -> None:
        store = self._with_temp_services({"image_download_append_prompt": False})
        rel = "2026/01/01/cat.png"
        self._write_image(store, rel)
        self._save_image_conversation(rel, "orange cat")

        response = self.image_module.get_image_download_response(rel)

        self.assertIsInstance(response, FileResponse)

    def test_zip_download_appends_prompt_to_matching_entry(self) -> None:
        store = self._with_temp_services({"image_download_append_prompt": True})
        rel = "2026/01/01/cat.png"
        self._write_image(store, rel)
        self._save_image_conversation(rel, "orange cat")

        buf = self.image_module.download_images_zip([rel])

        with zipfile.ZipFile(buf) as zf:
            self.assertTrue(zf.read("cat.png").endswith(b"orange cat\n-- end chatgpt2api prompt --\n"))

    def test_zip_download_keeps_unmatched_entry_unchanged(self) -> None:
        store = self._with_temp_services({"image_download_append_prompt": True})
        rel = "2026/01/01/cat.png"
        self._write_image(store, rel)

        buf = self.image_module.download_images_zip([rel])

        with zipfile.ZipFile(buf) as zf:
            self.assertEqual(zf.read("cat.png"), b"image")

    def test_single_download_prefers_selection_candidate_prompt(self) -> None:
        store = self._with_temp_services({"image_download_append_prompt": True})
        rel = "2026/01/01/cat.png"
        self._write_image(store, rel)
        self._save_image_selection(rel, "dog", "cat")

        response = self.image_module.get_image_download_response(rel)

        self.assertIsInstance(response, Response)
        self.assertTrue(response.body.endswith(b"cat\n-- end chatgpt2api prompt --\n"))
        self.assertNotIn(b"dog\n-- end chatgpt2api prompt --\n", response.body)

    def test_single_download_uses_selection_candidate_prompt_without_session_prompt(self) -> None:
        store = self._with_temp_services({"image_download_append_prompt": True})
        rel = "2026/01/01/cat.png"
        self._write_image(store, rel)
        self._save_image_selection(rel, "", "cat")

        response = self.image_module.get_image_download_response(rel)

        self.assertIsInstance(response, Response)
        self.assertTrue(response.body.endswith(b"cat\n-- end chatgpt2api prompt --\n"))

    def test_zip_download_falls_back_to_selection_session_prompt(self) -> None:
        store = self._with_temp_services({"image_download_append_prompt": True})
        rel = "2026/01/01/cat.png"
        self._write_image(store, rel)
        self._save_image_selection(rel, "dog")

        buf = self.image_module.download_images_zip([rel])

        with zipfile.ZipFile(buf) as zf:
            self.assertTrue(zf.read("cat.png").endswith(b"dog\n-- end chatgpt2api prompt --\n"))


if __name__ == "__main__":
    unittest.main()
