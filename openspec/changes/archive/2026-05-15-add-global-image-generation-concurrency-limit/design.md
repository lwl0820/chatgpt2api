## Context

Image task creation currently persists a task as `queued` and immediately starts a daemon thread. The thread updates the task to `running`, calls either the generation or edit handler, and then records `success` or `error`. Existing account selection already enforces `image_account_concurrency` per access token in `AccountService`, but there is no system-wide cap across all image task sources.

The settings path is already permissive and centralized: `/api/settings` returns `config.get()`, accepts extra fields through `SettingsUpdateRequest`, and `ConfigStore.update()` persists settings. The settings UI normalizes and saves image-related numeric fields in `web/src/app/settings/store.ts`, and renders image settings in `ConfigCard`.

## Goals / Non-Goals

**Goals:**
- Add an admin-configurable positive integer setting for global concurrent image generation tasks.
- Enforce the limit across normal image generation, image edits, and image-selection queue submissions because they all flow through `ImageTaskService`.
- Keep submitted-but-not-started tasks observable as `queued` through the existing image task polling API.
- Preserve existing task ownership, duplicate `client_task_id` behavior, logging, cleanup, and per-account concurrency behavior.

**Non-Goals:**
- No per-user, per-model, or per-session concurrency limits.
- No cancellation, priority queueing, or ETA reporting for queued tasks.
- No change to OpenAI-compatible synchronous image endpoints outside the local image task service unless they already submit through `ImageTaskService`.

## Decisions

1. Store the setting as `image_global_concurrency` with a default of `3` and a minimum of `1`.

   Rationale: the project already uses `image_account_concurrency` for the per-account limit, so this name clearly distinguishes system-wide concurrency from per-account concurrency. A default of `3` preserves current small-deployment safety without allowing zero-capacity deadlocks.

   Alternative considered: reuse `image_account_concurrency` as an implicit global limit. This was rejected because it would change the meaning of an existing setting and make multi-account capacity ambiguous.

2. Enforce the limit inside `ImageTaskService` before calling the image generation or edit handler.

   Rationale: all asynchronous local image task creation paths converge there, including image-selection queue submissions. Keeping the control at the task service preserves API behavior and avoids scattering concurrency checks across routes and queue services.

   Alternative considered: enforce in API routes only. This was rejected because background selection sessions submit directly through the service and would bypass route-level enforcement.

3. Use service-owned scheduling instead of starting a thread for every queued task.

   Rationale: `submit_generation()` and `submit_edit()` can persist a task as `queued`, keep the payload in memory, and call a private scheduler that starts only the oldest queued tasks up to `config.image_global_concurrency`. When a running task reaches a terminal state, the scheduler starts the next queued task. This limits active handler calls and avoids creating unbounded blocked worker threads.

   Alternative considered: start a thread immediately and block it on a semaphore. This is simpler but still allows unbounded waiting threads under load, which weakens the resource-protection value of a global limit.

4. Keep queued payloads in memory only and continue marking unfinished persisted tasks as interrupted on service startup.

   Rationale: the current service already treats `queued` and `running` persisted tasks as interrupted after restart because handler payloads are not persisted. Persisting prompts and uploaded image bytes for durable delayed execution would be a larger data-model change with privacy and storage implications.

   Alternative considered: persist full task payloads. This was rejected as out of scope for a concurrency setting and unnecessary for parity with current restart behavior.

5. Re-read the configured limit when scheduling tasks rather than caching it permanently.

   Rationale: saving settings should affect subsequent scheduling without restarting the backend. If the limit is lowered below current running count, existing running tasks continue and new tasks wait until active count drops below the new limit.

   Alternative considered: resize a long-lived semaphore. This is more error-prone when the configured limit changes while tasks are running.

## Risks / Trade-offs

- Lowering the setting does not preempt already running image tasks -> Mitigation: apply the new limit to future task starts and document that in code/tests.
- Queued task payloads are memory-only -> Mitigation: preserve existing startup recovery semantics by marking unfinished tasks as interrupted after restart.
- Very large uploaded edit images can remain in memory while queued -> Mitigation: the global queue should be bounded indirectly by callers and existing task retention; avoid adding durable binary persistence in this change.
- A bug in scheduler bookkeeping could leave queued tasks stuck -> Mitigation: add unit tests that block one task, verify the second remains queued, then release the first and verify the second runs.

## Migration Plan

- Existing `config.json` files without `image_global_concurrency` load with default value `3`.
- Saving settings writes the normalized field on the next admin settings update.
- Rollback is safe: older code ignores the extra config key because settings are already permissive.

## Open Questions

- None.
