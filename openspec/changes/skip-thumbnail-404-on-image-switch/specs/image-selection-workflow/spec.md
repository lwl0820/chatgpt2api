## MODIFIED Requirements

### Requirement: Candidate queue uses thumbnails
The system SHALL use thumbnail image URLs when available in the normal or immersive candidate queue. When a candidate has already been loaded through the original image path because its thumbnail is unavailable, the system SHALL remember that thumbnail-unavailable state for that candidate and SHALL load the original image directly on subsequent transitions without issuing another thumbnail request or waiting for a 404. The primary review image and immersive review image remain full resolution.

#### Scenario: Candidate with thumbnail still uses thumbnail
- **WHEN** a ready candidate has a valid thumbnail image URL
- **THEN** the system SHALL use that thumbnail URL in the normal or immersive candidate queue

#### Scenario: Known thumbnail-missing candidate skips probe
- **WHEN** a candidate has already been loaded through the original image path because its thumbnail was unavailable
- **THEN** the system SHALL load that candidate directly from the original image path on later transitions
- **AND** the system SHALL NOT issue another thumbnail request for that candidate
- **AND** the system SHALL NOT wait for a thumbnail 404 before showing the original image

#### Scenario: Revisiting a candidate does not retry a known-missing thumbnail
- **WHEN** the user switches away from and later returns to a candidate whose thumbnail-unavailable state is already known
- **THEN** the system SHALL reuse the known original-image path immediately
- **AND** the system SHALL NOT re-request the thumbnail URL
