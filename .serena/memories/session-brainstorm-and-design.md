# Attention Map - Session Summary

## Session Type
Brainstorming and System Design Session

## Date
2024 (48-hour hackathon preparation)

## Project Overview

**Attention Map** is a civic event monitoring platform that enables citizens to report incidents (fires, accidents, infrastructure issues, etc.) via mobile uploads. The system uses AI to classify and prioritize events, displaying them on a real-time map for government operators to triage and respond.

## Key Decisions Made

### Scope & Users
| Decision | Choice |
|----------|--------|
| Initial Scope | Municipal MVP (single city - Warsaw) |
| Target Users | Anonymous uploaders + government operators |
| Upload Source | Mobile devices only (GPS + camera) |
| Multi-source ingestion | Deferred to post-MVP |

### Technical Stack
| Layer | Technology |
|-------|------------|
| Backend API | Django 5 + Django Ninja (async) |
| Task Queue | Celery + Redis |
| Database | PostgreSQL 16 + PostGIS 3.4 |
| Object Storage | MinIO (dev) / Cloudflare R2 (prod) |
| AI Classification | OpenAI GPT-4o-mini + Vision API |
| Frontend | React 18 + Vite + TailwindCSS |
| Map | Leaflet.js + OpenStreetMap |
| Real-time | Server-Sent Events (SSE) - NOT Django Channels |
| Containerization | Docker + Docker Compose |

### Architecture Decisions
| Decision | Choice | Rationale |
|----------|--------|-----------|
| Real-time updates | SSE over WebSockets | Simpler, one-way push is sufficient, Django Channels was "messy" |
| Map library | Leaflet.js over MapLibre | Faster setup, lighter, hackathon-friendly |
| Mobile app | Responsive web (PWA-lite) | No time for native app in 48hrs |
| Video processing | Keyframe extraction (ffmpeg) | Later: YOLO for object detection |
| Classification | Public APIs (OpenAI) | No GPU infra, hackathon speed |
| Gamification | Badges/Achievements | Lower moderation risk than leaderboards |

### Event Taxonomy
Categories: emergency, security, traffic, protest, infrastructure, environmental, informational
Severity: 1 (Low) to 4 (Critical)
Priority Signal: AI severity + volume-based clustering (multiple uploads = higher priority)

## Artifacts Created

### SPECIFICATION.md
Complete product specification containing:
- Executive summary and problem statement
- User personas (Citizen Reporter, Government Operator, Anonymous Contributor)
- 50+ functional requirements with priority and MVP flags
- Non-functional requirements (performance, scalability, reliability)
- Data specifications (categories, severity levels, badges)
- Full API specification with request/response schemas
- UI specifications for mobile upload and operator dashboard
- Security requirements (MVP and future)
- Performance targets and resource limits
- Future roadmap (Phases 2-4)



### DESIGN.md
Comprehensive design document containing:
- System architecture diagrams
- Database schema with PostGIS
- API endpoint specifications
- React component architecture
- Celery processing pipeline
- SSE real-time implementation
- Docker Compose configuration
- Full project structure

## Hackathon Context
- **Duration**: 48 hours
- **Team**: Solo developer
- **Wow Factor**: Real-time map updates + Dashboard UX
- **Demo Strategy**: Pre-seeded Telegram scrapes + live upload during demo

## 48-Hour Schedule Summary
- Hours 0-8: Foundation (scaffolding, models, upload endpoint)
- Hours 8-16: AI Pipeline (keyframes, classification, clustering)
- Hours 16-28: Map & Real-time (Leaflet, SSE, dashboard UX)
- Hours 28-40: Demo Readiness (seed data, triage, mobile polish)
- Hours 40-48: Buffer & Presentation

## Next Steps
Ready to scaffold the full project structure. User should choose:
1. Start with backend (Django + Celery)
2. Start with frontend (React + Leaflet)
3. Full scaffolding (everything at once)

## Key Insights
- SSE is sufficient for one-way real-time updates (server → client)
- Volume-based emergency detection: multiple simultaneous uploads = high priority
- PostGIS ST_DWithin for 100m/30min clustering is simple and effective
- Classification: merge text + vision AI results for best accuracy
