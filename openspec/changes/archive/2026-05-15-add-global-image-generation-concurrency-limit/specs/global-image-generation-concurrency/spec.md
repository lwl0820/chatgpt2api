## ADDED Requirements

### Requirement: Global image concurrency setting
The system SHALL provide an admin setting that configures the maximum number of image generation tasks allowed to run concurrently across the whole system.

#### Scenario: Admin loads settings
- **WHEN** an admin loads system settings
- **THEN** the response SHALL include the current global image concurrency value, defaulting to `3` when absent from stored configuration

#### Scenario: Admin saves valid global concurrency
- **WHEN** an admin saves a positive integer global image concurrency value
- **THEN** the system SHALL persist the normalized value and use it for subsequent image task scheduling

#### Scenario: Missing or invalid global concurrency
- **WHEN** the stored or submitted global image concurrency value is missing, zero, negative, or not numeric
- **THEN** the system SHALL normalize it to a safe positive default or minimum value before exposing or using it

#### Scenario: Settings UI exposes global concurrency
- **WHEN** an admin opens the settings UI
- **THEN** the UI SHALL allow viewing and editing the global image concurrency value alongside the existing image task settings

### Requirement: Global image task scheduling limit
The system SHALL prevent more than the configured global image concurrency number of local image tasks from running upstream image generation or edit handlers at the same time.

#### Scenario: Tasks below the global limit
- **WHEN** fewer image tasks are running than the configured global image concurrency value and a new image task is submitted
- **THEN** the system SHALL allow that task to transition from `queued` to `running` and start the upstream image operation

#### Scenario: Tasks at the global limit
- **WHEN** the configured number of image tasks are already running and another image task is submitted
- **THEN** the system SHALL keep the additional task in `queued` status without starting its upstream image operation

#### Scenario: Running task releases a global slot
- **WHEN** a running image task reaches `success` or `error` while queued image tasks exist
- **THEN** the system SHALL start a queued image task if the number of running tasks is below the current global concurrency value

#### Scenario: Global limit applies to all local image task modes
- **WHEN** image generation and image edit tasks are submitted through the local image task service
- **THEN** both task modes SHALL count against the same global image concurrency limit

#### Scenario: Global and per-account limits both apply
- **WHEN** an image task is allowed to run by the global concurrency limit
- **THEN** the existing per-account image concurrency limit SHALL still be enforced before selecting or using an upstream image account

#### Scenario: Lowering the global limit during running tasks
- **WHEN** the configured global image concurrency value is lowered below the number of currently running image tasks
- **THEN** the system SHALL NOT start additional queued image tasks until enough running tasks finish to bring running count below the new configured value

### Requirement: Queued image task observability
The system SHALL preserve existing image task API semantics while using the global image concurrency queue.

#### Scenario: Queued task is visible to polling
- **WHEN** a submitted image task is waiting for a global concurrency slot
- **THEN** image task polling SHALL return that task with `queued` status and its public task metadata

#### Scenario: Duplicate task submission while queued
- **WHEN** the same owner submits the same `client_task_id` for an image task that is still queued
- **THEN** the system SHALL return the existing queued task instead of creating or scheduling a duplicate task

#### Scenario: Queued task eventually completes
- **WHEN** a queued image task later obtains a global slot and its upstream operation succeeds or fails
- **THEN** the system SHALL update the task to the same terminal success or error shape used by existing image task behavior

#### Scenario: Service restarts with unfinished tasks
- **WHEN** the image task service starts and finds persisted queued or running tasks from a previous process
- **THEN** the system SHALL mark those unfinished tasks as interrupted errors using the existing recovery semantics
