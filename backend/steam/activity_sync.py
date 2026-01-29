"""Discord activity synchronization with Steam games"""

import os
import time
import json
import ssl
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from .game_detector import SteamGameDetector
from ..utils.cache import LRUCache
from ..discord_rpc.client import DiscordRPCClient


class ActivitySyncManager:
    """
    Manages Discord activity (Rich Presence) synchronization with Steam games.

    Detects running Steam games and updates Discord status accordingly.
    Uses official Discord app IDs when available for better integration.
    """

    DISCORD_DETECTABLE_APPS_URL = "https://discord.com/api/v10/applications/detectable"
    CACHE_DURATION_SECONDS = 86400  # 24 hours

    def __init__(self, settings_dir: str, main_rpc_client: DiscordRPCClient, logger=None):
        """
        Initialize activity sync manager.

        Args:
            settings_dir: Directory for cache storage
            main_rpc_client: Main Discord RPC client (fallback)
            logger: Logger instance for logging operations
        """
        self.settings_dir = settings_dir
        self.main_rpc = main_rpc_client
        self.logger = logger

        # Game detection
        self.game_detector = SteamGameDetector(logger)

        # Current game state
        self.current_game_appid: Optional[str] = None
        self.current_game_name: Optional[str] = None
        self.game_start_time: Optional[int] = None

        # Game-specific RPC connection (when using official app ID)
        self.game_specific_rpc: Optional[DiscordRPCClient] = None

        # Discord detectable apps cache
        self.discord_apps: list[Dict[str, Any]] = []
        self.discord_apps_last_fetch: float = 0.0
        self.discord_appid_cache = LRUCache(max_size=100)

        # SSL context for API requests
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def sync(self) -> None:
        """
        Synchronize current game with Discord status.

        Call this periodically (e.g., every 15 seconds) to keep status updated.
        """
        try:
            detected_game = self.game_detector.detect_running_game()

            # Game changed
            if detected_game and detected_game["appid"] != self.current_game_appid:
                self._handle_game_start(detected_game)

            # Game closed
            elif not detected_game and self.current_game_appid:
                self._handle_game_stop()

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error in activity sync: {e}")

    def _handle_game_start(self, game_info: Dict[str, str]) -> None:
        """
        Handle new game launch.

        Args:
            game_info: Dictionary with appid, name, image_url
        """
        # Close previous game RPC if exists
        if self.game_specific_rpc:
            try:
                if self.logger:
                    self.logger.info("Discord Lite: Closing previous game RPC connection")
                self.game_specific_rpc.disconnect()
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Discord Lite: Error closing previous RPC: {e}")
            finally:
                self.game_specific_rpc = None

        # Update state
        self.current_game_appid = game_info["appid"]
        self.current_game_name = game_info["name"]
        self.game_start_time = int(time.time())

        if self.logger:
            self.logger.info(f"Discord Lite: Game started - {game_info['name']} (appid: {game_info['appid']})")

        # Find official Discord app ID
        discord_app_id = self._find_discord_app_id(game_info["name"])

        # Build activity payload
        activity = self._build_activity_payload(game_info, discord_app_id)

        # Try official app ID first
        if discord_app_id:
            if self._try_official_app_id(discord_app_id, activity):
                # Success - clear main RPC to avoid duplicate
                self._clear_main_rpc_activity()
                return

        # Fallback to main RPC
        self._set_main_rpc_activity(activity)

    def _handle_game_stop(self) -> None:
        """Handle game closing."""
        if self.logger:
            self.logger.info(f"Discord Lite: Game stopped - {self.current_game_name}")

        # Reset state
        self.current_game_appid = None
        self.current_game_name = None
        self.game_start_time = None

        # Close game-specific RPC
        if self.game_specific_rpc:
            try:
                self.game_specific_rpc.disconnect()
            except:
                pass
            self.game_specific_rpc = None

        # Clear main RPC activity
        self._clear_main_rpc_activity()

    def _build_activity_payload(self, game_info: Dict[str, str], discord_app_id: Optional[str]) -> Dict[str, Any]:
        """
        Build Discord activity payload.

        Args:
            game_info: Game information dictionary
            discord_app_id: Official Discord app ID (if found)

        Returns:
            Activity payload for SET_ACTIVITY command
        """
        # Determine display text
        if discord_app_id:
            # Official app shows game name as window title
            details = "Playing on Steam Deck"
            state = None
        else:
            # Fallback shows game name in details
            details = game_info["name"]
            state = "Playing on Steam Deck"

        activity = {
            "details": details,
            "timestamps": {"start": self.game_start_time},
            "assets": {
                "large_image": game_info["image_url"],
                "large_text": game_info["name"],
                "small_image": "https://steamcdn-a.akamaihd.net/steamcommunity/public/images/avatars/8d/8dd66ce1b9590825cebdce861c372cc3f5187f2e_full.jpg",
                "small_text": "Steam Deck"
            }
        }

        if state:
            activity["state"] = state

        return activity

    def _try_official_app_id(self, discord_app_id: str, activity: Dict[str, Any]) -> bool:
        """
        Try to connect with official Discord app ID.

        Args:
            discord_app_id: Official Discord application ID
            activity: Activity payload

        Returns:
            True if successful, False otherwise
        """
        try:
            if self.logger:
                self.logger.info(f"Discord Lite: Attempting official app ID: {discord_app_id}")

            official_rpc = DiscordRPCClient(discord_app_id, self.logger)

            if not official_rpc.connect():
                if self.logger:
                    self.logger.warning("Discord Lite: Failed to connect with official app ID")
                return False

            result = official_rpc.send_command("SET_ACTIVITY", {
                "pid": os.getpid(),
                "activity": activity
            })

            if result:
                self.game_specific_rpc = official_rpc
                if self.logger:
                    self.logger.info("Discord Lite: Successfully connected with official app ID")
                return True

            official_rpc.disconnect()
            return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error using official app ID: {e}")
            return False

    def _set_main_rpc_activity(self, activity: Dict[str, Any]) -> None:
        """
        Set activity on main RPC connection (fallback).

        Args:
            activity: Activity payload
        """
        try:
            self.main_rpc.send_command("SET_ACTIVITY", {
                "pid": os.getpid(),
                "activity": activity
            })
            if self.logger:
                self.logger.info(f"Discord Lite: Set activity via main RPC (fallback)")
        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error setting main RPC activity: {e}")

    def _clear_main_rpc_activity(self) -> None:
        """Clear activity on main RPC connection."""
        try:
            self.main_rpc.send_command("SET_ACTIVITY", {
                "pid": os.getpid(),
                "activity": None
            })
        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error clearing main RPC activity: {e}")

    def _find_discord_app_id(self, game_name: str) -> Optional[str]:
        """
        Find official Discord app ID for a game.

        Args:
            game_name: Steam game name

        Returns:
            Discord app ID or None if not found
        """
        # Check cache
        cached_app_id = self.discord_appid_cache.get(game_name)
        if cached_app_id is not None:
            return cached_app_id

        # Load detectable apps
        apps = self._load_discord_detectable_apps()
        if not apps:
            return None

        target_name = game_name.lower()

        # Try exact match first
        for app in apps:
            if app.get("name", "").lower() == target_name:
                app_id = app.get("id")
                self.discord_appid_cache.set(game_name, app_id)
                if self.logger:
                    self.logger.info(f"Discord Lite: Exact match - {game_name} -> {app_id}")
                return app_id

        # Try partial match
        for app in apps:
            app_name = app.get("name", "").lower()
            if target_name in app_name or app_name in target_name:
                app_id = app.get("id")
                self.discord_appid_cache.set(game_name, app_id)
                if self.logger:
                    self.logger.info(f"Discord Lite: Partial match - {game_name} -> {app_id}")
                return app_id

        # Not found - cache negative result
        self.discord_appid_cache.set(game_name, None)
        return None

    def _load_discord_detectable_apps(self) -> list[Dict[str, Any]]:
        """
        Load Discord detectable applications list.

        Uses 24-hour cache to avoid excessive API calls.

        Returns:
            List of app dictionaries
        """
        current_time = time.time()

        # Check memory cache
        if self.discord_apps and (current_time - self.discord_apps_last_fetch) < self.CACHE_DURATION_SECONDS:
            return self.discord_apps

        # Check disk cache
        cache_path = os.path.join(self.settings_dir, "discord_apps_cache.json")

        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                    last_fetch = cache_data.get("last_fetch", 0)

                    if (current_time - last_fetch) < self.CACHE_DURATION_SECONDS:
                        self.discord_apps = cache_data.get("apps", [])
                        self.discord_apps_last_fetch = last_fetch
                        if self.logger:
                            self.logger.info(f"Discord Lite: Loaded {len(self.discord_apps)} apps from disk cache")
                        return self.discord_apps

            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Discord Lite: Error reading disk cache: {e}")

        # Fetch from API
        return self._fetch_discord_apps_from_api(cache_path)

    def _fetch_discord_apps_from_api(self, cache_path: str) -> list[Dict[str, Any]]:
        """
        Fetch detectable apps from Discord API.

        Args:
            cache_path: Path to save cache file

        Returns:
            List of app dictionaries
        """
        try:
            if self.logger:
                self.logger.info("Discord Lite: Fetching detectable apps from Discord API...")

            request = urllib.request.Request(
                self.DISCORD_DETECTABLE_APPS_URL,
                headers={"User-Agent": "DiscordLite/1.0"}
            )

            with urllib.request.urlopen(request, timeout=10, context=self.ssl_context) as response:
                apps_data = json.loads(response.read().decode('utf-8'))

            self.discord_apps = apps_data
            self.discord_apps_last_fetch = time.time()

            # Save to disk
            try:
                os.makedirs(os.path.dirname(cache_path), exist_ok=True)
                with open(cache_path, 'w') as f:
                    json.dump({
                        "last_fetch": self.discord_apps_last_fetch,
                        "apps": apps_data
                    }, f)
                if self.logger:
                    self.logger.info(f"Discord Lite: Cached {len(apps_data)} apps to disk")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"Discord Lite: Error saving cache to disk: {e}")

            return apps_data

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error fetching detectable apps: {e}")
            return self.discord_apps  # Return stale cache if available

    def clear(self) -> None:
        """Clear all game state and disconnect game-specific RPC."""
        self._handle_game_stop()

    def get_current_game_info(self) -> Optional[Dict[str, str]]:
        """
        Get current game information.

        Returns:
            Dictionary with appid and name, or None if no game running
        """
        if self.current_game_appid:
            return {
                "appid": self.current_game_appid,
                "name": self.current_game_name
            }
        return None
