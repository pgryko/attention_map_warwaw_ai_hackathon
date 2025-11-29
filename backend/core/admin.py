"""
Admin configuration for core models.
"""

from django.contrib import admin
from django.contrib.gis.admin import GISModelAdmin

from .models import Event, EventCluster, UserProfile


@admin.register(Event)
class EventAdmin(GISModelAdmin):
    """Admin for Event model with map widget."""

    list_display = [
        "id",
        "category",
        "severity",
        "status",
        "created_at",
        "reporter",
    ]
    list_filter = ["category", "severity", "status", "created_at"]
    search_fields = ["id", "description", "address"]
    readonly_fields = ["id", "created_at", "ai_confidence", "ai_reasoning"]
    ordering = ["-created_at"]


@admin.register(EventCluster)
class EventClusterAdmin(GISModelAdmin):
    """Admin for EventCluster model."""

    list_display = [
        "id",
        "event_count",
        "computed_severity",
        "first_event_at",
        "last_event_at",
    ]
    list_filter = ["computed_severity"]
    readonly_fields = ["id", "first_event_at", "last_event_at"]


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """Admin for UserProfile model."""

    list_display = [
        "user",
        "reports_submitted",
        "reports_verified",
        "reputation_score",
        "created_at",
    ]
    search_fields = ["user__username", "user__email"]
    readonly_fields = ["created_at"]
