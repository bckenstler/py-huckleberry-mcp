"""Authentication handler for Huckleberry API."""

import os
import sys
from typing import Optional
from huckleberry_api import HuckleberryAPI


class HuckleberryAuthError(Exception):
    """Raised when authentication fails."""
    pass


class HuckleberryAuth:
    """Manages authentication with the Huckleberry API."""

    def __init__(self):
        self.api: Optional[HuckleberryAPI] = None
        self.email: Optional[str] = None
        self.password: Optional[str] = None
        self.timezone: Optional[str] = None

    def load_credentials(self) -> None:
        """Load credentials from environment variables."""
        self.email = os.getenv("HUCKLEBERRY_EMAIL")
        self.password = os.getenv("HUCKLEBERRY_PASSWORD")
        self.timezone = os.getenv("HUCKLEBERRY_TIMEZONE", "America/New_York")

        if not self.email or not self.password:
            raise HuckleberryAuthError(
                "Missing credentials. Please set HUCKLEBERRY_EMAIL and "
                "HUCKLEBERRY_PASSWORD environment variables."
            )

    async def authenticate(self) -> None:
        """Authenticate with the Huckleberry API."""
        if not self.email or not self.password:
            self.load_credentials()

        try:
            self.api = HuckleberryAPI(
                email=self.email,
                password=self.password,
                timezone=self.timezone
            )

            # Test authentication by attempting to get children
            # This will raise an exception if auth fails
            self.api.get_children()

            print(f"Successfully authenticated with Huckleberry API", file=sys.stderr)

        except Exception as e:
            raise HuckleberryAuthError(
                f"Failed to authenticate with Huckleberry API: {str(e)}"
            )

    def get_api(self) -> HuckleberryAPI:
        """Get the authenticated API instance."""
        if not self.api:
            raise HuckleberryAuthError(
                "Not authenticated. Call authenticate() first."
            )
        return self.api


# Global auth instance
_auth = HuckleberryAuth()


async def get_authenticated_api() -> HuckleberryAPI:
    """Get an authenticated Huckleberry API instance."""
    if not _auth.api:
        await _auth.authenticate()
    return _auth.get_api()
