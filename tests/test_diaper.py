"""Tests for diaper tracking tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo
from huckleberry_mcp.tools import diaper


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = MagicMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.log_diaper = MagicMock()  # Synchronous, not async
    api.get_diaper_intervals = MagicMock(return_value=[])  # Synchronous, not async
    api._timezone = ZoneInfo("America/New_York")  # EST/EDT timezone
    api._get_timezone_offset_minutes = MagicMock(return_value=-300.0)  # EST offset

    # Mock Firestore client for log_diaper with timestamp
    mock_firestore = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_intervals_collection = MagicMock()
    mock_interval_doc = MagicMock()

    # Setup chain: client.collection("diaper").document(child_uid)
    mock_firestore.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document

    # Setup chain: diaper_ref.collection("intervals").document(interval_id)
    mock_document.collection.return_value = mock_intervals_collection
    mock_intervals_collection.document.return_value = mock_interval_doc

    api._get_firestore_client = MagicMock(return_value=mock_firestore)

    return api


@pytest.mark.asyncio
async def test_log_diaper_success(mock_api):
    """Test logging a diaper change."""
    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await diaper.log_diaper("child1", "both")

        assert result["success"] is True
        assert result["mode"] == "both"


@pytest.mark.asyncio
async def test_log_diaper_with_details(mock_api):
    """Test logging a diaper change with color and consistency."""
    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await diaper.log_diaper(
            "child1",
            "poo",
            color="brown",
            consistency="solid"
        )

        assert result["success"] is True
        assert result["color"] == "brown"
        assert result["consistency"] == "solid"


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

        with pytest.raises(ValueError, match="Invalid color"):
            await diaper.log_diaper("child1", "poo", color="purple")


@pytest.mark.asyncio
async def test_get_diaper_history(mock_api):
    """Test getting diaper history."""
    # Mock get_diaper_intervals to return intervals with 'start' timestamp
    mock_api.get_diaper_intervals = MagicMock(return_value=[
        {
            "start": 1704103200,  # Unix timestamp for 2024-01-01T10:00:00 UTC
            "mode": "both",
            "color": "brown",
            "consistency": "solid",
            "notes": "test note"
        }
    ])

    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await diaper.get_diaper_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["mode"] == "both"
        assert result[0]["color"] == "brown"
        assert result[0]["consistency"] == "solid"


@pytest.mark.asyncio
async def test_log_diaper_with_timestamp(mock_api):
    """Test logging diaper with custom timestamp for retroactive logging."""
    with patch("huckleberry_mcp.tools.diaper.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await diaper.log_diaper(
            "child1",
            mode="poo",
            color="brown",
            timestamp="2024-01-15T10:30:00Z"
        )

        assert result["success"] is True
        assert result["mode"] == "poo"
        assert result["color"] == "brown"
        assert "2024-01-15" in result["timestamp"]
