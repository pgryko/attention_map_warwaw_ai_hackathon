# Attention Map - System Design Document

## Table of Contents
1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Database Design](#database-design)
4. [API Design](#api-design)
5. [Frontend Architecture](#frontend-architecture)
6. [Processing Pipeline](#processing-pipeline)
7. [Real-time System](#real-time-system)
8. [Deployment Architecture](#deployment-architecture)

---

## Overview

### Project Summary
Attention Map is a civic event monitoring platform that enables citizens to report incidents (fires, accidents, infrastructure issues, etc.) via mobile uploads. The system uses AI to classify and prioritize events, displaying them on a real-time map for government operators to triage and respond.

### Key Requirements
| Requirement | Decision |
|-------------|----------|
| Scope | Municipal MVP (single city) |
| Upload Source | Mobile devices (GPS + camera) |
| Classification | AI-powered (OpenAI/Claude API) |
| Real-time | Server-Sent Events (SSE) |
| Map | Leaflet.js + OpenStreetMap |
| Priority Signal | Volume-based clustering + AI severity |

### Tech Stack
```
┌─────────────────────────────────────────────────────────────────┐
│                        TECH STACK                                │
├─────────────────────────────────────────────────────────────────┤
│  Frontend     │ React 18 + Vite + Leaflet.js + TailwindCSS      │
│  Backend      │ Django 5 + Django Ninja (async)                  │
│  Task Queue   │ Celery + Redis                                   │
│  Database     │ PostgreSQL 16 + PostGIS 3.4                      │
│  Object Store │ MinIO (dev) / Cloudflare R2 (prod)               │
│  Cache/PubSub │ Redis 7                                          │
│  AI           │ OpenAI GPT-4o-mini + Vision API                  │
│  Video        │ ffmpeg (keyframe extraction)                     │
│  Container    │ Docker + Docker Compose                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## System Architecture

### High-Level Architecture Diagram

```
                                    ┌─────────────────────────────────────┐
                                    │         ATTENTION MAP               │
                                    │      System Architecture            │
                                    └─────────────────────────────────────┘

    ┌─────────────┐                           ┌─────────────────────────────────────────────────┐
    │   MOBILE    │                           │              REACT FRONTEND                     │
    │   UPLOADER  │                           │  ┌───────────────┐    ┌─────────────────────┐  │
    │             │                           │  │  Upload Page  │    │  Operator Dashboard │  │
    │ ┌─────────┐ │                           │  │  • Camera     │    │  • Live Map         │  │
    │ │  GPS    │ │                           │  │  • GPS        │    │  • Event Feed       │  │
    │ │  Camera │ │                           │  │  • Form       │    │  • Triage Actions   │  │
    │ │  Form   │ │                           │  └───────┬───────┘    └──────────┬──────────┘  │
    │ └────┬────┘ │                           │          │                       │             │
    └──────┼──────┘                           │          │         SSE           │             │
           │                                  └──────────┼───────────────────────┼─────────────┘
           │ HTTP POST                                   │                       │
           │ multipart/form-data                         │                       │
           ▼                                             ▼                       │
    ┌──────────────────────────────────────────────────────────────────────────────────────────┐
    │                              DJANGO NINJA API (ASYNC)                                     │
    │                                                                                          │
    │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────┐ │
    │  │  POST /upload   │  │  GET /events    │  │  GET /stream    │  │  PATCH /events/:id  │ │
    │  │                 │  │  (map data)     │  │  (SSE)          │  │  (triage)           │ │
    │  └────────┬────────┘  └─────────────────┘  └────────▲────────┘  └─────────────────────┘ │
    │           │                                         │                                    │
    └───────────┼─────────────────────────────────────────┼────────────────────────────────────┘
                │                                         │
                │ Celery Task                             │ Redis Pub/Sub
                ▼                                         │
    ┌───────────────────────────────────────────────────────────────────────────────────────────┐
    │                              CELERY WORKER                                                 │
    │                                                                                           │
    │   ┌─────────────────────────────────────────────────────────────────────────────────────┐ │
    │   │                         PROCESSING PIPELINE                                          │ │
    │   │                                                                                      │ │
    │   │   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐     │ │
    │   │   │  Store   │───▶│ Extract  │───▶│ Classify │───▶│ Cluster  │───▶│ Broadcast│     │ │
    │   │   │  Media   │    │ Keyframe │    │   (AI)   │    │  Events  │    │   SSE    │     │ │
    │   │   └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘     │ │
    │   │        │               │               │               │               │            │ │
    │   │        ▼               ▼               ▼               ▼               ▼            │ │
    │   │     MinIO          ffmpeg         OpenAI API       PostGIS         Redis           │ │
    │   └─────────────────────────────────────────────────────────────────────────────────────┘ │
    │                                                                                           │
    └───────────────────────────────────────────────────────────────────────────────────────────┘
                │
                ▼
    ┌───────────────────────────────────────────────────────────────────────────────────────────┐
    │                                    DATA LAYER                                              │
    │                                                                                           │
    │   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │
    │   │   PostgreSQL    │  │     PostGIS     │  │      Redis      │  │      MinIO      │     │
    │   │   + pgvector    │  │   (spatial)     │  │  (cache/queue)  │  │    (media)      │     │
    │   │                 │  │                 │  │                 │  │                 │     │
    │   │  • Events       │  │  • ST_DWithin   │  │  • Celery       │  │  • Videos       │     │
    │   │  • Users        │  │  • ST_Distance  │  │  • Sessions     │  │  • Images       │     │
    │   │  • Clusters     │  │  • Bounding Box │  │  • Pub/Sub      │  │  • Thumbnails   │     │
    │   └─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘     │
    │                                                                                           │
    └───────────────────────────────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| **Mobile Uploader** | Capture GPS, media; submit to API |
| **React Frontend** | Upload form, operator dashboard, live map |
| **Django Ninja API** | RESTful endpoints, SSE streaming, auth |
| **Celery Worker** | Async processing pipeline |
| **PostgreSQL/PostGIS** | Event storage, spatial queries |
| **Redis** | Task queue, pub/sub, caching |
| **MinIO** | Object storage for media files |
| **OpenAI API** | Text + vision classification |

---

## Database Design

### Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DATABASE SCHEMA (PostGIS)                                       │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

    ┌─────────────────────────┐          ┌─────────────────────────────┐
    │        auth_user        │          │         user_profile        │
    ├─────────────────────────┤          ├─────────────────────────────┤
    │ id (PK)                 │◀────────┐│ id (PK)                     │
    │ username                │         ││ user_id (FK) ───────────────┘
    │ email                   │         │ reports_submitted: int
    │ password                │         │ reports_verified: int
    │ is_active               │         │ badges: jsonb
    │ date_joined             │         │ reputation_score: int
    └─────────────────────────┘         │ created_at: timestamp
              │                          └─────────────────────────────┘
              │
              │ reported_by (nullable)
              │ reviewed_by (nullable)
              ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                            event                                 │
    ├─────────────────────────────────────────────────────────────────┤
    │ id: uuid (PK)                                                    │
    │ reporter_id: int (FK → auth_user, nullable)                     │
    │ created_at: timestamp with timezone                              │
    │                                                                  │
    │ ── LOCATION ──                                                   │
    │ location: geometry(Point, 4326)  ◀── PostGIS spatial column     │
    │ address: varchar(500)                                            │
    │                                                                  │
    │ ── CONTENT ──                                                    │
    │ description: text                                                │
    │ media_url: varchar(500)                                          │
    │ media_type: varchar(10) ['image', 'video']                      │
    │ thumbnail_url: varchar(500)                                      │
    │                                                                  │
    │ ── AI CLASSIFICATION ──                                          │
    │ category: varchar(50)                                            │
    │ subcategory: varchar(50)                                         │
    │ severity: int [1-4]                                              │
    │ ai_confidence: float                                             │
    │ ai_reasoning: text                                               │
    │                                                                  │
    │ ── CLUSTERING ──                                                 │
    │ cluster_id: uuid (FK → event_cluster, nullable)                 │
    │                                                                  │
    │ ── TRIAGE ──                                                     │
    │ status: varchar(20) ['new','reviewing','verified','resolved']   │
    │ reviewed_by_id: int (FK → auth_user, nullable)                  │
    │ reviewed_at: timestamp                                           │
    │                                                                  │
    │ ── INDEXES ──                                                    │
    │ • idx_event_location (GIST on location)                         │
    │ • idx_event_created_at (created_at DESC)                        │
    │ • idx_event_status_severity (status, severity DESC)             │
    │ • idx_event_category (category)                                  │
    └─────────────────────────────────────────────────────────────────┘
              │
              │ cluster_id
              ▼
    ┌─────────────────────────────────────────────────────────────────┐
    │                        event_cluster                             │
    ├─────────────────────────────────────────────────────────────────┤
    │ id: uuid (PK)                                                    │
    │ centroid: geometry(Point, 4326)                                  │
    │ radius_meters: int (default: 100)                               │
    │ event_count: int                                                 │
    │ first_event_at: timestamp                                        │
    │ last_event_at: timestamp                                         │
    │ computed_severity: int  ◀── Boosted by event_count              │
    │                                                                  │
    │ ── INDEXES ──                                                    │
    │ • idx_cluster_centroid (GIST on centroid)                       │
    │ • idx_cluster_severity (computed_severity DESC)                  │
    └─────────────────────────────────────────────────────────────────┘
```

### Category Enum Values

```python
CATEGORY_CHOICES = [
    ('emergency', 'Emergency'),        # Fire, explosion, collapse
    ('security', 'Security'),          # Drone, suspicious activity
    ('traffic', 'Traffic'),            # Accident, blockage
    ('protest', 'Protest/Gathering'),  # March, demonstration
    ('infrastructure', 'Infrastructure'), # Pothole, broken light
    ('environmental', 'Environmental'), # Pollution, fallen tree
    ('informational', 'Informational'), # General observation
]

SEVERITY_CHOICES = [
    (1, 'Low'),        # Informational only
    (2, 'Medium'),     # Needs attention, not urgent
    (3, 'High'),       # Urgent, requires response
    (4, 'Critical'),   # Life-threatening emergency
]

STATUS_CHOICES = [
    ('new', 'New'),
    ('reviewing', 'Reviewing'),
    ('verified', 'Verified'),
    ('resolved', 'Resolved'),
    ('false_alarm', 'False Alarm'),
]
```

### Key Spatial Queries

```sql
-- Find events within map viewport
SELECT * FROM event
WHERE location && ST_MakeEnvelope(lng1, lat1, lng2, lat2, 4326)
  AND status IN ('new', 'reviewing', 'verified')
ORDER BY severity DESC, created_at DESC;

-- Find nearby events for clustering (within 100m, last 30 min)
SELECT * FROM event
WHERE ST_DWithin(
    location::geography,
    ST_SetSRID(ST_MakePoint(:lng, :lat), 4326)::geography,
    100  -- meters
)
AND created_at > NOW() - INTERVAL '30 minutes';

-- Compute cluster centroid
SELECT ST_Centroid(ST_Collect(location)) as centroid
FROM event
WHERE cluster_id = :cluster_id;
```

---

## API Design

### Endpoint Specification

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              API ENDPOINTS (Django Ninja)                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

BASE URL: /api/v1

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ UPLOAD ENDPOINTS                                                                              │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  POST /events/upload                                                                          │
│  ─────────────────────────────────────────────────────────────────────────────────────────   │
│  Description: Submit a new event with media                                                   │
│  Auth: Optional (anonymous allowed)                                                           │
│  Content-Type: multipart/form-data                                                            │
│                                                                                               │
│  Request:                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                                        │ │
│  │   "media": File (required, image/* or video/*),                                         │ │
│  │   "latitude": float (required),                                                          │ │
│  │   "longitude": float (required),                                                         │ │
│  │   "description": string (optional, e.g., "fire in the building")                        │ │
│  │ }                                                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                               │
│  Response: 202 Accepted                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                                        │ │
│  │   "id": "uuid",                                                                          │ │
│  │   "status": "processing",                                                                │ │
│  │   "message": "Event received, processing..."                                             │ │
│  │ }                                                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ MAP/EVENT ENDPOINTS                                                                           │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  GET /events                                                                                  │
│  ─────────────────────────────────────────────────────────────────────────────────────────   │
│  Description: List events with filters (for map + feed)                                       │
│  Auth: Required (operator)                                                                    │
│                                                                                               │
│  Query Parameters:                                                                            │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ bounds      string   "lat1,lng1,lat2,lng2" - map viewport                               │ │
│  │ status      string   "new,reviewing" - comma-separated                                  │ │
│  │ severity    string   "3,4" - comma-separated                                            │ │
│  │ category    string   "emergency,traffic" - comma-separated                              │ │
│  │ since       datetime ISO 8601 - events after this time                                  │ │
│  │ limit       int      default=100, max=500                                               │ │
│  │ offset      int      pagination offset                                                  │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                               │
│  Response: 200 OK                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                                        │ │
│  │   "total": 1234,                                                                         │ │
│  │   "events": [                                                                            │ │
│  │     {                                                                                    │ │
│  │       "id": "uuid",                                                                      │ │
│  │       "latitude": 52.2297,                                                               │ │
│  │       "longitude": 21.0122,                                                              │ │
│  │       "category": "emergency",                                                           │ │
│  │       "subcategory": "fire",                                                             │ │
│  │       "severity": 4,                                                                     │ │
│  │       "status": "new",                                                                   │ │
│  │       "description": "fire in the building",                                             │ │
│  │       "thumbnail_url": "https://...",                                                    │ │
│  │       "created_at": "2024-01-01T12:00:00Z",                                              │ │
│  │       "cluster_id": "uuid" | null,                                                       │ │
│  │       "cluster_event_count": 5 | null                                                    │ │
│  │     }                                                                                    │ │
│  │   ]                                                                                      │ │
│  │ }                                                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                               │
│  GET /events/{id}                                                                             │
│  ─────────────────────────────────────────────────────────────────────────────────────────   │
│  Description: Get full event details                                                          │
│  Auth: Required (operator)                                                                    │
│  Response: Full event object with media_url, ai_reasoning, etc.                              │
│                                                                                               │
│  GET /events/stream                                                                           │
│  ─────────────────────────────────────────────────────────────────────────────────────────   │
│  Description: Server-Sent Events stream for real-time updates                                │
│  Auth: Required (operator)                                                                    │
│  Content-Type: text/event-stream                                                              │
│                                                                                               │
│  Events:                                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ event: connected                                                                         │ │
│  │ data: {}                                                                                 │ │
│  │                                                                                          │ │
│  │ event: new_event                                                                         │ │
│  │ data: {"id": "uuid", "lat": 52.23, "lng": 21.01, "category": "emergency", ...}          │ │
│  │                                                                                          │ │
│  │ event: event_updated                                                                     │ │
│  │ data: {"id": "uuid", "status": "verified", ...}                                          │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ TRIAGE ENDPOINTS                                                                              │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  PATCH /events/{id}/status                                                                    │
│  ─────────────────────────────────────────────────────────────────────────────────────────   │
│  Description: Update event status (triage action)                                             │
│  Auth: Required (operator)                                                                    │
│                                                                                               │
│  Request:                                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                                        │ │
│  │   "status": "verified" | "resolved" | "false_alarm",                                    │ │
│  │   "notes": string (optional)                                                             │ │
│  │ }                                                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                               │
│  Response: 200 OK with updated event                                                          │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ AUTH ENDPOINTS                                                                                │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  POST /auth/register                                                                          │
│  POST /auth/login           → Returns JWT access + refresh tokens                            │
│  POST /auth/refresh         → Refresh access token                                           │
│  GET  /auth/me              → Current user profile + badges                                  │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│ STATS ENDPOINTS                                                                               │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│  GET /stats/summary                                                                           │
│  ─────────────────────────────────────────────────────────────────────────────────────────   │
│  Description: Dashboard statistics                                                            │
│  Auth: Required (operator)                                                                    │
│                                                                                               │
│  Response:                                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │ {                                                                                        │ │
│  │   "today": {                                                                             │ │
│  │     "total": 156,                                                                        │ │
│  │     "by_severity": {"critical": 3, "high": 12, "medium": 45, "low": 96},                │ │
│  │     "by_category": {"emergency": 5, "traffic": 34, ...},                                │ │
│  │     "by_status": {"new": 23, "reviewing": 5, "verified": 100, ...}                      │ │
│  │   },                                                                                     │ │
│  │   "active_clusters": 4,                                                                  │ │
│  │   "avg_response_time_minutes": 12.5                                                      │ │
│  │ }                                                                                        │ │
│  └─────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Architecture

### Component Tree

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              REACT COMPONENT ARCHITECTURE                                    │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

src/
├── App.jsx                          # Router + global providers
├── main.jsx                         # Entry point
│
├── pages/
│   ├── UploadPage.jsx              # Mobile upload interface
│   ├── DashboardPage.jsx           # Operator dashboard (main)
│   └── LoginPage.jsx               # Auth
│
├── components/
│   │
│   ├── Map/
│   │   ├── EventMap.jsx            # Leaflet map container
│   │   │   └── Uses: MapContainer, TileLayer, MarkerClusterGroup
│   │   │
│   │   ├── EventMarker.jsx         # Individual event marker
│   │   │   └── Props: event, onClick, isSelected
│   │   │   └── Shows: severity color, category icon
│   │   │
│   │   └── ClusterMarker.jsx       # Cluster indicator
│   │       └── Props: cluster, eventCount
│   │       └── Shows: count badge, pulsing animation
│   │
│   ├── Dashboard/
│   │   ├── Dashboard.jsx           # Main layout (map + sidebar)
│   │   │   └── State: selectedEvent, filters
│   │   │
│   │   ├── EventFeed.jsx           # Live event list
│   │   │   └── Props: events, onSelect
│   │   │   └── Features: auto-scroll, new event highlight
│   │   │
│   │   ├── EventDetail.jsx         # Selected event panel
│   │   │   └── Props: event, onStatusChange
│   │   │   └── Shows: media, AI reasoning, triage buttons
│   │   │
│   │   ├── FilterBar.jsx           # Category/severity filters
│   │   │   └── Props: filters, onChange
│   │   │
│   │   └── StatsWidgets.jsx        # Summary statistics
│   │       └── Shows: today's count, by category, etc.
│   │
│   ├── Upload/
│   │   ├── UploadForm.jsx          # Main upload form
│   │   │   └── State: file, description, location, uploading
│   │   │
│   │   ├── CameraCapture.jsx       # Camera/file input
│   │   │   └── Uses: <input type="file" capture>
│   │   │
│   │   ├── LocationPicker.jsx      # GPS or manual location
│   │   │   └── Uses: navigator.geolocation
│   │   │
│   │   └── UploadSuccess.jsx       # Confirmation + badge teaser
│   │
│   └── common/
│       ├── Button.jsx
│       ├── Badge.jsx               # Severity/category badges
│       ├── Spinner.jsx
│       └── Toast.jsx
│
├── hooks/
│   ├── useEventStream.js          # SSE connection
│   │   └── Returns: { connected, lastEvent }
│   │   └── Listens: /api/v1/events/stream
│   │
│   ├── useEvents.js               # Event list fetching
│   │   └── Params: bounds, filters
│   │   └── Returns: { events, loading, refetch }
│   │
│   ├── useGeolocation.js          # GPS access
│   │   └── Returns: { latitude, longitude, error }
│   │
│   └── useAuth.js                 # JWT auth state
│       └── Returns: { user, login, logout, isOperator }
│
├── api/
│   └── client.js                  # Axios/fetch wrapper
│       └── Exports: uploadEvent, getEvents, updateStatus, etc.
│
├── utils/
│   ├── categories.js              # Category icons, colors
│   ├── severity.js                # Severity colors, labels
│   └── geo.js                     # Map utilities
│
└── styles/
    └── tailwind.css               # TailwindCSS imports
```

### Dashboard Layout

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  OPERATOR DASHBOARD LAYOUT                                                                   │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  HEADER                                                            [User] [Logout]     │ │
│  │  Attention Map - Warsaw                                                                │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  STATS BAR                                                                             │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐                     │ │
│  │  │ Today    │ │ Critical │ │ High     │ │ Pending  │ │ Clusters │                     │ │
│  │  │   156    │ │    3     │ │   12     │ │   28     │ │    4     │                     │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘                     │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                              │
│  ┌──────────────────────────────────────────────────────────┐ ┌────────────────────────────┐│
│  │                                                          │ │  EVENT FEED               ││
│  │                                                          │ │  ┌──────────────────────┐ ││
│  │                      LEAFLET MAP                         │ │  │ 🔴 Fire - Mokotów    │ ││
│  │                                                          │ │  │    2 min ago         │ ││
│  │               [Markers with severity colors]             │ │  └──────────────────────┘ ││
│  │               [Cluster indicators]                       │ │  ┌──────────────────────┐ ││
│  │               [Click → show detail]                      │ │  │ 🟠 Accident - Śród.  │ ││
│  │                                                          │ │  │    5 min ago         │ ││
│  │                                                          │ │  └──────────────────────┘ ││
│  │                                                          │ │  ┌──────────────────────┐ ││
│  │                                                          │ │  │ 🟡 Pothole - Wola    │ ││
│  │                                                          │ │  │    12 min ago        │ ││
│  │                                                          │ │  └──────────────────────┘ ││
│  │                                                          │ │           ...            ││
│  └──────────────────────────────────────────────────────────┘ └────────────────────────────┘│
│                                                                                              │
│  ┌────────────────────────────────────────────────────────────────────────────────────────┐ │
│  │  EVENT DETAIL (when selected)                                                          │ │
│  │  ┌─────────────────────┐                                                               │ │
│  │  │                     │  🔴 CRITICAL - Fire                                           │ │
│  │  │     [Thumbnail]     │  Mokotów, ul. Puławska 123                                    │ │
│  │  │                     │  "there's a fire in the building across the street"          │ │
│  │  │                     │                                                               │ │
│  │  └─────────────────────┘  AI: High confidence fire detection. Multiple heat sources.  │ │
│  │                                                                                        │ │
│  │  [ ✓ Verify ]  [ ✗ False Alarm ]  [ ✔ Resolved ]                                      │ │
│  └────────────────────────────────────────────────────────────────────────────────────────┘ │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Upload Flow

```
┌───────────────────────────────────────────────────────────────────────────────────────────────┐
│  MOBILE UPLOAD FLOW                                                                           │
├───────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                               │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐            │
│   │   STEP 1    │      │   STEP 2    │      │   STEP 3    │      │   STEP 4    │            │
│   │   Capture   │ ───▶ │   Location  │ ───▶ │   Describe  │ ───▶ │   Success   │            │
│   └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘            │
│                                                                                               │
│   ┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐            │
│   │             │      │             │      │             │      │             │            │
│   │  📷  📹     │      │    📍       │      │  What's     │      │   ✓        │            │
│   │             │      │   [Map]     │      │  happening? │      │  Thanks!    │            │
│   │  [Camera]   │      │             │      │             │      │             │            │
│   │  [Gallery]  │      │  Using GPS  │      │  [Text...]  │      │  Processing │            │
│   │             │      │  Auto-fill  │      │             │      │  your report│            │
│   │             │      │             │      │  [Submit]   │      │             │            │
│   │             │      │             │      │             │      │  🏅 +10 pts │            │
│   └─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘            │
│                                                                                               │
└───────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Processing Pipeline

### Celery Task Flow

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              CELERY PROCESSING PIPELINE                                      │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

API Upload
    │
    ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│  TASK: process_event_upload                                                                  │
│  Queue: celery (default)                                                                     │
│  Timeout: 5 minutes                                                                          │
├─────────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                              │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐    │
│   │  STEP 1: Store Media                                                                │    │
│   │  ───────────────────                                                                │    │
│   │  • Upload raw file to MinIO bucket: events/{event_id}/original.{ext}               │    │
│   │  • Generate presigned URL (1 hour expiry for processing)                           │    │
│   │  • Update event.media_url                                                          │    │
│   └────────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                                   │
│                          ▼                                                                   │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐    │
│   │  STEP 2: Extract Keyframe (if video)                                                │    │
│   │  ───────────────────────────────                                                    │    │
│   │  • ffmpeg: extract frame at 1 second mark                                          │    │
│   │  • Command: ffmpeg -i input.mp4 -ss 00:00:01 -frames:v 1 thumbnail.jpg             │    │
│   │  • Upload thumbnail to MinIO: events/{event_id}/thumbnail.jpg                      │    │
│   │  • Update event.thumbnail_url                                                       │    │
│   │  • If image: thumbnail = original                                                   │    │
│   └────────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                                   │
│                          ▼                                                                   │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐    │
│   │  STEP 3: AI Classification                                                          │    │
│   │  ──────────────────────                                                             │    │
│   │                                                                                      │    │
│   │  3a. Text Classification (if description provided)                                  │    │
│   │  ┌────────────────────────────────────────────────────────────────────────────────┐ │    │
│   │  │  Prompt: "Classify this civic incident: '{description}'"                       │ │    │
│   │  │  Model: gpt-4o-mini                                                            │ │    │
│   │  │  Response: { category, subcategory, severity, reasoning }                      │ │    │
│   │  └────────────────────────────────────────────────────────────────────────────────┘ │    │
│   │                                                                                      │    │
│   │  3b. Vision Classification (always)                                                 │    │
│   │  ┌────────────────────────────────────────────────────────────────────────────────┐ │    │
│   │  │  Prompt: "Analyze this image for civic incidents..."                          │ │    │
│   │  │  Model: gpt-4o (vision)                                                        │ │    │
│   │  │  Input: thumbnail image                                                        │ │    │
│   │  │  Response: { category, subcategory, severity, reasoning, detected_objects }   │ │    │
│   │  └────────────────────────────────────────────────────────────────────────────────┘ │    │
│   │                                                                                      │    │
│   │  3c. Merge Classifications                                                          │    │
│   │  ┌────────────────────────────────────────────────────────────────────────────────┐ │    │
│   │  │  • If both agree: use shared classification                                    │ │    │
│   │  │  • If differ: prefer vision for visual events (fire), text for context        │ │    │
│   │  │  • Confidence = min(text_conf, vision_conf) if both, else single              │ │    │
│   │  │  • Update: event.category, subcategory, severity, ai_confidence, ai_reasoning │ │    │
│   │  └────────────────────────────────────────────────────────────────────────────────┘ │    │
│   └────────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                                   │
│                          ▼                                                                   │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐    │
│   │  STEP 4: Spatial Clustering                                                         │    │
│   │  ──────────────────────────                                                         │    │
│   │                                                                                      │    │
│   │  Query: Find events within 100m in last 30 minutes                                 │    │
│   │  ┌────────────────────────────────────────────────────────────────────────────────┐ │    │
│   │  │  SELECT * FROM event                                                           │ │    │
│   │  │  WHERE ST_DWithin(location::geography, :point::geography, 100)                 │ │    │
│   │  │    AND created_at > NOW() - INTERVAL '30 minutes'                              │ │    │
│   │  │    AND id != :current_event_id;                                                │ │    │
│   │  └────────────────────────────────────────────────────────────────────────────────┘ │    │
│   │                                                                                      │    │
│   │  If nearby events found:                                                            │    │
│   │  ┌────────────────────────────────────────────────────────────────────────────────┐ │    │
│   │  │  • Check if existing cluster → add to it                                       │ │    │
│   │  │  • Else create new EventCluster                                                │ │    │
│   │  │  • Update cluster.event_count, centroid, computed_severity                     │ │    │
│   │  │  • Severity boost: base_severity + log2(event_count)                           │ │    │
│   │  └────────────────────────────────────────────────────────────────────────────────┘ │    │
│   └────────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                                   │
│                          ▼                                                                   │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐    │
│   │  STEP 5: Broadcast via SSE                                                          │    │
│   │  ────────────────────────                                                           │    │
│   │  • Publish to Redis channel: events:new                                            │    │
│   │  • Payload: { id, lat, lng, category, severity, thumbnail_url, cluster_id }       │    │
│   │  • All connected operator dashboards receive update                                │    │
│   └────────────────────────────────────────────────────────────────────────────────────┘    │
│                          │                                                                   │
│                          ▼                                                                   │
│   ┌────────────────────────────────────────────────────────────────────────────────────┐    │
│   │  STEP 6: Update User Stats (if authenticated)                                       │    │
│   │  ───────────────────────────────────────                                            │    │
│   │  • Increment user_profile.reports_submitted                                        │    │
│   │  • Check badge conditions → award new badges                                       │    │
│   │  • Update reputation_score                                                          │    │
│   └────────────────────────────────────────────────────────────────────────────────────┘    │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘
```

### AI Classification Prompts

```python
# Text Classification Prompt
TEXT_CLASSIFICATION_PROMPT = """
Analyze this civic incident report submitted by a citizen.

User's description: "{description}"
Location: {city}, {country}
Submitted at: {timestamp}

Classify this incident and respond in JSON format:
{{
  "category": one of ["emergency", "security", "traffic", "protest", "infrastructure", "environmental", "informational"],
  "subcategory": specific type (e.g., "fire", "car_accident", "pothole", "demonstration"),
  "severity": integer 1-4 where:
    4 = Critical (life-threatening, immediate response needed)
    3 = High (urgent, needs quick response)
    2 = Medium (needs attention but not urgent)
    1 = Low (informational only),
  "confidence": float 0-1,
  "reasoning": brief explanation (1-2 sentences),
  "suggested_responder": one of ["emergency_services", "police", "fire_department", "city_works", "traffic_control", "none"]
}}

Examples:
- "there's a fire in the building" → emergency, fire, severity 4
- "someone hit my car" → traffic, car_accident, severity 2
- "huge pothole on main street" → infrastructure, pothole, severity 2
- "protest downtown blocking traffic" → protest, demonstration, severity 2
"""

# Vision Classification Prompt
VISION_CLASSIFICATION_PROMPT = """
Analyze this image submitted as a civic incident report.

Look for:
- Fires, smoke, explosions
- Vehicle accidents or damage
- Crowds, gatherings, protests
- Infrastructure damage (potholes, broken lights, etc.)
- Environmental issues (flooding, fallen trees, pollution)
- Security concerns (suspicious objects, vandalism)

Respond in JSON format:
{{
  "category": one of ["emergency", "security", "traffic", "protest", "infrastructure", "environmental", "informational"],
  "subcategory": specific type detected,
  "severity": integer 1-4,
  "confidence": float 0-1,
  "reasoning": what you detected in the image,
  "detected_objects": list of relevant objects/scenes detected
}}

If the image is unclear or doesn't show a clear incident, use category "informational" with low severity.
"""
```

---

## Real-time System

### SSE Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              SERVER-SENT EVENTS (SSE) FLOW                                   │
└─────────────────────────────────────────────────────────────────────────────────────────────┘


       CELERY WORKER                    REDIS                     DJANGO                  REACT
            │                             │                          │                       │
            │                             │                          │                       │
            │  1. Event processed         │                          │                       │
            │────────────────────────────▶│                          │                       │
            │  PUBLISH events:new         │                          │                       │
            │  {id, lat, lng, ...}        │                          │                       │
            │                             │                          │                       │
            │                             │                          │     2. Connect SSE    │
            │                             │                          │◀──────────────────────│
            │                             │                          │   GET /events/stream  │
            │                             │                          │                       │
            │                             │  3. SUBSCRIBE            │                       │
            │                             │◀─────────────────────────│                       │
            │                             │     events:new           │                       │
            │                             │                          │                       │
            │                             │  4. Message received     │                       │
            │                             │─────────────────────────▶│                       │
            │                             │                          │                       │
            │                             │                          │  5. Stream SSE event  │
            │                             │                          │──────────────────────▶│
            │                             │                          │  event: new_event     │
            │                             │                          │  data: {...}          │
            │                             │                          │                       │
            │                             │                          │                       │
            │                             │                          │   6. Update UI        │
            │                             │                          │   - Add marker to map │
            │                             │                          │   - Add to feed       │
            │                             │                          │   - Update stats      │
            │                             │                          │                       │
```

### SSE Implementation Details

```python
# Backend: api/streaming.py
import json
import redis
from django.http import StreamingHttpResponse

def event_stream_view(request):
    """SSE endpoint for real-time event updates."""

    def generate():
        r = redis.Redis(host='redis', port=6379, db=0)
        pubsub = r.pubsub()
        pubsub.subscribe('events:new', 'events:updated')

        # Send initial connection event
        yield 'event: connected\ndata: {"status": "connected"}\n\n'

        # Keep-alive every 30 seconds
        import time
        last_ping = time.time()

        for message in pubsub.listen():
            # Send keep-alive ping
            if time.time() - last_ping > 30:
                yield 'event: ping\ndata: {}\n\n'
                last_ping = time.time()

            if message['type'] == 'message':
                channel = message['channel'].decode()
                data = message['data'].decode()

                if channel == 'events:new':
                    yield f'event: new_event\ndata: {data}\n\n'
                elif channel == 'events:updated':
                    yield f'event: event_updated\ndata: {data}\n\n'

    response = StreamingHttpResponse(
        generate(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'  # Disable nginx buffering
    return response


# Celery task: broadcast after processing
def broadcast_new_event(event):
    """Publish event to Redis for SSE broadcast."""
    r = redis.Redis(host='redis', port=6379, db=0)

    payload = json.dumps({
        'id': str(event.id),
        'latitude': event.location.y,
        'longitude': event.location.x,
        'category': event.category,
        'subcategory': event.subcategory,
        'severity': event.severity,
        'status': event.status,
        'thumbnail_url': event.thumbnail_url,
        'created_at': event.created_at.isoformat(),
        'cluster_id': str(event.cluster_id) if event.cluster_id else None,
    })

    r.publish('events:new', payload)
```

```javascript
// Frontend: hooks/useEventStream.js
import { useEffect, useCallback, useRef, useState } from 'react';

export function useEventStream(onNewEvent, onEventUpdated) {
  const [connected, setConnected] = useState(false);
  const eventSourceRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const eventSource = new EventSource('/api/v1/events/stream');
    eventSourceRef.current = eventSource;

    eventSource.addEventListener('connected', () => {
      setConnected(true);
      console.log('SSE connected');
    });

    eventSource.addEventListener('new_event', (e) => {
      const event = JSON.parse(e.data);
      onNewEvent(event);
    });

    eventSource.addEventListener('event_updated', (e) => {
      const event = JSON.parse(e.data);
      onEventUpdated?.(event);
    });

    eventSource.onerror = () => {
      setConnected(false);
      eventSource.close();
      // Reconnect after 5 seconds
      reconnectTimeoutRef.current = setTimeout(connect, 5000);
    };
  }, [onNewEvent, onEventUpdated]);

  useEffect(() => {
    connect();
    return () => {
      eventSourceRef.current?.close();
      clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connect]);

  return { connected };
}
```

---

## Deployment Architecture

### Docker Compose (Development)

```yaml
# docker-compose.yml
version: '3.8'

services:
  # ─────────────────────────────────────────────────────────────
  # DATABASE
  # ─────────────────────────────────────────────────────────────
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_DB: attention_map
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─────────────────────────────────────────────────────────────
  # REDIS (Queue + PubSub + Cache)
  # ─────────────────────────────────────────────────────────────
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ─────────────────────────────────────────────────────────────
  # OBJECT STORAGE (MinIO - S3 compatible)
  # ─────────────────────────────────────────────────────────────
  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    ports:
      - "9000:9000"   # API
      - "9001:9001"   # Console
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 30s
      timeout: 20s
      retries: 3

  # ─────────────────────────────────────────────────────────────
  # DJANGO BACKEND (API)
  # ─────────────────────────────────────────────────────────────
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: >
      sh -c "python manage.py migrate &&
             python manage.py runserver 0.0.0.0:8000"
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    environment:
      - DEBUG=1
      - DATABASE_URL=postgis://postgres:postgres@db:5432/attention_map  # pragma: allowlist secret
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
      - MINIO_BUCKET=events
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  # ─────────────────────────────────────────────────────────────
  # CELERY WORKER (Background Tasks)
  # ─────────────────────────────────────────────────────────────
  celery:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A attention_map worker -l info --concurrency=2
    volumes:
      - ./backend:/app
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
      minio:
        condition: service_healthy
    environment:
      - DEBUG=1
      - DATABASE_URL=postgis://postgres:postgres@db:5432/attention_map  # pragma: allowlist secret
      - REDIS_URL=redis://redis:6379/0
      - MINIO_ENDPOINT=minio:9000
      - MINIO_ACCESS_KEY=minioadmin
      - MINIO_SECRET_KEY=minioadmin
      - MINIO_BUCKET=events
      - OPENAI_API_KEY=${OPENAI_API_KEY}

  # ─────────────────────────────────────────────────────────────
  # REACT FRONTEND
  # ─────────────────────────────────────────────────────────────
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - VITE_API_URL=http://localhost:8000

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

### Service Diagram

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                              DOCKER COMPOSE SERVICES                                         │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

                                    ┌─────────────────┐
                                    │    FRONTEND     │
                                    │   React:3000    │
                                    └────────┬────────┘
                                             │
                                             │ HTTP
                                             ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                              │
│    ┌─────────────────┐           ┌─────────────────┐           ┌─────────────────┐         │
│    │    BACKEND      │           │     CELERY      │           │      REDIS      │         │
│    │  Django:8000    │◀─────────▶│     Worker      │◀─────────▶│      :6379      │         │
│    │                 │  Celery   │                 │   Queue   │                 │         │
│    │  • REST API     │  Tasks    │  • Process      │   PubSub  │  • Task Queue   │         │
│    │  • SSE Stream   │           │  • Classify     │           │  • SSE Pub/Sub  │         │
│    │  • Auth         │           │  • Cluster      │           │  • Cache        │         │
│    └────────┬────────┘           └────────┬────────┘           └─────────────────┘         │
│             │                             │                                                  │
│             │ SQL                         │ SQL + S3                                        │
│             ▼                             ▼                                                  │
│    ┌─────────────────┐           ┌─────────────────┐                                        │
│    │   POSTGRESQL    │           │      MINIO      │                                        │
│    │  + PostGIS      │           │     :9000       │                                        │
│    │     :5432       │           │                 │                                        │
│    │                 │           │  • Videos       │                                        │
│    │  • Events       │           │  • Images       │                                        │
│    │  • Users        │           │  • Thumbnails   │                                        │
│    │  • Spatial      │           │                 │                                        │
│    └─────────────────┘           └─────────────────┘                                        │
│                                                                                              │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

Ports:
  • 3000 - Frontend (React)
  • 8000 - Backend (Django Ninja)
  • 5432 - PostgreSQL
  • 6379 - Redis
  • 9000 - MinIO API
  • 9001 - MinIO Console
```

---

## Project Structure

```
attention_map/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── README.md
├── DESIGN.md                          # This document
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── manage.py
│   │
│   ├── attention_map/                 # Django project
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── celery.py
│   │   └── asgi.py
│   │
│   ├── core/                          # Core models
│   │   ├── __init__.py
│   │   ├── models.py                  # Event, EventCluster, UserProfile
│   │   ├── admin.py
│   │   └── migrations/
│   │
│   ├── api/                           # Django Ninja API
│   │   ├── __init__.py
│   │   ├── routes.py                  # All endpoints
│   │   ├── schemas.py                 # Pydantic schemas
│   │   ├── auth.py                    # JWT authentication
│   │   └── streaming.py               # SSE endpoint
│   │
│   ├── services/                      # Business logic
│   │   ├── __init__.py
│   │   ├── classification.py          # OpenAI integration
│   │   ├── media.py                   # MinIO + ffmpeg
│   │   ├── clustering.py              # PostGIS spatial
│   │   └── badges.py                  # Gamification logic
│   │
│   └── tasks/                         # Celery tasks
│       ├── __init__.py
│       └── processing.py              # Main pipeline
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    ├── index.html
    │
    └── src/
        ├── App.jsx
        ├── main.jsx
        │
        ├── pages/
        │   ├── UploadPage.jsx
        │   ├── DashboardPage.jsx
        │   └── LoginPage.jsx
        │
        ├── components/
        │   ├── Map/
        │   │   ├── EventMap.jsx
        │   │   ├── EventMarker.jsx
        │   │   └── ClusterMarker.jsx
        │   │
        │   ├── Dashboard/
        │   │   ├── Dashboard.jsx
        │   │   ├── EventFeed.jsx
        │   │   ├── EventDetail.jsx
        │   │   ├── FilterBar.jsx
        │   │   └── StatsWidgets.jsx
        │   │
        │   ├── Upload/
        │   │   ├── UploadForm.jsx
        │   │   ├── CameraCapture.jsx
        │   │   ├── LocationPicker.jsx
        │   │   └── UploadSuccess.jsx
        │   │
        │   └── common/
        │       ├── Button.jsx
        │       ├── Badge.jsx
        │       ├── Spinner.jsx
        │       └── Toast.jsx
        │
        ├── hooks/
        │   ├── useEventStream.js
        │   ├── useEvents.js
        │   ├── useGeolocation.js
        │   └── useAuth.js
        │
        ├── api/
        │   └── client.js
        │
        ├── utils/
        │   ├── categories.js
        │   ├── severity.js
        │   └── geo.js
        │
        └── styles/
            └── tailwind.css
```

---

## Next Steps

This design document is ready for implementation. The recommended order:

1. **Infrastructure Setup** (Hour 0-2)
   - Docker Compose with all services
   - Backend/Frontend scaffolding

2. **Core API** (Hour 2-6)
   - Models + migrations
   - Upload endpoint
   - Events list endpoint

3. **Processing Pipeline** (Hour 6-14)
   - Celery tasks
   - Media storage
   - AI classification

4. **Real-time + Map** (Hour 14-24)
   - SSE implementation
   - Leaflet map
   - Live updates

5. **Dashboard UX** (Hour 24-36)
   - Event feed
   - Triage actions
   - Stats widgets

6. **Polish + Demo** (Hour 36-48)
   - Seed data
   - Mobile testing
   - Bug fixes

---

*Document generated for Attention Map hackathon project.*
