"""Growth tracking tools for Huckleberry MCP server."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from ..auth import get_authenticated_api
from .children import validate_child_uid


async def log_growth(
    child_uid: str,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    head_circumference: Optional[float] = None,
    units: str = "imperial"
) -> Dict[str, Any]:
    """
    Log growth measurements.

    Args:
        child_uid: The child's unique identifier
        weight: Weight measurement (lbs if imperial, kg if metric)
        height: Height measurement (inches if imperial, cm if metric)
        head_circumference: Head circumference (inches if imperial, cm if metric)
        units: Measurement system ("imperial" or "metric")

    Returns:
        Status message confirming growth measurements logged
    """
    try:
        await validate_child_uid(child_uid)

        if units not in ["imperial", "metric"]:
            raise ValueError(
                f"Invalid units '{units}'. Must be 'imperial' or 'metric'."
            )

        if not any([weight, height, head_circumference]):
            raise ValueError(
                "At least one measurement (weight, height, or head_circumference) must be provided."
            )

        api = await get_authenticated_api()

        await api.log_growth_measurement(
            child_uid,
            weight=weight,
            height=height,
            head_circumference=head_circumference,
            units=units
        )

        measurements = []
        if weight is not None:
            unit = "lbs" if units == "imperial" else "kg"
            measurements.append(f"weight: {weight}{unit}")
        if height is not None:
            unit = "in" if units == "imperial" else "cm"
            measurements.append(f"height: {height}{unit}")
        if head_circumference is not None:
            unit = "in" if units == "imperial" else "cm"
            measurements.append(f"head: {head_circumference}{unit}")

        return {
            "success": True,
            "message": f"Logged growth measurements ({', '.join(measurements)}) for child {child_uid}",
            "weight": weight,
            "height": height,
            "head_circumference": head_circumference,
            "units": units,
            "timestamp": datetime.now().isoformat()
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to log growth measurements: {str(e)}")


async def get_latest_growth(child_uid: str) -> Dict[str, Any]:
    """
    Get the latest growth measurements for a child.

    Args:
        child_uid: The child's unique identifier

    Returns:
        Latest growth measurements with timestamp
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        latest = await api.get_latest_growth_measurement(child_uid)

        if not latest:
            return {
                "message": "No growth measurements found for this child"
            }

        return {
            "timestamp": latest.get("timestamp"),
            "weight": latest.get("weight"),
            "height": latest.get("height"),
            "head_circumference": latest.get("headCircumference"),
            "units": latest.get("units"),
            "age_days": latest.get("ageDays"),
        }

    except Exception as e:
        raise Exception(f"Failed to get latest growth measurements: {str(e)}")


async def get_growth_history(
    child_uid: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Get growth measurement history for a child.

    Args:
        child_uid: The child's unique identifier
        start_date: Start date in ISO format (YYYY-MM-DD), optional
        end_date: End date in ISO format (YYYY-MM-DD), optional

    Returns:
        List of growth measurements with details
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        history = await api.get_growth_history(
            child_uid,
            start_date=start_date,
            end_date=end_date
        )

        result = []
        for event in history:
            result.append({
                "timestamp": event.get("timestamp"),
                "weight": event.get("weight"),
                "height": event.get("height"),
                "head_circumference": event.get("headCircumference"),
                "units": event.get("units"),
                "age_days": event.get("ageDays"),
                "notes": event.get("notes"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get growth history: {str(e)}")
