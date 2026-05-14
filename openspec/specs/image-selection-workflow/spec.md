## Purpose
Define the image selection workflow for creating, resuming, reviewing, downloading, and filtering generated image candidates.

## Requirements

### Requirement: Image selection sessions
The system SHALL provide an image selection workflow where a user can create and resume local selection sessions built around a single prompt, image generation configuration, candidate queue length, and consecutive failure pause limit. The system SHALL list image selection sessions only by `updatedAt` descending; `updatedAt` represents only session creation or user-edited session configuration time and does not represent image generation task or candidate state changes inside the session.

#### Scenario: Create selection session
- **WHEN** the user enters a non-empty prompt on the image selection page and starts selection
- **THEN** the system SHALL create a selection session with the prompt, image size, queue limit, consecutive failure pause limit, empty candidate list, and running status
- **AND** the system SHALL set the session's `createdAt` and `updatedAt` to the creation time

#### Scenario: Restore existing selection session
- **WHEN** the user opens a previously created selection session
- **THEN** the system SHALL restore the session prompt, candidates, kept images, discarded images, and current status from local storage

#### Scenario: List sessions by updated time descending
- **WHEN** the system displays the image selection session list
- **THEN** the system SHALL sort sessions by `updatedAt` descending so the most recently created or most recently configuration-edited session appears first

#### Scenario: Editing session configuration updates sorting time
- **WHEN** the user edits and saves an image selection session's title, prompt, queue length, or consecutive failure pause limit
- **THEN** the system SHALL update that session's `updatedAt`
- **AND** the session list SHALL be resorted by the new `updatedAt`

#### Scenario: Image generation task changes do not update sorting time
- **WHEN** candidate task polling, completion, failure, keep, discard, undo, pause, or continue changes occur inside an image selection session
- **THEN** the system SHALL keep that session's `updatedAt` unchanged
- **AND** the system SHALL NOT move that session above other updated sessions because of those changes

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

### Requirement: Generation errors are skipped
The system SHALL automatically skip failed candidate generation tasks and continue filling the queue without requiring user decisions on failed candidates.

#### Scenario: Candidate task fails
- **WHEN** a candidate generation task returns an error
- **THEN** the system SHALL mark that candidate as error, exclude it from the active candidate queue, and continue filling available queue slots while the session is running

#### Scenario: Repeated failures pause selection
- **WHEN** candidate generation failures reach the selection session's configured consecutive failure limit
- **THEN** the system SHALL pause the selection session and show an error state requiring the user to manually continue

#### Scenario: Out-of-order failures do not pause selection
- **WHEN** failed candidate tasks complete after later successful tasks but those failures are not consecutive at the tail of candidate creation order
- **THEN** the system SHALL NOT pause the selection session solely because the failures were observed consecutively by polling

### Requirement: Selection delete is non-destructive
The system SHALL treat discarding a candidate as a selection-session state change and MUST NOT delete the underlying local image file.

#### Scenario: Discard keeps physical file
- **WHEN** the user discards a candidate whose image was saved to the local image directory
- **THEN** the system SHALL keep the underlying image file available to global image management and only mark the candidate as discarded in the selection session

### Requirement: Selection session deletion is non-destructive
The system SHALL allow users to delete an image selection session record without deleting any generated image files.

#### Scenario: Delete selection session
- **WHEN** the user confirms deletion of an image selection session
- **THEN** the system SHALL remove the local selection session record and keep all generated image files available in global image management

#### Scenario: Delete active selection session
- **WHEN** the user deletes the currently selected image selection session
- **THEN** the system SHALL select the first remaining available selection session sorted by `updatedAt` descending or return to the empty selection state

### Requirement: Immersive image selection mode
The image selection page SHALL provide an in-app immersive review mode that lets the current candidate image use as much of the browser viewport as possible without invoking browser or operating system fullscreen.

#### Scenario: Enter immersive mode
- **WHEN** the user activates immersive image selection mode for a selection session
- **THEN** the system SHALL display the review UI in a viewport-filling in-app overlay with the current image using the available browser window space

#### Scenario: Exit immersive mode
- **WHEN** the user presses Escape or clicks the exit control in immersive mode
- **THEN** the system SHALL return to the normal image selection page layout

#### Scenario: Immersive decisions
- **WHEN** the user keeps or discards a candidate in immersive mode
- **THEN** the system SHALL apply the same non-destructive candidate decision behavior as the normal review mode

### Requirement: Manual resume after page reload
The system SHALL restore selection session state after page reload without automatically submitting new generation tasks to fill the queue.

#### Scenario: Reload running session
- **WHEN** the user reloads or reopens the image selection page for a session that was previously running
- **THEN** the system SHALL restore the session in a paused or resumable state and SHALL NOT submit new generation tasks until the user manually continues selection

#### Scenario: Recover submitted tasks
- **WHEN** a restored selection session contains loading candidates with task IDs
- **THEN** the system SHALL be allowed to poll those existing tasks and update their terminal status without submitting additional replacement tasks until the user manually continues selection

### Requirement: Configurable selection session
The system SHALL allow users to configure the session title, prompt, candidate queue length, and consecutive failure pause limit when creating or editing an image selection session.

#### Scenario: Create with session limits
- **WHEN** the user starts an image selection session with valid queue length and consecutive failure pause values
- **THEN** the system SHALL store those values on that selection session and use them for queue fill and failure pause behavior

#### Scenario: Missing session limits
- **WHEN** session limit values are missing or invalid
- **THEN** the system SHALL use safe default values for queue length and consecutive failure pause behavior

#### Scenario: Update current session configuration
- **WHEN** the user updates the title, queue length, or consecutive failure pause value for the current selection session
- **THEN** the system SHALL persist the new values to that session and use the updated limits for subsequent queue fill and failure pause behavior

#### Scenario: Update current session prompt
- **WHEN** the user updates the prompt for the current selection session to a non-empty value
- **THEN** the system SHALL persist the new prompt to that session and use it for subsequent generation requests

#### Scenario: Reject empty session prompt update
- **WHEN** the user attempts to save an empty or whitespace-only prompt for the current selection session
- **THEN** the system SHALL reject the update and keep the previously persisted prompt

#### Scenario: Existing candidates remain unchanged after prompt update
- **WHEN** the user updates the prompt for a selection session that already has loading, ready, kept, discarded, or error candidates
- **THEN** the system SHALL keep existing candidates and decision history unchanged while applying the new prompt only to later generation requests

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
