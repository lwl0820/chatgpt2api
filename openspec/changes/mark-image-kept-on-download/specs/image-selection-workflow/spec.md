## MODIFIED Requirements

### Requirement: Candidate decision controls
The image selection page SHALL present the current ready candidate as a large primary image and provide both keyboard shortcuts and visible action buttons for keeping, discarding, undoing, and downloading it.

#### Scenario: Keep by keyboard
- **WHEN** a ready candidate is focused for review and the user presses ArrowUp outside of a text input
- **THEN** the system SHALL mark the current candidate as kept and advance to the next ready candidate when one exists

#### Scenario: Discard by keyboard
- **WHEN** a ready candidate is focused for review and the user presses ArrowDown outside of a text input
- **THEN** the system SHALL mark the current candidate as discarded and advance to the next ready candidate when one exists

#### Scenario: Keep or discard by button
- **WHEN** the user clicks the visible keep or discard button for the current ready candidate
- **THEN** the system SHALL perform the same decision action as the corresponding keyboard shortcut

#### Scenario: Undo latest decision
- **WHEN** the user presses ArrowLeft outside of a text input or clicks the visible undo control after keeping or discarding candidates
- **THEN** the system SHALL restore the latest kept or discarded candidate to ready status and make it the current candidate for review

#### Scenario: Undo history is bounded
- **WHEN** the user makes more than ten keep or discard decisions in a selection session
- **THEN** the system SHALL retain only the ten most recent decisions for undo

#### Scenario: Undo is non-destructive
- **WHEN** the user undoes a keep or discard decision
- **THEN** the system SHALL only update selection-session state and SHALL NOT create, delete, or restore physical image files

#### Scenario: Download current candidate
- **WHEN** a ready candidate is focused for review and the user presses ArrowRight outside of a text input or clicks the visible download control
- **THEN** the system SHALL download the current candidate image, mark that candidate as kept using the same decision history semantics as an explicit keep action, and advance to the next ready candidate when one exists

#### Scenario: Candidate queue uses thumbnails
- **WHEN** candidate images are shown in the normal or immersive candidate queue
- **THEN** the system SHALL use thumbnail image URLs when available while keeping the primary review image and immersive review image at full resolution

#### Scenario: Upcoming original images are preloaded
- **WHEN** a ready candidate is selected for review and additional ready candidates follow it
- **THEN** the system SHALL preload a small bounded number of upcoming original images to reduce primary review transition latency without rendering full-resolution images in the candidate queue

#### Scenario: Primary image loading is visible
- **WHEN** the primary review image or immersive review image is loading its original image
- **THEN** the system SHALL show a loading indication until the original image finishes loading or errors without changing candidate state or decision history
