"""Sleep tracking tools for Huckleberry MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from ..auth import get_authenticated_api
from .children import validate_child_uid


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

        # Check if there's already an active sleep session
        status = await api.get_sleep_timer_status(child_uid)
        if status and status.get("isActive"):
            raise ValueError(
                "Sleep session already active. Use pause_sleep, complete_sleep, "
                "or cancel_sleep to manage the existing session."
            )

        await api.start_sleep_timer(child_uid)

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

        # Check if there's an active sleep session
        status = await api.get_sleep_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active sleep session to pause. Use start_sleep to begin tracking."
            )

        if status.get("isPaused"):
            raise ValueError(
                "Sleep session is already paused. Use resume_sleep to continue."
            )

        await api.pause_sleep_timer(child_uid)

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

        # Check if there's a paused sleep session
        status = await api.get_sleep_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active sleep session to resume. Use start_sleep to begin tracking."
            )

        if not status.get("isPaused"):
            raise ValueError(
                "Sleep session is not paused. Use pause_sleep to pause it first."
            )

        await api.resume_sleep_timer(child_uid)

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

        # Check if there's an active sleep session
        status = await api.get_sleep_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active sleep session to complete. Use start_sleep to begin tracking."
            )

        await api.complete_sleep_timer(child_uid)

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

        # Check if there's an active sleep session
        status = await api.get_sleep_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active sleep session to cancel."
            )

        await api.cancel_sleep_timer(child_uid)

        return {
            "success": True,
            "message": f"Sleep tracking cancelled for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to cancel sleep session: {str(e)}")


async def get_sleep_status(child_uid: str) -> Dict[str, Any]:
    """
    Get the current status of sleep tracking for a child.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Current sleep timer status including active state and duration
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        status = await api.get_sleep_timer_status(child_uid)

        if not status or not status.get("isActive"):
            return {
                "is_active": False,
                "message": "No active sleep session"
            }

        return {
            "is_active": True,
            "is_paused": status.get("isPaused", False),
            "start_time": status.get("startTime"),
            "elapsed_seconds": status.get("elapsedSeconds", 0),
            "message": "Sleep session active"
        }

    except Exception as e:
        raise Exception(f"Failed to get sleep status: {str(e)}")


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

        history = await api.get_sleep_history(
            child_uid,
            start_date=start_date,
            end_date=end_date
        )

        result = []
        for event in history:
            result.append({
                "start_time": event.get("startTime"),
                "end_time": event.get("endTime"),
                "duration_minutes": event.get("durationMinutes"),
                "notes": event.get("notes"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get sleep history: {str(e)}")
