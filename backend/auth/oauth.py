"""OAuth2 PKCE authentication flow for Discord"""

import secrets
import hashlib
import base64
import json
import urllib.request
import urllib.parse
import urllib.error
import ssl
from typing import Dict, Tuple, Optional


class OAuth2Manager:
    """
    Manages OAuth2 PKCE authentication flow.

    PKCE (Proof Key for Code Exchange) allows public clients (like this plugin)
    to authenticate without storing a client_secret.
    """

    def __init__(self, client_id: str, logger=None):
        """
        Initialize OAuth2 manager.

        Args:
            client_id: Discord application client ID
            logger: Logger instance for logging operations
        """
        self.client_id = client_id
        self.logger = logger

        # SSL context for Steam Deck (certificates may not be properly configured)
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE

    def generate_pkce_pair(self) -> Tuple[str, str]:
        """
        Generate PKCE verifier and challenge pair.

        Returns:
            Tuple of (verifier, challenge)

        Example:
            >>> verifier, challenge = oauth.generate_pkce_pair()
            >>> len(verifier) >= 32
            True
        """
        # Generate random verifier (43-128 characters)
        verifier = secrets.token_urlsafe(32)

        # Create SHA256 hash of verifier
        digest = hashlib.sha256(verifier.encode()).digest()

        # Base64 URL-safe encode without padding
        challenge = base64.urlsafe_b64encode(digest).decode().rstrip('=')

        return verifier, challenge

    def exchange_code_for_token(self, code: str, code_verifier: str) -> Dict[str, any]:
        """
        Exchange authorization code for access token.

        Args:
            code: Authorization code from Discord
            code_verifier: PKCE code verifier

        Returns:
            Dictionary with 'success' and either 'access_token' or 'message'

        Example:
            >>> result = oauth.exchange_code_for_token(code, verifier)
            >>> result['success']
            True
            >>> 'access_token' in result
            True
        """
        if self.logger:
            self.logger.info("Discord Lite: Exchanging authorization code for token (PKCE)...")

        # Build request payload (no client_secret needed for PKCE)
        data_dict = {
            "grant_type": "authorization_code",
            "client_id": self.client_id,
            "code": code,
            "code_verifier": code_verifier,
        }

        data_encoded = urllib.parse.urlencode(data_dict).encode()

        try:
            request = urllib.request.Request(
                "https://discord.com/api/oauth2/token",
                data=data_encoded,
                method="POST",
                headers={
                    "Content-Type": "application/x-www-form-urlencoded",
                    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
                    "Accept": "application/json"
                }
            )

            with urllib.request.urlopen(request, timeout=15, context=self.ssl_context) as response:
                result = json.loads(response.read().decode())
                access_token = result.get("access_token")

                if access_token:
                    if self.logger:
                        self.logger.info("Discord Lite: Access token obtained via PKCE")
                    return {"success": True, "access_token": access_token}
                else:
                    error_description = result.get("error_description", "Unknown error")
                    if self.logger:
                        self.logger.error(f"Discord Lite: Token response missing access_token: {result}")
                    return {"success": False, "message": f"API error: {error_description}"}

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            if self.logger:
                self.logger.error(f"Discord Lite: HTTP {e.code} error: {error_body}")
            return {"success": False, "message": f"HTTP {e.code} error"}

        except Exception as e:
            if self.logger:
                self.logger.error(f"Discord Lite: Token exchange error: {e}")
            return {"success": False, "message": str(e)}

    def refresh_token(self, refresh_token: str) -> Dict[str, any]:
        """
        Refresh access token using refresh token.

        Note: Current implementation uses public client flow without refresh tokens.
        This method is a placeholder for future implementation.

        Args:
            refresh_token: OAuth2 refresh token

        Returns:
            Dictionary with 'success' and either 'access_token' or 'message'
        """
        if self.logger:
            self.logger.warning("Discord Lite: Token refresh not implemented for public client flow")
        return {"success": False, "message": "Refresh not supported"}
