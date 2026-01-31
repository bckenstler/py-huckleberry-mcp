"""Main MCP server entry point for Huckleberry baby tracking."""

import sys
import asyncio
from typing import Optional
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .auth import get_authenticated_api, HuckleberryAuthError
from .tools import children, sleep, feeding, diaper, growth


# Create MCP server instance
app = Server("huckleberry-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List all available MCP tools."""
    return [
        # Child management
        Tool(
            name="list_children",
            description="List all child profiles with their UID, name, and birth date",
            inputSchema={
                "type": "object",
                "properties": {},
                "required": []
            }
        ),

        # Sleep tracking
        Tool(
            name="start_sleep",
            description="Begin a sleep tracking session for a child",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="pause_sleep",
            description="Pause an active sleep tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="resume_sleep",
            description="Resume a paused sleep tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="complete_sleep",
            description="Complete and save a sleep tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="cancel_sleep",
            description="Cancel and discard a sleep tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="get_sleep_status",
            description="Get the current status of sleep tracking for a child",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="get_sleep_history",
            description="Get sleep history for a child within a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DD)"}
                },
                "required": ["child_uid"]
            }
        ),

        # Feeding tracking
        Tool(
            name="start_breastfeeding",
            description="Begin a breastfeeding tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "side": {"type": "string", "description": "Which side to start on (left or right)", "enum": ["left", "right"]}
                },
                "required": ["child_uid", "side"]
            }
        ),
        Tool(
            name="pause_feeding",
            description="Pause an active feeding tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="resume_feeding",
            description="Resume a paused feeding tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="switch_feeding_side",
            description="Switch between left and right breast during breastfeeding",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="complete_feeding",
            description="Complete and save a feeding tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="cancel_feeding",
            description="Cancel and discard a feeding tracking session",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="log_bottle_feeding",
            description="Log a bottle feeding without using a timer",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "amount": {"type": "number", "description": "Amount fed"},
                    "bottle_type": {"type": "string", "description": "Type of bottle feeding", "enum": ["formula", "breast_milk", "mixed"], "default": "formula"},
                    "units": {"type": "string", "description": "Units of measurement", "enum": ["oz", "ml"], "default": "oz"}
                },
                "required": ["child_uid", "amount"]
            }
        ),
        Tool(
            name="get_feeding_status",
            description="Get the current status of feeding tracking for a child",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="get_feeding_history",
            description="Get feeding history for a child within a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DD)"}
                },
                "required": ["child_uid"]
            }
        ),

        # Diaper tracking
        Tool(
            name="log_diaper",
            description="Log a diaper change with details",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "mode": {"type": "string", "description": "Diaper mode", "enum": ["pee", "poo", "both", "dry"], "default": "both"},
                    "poo_color": {"type": "string", "description": "Color of poo if present", "enum": ["brown", "yellow", "green", "black"]},
                    "consistency": {"type": "string", "description": "Consistency of poo if present", "enum": ["soft", "firm", "watery", "hard"]}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="get_diaper_history",
            description="Get diaper change history for a child within a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DD)"}
                },
                "required": ["child_uid"]
            }
        ),

        # Growth tracking
        Tool(
            name="log_growth",
            description="Log growth measurements (weight, height, head circumference)",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "weight": {"type": "number", "description": "Weight (lbs if imperial, kg if metric)"},
                    "height": {"type": "number", "description": "Height (inches if imperial, cm if metric)"},
                    "head_circumference": {"type": "number", "description": "Head circumference (inches if imperial, cm if metric)"},
                    "units": {"type": "string", "description": "Measurement system", "enum": ["imperial", "metric"], "default": "imperial"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="get_latest_growth",
            description="Get the latest growth measurements for a child",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"}
                },
                "required": ["child_uid"]
            }
        ),
        Tool(
            name="get_growth_history",
            description="Get growth measurement history for a child within a date range",
            inputSchema={
                "type": "object",
                "properties": {
                    "child_uid": {"type": "string", "description": "The child's unique identifier"},
                    "start_date": {"type": "string", "description": "Start date in ISO format (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "End date in ISO format (YYYY-MM-DD)"}
                },
                "required": ["child_uid"]
            }
        ),
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool invocations."""
    try:
        # Route to appropriate tool function
        if name == "list_children":
            result = await children.list_children()

        # Sleep tracking
        elif name == "start_sleep":
            result = await sleep.start_sleep(arguments["child_uid"])
        elif name == "pause_sleep":
            result = await sleep.pause_sleep(arguments["child_uid"])
        elif name == "resume_sleep":
            result = await sleep.resume_sleep(arguments["child_uid"])
        elif name == "complete_sleep":
            result = await sleep.complete_sleep(arguments["child_uid"])
        elif name == "cancel_sleep":
            result = await sleep.cancel_sleep(arguments["child_uid"])
        elif name == "get_sleep_status":
            result = await sleep.get_sleep_status(arguments["child_uid"])
        elif name == "get_sleep_history":
            result = await sleep.get_sleep_history(
                arguments["child_uid"],
                arguments.get("start_date"),
                arguments.get("end_date")
            )

        # Feeding tracking
        elif name == "start_breastfeeding":
            result = await feeding.start_breastfeeding(
                arguments["child_uid"],
                arguments["side"]
            )
        elif name == "pause_feeding":
            result = await feeding.pause_feeding(arguments["child_uid"])
        elif name == "resume_feeding":
            result = await feeding.resume_feeding(arguments["child_uid"])
        elif name == "switch_feeding_side":
            result = await feeding.switch_feeding_side(arguments["child_uid"])
        elif name == "complete_feeding":
            result = await feeding.complete_feeding(arguments["child_uid"])
        elif name == "cancel_feeding":
            result = await feeding.cancel_feeding(arguments["child_uid"])
        elif name == "log_bottle_feeding":
            result = await feeding.log_bottle_feeding(
                arguments["child_uid"],
                arguments["amount"],
                arguments.get("bottle_type", "formula"),
                arguments.get("units", "oz")
            )
        elif name == "get_feeding_status":
            result = await feeding.get_feeding_status(arguments["child_uid"])
        elif name == "get_feeding_history":
            result = await feeding.get_feeding_history(
                arguments["child_uid"],
                arguments.get("start_date"),
                arguments.get("end_date")
            )

        # Diaper tracking
        elif name == "log_diaper":
            result = await diaper.log_diaper(
                arguments["child_uid"],
                arguments.get("mode", "both"),
                arguments.get("has_pee", False),
                arguments.get("has_poo", False),
                arguments.get("poo_color"),
                arguments.get("consistency")
            )
        elif name == "get_diaper_history":
            result = await diaper.get_diaper_history(
                arguments["child_uid"],
                arguments.get("start_date"),
                arguments.get("end_date")
            )

        # Growth tracking
        elif name == "log_growth":
            result = await growth.log_growth(
                arguments["child_uid"],
                arguments.get("weight"),
                arguments.get("height"),
                arguments.get("head_circumference"),
                arguments.get("units", "imperial")
            )
        elif name == "get_latest_growth":
            result = await growth.get_latest_growth(arguments["child_uid"])
        elif name == "get_growth_history":
            result = await growth.get_growth_history(
                arguments["child_uid"],
                arguments.get("start_date"),
                arguments.get("end_date")
            )

        else:
            raise ValueError(f"Unknown tool: {name}")

        # Format result as TextContent
        import json
        return [TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        error_msg = f"Error executing {name}: {str(e)}"
        print(error_msg, file=sys.stderr)
        return [TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


async def main():
    """Main entry point for the MCP server."""
    try:
        print("Initializing Huckleberry MCP server...", file=sys.stderr)

        # Run the server - authentication will happen lazily when tools are called
        async with stdio_server() as (read_stream, write_stream):
            print("Server ready and waiting for requests", file=sys.stderr)
            await app.run(
                read_stream,
                write_stream,
                app.create_initialization_options()
            )

    except Exception as e:
        print(f"Server error: {e}", file=sys.stderr)
        sys.exit(1)


def run():
    """Entry point for the CLI command."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
