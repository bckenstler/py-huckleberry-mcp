"""Diaper tracking tools for Huckleberry MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from ..auth import get_authenticated_api
from .children import validate_child_uid


def iso_to_timestamp(iso_date: str) -> int:
    """Convert ISO date string (YYYY-MM-DD) to Unix timestamp."""
    dt = datetime.fromisoformat(iso_date).replace(tzinfo=timezone.utc)
    return int(dt.timestamp())


async def log_diaper(
    child_uid: str,
    mode: str = "both",
    pee_amount: Optional[str] = None,
    poo_amount: Optional[str] = None,
    color: Optional[str] = None,
    consistency: Optional[str] = None,
    diaper_rash: bool = False,
    notes: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log a diaper change.

    Args:
        child_uid: The child's unique identifier
        mode: Diaper mode ("pee", "poo", "both", "dry")
        pee_amount: Pee amount ("little", "medium", "big"), optional
        poo_amount: Poo amount ("little", "medium", "big"), optional
        color: Color of poo if present ("yellow", "brown", "black", "green", "red", "gray")
        consistency: Consistency of poo ("solid", "loose", "runny", "mucousy", "hard", "pebbles", "diarrhea")
        diaper_rash: Whether baby has diaper rash
        notes: Optional notes about this diaper change

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

        # Validate amounts if provided
        valid_amounts = ["little", "medium", "big"]
        if pee_amount and pee_amount not in valid_amounts:
            raise ValueError(
                f"Invalid pee_amount '{pee_amount}'. Must be one of: {', '.join(valid_amounts)}"
            )
        if poo_amount and poo_amount not in valid_amounts:
            raise ValueError(
                f"Invalid poo_amount '{poo_amount}'. Must be one of: {', '.join(valid_amounts)}"
            )

        # Validate color if provided
        if color:
            valid_colors = ["yellow", "brown", "black", "green", "red", "gray"]
            if color not in valid_colors:
                raise ValueError(
                    f"Invalid color '{color}'. Must be one of: {', '.join(valid_colors)}"
                )

        # Validate consistency if provided
        if consistency:
            valid_consistencies = ["solid", "loose", "runny", "mucousy", "hard", "pebbles", "diarrhea"]
            if consistency not in valid_consistencies:
                raise ValueError(
                    f"Invalid consistency '{consistency}'. Must be one of: {', '.join(valid_consistencies)}"
                )

        api = await get_authenticated_api()

        api.log_diaper(
            child_uid,
            mode=mode,
            pee_amount=pee_amount,
            poo_amount=poo_amount,
            color=color,
            consistency=consistency,
            diaper_rash=diaper_rash,
            notes=notes
        )

        message_parts = [f"Logged diaper change ({mode})"]
        if color:
            message_parts.append(f"color: {color}")
        if consistency:
            message_parts.append(f"consistency: {consistency}")

        return {
            "success": True,
            "message": f"{', '.join(message_parts)} for child {child_uid}",
            "mode": mode,
            "color": color,
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

        # Default to last 7 days if no dates provided
        if not start_date:
            start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=7)).timestamp())
        else:
            start_timestamp = iso_to_timestamp(start_date)

        if not end_date:
            end_timestamp = int(datetime.now(timezone.utc).timestamp())
        else:
            end_timestamp = iso_to_timestamp(end_date)

        # Use get_diaper_intervals
        intervals = api.get_diaper_intervals(child_uid, start_timestamp, end_timestamp)

        result = []
        for interval in intervals:
            # Convert timestamp to ISO format
            timestamp = datetime.fromtimestamp(interval["start"], tz=timezone.utc).isoformat()

            result.append({
                "timestamp": timestamp,
                "mode": interval.get("mode"),
                "color": interval.get("color"),
                "consistency": interval.get("consistency"),
                "notes": interval.get("notes"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get diaper history: {str(e)}")
