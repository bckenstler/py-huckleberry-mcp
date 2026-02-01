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
    api._get_timezone_offset_minutes = MagicMock(return_value=-300.0)  # EST offset

    # Mock Firestore client for log_breastfeeding
    mock_firestore = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_intervals_collection = MagicMock()
    mock_interval_doc = MagicMock()

    # Setup chain: client.collection("feed").document(child_uid)
    mock_firestore.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document

    # Setup chain: feed_ref.collection("intervals").document(interval_id)
    mock_document.collection.return_value = mock_intervals_collection
    mock_intervals_collection.document.return_value = mock_interval_doc

    api._get_firestore_client = MagicMock(return_value=mock_firestore)

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
    # Backend returns duration in seconds
    mock_api.get_feed_intervals = MagicMock(return_value=[
        {
            "start": 1704103200,  # Unix timestamp
            "leftDuration": 600,  # 600 seconds = 10 minutes
            "rightDuration": 900,  # 900 seconds = 15 minutes
            "is_multi_entry": False
        }
    ])

    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.get_feeding_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["left_duration_minutes"] == 10  # 600 seconds / 60 = 10 minutes
        assert result[0]["right_duration_minutes"] == 15  # 900 seconds / 60 = 15 minutes


@pytest.mark.asyncio
async def test_log_breastfeeding_with_durations(mock_api):
    """Test logging breastfeeding with left and right durations."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_breastfeeding(
            "child1",
            start_time="2024-01-01T14:00:00Z",
            left_duration_minutes=10,
            right_duration_minutes=15
        )

        assert result["success"] is True
        assert result["left_duration_minutes"] == 10
        assert result["right_duration_minutes"] == 15
        assert result["total_duration_minutes"] == 25
        assert result["last_side"] == "right"  # Right has more duration
        assert "interval_id" in result


@pytest.mark.asyncio
async def test_log_breastfeeding_with_end_time(mock_api):
    """Test logging breastfeeding with end_time."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_breastfeeding(
            "child1",
            start_time="2024-01-01T14:00:00Z",
            end_time="2024-01-01T14:30:00Z",
            last_side="left"
        )

        assert result["success"] is True
        assert result["left_duration_minutes"] == 30
        assert result["right_duration_minutes"] == 0
        assert result["total_duration_minutes"] == 30
        assert result["last_side"] == "left"


@pytest.mark.asyncio
async def test_log_breastfeeding_left_only(mock_api):
    """Test logging breastfeeding with only left duration."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_breastfeeding(
            "child1",
            start_time="2024-01-01T14:00:00Z",
            left_duration_minutes=20
        )

        assert result["success"] is True
        assert result["left_duration_minutes"] == 20
        assert result["right_duration_minutes"] == 0
        assert result["last_side"] == "left"


@pytest.mark.asyncio
async def test_log_breastfeeding_no_duration_or_end_time(mock_api):
    """Test logging breastfeeding without duration or end_time raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Must provide either end_time OR"):
            await feeding.log_breastfeeding("child1", start_time="2024-01-01T14:00:00Z")


@pytest.mark.asyncio
async def test_log_breastfeeding_both_end_time_and_durations(mock_api):
    """Test logging breastfeeding with both end_time and durations raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="When using end_time, do not specify"):
            await feeding.log_breastfeeding(
                "child1",
                start_time="2024-01-01T14:00:00Z",
                end_time="2024-01-01T14:30:00Z",
                left_duration_minutes=10
            )


@pytest.mark.asyncio
async def test_log_breastfeeding_end_time_without_last_side(mock_api):
    """Test logging breastfeeding with end_time but no last_side raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="When using end_time, last_side is required"):
            await feeding.log_breastfeeding(
                "child1",
                start_time="2024-01-01T14:00:00Z",
                end_time="2024-01-01T14:30:00Z"
            )


@pytest.mark.asyncio
async def test_log_breastfeeding_invalid_last_side(mock_api):
    """Test logging breastfeeding with invalid last_side raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid last_side"):
            await feeding.log_breastfeeding(
                "child1",
                start_time="2024-01-01T14:00:00Z",
                left_duration_minutes=10,
                last_side="middle"
            )


@pytest.mark.asyncio
async def test_get_feeding_history_multi_entry(mock_api):
    """Test getting feeding history with multi-entry (seconds conversion)."""
    # Mock get_feed_intervals to return multi-entry intervals
    # Backend returns duration in seconds for multi-entry
    mock_api.get_feed_intervals = MagicMock(return_value=[
        {
            "start": 1704103200,  # Unix timestamp
            "leftDuration": 600,  # 600 seconds = 10 minutes
            "rightDuration": 900,  # 900 seconds = 15 minutes
            "is_multi_entry": True
        }
    ])

    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.get_feeding_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["left_duration_minutes"] == 10  # 600 seconds / 60 = 10 minutes
        assert result[0]["right_duration_minutes"] == 15  # 900 seconds / 60 = 15 minutes
        assert result[0]["is_multi_entry"] is True


# ============== Bottle Feeding Tests ==============

@pytest.mark.asyncio
async def test_log_bottle_feeding_success(mock_api):
    """Test logging bottle feeding with default values."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_bottle_feeding("child1", amount=4.0)

        assert result["success"] is True
        assert result["amount"] == 4.0
        assert result["units"] == "oz"
        assert result["bottle_type"] == "Formula"
        assert "interval_id" in result
        assert "timestamp" in result


@pytest.mark.asyncio
async def test_log_bottle_feeding_breast_milk(mock_api):
    """Test logging bottle feeding with breast milk."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_bottle_feeding(
            "child1",
            amount=120,
            bottle_type="Breast Milk",
            units="ml"
        )

        assert result["success"] is True
        assert result["amount"] == 120
        assert result["units"] == "ml"
        assert result["bottle_type"] == "Breast Milk"


@pytest.mark.asyncio
async def test_log_bottle_feeding_mixed(mock_api):
    """Test logging bottle feeding with mixed content."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_bottle_feeding(
            "child1",
            amount=5.5,
            bottle_type="Mixed",
            units="oz"
        )

        assert result["success"] is True
        assert result["amount"] == 5.5
        assert result["bottle_type"] == "Mixed"


@pytest.mark.asyncio
async def test_log_bottle_feeding_with_timestamp(mock_api):
    """Test logging bottle feeding with retroactive timestamp."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await feeding.log_bottle_feeding(
            "child1",
            amount=4.0,
            timestamp="2024-01-01T14:30:00Z"
        )

        assert result["success"] is True
        assert result["amount"] == 4.0
        # Timestamp should be converted to local timezone
        assert "2024-01-01" in result["timestamp"]


@pytest.mark.asyncio
async def test_log_bottle_feeding_invalid_type(mock_api):
    """Test logging bottle feeding with invalid bottle_type raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid bottle_type"):
            await feeding.log_bottle_feeding("child1", amount=4.0, bottle_type="Water")


@pytest.mark.asyncio
async def test_log_bottle_feeding_invalid_units(mock_api):
    """Test logging bottle feeding with invalid units raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Invalid units"):
            await feeding.log_bottle_feeding("child1", amount=4.0, units="cups")


@pytest.mark.asyncio
async def test_log_bottle_feeding_zero_amount(mock_api):
    """Test logging bottle feeding with zero amount raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Amount must be a positive number"):
            await feeding.log_bottle_feeding("child1", amount=0)


@pytest.mark.asyncio
async def test_log_bottle_feeding_negative_amount(mock_api):
    """Test logging bottle feeding with negative amount raises error."""
    with patch("huckleberry_mcp.tools.feeding.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Amount must be a positive number"):
            await feeding.log_bottle_feeding("child1", amount=-2.5)
