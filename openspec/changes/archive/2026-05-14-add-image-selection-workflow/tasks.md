## 1. Settings And Data Model

- [x] 1.1 Keep selection queue length and consecutive failure pause threshold as per-session fields instead of global settings.
- [x] 1.2 Remove the global selection queue length control from settings.
- [x] 1.3 Create a local `image-selection-sessions` store with session, candidate, status, limits, normalization, persistence, and stats helpers.
- [x] 1.4 Add utilities to extract image relative paths from generated image URLs for matching against `ManagedImage.rel`.

## 2. Image Selection Page

- [x] 2.1 Add a `/image-select` route and top navigation entry that preserves existing auth behavior.
- [x] 2.2 Build the selection composer for prompt, image size, start, pause, and continue actions.
- [x] 2.3 Build the large current-candidate review surface with candidate thumbnails and loading/empty states.
- [x] 2.4 Add visible keep and discard buttons that update candidate state without deleting image files.
- [x] 2.5 Add ArrowUp and ArrowDown keyboard shortcuts for keep and discard while ignoring text input focus.

## 3. Candidate Queue Engine

- [x] 3.1 Implement candidate task submission using the existing image generation task API.
- [x] 3.2 Implement task polling and candidate updates for loading, ready, error, kept, and discarded states.
- [x] 3.3 Implement auto-fill logic based on loading plus ready candidates and the session queue limit.
- [x] 3.4 Implement automatic error skipping and consecutive failure protection that pauses the session with a visible message.
- [x] 3.5 Ensure reload restores sessions and polls existing submitted tasks without submitting new replacement tasks until the user clicks continue.

## 4. Image Manager Integration

- [x] 4.1 Load local image selection sessions in the image manager page.
- [x] 4.2 Add a selection-session filter control with a clear-filter action.
- [x] 4.3 Filter managed images by kept candidate relative paths from the selected session, composed with existing date and tag filters.
- [x] 4.4 Ensure discarded candidates are excluded from the session filter while their physical files remain visible when no session filter is active.

## 5. Verification

- [x] 5.1 Verify starting selection fills the queue up to the configured limit and does not exceed it.
- [x] 5.2 Verify keep and discard via both keyboard and buttons advance the current candidate and refill the queue.
- [x] 5.3 Verify failed generations are skipped and repeated failures pause the session.
- [x] 5.4 Verify discarding a candidate does not call image deletion and the image remains available in global image management.
- [x] 5.5 Verify refreshing or reopening a session restores state but does not submit new tasks until continue is clicked.
- [x] 5.6 Verify image manager selection-session filtering shows only kept images and works with existing tag/date filters.
- [x] 5.7 Run the available frontend checks, at least TypeScript or lint, and address any regressions.

## 6. Session Management And Immersive Review

- [x] 6.1 Add non-destructive image selection session deletion to local storage.
- [x] 6.2 Add delete controls and confirmation UI to the image selection session list.
- [x] 6.3 Ensure deleting the active session selects a fallback session or returns to empty state without deleting image files.
- [x] 6.4 Add an in-app immersive review mode that fills the browser viewport without using browser fullscreen APIs.
- [x] 6.5 Preserve keep, discard, thumbnail selection, and Escape-to-exit behavior in immersive mode.

## 7. Session Configuration

- [x] 7.1 Add a current-session configuration dialog for queue length and consecutive failure pause values.
- [x] 7.2 Persist edited session limits and use them for subsequent queue fill and failure pause behavior.
- [x] 7.3 Allow editing the current selection session title from the configuration dialog.
- [x] 7.4 Calculate consecutive failures from the tail of candidate creation order instead of task completion order.

## 8. Decision Undo

- [x] 8.1 Add per-session persisted decision history bounded to the ten most recent keep/discard decisions.
- [x] 8.2 Record keep and discard decisions in history while preserving non-destructive image behavior.
- [x] 8.3 Add undo logic that restores the latest valid kept/discarded candidate to ready and makes it current.
- [x] 8.4 Add ArrowLeft and visible undo controls in normal and immersive review modes.

## 9. Candidate Download

- [x] 9.1 Add a current-candidate download action with safe filenames.
- [x] 9.2 Add ArrowRight and visible download controls in normal and immersive review modes.
- [x] 9.3 Ensure downloading does not change candidate state or decision history.

## 10. Candidate Queue Performance

- [x] 10.1 Use thumbnail images for normal and immersive candidate queues.
- [x] 10.2 Keep primary review images and immersive review images loading the original full-resolution image.
- [x] 10.3 Preload a small bounded number of upcoming original images for smoother review transitions.
- [x] 10.4 Show a loading indication while the primary review image or immersive review image loads the original image.
