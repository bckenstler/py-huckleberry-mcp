"""Shared utility functions for Huckleberry MCP server."""

from datetime import datetime, timezone


def iso_to_timestamp(iso_date: str, user_timezone=None) -> int:
    """Convert ISO date string (YYYY-MM-DD) to Unix timestamp.

    Args:
        iso_date: Date string in YYYY-MM-DD format
        user_timezone: ZoneInfo object. If provided, interprets date as midnight in this timezone.
                      Otherwise defaults to UTC.

    Returns:
        Unix timestamp in seconds
    """
    dt = datetime.fromisoformat(iso_date)

    # Apply timezone (user's local or UTC)
    if user_timezone is not None:
        dt = dt.replace(tzinfo=user_timezone)
    else:
        dt = dt.replace(tzinfo=timezone.utc)

    return int(dt.timestamp())


def iso_datetime_to_timestamp(iso_datetime: str, user_timezone=None) -> int:
    """Convert ISO datetime string to Unix timestamp (seconds).

    Args:
        iso_datetime: ISO datetime string (e.g., "2026-01-25T08:15:00" or "2026-01-25T08:15:00Z")
        user_timezone: ZoneInfo object representing user's timezone. If provided and iso_datetime
                       has no timezone, interprets the datetime as being in this timezone.

    Returns:
        Unix timestamp in seconds
    """
    dt = datetime.fromisoformat(iso_datetime.replace('Z', '+00:00'))

    # If no timezone specified in the input string, use user's configured timezone
    if dt.tzinfo is None:
        if user_timezone is not None:
            # Interpret as user's local time
            dt = dt.replace(tzinfo=user_timezone)
        else:
            # Fallback to UTC if no user timezone provided
            dt = dt.replace(tzinfo=timezone.utc)

    return int(dt.timestamp())


def timestamp_to_local_iso(timestamp: float, user_timezone=None) -> str:
    """Convert Unix timestamp to ISO string in user's local timezone.

    Args:
        timestamp: Unix timestamp in seconds
        user_timezone: ZoneInfo object representing user's timezone. If provided,
                       the returned ISO string will be in this timezone.

    Returns:
        ISO datetime string in user's local timezone (or UTC if no timezone provided)
    """
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    if user_timezone:
        dt = dt.astimezone(user_timezone)
    return dt.isoformat()
