"""Discord RPC event system"""

from enum import Enum
from typing import Dict, Any, Optional
import time


class EventType(str, Enum):
    """Discord RPC event types"""
    VOICE_SETTINGS_UPDATE = "VOICE_SETTINGS_UPDATE"
    VOICE_CHANNEL_SELECT = "VOICE_CHANNEL_SELECT"
    SPEAKING_START = "SPEAKING_START"
    SPEAKING_STOP = "SPEAKING_STOP"
    VOICE_STATE_UPDATE = "VOICE_STATE_UPDATE"


class SpeakingTracker:
    """
    Tracks which users are currently speaking in voice channel.

    Uses timestamp-based tracking to automatically expire stale entries.
    """

    def __init__(self, expiry_seconds: float = 2.0):
        """
        Initialize speaking tracker.

        Args:
            expiry_seconds: How long to keep users as "speaking" without updates
        """
        self.expiry_seconds = expiry_seconds
        self._speaking_users: Dict[str, float] = {}  # user_id -> timestamp

    def mark_speaking(self, user_id: str) -> None:
        """
        Mark user as currently speaking.

        Args:
            user_id: Discord user ID
        """
        self._speaking_users[user_id] = time.time()

    def mark_stopped(self, user_id: str) -> None:
        """
        Mark user as stopped speaking.

        Args:
            user_id: Discord user ID
        """
        if user_id in self._speaking_users:
            del self._speaking_users[user_id]

    def get_speaking_users(self) -> list[str]:
        """
        Get list of users currently speaking.

        Automatically removes stale entries (older than expiry_seconds).

        Returns:
            List of user IDs currently speaking
        """
        now = time.time()

        # Clean up stale entries
        self._speaking_users = {
            user_id: timestamp
            for user_id, timestamp in self._speaking_users.items()
            if now - timestamp < self.expiry_seconds
        }

        return list(self._speaking_users.keys())

    def is_speaking(self, user_id: str) -> bool:
        """
        Check if user is currently speaking.

        Args:
            user_id: Discord user ID

        Returns:
            True if user is speaking, False otherwise
        """
        if user_id not in self._speaking_users:
            return False

        timestamp = self._speaking_users[user_id]
        is_active = time.time() - timestamp < self.expiry_seconds

        # Clean up if expired
        if not is_active:
            del self._speaking_users[user_id]

        return is_active

    def clear(self) -> None:
        """Clear all speaking users."""
        self._speaking_users.clear()


def process_event(event_payload: Dict[str, Any], speaking_tracker: SpeakingTracker, logger=None) -> Optional[EventType]:
    """
    Process incoming Discord RPC event.

    Args:
        event_payload: Raw event data from Discord
        speaking_tracker: SpeakingTracker instance to update
        logger: Optional logger instance for debug messages

    Returns:
        EventType if recognized, None otherwise
    """
    event_name = event_payload.get("evt")

    if event_name == "SPEAKING_START":
        data = event_payload.get("data", {})
        user_id = data.get("user_id")
        if user_id:
            speaking_tracker.mark_speaking(user_id)
            if logger:
                logger.debug(f"Discord Lite: User {user_id} started speaking")
        return EventType.SPEAKING_START

    elif event_name == "SPEAKING_STOP":
        data = event_payload.get("data", {})
        user_id = data.get("user_id")
        if user_id:
            speaking_tracker.mark_stopped(user_id)
            if logger:
                logger.debug(f"Discord Lite: User {user_id} stopped speaking")
        return EventType.SPEAKING_STOP

    elif event_name == "VOICE_SETTINGS_UPDATE":
        return EventType.VOICE_SETTINGS_UPDATE

    elif event_name == "VOICE_CHANNEL_SELECT":
        return EventType.VOICE_CHANNEL_SELECT

    elif event_name == "VOICE_STATE_UPDATE":
        return EventType.VOICE_STATE_UPDATE

    return None
