## Why

Session state is currently managed primarily in the frontend, which makes conversation continuity dependent on browser-local state and limits consistency across refreshes, devices, and API-driven usage. Moving session management to the backend creates a single authoritative source for sessions and prepares the app for more reliable multi-client and server-side workflows.

## What Changes

- Add backend-owned session lifecycle management for chat conversations.
- Persist conversation/session metadata on the server instead of relying on frontend-only state.
- Expose backend APIs for creating, loading, updating, and listing sessions as needed by the UI.
- Update the frontend to consume backend session APIs and treat server session IDs as canonical.
- Treat previously saved frontend-local sessions as nonexistent; no migration or import will be provided.
- Move image-selection queue filling and task-result synchronization to the backend so running sessions continue while the browser is closed.

## Capabilities

### New Capabilities
- `backend-session-management`: Backend-owned lifecycle, persistence, and retrieval of chat sessions.

### Modified Capabilities
- None.

## Impact

- Backend API routes and services responsible for chat/session state.
- Backend worker/service responsible for running image-selection session queues.
- Frontend conversation/session state management and API integration.
- Any persistence layer or storage abstraction used for conversation metadata.
- Tests covering session creation, retrieval, update, deletion, and frontend/backend integration.
