"""Discord RPC client with IPC socket communication"""

import socket
import secrets
from typing import Optional, Dict, Any, List

from .protocol import RPCOpcode, encode_message, decode_message
from .events import SpeakingTracker, process_event
from ..utils.socket_finder import find_discord_ipc_socket


class DiscordRPCClient:
    """
    Discord RPC client for IPC communication.

    Handles socket connection, authentication, and command execution.
    """

    def __init__(self, client_id: str, logger=None):
        """
        Initialize Discord RPC client.

        Args:
            client_id: Discord application client ID
            logger: Logger instance for logging operations
        """
        self.client_id = client_id
        self.logger = logger
        self.socket: Optional[socket.socket] = None
        self.connected = False
        self.authenticated = False
        self.access_token: Optional[str] = None
        self.user: Optional[Dict[str, Any]] = None

        # Speaking tracker for voice events
        self.speaking_tracker = SpeakingTracker()

    def connect(self) -> bool:
        """
        Connect to Discord IPC socket and perform handshake.

        Returns:
            True if connection successful, False otherwise
        """
        ipc_path = find_discord_ipc_socket(self.logger)
        if not ipc_path:
            if self.logger:
                self.logger.error("Discord Lite: Discord IPC socket not found")
            return False

        try:
            self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.socket.settimeout(60.0)
            self.socket.connect(ipc_path)

            # Send handshake
            handshake_payload = {"v": 1, "client_id": self.client_id}
            self.socket.send(encode_message(RPCOpcode.HANDSHAKE, handshake_payload))

            # Wait for READY response
            response_data = self.socket.recv(4096)
            opcode, payload = decode_message(response_data, self.logger)

            if payload and payload.get("cmd") == "DISPATCH" and payload.get("evt") == "READY":
                self.connected = True
                if self.logger:
                    self.logger.info("Discord Lite: Connected to Discord IPC")
                return True
            else:
                if self.logger:
                    self.logger.error(f"Discord Lite: Unexpected handshake response: {payload}")
                return False

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Connection error: {e}")
            return False

    def disconnect(self) -> None:
        """Close socket connection and reset state."""
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

        self.connected = False
        self.authenticated = False
        self.speaking_tracker.clear()

    def send_command(self, cmd: str, args: Optional[Dict[str, Any]] = None, nonce: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Send RPC command to Discord and wait for response.

        Args:
            cmd: Command name (e.g., "GET_VOICE_SETTINGS")
            args: Command arguments dictionary
            nonce: Unique request identifier (auto-generated if None)

        Returns:
            Response payload or None on error

        Example:
            >>> client.send_command("SET_VOICE_SETTINGS", {"mute": True})
            {"cmd": "SET_VOICE_SETTINGS", "data": {...}}
        """
        if not self.socket:
            if self.logger:
                self.logger.error("Discord Lite: Cannot send command - not connected")
            return None

        if nonce is None:
            nonce = secrets.token_hex(16)

        payload = {"cmd": cmd, "nonce": nonce}
        if args:
            payload["args"] = args

        try:
            self.socket.send(encode_message(RPCOpcode.FRAME, payload))
            response_data = self.socket.recv(8192)
            opcode, result = decode_message(response_data, self.logger)

            if self.logger:
                self.logger.info(f"Discord Lite: Command {cmd} response: {result}")
            return result

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error sending command {cmd}: {e}")
            return None

    def authorize(self, scopes: List[str], code_challenge: Optional[str] = None) -> Optional[str]:
        """
        Request OAuth2 authorization from Discord.

        Opens authorization dialog in Discord client.

        Args:
            scopes: List of OAuth2 scopes (e.g., ["rpc", "rpc.voice.read"])
            code_challenge: PKCE code challenge (optional)

        Returns:
            Authorization code or None if user declined
        """
        args = {
            "client_id": self.client_id,
            "scopes": scopes,
        }

        # Add PKCE if provided
        if code_challenge:
            args["code_challenge"] = code_challenge
            args["code_challenge_method"] = "S256"

        result = self.send_command("AUTHORIZE", args)

        if result and result.get("data"):
            return result["data"].get("code")

        return None

    def authenticate(self, access_token: str) -> bool:
        """
        Authenticate with Discord using access token.

        Args:
            access_token: OAuth2 access token

        Returns:
            True if authentication successful, False otherwise
        """
        result = self.send_command("AUTHENTICATE", {"access_token": access_token})

        if result and result.get("data"):
            self.authenticated = True
            self.user = result["data"].get("user")
            self.access_token = access_token
            username = self.user.get('username', 'unknown') if self.user else 'unknown'
            if self.logger:
                self.logger.info(f"Discord Lite: Authenticated as {username}")
            return True

        if self.logger:
            self.logger.error(f"Discord Lite: Authentication failed: {result}")
        return False

    def subscribe(self, event: str, args: Optional[Dict[str, Any]] = None) -> bool:
        """
        Subscribe to Discord RPC event.

        Args:
            event: Event name (e.g., "SPEAKING_START")
            args: Event filter arguments (e.g., {"channel_id": "123"})

        Returns:
            True if subscription successful, False otherwise
        """
        payload = {
            "cmd": "SUBSCRIBE",
            "evt": event,
            "nonce": secrets.token_hex(16)
        }

        if args:
            payload["args"] = args

        try:
            self.socket.send(encode_message(RPCOpcode.FRAME, payload))
            response_data = self.socket.recv(4096)
            opcode, result = decode_message(response_data, self.logger)

            if self.logger:
                self.logger.info(f"Discord Lite: Subscribed to {event}: {result}")
            return result is not None and result.get("evt") == event

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error subscribing to {event}: {e}")
            return False

    def receive_event(self, timeout: float = 0.1) -> Optional[Dict[str, Any]]:
        """
        Receive event from Discord (non-blocking).

        Args:
            timeout: Socket timeout in seconds

        Returns:
            Event payload or None if no event available
        """
        if not self.socket:
            return None

        try:
            old_timeout = self.socket.gettimeout()
            self.socket.settimeout(timeout)

            response_data = self.socket.recv(4096)
            self.socket.settimeout(old_timeout)

            opcode, payload = decode_message(response_data, self.logger)

            # Process event through event system
            if payload:
                process_event(payload, self.speaking_tracker, self.logger)

            return payload

        except socket.timeout:
            return None
        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error receiving event: {e}")
            return None

    def get_speaking_users(self) -> List[str]:
        """
        Get list of users currently speaking in voice channel.

        Returns:
            List of user IDs
        """
        return self.speaking_tracker.get_speaking_users()

    def subscribe_speaking_events(self, channel_id: str) -> bool:
        """
        Subscribe to speaking events for a voice channel.

        Args:
            channel_id: Voice channel ID

        Returns:
            True if subscription successful
        """
        try:
            success = True
            success &= self.subscribe("SPEAKING_START", {"channel_id": channel_id})
            success &= self.subscribe("SPEAKING_STOP", {"channel_id": channel_id})

            if success and self.logger:
                self.logger.info(f"Discord Lite: Subscribed to speaking events for channel {channel_id}")

            return success

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Error subscribing to speaking events: {e}")
            return False

    def close(self) -> None:
        """Alias for disconnect() for compatibility."""
        self.disconnect()
