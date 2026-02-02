"""Feeding tracking tools for Huckleberry MCP server.

Timer State Machine
-------------------
Feeding sessions follow this state machine: IDLE -> RUNNING <-> PAUSED -> COMPLETED/CANCELLED

Valid operations by state:
- start_breastfeeding: IDLE -> RUNNING (fails if session already active for this child)
- pause_feeding: RUNNING -> PAUSED (fails if not running)
- resume_feeding: PAUSED -> RUNNING (fails if not paused)
- switch_feeding_side: RUNNING/PAUSED -> same state (fails if no active session)
- complete_feeding: RUNNING/PAUSED -> saved to history (fails if no active session)
- cancel_feeding: RUNNING/PAUSED -> discarded (fails if no active session)

Only one feeding session can be active per child at a time.
"""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from ..auth import get_authenticated_api
from .children import validate_child_uid
from ..utils import iso_to_timestamp, iso_datetime_to_timestamp, timestamp_to_local_iso


async def log_bottle_feeding(
    child_uid: str,
    amount: float,
    bottle_type: str = "Formula",
    units: str = "oz",
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a bottle feeding session.

    Records a bottle feeding with the specified amount and content type. Supports
    retroactive logging by providing an optional timestamp.

    Args:
        child_uid: The child's unique identifier (from list_children)
        amount: Amount fed (in the specified units)
        bottle_type: What was fed - one of "Formula", "Breast Milk", or "Mixed"
        units: Measurement units - "oz" (ounces) or "ml" (milliliters)
        timestamp: When the feeding occurred in ISO format (e.g., "2026-01-30T14:30:00").
                   Defaults to current time if not provided.

    Returns:
        Dict with keys:
        - success (bool): True if feeding was logged
        - message (str): Human-readable confirmation
        - amount (float): Amount fed
        - units (str): Measurement units used
        - bottle_type (str): Type of feeding (Formula, Breast Milk, Mixed)
        - timestamp (str): Logged feeding time in local ISO format
        - interval_id (str): Unique identifier for this feeding record

    Raises:
        ValueError: If bottle_type or units are invalid, or amount is not positive
        Exception: When API fails
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Validate bottle_type
        valid_types = ["Formula", "Breast Milk", "Mixed"]
        if bottle_type not in valid_types:
            raise ValueError(f"Invalid bottle_type '{bottle_type}'. Must be one of: {', '.join(valid_types)}")

        # Validate units
        valid_units = ["oz", "ml"]
        if units not in valid_units:
            raise ValueError(f"Invalid units '{units}'. Must be one of: {', '.join(valid_units)}")

        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be a positive number")

        # Get user's timezone
        user_timezone = api._timezone

        # Determine feeding timestamp
        current_time = time.time()
        if timestamp is not None:
            feed_timestamp = iso_datetime_to_timestamp(timestamp, user_timezone)
        else:
            feed_timestamp = current_time

        # Access Firestore client directly (following library's internal pattern)
        client = api._get_firestore_client()
        feed_ref = client.collection("feed").document(child_uid)

        # Generate interval ID (format: timestamp-random, matching complete_feeding)
        interval_id = f"{int(current_time * 1000)}-{uuid.uuid4().hex[:20]}"

        # Create interval document for bottle feeding
        interval_data = {
            "mode": "bottle",
            "start": feed_timestamp,
            "amount": amount,
            "units": units,
            "bottleType": bottle_type,
            "lastUpdated": current_time,
            "offset": api._get_timezone_offset_minutes(),
            "end_offset": api._get_timezone_offset_minutes(),
        }

        # Write to intervals subcollection
        feed_ref.collection("intervals").document(interval_id).set(interval_data)

        # Update prefs.lastBottle (matching pattern from other feeding types)
        last_bottle_data = {
            "mode": "bottle",
            "start": feed_timestamp,
            "amount": amount,
            "units": units,
            "bottleType": bottle_type,
            "offset": api._get_timezone_offset_minutes(),
        }

        feed_ref.update({
            "prefs.lastBottle": last_bottle_data,
            "prefs.timestamp": {"seconds": current_time},
            "prefs.local_timestamp": current_time,
        })

        return {
            "success": True,
            "message": f"Bottle feeding logged: {amount}{units} of {bottle_type} for child {child_uid}",
            "amount": amount,
            "units": units,
            "bottle_type": bottle_type,
            "timestamp": timestamp_to_local_iso(feed_timestamp, user_timezone),
            "interval_id": interval_id
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to log bottle feeding: {str(e)}")


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

    Useful for retroactive logging or importing past feeding data. Does not
    require an active timer session.

    Args:
        child_uid: The child's unique identifier (from list_children)
        start_time: Feeding start time in ISO format (e.g., "2026-01-30T14:30:00" or "2026-01-30T14:30:00Z")
        left_duration_minutes: Duration on left breast in minutes (optional)
        right_duration_minutes: Duration on right breast in minutes (optional)
        end_time: Feeding end time in ISO format (optional, alternative to specifying durations)
        last_side: Which side finished on ("left" or "right"). Required if using end_time, optional otherwise.

    Returns:
        Dict with keys:
        - success (bool): True if feeding was logged
        - message (str): Human-readable confirmation
        - start_time (str): Logged start time in local ISO format
        - left_duration_minutes (int): Duration on left breast
        - right_duration_minutes (int): Duration on right breast
        - total_duration_minutes (int): Combined duration from both sides
        - last_side (str): Which side finished on ("left" or "right")
        - interval_id (str): Unique identifier for this feeding record

    Raises:
        ValueError: If invalid combination of parameters provided (e.g., both end_time and durations)
        Exception: When API fails
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

        return {
            "success": True,
            "message": f"Breastfeeding logged for child {child_uid}",
            "start_time": timestamp_to_local_iso(start_timestamp, user_timezone),
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

    Starts the feeding timer on the specified breast. Only one feeding session
    can be active per child at a time.

    Args:
        child_uid: The child's unique identifier (from list_children)
        side: Which side to start on ("left" or "right")

    Returns:
        Dict with keys:
        - success (bool): True if session started
        - message (str): Human-readable confirmation
        - side (str): Which side feeding started on ("left" or "right")
        - timestamp (str): Session start time in local ISO format

    Raises:
        ValueError: If side is not "left" or "right", or child_uid is invalid
        Exception: If a feeding session is already active for this child, or API fails
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
            "timestamp": timestamp_to_local_iso(time.time(), api._timezone)
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to start breastfeeding session: {str(e)}")



async def pause_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Pause an active feeding tracking session.

    Args:
        child_uid: The child's unique identifier (from list_children)

    Returns:
        Dict with keys:
        - success (bool): True if session paused
        - message (str): Human-readable confirmation
        - timestamp (str): Pause time in local ISO format

    Raises:
        ValueError: If child_uid is invalid
        Exception: If no active (running) feeding session exists, or API fails

    Precondition:
        A feeding session must be active and running (started via start_breastfeeding, not paused).
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Pause feeding timer
        api.pause_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking paused for child {child_uid}",
            "timestamp": timestamp_to_local_iso(time.time(), api._timezone)
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to pause feeding session: {str(e)}")



async def resume_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Resume a paused feeding tracking session.

    Args:
        child_uid: The child's unique identifier (from list_children)

    Returns:
        Dict with keys:
        - success (bool): True if session resumed
        - message (str): Human-readable confirmation
        - timestamp (str): Resume time in local ISO format

    Raises:
        ValueError: If child_uid is invalid
        Exception: If no paused feeding session exists, or API fails

    Precondition:
        A feeding session must be paused (via pause_feeding).
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Resume feeding timer
        api.resume_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking resumed for child {child_uid}",
            "timestamp": timestamp_to_local_iso(time.time(), api._timezone)
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to resume feeding session: {str(e)}")



async def switch_feeding_side(child_uid: str) -> Dict[str, Any]:
    """
    Switch between left and right breast during breastfeeding.

    Toggles from left to right or right to left. The timer continues running
    on the new side.

    Args:
        child_uid: The child's unique identifier (from list_children)

    Returns:
        Dict with keys:
        - success (bool): True if side switched
        - message (str): Human-readable confirmation
        - timestamp (str): Switch time in local ISO format

    Raises:
        ValueError: If child_uid is invalid
        Exception: If no active feeding session exists (running or paused), or API fails

    Precondition:
        A feeding session must be active (running or paused).
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Switch feeding side
        api.switch_feeding_side(child_uid)

        return {
            "success": True,
            "message": "Switched feeding side",
            "timestamp": timestamp_to_local_iso(time.time(), api._timezone)
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to switch feeding side: {str(e)}")



async def complete_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Complete and save a feeding tracking session.

    Ends the active feeding session and saves it to the child's feeding history.

    Args:
        child_uid: The child's unique identifier (from list_children)

    Returns:
        Dict with keys:
        - success (bool): True if session completed and saved
        - message (str): Human-readable confirmation
        - timestamp (str): Completion time in local ISO format

    Raises:
        ValueError: If child_uid is invalid
        Exception: If no active feeding session exists (running or paused), or API fails

    Precondition:
        A feeding session must be active (running or paused).
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Complete feeding timer
        api.complete_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking completed and saved for child {child_uid}",
            "timestamp": timestamp_to_local_iso(time.time(), api._timezone)
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to complete feeding session: {str(e)}")



async def cancel_feeding(child_uid: str) -> Dict[str, Any]:
    """
    Cancel and discard a feeding tracking session.

    Ends the active feeding session without saving it. The session data is discarded.

    Args:
        child_uid: The child's unique identifier (from list_children)

    Returns:
        Dict with keys:
        - success (bool): True if session cancelled
        - message (str): Human-readable confirmation
        - timestamp (str): Cancellation time in local ISO format

    Raises:
        ValueError: If child_uid is invalid
        Exception: If no active feeding session exists (running or paused), or API fails

    Precondition:
        A feeding session must be active (running or paused).
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        # Cancel feeding timer
        api.cancel_feeding(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking cancelled for child {child_uid}",
            "timestamp": timestamp_to_local_iso(time.time(), api._timezone)
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
        child_uid: The child's unique identifier (from list_children)
        start_date: Start date in ISO format (YYYY-MM-DD), defaults to 7 days ago
        end_date: End date in ISO format (YYYY-MM-DD), defaults to today

    Returns:
        List of dicts, each containing:
        - start_time (str): Feeding start time in local ISO format
        - left_duration_minutes (int): Duration on left breast in minutes
        - right_duration_minutes (int): Duration on right breast in minutes
        - is_multi_entry (bool): True if this was a batch-logged entry

    Raises:
        Exception: When API fails
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
            # Convert timestamp to ISO format in user's timezone
            start_time = timestamp_to_local_iso(interval["start"], user_timezone)

            # Backend returns duration in seconds, convert to minutes
            left_mins = interval.get("leftDuration", 0) // 60
            right_mins = interval.get("rightDuration", 0) // 60

            result.append({
                "start_time": start_time,
                "left_duration_minutes": left_mins,
                "right_duration_minutes": right_mins,
                "is_multi_entry": interval.get("is_multi_entry", False),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get feeding history: {str(e)}")


def register_feeding_tools(mcp):
    """Register feeding tracking tools with FastMCP instance."""
    mcp.tool()(log_bottle_feeding)
    mcp.tool()(log_breastfeeding)
    mcp.tool()(start_breastfeeding)
    mcp.tool()(pause_feeding)
    mcp.tool()(resume_feeding)
    mcp.tool()(switch_feeding_side)
    mcp.tool()(complete_feeding)
    mcp.tool()(cancel_feeding)
    mcp.tool()(get_feeding_history)
