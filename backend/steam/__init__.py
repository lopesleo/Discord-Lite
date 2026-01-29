"""Steam game detection and Discord activity sync"""

from .game_detector import SteamGameDetector
from .activity_sync import ActivitySyncManager

__all__ = ['SteamGameDetector', 'ActivitySyncManager']
