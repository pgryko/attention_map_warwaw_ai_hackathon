# Attention Map Backend - Implementation Plan

## Overview

This plan covers the remaining features needed to complete the backend:

1. **User Authentication** (Priority 1)
2. **Video Keyframe Extraction** (Priority 1)
3. **Audio Transcription Integration** (Priority 2)
4. **User Profile API** (Priority 2)

---

## Phase 1: User Authentication

### Approach
Use `django-ninja-jwt` for JWT-based authentication. This integrates seamlessly with Django Ninja and provides:
- Token obtain (login)
- Token refresh
- Token verify
- Built-in auth decorators

### New Dependencies
```bash
pip install django-ninja-jwt
```

### Implementation Steps

#### 1.1 Install and Configure JWT
**File: `attention_map/settings.py`**
- Add `ninja_jwt` to `INSTALLED_APPS`
- Add `NINJA_JWT` configuration:
  ```python
  NINJA_JWT = {
      'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
      'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
      'ROTATE_REFRESH_TOKENS': True,
      'ALGORITHM': 'HS256',
      'SIGNING_KEY': SECRET_KEY,
      'USER_ID_FIELD': 'id',
      'USER_ID_CLAIM': 'user_id',
  }
  ```

#### 1.2 Create Auth Schemas
**File: `api/schemas.py`**
```python
class RegisterIn(Schema):
    username: str
    email: str
    password: str

class RegisterOut(Schema):
    id: int
    username: str
    email: str
    message: str = "Registration successful"

class LoginOut(Schema):
    access: str
    refresh: str
    user: UserOut
```

#### 1.3 Create Auth Routes
**File: `api/auth.py`** (new file)
```python
from ninja import Router
from ninja_jwt.authentication import JWTAuth
from ninja_jwt.controller import NinjaJWTDefaultController
from django.contrib.auth.models import User
from core.models import UserProfile

auth_router = Router(tags=["auth"])

@auth_router.post("/register", response={201: RegisterOut, 400: ErrorOut})
def register(request, data: RegisterIn):
    # Create user and profile
    ...

@auth_router.get("/me", auth=JWTAuth(), response=UserProfileOut)
def get_profile(request):
    # Return current user profile
    ...

@auth_router.patch("/me", auth=JWTAuth(), response=UserProfileOut)
def update_profile(request, data: ProfileUpdateIn):
    # Update profile
    ...
```

#### 1.4 Register JWT Controller
**File: `api/__init__.py`**
```python
from ninja import NinjaAPI
from ninja_jwt.controller import NinjaJWTDefaultController

api = NinjaAPI()
api.register_controllers(NinjaJWTDefaultController)
api.add_router("/auth/", auth_router)
```

#### 1.5 Protect Triage Endpoint
**File: `api/routes.py`**
- Add `auth=JWTAuth()` to `update_event_status`
- Add staff check: `if not request.auth.is_staff: return 403, ...`

#### 1.6 Track Reporter on Upload
**File: `api/routes.py`**
- Optional JWT auth on upload endpoint
- Set `reporter=request.auth` when authenticated

### Tests to Add
- `test_register_creates_user_and_profile`
- `test_register_duplicate_username_fails`
- `test_login_returns_tokens`
- `test_login_invalid_credentials_fails`
- `test_get_profile_requires_auth`
- `test_get_profile_returns_user_data`
- `test_update_status_requires_staff`
- `test_upload_tracks_reporter_when_authenticated`

---

## Phase 2: Video Keyframe Extraction

### Approach
Use `ffmpeg-python` to extract a frame from uploaded videos. Store thumbnail in MinIO.

### New Dependencies
```bash
pip install ffmpeg-python
# System: apt install ffmpeg
```

### Implementation Steps

#### 2.1 Create Keyframe Service
**File: `services/keyframe.py`** (new file)
```python
import ffmpeg
import tempfile
from .storage import StorageService

class KeyframeService:
    def __init__(self):
        self.storage = StorageService()

    def extract_keyframe(
        self,
        video_data: bytes,
        event_id: str,
        timestamp: float = 1.0
    ) -> str:
        """
        Extract a keyframe from video at given timestamp.
        Returns URL of uploaded thumbnail.
        """
        with tempfile.NamedTemporaryFile(suffix='.mp4') as video_file:
            video_file.write(video_data)
            video_file.flush()

            with tempfile.NamedTemporaryFile(suffix='.jpg') as thumb_file:
                # Extract frame using ffmpeg
                (
                    ffmpeg
                    .input(video_file.name, ss=timestamp)
                    .output(thumb_file.name, vframes=1, format='image2')
                    .overwrite_output()
                    .run(quiet=True)
                )

                # Upload to MinIO
                thumb_data = thumb_file.read()
                return self.storage.upload_thumbnail(event_id, thumb_data)
```

#### 2.2 Update Processing Service
**File: `services/processing.py`**
```python
from .keyframe import KeyframeService

class EventProcessingService:
    def __init__(self):
        ...
        self.keyframe = KeyframeService()

    def _extract_keyframe(self, event: Event, video_data: bytes) -> Optional[str]:
        return self.keyframe.extract_keyframe(video_data, str(event.id))
```

#### 2.3 Update Celery Task
**File: `tasks/processing.py`**
```python
@shared_task
def extract_keyframe(video_data: bytes, event_id: str) -> str:
    from services.keyframe import KeyframeService
    service = KeyframeService()
    return service.extract_keyframe(video_data, event_id)
```

#### 2.4 Pass Video Data Through Pipeline
**File: `tasks/processing.py`**
- Modify `process_event` to pass video bytes to keyframe extraction
- Store video data temporarily or download from MinIO URL

### Tests to Add
- `test_extract_keyframe_creates_thumbnail`
- `test_extract_keyframe_handles_invalid_video`
- `test_extract_keyframe_uploads_to_minio`
- `test_processing_extracts_keyframe_for_video`

---

## Phase 3: Audio Transcription Integration

### Approach
Wire existing `transcribe_audio` task into the processing pipeline. Extract audio from videos for transcription.

### Implementation Steps

#### 3.1 Add Audio Extraction
**File: `services/keyframe.py`** (rename to `services/media.py`)
```python
class MediaService:
    def extract_audio(self, video_data: bytes) -> bytes:
        """Extract audio track from video as MP3."""
        with tempfile.NamedTemporaryFile(suffix='.mp4') as video_file:
            video_file.write(video_data)
            video_file.flush()

            with tempfile.NamedTemporaryFile(suffix='.mp3') as audio_file:
                (
                    ffmpeg
                    .input(video_file.name)
                    .output(audio_file.name, acodec='libmp3lame', ac=1, ar='16000')
                    .overwrite_output()
                    .run(quiet=True)
                )
                return audio_file.read()
```

#### 3.2 Update Processing Pipeline
**File: `services/processing.py`**
```python
def process_event(self, event, media_data, media_content_type):
    ...
    # Step 2b: Transcribe audio (if video)
    if event.media_type == "video" and media_data:
        try:
            audio_data = self.media.extract_audio(media_data)
            transcription = transcribe_audio(audio_data)
            if transcription:
                # Append to description for better classification
                event.description = f"{event.description}\n\n[Audio]: {transcription}"
                event.save()
        except Exception as e:
            logger.warning(f"Audio transcription failed: {e}")
```

#### 3.3 Update Celery Task
**File: `tasks/processing.py`**
- Call `transcribe_audio` in `process_event` task
- Add transcription to event description before classification

### Tests to Add
- `test_extract_audio_from_video`
- `test_transcription_added_to_description`
- `test_classification_uses_transcription`

---

## Phase 4: User Profile API

### Approach
Expose profile endpoints for gamification features.

### Implementation Steps

#### 4.1 Add Profile Endpoints
**File: `api/auth.py`**
```python
@auth_router.get("/me/stats", auth=JWTAuth(), response=UserStatsOut)
def get_user_stats(request):
    profile = request.auth.profile
    return UserStatsOut(
        reports_submitted=profile.reports_submitted,
        reports_verified=profile.reports_verified,
        badges=profile.badges,
        reputation_score=profile.reputation_score,
    )
```

#### 4.2 Track Report Submissions
**File: `api/routes.py`**
```python
def upload_event(...):
    ...
    # Increment user's report count
    if request.auth and hasattr(request.auth, 'profile'):
        profile = request.auth.profile
        profile.reports_submitted += 1
        profile.save()
```

#### 4.3 Track Verified Reports
**File: `api/routes.py`**
```python
def update_event_status(...):
    ...
    # If verified, credit the original reporter
    if data.status == "verified" and event.reporter:
        reporter_profile = event.reporter.profile
        reporter_profile.reports_verified += 1
        reporter_profile.reputation_score += 10
        reporter_profile.save()
```

#### 4.4 Badge System
**File: `services/gamification.py`** (new file)
```python
BADGES = {
    "first_report": {"name": "First Report", "threshold": 1},
    "reporter_10": {"name": "Active Reporter", "threshold": 10},
    "verified_5": {"name": "Trusted Source", "threshold": 5},
}

def check_and_award_badges(profile: UserProfile) -> list[str]:
    new_badges = []
    if profile.reports_submitted >= 1 and "first_report" not in profile.badges:
        profile.badges.append("first_report")
        new_badges.append("first_report")
    # ... more badge checks
    return new_badges
```

### Tests to Add
- `test_upload_increments_reports_submitted`
- `test_verify_increments_reports_verified`
- `test_badge_awarded_on_first_report`
- `test_reputation_increases_on_verify`

---

## File Changes Summary

### New Files
| File | Purpose |
|------|---------|
| `api/auth.py` | Auth routes (register, profile) |
| `services/media.py` | Video keyframe & audio extraction |
| `services/gamification.py` | Badge system |

### Modified Files
| File | Changes |
|------|---------|
| `attention_map/settings.py` | Add ninja_jwt config |
| `api/__init__.py` | Register JWT controller |
| `api/routes.py` | Add auth to triage, track reporter |
| `api/schemas.py` | Add auth schemas |
| `services/processing.py` | Integrate keyframe & transcription |
| `tasks/processing.py` | Update keyframe task, add transcription |

### New Dependencies
```
django-ninja-jwt>=5.3.0
ffmpeg-python>=0.2.0
```

---

## Test Count Estimate

| Phase | New Tests |
|-------|-----------|
| Phase 1: Auth | ~15 tests |
| Phase 2: Keyframe | ~8 tests |
| Phase 3: Transcription | ~6 tests |
| Phase 4: Profile | ~10 tests |
| **Total** | **~39 tests** |

Current: 127 tests
Expected: ~166 tests

---

## Implementation Order

1. **Phase 1: User Authentication** - Foundation for other features
2. **Phase 4: User Profile API** - Depends on auth
3. **Phase 2: Video Keyframe** - Independent, can parallel with Phase 4
4. **Phase 3: Audio Transcription** - Depends on Phase 2 (ffmpeg setup)

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| ffmpeg not installed | Add dockerfile/CI check, graceful degradation |
| Groq API rate limits | Queue transcription, add retry logic |
| Large video files | Stream processing, file size limits |
| JWT token security | Use short access lifetime, rotate refresh |
