## Purpose
Define performance-related image generation behavior for save-time cleanup and thumbnail generation.

## Requirements

### Requirement: Image save path does not trigger retention cleanup
The system SHALL NOT run automatic image retention cleanup as a side effect of saving newly generated image results.

#### Scenario: Save generated image
- **WHEN** an image generation task completes successfully and the system writes result image files
- **THEN** the save operation SHALL complete without invoking automatic retention cleanup

#### Scenario: Explicit cleanup remains independent
- **WHEN** cleanup is triggered after image saving through an explicit maintenance path or retention path
- **THEN** cleanup behavior SHALL preserve its existing semantics and remain independent from the save operation

### Requirement: Thumbnail generation is configurable
The system SHALL provide an admin setting that enables or disables thumbnail generation for local images; when no stored value exists, the setting SHALL default to enabled.

#### Scenario: Admin loads setting without stored value
- **WHEN** an admin loads system settings and the thumbnail generation flag has not yet been stored
- **THEN** the response SHALL report thumbnail generation as enabled

#### Scenario: Admin disables thumbnail generation
- **WHEN** an admin disables thumbnail generation and saves settings
- **THEN** the system SHALL persist the disabled state and SHALL stop creating new thumbnail files for subsequent images

### Requirement: Thumbnail switch only affects creation
The thumbnail generation switch SHALL only control whether the system creates new thumbnail files and SHALL NOT change thumbnail cleanup or thumbnail response behavior.

#### Scenario: Request existing thumbnail after disabling switch
- **WHEN** thumbnail generation is disabled and the requested thumbnail file already exists
- **THEN** the system SHALL return that thumbnail using existing thumbnail response behavior

#### Scenario: Run thumbnail cleanup after disabling switch
- **WHEN** thumbnail generation is disabled and the system runs thumbnail cleanup
- **THEN** the system SHALL clean invalid thumbnails using existing thumbnail cleanup rules

#### Scenario: Request missing thumbnail after disabling switch
- **WHEN** thumbnail generation is disabled and the requested thumbnail file does not exist
- **THEN** the system SHALL preserve current response behavior and SHALL NOT add an original-image response branch because of the switch
