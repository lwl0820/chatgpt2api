## Why

Image auto-cleanup currently removes old local image files solely by file age. Users who mark generated images as kept in image selection sessions need a way to preserve those intentional selections from automatic retention cleanup.

## What Changes

- Add a configurable image auto-cleanup option that prevents kept image-selection candidates from being deleted by age-based cleanup.
- Expose the option in settings alongside the existing image retention-days control.
- Preserve current cleanup behavior by default unless the option is enabled.
- Keep manual image deletion behavior unchanged so admins can still explicitly delete images.

## Capabilities

### New Capabilities
- `image-retention-cleanup`: Covers local image auto-cleanup settings, retention-day behavior, and optional preservation of kept image-selection candidates.

### Modified Capabilities

## Impact

- Affects backend configuration loading, update serialization, and settings API payloads.
- Affects automatic local image cleanup in `services.config.Config.cleanup_old_images` and callers such as app startup and image listing.
- Affects the settings UI and API client config types.
- Requires tests for default cleanup behavior and the new skip-kept-images option.
