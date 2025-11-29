"""
Gamification service for user badges and reputation.

Manages badge awards, reputation scoring, and leaderboard calculations.
"""

import logging
from dataclasses import dataclass
from typing import Optional

from django.db.models import F

from core.models import UserProfile

logger = logging.getLogger(__name__)


@dataclass
class BadgeDefinition:
    """Definition of a badge that can be earned."""

    id: str
    name: str
    description: str
    icon: str  # Emoji or icon identifier
    category: str  # "reports", "verified", "reputation", "special"
    threshold: Optional[int] = None  # For milestone badges


# Badge definitions
BADGE_DEFINITIONS: dict[str, BadgeDefinition] = {
    # Report milestones
    "first_report": BadgeDefinition(
        id="first_report",
        name="First Reporter",
        description="Submitted your first report",
        icon="flag",
        category="reports",
        threshold=1,
    ),
    "reporter_10": BadgeDefinition(
        id="reporter_10",
        name="Active Reporter",
        description="Submitted 10 reports",
        icon="megaphone",
        category="reports",
        threshold=10,
    ),
    "reporter_50": BadgeDefinition(
        id="reporter_50",
        name="Dedicated Reporter",
        description="Submitted 50 reports",
        icon="star",
        category="reports",
        threshold=50,
    ),
    "reporter_100": BadgeDefinition(
        id="reporter_100",
        name="Champion Reporter",
        description="Submitted 100 reports",
        icon="trophy",
        category="reports",
        threshold=100,
    ),
    # Verification milestones
    "first_verified": BadgeDefinition(
        id="first_verified",
        name="Trusted Source",
        description="Had your first report verified",
        icon="check",
        category="verified",
        threshold=1,
    ),
    "verified_10": BadgeDefinition(
        id="verified_10",
        name="Reliable Reporter",
        description="Had 10 reports verified",
        icon="shield",
        category="verified",
        threshold=10,
    ),
    "verified_25": BadgeDefinition(
        id="verified_25",
        name="Accuracy Expert",
        description="Had 25 reports verified",
        icon="medal",
        category="verified",
        threshold=25,
    ),
    "verified_50": BadgeDefinition(
        id="verified_50",
        name="Verification Master",
        description="Had 50 reports verified",
        icon="crown",
        category="verified",
        threshold=50,
    ),
    # Reputation milestones
    "reputation_100": BadgeDefinition(
        id="reputation_100",
        name="Rising Star",
        description="Reached 100 reputation points",
        icon="sparkles",
        category="reputation",
        threshold=100,
    ),
    "reputation_500": BadgeDefinition(
        id="reputation_500",
        name="Community Leader",
        description="Reached 500 reputation points",
        icon="gem",
        category="reputation",
        threshold=500,
    ),
    "reputation_1000": BadgeDefinition(
        id="reputation_1000",
        name="City Guardian",
        description="Reached 1000 reputation points",
        icon="shield_star",
        category="reputation",
        threshold=1000,
    ),
    # Special badges
    "early_adopter": BadgeDefinition(
        id="early_adopter",
        name="Early Adopter",
        description="Joined during the early access period",
        icon="rocket",
        category="special",
    ),
    "night_owl": BadgeDefinition(
        id="night_owl",
        name="Night Owl",
        description="Submitted a report between midnight and 5am",
        icon="moon",
        category="special",
    ),
    "emergency_responder": BadgeDefinition(
        id="emergency_responder",
        name="Emergency Responder",
        description="Reported a verified critical emergency",
        icon="siren",
        category="special",
    ),
}


# Reputation point values
REPUTATION_POINTS = {
    "report_submitted": 5,
    "report_verified": 10,
    "report_false_alarm": -5,
    "critical_verified": 25,  # Bonus for critical emergencies
}


class GamificationService:
    """
    Service for managing user gamification features.

    Handles:
    - Badge awards based on milestones
    - Reputation point calculations
    - Leaderboard generation
    """

    def __init__(self):
        """Initialize the gamification service."""
        self.badges = BADGE_DEFINITIONS
        self.points = REPUTATION_POINTS

    def get_badge_definition(self, badge_id: str) -> Optional[BadgeDefinition]:
        """Get a badge definition by ID."""
        return self.badges.get(badge_id)

    def get_all_badges(self) -> list[dict]:
        """Get all badge definitions as dictionaries."""
        return [
            {
                "id": b.id,
                "name": b.name,
                "description": b.description,
                "icon": b.icon,
                "category": b.category,
                "threshold": b.threshold,
            }
            for b in self.badges.values()
        ]

    def check_and_award_badges(self, profile: UserProfile) -> list[str]:
        """
        Check if user qualifies for any new badges and award them.

        Args:
            profile: The UserProfile to check

        Returns:
            List of newly awarded badge IDs
        """
        newly_awarded = []
        current_badges = set(profile.badges or [])

        # Check report milestone badges
        report_badges = [
            ("first_report", 1),
            ("reporter_10", 10),
            ("reporter_50", 50),
            ("reporter_100", 100),
        ]
        for badge_id, threshold in report_badges:
            if (
                badge_id not in current_badges
                and profile.reports_submitted >= threshold
            ):
                newly_awarded.append(badge_id)

        # Check verification milestone badges
        verified_badges = [
            ("first_verified", 1),
            ("verified_10", 10),
            ("verified_25", 25),
            ("verified_50", 50),
        ]
        for badge_id, threshold in verified_badges:
            if badge_id not in current_badges and profile.reports_verified >= threshold:
                newly_awarded.append(badge_id)

        # Check reputation milestone badges
        reputation_badges = [
            ("reputation_100", 100),
            ("reputation_500", 500),
            ("reputation_1000", 1000),
        ]
        for badge_id, threshold in reputation_badges:
            if badge_id not in current_badges and profile.reputation_score >= threshold:
                newly_awarded.append(badge_id)

        # Award new badges
        if newly_awarded:
            profile.badges = list(current_badges | set(newly_awarded))
            profile.save(update_fields=["badges"])
            logger.info(
                f"Awarded badges to user {profile.user.username}: {newly_awarded}"
            )

        return newly_awarded

    def award_special_badge(self, profile: UserProfile, badge_id: str) -> bool:
        """
        Award a special badge to a user.

        Args:
            profile: The UserProfile to award
            badge_id: The special badge ID

        Returns:
            True if badge was newly awarded, False if already had it
        """
        if badge_id not in self.badges:
            logger.warning(f"Unknown badge ID: {badge_id}")
            return False

        current_badges = set(profile.badges or [])
        if badge_id in current_badges:
            return False

        profile.badges = list(current_badges | {badge_id})
        profile.save(update_fields=["badges"])
        logger.info(f"Awarded special badge '{badge_id}' to {profile.user.username}")
        return True

    def add_reputation(
        self,
        profile: UserProfile,
        points: int,
        reason: str = "",
    ) -> int:
        """
        Add reputation points to a user profile.

        Args:
            profile: The UserProfile to update
            points: Points to add (can be negative)
            reason: Reason for the points change

        Returns:
            New reputation score
        """
        profile.reputation_score = F("reputation_score") + points
        profile.save(update_fields=["reputation_score"])
        profile.refresh_from_db()

        logger.info(
            f"Updated reputation for {profile.user.username}: "
            f"{'+' if points >= 0 else ''}{points} ({reason})"
        )

        # Check for new reputation badges
        self.check_and_award_badges(profile)

        return profile.reputation_score

    def on_report_submitted(self, profile: UserProfile) -> list[str]:
        """
        Handle gamification updates when a report is submitted.

        Args:
            profile: The reporter's profile

        Returns:
            List of newly awarded badges
        """
        # Increment is already done in the API, just check badges
        return self.check_and_award_badges(profile)

    def on_report_verified(
        self,
        profile: UserProfile,
        is_critical: bool = False,
    ) -> list[str]:
        """
        Handle gamification updates when a report is verified.

        Args:
            profile: The reporter's profile
            is_critical: Whether the report was critical severity

        Returns:
            List of newly awarded badges
        """
        # Add reputation points
        points = self.points["report_verified"]
        if is_critical:
            points += self.points["critical_verified"]
            # Award emergency responder badge
            self.award_special_badge(profile, "emergency_responder")

        self.add_reputation(profile, points, "report_verified")

        # Check for milestone badges
        return self.check_and_award_badges(profile)

    def on_report_rejected(self, profile: UserProfile) -> None:
        """
        Handle gamification updates when a report is marked as false alarm.

        Args:
            profile: The reporter's profile
        """
        points = self.points["report_false_alarm"]
        self.add_reputation(profile, points, "false_alarm")

    def get_leaderboard(self, limit: int = 10) -> list[dict]:
        """
        Get the top users by reputation score.

        Args:
            limit: Maximum number of users to return

        Returns:
            List of leaderboard entries
        """
        profiles = (
            UserProfile.objects.select_related("user")
            .order_by("-reputation_score", "-reports_verified", "-reports_submitted")
            .values(
                "user__id",
                "user__username",
                "reputation_score",
                "reports_submitted",
                "reports_verified",
                "badges",
            )[:limit]
        )

        return [
            {
                "rank": idx + 1,
                "user_id": p["user__id"],
                "username": p["user__username"],
                "reputation_score": p["reputation_score"],
                "reports_submitted": p["reports_submitted"],
                "reports_verified": p["reports_verified"],
                "badge_count": len(p["badges"] or []),
            }
            for idx, p in enumerate(profiles)
        ]

    def get_user_rank(self, profile: UserProfile) -> int:
        """
        Get a user's rank on the leaderboard.

        Args:
            profile: The user's profile

        Returns:
            The user's rank (1-indexed)
        """
        rank = (
            UserProfile.objects.filter(
                reputation_score__gt=profile.reputation_score
            ).count()
            + 1
        )
        return rank

    def get_user_stats(self, profile: UserProfile) -> dict:
        """
        Get detailed statistics for a user.

        Args:
            profile: The user's profile

        Returns:
            Dictionary with user statistics
        """
        badge_details = []
        for badge_id in profile.badges or []:
            badge_def = self.get_badge_definition(badge_id)
            if badge_def:
                badge_details.append(
                    {
                        "id": badge_def.id,
                        "name": badge_def.name,
                        "description": badge_def.description,
                        "icon": badge_def.icon,
                        "category": badge_def.category,
                    }
                )

        return {
            "reports_submitted": profile.reports_submitted,
            "reports_verified": profile.reports_verified,
            "verification_rate": (
                round(profile.reports_verified / profile.reports_submitted * 100, 1)
                if profile.reports_submitted > 0
                else 0.0
            ),
            "reputation_score": profile.reputation_score,
            "rank": self.get_user_rank(profile),
            "badges": badge_details,
            "badge_count": len(badge_details),
            "next_report_badge": self._get_next_badge(
                profile.reports_submitted,
                [1, 10, 50, 100],
                ["first_report", "reporter_10", "reporter_50", "reporter_100"],
            ),
            "next_verified_badge": self._get_next_badge(
                profile.reports_verified,
                [1, 10, 25, 50],
                ["first_verified", "verified_10", "verified_25", "verified_50"],
            ),
        }

    def _get_next_badge(
        self,
        current_value: int,
        thresholds: list[int],
        badge_ids: list[str],
    ) -> Optional[dict]:
        """Get the next achievable badge in a progression."""
        for threshold, badge_id in zip(thresholds, badge_ids):
            if current_value < threshold:
                badge_def = self.get_badge_definition(badge_id)
                if badge_def:
                    return {
                        "id": badge_def.id,
                        "name": badge_def.name,
                        "threshold": threshold,
                        "progress": current_value,
                        "remaining": threshold - current_value,
                    }
        return None
