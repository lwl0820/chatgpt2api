## Context

The image selection page already has a single decision path for keeping or discarding the current ready candidate, including status changes, bounded undo history, and queue refill behavior. The current download action is separate: `downloadCurrentCandidate` downloads the image but does not update the candidate status, which leaves downloaded images out of the session's kept set.

## Goals / Non-Goals

**Goals:**

- Treat downloading the current ready candidate as an intentional keep decision.
- Reuse the existing keep decision semantics so undo history, status updates, and queue refill remain consistent.
- Keep the user-facing download action intact for the right-arrow shortcut and visible download control.

**Non-Goals:**

- Do not add new candidate statuses or change the persisted image selection session schema.
- Do not alter discard, undo, thumbnail, immersive mode, or image manager filtering semantics except through the candidate becoming kept.
- Do not change how image files are downloaded or where downloaded browser files are saved.

## Decisions

- Download then keep in the page action handler. The download action should first attempt the existing image download and, after it succeeds, invoke the same keep decision path used by ArrowUp and the keep button. This preserves user expectations that a failed download does not mark the candidate as kept.
- Reuse `decideCurrent("kept")` rather than duplicating session mutation logic. This keeps bounded undo history, `decidedAt`, current candidate advancement, and queue refill behavior aligned with the established keep action.
- Keep the shortcut/control surface unchanged. ArrowRight and the visible download control continue to represent the download action, but the resulting state now matches an explicit keep.

## Risks / Trade-offs

- Download failure could leave the candidate ready even if the user intended to keep it -> Only mark kept after a successful download and show the existing error toast on failure.
- The download action may advance the current candidate after success -> This is intentional because it now follows keep semantics; undo can restore the candidate to ready status.
- Calling the keep path after async download may operate on stale state if the candidate changes during download -> Capture the candidate identity at the start of the action or ensure the decision function still targets the candidate that was downloaded.
