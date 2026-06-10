import json
import tempfile
import time
import unittest
from pathlib import Path


class ImageMetadataServiceTests(unittest.TestCase):
    def test_save_get_and_remove_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "image_metadata.json"

            from services.image_metadata_service import get_image_created_timestamp, remove_image_metadata, save_image_metadata

            save_image_metadata("2026/01/01/cat.png", 123.5, path=path)

            self.assertEqual(get_image_created_timestamp("2026/01/01/cat.png", path=path), 123.5)
            self.assertTrue(remove_image_metadata("2026/01/01/cat.png", path=path))
            self.assertEqual(get_image_created_timestamp("2026/01/01/cat.png", path=path), 0.0)

    def test_missing_invalid_and_unsafe_metadata_default_to_zero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "image_metadata.json"
            path.write_text(json.dumps({"images": {"2026/01/01/bad.png": {"created_at": "bad"}}}), encoding="utf-8")

            from services.image_metadata_service import get_image_created_timestamp

            self.assertEqual(get_image_created_timestamp("2026/01/01/missing.png", path=path), 0.0)
            self.assertEqual(get_image_created_timestamp("2026/01/01/bad.png", path=path), 0.0)
            self.assertEqual(get_image_created_timestamp("../unsafe.png", path=path), 0.0)

    def test_save_image_bytes_records_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            from services import config as config_module
            from services.image_metadata_service import get_image_created_timestamp
            from services.protocol.conversation import save_image_bytes

            old_data_dir = config_module.DATA_DIR
            config_module.DATA_DIR = Path(tmp_dir) / "data"
            self.addCleanup(lambda: setattr(config_module, "DATA_DIR", old_data_dir))

            before = time.time() - 1
            url = save_image_bytes(b"image-bytes", "http://example.test")
            rel = url.split("/images/", 1)[1]

            self.assertGreaterEqual(get_image_created_timestamp(rel), before)

    def test_image_items_use_metadata_time_and_zero_default(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            from services import config as config_module
            from services.image_metadata_service import format_created_at, save_image_metadata
            from services.image_service import _image_items

            old_data_dir = config_module.DATA_DIR
            config_module.DATA_DIR = Path(tmp_dir) / "data"
            self.addCleanup(lambda: setattr(config_module, "DATA_DIR", old_data_dir))

            root = config_module.DATA_DIR / "images"
            for rel in ("2026/01/01/old.png", "2026/01/02/new.png", "2026/01/03/missing.png"):
                path = root / rel
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"image")

            save_image_metadata("2026/01/01/old.png", 100)
            save_image_metadata("2026/01/02/new.png", 200)

            items = _image_items()

            self.assertEqual([item["path"] for item in items], ["2026/01/02/new.png", "2026/01/01/old.png", "2026/01/03/missing.png"])
            self.assertEqual(items[-1]["created_at"], format_created_at(0))

    def test_delete_images_removes_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            from services import config as config_module
            from services.image_metadata_service import get_image_created_timestamp, save_image_metadata
            from services.image_service import delete_images

            old_data_dir = config_module.DATA_DIR
            config_module.DATA_DIR = Path(tmp_dir) / "data"
            self.addCleanup(lambda: setattr(config_module, "DATA_DIR", old_data_dir))

            rel = "2026/01/01/delete.png"
            image_path = config_module.DATA_DIR / "images" / rel
            image_path.parent.mkdir(parents=True, exist_ok=True)
            image_path.write_bytes(b"image")
            save_image_metadata(rel, 100)

            result = delete_images([rel])

            self.assertEqual(result, {"removed": 1})
            self.assertFalse(image_path.exists())
            self.assertEqual(get_image_created_timestamp(rel), 0.0)


if __name__ == "__main__":
    unittest.main()
