from __future__ import annotations

import io
import mimetypes
import zipfile
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

from fastapi import HTTPException
from fastapi.responses import FileResponse, Response
from PIL import Image, ImageOps

from services.config import config
from services.image_tags_service import load_tags, remove_tags

THUMBNAIL_SIZE = (320, 320)
PROMPT_PAYLOAD_PREFIX = b"\n\n-- chatgpt2api prompt --\n"
PROMPT_PAYLOAD_SUFFIX = b"\n-- end chatgpt2api prompt --\n"


def _cleanup_empty_dirs(root: Path) -> None:
    for path in sorted((p for p in root.rglob("*") if p.is_dir()), key=lambda p: len(p.parts), reverse=True):
        try:
            path.rmdir()
        except OSError:
            pass


def _safe_relative_path(path: str) -> str:
    value = str(path or "").strip().replace("\\", "/").lstrip("/")
    if not value:
        raise HTTPException(status_code=404, detail="image not found")
    parts = Path(value).parts
    if any(part in {"", ".", ".."} for part in parts):
        raise HTTPException(status_code=404, detail="image not found")
    return Path(*parts).as_posix()


def _safe_image_path(relative_path: str) -> Path:
    rel = _safe_relative_path(relative_path)
    root = config.images_dir.resolve()
    path = (root / rel).resolve()
    try:
        path.relative_to(root)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="image not found") from exc
    if not path.is_file():
        raise HTTPException(status_code=404, detail="image not found")
    return path


def append_prompt_payload(data: bytes, prompt: str) -> bytes:
    normalized = str(prompt or "").strip()
    if not normalized:
        return data
    return data + PROMPT_PAYLOAD_PREFIX + normalized.encode("utf-8") + PROMPT_PAYLOAD_SUFFIX


def _extract_image_relative_path(value: object) -> str:
    source = str(value or "").strip()
    if not source:
        return ""
    marker = "/images/"
    if marker in source:
        source = source.split(marker, 1)[1].split("?", 1)[0].split("#", 1)[0]
    return _safe_relative_path(unquote(source))


def _safe_extract_image_relative_path(value: object) -> str:
    try:
        return _extract_image_relative_path(value)
    except HTTPException:
        return ""


def _image_prompt_map() -> dict[str, str]:
    try:
        from services.session_service import SESSION_KIND_IMAGE_CONVERSATION, SESSION_KIND_IMAGE_SELECTION, session_service
    except Exception:
        return {}

    prompts: dict[str, str] = {}
    for record in session_service.list_all_sessions(SESSION_KIND_IMAGE_CONVERSATION):
        item = record.get("item") if isinstance(record, dict) else None
        turns = item.get("turns") if isinstance(item, dict) else None
        if not isinstance(turns, list):
            continue
        for turn in turns:
            if not isinstance(turn, dict):
                continue
            prompt = str(turn.get("prompt") or "").strip()
            images = turn.get("images")
            if not prompt or not isinstance(images, list):
                continue
            for image in images:
                if not isinstance(image, dict):
                    continue
                rel = _safe_extract_image_relative_path(image.get("rel") or image.get("path") or image.get("url"))
                if rel:
                    prompts[rel] = prompt

    for record in session_service.list_all_sessions(SESSION_KIND_IMAGE_SELECTION):
        item = record.get("item") if isinstance(record, dict) else None
        if not isinstance(item, dict):
            continue
        prompt = str(item.get("prompt") or "").strip()
        candidates = item.get("candidates")
        if not prompt or not isinstance(candidates, list):
            continue
        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue
            rel = _safe_extract_image_relative_path(candidate.get("rel") or candidate.get("path") or candidate.get("url"))
            if rel:
                prompts[rel] = prompt
    return prompts


def _thumbnail_path(relative_path: str) -> Path:
    rel = _safe_relative_path(relative_path)
    return config.image_thumbnails_dir / f"{rel}.png"


def thumbnail_url(base_url: str, relative_path: str) -> str:
    return f"{base_url.rstrip('/')}/image-thumbnails/{_safe_relative_path(relative_path)}"


def _image_dimensions(path: Path) -> tuple[int, int] | None:
    try:
        with Image.open(path) as image:
            return image.size
    except Exception:
        return None


def ensure_thumbnail(relative_path: str) -> Path:
    source = _safe_image_path(relative_path)
    target = _thumbnail_path(relative_path)
    source_mtime = source.stat().st_mtime
    if target.exists() and target.stat().st_mtime >= source_mtime:
        return target

    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        with Image.open(source) as image:
            image = ImageOps.exif_transpose(image)
            if image.mode not in {"RGB", "RGBA"}:
                image = image.convert("RGBA" if "A" in image.getbands() else "RGB")
            image.thumbnail(THUMBNAIL_SIZE, Image.Resampling.LANCZOS)
            image.save(target, format="PNG", optimize=True)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=422, detail="failed to create thumbnail") from exc
    return target


def get_thumbnail_response(relative_path: str) -> FileResponse:
    return FileResponse(ensure_thumbnail(relative_path))


def get_image_download_response(relative_path: str) -> FileResponse | Response:
    path = _safe_image_path(relative_path)
    rel = path.relative_to(config.images_dir.resolve()).as_posix()
    prompt = _image_prompt_map().get(rel) if config.image_download_append_prompt else ""
    if prompt:
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return Response(
            append_prompt_payload(path.read_bytes(), prompt),
            media_type=media_type,
            headers={"Content-Disposition": f'attachment; filename="{path.name}"'},
        )
    return FileResponse(path, filename=path.name)


def cleanup_image_thumbnails() -> int:
    thumbnails_root = config.image_thumbnails_dir
    images_root = config.images_dir
    removed = 0
    for path in thumbnails_root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(thumbnails_root).as_posix()
        if not rel.endswith(".png") or not (images_root / rel[:-4]).exists():
            path.unlink()
            removed += 1
    _cleanup_empty_dirs(thumbnails_root)
    return removed


def _image_items(start_date: str = "", end_date: str = "") -> list[dict[str, object]]:
    items = []
    root = config.images_dir
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        parts = rel.split("/")
        day = "-".join(parts[:3]) if len(parts) >= 4 else datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d")
        if start_date and day < start_date:
            continue
        if end_date and day > end_date:
            continue
        dimensions = _image_dimensions(path)
        items.append({
            "rel": rel,
            "path": rel,
            "name": path.name,
            "date": day,
            "size": path.stat().st_size,
            "created_at": datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            **({"width": dimensions[0], "height": dimensions[1]} if dimensions else {}),
        })
    items.sort(key=lambda item: str(item["created_at"]), reverse=True)
    return items


def list_images(base_url: str, start_date: str = "", end_date: str = "") -> dict[str, object]:
    config.cleanup_old_images()
    cleanup_image_thumbnails()
    all_tags = load_tags()
    items = [
        {
            **item,
            "url": f"{base_url.rstrip('/')}/images/{item['path']}",
            "thumbnail_url": thumbnail_url(base_url, str(item["path"])),
            "tags": all_tags.get(str(item["path"]), []),
        }
        for item in _image_items(start_date, end_date)
    ]
    groups: dict[str, list[dict[str, object]]] = {}
    for item in items:
        groups.setdefault(str(item["date"]), []).append(item)
    return {"items": items, "groups": [{"date": key, "items": value} for key, value in groups.items()]}


def delete_images(paths: list[str] | None = None, start_date: str = "", end_date: str = "", all_matching: bool = False) -> dict[str, int]:
    root = config.images_dir.resolve()
    targets = [str(item["path"]) for item in _image_items(start_date, end_date)] if all_matching else (paths or [])
    removed = 0
    for item in targets:
        path = (root / item).resolve()
        try:
            path.relative_to(root)
        except ValueError:
            continue
        if path.is_file():
            path.unlink()
            for thumbnail in (_thumbnail_path(item), config.image_thumbnails_dir / _safe_relative_path(item)):
                if thumbnail.is_file():
                    thumbnail.unlink()
            remove_tags(item)
            removed += 1
    _cleanup_empty_dirs(root)
    _cleanup_empty_dirs(config.image_thumbnails_dir)
    return {"removed": removed}


def download_images_zip(paths: list[str]) -> io.BytesIO:
    root = config.images_dir.resolve()
    buf = io.BytesIO()
    added = 0
    used_names: set[str] = set()
    prompt_map = _image_prompt_map() if config.image_download_append_prompt else {}
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for item in paths:
            rel = _safe_relative_path(item)
            path = (root / rel).resolve()
            try:
                path.relative_to(root)
            except ValueError:
                continue
            if not path.is_file():
                continue
            name = path.name
            if name in used_names:
                stem = path.stem
                suffix = path.suffix
                counter = 2
                while f"{stem}_{counter}{suffix}" in used_names:
                    counter += 1
                name = f"{stem}_{counter}{suffix}"
            used_names.add(name)
            prompt = prompt_map.get(rel)
            if prompt:
                zf.writestr(name, append_prompt_payload(path.read_bytes(), prompt))
            else:
                zf.write(path, name)
            added += 1
    if added == 0:
        raise HTTPException(status_code=404, detail="no images found")
    buf.seek(0)
    return buf
