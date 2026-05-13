## 1. Backend Session Service

- [x] 1.1 Add a backend session service that persists owner-scoped image conversation and image-selection session documents with serialized writes.
- [x] 1.2 Add validation and normalization for session kind, ID, timestamps, and payload shape before saving documents.
- [x] 1.3 Implement owner-scoped list, get, create/update, and delete service methods sorted by latest update time.

## 2. Backend API

- [x] 2.1 Add authenticated API routes for listing and retrieving backend sessions for the current identity.
- [x] 2.2 Add authenticated API routes for creating/updating and deleting sessions owned by the current identity.
- [x] 2.3 Register the new session router in the FastAPI application.

## 3. Frontend API And Stores

- [x] 3.1 Add typed frontend API client methods for backend session list, get, save, and delete operations.
- [x] 3.2 Update image conversation storage functions to use backend APIs as the authoritative store after authentication.
- [x] 3.3 Update image-selection session storage functions to use backend APIs as the authoritative store after authentication.
- [x] 3.4 Keep frontend normalization at API boundaries so existing UI code can consume backend-loaded documents safely.

## 4. Legacy Local Session Discard

- [x] 4.1 Stop reading `localforage` image conversations and image-selection sessions as authoritative session sources.
- [x] 4.2 Ensure existing browser-local sessions are not submitted to the backend and do not appear in the UI unless recreated as backend sessions.
- [x] 4.3 Leave old local data untouched but unused; do not add import markers or cleanup workflows.

## 5. Verification

- [x] 5.1 Add backend tests for create/update/list/delete behavior and ownership isolation.
- [x] 5.2 Add frontend or integration tests for loading sessions from backend APIs and persisting session mutations.
- [x] 5.3 Add frontend coverage that legacy local session data is ignored once backend session management is enabled.
- [x] 5.4 Run the relevant backend and frontend test suites and fix any regressions.

## 6. Backend Image-Selection Queue Runner

- [x] 6.1 Add a backend worker that scans running image-selection sessions and syncs loading candidates from image task results.
- [x] 6.2 Have the backend worker submit new image generation tasks until each running session reaches its queue limit.
- [x] 6.3 Start and stop the backend worker from the FastAPI lifespan.
- [x] 6.4 Remove frontend-owned queue filling so the UI no longer controls continuous generation.
- [x] 6.5 Add backend tests for queue filling, result syncing, and failure-limit pausing.

## 7. Frontend Refresh And Development Assets

- [x] 7.1 Remove frontend image-task polling from the image-selection page.
- [x] 7.2 Refresh only the selected backend image-selection session while it is running.
- [x] 7.3 Prevent overlapping selected-session refresh requests from accumulating in the browser.
- [x] 7.4 Add development-only Next rewrites for `/images/*` and `/image-thumbnails/*` backend asset paths.
