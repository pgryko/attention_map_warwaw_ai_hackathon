"""
Pydantic schemas for the API.
"""

from datetime import datetime
from typing import Literal
from uuid import UUID

from ninja import Schema


# ─────────────────────────────────────────────────────────────
# Event Schemas
# ─────────────────────────────────────────────────────────────


class EventUploadIn(Schema):
    """Input schema for event upload."""

    latitude: float
    longitude: float
    description: str = ""


class EventUploadOut(Schema):
    """Response schema for event upload."""

    id: UUID
    status: str = "processing"
    message: str = "Event received, processing..."


class EventOut(Schema):
    """Output schema for event details."""

    id: UUID
    created_at: datetime

    # Location
    latitude: float
    longitude: float
    address: str

    # Content
    description: str
    media_url: str
    media_type: str
    thumbnail_url: str

    # AI Classification
    category: str
    subcategory: str
    severity: int
    ai_confidence: float | None

    # Clustering
    cluster_id: UUID | None

    # Triage
    status: str
    reviewed_by_id: int | None
    reviewed_at: datetime | None


class EventListOut(Schema):
    """Output schema for event list."""

    events: list[EventOut]
    total: int
    limit: int
    offset: int


class EventStatusUpdateIn(Schema):
    """Input schema for status update."""

    status: Literal["reviewing", "verified", "resolved", "false_alarm"]


# ─────────────────────────────────────────────────────────────
# Cluster Schemas
# ─────────────────────────────────────────────────────────────


class ClusterOut(Schema):
    """Output schema for event cluster."""

    id: UUID
    latitude: float
    longitude: float
    event_count: int
    computed_severity: int
    first_event_at: datetime
    last_event_at: datetime


# ─────────────────────────────────────────────────────────────
# Stats Schemas
# ─────────────────────────────────────────────────────────────


class StatsOut(Schema):
    """Output schema for dashboard stats."""

    total_events: int
    events_by_status: dict[str, int]
    events_by_category: dict[str, int]
    events_by_severity: dict[str, int]
    active_clusters: int


# ─────────────────────────────────────────────────────────────
# Auth Schemas
# ─────────────────────────────────────────────────────────────


class UserOut(Schema):
    """Output schema for user details."""

    id: int
    username: str
    email: str


class UserProfileOut(Schema):
    """Output schema for user profile."""

    user: UserOut
    reports_submitted: int
    reports_verified: int
    badges: list[str]
    reputation_score: int


# ─────────────────────────────────────────────────────────────
# Error Schemas
# ─────────────────────────────────────────────────────────────


class ErrorOut(Schema):
    """Standard error response."""

    detail: str
