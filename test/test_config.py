import json
import os
import tempfile
import time
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
ROOT_CONFIG_FILE = ROOT_DIR / "config.json"


class ConfigLoadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._created_root_config = False
        if not ROOT_CONFIG_FILE.exists():
            ROOT_CONFIG_FILE.write_text(json.dumps({"auth-key": "test-auth"}), encoding="utf-8")
            cls._created_root_config = True

        from services import config as config_module

        cls.config_module = config_module

    @classmethod
    def tearDownClass(cls) -> None:
        if cls._created_root_config and ROOT_CONFIG_FILE.exists():
            ROOT_CONFIG_FILE.unlink()

    def test_load_settings_ignores_directory_config_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            base_dir = Path(tmp_dir)
            data_dir = base_dir / "data"
            config_dir = base_dir / "config.json"
            os_auth_key = "env-auth"

            config_dir.mkdir()

            module = self.config_module
            old_base_dir = module.BASE_DIR
            old_data_dir = module.DATA_DIR
            old_config_file = module.CONFIG_FILE
            old_env_auth_key = module.os.environ.get("CHATGPT2API_AUTH_KEY")
            try:
                module.BASE_DIR = base_dir
                module.DATA_DIR = data_dir
                module.CONFIG_FILE = config_dir
                module.os.environ["CHATGPT2API_AUTH_KEY"] = os_auth_key

                settings = module._load_settings()

                self.assertEqual(settings.auth_key, os_auth_key)
                self.assertEqual(settings.refresh_account_interval_minute, 5)
            finally:
                module.BASE_DIR = old_base_dir
                module.DATA_DIR = old_data_dir
                module.CONFIG_FILE = old_config_file
                if old_env_auth_key is None:
                    module.os.environ.pop("CHATGPT2API_AUTH_KEY", None)
                else:
                    module.os.environ["CHATGPT2API_AUTH_KEY"] = old_env_auth_key

    def _with_temp_config(self, data: dict[str, object] | None = None):
        temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(temp_dir.cleanup)
        base_dir = Path(temp_dir.name)
        config_path = base_dir / "config.json"
        config_path.write_text(json.dumps({"auth-key": "test-auth", **(data or {})}), encoding="utf-8")

        module = self.config_module
        old_data_dir = module.DATA_DIR
        module.DATA_DIR = base_dir / "data"
        self.addCleanup(lambda: setattr(module, "DATA_DIR", old_data_dir))

        return module.ConfigStore(config_path)

    def _write_old_image(self, store, rel: str) -> Path:
        path = store.images_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")
        old_time = time.time() - 3 * 86400
        os.utime(path, (old_time, old_time))
        return path

    def test_cleanup_old_images_deletes_old_images_by_default(self) -> None:
        store = self._with_temp_config({"image_retention_days": 1})
        old_image = self._write_old_image(store, "2026/01/01/old.png")

        removed = store.cleanup_old_images()

        self.assertEqual(removed, 1)
        self.assertFalse(old_image.exists())

    def test_cleanup_old_images_preserves_kept_selection_images_when_enabled(self) -> None:
        store = self._with_temp_config({"image_retention_days": 1, "image_cleanup_skip_kept": True})
        kept_image = self._write_old_image(store, "2026/01/01/kept.png")
        other_image = self._write_old_image(store, "2026/01/01/other.png")

        from services import session_service as session_module

        old_session_service = session_module.session_service
        session_module.session_service = session_module.SessionService(store.images_dir.parent / "sessions.json")
        self.addCleanup(lambda: setattr(session_module, "session_service", old_session_service))
        session_module.session_service.save_session(
            {"id": "alice"},
            session_module.SESSION_KIND_IMAGE_SELECTION,
            {
                "id": "selection-1",
                "candidates": [
                    {"id": "candidate-1", "status": "kept", "rel": "2026/01/01/kept.png"},
                ],
            },
        )

        removed = store.cleanup_old_images()

        self.assertEqual(removed, 1)
        self.assertTrue(kept_image.exists())
        self.assertFalse(other_image.exists())

    def test_cleanup_old_images_does_not_protect_non_kept_or_invalid_candidates(self) -> None:
        store = self._with_temp_config({"image_retention_days": 1, "image_cleanup_skip_kept": True})
        discarded_image = self._write_old_image(store, "2026/01/01/discarded.png")
        ready_image = self._write_old_image(store, "2026/01/01/ready.png")
        unsafe_image = self._write_old_image(store, "2026/01/01/unsafe.png")
        missing_path_image = self._write_old_image(store, "2026/01/01/missing-path.png")

        from services import session_service as session_module

        old_session_service = session_module.session_service
        session_module.session_service = session_module.SessionService(store.images_dir.parent / "sessions.json")
        self.addCleanup(lambda: setattr(session_module, "session_service", old_session_service))
        session_module.session_service.save_session(
            {"id": "alice"},
            session_module.SESSION_KIND_IMAGE_SELECTION,
            {
                "id": "selection-1",
                "candidates": [
                    {"id": "candidate-1", "status": "discarded", "rel": "2026/01/01/discarded.png"},
                    {"id": "candidate-2", "status": "ready", "rel": "2026/01/01/ready.png"},
                    {"id": "candidate-3", "status": "kept", "rel": "../2026/01/01/unsafe.png"},
                    {"id": "candidate-4", "status": "kept"},
                ],
            },
        )

        removed = store.cleanup_old_images()

        self.assertEqual(removed, 4)
        self.assertFalse(discarded_image.exists())
        self.assertFalse(ready_image.exists())
        self.assertFalse(unsafe_image.exists())
        self.assertFalse(missing_path_image.exists())


if __name__ == "__main__":
    unittest.main()
