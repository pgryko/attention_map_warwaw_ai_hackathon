# Attention Map - Project Context

## Quick Reference

### What is this project?
Civic event monitoring platform - citizens upload incident reports (fires, accidents, potholes), AI classifies them, operators view on real-time map.

### Tech Stack (Memorize)
- **Backend**: Django 5 + Django Ninja
- **Queue**: Celery + Redis
- **DB**: PostgreSQL + PostGIS
- **Storage**: MinIO (dev) / R2 (prod)
- **AI**: OpenAI API (text + vision)
- **Frontend**: React + Vite + Leaflet.js
- **Real-time**: SSE (NOT Django Channels)
- **Container**: Docker Compose

### Key Files
- `SPECIFICATION.md` - Product specification with 50+ requirements
- `DESIGN.md` - Complete system design with diagrams, schemas, API specs
- `DESIGN.md` - Complete system design with diagrams, schemas, API specs
- `docker-compose.yml` - All services configuration
- `backend/` - Django project
- `frontend/` - React project

### Critical Design Choices
1. **SSE over WebSockets** - One-way push is sufficient
2. **Leaflet over MapLibre** - Simpler, faster for hackathon
3. **Responsive web over native app** - Time constraint
4. **OpenAI API over local models** - No GPU infra

### Database Models
- `Event` - Core incident report with PostGIS Point location
- `EventCluster` - Groups nearby events (100m/30min)
- `UserProfile` - Gamification badges

### API Endpoints (Main)
- `POST /api/v1/events/upload` - Submit incident
- `GET /api/v1/events` - List with spatial filters
- `GET /api/v1/events/stream` - SSE real-time
- `PATCH /api/v1/events/{id}/status` - Triage action

### Celery Pipeline
1. Store media → MinIO
2. Extract keyframe → FFmpeg
3. Transcribe audio → Groq Whisper
4. Classify → OpenRouter API (text + vision)
5. Cluster → PostGIS ST_DWithin
6. Broadcast → Redis pub/sub → SSE

### Implementation Status (205 tests passing)
- ✅ Phase 1: JWT Authentication
- ✅ Phase 2: Video Keyframe Extraction (FFmpeg)
- ✅ Phase 3: Audio Transcription (Groq Whisper)
- ✅ Phase 4: Gamification (badges, reputation, leaderboard)
- ⏳ Frontend: Spec complete (FRONTEND_SPEC.md), implementation pending

### Frontend Spec Summary
- **Tech**: TanStack Query + Tailwind CSS
- **Theme**: Light/dark toggle
- **Priority Features**: SSE real-time, media upload, triage workflow
- **Phases**: 6 phases, ~44 components total

### User's Background
- Familiar with: Python, Django, Django Ninja
- Django Channels experience: "messy"
- Has Telegram video scrapes for demo data

### Deployment Targets
- Poland, UK, US (eventually)
- Map tiles: OpenStreetMap
- Start municipal (single city), expand later
