"""
Authentication routes for Attention Map.
"""

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.http import HttpRequest
from ninja import Router
from ninja_jwt.authentication import JWTAuth

from core.models import UserProfile
from services.gamification import GamificationService

from .schemas import (
    BadgeOut,
    ErrorOut,
    LeaderboardEntryOut,
    LeaderboardOut,
    ProfileUpdateIn,
    RegisterIn,
    RegisterOut,
    UserOut,
    UserProfileOut,
    UserStatsOut,
)

auth_router = Router(tags=["auth"])


def user_to_schema(user: User) -> UserOut:
    """Convert User model to output schema."""
    return UserOut(
        id=user.id,
        username=user.username,
        email=user.email,
        is_staff=user.is_staff,
    )


def profile_to_schema(profile: UserProfile) -> UserProfileOut:
    """Convert UserProfile model to output schema."""
    return UserProfileOut(
        user=user_to_schema(profile.user),
        reports_submitted=profile.reports_submitted,
        reports_verified=profile.reports_verified,
        badges=profile.badges,
        reputation_score=profile.reputation_score,
    )


# ─────────────────────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────────────────────


@auth_router.post(
    "/register",
    response={201: RegisterOut, 400: ErrorOut},
    summary="Register a new user",
)
def register(
    request: HttpRequest, data: RegisterIn
) -> tuple[int, RegisterOut | ErrorOut]:
    """
    Register a new user account.

    Creates a user and associated profile for gamification tracking.
    """
    # Validate email
    if "@" not in data.email:
        return 400, ErrorOut(detail="Invalid email address")

    # Validate password
    if len(data.password) < 8:
        return 400, ErrorOut(detail="Password must be at least 8 characters")

    # Derive username from email if not provided
    username = data.username or data.email.split("@")[0]

    # Validate username
    if len(username) < 3:
        return 400, ErrorOut(detail="Username must be at least 3 characters")

    try:
        # Create user
        user = User.objects.create_user(
            username=username,
            email=data.email,
            password=data.password,
        )

        # Create profile
        UserProfile.objects.create(user=user)

        return 201, RegisterOut(
            id=user.id,
            username=user.username,
            email=user.email,
        )

    except IntegrityError:
        return 400, ErrorOut(detail="Username or email already exists")


# ─────────────────────────────────────────────────────────────
# Profile Management
# ─────────────────────────────────────────────────────────────


@auth_router.get(
    "/me",
    auth=JWTAuth(),
    response=UserProfileOut,
    summary="Get current user profile",
)
def get_profile(request: HttpRequest) -> UserProfileOut:
    """
    Get the current authenticated user's profile.

    Returns user details and gamification stats (badges, reputation).
    """
    user = request.auth
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile_to_schema(profile)


@auth_router.patch(
    "/me",
    auth=JWTAuth(),
    response={200: UserProfileOut, 400: ErrorOut},
    summary="Update current user profile",
)
def update_profile(
    request: HttpRequest, data: ProfileUpdateIn
) -> tuple[int, UserProfileOut | ErrorOut]:
    """
    Update the current authenticated user's profile.

    Only email can be updated via this endpoint.
    """
    user = request.auth

    if data.email is not None:
        if "@" not in data.email:
            return 400, ErrorOut(detail="Invalid email address")

        # Check if email is already taken
        if User.objects.filter(email=data.email).exclude(id=user.id).exists():
            return 400, ErrorOut(detail="Email already in use")

        user.email = data.email
        user.save()

    profile, _ = UserProfile.objects.get_or_create(user=user)
    return 200, profile_to_schema(profile)


# ─────────────────────────────────────────────────────────────
# Gamification Endpoints
# ─────────────────────────────────────────────────────────────


@auth_router.get(
    "/me/stats",
    auth=JWTAuth(),
    response=UserStatsOut,
    summary="Get detailed user statistics",
)
def get_user_stats(request: HttpRequest) -> UserStatsOut:
    """
    Get detailed statistics for the current user.

    Includes:
    - Report counts and verification rate
    - Reputation score and leaderboard rank
    - Earned badges with details
    - Progress towards next badges
    """
    user = request.auth
    profile, _ = UserProfile.objects.get_or_create(user=user)

    gamification = GamificationService()
    stats = gamification.get_user_stats(profile)

    return UserStatsOut(
        reports_submitted=stats["reports_submitted"],
        reports_verified=stats["reports_verified"],
        verification_rate=stats["verification_rate"],
        reputation_score=stats["reputation_score"],
        rank=stats["rank"],
        badges=[BadgeOut(**b) for b in stats["badges"]],
        badge_count=stats["badge_count"],
        next_report_badge=stats["next_report_badge"],
        next_verified_badge=stats["next_verified_badge"],
    )


@auth_router.get(
    "/leaderboard",
    response=LeaderboardOut,
    summary="Get the reputation leaderboard",
)
def get_leaderboard(request: HttpRequest, limit: int = 10) -> LeaderboardOut:
    """
    Get the top users by reputation score.

    Returns the leaderboard with user rankings, reputation scores,
    and report statistics.
    """
    limit = min(limit, 100)  # Cap at 100

    gamification = GamificationService()
    entries = gamification.get_leaderboard(limit=limit)

    total_users = UserProfile.objects.count()

    return LeaderboardOut(
        entries=[LeaderboardEntryOut(**e) for e in entries],
        total_users=total_users,
    )


@auth_router.get(
    "/badges",
    response=list[BadgeOut],
    summary="Get all available badges",
)
def get_all_badges(request: HttpRequest) -> list[BadgeOut]:
    """
    Get all available badges in the system.

    Returns all badge definitions with their requirements.
    """
    gamification = GamificationService()
    badges = gamification.get_all_badges()

    return [BadgeOut(**b) for b in badges]
