"""Discord IPC socket detection for Linux/Steam Deck"""

import os
from typing import Optional


def find_discord_ipc_socket(logger=None) -> Optional[str]:
    """
    Find Discord IPC socket on the system.

    Args:
        logger: Optional logger instance for logging operations

    Searches in three priority locations:
    1. Flatpak: /run/user/{uid}/app/com.discordapp.Discord/discord-ipc-*
    2. Native: /run/user/{uid}/discord-ipc-*
    3. Fallback: /tmp/discord-ipc-*

    Returns:
        Full path to socket file or None if Discord is not running

    Example:
        >>> find_discord_ipc_socket()
        '/run/user/1000/discord-ipc-0'
    """
    # Get possible UIDs (Steam Deck typically uses 1000)
    possible_uids = [1000, os.getuid()]
    possible_uids = list(set(possible_uids))  # Remove duplicates

    for uid in possible_uids:
        for socket_number in range(10):  # Discord creates discord-ipc-0 through discord-ipc-9
            possible_paths = [
                # Flatpak path (Steam Deck uses this most often)
                f"/run/user/{uid}/app/com.discordapp.Discord/discord-ipc-{socket_number}",
                # Native installation path
                f"/run/user/{uid}/discord-ipc-{socket_number}",
                # Temporary fallback path
                f"/tmp/discord-ipc-{socket_number}",
            ]

            for socket_path in possible_paths:
                if os.path.exists(socket_path):
                    if logger:
                        logger.info(f"Discord Lite: Socket found at: {socket_path}")
                    return socket_path

    if logger:
        logger.warning(f"Discord Lite: No socket found. Tested UIDs: {possible_uids}")
    return None
