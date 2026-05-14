## MODIFIED Requirements

### Requirement: Configurable selection session
The system SHALL allow users to configure the session title, prompt, candidate queue length, and consecutive failure pause limit when creating or editing an image selection session.

#### Scenario: Create with session limits
- **WHEN** the user starts an image selection session with valid queue length and consecutive failure pause values
- **THEN** the system SHALL store those values on that selection session and use them for queue fill and failure pause behavior

#### Scenario: Missing session limits
- **WHEN** session limit values are missing or invalid
- **THEN** the system SHALL use safe default values for queue length and consecutive failure pause behavior

#### Scenario: Update current session configuration
- **WHEN** the user updates the title, queue length, or consecutive failure pause value for the current selection session
- **THEN** the system SHALL persist the new values to that session and use the updated limits for subsequent queue fill and failure pause behavior

#### Scenario: Update current session prompt
- **WHEN** the user updates the prompt for the current selection session to a non-empty value
- **THEN** the system SHALL persist the new prompt to that session and use it for subsequent generation requests

#### Scenario: Reject empty session prompt update
- **WHEN** the user attempts to save an empty or whitespace-only prompt for the current selection session
- **THEN** the system SHALL reject the update and keep the previously persisted prompt

#### Scenario: Existing candidates remain unchanged after prompt update
- **WHEN** the user updates the prompt for a selection session that already has loading, ready, kept, discarded, or error candidates
- **THEN** the system SHALL keep existing candidates and decision history unchanged while applying the new prompt only to later generation requests
