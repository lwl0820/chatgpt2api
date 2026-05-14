## ADDED Requirements

### Requirement: Candidate generation prompt provenance
The system SHALL record the prompt used to submit each new image selection candidate and use that candidate-level generation prompt wherever a prompt must be associated with that candidate image.

#### Scenario: New candidate records submitted prompt
- **WHEN** a running image selection session submits a new candidate generation task
- **THEN** the system SHALL store the non-empty session prompt used for that generation request on the candidate record before or while submitting the task

#### Scenario: Prompt update does not rewrite existing candidate prompts
- **WHEN** the user updates the prompt for an image selection session that already has loading, ready, kept, discarded, or error candidates
- **THEN** the system SHALL keep any existing candidate-level generation prompts unchanged while using the updated session prompt only for later candidate generation requests

#### Scenario: Image manager uses candidate prompt for selection images
- **WHEN** the image manager downloads an image that can be matched to an image selection candidate with a non-empty candidate-level generation prompt
- **THEN** the system SHALL use that candidate-level generation prompt as the prompt associated with the downloaded image

#### Scenario: Historical candidate prompt fallback
- **WHEN** a historical image selection candidate has no candidate-level generation prompt but belongs to a session with a non-empty prompt
- **THEN** the system SHALL be allowed to use the session prompt as the fallback prompt associated with that candidate image

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
- **THEN** the system SHALL download the current candidate image, use the candidate-level generation prompt for any enabled download prompt payload when that prompt is available, mark that candidate as kept using the same decision history semantics as an explicit keep action, and advance to the next ready candidate when one exists

#### Scenario: Download historical current candidate
- **WHEN** a ready candidate without a candidate-level generation prompt is focused for review and the user downloads it
- **THEN** the system SHALL download the current candidate image using the session prompt as the fallback prompt for any enabled download prompt payload, then preserve the same kept decision history and advancement semantics as other current candidate downloads

#### Scenario: Candidate queue uses thumbnails
- **WHEN** candidate images are shown in the normal or immersive candidate queue
- **THEN** the system SHALL use thumbnail image URLs when available while keeping the primary review image and immersive review image at full resolution

#### Scenario: Upcoming original images are preloaded
- **WHEN** a ready candidate is selected for review and additional ready candidates follow it
- **THEN** the system SHALL preload a small bounded number of upcoming original images to reduce primary review transition latency without rendering full-resolution images in the candidate queue

#### Scenario: Primary image loading is visible
- **WHEN** the primary review image or immersive review image is loading its original image
- **THEN** the system SHALL show a loading indication until the original image finishes loading or errors without changing candidate state or decision history
