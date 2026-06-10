from __future__ import annotations

from datetime import datetime
import json
from math import isfinite
from pathlib import Path
import threading
import time

from services import config as config_module

_LOCK = threading.RLock()


def _default_path() -> Path:
    return config_module.DATA_DIR / "image_metadata.json"


def normalize_image_relative_path(value: object) -> str:
    rel = str(value or "").strip().replace("\\", "/").lstrip("/")
    if not rel:
        return ""
    parts = Path(rel).parts
    if any(part in {"", ".", ".."} for part in parts):
        return ""
    return Path(*parts).as_posix()


def parse_created_timestamp(value: object) -> float:
    if isinstance(value, bool):
        return 0.0
    if isinstance(value, (int, float)):
        timestamp = float(value)
        return max(0.0, timestamp) if isfinite(timestamp) else 0.0
    if not isinstance(value, str):
        return 0.0

    text = value.strip()
    if not text:
        return 0.0
    try:
        timestamp = float(text)
        return max(0.0, timestamp) if isfinite(timestamp) else 0.0
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return max(0.0, datetime.strptime(text[:26], fmt).timestamp())
        except ValueError:
            continue
    try:
        return max(0.0, datetime.fromisoformat(text.replace("Z", "+00:00")).timestamp())
    except Exception:
        return 0.0


def format_created_at(timestamp: float) -> str:
    return datetime.fromtimestamp(max(0.0, float(timestamp))).strftime("%Y-%m-%d %H:%M:%S")


def _load(path: Path) -> dict[str, dict[str, object]]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    if isinstance(data, dict) and isinstance(data.get("images"), dict):
        source = data["images"]
    elif isinstance(data, dict):
        source = data
    else:
        return {}

    images: dict[str, dict[str, object]] = {}
    for key, value in source.items():
        rel = normalize_image_relative_path(key)
        if not rel or not isinstance(value, dict):
            continue
        images[rel] = dict(value)
    return images


def _save(path: Path, images: dict[str, dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps({"images": images}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def save_image_metadata(relative_path: object, created_at: object | None = None, *, path: Path | None = None) -> dict[str, object]:
    rel = normalize_image_relative_path(relative_path)
    if not rel:
        raise ValueError("invalid image relative path")
    metadata_path = path or _default_path()
    timestamp = parse_created_timestamp(created_at) if created_at is not None else time.time()
    record = {"created_at": timestamp}
    with _LOCK:
        images = _load(metadata_path)
        images[rel] = record
        _save(metadata_path, images)
    return {"rel": rel, **record}


def get_image_created_timestamp(relative_path: object, *, path: Path | None = None) -> float:
    rel = normalize_image_relative_path(relative_path)
    if not rel:
        return 0.0
    with _LOCK:
        record = _load(path or _default_path()).get(rel)
    if not isinstance(record, dict):
        return 0.0
    return parse_created_timestamp(record.get("created_at"))


def remove_image_metadata(relative_path: object, *, path: Path | None = None) -> bool:
    rel = normalize_image_relative_path(relative_path)
    if not rel:
        return False
    metadata_path = path or _default_path()
    with _LOCK:
        images = _load(metadata_path)
        removed = images.pop(rel, None) is not None
        if removed:
            _save(metadata_path, images)
    return removed
