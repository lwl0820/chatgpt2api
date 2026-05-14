## 1. Frontend Session Configuration

- [x] 1.1 Add editable prompt state for the selected image selection session configuration dialog.
- [x] 1.2 Initialize the configuration prompt field from the selected session when opening the dialog.
- [x] 1.3 Render a prompt textarea in the existing configuration dialog with clear copy that the updated prompt applies to future candidates.
- [x] 1.4 Validate that the prompt is non-empty before saving and keep the dialog open with user feedback when invalid.
- [x] 1.5 Persist the trimmed prompt along with title, queue length, and consecutive failure limit without changing candidates or decision history.

## 2. Generation Behavior

- [x] 2.1 Confirm the backend queue service submits new candidates using the latest persisted `session.prompt`.
- [x] 2.2 Add or update backend queue service coverage proving submissions after a session prompt edit use the edited prompt.

## 3. Verification

- [x] 3.1 Run the relevant Python tests for image selection queue behavior.
- [x] 3.2 Run the frontend build or type-check equivalent available in the project.
- [x] 3.3 Manually verify that editing a prompt in an existing selection session leaves existing candidates intact and causes subsequent candidates to use the edited prompt.
