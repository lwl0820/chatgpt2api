## 1. Backend Configuration

- [x] 1.1 Add `image_cleanup_skip_kept` normalization to backend config loading and settings serialization with a default of `false`.
- [x] 1.2 Ensure settings updates persist `image_cleanup_skip_kept` without changing existing `image_retention_days` validation.

## 2. Cleanup Protection

- [x] 2.1 Add a backend helper that collects valid relative image paths from persisted image-selection candidates with `status == "kept"`.
- [x] 2.2 Update `cleanup_old_images()` to skip protected kept-image paths only when `image_cleanup_skip_kept` is enabled.
- [x] 2.3 Preserve existing automatic cleanup behavior for old images that are not protected or when the option is disabled.
- [x] 2.4 Keep manual image deletion and thumbnail orphan cleanup behavior unchanged.

## 3. Settings UI

- [x] 3.1 Add `image_cleanup_skip_kept` to the frontend settings config type and store normalization/save flow.
- [x] 3.2 Add a settings-page checkbox near the image auto-cleanup input to control whether kept selection images are skipped.
- [x] 3.3 Use clear UI copy indicating that the option affects automatic cleanup only, not manual deletion.

## 4. Verification

- [x] 4.1 Add backend tests showing default age-based cleanup still deletes old images.
- [x] 4.2 Add backend tests showing enabled skip-kept cleanup preserves old images referenced by kept selection candidates.
- [x] 4.3 Add backend tests showing discarded, ready, missing-path, or unsafe-path candidates do not protect old images.
- [x] 4.4 Run the relevant backend and frontend checks for configuration, image cleanup, and settings UI changes.
