"""Feeding tracking tools for Huckleberry MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from ..auth import get_authenticated_api
from .children import validate_child_uid


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

        # Check if there's already an active feeding session
        status = await api.get_feeding_timer_status(child_uid)
        if status and status.get("isActive"):
            raise ValueError(
                "Feeding session already active. Use pause_feeding, complete_feeding, "
                "or cancel_feeding to manage the existing session."
            )

        await api.start_breastfeeding_timer(child_uid, side=side.lower())

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

        # Check if there's an active feeding session
        status = await api.get_feeding_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active feeding session to pause. Use start_breastfeeding to begin tracking."
            )

        if status.get("isPaused"):
            raise ValueError(
                "Feeding session is already paused. Use resume_feeding to continue."
            )

        await api.pause_feeding_timer(child_uid)

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

        # Check if there's a paused feeding session
        status = await api.get_feeding_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active feeding session to resume. Use start_breastfeeding to begin tracking."
            )

        if not status.get("isPaused"):
            raise ValueError(
                "Feeding session is not paused. Use pause_feeding to pause it first."
            )

        await api.resume_feeding_timer(child_uid)

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

        # Check if there's an active feeding session
        status = await api.get_feeding_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active feeding session. Use start_breastfeeding to begin tracking."
            )

        await api.switch_breastfeeding_side(child_uid)

        current_side = status.get("currentSide", "unknown")
        new_side = "right" if current_side == "left" else "left"

        return {
            "success": True,
            "message": f"Switched from {current_side} to {new_side} side",
            "new_side": new_side,
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

        # Check if there's an active feeding session
        status = await api.get_feeding_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active feeding session to complete. Use start_breastfeeding to begin tracking."
            )

        await api.complete_feeding_timer(child_uid)

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

        # Check if there's an active feeding session
        status = await api.get_feeding_timer_status(child_uid)
        if not status or not status.get("isActive"):
            raise ValueError(
                "No active feeding session to cancel."
            )

        await api.cancel_feeding_timer(child_uid)

        return {
            "success": True,
            "message": f"Feeding tracking cancelled for child {child_uid}",
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to cancel feeding session: {str(e)}")


async def log_bottle_feeding(
    child_uid: str,
    amount: float,
    bottle_type: str = "formula",
    units: str = "oz"
) -> Dict[str, Any]:
    """
    Log a bottle feeding without using a timer.

    Args:
        child_uid: The child's unique identifier
        amount: Amount fed
        bottle_type: Type of bottle feeding ("formula", "breast_milk", "mixed")
        units: Units of measurement ("oz" or "ml")

    Returns:
        Status message confirming bottle feeding logged
    """
    try:
        await validate_child_uid(child_uid)

        if bottle_type not in ["formula", "breast_milk", "mixed"]:
            raise ValueError(
                f"Invalid bottle_type '{bottle_type}'. "
                "Must be 'formula', 'breast_milk', or 'mixed'."
            )

        if units not in ["oz", "ml"]:
            raise ValueError(
                f"Invalid units '{units}'. Must be 'oz' or 'ml'."
            )

        api = await get_authenticated_api()

        await api.log_bottle_feeding(
            child_uid,
            amount=amount,
            bottle_type=bottle_type,
            units=units
        )

        return {
            "success": True,
            "message": f"Logged {amount}{units} {bottle_type} bottle feeding for child {child_uid}",
            "amount": amount,
            "units": units,
            "bottle_type": bottle_type,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to log bottle feeding: {str(e)}")


async def get_feeding_status(child_uid: str) -> Dict[str, Any]:
    """
    Get the current status of feeding tracking for a child.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Current feeding timer status including active state and duration
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        status = await api.get_feeding_timer_status(child_uid)

        if not status or not status.get("isActive"):
            return {
                "is_active": False,
                "message": "No active feeding session"
            }

        return {
            "is_active": True,
            "is_paused": status.get("isPaused", False),
            "current_side": status.get("currentSide"),
            "start_time": status.get("startTime"),
            "elapsed_seconds": status.get("elapsedSeconds", 0),
            "message": "Feeding session active"
        }

    except Exception as e:
        raise Exception(f"Failed to get feeding status: {str(e)}")


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

        history = await api.get_feeding_history(
            child_uid,
            start_date=start_date,
            end_date=end_date
        )

        result = []
        for event in history:
            result.append({
                "start_time": event.get("startTime"),
                "end_time": event.get("endTime"),
                "type": event.get("type"),
                "amount": event.get("amount"),
                "units": event.get("units"),
                "sides": event.get("sides"),
                "duration_minutes": event.get("durationMinutes"),
                "notes": event.get("notes"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get feeding history: {str(e)}")
