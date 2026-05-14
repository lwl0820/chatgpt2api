## ADDED Requirements

### Requirement: Backend-owned session persistence
The system SHALL persist image conversation and image-selection session documents on the backend as the authoritative session store for each authenticated identity.

#### Scenario: Create a new backend session
- **WHEN** an authenticated client creates an image conversation or image-selection session
- **THEN** the backend SHALL persist the session under the caller's identity and return the canonical session document including its session ID and timestamps

#### Scenario: Update an existing backend session
- **WHEN** an authenticated client updates a session owned by the caller
- **THEN** the backend SHALL persist the updated document and update the session's modification timestamp

#### Scenario: List backend sessions
- **WHEN** an authenticated client requests its sessions
- **THEN** the backend SHALL return only sessions owned by the caller sorted by most recently updated first

### Requirement: Session ownership isolation
The system SHALL prevent one identity from reading, updating, or deleting sessions owned by another identity.

#### Scenario: Access another user's session
- **WHEN** an authenticated client requests a session ID that belongs to a different identity
- **THEN** the backend SHALL respond as if the session is unavailable to the caller

#### Scenario: Unauthenticated session access
- **WHEN** a client calls a backend session API without valid authentication
- **THEN** the backend SHALL reject the request before reading or mutating session data

### Requirement: Frontend uses backend session APIs
The frontend SHALL treat backend session APIs as the source of truth for image conversations and image-selection sessions after authentication succeeds.

#### Scenario: Load sessions after authentication
- **WHEN** the authenticated image UI initializes
- **THEN** it SHALL load session lists from backend APIs instead of relying on browser-local storage as the authoritative source

#### Scenario: Persist session changes
- **WHEN** the user creates, renames, updates, or deletes a session in the frontend
- **THEN** the frontend SHALL send the change to the backend session API and update its in-memory view from the backend result

### Requirement: Legacy local sessions are ignored
The system SHALL treat existing browser-local image conversations and image-selection sessions as nonexistent after backend session management is enabled.

#### Scenario: Existing local sessions are present
- **WHEN** an authenticated client has browser-local image conversation or image-selection session data from before this change
- **THEN** the frontend SHALL ignore that data and display only sessions returned by the backend

#### Scenario: No backend sessions exist
- **WHEN** an authenticated client has no backend sessions
- **THEN** the frontend SHALL show an empty session state even if legacy browser-local session data exists

### Requirement: Backend runs image-selection queues
The system SHALL continue filling running image-selection session queues and syncing task results on the backend after the frontend is closed.

#### Scenario: Browser closes during a running selection session
- **WHEN** an image-selection session has `status` set to `running` and has fewer active candidates than its queue limit
- **THEN** the backend SHALL submit additional image generation tasks until the active candidate count reaches the queue limit

#### Scenario: Submitted image tasks complete while browser is closed
- **WHEN** a backend-submitted candidate task reaches a terminal status
- **THEN** the backend SHALL update the corresponding candidate in the image-selection session with ready image data or an error

#### Scenario: Consecutive failures reach the session limit
- **WHEN** backend queue processing observes consecutive candidate errors greater than or equal to the session failure limit
- **THEN** the backend SHALL pause the image-selection session and persist the latest error state

### Requirement: Frontend updates remain bounded
The frontend SHALL avoid per-candidate image-task polling for backend-managed image-selection sessions.

#### Scenario: Running session has many loading candidates
- **WHEN** the selected image-selection session is running with many candidates
- **THEN** the frontend SHALL receive selected-session updates from the backend without polling `/api/image-tasks` for each loading candidate

#### Scenario: Stream reconnects after interruption
- **WHEN** the selected-session event stream is interrupted
- **THEN** the frontend SHALL reconnect to a single selected-session stream rather than opening overlapping connections

### Requirement: Selected session updates are pushed
The system SHALL push selected image-selection session updates to the frontend so stale polling responses do not overwrite user decisions.

#### Scenario: Backend session changes while selected
- **WHEN** the selected image-selection session is saved by a user action or backend worker
- **THEN** the backend SHALL publish the latest session document to subscribers of that session

#### Scenario: User decision is saved optimistically
- **WHEN** the user keeps or discards a candidate while subscribed to the session stream
- **THEN** the frontend SHALL not apply an older streamed session snapshot over the newer local decision

#### Scenario: Selected session is deleted
- **WHEN** the selected image-selection session is deleted
- **THEN** the backend SHALL publish a delete event and the frontend SHALL remove that session from its local view

### Requirement: Worker preserves candidate decisions
The backend queue worker SHALL preserve user decisions when saving task reconciliation updates.

#### Scenario: Candidate was discarded while worker processed an older snapshot
- **WHEN** the worker saves updates based on a snapshot where a candidate was ready but the latest persisted session marks that candidate as discarded
- **THEN** the saved session SHALL keep that candidate discarded while applying other task-result updates

### Requirement: Development image paths resolve through backend proxy
The development frontend SHALL proxy backend image asset paths so persisted same-origin URLs work while running Next and FastAPI on different local ports.

#### Scenario: Image candidate has a same-origin image path in development
- **WHEN** the frontend runs in development and displays a candidate URL beginning with `/images/`
- **THEN** the Next development server SHALL proxy the image request to the backend image route

#### Scenario: Candidate thumbnail is requested in development
- **WHEN** the frontend runs in development and requests `/image-thumbnails/` for a generated image
- **THEN** the Next development server SHALL proxy the thumbnail request to the backend thumbnail route
