"""
URL configuration for attention_map project.
"""

from django.contrib import admin
from django.urls import path
from ninja import NinjaAPI

from api.routes import router as events_router
from api.streaming import stream_events

# Create API instance
api = NinjaAPI(
    title="Attention Map API",
    version="1.0.0",
    description="Civic event monitoring platform API",
)

# Register routers
api.add_router("/", events_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("api/v1/events/stream", stream_events, name="events_stream"),
]
