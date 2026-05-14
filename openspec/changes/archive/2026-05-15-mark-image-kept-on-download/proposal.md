## Why

Users can download the current image candidate during selection, but the download action currently leaves the candidate undecided. When a user deliberately saves a candidate via the right/download action, the selection workflow should treat that image as worth keeping so session results stay aligned with user intent.

## What Changes

- Change the image selection download action so it also marks the current ready candidate as kept.
- Preserve the existing download behavior: the candidate image is still downloaded when the user triggers the download control or shortcut.
- Advance/refill the candidate queue using the same semantics as an explicit keep decision.
- Record the keep decision in undo history so the user can undo the state change if needed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `image-selection-workflow`: Downloading the current candidate becomes a keep decision instead of a state-neutral action.

## Impact

- Affects the image selection page's download action handling and any shared candidate decision logic.
- Updates the `image-selection-workflow` OpenSpec requirements for candidate decision controls.
- No API, storage schema, or dependency changes are expected.
