"""Tests for growth tracking tools."""

import pytest
from unittest.mock import AsyncMock, patch
from huckleberry_mcp.tools import growth


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = AsyncMock(return_value=[{"uid": "child1", "name": "Alice"}])
    api.log_growth_measurement = AsyncMock()
    api.get_latest_growth_measurement = AsyncMock(return_value=None)
    api.get_growth_history = AsyncMock(return_value=[])
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
        mock_api.log_growth_measurement.assert_called_once()


@pytest.mark.asyncio
async def test_log_growth_all_measurements(mock_api):
    """Test logging all growth measurements."""
    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.log_growth(
            "child1",
            weight=10.5,
            height=24.0,
            head_circumference=16.5,
            units="imperial"
        )

        assert result["success"] is True
        assert result["weight"] == 10.5
        assert result["height"] == 24.0
        assert result["head_circumference"] == 16.5


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
    mock_api.get_latest_growth_measurement = AsyncMock(return_value={
        "timestamp": "2024-01-01T10:00:00",
        "weight": 10.5,
        "height": 24.0,
        "headCircumference": 16.5,
        "units": "imperial",
        "ageDays": 90
    })

    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.get_latest_growth("child1")

        assert result["weight"] == 10.5
        assert result["height"] == 24.0
        assert result["head_circumference"] == 16.5


@pytest.mark.asyncio
async def test_get_latest_growth_no_data(mock_api):
    """Test getting latest growth when no measurements exist."""
    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.get_latest_growth("child1")

        assert "No growth measurements" in result["message"]


@pytest.mark.asyncio
async def test_get_growth_history(mock_api):
    """Test getting growth history."""
    mock_api.get_growth_history = AsyncMock(return_value=[
        {
            "timestamp": "2024-01-01T10:00:00",
            "weight": 10.5,
            "height": 24.0,
            "headCircumference": 16.5,
            "units": "imperial",
            "ageDays": 90
        }
    ])

    with patch("huckleberry_mcp.tools.growth.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await growth.get_growth_history("child1", "2024-01-01", "2024-01-31")

        assert len(result) == 1
        assert result[0]["weight"] == 10.5
