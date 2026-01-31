"""Tests for sleep tracking tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from huckleberry_mcp.tools import sleep


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = MagicMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.start_sleep = MagicMock()  # Synchronous, not async
    api.pause_sleep = MagicMock()  # Synchronous, not async
    api.resume_sleep = MagicMock()  # Synchronous, not async
    api.complete_sleep = MagicMock()  # Synchronous, not async
    api.cancel_sleep = MagicMock()  # Synchronous, not async
    api.get_sleep_intervals = MagicMock(return_value=[])  # Synchronous, not async
    return api


@pytest.mark.asyncio
async def test_start_sleep_success(mock_api):
    """Test starting a sleep session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.start_sleep("child1")

        assert result["success"] is True
        assert "started" in result["message"].lower()
        mock_api.start_sleep.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_pause_sleep_success(mock_api):
    """Test pausing a sleep session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.pause_sleep("child1")

        assert result["success"] is True
        assert "paused" in result["message"].lower()
        mock_api.pause_sleep.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_resume_sleep_success(mock_api):
    """Test resuming a paused sleep session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.resume_sleep("child1")

        assert result["success"] is True
        assert "resumed" in result["message"].lower()
        mock_api.resume_sleep.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_complete_sleep_success(mock_api):
    """Test completing a sleep session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.complete_sleep("child1")

        assert result["success"] is True
        assert "completed" in result["message"].lower()
        mock_api.complete_sleep.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_cancel_sleep_success(mock_api):
    """Test cancelling a sleep session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.cancel_sleep("child1")

        assert result["success"] is True
        assert "cancelled" in result["message"].lower()
        mock_api.cancel_sleep.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_get_sleep_history(mock_api):
    """Test getting sleep history."""
    # Mock get_sleep_intervals to return intervals with 'start', 'end', 'duration'
    mock_api.get_sleep_intervals = MagicMock(return_value=[
        {
            "start": 1704103200,  # Unix timestamp
            "end": 1704110400,
            "duration": 120
        }
    ])

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.get_sleep_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["duration_minutes"] == 120
