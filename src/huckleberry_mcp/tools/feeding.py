"""Feeding tracking tools for Huckleberry MCP server."""

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


async def start_breastfeeding(child_uid: str, side: str) -> Dict[str, Any]:
    """
    Begin a breastfeeding tracking session.

    Args:
        child_uid: The child's unique identifier
        side: Which side to start on ("left" or "right")

    Returns:
        Status message confirming breastfeeding session started
    """
    try:
        await validate_child_uid(child_uid)

        if side.lower() not in ["left", "right"]:
            raise ValueError(
                f"Invalid side '{side}'. Must be 'left' or 'right'."
            )

        api = await get_authenticated_api()

        # Start feeding timer
        api.start_feeding(child_uid, side=side.lower())

        return {
            "success": True,
            "message": f"Breastfeeding started on {side} side for child {child_uid}",
            "side": side.lower(),
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to start breastfeeding session: {str(e)}")


async def pause_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Pause an active feeding tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming feeding session paused
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Pause feeding timer
        api.pause_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking paused for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to pause feeding session: {str(e)}")


async def resume_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Resume a paused feeding tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming feeding session resumed
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Resume feeding timer
        api.resume_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking resumed for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to resume feeding session: {str(e)}")


async def switch_feeding_side(child_uid: str) -> Dict[str, Any]:
    """
    Switch between left and right breast during breastfeeding.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming side switched
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Switch feeding side
        api.switch_feeding_side(child_uid)

        return {
            "success": True,
            "message": "Switched feeding side",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to switch feeding side: {str(e)}")


async def complete_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Complete and save a feeding tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming feeding session completed
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Complete feeding timer
        api.complete_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking completed and saved for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to complete feeding session: {str(e)}")


async def cancel_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Cancel and discard a feeding tracking session.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Status message confirming feeding session cancelled
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Cancel feeding timer
        api.cancel_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking cancelled for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to cancel feeding session: {str(e)}")




async def get_feeding_history(
    child_uid: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get feeding history for a child.

    Args:
        child_uid: The child's unique identifier
        start_date: Start date in ISO format (YYYY-MM-DD), optional
        end_date: End date in ISO format (YYYY-MM-DD), optional

    Returns:
        List of feeding events with details
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

        # Use get_feed_intervals which returns list of dicts with 'start', 'leftDuration', 'rightDuration'
        intervals = api.get_feed_intervals(child_uid, start_timestamp, end_timestamp)

        result = []
        for interval in intervals:
            # Convert timestamp to ISO format
            start_time = datetime.fromtimestamp(interval["start"], tz=timezone.utc).isoformat()

            result.append({
                "start_time": start_time,
                "left_duration_minutes": interval.get("leftDuration", 0),
                "right_duration_minutes": interval.get("rightDuration", 0),
                "is_multi_entry": interval.get("is_multi_entry", False),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get feeding history: {str(e)}")
