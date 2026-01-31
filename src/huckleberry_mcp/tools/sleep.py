"""Sleep tracking tools for Huckleberry MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from ..auth import get_authenticated_api
from .children import validate_child_uid


def iso_to_timestamp(iso_date: str) -> int:
    """Convert ISO date string (YYYY-MM-DD) to Unix timestamp."""
    dt = datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


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

        # Default to last 7 days if no dates provided
        if not start_date:
            start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
        else:
            start_timestamp = iso_to_timestamp(start_date)

        if not end_date:
            end_timestamp = int(datetime.now(timezone.utc).timestamp())
        else:
            end_timestamp = iso_to_timestamp(end_date)

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
