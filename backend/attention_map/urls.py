"""
URL configuration for attention_map project.
"""

from django.contrib import admin
from django.urls import path
from ninja_extra import NinjaExtraAPI
from ninja_jwt.controller import NinjaJWTDefaultController

from api.auth import auth_router
from api.routes import router as events_router
from api.streaming import stream_events

# Create API instance with NinjaExtraAPI for JWT controller support
api = NinjaExtraAPI(
    title="Attention Map API",
    version="1.0.0",
    description="Civic event monitoring platform API",
)

# Register JWT controller for token endpoints
api.register_controllers(NinjaJWTDefaultController)

# Register routers
api.add_router("/", events_router)
api.add_router("/auth", auth_router)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", api.urls),
    path("api/v1/events/stream", stream_events, name="events_stream"),
]
