"""Tests for growth tracking tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from zoneinfo import ZoneInfo
from huckleberry_mcp.tools import growth


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = MagicMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.log_growth = MagicMock()  # Synchronous, not async
    api.get_growth_data = MagicMock(return_value={
        "weight_units": "kg",
        "height_units": "cm",
        "head_units": "hcm"
    })  # Synchronous, not async
    api.get_health_entries = MagicMock(return_value=[])  # Synchronous, not async
    api._timezone = ZoneInfo("America/New_York")  # EST/EDT timezone
    return api


@pytest.mark.asyncio
async def test_log_growth_weight_only(mock_api):
    """Test logging weight measurement only."""
    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.log_growth("child1", weight=10.5)

        assert result["success"] is True
        assert result["weight"] == 10.5
        assert "weight: 10.5lbs" in result["message"]
        mock_api.log_growth.assert_called_once()


@pytest.mark.asyncio
async def test_log_growth_all_measurements(mock_api):
    """Test logging all growth measurements."""
    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.log_growth(
            "child1",
            weight=10.5,
            height=24.0,
            head=16.5,
            units="imperial"
        )

        assert result["success"] is True
        assert result["weight"] == 10.5
        assert result["height"] == 24.0
        assert result["head"] == 16.5


@pytest.mark.asyncio
async def test_log_growth_metric_units(mock_api):
    """Test logging growth with metric units."""
    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.log_growth("child1", weight=5.0, units="metric")

        assert result["success"] is True
        assert "5.0kg" in result["message"]


@pytest.mark.asyncio
async def test_log_growth_no_measurements(mock_api):
    """Test logging growth with no measurements."""
    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="At least one measurement"):
            await growth.log_growth("child1")


@pytest.mark.asyncio
async def test_log_growth_invalid_units(mock_api):
    """Test logging growth with invalid units."""
    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid units"):
            await growth.log_growth("child1", weight=10.5, units="invalid")


@pytest.mark.asyncio
async def test_get_latest_growth(mock_api):
    """Test getting latest growth measurements."""
    mock_api.get_growth_data = MagicMock(return_value={
        "weight": 10.5,
        "height": 24.0,
        "head": 16.5,
        "weight_units": "lbs",
        "height_units": "in",
        "head_units": "in",
        "timestamp_sec": 1704103200
    })

    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.get_latest_growth("child1")

        assert result["weight"] == 10.5
        assert result["height"] == 24.0
        assert result["head"] == 16.5


@pytest.mark.asyncio
async def test_get_latest_growth_no_data(mock_api):
    """Test getting latest growth when no measurements exist."""
    mock_api.get_growth_data = MagicMock(return_value={
        "weight_units": "kg",
        "height_units": "cm",
        "head_units": "hcm"
    })

    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.get_latest_growth("child1")

        assert "No growth measurements" in result["message"]


@pytest.mark.asyncio
async def test_get_growth_history(mock_api):
    """Test getting growth history."""
    mock_api.get_health_entries = MagicMock(return_value=[
        {
            "start": 1704103200,  # Unix timestamp
            "weight": 10.5,
            "height": 24.0,
            "head": 16.5
        }
    ])

    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.get_growth_history("child1", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["weight"] == 10.5
        assert result[0]["height"] == 24.0
        assert result[0]["head"] == 16.5
