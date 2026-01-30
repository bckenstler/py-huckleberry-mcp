# Huckleberry MCP Server

A Model Context Protocol (MCP) server that interfaces with the Huckleberry baby tracking API, enabling Claude to help you track your baby's sleep, feeding, diaper changes, and growth measurements through natural conversation.

## Features

- **Child Management**: List and manage multiple child profiles
- **Sleep Tracking**: Start, pause, resume, complete, and cancel sleep sessions
- **Feeding Tracking**: Track breastfeeding sessions with side switching and bottle feeding
- **Diaper Logging**: Record diaper changes with type, color, and consistency details
- **Growth Tracking**: Log and retrieve weight, height, and head circumference measurements

## Prerequisites

- Python 3.10 or higher
- A Huckleberry account with valid credentials
- Claude Desktop application (for integration)
- `uv` package manager (recommended) or `pip`

## Installation

### Using uv (Recommended)

```bash
cd /home/ubuntu/projects/huckleberry-mcp
uv sync
```

### Using pip

```bash
cd /home/ubuntu/projects/huckleberry-mcp
pip install -e .
```

## Authentication Setup

The server requires your Huckleberry credentials to be configured as environment variables. You have two options:

### Option 1: Claude Desktop Configuration (Recommended)

Add the server to your Claude Desktop configuration file with your credentials:

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**Linux**: `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "huckleberry": {
      "command": "uv",
      "args": [
        "--directory",
        "/home/ubuntu/projects/huckleberry-mcp",
        "run",
        "huckleberry-mcp"
      ],
      "env": {
        "HUCKLEBERRY_EMAIL": "your-email@example.com",
        "HUCKLEBERRY_PASSWORD": "your-password",
        "HUCKLEBERRY_TIMEZONE": "America/New_York"
      }
    }
  }
}
```

### Option 2: Environment Variables

Create a `.env` file in the project root (copy from `.env.example`):

```bash
cp .env.example .env
```

Then edit `.env` with your credentials:

```bash
HUCKLEBERRY_EMAIL=your-email@example.com
HUCKLEBERRY_PASSWORD=your-password
HUCKLEBERRY_TIMEZONE=America/New_York
```

## Available Tools

### Child Management

#### `list_children`
List all child profiles with their UID, name, and birth date.

**Example**: "List my children"

### Sleep Tracking

#### `start_sleep`
Begin a sleep tracking session for a child.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Start a sleep session for Alice"

#### `pause_sleep`
Pause an active sleep tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Pause the sleep session"

#### `resume_sleep`
Resume a paused sleep tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Resume the sleep session"

#### `complete_sleep`
Complete and save a sleep tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Complete the sleep session"

#### `cancel_sleep`
Cancel and discard a sleep tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Cancel the sleep session"

#### `get_sleep_status`
Get the current status of sleep tracking for a child.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "What's the sleep status?"

#### `get_sleep_history`
Get sleep history for a child within a date range.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD)
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD)

**Example**: "Show me sleep history for the last week"

### Feeding Tracking

#### `start_breastfeeding`
Begin a breastfeeding tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `side` (string, required): Which side to start on ("left" or "right")

**Example**: "Start breastfeeding on the left side"

#### `pause_feeding`
Pause an active feeding tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Pause feeding"

#### `resume_feeding`
Resume a paused feeding tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Resume feeding"

#### `switch_feeding_side`
Switch between left and right breast during breastfeeding.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Switch to the other side"

#### `complete_feeding`
Complete and save a feeding tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Complete feeding"

#### `cancel_feeding`
Cancel and discard a feeding tracking session.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "Cancel feeding"

#### `log_bottle_feeding`
Log a bottle feeding without using a timer.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `amount` (number, required): Amount fed
- `bottle_type` (string, optional): Type of bottle feeding ("formula", "breast_milk", "mixed"), default: "formula"
- `units` (string, optional): Units of measurement ("oz" or "ml"), default: "oz"

**Example**: "Log a 4oz formula bottle"

#### `get_feeding_status`
Get the current status of feeding tracking for a child.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "What's the feeding status?"

#### `get_feeding_history`
Get feeding history for a child within a date range.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD)
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD)

**Example**: "Show me today's feedings"

### Diaper Tracking

#### `log_diaper`
Log a diaper change with details.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `mode` (string, optional): Diaper mode ("pee", "poo", "both", "dry"), default: "both"
- `poo_color` (string, optional): Color of poo if present ("brown", "yellow", "green", "black")
- `consistency` (string, optional): Consistency of poo if present ("soft", "firm", "watery", "hard")

**Example**: "Log a diaper change with pee and poo"

#### `get_diaper_history`
Get diaper change history for a child within a date range.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD)
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD)

**Example**: "Show me today's diaper changes"

### Growth Tracking

#### `log_growth`
Log growth measurements (weight, height, head circumference).

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `weight` (number, optional): Weight (lbs if imperial, kg if metric)
- `height` (number, optional): Height (inches if imperial, cm if metric)
- `head_circumference` (number, optional): Head circumference (inches if imperial, cm if metric)
- `units` (string, optional): Measurement system ("imperial" or "metric"), default: "imperial"

**Example**: "Log weight of 12.5 lbs and height of 24 inches"

#### `get_latest_growth`
Get the latest growth measurements for a child.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "What are the latest growth measurements?"

#### `get_growth_history`
Get growth measurement history for a child within a date range.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD)
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD)

**Example**: "Show me growth history for the last month"

## Usage Examples

Once configured in Claude Desktop, you can interact with the server through natural conversation:

1. **List your children**:
   - "List my children"
   - "Show me all my kids"

2. **Track sleep**:
   - "Start a sleep session for Alice"
   - "Alice is sleeping"
   - "Pause the sleep timer"
   - "Alice woke up, complete the sleep session"

3. **Track feeding**:
   - "Start breastfeeding on the left side"
   - "Switch to the right breast"
   - "Complete the feeding session"
   - "Log a 4oz formula bottle"

4. **Log diaper changes**:
   - "Log a diaper change with pee and poo"
   - "Log a wet diaper"
   - "Log a poopy diaper with soft brown poo"

5. **Track growth**:
   - "Log weight of 12.5 lbs"
   - "Log weight 12.5 lbs, height 24 inches, and head circumference 16 inches"
   - "What are the latest growth measurements?"

6. **View history**:
   - "Show me sleep history for last week"
   - "How many diaper changes today?"
   - "Show me all feedings from yesterday"

## Development

### Running Tests

```bash
# Using uv
uv run pytest tests/ -v

# Using pip
pytest tests/ -v
```

### Project Structure

```
huckleberry-mcp/
├── src/
│   └── huckleberry_mcp/
│       ├── __init__.py
│       ├── server.py              # Main MCP server entry point
│       ├── auth.py                # Authentication handler
│       └── tools/
│           ├── __init__.py
│           ├── children.py        # Child management tools
│           ├── sleep.py           # Sleep tracking tools
│           ├── feeding.py         # Feeding tracking tools
│           ├── diaper.py          # Diaper logging tools
│           └── growth.py          # Growth measurement tools
├── tests/                         # Test suite
├── pyproject.toml                 # Project configuration
├── README.md                      # This file
├── .env.example                   # Example environment variables
└── .gitignore
```

## Troubleshooting

### Authentication Errors

If you see authentication errors:

1. Verify your credentials are correct in the Claude Desktop config
2. Ensure your Huckleberry account is active
3. Check that the timezone is valid (e.g., "America/New_York", "Europe/London")

### Server Not Appearing in Claude Desktop

1. Verify the configuration file path is correct for your OS
2. Restart Claude Desktop after making config changes
3. Check the Claude Desktop logs for error messages
4. Ensure `uv` is installed and in your PATH

### Tools Not Working

1. Make sure you've listed children first to get valid child UIDs
2. Verify the child UID is correct when using tools
3. Check for active sessions before starting new ones (sleep/feeding)
4. Review error messages for specific validation issues

## Security Considerations

- Never commit your `.env` file or credentials to version control
- Store credentials only in environment variables or Claude Desktop config
- The `.gitignore` file excludes `.env` files by default
- Credentials are never logged by the server

## Contributing

This is a personal project, but suggestions and bug reports are welcome!

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses the [huckleberry-api](https://github.com/Woyken/py-huckleberry-api) Python library
- Powered by Claude from Anthropic

## Support

For issues with:
- **This MCP server**: Open an issue in this repository
- **The Huckleberry API library**: See [py-huckleberry-api](https://github.com/Woyken/py-huckleberry-api)
- **Huckleberry app**: Contact Huckleberry support
- **Claude Desktop**: See [Anthropic documentation](https://docs.anthropic.com/)
