"""Growth tracking tools for Huckleberry MCP server."""

import time
import uuid
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone, timedelta
from ..auth import get_authenticated_api
from .children import validate_child_uid
from ..utils import iso_to_timestamp, iso_datetime_to_timestamp, timestamp_to_local_iso


async def log_growth(
    child_uid: str,
    weight: Optional[float] = None,
    height: Optional[float] = None,
    head: Optional[float] = None,
    units: str = "imperial",
    timestamp: Optional[str] = None
) -> Dict[str, Any]:
    """
    Log growth measurements.

    At least one measurement (weight, height, or head) must be provided.

    Args:
        child_uid: The child's unique identifier (from list_children)
        weight: Weight measurement (lbs if imperial, kg if metric) (optional)
        height: Height measurement (inches if imperial, cm if metric) (optional)
        head: Head circumference (inches if imperial, cm if metric) (optional)
        units: Measurement system - "imperial" or "metric" (default "imperial")
        timestamp: Optional timestamp in ISO format for retroactive logging. If not provided, uses current time.

    Returns:
        Dict with keys:
        - success (bool): True if measurements were logged
        - message (str): Human-readable confirmation with recorded values
        - weight (float | None): Logged weight value, None if not provided
        - height (float | None): Logged height value, None if not provided
        - head (float | None): Logged head circumference, None if not provided
        - units (str): Measurement system used ("imperial" or "metric")
        - timestamp (str): Logged time in local ISO format

    Raises:
        ValueError: If units is invalid or no measurements provided
        Exception: When API fails
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

        # Determine timestamp to use
        if timestamp:
            user_timezone = api._timezone
            measurement_time = iso_datetime_to_timestamp(timestamp, user_timezone)
        else:
            measurement_time = time.time()

        # Access Firestore client directly for custom timestamp support
        client = api._get_firestore_client()
        health_ref = client.collection("health").document(child_uid)

        # Create interval ID (timestamp in ms + random suffix)
        interval_timestamp_ms = int(measurement_time * 1000)
        interval_id = f"{interval_timestamp_ms}-{uuid.uuid4().hex[:20]}"

        # Build growth entry matching Huckleberry app structure
        growth_entry = {
            "_id": interval_id,
            "type": "health",
            "mode": "growth",
            "start": measurement_time,
            "lastUpdated": measurement_time,
            "offset": api._get_timezone_offset_minutes(),
            "isNight": False,
            "multientry_key": None,
        }

        # Add measurements with proper unit fields
        if units == "metric":
            if weight is not None:
                growth_entry["weight"] = float(weight)
                growth_entry["weightUnits"] = "kg"
            if height is not None:
                growth_entry["height"] = float(height)
                growth_entry["heightUnits"] = "cm"
            if head is not None:
                growth_entry["head"] = float(head)
                growth_entry["headUnits"] = "hcm"
        else:  # imperial
            if weight is not None:
                growth_entry["weight"] = float(weight)
                growth_entry["weightUnits"] = "lbs"
            if height is not None:
                growth_entry["height"] = float(height)
                growth_entry["heightUnits"] = "in"
            if head is not None:
                growth_entry["head"] = float(head)
                growth_entry["headUnits"] = "hin"

        # Create interval document in health/{child_uid}/data subcollection
        health_data_ref = health_ref.collection("data").document(interval_id)
        health_data_ref.set(growth_entry)

        # Update prefs.lastGrowthEntry and timestamps
        health_ref.update({
            "prefs.lastGrowthEntry": growth_entry,
            "prefs.timestamp": {"seconds": measurement_time},
            "prefs.local_timestamp": measurement_time,
        })

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

        # Get user's timezone for response
        user_timezone = api._timezone

        return {
            "success": True,
            "message": f"Logged growth measurements ({', '.join(measurements)}) for child {child_uid}",
            "weight": weight,
            "height": height,
            "head": head,
            "units": units,
            "timestamp": timestamp_to_local_iso(measurement_time, user_timezone)
        }

    except ValueError as e:
        raise
    except Exception as e:
        raise Exception(f"Failed to log growth measurements: {str(e)}")


async def get_latest_growth(child_uid: str) -> Dict[str, Any]:
    """
    Get the latest growth measurements for a child.

    Args:
        child_uid: The child's unique identifier (from list_children)

    Returns:
        Dict with keys (when measurements exist):
        - weight (float | None): Latest weight value
        - height (float | None): Latest height value
        - head (float | None): Latest head circumference
        - weight_units (str | None): Units for weight ("lbs" or "kg")
        - height_units (str | None): Units for height ("in" or "cm")
        - head_units (str | None): Units for head circumference
        - timestamp (str | None): Measurement time in local ISO format

        OR when no measurements exist:
        - message (str): "No growth measurements found for this child"

    Raises:
        Exception: When API fails
    """
    try:
        await validate_child_uid(child_uid)
        api = await get_authenticated_api()

        growth_data = api.get_growth_data(child_uid)

        if not growth_data.get("weight") and not growth_data.get("height") and not growth_data.get("head"):
            return {
                "message": "No growth measurements found for this child"
            }

        # Convert timestamp to user's timezone if available
        timestamp_sec = growth_data.get("timestamp_sec")
        timestamp_str = None
        if timestamp_sec:
            timestamp_str = timestamp_to_local_iso(timestamp_sec, api._timezone)

        return {
            "weight": growth_data.get("weight"),
            "height": growth_data.get("height"),
            "head": growth_data.get("head"),
            "weight_units": growth_data.get("weight_units"),
            "height_units": growth_data.get("height_units"),
            "head_units": growth_data.get("head_units"),
            "timestamp": timestamp_str,
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
        child_uid: The child's unique identifier (from list_children)
        start_date: Start date in ISO format (YYYY-MM-DD), defaults to 30 days ago
        end_date: End date in ISO format (YYYY-MM-DD), defaults to today

    Returns:
        List of dicts, each containing:
        - timestamp (str): Measurement time in local ISO format
        - weight (float | None): Weight value if recorded, None otherwise
        - height (float | None): Height value if recorded, None otherwise
        - head (float | None): Head circumference if recorded, None otherwise

    Raises:
        Exception: When API fails
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
            # Convert timestamp to ISO format in user's timezone
            timestamp = timestamp_to_local_iso(entry["start"], user_timezone)

            result.append({
                "timestamp": timestamp,
                "weight": entry.get("weight"),
                "height": entry.get("height"),
                "head": entry.get("head"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to get growth history: {str(e)}")


def register_growth_tools(mcp):
    """Register growth tracking tools with FastMCP instance."""
    mcp.tool()(log_growth)
    mcp.tool()(get_latest_growth)
    mcp.tool()(get_growth_history)
