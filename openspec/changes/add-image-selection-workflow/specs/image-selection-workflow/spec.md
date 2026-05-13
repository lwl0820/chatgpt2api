## ADDED Requirements

### Requirement: Image selection sessions
The system SHALL provide an image selection workflow where a user can create and resume local selection sessions built around a single prompt and image generation configuration.

#### Scenario: Create selection session
- **WHEN** the user enters a non-empty prompt on the image selection page and starts selection
- **THEN** the system SHALL create a selection session with the prompt, image size, queue limit snapshot, empty candidate list, and running status

#### Scenario: Restore existing selection session
- **WHEN** the user opens a previously created selection session
- **THEN** the system SHALL restore the session prompt, candidates, kept images, discarded images, and current status from local storage

### Requirement: Candidate queue auto-fill
The system SHALL continuously submit image generation tasks while a selection session is running until the number of loading and ready candidates reaches the configured queue limit.

#### Scenario: Fill empty queue
- **WHEN** a running selection session has fewer loading plus ready candidates than its queue limit
- **THEN** the system SHALL submit enough generation tasks to fill the available candidate slots

#### Scenario: Keep candidate and refill slot
- **WHEN** the user keeps a ready candidate
- **THEN** the system SHALL mark the candidate as kept and submit a replacement generation task if the running session is below its queue limit

#### Scenario: Discard candidate and refill slot
- **WHEN** the user discards a ready candidate
- **THEN** the system SHALL mark the candidate as discarded without deleting the image file and submit a replacement generation task if the running session is below its queue limit

### Requirement: Candidate decision controls
The image selection page SHALL present the current ready candidate as a large primary image and provide both keyboard shortcuts and visible action buttons for keeping or discarding it.

#### Scenario: Keep by keyboard
- **WHEN** a ready candidate is focused for review and the user presses ArrowUp outside of a text input
- **THEN** the system SHALL mark the current candidate as kept and advance to the next ready candidate when one exists

#### Scenario: Discard by keyboard
- **WHEN** a ready candidate is focused for review and the user presses ArrowDown outside of a text input
- **THEN** the system SHALL mark the current candidate as discarded and advance to the next ready candidate when one exists

#### Scenario: Keep or discard by button
- **WHEN** the user clicks the visible keep or discard button for the current ready candidate
- **THEN** the system SHALL perform the same decision action as the corresponding keyboard shortcut

### Requirement: Generation errors are skipped
The system SHALL automatically skip failed candidate generation tasks and continue filling the queue without requiring user decisions on failed candidates.

#### Scenario: Candidate task fails
- **WHEN** a candidate generation task returns an error
- **THEN** the system SHALL mark that candidate as error, exclude it from the active candidate queue, and continue filling available queue slots while the session is running

#### Scenario: Repeated failures pause selection
- **WHEN** candidate generation failures continue past the implementation-defined consecutive failure limit
- **THEN** the system SHALL pause the selection session and show an error state requiring the user to manually continue

### Requirement: Selection delete is non-destructive
The system SHALL treat discarding a candidate as a selection-session state change and MUST NOT delete the underlying local image file.

#### Scenario: Discard keeps physical file
- **WHEN** the user discards a candidate whose image was saved to the local image directory
- **THEN** the system SHALL keep the underlying image file available to global image management and only mark the candidate as discarded in the selection session

### Requirement: Manual resume after page reload
The system SHALL restore selection session state after page reload without automatically submitting new generation tasks to fill the queue.

#### Scenario: Reload running session
- **WHEN** the user reloads or reopens the image selection page for a session that was previously running
- **THEN** the system SHALL restore the session in a paused or resumable state and SHALL NOT submit new generation tasks until the user manually continues selection

#### Scenario: Recover submitted tasks
- **WHEN** a restored selection session contains loading candidates with task IDs
- **THEN** the system SHALL be allowed to poll those existing tasks and update their terminal status without submitting additional replacement tasks until the user manually continues selection

### Requirement: Configurable selection queue limit
The system SHALL allow administrators to configure the default image selection candidate queue length in settings.

#### Scenario: Save queue length setting
- **WHEN** an administrator saves a valid image selection queue length in settings
- **THEN** new selection sessions SHALL use that value as their default queue limit

#### Scenario: Missing queue length setting
- **WHEN** the queue length setting is missing or invalid
- **THEN** the system SHALL use a safe default queue length

### Requirement: Image manager selection-session filtering
The image manager SHALL allow users with image manager access to filter images by a local image selection session's kept images.

#### Scenario: Filter by selection session
- **WHEN** the user selects an image selection session filter in the image manager
- **THEN** the image manager SHALL show only images whose relative path matches kept candidates in that selection session, combined with the existing date and tag filters

#### Scenario: Discarded images excluded from session filter
- **WHEN** an image is marked discarded in a selection session
- **THEN** that image SHALL NOT appear when filtering the image manager by that selection session's kept images

#### Scenario: Clear selection session filter
- **WHEN** the user clears the image selection session filter
- **THEN** the image manager SHALL return to showing images according to the existing global image filters
