"""Sleep tracking tools for Huckleberry MCP server."""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from ..auth import get_authenticated_api
from .children import validate_child_uid


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


async def log_sleep(
    child_uid: str,
    start_time: str,
    end_time: Optional[str] = None,
    duration_minutes: Optional[int] = None
) -> Dict[str, Any]:
    """
    Directly log a completed sleep session without using the timer.
    Useful for retroactive logging or importing sleep data.

    Args:
        child_uid: The child's unique identifier
        start_time: Sleep start time in ISO format (e.g., "2026-01-30T14:30:00" or "2026-01-30T14:30:00Z")
        end_time: Sleep end time in ISO format (optional if duration_minutes provided)
        duration_minutes: Sleep duration in minutes (optional if end_time provided)

    Returns:
        Status message confirming sleep logged with details

    Raises:
        ValueError: If neither end_time nor duration_minutes is provided, or if both are provided
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Validate inputs
        if end_time is None and duration_minutes is None:
            raise ValueError("Either end_time or duration_minutes must be provided")
        if end_time is not None and duration_minutes is not None:
            raise ValueError("Provide either end_time or duration_minutes, not both")

        # Get user's timezone from API for proper timestamp conversion
        user_timezone = api._timezone

        # Convert start time to timestamp (using user's timezone for naive datetimes)
        start_timestamp = iso_datetime_to_timestamp(start_time, user_timezone)

        # Calculate duration
        if duration_minutes is not None:
            duration_sec = duration_minutes * 60
            end_timestamp = start_timestamp + duration_sec
        else:
            end_timestamp = iso_datetime_to_timestamp(end_time, user_timezone)
            duration_sec = end_timestamp - start_timestamp

            if duration_sec <= 0:
                raise ValueError("end_time must be after start_time")

        # Access Firestore client directly (following library's internal pattern)
        client = api._get_firestore_client()
        sleep_ref = client.collection("sleep").document(child_uid)

        # Generate interval ID
        interval_id = uuid.uuid4().hex[:16]

        # Create interval document (matching complete_sleep structure)
        interval_data = {
            "_id": interval_id,
            "start": start_timestamp,
            "duration": duration_sec,
            "offset": api._get_timezone_offset_minutes(),
            "end_offset": api._get_timezone_offset_minutes(),
            "details": {
                "startSleepCondition": {
                    "happy": False,
                    "longTimeToFallAsleep": False,
                    "10-20_minutes": False,
                    "upset": False,
                    "under_10_minutes": False,
                },
                "sleepLocations": {
                    "car": False,
                    "nursing": False,
                    "wornOrHeld": False,
                    "stroller": False,
                    "coSleep": False,
                    "nextToCarer": False,
                    "onOwnInBed": False,
                    "bottle": False,
                    "swing": False,
                },
                "endSleepCondition": {
                    "happy": False,
                    "wokeUpChild": False,
                    "upset": False,
                },
            },
            "lastUpdated": time.time(),
        }

        # Write to intervals subcollection
        sleep_ref.collection("intervals").document(interval_id).set(interval_data)

        # Update prefs.lastSleep (matching complete_sleep behavior)
        current_time = time.time()
        last_sleep_data = {
            "start": start_timestamp,
            "duration": duration_sec,
            "offset": api._get_timezone_offset_minutes(),
        }

        sleep_ref.update({
            "prefs.lastSleep": last_sleep_data,
            "prefs.timestamp": {"seconds": current_time},
            "prefs.local_timestamp": current_time,
        })

        # Convert timestamps for response
        start_dt = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)
        end_dt = datetime.fromtimestamp(end_timestamp, tz=timezone.utc)

        return {
            "success": True,
            "message": f"Sleep logged for child {child_uid}",
            "start_time": start_dt.isoformat(),
            "end_time": end_dt.isoformat(),
            "duration_minutes": duration_sec // 60,
            "interval_id": interval_id
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to log sleep: {str(e)}")


async def start_sleep(child_uid: str) -> Dict[str, Any]:
    """
    Begin a sleep tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming sleep session started
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Start sleep timer
        api.start_sleep(child_uid)

        return {
            "success": True,
            "message": f"Sleep tracking started for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to start sleep session: {str(e)}")


async def pause_sleep(child_uid: str) -> Dict[str, Any]:
    """
    Pause an active sleep tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming sleep session paused
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Pause sleep timer
        api.pause_sleep(child_uid)

        return {
            "success": True,
            "message": f"Sleep tracking paused for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to pause sleep session: {str(e)}")


async def resume_sleep(child_uid: str) -> Dict[str, Any]:
    """
    Resume a paused sleep tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming sleep session resumed
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Resume sleep timer
        api.resume_sleep(child_uid)

        return {
            "success": True,
            "message": f"Sleep tracking resumed for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to resume sleep session: {str(e)}")


async def complete_sleep(child_uid: str) -> Dict[str, Any]:
    """
    Complete and save a sleep tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming sleep session completed
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Complete sleep timer
        api.complete_sleep(child_uid)

        return {
            "success": True,
            "message": f"Sleep tracking completed and saved for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to complete sleep session: {str(e)}")


async def cancel_sleep(child_uid: str) -> Dict[str, Any]:
    """
    Cancel and discard a sleep tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming sleep session cancelled
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Cancel sleep timer
        api.cancel_sleep(child_uid)

        return {
            "success": True,
            "message": f"Sleep tracking cancelled for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to cancel sleep session: {str(e)}")


async def get_sleep_history(
    child_uid: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get sleep history for a child.

    Args:
        child_uid: The child's unique identifier
        start_date: Start date in ISO format (YYYY-MM-DD), optional
        end_date: End date in ISO format (YYYY-MM-DD), optional

    Returns:
        List of sleep events with start time, end time, and duration
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Get user's timezone for proper date interpretation
        user_timezone = api._timezone

        # Default to last 7 days if no dates provided
        if not start_date:
            start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
        else:
            start_timestamp = iso_to_timestamp(start_date, user_timezone)

        if not end_date:
            end_timestamp = int(datetime.now(timezone.utc).timestamp())
        else:
            end_timestamp = iso_to_timestamp(end_date, user_timezone)

        # Use get_sleep_intervals which returns list of dicts with 'start', 'end', 'duration'
        intervals = api.get_sleep_intervals(child_uid, start_timestamp, end_timestamp)

        result = []
        for interval in intervals:
            # Convert timestamps to ISO format
            start_time = datetime.fromtimestamp(interval["start"], tz=timezone.utc).isoformat()
            end_time = datetime.fromtimestamp(interval["end"], tz=timezone.utc).isoformat() if "end" in interval else None

            result.append({
                "start_time": start_time,
                "end_time": end_time,
                "duration_minutes": interval.get("duration", 0),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get sleep history: {str(e)}")
