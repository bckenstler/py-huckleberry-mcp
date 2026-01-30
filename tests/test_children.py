"""Tests for child management tools."""

import pytest
from unittest.mock import AsyncMock, patch
from huckleberry_mcp.tools.children import list_children, validate_child_uid, get_child_name


@pytest.fixture
def mock_api():
    """Create a mock API instance."""
    api = AsyncMock()
    api.get_children = AsyncMock(return_value=[
        {"uid": "child1", "name": "Alice", "birthDate": "2023-01-15"},
        {"uid": "child2", "name": "Bob", "birthDate": "2024-03-20"},
    ])
    return api


@pytest.mark.asyncio
async def test_list_children(mock_api):
    """Test listing children."""
    with patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):
        result = await list_children()

        assert len(result) == 2
        assert result[0]["uid"] == "child1"
        assert result[0]["name"] == "Alice"
        assert result[0]["birth_date"] == "2023-01-15"
        assert result[1]["uid"] == "child2"
        assert result[1]["name"] == "Bob"


@pytest.mark.asyncio
async def test_validate_child_uid_valid(mock_api):
    """Test validating a valid child UID."""
    with patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):
        result = await validate_child_uid("child1")
        assert result is True


@pytest.mark.asyncio
async def test_validate_child_uid_invalid(mock_api):
    """Test validating an invalid child UID."""
    with patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):
        with pytest.raises(ValueError, match="Invalid child_uid"):
            await validate_child_uid("invalid_uid")


@pytest.mark.asyncio
async def test_get_child_name_found(mock_api):
    """Test getting child name when found."""
    with patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):
        result = await get_child_name("child1")
        assert result == "Alice"


@pytest.mark.asyncio
async def test_get_child_name_not_found(mock_api):
    """Test getting child name when not found."""
    with patch("huckleberry_mcp.tools.children.get_authenticated_api", return_value=mock_api):
        result = await get_child_name("invalid_uid")
        assert result is None
