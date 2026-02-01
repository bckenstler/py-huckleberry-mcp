"""Child management tools for Huckleberry MCP server."""

from typing import Any, Dict, List, Optional
from ..auth import get_authenticated_api


async def list_children() -> List[Dict[str, Any]]:
    """
    List all child profiles.

    Returns:
        List of children with uid, name, and birth_date.
    """
    try:
        api = await get_authenticated_api()
        children = api.get_children()

        result = []
        for child in children:
            result.append({
                "uid": child.get("uid"),
                "name": child.get("name"),
                "birth_date": child.get("birthDate"),
            })

        return result

    except Exception as e:
        raise Exception(f"Failed to list children: {str(e)}")


async def get_child_name(child_uid: str) -> Optional[str]:
    """
    Get a child's name from their UID.

    Args:
        child_uid: The child's unique identifier

    Returns:
        The child's name, or None if not found
    """
    try:
        api = await get_authenticated_api()
        children = api.get_children()

        for child in children:
            if child.get("uid") == child_uid:
                return child.get("name")

        return None

    except Exception as e:
        raise Exception(f"Failed to get child name: {str(e)}")


async def validate_child_uid(child_uid: str) -> bool:
    """
    Validate that a child_uid exists.

    Args:
        child_uid: The child's unique identifier

    Returns:
        True if valid, raises exception otherwise
    """
    try:
        api = await get_authenticated_api()
        children = api.get_children()

        valid_uids = [child.get("uid") for child in children]

        if child_uid not in valid_uids:
            raise ValueError(
                f"Invalid child_uid '{child_uid}'. "
                f"Valid UIDs: {', '.join(valid_uids)}"
            )

        return True

    except ValueError:
        raise
    except Exception as e:
        raise Exception(f"Failed to validate child_uid: {str(e)}")


def register_children_tools(mcp):
    """Register child management tools with FastMCP instance."""
    mcp.tool()(list_children)
    mcp.tool()(get_child_name)


