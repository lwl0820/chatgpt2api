## 1. Implementation

- [x] 1.1 Update the image selection download action so a successful current-candidate download marks the same candidate as kept.
- [x] 1.2 Reuse the existing keep decision path so `decidedAt`, bounded undo history, current-candidate advancement, and queue refill behavior match an explicit keep action.
- [x] 1.3 Ensure failed downloads do not change candidate state or decision history.

## 2. Verification

- [x] 2.1 Verify ArrowRight downloads the current ready candidate and marks it kept.
- [x] 2.2 Verify the visible download control downloads the current ready candidate and marks it kept.
- [x] 2.3 Verify undo restores a candidate kept through download back to ready status.
- [x] 2.4 Run the relevant frontend checks or test suite for the image selection page.
