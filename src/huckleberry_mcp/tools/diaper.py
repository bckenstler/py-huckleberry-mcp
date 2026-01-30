"""Diaper tracking tools for Huckleberry MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from ..auth import get_authenticated_api
from .children import validate_child_uid


async def log_diaper(
    child_uid: str,
    mode: str = "both",
    has_pee: bool = False,
    has_poo: bool = False,
    poo_color: Optional[str] = None,
    consistency: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a diaper change.

    Args:
        child_uid: The child's unique identifier
        mode: Diaper mode ("pee", "poo", "both", "dry")
        has_pee: Whether diaper had pee (deprecated, use mode instead)
        has_poo: Whether diaper had poo (deprecated, use mode instead)
        poo_color: Color of poo if present ("brown", "yellow", "green", "black")
        consistency: Consistency of poo if present ("soft", "firm", "watery", "hard")

    Returns:
        Status message confirming diaper logged
    """
    try:
        await validate_child_uid(child_uid)

        # Validate mode
        valid_modes = ["pee", "poo", "both", "dry"]
        if mode not in valid_modes:
            raise ValueError(
                f"Invalid mode '{mode}'. Must be one of: {', '.join(valid_modes)}"
            )

        # Validate poo_color if provided
        if poo_color:
            valid_colors = ["brown", "yellow", "green", "black"]
            if poo_color not in valid_colors:
                raise ValueError(
                    f"Invalid poo_color '{poo_color}'. "
                    f"Must be one of: {', '.join(valid_colors)}"
                )

        # Validate consistency if provided
        if consistency:
            valid_consistencies = ["soft", "firm", "watery", "hard"]
            if consistency not in valid_consistencies:
                raise ValueError(
                    f"Invalid consistency '{consistency}'. "
                    f"Must be one of: {', '.join(valid_consistencies)}"
                )

        api = await get_authenticated_api()

        await api.log_diaper_change(
            child_uid,
            mode=mode,
            poo_color=poo_color,
            consistency=consistency
        )

        message_parts = [f"Logged diaper change ({mode})"]
        if poo_color:
            message_parts.append(f"color: {poo_color}")
        if consistency:
            message_parts.append(f"consistency: {consistency}")

        return {
            "success": True,
            "message": f"{', '.join(message_parts)} for child {child_uid}",
            "mode": mode,
            "poo_color": poo_color,
            "consistency": consistency,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to log diaper change: {str(e)}")


async def get_diaper_history(
    child_uid: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get diaper change history for a child.

    Args:
        child_uid: The child's unique identifier
        start_date: Start date in ISO format (YYYY-MM-DD), optional
        end_date: End date in ISO format (YYYY-MM-DD), optional

    Returns:
        List of diaper change events with details
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        history = await api.get_diaper_history(
            child_uid,
            start_date=start_date,
            end_date=end_date
        )

        result = []
        for event in history:
            result.append({
                "timestamp": event.get("timestamp"),
                "mode": event.get("mode"),
                "has_pee": event.get("hasPee"),
                "has_poo": event.get("hasPoo"),
                "poo_color": event.get("pooColor"),
                "consistency": event.get("consistency"),
                "notes": event.get("notes"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get diaper history: {str(e)}")
