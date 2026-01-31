"""Tests for diaper tracking tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from huckleberry_mcp.tools import diaper


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = MagicMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.log_diaper_change = AsyncMock()
    api.get_diaper_history = AsyncMock(return_value=[])
    return api


@pytest.mark.asyncio
async def test_log_diaper_success(mock_api):
    """Test logging a diaper change."""
    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await diaper.log_diaper("child1", "both")

        assert result["success"] is True
        assert result["mode"] == "both"
        mock_api.log_diaper_change.assert_called_once()


@pytest.mark.asyncio
async def test_log_diaper_with_details(mock_api):
    """Test logging a diaper change with color and consistency."""
    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await diaper.log_diaper(
            "child1",
            "poo",
            poo_color="brown",
            consistency="soft"
        )

        assert result["success"] is True
        assert result["poo_color"] == "brown"
        assert result["consistency"] == "soft"


@pytest.mark.asyncio
async def test_log_diaper_invalid_mode(mock_api):
    """Test logging diaper with invalid mode."""
    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid mode"):
            await diaper.log_diaper("child1", "invalid")


@pytest.mark.asyncio
async def test_log_diaper_invalid_color(mock_api):
    """Test logging diaper with invalid poo color."""
    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid poo_color"):
            await diaper.log_diaper("child1", "poo", poo_color="purple")


@pytest.mark.asyncio
async def test_get_diaper_history(mock_api):
    """Test getting diaper history."""
    mock_api.get_diaper_history = AsyncMock(return_value=[
        {
            "timestamp": "2024-01-01T10:00:00",
            "mode": "both",
            "hasPee": True,
            "hasPoo": True,
            "pooColor": "brown",
            "consistency": "soft"
        }
    ])

    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await diaper.get_diaper_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["mode"] == "both"
        assert result[0]["poo_color"] == "brown"
