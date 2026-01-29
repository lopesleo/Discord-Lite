"""
Discord Lite - Discord voice control plugin for Steam Deck

Refactored architecture with modular components.
This file maintains the Plugin class API for Decky Loader compatibility.
"""

import os
import sys
import subprocess
from typing import Optional, Dict, List, Any
import decky

# Add plugin directory to Python path for backend imports
# This is needed because Decky Loader doesn't always add the plugin directory to sys.path
plugin_dir = os.path.dirname(os.path.abspath(__file__))
if plugin_dir not in sys.path:
    sys.path.insert(0, plugin_dir)

# Import modular backend components
from backend.discord_rpc.client import DiscordRPCClient
from backend.auth.oauth import OAuth2Manager
from backend.auth.token_manager import TokenManager
from backend.voice.controller import VoiceController
from backend.voice.members import MemberTracker
from backend.voice.volume import perceptual_to_amplitude, amplitude_to_perceptual
from backend.steam.game_detector import SteamGameDetector
from backend.steam.activity_sync import ActivitySyncManager
from backend.polling.voice_poller import VoicePoller
from backend.utils.settings import SettingsManager


class Plugin:
    """
    Discord Lite - Complete Discord control from Steam Deck.

    Main plugin class that exposes async methods to the frontend.
    All methods maintain backward compatibility with existing frontend code.
    """

    CLIENT_ID = "1461502476401381446"
    SCOPES = ["rpc", "rpc.voice.read", "rpc.voice.write"]

    def __init__(self):
        """Initialize plugin with modular components."""
        # Core components
        self.rpc_client: Optional[DiscordRPCClient] = None
        self.voice_controller: Optional[VoiceController] = None
        self.member_tracker = MemberTracker()
        self.settings_manager = SettingsManager(decky.DECKY_PLUGIN_SETTINGS_DIR, decky.logger)
        self.token_manager = TokenManager(decky.DECKY_PLUGIN_SETTINGS_DIR, decky.logger)
        self.oauth_manager = OAuth2Manager(self.CLIENT_ID, decky.logger)

        # Game sync
        self.game_detector = SteamGameDetector(decky.logger)
        self.activity_sync: Optional[ActivitySyncManager] = None
        self.game_sync_enabled = True

        # Polling system
        self.voice_poller = VoicePoller(decky.logger)

        # Authentication state
        self.access_token: Optional[str] = None
        self.auth_in_progress = False

        # Guild/server selection
        self.guilds_cache: List[Dict] = []
        self.selected_guild_id: Optional[str] = None

    # ==================== LIFECYCLE ====================

    async def _main(self):
        """Plugin initialization."""
        decky.logger.info("Discord Lite: Initializing plugin...")

        # Load saved token
        self.access_token = self.token_manager.load()

        # Load settings
        settings = self.settings_manager.load_settings()
        self.selected_guild_id = settings.get("selected_guild_id")
        self.game_sync_enabled = settings.get("game_sync_enabled", True)

        decky.logger.info("Discord Lite: Plugin initialized")

    async def _unload(self):
        """Plugin cleanup."""
        decky.logger.info("Discord Lite: Unloading plugin...")

        # Stop polling
        self.voice_poller.stop()

        # Disconnect RPC
        if self.rpc_client:
            self.rpc_client.disconnect()

        # Clear activity sync
        if self.activity_sync:
            self.activity_sync.clear()

        decky.logger.info("Discord Lite: Plugin unloaded")

    # ==================== AUTHENTICATION ====================

    async def auto_auth(self) -> dict:
        """
        Automatic authentication with Discord.

        Tries saved token first (fast path), then initiates OAuth2 PKCE flow if needed.

        Returns:
            Dictionary with success status and user info
        """
        if self.auth_in_progress:
            return {"success": False, "message": "Authentication already in progress"}

        self.auth_in_progress = True

        try:
            # Load token if not already loaded
            if not self.access_token:
                self.access_token = self.token_manager.load()

            # Create RPC client
            self.rpc_client = DiscordRPCClient(self.CLIENT_ID, decky.logger)

            # Connect to Discord IPC
            if not self.rpc_client.connect():
                return {"success": False, "message": "Discord not running or socket not found"}

            # Try saved token first (fast login)
            if self.access_token:
                decky.logger.info("Discord Lite: Attempting login with saved token...")

                if self.rpc_client.authenticate(self.access_token):
                    self._post_authentication_setup()
                    return {
                        "success": True,
                        "authenticated": True,
                        "user": self.rpc_client.user,
                        "message": f"Connected as {self.rpc_client.user.get('username', 'User')}"
                    }
                else:
                    decky.logger.warning("Discord Lite: Saved token expired or invalid")
                    self.access_token = None

            # Initiate OAuth2 PKCE flow
            decky.logger.info("Discord Lite: Starting OAuth2 PKCE flow...")

            verifier, challenge = self.oauth_manager.generate_pkce_pair()

            # Request authorization (opens dialog in Discord)
            code = self.rpc_client.authorize(self.SCOPES, challenge)

            if not code:
                return {"success": False, "message": "Authorization declined by user"}

            # Exchange code for token
            exchange_result = self.oauth_manager.exchange_code_for_token(code, verifier)

            if not exchange_result.get("success"):
                return exchange_result

            # Reconnect with new token
            self.rpc_client.disconnect()
            self.rpc_client = DiscordRPCClient(self.CLIENT_ID, decky.logger)

            if not self.rpc_client.connect():
                return {"success": False, "message": "Failed to reconnect after authentication"}

            new_token = exchange_result["access_token"]

            if self.rpc_client.authenticate(new_token):
                self.access_token = new_token
                self.token_manager.save(new_token)
                self._post_authentication_setup()

                return {
                    "success": True,
                    "authenticated": True,
                    "user": self.rpc_client.user
                }

            return {"success": False, "message": "Final authentication failed"}

        except Exception as e:
            decky.logger.error(f"Discord Lite: Authentication error: {e}")
            return {"success": False, "message": str(e)}

        finally:
            self.auth_in_progress = False

    def _post_authentication_setup(self):
        """Setup components after successful authentication."""
        # Create voice controller
        self.voice_controller = VoiceController(self.rpc_client, decky.logger)

        # Create activity sync manager
        self.activity_sync = ActivitySyncManager(
            decky.DECKY_PLUGIN_SETTINGS_DIR,
            self.rpc_client,
            decky.logger
        )

        # Start polling
        self._start_voice_polling()

    async def logout(self) -> dict:
        """
        Logout and clear saved token.

        Returns:
            Dictionary with success status
        """
        self.access_token = None
        self.token_manager.delete()

        if self.rpc_client:
            self.rpc_client.authenticated = False
            self.rpc_client.access_token = None

        # Stop polling
        self.voice_poller.stop()

        return {"success": True, "message": "Logged out"}

    async def check_status(self) -> dict:
        """
        Check connection and authentication status.

        Returns:
            Dictionary with connection status and user info
        """
        if not self.rpc_client or not self.rpc_client.connected:
            return {
                "success": False,
                "connected": False,
                "authenticated": False,
                "message": "Not connected"
            }

        return {
            "success": True,
            "connected": True,
            "authenticated": self.rpc_client.authenticated,
            "user": self.rpc_client.user if self.rpc_client.authenticated else None,
            "message": "Connected" if self.rpc_client.authenticated else "Not authenticated"
        }

    # ==================== DISCORD LAUNCHER ====================

    async def check_discord_installed(self) -> dict:
        """
        Check if Discord is installed on the system.

        Returns:
            Dictionary with installation status
        """
        flatpak_path = os.path.expanduser("~/.var/app/com.discordapp.Discord")
        flatpak_installed = os.path.exists(flatpak_path)

        native_paths = [
            "/usr/bin/discord",
            "/usr/bin/Discord",
            os.path.expanduser("~/Discord/Discord")
        ]
        native_installed = any(os.path.exists(p) for p in native_paths)

        return {
            "success": True,
            "installed": flatpak_installed or native_installed,
            "flatpak": flatpak_installed,
            "native": native_installed
        }

    async def launch_discord(self) -> dict:
        """
        Launch Discord application.

        Returns:
            Dictionary with success status
        """
        try:
            # Try Flatpak first
            flatpak_path = os.path.expanduser("~/.var/app/com.discordapp.Discord")
            if os.path.exists(flatpak_path):
                subprocess.Popen(
                    ["flatpak", "run", "com.discordapp.Discord"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True
                )
                return {"success": True, "message": "Discord launched (Flatpak)"}

            # Try native installation
            for path in ["/usr/bin/discord", "/usr/bin/Discord"]:
                if os.path.exists(path):
                    subprocess.Popen(
                        [path],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        start_new_session=True
                    )
                    return {"success": True, "message": "Discord launched"}

            return {"success": False, "message": "Discord not found"}

        except Exception as e:
            decky.logger.error(f"Discord Lite: Error launching Discord: {e}")
            return {"success": False, "message": str(e)}

    async def check_discord_running(self) -> dict:
        """
        Check if Discord is currently running.

        Returns:
            Dictionary with running status
        """
        try:
            temp_rpc = DiscordRPCClient(self.CLIENT_ID, decky.logger)
            from backend.utils.socket_finder import find_discord_ipc_socket

            ipc_path = find_discord_ipc_socket(decky.logger)
            is_running = ipc_path is not None

            return {"success": True, "running": is_running}

        except Exception as e:
            decky.logger.error(f"Discord Lite: Error checking if Discord is running: {e}")
            return {"success": False, "running": False}

    # ==================== VOICE CONTROL ====================

    async def get_voice_state(self) -> dict:
        """
        Get current voice state including settings and channel info.

        Returns:
            Dictionary with voice state
        """
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated", "authenticated": False}

        self.voice_controller.get_voice_settings()
        self.voice_controller.get_selected_voice_channel()

        speaking_users = self.rpc_client.get_speaking_users()

        return {
            "success": True,
            "authenticated": True,
            "is_muted": self.voice_controller.is_muted,
            "is_deafened": self.voice_controller.is_deafened,
            "input_volume": self.voice_controller.input_volume,
            "output_volume": self.voice_controller.output_volume,
            "channel_id": self.voice_controller.voice_channel_id,
            "channel_name": self.voice_controller.voice_channel_name,
            "guild_id": self.voice_controller.voice_guild_id,
            "in_voice": self.voice_controller.voice_channel_id is not None,
            "members": self.voice_controller.voice_members,
            "speaking_users": speaking_users,
            "mode_type": self.voice_controller.mode_type,
            "noise_suppression": self.voice_controller.noise_suppression,
            "echo_cancellation": self.voice_controller.echo_cancellation,
            "automatic_gain_control": self.voice_controller.automatic_gain_control,
        }

    async def toggle_mute(self) -> dict:
        """Toggle mute state."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        return self.voice_controller.toggle_mute()

    async def toggle_deafen(self) -> dict:
        """Toggle deafen state."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        return self.voice_controller.toggle_deafen()

    async def set_input_volume(self, volume: int) -> dict:
        """Set microphone input volume (0-100)."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        result = self.voice_controller.set_input_volume(volume)
        return {"success": result.get("success"), "volume": volume}

    async def set_output_volume(self, volume: int) -> dict:
        """Set voice output volume (0-200)."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        result = self.voice_controller.set_output_volume(volume)
        return {"success": result.get("success"), "volume": volume}

    async def leave_voice(self) -> dict:
        """Leave current voice channel."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        if self.voice_controller.select_voice_channel(None):
            self.voice_controller.voice_channel_id = None
            self.voice_controller.voice_channel_name = None
            return {"success": True}

        return {"success": False, "message": "Failed to leave channel"}

    # ==================== GUILDS AND CHANNELS ====================

    async def get_guilds(self) -> dict:
        """Get list of guilds (servers)."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated", "guilds": []}

        self.guilds_cache = self.voice_controller.get_guilds()

        return {
            "success": True,
            "guilds": self.guilds_cache,
            "selected_guild_id": self.selected_guild_id
        }

    async def select_guild(self, guild_id: str) -> dict:
        """Select a guild (server)."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        self.selected_guild_id = guild_id
        self.settings_manager.save_settings({"selected_guild_id": guild_id})

        return {"success": True, "guild_id": guild_id}

    async def get_voice_channels(self, guild_id: str = None) -> dict:
        """Get voice channels for a guild."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated", "channels": []}

        if not guild_id:
            guild_id = self.selected_guild_id

        if not guild_id:
            self.voice_controller.get_selected_voice_channel()
            guild_id = self.voice_controller.voice_guild_id

        if not guild_id:
            return {"success": False, "message": "No server selected", "channels": []}

        channels = self.voice_controller.get_channels(guild_id)

        return {"success": True, "guild_id": guild_id, "channels": channels}

    async def join_voice_channel(self, channel_id: str) -> dict:
        """Join a voice channel."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        if self.voice_controller.select_voice_channel(channel_id, force=True):
            self.voice_controller.get_selected_voice_channel()
            return {
                "success": True,
                "channel_id": self.voice_controller.voice_channel_id,
                "channel_name": self.voice_controller.voice_channel_name
            }

        return {"success": False, "message": "Failed to join channel"}

    # ==================== USER VOICE SETTINGS ====================

    async def set_user_volume(self, user_id: str, volume: int) -> dict:
        """
        Set volume for a specific user (0-200).

        If user_id is the current user, redirects to set_output_volume.
        """
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        volume = max(0, min(200, volume))

        # Redirect if setting own volume
        if self.rpc_client.user and str(self.rpc_client.user.get('id')) == str(user_id):
            decky.logger.info("Discord Lite: Redirecting own volume to output_volume")
            return await self.set_output_volume(volume)

        # Convert perceptual to amplitude
        amplitude = int(perceptual_to_amplitude(volume, 200))

        decky.logger.info(f"Discord Lite: set_user_volume user={user_id} perceptual={volume} amplitude={amplitude}")

        if self.voice_controller.set_user_voice_settings(user_id, volume=amplitude):
            return {"success": True, "user_id": user_id, "volume": volume}

        return {"success": False, "message": "Failed to set user volume"}

    async def mute_user(self, user_id: str, mute: bool) -> dict:
        """
        Mute/unmute a specific user.

        If user_id is the current user, redirects to toggle_mute.
        """
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        # Redirect if muting self
        if self.rpc_client.user and str(self.rpc_client.user.get('id')) == str(user_id):
            decky.logger.info("Discord Lite: Redirecting own mute to toggle_mute")
            current_mute = self.voice_controller.is_muted

            if current_mute != mute:
                return await self.toggle_mute()
            else:
                return {"success": True, "user_id": user_id, "muted": mute, "message": "Already in correct state"}

        if self.voice_controller.set_user_voice_settings(user_id, mute=mute):
            return {"success": True, "user_id": user_id, "muted": mute}

        return {"success": False, "message": "Failed to mute user"}

    # ==================== ADVANCED VOICE SETTINGS ====================

    async def set_voice_mode(self, mode_type: str) -> dict:
        """Set voice mode (VOICE_ACTIVITY or PUSH_TO_TALK)."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        if mode_type not in ["VOICE_ACTIVITY", "PUSH_TO_TALK"]:
            return {"success": False, "message": "Invalid mode type"}

        result = self.voice_controller.set_voice_settings(mode={"type": mode_type})

        if result.get("success"):
            self.voice_controller.mode_type = mode_type
            return {"success": True, "mode_type": mode_type}

        return result

    async def set_ptt_shortcut(self, key_type: int, key_code: int, key_name: str) -> dict:
        """Set push-to-talk shortcut."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        shortcut = [{"type": key_type, "code": key_code, "name": key_name}]

        result = self.voice_controller.set_voice_settings(mode={
            "type": "PUSH_TO_TALK",
            "shortcut": shortcut,
            "delay": 100.0
        })

        if result.get("success"):
            self.voice_controller.mode_type = "PUSH_TO_TALK"
            return {"success": True, "shortcut": key_name}

        return result

    async def set_noise_suppression(self, enabled: bool) -> dict:
        """Enable/disable noise suppression."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        result = self.voice_controller.set_voice_settings(noise_suppression=enabled)

        if result.get("success"):
            self.voice_controller.noise_suppression = enabled
            return {"success": True, "enabled": enabled}

        return result

    async def set_echo_cancellation(self, enabled: bool) -> dict:
        """Enable/disable echo cancellation."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        result = self.voice_controller.set_voice_settings(echo_cancellation=enabled)

        if result.get("success"):
            self.voice_controller.echo_cancellation = enabled
            return {"success": True, "enabled": enabled}

        return result

    async def set_automatic_gain_control(self, enabled: bool) -> dict:
        """Enable/disable automatic gain control."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        result = self.voice_controller.set_voice_settings(automatic_gain_control=enabled)

        if result.get("success"):
            self.voice_controller.automatic_gain_control = enabled
            return {"success": True, "enabled": enabled}

        return result

    # ==================== SETTINGS ====================

    async def get_settings(self) -> dict:
        """Get plugin settings."""
        settings = self.settings_manager.load_settings()

        return {
            "success": True,
            "settings": {
                "notifications_enabled": settings.get("notifications_enabled", True),
                "auto_connect": settings.get("auto_connect", False),
                "language": settings.get("language", "pt"),
                "user_volumes": settings.get("user_volumes", {}),
                "game_sync_enabled": settings.get("game_sync_enabled", True),
            }
        }

    async def save_settings_async(self, settings: dict) -> dict:
        """Save plugin settings."""
        try:
            self.settings_manager.save_settings(settings)

            # Handle game sync toggle
            if "game_sync_enabled" in settings:
                self.game_sync_enabled = settings["game_sync_enabled"]

                if not self.game_sync_enabled and self.activity_sync:
                    self.activity_sync.clear()
                elif self.game_sync_enabled and self.activity_sync:
                    self.activity_sync.sync()

            return {"success": True}

        except Exception as e:
            decky.logger.error(f"Discord Lite: Error saving settings: {e}")
            return {"success": False, "message": str(e)}

    # ==================== MEMBER TRACKING ====================

    async def get_voice_members_diff(self) -> dict:
        """Get members who joined/left since last check."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        self.voice_controller.get_selected_voice_channel()

        diff = self.member_tracker.update_and_get_diff(self.voice_controller.voice_members)

        return {
            "success": True,
            "joined": diff["joined"],
            "left": diff["left"],
            "current_count": diff["current_count"]
        }

    async def sync_full_state(self) -> dict:
        """Synchronize complete plugin state."""
        if not self.rpc_client or not self.rpc_client.authenticated:
            return {"success": False, "message": "Not authenticated"}

        # Get voice settings
        self.voice_controller.get_voice_settings()

        # Get voice channel
        self.voice_controller.get_selected_voice_channel()

        # Update selected guild if in voice
        if self.voice_controller.voice_guild_id:
            self.selected_guild_id = self.voice_controller.voice_guild_id
            self.settings_manager.save_settings({"selected_guild_id": self.voice_controller.voice_guild_id})

        # Initialize member tracker
        self.member_tracker.initialize(self.voice_controller.voice_members)

        # Get guilds
        self.guilds_cache = self.voice_controller.get_guilds()

        # Get current game
        current_game = self.activity_sync.get_current_game_info() if self.activity_sync else None

        return {
            "success": True,
            "authenticated": True,
            "is_muted": self.voice_controller.is_muted,
            "is_deafened": self.voice_controller.is_deafened,
            "input_volume": self.voice_controller.input_volume,
            "output_volume": self.voice_controller.output_volume,
            "channel_id": self.voice_controller.voice_channel_id,
            "channel_name": self.voice_controller.voice_channel_name,
            "guild_id": self.voice_controller.voice_guild_id,
            "in_voice": self.voice_controller.voice_channel_id is not None,
            "members": self.voice_controller.voice_members,
            "mode_type": self.voice_controller.mode_type,
            "noise_suppression": self.voice_controller.noise_suppression,
            "echo_cancellation": self.voice_controller.echo_cancellation,
            "automatic_gain_control": self.voice_controller.automatic_gain_control,
            "guilds": self.guilds_cache,
            "selected_guild_id": self.selected_guild_id,
            "game_sync_enabled": self.game_sync_enabled,
            "current_game": current_game,
        }

    # ==================== POLLING SYSTEM ====================

    async def get_pending_events(self) -> dict:
        """Get pending events from polling queue."""
        events = self.voice_poller.get_pending_events()
        return {"success": True, "events": events}

    def _start_voice_polling(self):
        """Start background polling thread."""
        # Initialize member tracker
        if self.voice_controller:
            self.voice_controller.get_selected_voice_channel()
            self.member_tracker.initialize(self.voice_controller.voice_members)

        # Start polling with callbacks
        self.voice_poller.start(
            check_members_callback=self._check_voice_members_changes,
            sync_game_callback=self._sync_game_to_discord,
            is_active_callback=self._is_user_active
        )

    def _check_voice_members_changes(self):
        """Check for voice member changes (called by poller)."""
        try:
            if not self.member_tracker.should_emit_events():
                return

            if not self.voice_controller.voice_channel_id:
                return

            self.voice_controller.get_selected_voice_channel()

            if not self.voice_controller.voice_channel_id:
                self.member_tracker.reset()
                return

            diff = self.member_tracker.update_and_get_diff(self.voice_controller.voice_members)

            # Enqueue join events
            for member in diff["joined"]:
                decky.logger.info(f"Discord Lite: {member['username']} joined channel")
                self.voice_poller.enqueue_event(
                    "VOICE_JOIN",
                    user_id=member["user_id"],
                    username=member["username"],
                    avatar=member.get("avatar")
                )

            # Enqueue leave events
            for member in diff["left"]:
                decky.logger.info(f"Discord Lite: {member['username']} left channel")
                self.voice_poller.enqueue_event(
                    "VOICE_LEAVE",
                    user_id=member["user_id"],
                    username=member["username"],
                    avatar=member.get("avatar")
                )

        except Exception as e:
            decky.logger.error(f"Discord Lite: Error checking member changes: {e}")

    def _sync_game_to_discord(self):
        """Sync current game to Discord (called by poller)."""
        if self.activity_sync and self.game_sync_enabled:
            self.activity_sync.sync()

    def _is_user_active(self) -> bool:
        """Check if user is active (in voice or game running)."""
        in_voice = self.voice_controller and self.voice_controller.voice_channel_id is not None
        game_running = self.activity_sync and self.activity_sync.current_game_appid is not None
        return in_voice or game_running
