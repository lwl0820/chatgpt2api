## Purpose
Define automatic local image retention cleanup and protection for kept image-selection candidates.

## Requirements

### Requirement: Configurable automatic image retention cleanup
The system SHALL automatically delete local image files older than the configured image retention window, and SHALL provide an admin setting that optionally excludes kept image-selection candidates from that automatic cleanup.

#### Scenario: Default cleanup deletes old local images
- **WHEN** automatic image cleanup runs with the skip-kept-images option disabled or unset
- **THEN** the system SHALL delete local image files older than the configured image retention window using the existing age-based behavior

#### Scenario: Cleanup skips kept selection images when enabled
- **WHEN** automatic image cleanup runs with the skip-kept-images option enabled and an old local image is referenced by a kept image-selection candidate
- **THEN** the system SHALL keep that image file even when it is older than the configured image retention window

#### Scenario: Cleanup still removes old non-kept images when enabled
- **WHEN** automatic image cleanup runs with the skip-kept-images option enabled and an old local image is not referenced by any kept image-selection candidate
- **THEN** the system SHALL delete that image file according to the configured image retention window

### Requirement: Kept image protection source
The system SHALL determine protected kept images from persisted image-selection session candidates that are marked kept and reference a valid local image relative path.

#### Scenario: Kept candidate has a local relative path
- **WHEN** an image-selection candidate has `status` set to `kept` and references a valid local relative image path
- **THEN** automatic cleanup SHALL treat the referenced image as protected while the skip-kept-images option is enabled

#### Scenario: Candidate is not kept
- **WHEN** an image-selection candidate is loading, ready, discarded, or error
- **THEN** automatic cleanup SHALL NOT protect its image solely because it appears in an image-selection session

#### Scenario: Candidate path is missing or unsafe
- **WHEN** a kept image-selection candidate does not include a local relative image path or includes a path that resolves outside the local image directory
- **THEN** automatic cleanup SHALL ignore that candidate for cleanup protection

### Requirement: Settings expose kept-image cleanup option
The settings API and settings UI SHALL expose the skip-kept-images cleanup option alongside the existing image auto-cleanup retention setting.

#### Scenario: Admin loads settings
- **WHEN** an admin loads system settings
- **THEN** the response SHALL include the current skip-kept-images cleanup option value, defaulting to disabled when absent from stored configuration

#### Scenario: Admin saves setting
- **WHEN** an admin changes the skip-kept-images cleanup option and saves settings
- **THEN** the system SHALL persist the option and use it for subsequent automatic image cleanup runs

#### Scenario: Manual deletion remains explicit
- **WHEN** an admin manually deletes images through the image manager delete action
- **THEN** the system SHALL delete the requested images regardless of the skip-kept-images cleanup option
