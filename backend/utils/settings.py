"""Settings persistence manager"""

import os
import json
from typing import Dict, Any, Optional


class SettingsManager:
    """
    Manages persistent plugin settings stored in JSON files.

    Handles both settings.json and token storage with proper error handling.
    """

    def __init__(self, settings_dir: str, logger=None):
        """
        Initialize settings manager with plugin directory.

        Args:
            settings_dir: Directory for storing settings files
            logger: Logger instance for logging operations
        """
        self.settings_dir = settings_dir
        self.logger = logger
        self.settings_path = os.path.join(self.settings_dir, "settings.json")
        self.token_path = os.path.join(self.settings_dir, "discord_token.json")

    def load_settings(self) -> Dict[str, Any]:
        """
        Load plugin settings from disk.

        Returns:
            Dictionary of settings, empty dict if file doesn't exist or is corrupted
        """
        try:
            if os.path.exists(self.settings_path):
                with open(self.settings_path, 'r') as f:
                    return json.load(f)
        except json.JSONDecodeError:
            if self.logger:
                self.logger.warning("Discord Lite: Corrupted settings file detected. Resetting.")
            try:
                os.remove(self.settings_path)
            except:
                pass
        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error loading settings: {e}")

        return {}

    def save_settings(self, settings: Dict[str, Any]) -> bool:
        """
        Save plugin settings to disk.

        Args:
            settings: Dictionary of settings to save (merged with existing)

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            os.makedirs(self.settings_dir, exist_ok=True)

            # Merge with existing settings
            current = self.load_settings()
            current.update(settings)

            with open(self.settings_path, 'w') as f:
                json.dump(current, f, indent=2)

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error saving settings: {e}")
            return False

    def load_token(self) -> Optional[str]:
        """
        Load saved Discord access token.

        Returns:
            Access token string or None if not found/corrupted
        """
        try:
            if os.path.exists(self.token_path):
                with open(self.token_path, 'r') as f:
                    data = json.load(f)
                    return data.get("access_token")
        except json.JSONDecodeError:
            if self.logger:
                self.logger.warning("Discord Lite: Corrupted token file detected. Resetting.")
            try:
                os.remove(self.token_path)
            except:
                pass
        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error loading token: {e}")

        return None

    def save_token(self, access_token: str) -> bool:
        """
        Save Discord access token to disk.

        Args:
            access_token: OAuth2 access token from Discord

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            os.makedirs(self.settings_dir, exist_ok=True)

            with open(self.token_path, 'w') as f:
                json.dump({"access_token": access_token}, f)

            if self.logger:
                self.logger.info("Discord Lite: Token saved successfully")
            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error saving token: {e}")
            return False

    def delete_token(self) -> bool:
        """
        Delete saved access token (logout).

        Returns:
            True if deleted successfully or file didn't exist
        """
        try:
            if os.path.exists(self.token_path):
                os.remove(self.token_path)
            return True
        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error deleting token: {e}")
            return False
