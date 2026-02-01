"""Tests for utility functions."""

from zoneinfo import ZoneInfo
from huckleberry_mcp.utils import (
    iso_to_timestamp,
    iso_datetime_to_timestamp,
    timestamp_to_local_iso,
)


def test_timestamp_to_local_iso_without_timezone():
    """Test converting timestamp to ISO string without timezone returns UTC."""
    ts = 1738432800  # 2025-02-01T18:00:00 UTC
    result = timestamp_to_local_iso(ts, None)
    assert result == "2025-02-01T18:00:00+00:00"


def test_timestamp_to_local_iso_with_timezone():
    """Test converting timestamp to ISO string with timezone returns local time."""
    ts = 1738432800  # 2025-02-01T18:00:00 UTC
    est = ZoneInfo("America/New_York")
    result = timestamp_to_local_iso(ts, est)
    assert result == "2025-02-01T13:00:00-05:00"


def test_timestamp_to_local_iso_with_pst():
    """Test converting timestamp to ISO string with PST timezone."""
    ts = 1738432800  # 2025-02-01T18:00:00 UTC
    pst = ZoneInfo("America/Los_Angeles")
    result = timestamp_to_local_iso(ts, pst)
    assert result == "2025-02-01T10:00:00-08:00"


def test_round_trip_conversion():
    """Test that input timezone -> timestamp -> local ISO is consistent."""
    # Start with a local time in EST
    local_time = "2025-02-01T14:30:00"
    est = ZoneInfo("America/New_York")

    # Convert to timestamp
    ts = iso_datetime_to_timestamp(local_time, est)

    # Convert back to local ISO
    result = timestamp_to_local_iso(ts, est)

    # Should get back the same time (with timezone info)
    assert result == "2025-02-01T14:30:00-05:00"
