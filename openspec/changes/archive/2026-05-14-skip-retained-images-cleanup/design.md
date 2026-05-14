## Context

Local generated images are stored under the configured images directory and are currently cleaned by `ConfigStore.cleanup_old_images()` using only `image_retention_days` and file modification time. Cleanup runs during app startup, image listing, and conversation image handling, so any preservation rule must be centralized in the backend cleanup path rather than added to a single caller.

Kept images are represented as image-selection session candidates with `status: "kept"` and a relative image path such as `rel` or `path`. Sessions are now persisted through the backend session store, while the image manager already uses kept candidate relative paths for selection-session filtering.

## Goals / Non-Goals

**Goals:**
- Add an admin setting that controls whether automatic image cleanup skips images kept in image-selection sessions.
- Keep the existing retention-days behavior and default cleanup semantics unchanged unless the new setting is enabled.
- Resolve protected images by relative path so cleanup can compare against files in the local images directory without relying on URLs.
- Surface the setting in the existing settings page and persist it through the settings API.

**Non-Goals:**
- Do not change manual image deletion, bulk deletion, downloads, tagging, or thumbnail cleanup semantics.
- Do not introduce a new candidate status or change image-selection session persistence shape.
- Do not make retained images permanent backups; this only protects them from automatic age-based cleanup.

## Decisions

1. Add a boolean config field named `image_cleanup_skip_kept` with default `false`.

   This preserves existing behavior for current deployments and makes the option explicit. The alternative was overloading `image_retention_days` with a sentinel value, but that would obscure two independent choices: retention window and whether kept images are exempt.

2. Centralize the skip check in `cleanup_old_images()`.

   All automatic cleanup callers already route through this method for original image files. Adding the preservation set there prevents inconsistent behavior between startup cleanup, image-list cleanup, and image-conversation cleanup. The alternative was filtering only in `list_images()`, which would still allow startup cleanup to delete kept files.

3. Build the protected relative-path set from backend image-selection sessions when the option is enabled.

   A protected file is any candidate in any accessible image-selection session with `status == "kept"` and a valid local relative path. Invalid or missing paths are ignored. The alternative was storing a separate keep registry, but the session documents already contain the source of truth and avoid migration work.

4. Leave manual deletion authoritative.

   The new setting only affects automatic cleanup. Admin-triggered image deletion should continue deleting selected files because it is an explicit user action, and changing it would conflict with image manager expectations.

## Risks / Trade-offs

- Session scan cost grows with the number of image-selection sessions -> Only scan sessions when `image_cleanup_skip_kept` is enabled and keep the result as an in-memory set for the cleanup pass.
- Stale session references may protect images longer than expected -> This is intentional for kept selections; manual deletion remains available for cleanup.
- Missing or malformed candidate paths may fail to protect an image -> Ignore unsafe paths rather than risk protecting files outside the image directory.
- Thumbnail cleanup may remove thumbnails for images that no longer exist -> This remains correct because thumbnails are derived artifacts; original images are the files being protected.
