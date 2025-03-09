import time
from typing import Optional

import httpx
from config import Config
from httpx import HTTPStatusError
from src.Shared.Exceptions import OauthTokenRetrievalError

config = Config()


class OAuthService:
    def __init__(self, config: Config):
        self.config = config
        self.issued_at: Optional[float] = None
        self.issued_at = None
        self.expires_in = None
        self.access_token: Optional[str] = None

    async def get_oauth_token(self) -> str:
        """Returns a fresh oauth token.

        Returns:
            str: the fresh oauth token

        Raises:
            OauthTokenRetrievalError: if a non 2XX status code is received
        """

        if self.access_token is not None and time.time() - self.issued_at <= self.expires_in / 2:
            if self.access_token is None:
                raise OauthTokenRetrievalError("Failed to retrieve access token")
            return self.access_token

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    config.oauth_url,  # Changed from self.settings.oauth_url to config.oauth_url
                    headers={
                        "Authorization": "Basic " + config.oauth_client_credentials
                    },  # Changed to config
                    data={
                        "grant_type": "password",
                        "username": config.oauth_nuid_username,  # Changed to config
                        "password": config.oauth_nuid_password,  # Changed to config
                        "scope": "openid profile email",
                    },
                )
                response.raise_for_status()
                data = response.json()

                self.access_token = data["access_token"]
                self.issued_at = time.time()
                self.expires_in = data["expires_in"]
                return self.access_token
            except HTTPStatusError as e:
                raise OauthTokenRetrievalError(e.response.status_code, e.response.text)


oauth_service = OAuthService(config)  # Pass config object to OAuthService
