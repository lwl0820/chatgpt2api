## Why

Image selection sessions currently keep using the prompt captured when the session was created, even after users revise their intent while configuring the session. Allowing the prompt to be edited in session configuration lets subsequent generated candidates follow the updated direction without requiring a new selection session.

## What Changes

- Allow users to edit the prompt from the image selection session configuration UI.
- Persist the edited prompt on the current selection session.
- Ensure newly submitted generation requests for that selection session use the latest persisted prompt.
- Preserve existing generated candidates, kept/discarded decisions, and session limits when the prompt is edited.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `image-selection-workflow`: Session configuration requirements now include editing the prompt and using the updated prompt for subsequent generation requests.

## Impact

- Affects the image selection session configuration UI and state persistence.
- Affects the candidate generation submission path for image selection sessions.
- No API or dependency changes are expected unless existing local session persistence helpers require a schema update.
