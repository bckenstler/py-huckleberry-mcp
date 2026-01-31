"""Tests for authentication module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from huckleberry_mcp.auth import HuckleberryAuth, HuckleberryAuthError, get_authenticated_api


@pytest.fixture
def auth():
    """Create a fresh auth instance for each test."""
    return HuckleberryAuth()


@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables."""
    monkeypatch.setenv("HUCKLEBERRY_EMAIL", "test@example.com")
    monkeypatch.setenv("HUCKLEBERRY_PASSWORD", "testpassword")
    monkeypatch.setenv("HUCKLEBERRY_TIMEZONE", "America/New_York")


def test_load_credentials_success(auth, mock_env):
    """Test successful credential loading."""
    auth.load_credentials()
    assert auth.email == "test@example.com"
    assert auth.password == "testpassword"
    assert auth.timezone == "America/New_York"


def test_load_credentials_missing_email(auth, monkeypatch):
    """Test error when email is missing."""
    monkeypatch.setenv("HUCKLEBERRY_PASSWORD", "testpassword")
    monkeypatch.delenv("HUCKLEBERRY_EMAIL", raising=False)

    with pytest.raises(HuckleberryAuthError, match="Missing credentials"):
        auth.load_credentials()


def test_load_credentials_missing_password(auth, monkeypatch):
    """Test error when password is missing."""
    monkeypatch.setenv("HUCKLEBERRY_EMAIL", "test@example.com")
    monkeypatch.delenv("HUCKLEBERRY_PASSWORD", raising=False)

    with pytest.raises(HuckleberryAuthError, match="Missing credentials"):
        auth.load_credentials()


def test_load_credentials_default_timezone(auth, monkeypatch):
    """Test default timezone when not specified."""
    monkeypatch.setenv("HUCKLEBERRY_EMAIL", "test@example.com")
    monkeypatch.setenv("HUCKLEBERRY_PASSWORD", "testpassword")
    monkeypatch.delenv("HUCKLEBERRY_TIMEZONE", raising=False)

    auth.load_credentials()
    assert auth.timezone == "America/New_York"


@pytest.mark.asyncio
async def test_authenticate_success(auth, mock_env):
    """Test successful authentication."""
    with patch("huckleberry_mcp.auth.HuckleberryAPI") as mock_api_class:
        mock_api = AsyncMock()
        # get_children is synchronous, not async! Use MagicMock for synchronous methods
        mock_api.get_children = MagicMock(return_value=[])
        mock_api_class.return_value = mock_api

        await auth.authenticate()

        assert auth.api is not None
        mock_api_class.assert_called_once_with(
            email="test@example.com",
            password="testpassword",
            timezone="America/New_York"
        )
        mock_api.get_children.assert_called_once()


@pytest.mark.asyncio
async def test_authenticate_failure(auth, mock_env):
    """Test authentication failure."""
    with patch("huckleberry_mcp.auth.HuckleberryAPI") as mock_api_class:
        mock_api = AsyncMock()
        # get_children is synchronous, not async! Use MagicMock for synchronous methods
        mock_api.get_children = MagicMock(side_effect=Exception("Auth failed"))
        mock_api_class.return_value = mock_api

        with pytest.raises(HuckleberryAuthError, match="Failed to authenticate"):
            await auth.authenticate()


def test_get_api_not_authenticated(auth):
    """Test getting API when not authenticated."""
    with pytest.raises(HuckleberryAuthError, match="Not authenticated"):
        auth.get_api()


@pytest.mark.asyncio
async def test_get_api_authenticated(auth, mock_env):
    """Test getting API after authentication."""
    with patch("huckleberry_mcp.auth.HuckleberryAPI") as mock_api_class:
        mock_api = AsyncMock()
        # get_children is synchronous, not async! Use MagicMock for synchronous methods
        mock_api.get_children = MagicMock(return_value=[])
        mock_api_class.return_value = mock_api

        await auth.authenticate()
        api = auth.get_api()

        assert api is mock_api
