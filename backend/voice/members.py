"""Voice channel member tracking and diff detection"""

from typing import Dict, List, Set
from dataclasses import dataclass


@dataclass
class MemberInfo:
    """Voice channel member information"""
    user_id: str
    username: str
    avatar: str | None

    def to_dict(self) -> Dict[str, any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "avatar": self.avatar
        }


class MemberTracker:
    """
    Tracks voice channel members and detects join/leave events.

    Maintains a cache of previous state to compute diffs efficiently.
    """

    def __init__(self):
        """Initialize member tracker with empty state."""
        self.previous_members: Dict[str, MemberInfo] = {}
        self.initial_sync_done = False

    def initialize(self, members: List[Dict[str, any]]) -> None:
        """
        Initialize tracker with current members (silent sync).

        Call this when first joining a channel to avoid spurious join notifications.

        Args:
            members: List of member dictionaries from Discord
        """
        self.previous_members = {}

        for member_data in members:
            user_id = member_data.get("user_id")
            if user_id:
                self.previous_members[user_id] = MemberInfo(
                    user_id=user_id,
                    username=member_data.get("username", "User"),
                    avatar=member_data.get("avatar")
                )

        self.initial_sync_done = True

    def update_and_get_diff(self, current_members: List[Dict[str, any]]) -> Dict[str, List[Dict[str, any]]]:
        """
        Update member state and return diff since last update.

        Args:
            current_members: Current member list from Discord

        Returns:
            Dictionary with 'joined', 'left', and 'current_count' keys

        Example:
            >>> diff = tracker.update_and_get_diff(members)
            >>> diff['joined']
            [{"user_id": "123", "username": "Alice", "avatar": "..."}]
            >>> diff['left']
            []
            >>> diff['current_count']
            5
        """
        # Build current state
        current_member_map: Dict[str, MemberInfo] = {}
        for member_data in current_members:
            user_id = member_data.get("user_id")
            if user_id:
                current_member_map[user_id] = MemberInfo(
                    user_id=user_id,
                    username=member_data.get("username", "User"),
                    avatar=member_data.get("avatar")
                )

        # Calculate diffs
        current_ids = set(current_member_map.keys())
        previous_ids = set(self.previous_members.keys())

        joined_ids = current_ids - previous_ids
        left_ids = previous_ids - current_ids

        joined_info = [current_member_map[uid].to_dict() for uid in joined_ids]
        left_info = [self.previous_members[uid].to_dict() for uid in left_ids]

        # Update cache
        self.previous_members = current_member_map

        return {
            "joined": joined_info,
            "left": left_info,
            "current_count": len(current_member_map)
        }

    def should_emit_events(self) -> bool:
        """
        Check if events should be emitted.

        Returns False during initial sync to avoid spurious notifications.

        Returns:
            True if events should be emitted
        """
        return self.initial_sync_done

    def reset(self) -> None:
        """Reset tracker state (e.g., when leaving channel)."""
        self.previous_members = {}
        self.initial_sync_done = False

    def get_current_member_ids(self) -> Set[str]:
        """
        Get set of current member user IDs.

        Returns:
            Set of user ID strings
        """
        return set(self.previous_members.keys())

    def get_member_count(self) -> int:
        """
        Get current member count.

        Returns:
            Number of members in channel
        """
        return len(self.previous_members)
