"""Voice settings controller for Discord RPC"""

from typing import Dict, Any, Optional, List

from .volume import perceptual_to_amplitude, amplitude_to_perceptual


class VoiceController:
    """
    High-level controller for Discord voice settings.

    Manages voice state, settings, and channel operations with automatic
    conversion between perceptual and amplitude values.
    """

    def __init__(self, rpc_client, logger=None):
        """
        Initialize voice controller.

        Args:
            rpc_client: DiscordRPCClient instance
            logger: Logger instance for logging operations
        """
        self.rpc = rpc_client
        self.logger = logger

        # Voice state
        self.is_muted = False
        self.is_deafened = False
        self.input_volume = 100
        self.output_volume = 100

        # Voice settings
        self.mode_type = "VOICE_ACTIVITY"  # or PUSH_TO_TALK
        self.automatic_gain_control = True
        self.echo_cancellation = True
        self.noise_suppression = True
        self.qos = True
        self.silence_warning = False

        # Channel state
        self.voice_channel_id: Optional[str] = None
        self.voice_channel_name: Optional[str] = None
        self.voice_guild_id: Optional[str] = None
        self.voice_members: List[Dict[str, Any]] = []

    def get_voice_settings(self) -> Optional[Dict[str, Any]]:
        """
        Fetch current voice settings from Discord and update internal state.

        Returns:
            Raw Discord response or None on error
        """
        result = self.rpc.send_command("GET_VOICE_SETTINGS")

        if not result or not result.get("data"):
            return None

        data = result["data"]

        # Update mute/deafen state
        self.is_muted = data.get("mute", False)
        self.is_deafened = data.get("deaf", False)

        # Update input volume (0-100 range)
        input_data = data.get("input", {})
        if isinstance(input_data, dict):
            raw_amplitude = float(input_data.get("volume", 100))
            perceptual = amplitude_to_perceptual(raw_amplitude, 100)
            if self.logger:
                self.logger.info(f"Discord Lite: GET_VOICE_SETTINGS input amplitude={raw_amplitude:.2f} perceptual={perceptual:.2f}")
            self.input_volume = int(perceptual)

        # Update output volume (0-200 range with boost)
        output_data = data.get("output", {})
        if isinstance(output_data, dict):
            raw_amplitude = float(output_data.get("volume", 100))
            perceptual = amplitude_to_perceptual(raw_amplitude, 200)
            if self.logger:
                self.logger.info(f"Discord Lite: GET_VOICE_SETTINGS output amplitude={raw_amplitude:.2f} perceptual={perceptual:.2f}")
            self.output_volume = int(perceptual)

        # Update mode
        mode_data = data.get("mode", {})
        if isinstance(mode_data, dict):
            self.mode_type = mode_data.get("type", "VOICE_ACTIVITY")

        # Update advanced settings
        self.automatic_gain_control = data.get("automatic_gain_control", True)
        self.echo_cancellation = data.get("echo_cancellation", True)
        self.noise_suppression = data.get("noise_suppression", True)
        self.qos = data.get("qos", True)
        self.silence_warning = data.get("silence_warning", False)

        return data

    def set_voice_settings(self, **kwargs) -> Dict[str, Any]:
        """
        Set voice settings on Discord.

        Args:
            **kwargs: Settings to update (e.g., mute=True, input={"volume": 50})

        Returns:
            Dictionary with 'success' and optional 'message'
        """
        result = self.rpc.send_command("SET_VOICE_SETTINGS", kwargs)

        if not result:
            return {"success": False, "message": "No response from Discord"}

        if result.get("evt") == "ERROR":
            error_message = result.get("data", {}).get("message", "Unknown error")
            return {"success": False, "message": error_message}

        return {"success": True, "data": result.get("data")}

    def set_input_volume(self, perceptual_volume: int) -> Dict[str, Any]:
        """
        Set microphone input volume (0-100%).

        Args:
            perceptual_volume: User-facing volume (0-100)

        Returns:
            Dictionary with 'success' and optional 'message'
        """
        perceptual_volume = max(0, min(100, perceptual_volume))
        amplitude = perceptual_to_amplitude(perceptual_volume, 100)

        if self.logger:
            self.logger.info(f"Discord Lite: Setting input volume perceptual={perceptual_volume} amplitude={amplitude:.2f}")

        result = self.set_voice_settings(input={"volume": amplitude})

        if result.get("success"):
            self.input_volume = perceptual_volume

        return result

    def set_output_volume(self, perceptual_volume: int) -> Dict[str, Any]:
        """
        Set voice output volume (0-200%, where 100% is normal and 100-200% is boost).

        Args:
            perceptual_volume: User-facing volume (0-200)

        Returns:
            Dictionary with 'success' and optional 'message'
        """
        perceptual_volume = max(0, min(200, perceptual_volume))
        amplitude = perceptual_to_amplitude(perceptual_volume, 200)

        if self.logger:
            self.logger.info(f"Discord Lite: Setting output volume perceptual={perceptual_volume} amplitude={amplitude:.2f}")

        result = self.set_voice_settings(output={"volume": amplitude})

        if result.get("success"):
            self.output_volume = perceptual_volume

        return result

    def toggle_mute(self) -> Dict[str, Any]:
        """
        Toggle mute state.

        Returns:
            Dictionary with 'success', 'is_muted', and optional 'message'
        """
        self.get_voice_settings()  # Refresh current state
        new_state = not self.is_muted

        result = self.set_voice_settings(mute=new_state)

        if result.get("success"):
            self.is_muted = new_state
            return {"success": True, "is_muted": new_state}

        return result

    def toggle_deafen(self) -> Dict[str, Any]:
        """
        Toggle deafen state.

        Note: Deafening also mutes the user.

        Returns:
            Dictionary with 'success', 'is_deafened', 'is_muted', and optional 'message'
        """
        self.get_voice_settings()  # Refresh current state
        new_state = not self.is_deafened

        result = self.set_voice_settings(deaf=new_state)

        if result.get("success"):
            self.is_deafened = new_state
            if new_state:
                self.is_muted = True
            return {"success": True, "is_deafened": new_state, "is_muted": self.is_muted}

        return result

    def get_selected_voice_channel(self) -> Optional[Dict[str, Any]]:
        """
        Get currently selected voice channel and members.

        Updates internal state with channel info and members.

        Returns:
            Channel data or None if not in voice
        """
        result = self.rpc.send_command("GET_SELECTED_VOICE_CHANNEL")

        if not result or not result.get("data"):
            # Not in voice channel
            self.voice_channel_id = None
            self.voice_channel_name = None
            self.voice_guild_id = None
            self.voice_members = []
            return None

        data = result["data"]

        if not data:
            # Empty response means not in voice
            self.voice_channel_id = None
            self.voice_channel_name = None
            self.voice_guild_id = None
            self.voice_members = []
            return None

        # Update channel info
        self.voice_channel_id = data.get("id")
        self.voice_channel_name = data.get("name")
        self.voice_guild_id = data.get("guild_id")

        # Parse members
        voice_states = data.get("voice_states", [])
        self.voice_members = []

        for vs in voice_states:
            user = vs.get("user", {})
            member = {
                "user_id": user.get("id"),
                "username": user.get("username", "User"),
                "avatar": user.get("avatar"),
                "mute": vs.get("mute", False) or vs.get("self_mute", False),
                "deaf": vs.get("deaf", False) or vs.get("self_deaf", False),
                "volume": vs.get("volume", 100),
            }
            self.voice_members.append(member)

        return data

    def select_voice_channel(self, channel_id: Optional[str], force: bool = False) -> bool:
        """
        Join or leave voice channel.

        Args:
            channel_id: Channel ID to join, or None to leave
            force: Force join even if already in another channel

        Returns:
            True if successful, False otherwise
        """
        args = {"channel_id": channel_id}
        if force:
            args["force"] = True

        result = self.rpc.send_command("SELECT_VOICE_CHANNEL", args)
        return result is not None

    def set_user_voice_settings(self, user_id: str, volume: Optional[int] = None, mute: Optional[bool] = None) -> bool:
        """
        Set voice settings for a specific user (local, not server-wide).

        Args:
            user_id: Discord user ID
            volume: User volume (0-200), optional
            mute: Mute state, optional

        Returns:
            True if successful, False otherwise
        """
        args = {"user_id": user_id}

        if volume is not None:
            args["volume"] = max(0, min(200, volume))

        if mute is not None:
            args["mute"] = mute

        result = self.rpc.send_command("SET_USER_VOICE_SETTINGS", args)
        return result is not None and result.get("cmd") == "SET_USER_VOICE_SETTINGS"

    def get_channels(self, guild_id: str) -> List[Dict[str, Any]]:
        """
        Get voice channels for a guild.

        Args:
            guild_id: Discord guild (server) ID

        Returns:
            List of voice channel dictionaries
        """
        result = self.rpc.send_command("GET_CHANNELS", {"guild_id": guild_id})

        if result and result.get("data"):
            channels = result["data"].get("channels", [])
            # Filter for voice channels (type 2)
            voice_channels = [c for c in channels if c.get("type") == 2]
            return voice_channels

        return []

    def get_guilds(self) -> List[Dict[str, Any]]:
        """
        Get list of guilds (servers) user is in.

        Adds icon_url field for convenience.

        Returns:
            List of guild dictionaries with icon URLs
        """
        result = self.rpc.send_command("GET_GUILDS")

        if result and result.get("data"):
            guilds = result["data"].get("guilds", [])

            # Add icon URLs
            for guild in guilds:
                guild_id = guild.get("id")
                icon_hash = guild.get("icon")

                if guild_id and icon_hash:
                    guild["icon_url"] = f"https://cdn.discordapp.com/icons/{guild_id}/{icon_hash}.png?size=64"
                else:
                    guild["icon_url"] = None

            return guilds

        return []
