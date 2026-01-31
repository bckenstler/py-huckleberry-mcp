"""Tests for feeding tracking tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo
from huckleberry_mcp.tools import feeding


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = MagicMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.start_feeding = MagicMock()  # Synchronous, not async
    api.pause_feeding = MagicMock()  # Synchronous, not async
    api.resume_feeding = MagicMock()  # Synchronous, not async
    api.switch_feeding_side = MagicMock()  # Synchronous, not async
    api.complete_feeding = MagicMock()  # Synchronous, not async
    api.cancel_feeding = MagicMock()  # Synchronous, not async
    api.get_feed_intervals = MagicMock(return_value=[])  # Synchronous, not async
    api._timezone = ZoneInfo("America/New_York")  # EST/EDT timezone
    return api


@pytest.mark.asyncio
async def test_start_breastfeeding_success(mock_api):
    """Test starting a breastfeeding session."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.start_breastfeeding("child1", "left")

        assert result["success"] is True
        assert result["side"] == "left"
        mock_api.start_feeding.assert_called_once_with("child1", side="left")


@pytest.mark.asyncio
async def test_start_breastfeeding_invalid_side(mock_api):
    """Test starting breastfeeding with invalid side."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid side"):
            await feeding.start_breastfeeding("child1", "middle")


@pytest.mark.asyncio
async def test_switch_feeding_side_success(mock_api):
    """Test switching feeding sides."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.switch_feeding_side("child1")

        assert result["success"] is True
        assert "message" in result
        mock_api.switch_feeding_side.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_get_feeding_history(mock_api):
    """Test getting feeding history."""
    # Mock get_feed_intervals to return intervals with 'start' timestamp
    mock_api.get_feed_intervals = MagicMock(return_value=[
        {
            "start": 1704103200,  # Unix timestamp
            "leftDuration": 10,
            "rightDuration": 15,
            "is_multi_entry": False
        }
    ])

    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.get_feeding_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["left_duration_minutes"] == 10
        assert result[0]["right_duration_minutes"] == 15
