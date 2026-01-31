"""Growth tracking tools for Huckleberry MCP server."""

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


async def log_growth(
    child_uid: str,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    head: Optional[float] = None,
    units: str = "imperial"
) -> Dict[str, Any]:
    """
    Log growth measurements.

    Args:
        child_uid: The child's unique identifier
        weight: Weight measurement (lbs if imperial, kg if metric)
        height: Height measurement (inches if imperial, cm if metric)
        head: Head circumference (inches if imperial, cm if metric)
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

        if not any([weight, height, head]):
            raise ValueError(
                "At least one measurement (weight, height, or head) must be provided."
            )

        api = await get_authenticated_api()

        api.log_growth(
            child_uid,
            weight=weight,
            height=height,
            head=head,
            units=units
        )

        measurements = []
        if weight is not None:
            unit = "lbs" if units == "imperial" else "kg"
            measurements.append(f"weight: {weight}{unit}")
        if height is not None:
            unit = "in" if units == "imperial" else "cm"
            measurements.append(f"height: {height}{unit}")
        if head is not None:
            unit = "in" if units == "imperial" else "cm"
            measurements.append(f"head: {head}{unit}")

        return {
            "success": True,
            "message": f"Logged growth measurements ({', '.join(measurements)}) for child {child_uid}",
            "weight": weight,
            "height": height,
            "head": head,
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

        growth_data = api.get_growth_data(child_uid)

        if not growth_data.get("weight") and not growth_data.get("height") and not growth_data.get("head"):
            return {
                "message": "No growth measurements found for this child"
            }

        return {
            "weight": growth_data.get("weight"),
            "height": growth_data.get("height"),
            "head": growth_data.get("head"),
            "weight_units": growth_data.get("weight_units"),
            "height_units": growth_data.get("height_units"),
            "head_units": growth_data.get("head_units"),
            "timestamp": growth_data.get("timestamp_sec"),
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

        # Get user's timezone for proper date interpretation
        user_timezone = api._timezone

        # Default to last 30 days if no dates provided
        if not start_date:
            start_timestamp = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
        else:
            start_timestamp = iso_to_timestamp(start_date, user_timezone)

        if not end_date:
            end_timestamp = int(datetime.now(timezone.utc).timestamp())
        else:
            end_timestamp = iso_to_timestamp(end_date, user_timezone)

        # Use get_health_entries which returns growth/health measurements
        entries = api.get_health_entries(child_uid, start_timestamp, end_timestamp)

        result = []
        for entry in entries:
            # Convert timestamp to ISO format
            timestamp = datetime.fromtimestamp(entry["start"], tz=timezone.utc).isoformat()

            result.append({
                "timestamp": timestamp,
                "weight": entry.get("weight"),
                "height": entry.get("height"),
                "head": entry.get("head"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get growth history: {str(e)}")
