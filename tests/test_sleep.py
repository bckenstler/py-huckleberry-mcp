"""Tests for sleep tracking tools."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from zoneinfo import ZoneInfo
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
    api._get_timezone_offset_minutes = MagicMock(return_value=-300.0)  # EST offset
    api._timezone = ZoneInfo("America/New_York")  # EST/EDT timezone

    # Mock Firestore client for log_sleep
    mock_firestore = MagicMock()
    mock_collection = MagicMock()
    mock_document = MagicMock()
    mock_intervals_collection = MagicMock()
    mock_interval_doc = MagicMock()

    # Setup chain: client.collection("sleep").document(child_uid)
    mock_firestore.collection.return_value = mock_collection
    mock_collection.document.return_value = mock_document

    # Setup chain: sleep_ref.collection("intervals").document(interval_id)
    mock_document.collection.return_value = mock_intervals_collection
    mock_intervals_collection.document.return_value = mock_interval_doc

    api._get_firestore_client = MagicMock(return_value=mock_firestore)

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
    # Backend returns duration in seconds
    mock_api.get_sleep_intervals = MagicMock(return_value=[
        {
            "start": 1704103200,  # Unix timestamp
            "end": 1704110400,
            "duration": 120  # Backend returns seconds
        }
    ])

    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.get_sleep_history("child1", "2024-01-01", "2024-01-02")

        assert len(result) == 1
        assert result[0]["duration_minutes"] == 2  # 120 seconds / 60 = 2 minutes


@pytest.mark.asyncio
async def test_log_sleep_with_duration(mock_api):
    """Test logging sleep with duration_minutes."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.log_sleep(
            "child1",
            start_time="2024-01-01T14:00:00Z",
            duration_minutes=90
        )

        assert result["success"] is True
        assert result["duration_minutes"] == 90
        assert "start_time" in result
        assert "end_time" in result
        assert "interval_id" in result


@pytest.mark.asyncio
async def test_log_sleep_with_end_time(mock_api):
    """Test logging sleep with end_time."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        result = await sleep.log_sleep(
            "child1",
            start_time="2024-01-01T14:00:00Z",
            end_time="2024-01-01T15:30:00Z"
        )

        assert result["success"] is True
        assert result["duration_minutes"] == 90
        assert "interval_id" in result


@pytest.mark.asyncio
async def test_log_sleep_no_duration_or_end_time(mock_api):
    """Test logging sleep without duration or end_time raises error."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Either end_time or duration_minutes must be provided"):
            await sleep.log_sleep("child1", start_time="2024-01-01T14:00:00Z")


@pytest.mark.asyncio
async def test_log_sleep_both_duration_and_end_time(mock_api):
    """Test logging sleep with both duration and end_time raises error."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="Provide either end_time or duration_minutes, not both"):
            await sleep.log_sleep(
                "child1",
                start_time="2024-01-01T14:00:00Z",
                end_time="2024-01-01T15:30:00Z",
                duration_minutes=90
            )


@pytest.mark.asyncio
async def test_log_sleep_end_before_start(mock_api):
    """Test logging sleep with end_time before start_time raises error."""
    with patch("huckleberry_mcp.tools.sleep.get_authenticated_api", return_value=mock_api), \
         patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):

        with pytest.raises(ValueError, match="end_time must be after start_time"):
            await sleep.log_sleep(
                "child1",
                start_time="2024-01-01T15:00:00Z",
                end_time="2024-01-01T14:00:00Z"
            )
