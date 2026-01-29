"""Steam game detection for Steam Deck"""

import os
import re
import glob
from typing import Optional, Dict

from ..utils.cache import LRUCache


class SteamGameDetector:
    """
    Detects currently running Steam games on Steam Deck.

    Uses /proc inspection to find Steam game processes and manifest files
    to resolve game names.
    """

    # Pre-compiled regex for performance (regex is expensive)
    GAME_ID_REGEX = re.compile(r'SteamLaunch.*?AppId=(\d+)')

    def __init__(self, logger=None):
        """
        Initialize game detector with caches.

        Args:
            logger: Logger instance for logging operations
        """
        self.logger = logger
        self.game_name_cache = LRUCache(max_size=50)

        # Steam library paths
        self.steam_paths = [
            "/home/deck/.local/share/Steam/steamapps",
            "/home/deck/.steam/steam/steamapps"
        ]

    def detect_running_game(self) -> Optional[Dict[str, str]]:
        """
        Detect currently running Steam game.

        Returns:
            Dictionary with 'appid', 'name', 'image_url' or None if no game running

        Example:
            >>> detector.detect_running_game()
            {
                "appid": "730",
                "name": "Counter-Strike 2",
                "image_url": "https://steamcdn-a.akamaihd.net/steam/apps/730/header.jpg"
            }
        """
        try:
            # List all numeric PIDs in /proc (much faster than glob)
            pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]

            for pid in pids:
                try:
                    cmdline_path = f'/proc/{pid}/cmdline'

                    # Read command line (errors='ignore' handles binary data)
                    with open(cmdline_path, 'r', errors='ignore') as f:
                        cmdline = f.read()

                    # Fast string check before expensive regex
                    if 'SteamLaunch' not in cmdline:
                        continue

                    # Ignore Discord and Flatpak processes
                    cmdline_lower = cmdline.lower()
                    if 'discord' in cmdline_lower or 'flatpak' in cmdline_lower:
                        continue

                    # Extract App ID with regex
                    match = self.GAME_ID_REGEX.search(cmdline)
                    if match:
                        appid = match.group(1)

                        # Get game name
                        game_name = self._get_game_name(appid)
                        if not game_name:
                            game_name = f"Game {appid}"

                        return {
                            "appid": appid,
                            "name": game_name,
                            "image_url": f"https://steamcdn-a.akamaihd.net/steam/apps/{appid}/header.jpg"
                        }

                except (IOError, PermissionError, FileNotFoundError):
                    # Process died or no permission - skip
                    continue

            return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error detecting Steam game: {e}")
            return None

    def _get_game_name(self, appid: str) -> Optional[str]:
        """
        Get game name from App ID using manifest files.

        Args:
            appid: Steam application ID

        Returns:
            Game name or None if not found
        """
        # Check cache first
        cached_name = self.game_name_cache.get(appid)
        if cached_name:
            return cached_name

        try:
            # Add external libraries (SD card, USB drives)
            all_steam_paths = self.steam_paths.copy()
            external_paths = glob.glob("/run/media/*/steamapps")
            all_steam_paths.extend(external_paths)

            # Search for manifest file
            for base_path in all_steam_paths:
                manifest_path = f"{base_path}/appmanifest_{appid}.acf"

                if os.path.exists(manifest_path):
                    try:
                        with open(manifest_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()

                        # Extract name from ACF file
                        match = re.search(r'"name"\s+"([^"]+)"', content)

                        if match:
                            name = match.group(1)
                            self.game_name_cache.set(appid, name)
                            return name

                    except Exception:
                        continue

            return None

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error getting game name for appid {appid}: {e}")
            return None

    def refresh_library_paths(self) -> None:
        """
        Refresh list of Steam library paths.

        Call this if the user adds/removes external storage.
        """
        self.steam_paths = [
            "/home/deck/.local/share/Steam/steamapps",
            "/home/deck/.steam/steam/steamapps"
        ]

        external_paths = glob.glob("/run/media/*/steamapps")
        self.steam_paths.extend(external_paths)

        if self.logger:
            self.logger.info(f"Discord Lite: Refreshed Steam library paths: {len(self.steam_paths)} locations")
