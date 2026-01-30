"""Tests for sleep tracking tools."""

import pytest
from unittest.mock import AsyncMock, patch
from huckleberry_mcp.tools import sleep


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = AsyncMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.start_sleep_timer = AsyncMock()
    api.pause_sleep_timer = AsyncMock()
    api.resume_sleep_timer = AsyncMock()
    api.complete_sleep_timer = AsyncMock()
    api.cancel_sleep_timer = AsyncMock()
    api.get_sleep_timer_status = AsyncMock(return_value=None)
    api.get_sleep_history = AsyncMock(return_value=[])
    return api


@pytest.mark.asyncio
async def test_start_sleep_success(mock_api):
    """Test starting a sleep session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.start_sleep("child1")

        assert result["success"] is True
        assert "started" in result["message"]
        mock_api.start_sleep_timer.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_start_sleep_already_active(mock_api):
    """Test starting sleep when already active."""
    mock_api.get_sleep_timer_status = AsyncMock(return_value={"isActive": True})

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="already active"):
            await sleep.start_sleep("child1")


@pytest.mark.asyncio
async def test_pause_sleep_success(mock_api):
    """Test pausing a sleep session."""
    mock_api.get_sleep_timer_status = AsyncMock(return_value={"isActive": True, "isPaused": False})

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.pause_sleep("child1")

        assert result["success"] is True
        assert "paused" in result["message"]
        mock_api.pause_sleep_timer.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_pause_sleep_no_active_session(mock_api):
    """Test pausing when no active session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="No active sleep session"):
            await sleep.pause_sleep("child1")


@pytest.mark.asyncio
async def test_resume_sleep_success(mock_api):
    """Test resuming a paused sleep session."""
    mock_api.get_sleep_timer_status = AsyncMock(return_value={"isActive": True, "isPaused": True})

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.resume_sleep("child1")

        assert result["success"] is True
        assert "resumed" in result["message"]
        mock_api.resume_sleep_timer.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_complete_sleep_success(mock_api):
    """Test completing a sleep session."""
    mock_api.get_sleep_timer_status = AsyncMock(return_value={"isActive": True})

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.complete_sleep("child1")

        assert result["success"] is True
        assert "completed" in result["message"]
        mock_api.complete_sleep_timer.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_cancel_sleep_success(mock_api):
    """Test cancelling a sleep session."""
    mock_api.get_sleep_timer_status = AsyncMock(return_value={"isActive": True})

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.cancel_sleep("child1")

        assert result["success"] is True
        assert "cancelled" in result["message"]
        mock_api.cancel_sleep_timer.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_get_sleep_status_active(mock_api):
    """Test getting status of active sleep session."""
    mock_api.get_sleep_timer_status = AsyncMock(return_value={
        "isActive": True,
        "isPaused": False,
        "startTime": "2024-01-01T10:00:00",
        "elapsedSeconds": 3600
    })

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.get_sleep_status("child1")

        assert result["is_active"] is True
        assert result["is_paused"] is False
        assert result["elapsed_seconds"] == 3600


@pytest.mark.asyncio
async def test_get_sleep_status_inactive(mock_api):
    """Test getting status when no active session."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.get_sleep_status("child1")

        assert result["is_active"] is False


@pytest.mark.asyncio
async def test_get_sleep_history(mock_api):
    """Test getting sleep history."""
    mock_api.get_sleep_history = AsyncMock(return_value=[
        {
            "startTime": "2024-01-01T10:00:00",
            "endTime": "2024-01-01T12:00:00",
            "durationMinutes": 120,
            "notes": "Good nap"
        }
    ])

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.get_sleep_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["duration_minutes"] == 120
        mock_api.get_sleep_history.assert_called_once_with(
            "child1",
            start_date="2024-01-01",
            end_date="2024-01-02"
        )
