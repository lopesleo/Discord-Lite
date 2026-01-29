"""Access token persistence (wrapper around SettingsManager)"""

from typing import Optional
from ..utils.settings import SettingsManager


class TokenManager:
    """
    Manages Discord access token storage and retrieval.

    This is a thin wrapper around SettingsManager focused on token operations.
    """

    def __init__(self, settings_dir: str, logger=None):
        """
        Initialize token manager.

        Args:
            settings_dir: Directory for storing token files
            logger: Logger instance for logging operations
        """
        self.settings_manager = SettingsManager(settings_dir, logger)

    def load(self) -> Optional[str]:
        """
        Load saved access token.

        Returns:
            Access token or None if not found
        """
        return self.settings_manager.load_token()

    def save(self, access_token: str) -> bool:
        """
        Save access token to disk.

        Args:
            access_token: OAuth2 access token from Discord

        Returns:
            True if saved successfully
        """
        return self.settings_manager.save_token(access_token)

    def delete(self) -> bool:
        """
        Delete saved token (logout).

        Returns:
            True if deleted successfully
        """
        return self.settings_manager.delete_token()

    def is_saved(self) -> bool:
        """
        Check if token exists on disk.

        Returns:
            True if token file exists
        """
        return self.load() is not None
