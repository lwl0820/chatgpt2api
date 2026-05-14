## Purpose
Define how image downloads optionally append associated prompts to downloaded file data.

## Requirements

### Requirement: Setting controls prompt tail payload
The system SHALL provide a setting that controls whether image downloads append the prompt to the end of the file data, and that setting SHALL default to disabled.

#### Scenario: Prompt append defaults disabled
- **WHEN** the system configuration lacks the setting or an admin has not enabled it
- **THEN** image downloads SHALL preserve the previous file content and SHALL NOT append a prompt tail payload

#### Scenario: Admin enables prompt append
- **WHEN** an admin enables the append-prompt-on-image-download setting in the settings page and saves settings
- **THEN** the system SHALL persist the setting and append a prompt tail payload for subsequent image downloads that can be associated with a non-empty prompt

#### Scenario: Admin disables prompt append
- **WHEN** an admin disables the append-prompt-on-image-download setting in the settings page and saves settings
- **THEN** the system SHALL persist the setting and stop appending prompt tail payloads for subsequent image downloads

### Requirement: Image download file tail carries prompt
The system SHALL append the associated prompt as a UTF-8 text payload to the end of downloaded file data when prompt append is enabled and the image can be associated with a non-empty prompt.

#### Scenario: Download image conversation result
- **WHEN** prompt append is enabled and the user downloads a successfully generated image from an image conversation result whose turn has a non-empty prompt
- **THEN** the downloaded file data tail SHALL contain that turn prompt as a UTF-8 text payload

#### Scenario: Download image from preview
- **WHEN** prompt append is enabled and the user downloads the current image in an image preview dialog and the image can be associated with a non-empty prompt
- **THEN** the downloaded file data tail SHALL contain that prompt as a UTF-8 text payload

#### Scenario: Download single image from image manager
- **WHEN** prompt append is enabled and an admin downloads a single image from the image manager and the system can determine the image's non-empty prompt from existing conversation or selection records
- **THEN** the download response data tail SHALL contain that prompt as a UTF-8 text payload

#### Scenario: Batch download image manager images
- **WHEN** prompt append is enabled and an admin batch downloads images from the image manager and a zip entry can be associated with a non-empty prompt
- **THEN** that zip entry's image file data tail SHALL contain the corresponding prompt as a UTF-8 text payload

### Requirement: Prompt payload does not change downloaded filenames
The system MUST NOT carry prompts by appending prompt text to downloaded filenames, zip entry names, or extensions.

#### Scenario: Download filename keeps existing naming rules
- **WHEN** a user downloads an image that needs a prompt payload appended
- **THEN** the downloaded filename SHALL use the previous naming rules and MUST NOT include prompt content

#### Scenario: Zip entry name keeps existing naming rules
- **WHEN** a user batch downloads images that need prompt payloads appended
- **THEN** zip image entry names SHALL use the previous naming and deduplication rules and MUST NOT include prompt content

### Requirement: Downloads without prompts preserve original content
The system SHALL preserve image download content without appending empty prompts, placeholder text, or error messages when prompt append is disabled or no non-empty prompt can be obtained.

#### Scenario: Download image with prompt when setting disabled
- **WHEN** prompt append is disabled and the user downloads an image that can be associated with a non-empty prompt
- **THEN** the downloaded file content SHALL match the original download content and SHALL NOT contain a prompt tail payload

#### Scenario: Download image without associated prompt
- **WHEN** prompt append is enabled and the user downloads an image that the system cannot associate with a non-empty prompt
- **THEN** the downloaded file content SHALL match the original download content and SHALL NOT contain a prompt tail payload

#### Scenario: Batch download includes images without prompts
- **WHEN** a user batch downloads images and some zip entries cannot be associated with a non-empty prompt
- **THEN** those entries' file content SHALL preserve the original image content
