# Attention Map - Product Specification

**Version**: 1.0
**Status**: Draft
**Last Updated**: 2024
**Target**: 48-hour Hackathon MVP

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Product Vision](#3-product-vision)
4. [User Personas](#4-user-personas)
5. [Functional Requirements](#5-functional-requirements)
6. [Non-Functional Requirements](#6-non-functional-requirements)
7. [System Constraints](#7-system-constraints)
8. [Data Specifications](#8-data-specifications)
9. [API Specification](#9-api-specification)
10. [User Interface Specifications](#10-user-interface-specifications)
11. [Security Requirements](#11-security-requirements)
12. [Performance Requirements](#12-performance-requirements)
13. [Future Roadmap](#13-future-roadmap)
14. [Glossary](#14-glossary)

---

## 1. Executive Summary

### 1.1 Product Name
**Attention Map**

### 1.2 Tagline
*Real-time civic incident monitoring for smarter city response*

### 1.3 Description
Attention Map is a platform that enables citizens to report civic incidents (emergencies, traffic accidents, infrastructure issues, public gatherings) via mobile uploads. The system leverages AI to automatically classify and prioritize reports, displaying them on a real-time interactive map for government operators to monitor, triage, and coordinate responses.

### 1.4 Key Value Propositions

| Stakeholder | Value |
|-------------|-------|
| **Citizens** | Easy incident reporting via mobile; gamification rewards engagement |
| **Government Operators** | Real-time situational awareness; AI-assisted prioritization |
| **Emergency Services** | Faster incident detection; volume-based severity signals |
| **City Administration** | Data-driven insights; infrastructure issue tracking |

### 1.5 MVP Scope
- Municipal deployment (single city)
- Mobile web upload interface
- AI-powered classification (text + vision)
- Real-time operator dashboard with live map
- Basic triage workflow
- Badge-based gamification

---

## 2. Problem Statement

### 2.1 Current Challenges

1. **Delayed Incident Awareness**: Government agencies often learn about incidents from traditional channels (phone calls, social media monitoring) with significant delays.

2. **Information Fragmentation**: Citizen reports are scattered across multiple platforms (Twitter, Telegram, phone hotlines) with no unified view.

3. **Manual Prioritization**: Operators manually assess incident severity, leading to inconsistent triage and potential missed emergencies.

4. **Volume Blindness**: Traditional systems treat each report independently, missing the signal that multiple simultaneous reports indicate a major incident.

5. **Citizen Disengagement**: Lack of feedback or recognition discourages repeat reporting.

### 2.2 Opportunity

Smartphones with GPS and cameras are ubiquitous. Citizens are already capturing and sharing incident content on social media. By providing a dedicated platform with:
- Frictionless upload experience
- Automatic location capture
- AI-powered classification
- Real-time operator visibility
- Gamified engagement

...we can transform passive bystanders into an active civic sensor network.

---

## 3. Product Vision

### 3.1 Vision Statement

> Enable every citizen to contribute to city safety by making incident reporting instant, intelligent, and impactful.

### 3.2 Success Metrics (MVP)

| Metric | Target | Measurement |
|--------|--------|-------------|
| Upload Success Rate | >95% | Successful uploads / attempts |
| Classification Accuracy | >80% | Verified category matches AI prediction |
| Time to Dashboard | <60 seconds | Upload timestamp to SSE broadcast |
| Operator Response Time | <5 minutes | Event appears to status change |
| Demo Wow Factor | Qualitative | Hackathon judge feedback |

### 3.3 Long-term Vision (Post-MVP)

- Multi-city and national deployment
- Integration with emergency dispatch systems (CAD)
- Multi-source ingestion (Twitter, Telegram, CCTV)
- Predictive analytics and hotspot identification
- Mobile native apps (iOS/Android)
- API access for third-party integrations

---

## 4. User Personas

### 4.1 Citizen Reporter (Primary)

**Name**: Maria, 32
**Role**: Warsaw resident, daily commuter
**Tech Savvy**: Medium (uses smartphone daily, social media active)

**Goals**:
- Report incidents quickly without complex forms
- Know that her report was received and matters
- Feel recognized for civic contribution

**Pain Points**:
- Doesn't know which agency to contact for different issues
- Previous reports via hotlines felt like shouting into void
- No feedback on whether anything was done

**Scenarios**:
1. Witnesses a car accident, wants to report immediately
2. Notices a pothole on daily route, reports during commute
3. Sees smoke from a building, uploads video while calling emergency

### 4.2 Government Operator (Primary)

**Name**: Tomasz, 45
**Role**: Warsaw City Emergency Coordination Center
**Tech Savvy**: Medium-High (uses GIS systems, dispatch software)

**Goals**:
- See all active incidents in real-time on a single screen
- Quickly identify high-priority situations
- Efficiently triage and route to appropriate responders

**Pain Points**:
- Switching between multiple information sources
- Missing incidents buried in social media noise
- Difficulty assessing severity from text-only reports

**Scenarios**:
1. Monitoring dashboard during normal shift
2. Multiple reports appear in same area - identifies cluster as major incident
3. Verifies AI classification, marks as confirmed, dispatches response

### 4.3 Anonymous Contributor (Secondary)

**Name**: Anonymous
**Role**: Privacy-conscious citizen
**Tech Savvy**: Variable

**Goals**:
- Report sensitive incidents without identification
- Contribute to civic good without creating digital footprint

**Pain Points**:
- Fear of retaliation for reporting certain incidents
- Distrust of government data collection

**Scenarios**:
1. Reports suspicious activity but doesn't want to be identified
2. Documents protest or police activity anonymously

---

## 5. Functional Requirements

### 5.1 Upload System (FR-UP)

| ID | Requirement | Priority | MVP |
|----|-------------|----------|-----|
| FR-UP-01 | System SHALL accept image uploads (JPEG, PNG, HEIC) up to 20MB | Must | ✓ |
| FR-UP-02 | System SHALL accept video uploads (MP4, MOV) up to 100MB | Must | ✓ |
| FR-UP-03 | System SHALL capture GPS coordinates from device | Must | ✓ |
| FR-UP-04 | System SHALL accept optional text description (max 500 chars) | Must | ✓ |
| FR-UP-05 | System SHALL support anonymous uploads (no auth required) | Must | ✓ |
| FR-UP-06 | System SHALL support authenticated uploads (optional login) | Should | ✓ |
| FR-UP-07 | System SHALL show upload progress indicator | Must | ✓ |
| FR-UP-08 | System SHALL confirm successful upload with event ID | Must | ✓ |
| FR-UP-09 | System SHALL handle upload failures gracefully with retry option | Should | ✓ |
| FR-UP-10 | System SHALL support camera capture directly from browser | Must | ✓ |

### 5.2 Classification System (FR-CL)

| ID | Requirement | Priority | MVP |
|----|-------------|----------|-----|
| FR-CL-01 | System SHALL classify events into predefined categories | Must | ✓ |
| FR-CL-02 | System SHALL assign severity score (1-4) to each event | Must | ✓ |
| FR-CL-03 | System SHALL provide AI reasoning/explanation for classification | Should | ✓ |
| FR-CL-04 | System SHALL classify based on text description when provided | Must | ✓ |
| FR-CL-05 | System SHALL classify based on visual content analysis | Must | ✓ |
| FR-CL-06 | System SHALL merge text and vision classifications intelligently | Must | ✓ |
| FR-CL-07 | System SHALL assign confidence score (0-1) to classification | Should | ✓ |
| FR-CL-08 | System SHALL suggest appropriate responder type | Could | ✓ |
| FR-CL-09 | System SHALL process classification within 30 seconds | Must | ✓ |
| FR-CL-10 | System SHALL handle classification failures with fallback | Must | ✓ |

### 5.3 Clustering System (FR-CS)

| ID | Requirement | Priority | MVP |
|----|-------------|----------|-----|
| FR-CS-01 | System SHALL detect events within 100m radius as related | Must | ✓ |
| FR-CS-02 | System SHALL cluster events within 30-minute time window | Must | ✓ |
| FR-CS-03 | System SHALL calculate cluster centroid for map display | Must | ✓ |
| FR-CS-04 | System SHALL boost severity based on event count in cluster | Must | ✓ |
| FR-CS-05 | System SHALL update cluster metadata when new events join | Must | ✓ |
| FR-CS-06 | System SHALL display cluster event count on map | Should | ✓ |

### 5.4 Map & Dashboard (FR-MD)

| ID | Requirement | Priority | MVP |
|----|-------------|----------|-----|
| FR-MD-01 | System SHALL display events on interactive map | Must | ✓ |
| FR-MD-02 | System SHALL use OpenStreetMap tiles | Must | ✓ |
| FR-MD-03 | System SHALL color-code markers by severity | Must | ✓ |
| FR-MD-04 | System SHALL show category icon on markers | Should | ✓ |
| FR-MD-05 | System SHALL cluster dense markers visually | Must | ✓ |
| FR-MD-06 | System SHALL filter events by category | Must | ✓ |
| FR-MD-07 | System SHALL filter events by severity | Must | ✓ |
| FR-MD-08 | System SHALL filter events by status | Must | ✓ |
| FR-MD-09 | System SHALL show event detail panel on marker click | Must | ✓ |
| FR-MD-10 | System SHALL display event thumbnail in detail panel | Must | ✓ |
| FR-MD-11 | System SHALL display AI reasoning in detail panel | Should | ✓ |
| FR-MD-12 | System SHALL show live event feed sidebar | Must | ✓ |
| FR-MD-13 | System SHALL show summary statistics widgets | Should | ✓ |
| FR-MD-14 | System SHALL update in real-time without page refresh | Must | ✓ |

### 5.5 Real-time Updates (FR-RT)

| ID | Requirement | Priority | MVP |
|----|-------------|----------|-----|
| FR-RT-01 | System SHALL push new events to connected clients | Must | ✓ |
| FR-RT-02 | System SHALL push event status updates to connected clients | Must | ✓ |
| FR-RT-03 | System SHALL use Server-Sent Events (SSE) protocol | Must | ✓ |
| FR-RT-04 | System SHALL automatically reconnect on connection loss | Must | ✓ |
| FR-RT-05 | System SHALL show connection status indicator | Should | ✓ |
| FR-RT-06 | System SHALL animate new event appearance on map | Should | ✓ |

### 5.6 Triage Workflow (FR-TR)

| ID | Requirement | Priority | MVP |
|----|-------------|----------|-----|
| FR-TR-01 | Operator SHALL be able to verify an event as accurate | Must | ✓ |
| FR-TR-02 | Operator SHALL be able to mark event as false alarm | Must | ✓ |
| FR-TR-03 | Operator SHALL be able to mark event as resolved | Must | ✓ |
| FR-TR-04 | System SHALL record operator ID and timestamp for status changes | Should | ✓ |
| FR-TR-05 | System SHALL broadcast status changes to all connected clients | Must | ✓ |
| FR-TR-06 | System SHALL visually indicate status in marker/list | Must | ✓ |

### 5.7 Authentication & Gamification (FR-AG)

| ID | Requirement | Priority | MVP |
|----|-------------|----------|-----|
| FR-AG-01 | System SHALL support user registration (email/password) | Should | ✓ |
| FR-AG-02 | System SHALL support JWT-based authentication | Should | ✓ |
| FR-AG-03 | System SHALL track report count per authenticated user | Should | ✓ |
| FR-AG-04 | System SHALL award badges based on achievements | Should | ✓ |
| FR-AG-05 | System SHALL display earned badges on profile | Should | ✓ |
| FR-AG-06 | System SHALL show badge unlock notification after upload | Could | ✓ |

---

## 6. Non-Functional Requirements

### 6.1 Usability (NFR-US)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-US-01 | Upload flow SHALL complete in ≤3 taps from app launch | 3 taps |
| NFR-US-02 | Mobile UI SHALL be responsive (320px - 768px) | All breakpoints |
| NFR-US-03 | Dashboard SHALL be usable on desktop (1280px+) | Full functionality |
| NFR-US-04 | UI text SHALL be in English (MVP), Polish (future) | English |
| NFR-US-05 | Error messages SHALL be user-friendly, not technical | Plain language |

### 6.2 Performance (NFR-PF)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-PF-01 | Upload API response time | <2 seconds (excluding transfer) |
| NFR-PF-02 | Event list API response time | <500ms for 100 events |
| NFR-PF-03 | SSE event delivery latency | <1 second from broadcast |
| NFR-PF-04 | Map initial render time | <3 seconds |
| NFR-PF-05 | AI classification time | <30 seconds |
| NFR-PF-06 | End-to-end upload to dashboard | <60 seconds |

### 6.3 Scalability (NFR-SC)

| ID | Requirement | MVP Target | Future Target |
|----|-------------|------------|---------------|
| NFR-SC-01 | Concurrent uploads | 50 | 1,000 |
| NFR-SC-02 | Events per day | 500 | 10,000 |
| NFR-SC-03 | Concurrent dashboard users | 10 | 100 |
| NFR-SC-04 | SSE connections | 20 | 500 |
| NFR-SC-05 | Media storage | 50GB | 5TB |

### 6.4 Reliability (NFR-RL)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-RL-01 | System uptime | 99% (MVP acceptable) |
| NFR-RL-02 | Data durability | No event loss after successful upload |
| NFR-RL-03 | Graceful degradation | Dashboard works if AI fails |
| NFR-RL-04 | SSE reconnection | Automatic within 10 seconds |

### 6.5 Compatibility (NFR-CM)

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-CM-01 | Mobile browsers | Chrome, Safari (iOS), Firefox |
| NFR-CM-02 | Desktop browsers | Chrome, Firefox, Edge |
| NFR-CM-03 | Minimum iOS version | iOS 14+ |
| NFR-CM-04 | Minimum Android version | Android 10+ |

---

## 7. System Constraints

### 7.1 Technical Constraints

| Constraint | Description | Rationale |
|------------|-------------|-----------|
| Python/Django | Backend must use Django + Django Ninja | Developer expertise |
| React | Frontend must use React | Developer expertise |
| Docker | Must be containerized with Docker Compose | Portability |
| OpenStreetMap | Must use OSM for map tiles | Free, open data |
| SSE over WebSockets | Real-time via SSE, not Django Channels | Simplicity, past issues with Channels |
| Cloud APIs for AI | Use OpenAI/Claude, no local GPU | No GPU infrastructure |

### 7.2 Business Constraints

| Constraint | Description |
|------------|-------------|
| Timeline | 48-hour hackathon |
| Team | Solo developer |
| Budget | Minimal (free tiers, OSM) |
| Demo Focus | Real-time map + UX over feature breadth |

### 7.3 Regulatory Constraints (Post-MVP)

| Constraint | Applies To |
|------------|------------|
| GDPR | Poland, EU deployment |
| Data Localization | May require EU-hosted infrastructure |
| Content Moderation | User-generated content requires policies |

---

## 8. Data Specifications

### 8.1 Event Categories

| Category | Code | Description | Example Subcategories |
|----------|------|-------------|----------------------|
| Emergency | `emergency` | Life-threatening, immediate response | fire, explosion, collapse, medical |
| Security | `security` | Safety threats, suspicious activity | drone, suspicious_package, break_in |
| Traffic | `traffic` | Road incidents, transportation | car_accident, road_blockage, flooding |
| Protest | `protest` | Public gatherings, demonstrations | march, demonstration, crowd |
| Infrastructure | `infrastructure` | City infrastructure issues | pothole, broken_light, graffiti |
| Environmental | `environmental` | Environmental hazards | pollution, fallen_tree, animal_hazard |
| Informational | `informational` | General observations | observation, positive_report |

### 8.2 Severity Levels

| Level | Code | Label | Description | Response Expectation |
|-------|------|-------|-------------|---------------------|
| 4 | `critical` | Critical | Life-threatening emergency | Immediate dispatch |
| 3 | `high` | High | Urgent, significant impact | Response within 1 hour |
| 2 | `medium` | Medium | Needs attention, not urgent | Response within 24 hours |
| 1 | `low` | Low | Informational only | No immediate action |

### 8.3 Event Status

| Status | Code | Description | Transitions From |
|--------|------|-------------|------------------|
| New | `new` | Just received, pending review | (initial) |
| Reviewing | `reviewing` | Operator is examining | new |
| Verified | `verified` | Confirmed as accurate | new, reviewing |
| Resolved | `resolved` | Issue has been addressed | verified, reviewing |
| False Alarm | `false_alarm` | Not a real incident | new, reviewing |

### 8.4 Badge Definitions

| Badge ID | Name | Icon | Condition |
|----------|------|------|-----------|
| `first_report` | First Responder | 🚨 | First report submitted |
| `verified_5` | Trusted Source | ✅ | 5 reports verified as accurate |
| `verified_25` | Civic Guardian | 🛡️ | 25 reports verified as accurate |
| `night_owl` | Night Owl | 🦉 | Report between 00:00-05:00 |
| `early_bird` | Early Bird | 🐦 | Report between 05:00-07:00 |
| `cluster_hero` | Cluster Hero | 🦸 | Report contributed to 5+ event cluster |
| `category_master` | Category Master | 🏅 | 10+ reports in single category |
| `streak_7` | Week Warrior | 🔥 | Reports on 7 consecutive days |

### 8.5 Data Retention

| Data Type | Retention Period | Notes |
|-----------|------------------|-------|
| Event metadata | Indefinite | Core operational data |
| Media files | 90 days | Configurable, storage cost |
| User accounts | Until deletion request | GDPR compliance |
| Classification logs | 30 days | Debugging, model improvement |

---

## 9. API Specification

### 9.1 Base Configuration

```
Base URL: /api/v1
Content-Type: application/json (except uploads)
Authentication: Bearer JWT (optional for uploads, required for operator endpoints)
```

### 9.2 Endpoints

#### 9.2.1 Upload Event

```
POST /events/upload
Content-Type: multipart/form-data
Auth: Optional
```

**Request Body:**
| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| media | File | Yes | image/* or video/*, max 100MB |
| latitude | float | Yes | -90 to 90 |
| longitude | float | Yes | -180 to 180 |
| description | string | No | max 500 characters |

**Response (202 Accepted):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "message": "Event received, processing in background"
}
```

**Errors:**
| Code | Condition |
|------|-----------|
| 400 | Invalid coordinates, missing media |
| 413 | File too large |
| 415 | Unsupported media type |
| 429 | Rate limit exceeded |

#### 9.2.2 List Events

```
GET /events
Auth: Required (Operator)
```

**Query Parameters:**
| Param | Type | Description |
|-------|------|-------------|
| bounds | string | `lat1,lng1,lat2,lng2` viewport |
| status | string | Comma-separated statuses |
| severity | string | Comma-separated severities (1-4) |
| category | string | Comma-separated categories |
| since | datetime | ISO 8601, events after this time |
| limit | int | Max results (default 100, max 500) |
| offset | int | Pagination offset |

**Response (200 OK):**
```json
{
  "total": 1234,
  "limit": 100,
  "offset": 0,
  "events": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "latitude": 52.2297,
      "longitude": 21.0122,
      "category": "emergency",
      "subcategory": "fire",
      "severity": 4,
      "status": "new",
      "description": "Fire in building",
      "thumbnail_url": "https://storage/events/.../thumb.jpg",
      "created_at": "2024-01-15T14:30:00Z",
      "cluster_id": "660e8400-e29b-41d4-a716-446655440000",
      "cluster_event_count": 5
    }
  ]
}
```

#### 9.2.3 Get Event Detail

```
GET /events/{id}
Auth: Required (Operator)
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "latitude": 52.2297,
  "longitude": 21.0122,
  "address": "ul. Marszałkowska 100, Warsaw",
  "category": "emergency",
  "subcategory": "fire",
  "severity": 4,
  "status": "new",
  "description": "Fire in building across the street",
  "media_url": "https://storage/events/.../original.mp4",
  "media_type": "video",
  "thumbnail_url": "https://storage/events/.../thumb.jpg",
  "ai_confidence": 0.92,
  "ai_reasoning": "Visible flames and smoke detected in video frame. Text description confirms fire incident.",
  "suggested_responder": "fire_department",
  "created_at": "2024-01-15T14:30:00Z",
  "cluster_id": "660e8400-e29b-41d4-a716-446655440000",
  "cluster_event_count": 5,
  "reporter": null,
  "reviewed_by": null,
  "reviewed_at": null
}
```

#### 9.2.4 Update Event Status

```
PATCH /events/{id}/status
Auth: Required (Operator)
```

**Request Body:**
```json
{
  "status": "verified",
  "notes": "Confirmed with fire department dispatch"
}
```

**Response (200 OK):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "verified",
  "reviewed_by": "operator@city.gov",
  "reviewed_at": "2024-01-15T14:35:00Z"
}
```

#### 9.2.5 Event Stream (SSE)

```
GET /events/stream
Auth: Required (Operator)
Content-Type: text/event-stream
```

**Event Types:**
```
event: connected
data: {"status": "connected"}

event: new_event
data: {"id": "...", "latitude": 52.23, "longitude": 21.01, "category": "emergency", ...}

event: event_updated
data: {"id": "...", "status": "verified", ...}

event: ping
data: {}
```

#### 9.2.6 Statistics

```
GET /stats/summary
Auth: Required (Operator)
```

**Response (200 OK):**
```json
{
  "today": {
    "total": 156,
    "by_severity": {
      "critical": 3,
      "high": 12,
      "medium": 45,
      "low": 96
    },
    "by_category": {
      "emergency": 5,
      "traffic": 34,
      "infrastructure": 67,
      "other": 50
    },
    "by_status": {
      "new": 23,
      "reviewing": 5,
      "verified": 100,
      "resolved": 20,
      "false_alarm": 8
    }
  },
  "active_clusters": 4,
  "pending_triage": 28,
  "avg_response_minutes": 12.5
}
```

#### 9.2.7 Authentication

```
POST /auth/register
POST /auth/login
POST /auth/refresh
GET /auth/me
```

(Standard JWT flow - see DESIGN.md for details)

---

## 10. User Interface Specifications

### 10.1 Mobile Upload Interface

#### 10.1.1 Screen Flow

```
[Launch] → [Capture] → [Location] → [Describe] → [Success]
```

#### 10.1.2 Capture Screen

**Elements:**
- Large camera/gallery button (primary action)
- "Take Photo" and "Record Video" options
- Gallery access for existing media
- Skip to "Report without media" (text-only, deprioritized)

**Behavior:**
- Request camera permission on first use
- Support both front and rear cameras
- Auto-orient based on device position

#### 10.1.3 Location Screen

**Elements:**
- Map preview with current location pin
- "Use Current Location" button (default, auto-selected if GPS available)
- "Adjust Location" option (tap to drag pin)
- Location accuracy indicator

**Behavior:**
- Auto-populate from device GPS
- Show accuracy radius on map
- Allow manual adjustment if GPS is inaccurate

#### 10.1.4 Describe Screen

**Elements:**
- Text input field (placeholder: "What's happening?")
- Character counter (500 max)
- Example prompts ("e.g., 'car accident', 'fire', 'pothole'")
- "Skip" option
- "Submit" button (prominent)

**Behavior:**
- Optional - user can skip
- Keyboard opens automatically
- Submit button disabled during upload

#### 10.1.5 Success Screen

**Elements:**
- Checkmark animation
- "Report Received" confirmation
- Event ID for reference
- Badge unlock notification (if applicable)
- "Report Another" button
- "View on Map" link (if authenticated)

### 10.2 Operator Dashboard

#### 10.2.1 Layout (Desktop)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ HEADER: Logo | City: Warsaw | Connection Status | User Menu                 │
├─────────────────────────────────────────────────────────────────────────────┤
│ STATS BAR: [Today: 156] [Critical: 3] [High: 12] [Pending: 28] [Clusters: 4]│
├─────────────────────────────────────────────────────────────────────────────┤
│ FILTER BAR: [Category ▼] [Severity ▼] [Status ▼] [Time Range ▼] [Clear All]│
├───────────────────────────────────────────────────────┬─────────────────────┤
│                                                       │                     │
│                                                       │    EVENT FEED       │
│                      MAP                              │    (Scrollable)     │
│                   (70% width)                         │    (30% width)      │
│                                                       │                     │
│    [Markers with severity colors]                     │  ┌───────────────┐  │
│    [Cluster indicators]                               │  │ Event Card    │  │
│    [Zoom controls]                                    │  └───────────────┘  │
│                                                       │  ┌───────────────┐  │
│                                                       │  │ Event Card    │  │
│                                                       │  └───────────────┘  │
│                                                       │        ...          │
├───────────────────────────────────────────────────────┴─────────────────────┤
│ EVENT DETAIL PANEL (Expandable from bottom, shown when event selected)      │
│ [Thumbnail] [Details] [AI Reasoning] [✓ Verify] [✗ False] [✔ Resolve]       │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### 10.2.2 Map Markers

**Severity Colors:**
| Severity | Color | Hex |
|----------|-------|-----|
| Critical | Red | #EF4444 |
| High | Orange | #F97316 |
| Medium | Yellow | #EAB308 |
| Low | Green | #22C55E |

**Status Indicators:**
| Status | Visual |
|--------|--------|
| New | Solid fill, pulsing animation |
| Reviewing | Solid fill, no pulse |
| Verified | Checkmark overlay |
| Resolved | Grayed out, 50% opacity |
| False Alarm | Crossed out, hidden by default |

**Cluster Display:**
- Circle with event count
- Color = highest severity in cluster
- Size proportional to count
- Click to zoom in

#### 10.2.3 Event Feed Card

```
┌─────────────────────────────────────────┐
│ 🔴 CRITICAL                    2 min ago│
│ ─────────────────────────────────────── │
│ Fire - Mokotów                          │
│ ul. Puławska 123                        │
│ "fire in building across..."            │
│ ─────────────────────────────────────── │
│ [Thumbnail]          Cluster: 5 reports │
└─────────────────────────────────────────┘
```

#### 10.2.4 Event Detail Panel

**Sections:**
1. **Header**: Category badge, severity, status, time
2. **Media**: Thumbnail (click to expand), play button for video
3. **Location**: Address, mini-map, coordinates
4. **Description**: User's text
5. **AI Analysis**: Reasoning, confidence score, detected objects
6. **Cluster Info**: If part of cluster, link to related events
7. **Actions**: Verify, False Alarm, Resolve buttons
8. **History**: Status changes with operator and timestamp

---

## 11. Security Requirements

### 11.1 MVP Security (Must Have)

| Requirement | Implementation |
|-------------|----------------|
| API Authentication | JWT tokens for operator endpoints |
| Upload Rate Limiting | 10 uploads/minute per IP |
| File Validation | MIME type + extension + size checks |
| Input Sanitization | Escape user text, validate coordinates |
| HTTPS | TLS 1.2+ for all connections |
| Secure Headers | CSP, X-Frame-Options, etc. |

### 11.2 Post-MVP Security (Future)

| Requirement | Notes |
|-------------|-------|
| Content Moderation | AI + human review for inappropriate content |
| Face Blurring | Privacy protection in public spaces |
| GDPR Compliance | Consent, deletion, data portability |
| Audit Logging | Track all operator actions |
| Role-Based Access | Admin, Operator, Viewer roles |
| 2FA | For operator accounts |

### 11.3 Abuse Prevention

| Threat | Mitigation |
|--------|------------|
| Spam Uploads | Rate limiting, file size limits |
| Fake Reports | AI confidence thresholds, cluster validation |
| Offensive Content | Vision API content moderation (future) |
| Location Spoofing | Cross-reference with IP geolocation (future) |
| DDoS | CDN, request throttling, WAF |

---

## 12. Performance Requirements

### 12.1 Response Time Targets

| Operation | Target | P99 |
|-----------|--------|-----|
| Upload API (excl. transfer) | <2s | <5s |
| Event List API (100 events) | <500ms | <1s |
| Event Detail API | <200ms | <500ms |
| SSE Connection Establish | <1s | <3s |
| SSE Event Delivery | <1s | <2s |
| Map Initial Render | <3s | <5s |
| AI Classification | <30s | <60s |

### 12.2 Throughput Targets (MVP)

| Metric | Target |
|--------|--------|
| Concurrent Uploads | 50 |
| Uploads per Minute | 100 |
| SSE Connections | 20 |
| API Requests per Second | 100 |

### 12.3 Resource Limits

| Resource | Limit |
|----------|-------|
| Upload File Size | 100MB |
| Description Length | 500 chars |
| Events per API Response | 500 max |
| Map Markers Rendered | 1000 max (cluster beyond) |

---

## 13. Future Roadmap

### 13.1 Phase 2: Enhanced Platform (Post-Hackathon)

| Feature | Description |
|---------|-------------|
| Multi-Source Ingestion | Twitter, Telegram, public feeds |
| CCTV Integration | City camera feed analysis |
| Polish Language | UI + AI classification in Polish |
| Mobile Native Apps | iOS and Android |
| Push Notifications | Alert operators on critical events |
| Historical Analytics | Trends, heatmaps, reports |

### 13.2 Phase 3: Multi-City (3-6 months)

| Feature | Description |
|---------|-------------|
| Multi-Tenant | Multiple cities on single platform |
| City Admin Panel | Self-service city onboarding |
| Custom Categories | City-specific event types |
| Dispatch Integration | CAD system APIs |
| SLA Tracking | Response time monitoring |

### 13.3 Phase 4: National Scale (6-12 months)

| Feature | Description |
|---------|-------------|
| National Dashboard | Cross-city visibility |
| Predictive Analytics | Incident forecasting |
| Automated Dispatch | AI-suggested responses |
| Public API | Third-party integrations |
| White-Label | Customizable branding |

---

## 14. Glossary

| Term | Definition |
|------|------------|
| **Event** | A single incident report submitted by a user |
| **Cluster** | A group of related events in close proximity and time |
| **Operator** | Government staff member monitoring the dashboard |
| **Triage** | Process of reviewing and prioritizing events |
| **Severity** | Urgency level (1-4) assigned to an event |
| **SSE** | Server-Sent Events, one-way real-time push from server |
| **PostGIS** | PostgreSQL extension for geographic data |
| **Keyframe** | Representative image extracted from video |
| **Classification** | AI-determined category and severity |
| **Badge** | Gamification achievement awarded to users |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024 | Claude | Initial specification |

---

*This specification is a living document and will be updated as requirements evolve.*
