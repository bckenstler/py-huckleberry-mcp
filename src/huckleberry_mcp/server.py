"""Main MCP server entry point for Huckleberry baby tracking."""

import sys
import asyncio
from fastmcp import FastMCP

from huckleberry_mcp.tools.children import register_children_tools
from huckleberry_mcp.tools.sleep import register_sleep_tools
from huckleberry_mcp.tools.feeding import register_feeding_tools
from huckleberry_mcp.tools.diaper import register_diaper_tools
from huckleberry_mcp.tools.growth import register_growth_tools


# Create FastMCP server instance
mcp = FastMCP("huckleberry-mcp")

# Register all tools from modules
register_children_tools(mcp)
register_sleep_tools(mcp)
register_feeding_tools(mcp)
register_diaper_tools(mcp)
register_growth_tools(mcp)


async def main():
    """Main entry point for the MCP server."""
    try:
        print("Initializing Huckleberry MCP server...", file=sys.stderr)
        print("Server ready and waiting for requests", file=sys.stderr)

        # Run the server using FastMCP's async method
        # Authentication will happen lazily when tools are called
        await mcp.run_async()

    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


def run():
    """Entry point for the CLI command."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
