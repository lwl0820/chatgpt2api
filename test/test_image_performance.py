from __future__ import annotations

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from fastapi import HTTPException

from services import config as config_module
from services import image_service
from services.protocol import conversation


PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/p9sAAAAASUVORK5CYII="
)


class NoCleanupConfig:
    def __init__(self, images_dir: Path):
        self.images_dir = images_dir
        self.base_url = "http://local.test"

    def cleanup_old_images(self) -> int:
        raise AssertionError("cleanup_old_images should not run while saving images")


class ImagePerformanceTests(unittest.TestCase):
    def _make_store(self, base_dir: Path, data: dict[str, object] | None = None):
        config_path = base_dir / "config.json"
        config_path.write_text(json.dumps({"auth-key": "test-auth", **(data or {})}), encoding="utf-8")
        old_data_dir = config_module.DATA_DIR
        config_module.DATA_DIR = base_dir / "data"
        self.addCleanup(lambda: setattr(config_module, "DATA_DIR", old_data_dir))
        return config_module.ConfigStore(config_path)

    def test_save_image_bytes_does_not_trigger_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            images_dir = Path(tmp_dir) / "images"
            fake_config = NoCleanupConfig(images_dir)

            with mock.patch.object(conversation, "config", fake_config):
                url = conversation.save_image_bytes(PNG_1X1, "http://local.test")

            self.assertIn("/images/", url)
            self.assertEqual(len(list(images_dir.rglob("*.png"))), 1)

    def test_thumbnail_generation_disabled_does_not_create_thumbnail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = self._make_store(Path(tmp_dir), {"image_thumbnail_generation": False})
            source = store.images_dir / "2026/01/01/source.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(PNG_1X1)
            target = store.image_thumbnails_dir / "2026/01/01/source.png.png"

            with mock.patch.object(image_service, "config", store):
                with self.assertRaises(HTTPException) as raised:
                    image_service.ensure_thumbnail("2026/01/01/source.png")

            self.assertEqual(raised.exception.status_code, 404)
            self.assertFalse(target.exists())

    def test_thumbnail_generation_disabled_still_returns_existing_thumbnail(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            store = self._make_store(Path(tmp_dir), {"image_thumbnail_generation": False})
            source = store.images_dir / "2026/01/01/source.png"
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_bytes(PNG_1X1)
            target = store.image_thumbnails_dir / "2026/01/01/source.png.png"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(PNG_1X1)

            with mock.patch.object(image_service, "config", store):
                result = image_service.ensure_thumbnail("2026/01/01/source.png")

            self.assertEqual(result, target)


if __name__ == "__main__":
    unittest.main()
