## Context

The web app currently stores image conversations and image-selection sessions in browser-local `localforage` stores. This keeps session lifecycle and merge behavior in frontend modules such as `web/src/store/image-conversations.ts` and `web/src/store/image-selection-sessions.ts`, while the backend already owns authenticated image task execution through `/api/image-tasks` and `ImageTaskService`.

Because frontend storage is browser-local, sessions can disappear across browsers, are difficult to recover after local storage loss, and cannot be treated as authoritative by backend APIs. The backend already has identity-aware request handling and file-backed task persistence, so session ownership should move to the server while the UI remains responsible for rendering and optimistic interaction.

## Goals / Non-Goals

**Goals:**

- Introduce backend-owned persistence for image conversations and image-selection sessions.
- Add authenticated APIs for listing, creating, updating, retrieving, and deleting sessions owned by the current identity.
- Keep frontend state as an in-memory view/cache of backend sessions rather than the authoritative store.
- Preserve existing session shapes where practical so UI migration is incremental.
- Ignore previously saved browser-local sessions; backend session storage starts empty for each identity until new server-backed sessions are created.
- Keep running image-selection sessions active on the backend by filling queue slots and syncing image task results without requiring an open browser tab.

**Non-Goals:**

- Reworking image task execution or image generation semantics.
- Adding collaborative editing, sharing, or cross-user session access.
- Replacing the repository storage backend system globally.
- Migrating browser-local session data, settings, auth, account state, or other unrelated frontend state.

## Decisions

1. Add a dedicated backend session service instead of folding sessions into image tasks.

   Image tasks represent asynchronous generation work, while conversations and selection sessions are user-facing UI aggregates that reference task IDs, prompts, decisions, and display metadata. Keeping a separate service avoids coupling task retention or execution status to session lifecycle. The alternative was to enrich `ImageTaskService`, but that would mix task execution concerns with editable session documents.

2. Store sessions per authenticated identity and enforce ownership in the API layer.

   All session APIs will resolve identity with the same auth path used by image task APIs. Storage keys will include owner ID so one user cannot access another user's sessions. The alternative was unauthenticated global session storage, but that would regress existing authorization expectations.

3. Use server-issued canonical session IDs for all new sessions and do not import legacy local IDs.

   New sessions should be created through the backend so the server is authoritative from the beginning. Existing `localforage` sessions are intentionally ignored and treated as absent to avoid migration complexity and stale local state. The alternative was importing legacy IDs, but that would add collision handling and state reconciliation for data that is acceptable to discard.

4. Keep client-side normalization as compatibility code only at the API boundary.

   The frontend may continue normalizing backend-loaded session payloads before rendering, but save/list/delete operations should call backend APIs. It should not read old `localforage` sessions for this feature. The alternative was a big-bang frontend rewrite, which would increase implementation risk.

5. Persist full session documents initially, then evolve schema only when requirements demand it.

   The existing UI already has defined document shapes for image conversations and image-selection sessions. Persisting these as validated documents avoids premature relational modeling. The alternative was a normalized backend schema, but there is no current requirement for cross-session querying beyond owner-scoped listing and retrieval.

6. Run a backend image-selection queue worker alongside the FastAPI app.

   The worker scans backend-owned image-selection sessions with `status=running`, reconciles loading candidates with existing image task results, and submits new image generation tasks until each session reaches its queue limit. This keeps selection sessions progressing when the browser is closed. The alternative was keeping queue filling in React effects, but that would make continuous generation dependent on an open tab.

7. Keep frontend refresh bounded to the current backend session.

   Since the backend worker owns task-state reconciliation, the frontend should not poll `/api/image-tasks` for every loading candidate. The running selection UI should refresh only the selected session document, skip overlapping refreshes, and use the backend-computed candidate state. This prevents large queues from exhausting browser connection limits.

8. Proxy image asset paths in development instead of rewriting persisted URLs.

   Backend-generated selection candidates may store same-origin image paths such as `/images/...`, which are correct in production when FastAPI serves the exported frontend and image assets from the same origin. In local development, Next runs on port 3000 and FastAPI on port 8000, so Next should proxy `/images/*` and `/image-thumbnails/*` to the backend rather than persisting development-only absolute URLs.

## Risks / Trade-offs

- Existing frontend-local sessions disappear from the UI -> This is intentional for this change; communicate by treating backend session lists as authoritative and empty when no server sessions exist.
- Large session payloads from embedded reference images -> Validate request sizes and consider excluding or externalizing large blobs if payload limits are hit.
- Running frontend-local sessions cannot be resumed -> This is intentional because local sessions are discarded rather than migrated.
- Backend queue worker may race with frontend user decisions -> Keep worker updates narrow to loading/error/new-candidate fields and preserve kept/discarded decisions when recalculating queue state.
- Large queues can overload the browser if the frontend polls task status per candidate -> Remove frontend task polling and refresh only the current backend session with an in-flight guard.
- Development image URLs can point at the Next dev server instead of FastAPI -> Add development-only rewrites for image asset routes while keeping production same-origin behavior.
- Storage corruption affects all clients for a user -> Keep writes serialized in the backend service and validate session documents before persistence.
- Backend persistence format may need future migration -> Include document `kind` and timestamps so future storage migrations can distinguish conversation and selection-session records.

## Migration Plan

1. Add backend session service and API routes behind existing authentication.
2. Add frontend API client methods for session CRUD.
3. Update image conversation and selection-session stores to load and persist via backend APIs.
4. Add a backend image-selection queue worker that starts and stops with the app lifespan.
5. Remove frontend-owned queue filling and frontend image-task polling; refresh only the selected backend session for UI updates.
6. Add development-only proxy rewrites for image and thumbnail asset paths.
7. Stop reading existing `localforage` sessions for image conversations and image-selection sessions.
8. Leave old local data untouched but unused; no import marker or cleanup workflow is required.

## Open Questions

- Should backend session retention follow image retention settings, or should sessions have separate retention behavior?
