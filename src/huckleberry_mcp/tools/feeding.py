"""Feeding tracking tools for Huckleberry MCP server."""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from ..auth import get_authenticated_api
from .children import validate_child_uid
from ..utils import iso_to_timestamp, iso_datetime_to_timestamp


async def log_breastfeeding(
    child_uid: str,
    start_time: str,
    left_duration_minutes: Optional[int] = None,
    right_duration_minutes: Optional[int] = None,
    end_time: Optional[str] = None,
    last_side: Optional[str] = None
) -> Dict[str, Any]:
    """
    Directly log a completed breastfeeding session without using the timer.
    Useful for retroactive logging or importing past feeding data.

    Args:
        child_uid: The child's unique identifier
        start_time: Feeding start time in ISO format (e.g., "2026-01-30T14:30:00" or "2026-01-30T14:30:00Z")
        left_duration_minutes: Duration on left breast in minutes (optional)
        right_duration_minutes: Duration on right breast in minutes (optional)
        end_time: Feeding end time in ISO format (optional, alternative to specifying durations)
        last_side: Which side finished on ("left" or "right"). Required if using end_time, optional otherwise.

    Returns:
        Status message confirming feeding logged with details

    Raises:
        ValueError: If invalid combination of parameters provided
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Validate side if provided
        if last_side and last_side not in ["left", "right"]:
            raise ValueError("Invalid last_side. Must be 'left' or 'right'")

        # Get user's timezone
        user_timezone = api._timezone

        # Convert start time to timestamp
        start_timestamp = iso_datetime_to_timestamp(start_time, user_timezone)

        # Determine durations
        if end_time is not None:
            # Calculate total duration from end_time
            if left_duration_minutes is not None or right_duration_minutes is not None:
                raise ValueError("When using end_time, do not specify left_duration_minutes or right_duration_minutes")

            if last_side is None:
                raise ValueError("When using end_time, last_side is required to determine which breast to assign duration to")

            end_timestamp = iso_datetime_to_timestamp(end_time, user_timezone)
            total_duration_sec = end_timestamp - start_timestamp

            if total_duration_sec <= 0:
                raise ValueError("end_time must be after start_time")

            total_duration_min = total_duration_sec / 60

            # Assign all duration to the specified side
            if last_side == "left":
                left_duration = total_duration_min
                right_duration = 0.0
            else:
                left_duration = 0.0
                right_duration = total_duration_min
        else:
            # Use provided durations
            if left_duration_minutes is None and right_duration_minutes is None:
                raise ValueError("Must provide either end_time OR at least one of left_duration_minutes/right_duration_minutes")

            left_duration = float(left_duration_minutes) if left_duration_minutes is not None else 0.0
            right_duration = float(right_duration_minutes) if right_duration_minutes is not None else 0.0

            # Determine last_side if not provided
            if last_side is None:
                # Default to whichever side has more duration
                last_side = "right" if right_duration >= left_duration else "left"

        # Access Firestore client directly (following library's internal pattern)
        client = api._get_firestore_client()
        feed_ref = client.collection("feed").document(child_uid)

        # Generate interval ID (format: timestamp-random, matching complete_feeding)
        current_time = time.time()
        interval_id = f"{int(current_time * 1000)}-{uuid.uuid4().hex[:20]}"

        # Create interval document (matching complete_feeding structure)
        interval_data = {
            "mode": "breast",
            "start": start_timestamp,
            "lastSide": last_side,
            "lastUpdated": current_time,
            "leftDuration": left_duration,
            "rightDuration": right_duration,
            "offset": api._get_timezone_offset_minutes(),
            "end_offset": api._get_timezone_offset_minutes(),
        }

        # Write to intervals subcollection
        feed_ref.collection("intervals").document(interval_id).set(interval_data)

        # Update prefs.lastNursing and prefs.lastSide (matching complete_feeding behavior)
        total_duration = left_duration + right_duration

        last_nursing_data = {
            "mode": "breast",
            "start": start_timestamp,
            "duration": total_duration,
            "leftDuration": left_duration,
            "rightDuration": right_duration,
            "offset": api._get_timezone_offset_minutes(),
        }

        last_side_data = {
            "start": start_timestamp,
            "lastSide": last_side,
        }

        feed_ref.update({
            "prefs.lastNursing": last_nursing_data,
            "prefs.lastSide": last_side_data,
            "prefs.timestamp": {"seconds": current_time},
            "prefs.local_timestamp": current_time,
        })

        # Convert timestamp for response
        start_dt = datetime.fromtimestamp(start_timestamp, tz=timezone.utc)

        return {
            "success": True,
            "message": f"Breastfeeding logged for child {child_uid}",
            "start_time": start_dt.isoformat(),
            "left_duration_minutes": int(left_duration),
            "right_duration_minutes": int(right_duration),
            "total_duration_minutes": int(total_duration),
            "last_side": last_side,
            "interval_id": interval_id
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to log breastfeeding: {str(e)}")


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


def register_feeding_tools(mcp):
    """Register feeding tracking tools with FastMCP instance."""
    mcp.tool()(log_breastfeeding)
    mcp.tool()(start_breastfeeding)
    mcp.tool()(pause_feeding)
    mcp.tool()(resume_feeding)
    mcp.tool()(switch_feeding_side)
    mcp.tool()(complete_feeding)
    mcp.tool()(cancel_feeding)
    mcp.tool()(get_feeding_history)
