## 1. Candidate Prompt Provenance

- [x] 1.1 Extend the image selection candidate data shape with an optional generation prompt field and normalize persisted sessions without dropping it
- [x] 1.2 Update the image selection queue service to freeze the cleaned session prompt on each newly created loading candidate and submit generation with the same value
- [x] 1.3 Ensure candidate status synchronization preserves the frozen candidate prompt through loading, ready, error, kept, and discarded states
- [x] 1.4 Add backend tests proving new candidates record the submitted prompt and existing candidate prompts are not rewritten after session prompt updates

## 2. Download Prompt Selection

- [x] 2.1 Update the image selection download action to pass `currentCandidate.prompt || selectedSession.prompt` into the shared image download helper
- [x] 2.2 Preserve existing download side effects: mark the downloaded candidate as kept, record undo history, and advance to the next ready candidate
- [x] 2.3 Add frontend coverage for downloading an old candidate after the session prompt changes, verifying the candidate prompt is used when present and session prompt is used only as fallback

## 3. Image Manager Prompt Mapping

- [x] 3.1 Update image prompt lookup for selection-session images to prefer candidate-level generation prompts and fall back to session prompt for historical candidates
- [x] 3.2 Add backend download tests covering single-image or zip downloads for selection candidates with candidate-level prompts and legacy fallback prompts

## 4. Validation

- [x] 4.1 Run the affected backend test suite for image selection queue behavior and image manager download prompt payloads
- [x] 4.2 Run the affected frontend tests for image selection download behavior
- [x] 4.3 Manually verify the core flow: generate candidate with prompt A, edit session prompt to B, download the old candidate with prompt append enabled, and confirm the file tail contains A
