"""Tests for feeding tracking tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from huckleberry_mcp.tools import feeding


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = MagicMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.start_breastfeeding_timer = AsyncMock()
    api.pause_feeding_timer = AsyncMock()
    api.resume_feeding_timer = AsyncMock()
    api.switch_breastfeeding_side = AsyncMock()
    api.complete_feeding_timer = AsyncMock()
    api.cancel_feeding_timer = AsyncMock()
    api.log_bottle_feeding = AsyncMock()
    api.get_feeding_timer_status = AsyncMock(return_value=None)
    api.get_feeding_history = AsyncMock(return_value=[])
    return api


@pytest.mark.asyncio
async def test_start_breastfeeding_success(mock_api):
    """Test starting a breastfeeding session."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.start_breastfeeding("child1", "left")

        assert result["success"] is True
        assert result["side"] == "left"
        mock_api.start_breastfeeding_timer.assert_called_once_with("child1", side="left")


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
    mock_api.get_feeding_timer_status = AsyncMock(return_value={
        "isActive": True,
        "currentSide": "left"
    })

    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.switch_feeding_side("child1")

        assert result["success"] is True
        assert result["new_side"] == "right"
        mock_api.switch_breastfeeding_side.assert_called_once_with("child1")


@pytest.mark.asyncio
async def test_log_bottle_feeding_success(mock_api):
    """Test logging bottle feeding."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_bottle_feeding("child1", 4.0, "formula", "oz")

        assert result["success"] is True
        assert result["amount"] == 4.0
        assert result["bottle_type"] == "formula"
        mock_api.log_bottle_feeding.assert_called_once()


@pytest.mark.asyncio
async def test_log_bottle_feeding_invalid_type(mock_api):
    """Test logging bottle feeding with invalid type."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid bottle_type"):
            await feeding.log_bottle_feeding("child1", 4.0, "invalid", "oz")


@pytest.mark.asyncio
async def test_get_feeding_status_active(mock_api):
    """Test getting status of active feeding session."""
    mock_api.get_feeding_timer_status = AsyncMock(return_value={
        "isActive": True,
        "isPaused": False,
        "currentSide": "left",
        "startTime": "2024-01-01T10:00:00",
        "elapsedSeconds": 600
    })

    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.get_feeding_status("child1")

        assert result["is_active"] is True
        assert result["current_side"] == "left"
