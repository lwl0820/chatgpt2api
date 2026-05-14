## Context

Image selection sessions are stored as `image-selection-session` backend session records and normalized in `web/src/store/image-selection-sessions.ts`. The selection page already has a session configuration dialog for title, queue length, and consecutive failure limit, while `services/image_selection_queue_service.py` reads the persisted session prompt each time it submits a new candidate generation task.

## Goals / Non-Goals

**Goals:**

- Let users edit the current selection session prompt from the existing configuration dialog.
- Persist the edited prompt with the rest of the session configuration.
- Ensure newly submitted candidate generation tasks use the edited prompt.
- Keep existing candidates, decision history, status, and configured limits intact when the prompt changes.

**Non-Goals:**

- Do not rewrite prompts on candidates or tasks that were already submitted.
- Do not create a separate prompt history or per-candidate prompt attribution UI.
- Do not change image task APIs or global image conversation behavior.

## Decisions

- Extend the existing configuration dialog instead of adding a separate prompt editor. This keeps all mutable session settings in one place and avoids introducing a second save flow.
- Treat prompt edits as normal session configuration persistence. The frontend should update `session.prompt` through the existing session update path, and the backend queue service can continue reading `session.get("prompt")` when submitting replacements.
- Require a non-empty prompt when saving configuration. This preserves the existing invariant that a selection session is built around a usable prompt and prevents the queue service from submitting empty generation requests.
- Leave existing candidates untouched after a prompt change. Already submitted or ready candidates represent prior requests; only future queue-fill submissions should reflect the edited prompt.

## Risks / Trade-offs

- Existing candidates may visually coexist with future candidates generated from a different prompt -> Mitigation: make the edited prompt apply only to new submissions and preserve current selection state without retroactive mutation.
- A running session can submit new candidates shortly after saving the prompt -> Mitigation: persist the prompt before closing the dialog; the queue service already reads the latest saved session record for each submission cycle.
- Empty or whitespace-only prompt edits could create unusable sessions -> Mitigation: validate and reject empty prompt values in the configuration save handler.

## Migration Plan

- No persisted data migration is required because existing sessions already contain a `prompt` field.
- Existing sessions continue loading through current normalization. The edit UI should initialize from the stored prompt.
- Rollback is limited to hiding/removing the prompt field from the configuration dialog; persisted prompt values remain compatible.

## Open Questions

- None.
