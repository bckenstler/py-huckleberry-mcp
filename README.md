# Huckleberry MCP Server

A Model Context Protocol (MCP) server that interfaces with the Huckleberry baby tracking API, enabling Claude to help you track your baby's sleep, feeding, diaper changes, and growth measurements through natural conversation.

## Features

- **Child Management**: List and manage multiple child profiles
- **Sleep Tracking**: Start, pause, resume, complete, and cancel sleep sessions with automatic history tracking
- **Feeding Tracking**: Track breastfeeding sessions with side switching
- **Diaper Logging**: Record diaper changes with type, amount, color, and consistency details
- **Growth Tracking**: Log and retrieve weight, height, and head circumference measurements

## Prerequisites

- Python 3.10 or higher
- A Huckleberry account with valid credentials
- Claude Desktop application (for integration)
- `uv` package manager (recommended) or `pip`

## Installation

### Using uv (Recommended)

```bash
# Clone or navigate to the project directory
cd /path/to/huckleberry-mcp
uv sync
```

### Using pip

```bash
cd /path/to/huckleberry-mcp
pip install -e .
```

## Authentication Setup

The server requires your Huckleberry credentials to be configured as environment variables.

### Claude Desktop Configuration (Recommended)

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
        "/absolute/path/to/huckleberry-mcp",
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

**Important**:
- Replace `/absolute/path/to/huckleberry-mcp` with the actual absolute path to this project
- On macOS, if using Anaconda, specify the full path to `uv`: `/Users/your-username/anaconda3/bin/uv`
- Ensure `uv` is in your PATH or use the full path to the `uv` executable

## Available Tools

### Child Management

#### `list_children`
List all child profiles with their UID, name, and birth date.

**Example**: "List my children"

### Sleep Tracking

#### `log_sleep`
Directly log a completed sleep session without using the timer. Useful for retroactive logging or importing past sleep data.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_time` (string, required): Sleep start time in ISO format. If no timezone specified (e.g., "2026-01-30T14:30:00"), interpreted as your configured timezone. For UTC, use "2026-01-30T14:30:00Z".
- `end_time` (string, optional): Sleep end time in ISO format (provide this OR duration_minutes). Same timezone handling as start_time.
- `duration_minutes` (integer, optional): Sleep duration in minutes (provide this OR end_time)

**Timezone Note**: Times without timezone info are interpreted using your `HUCKLEBERRY_TIMEZONE` setting (e.g., "America/New_York"). This ensures times appear correctly in the Huckleberry app.

**Example**: "Log a sleep session from 2pm to 4pm yesterday"

#### `start_sleep`
Begin a sleep tracking session for a child using real-time timer.

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

#### `get_sleep_history`
Get sleep history for a child within a date range (defaults to last 7 days).

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD), inclusive
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD), exclusive (data up to but not including this date)

**Important**: The `end_date` is exclusive. To get data for a single day (e.g., Jan 30), set `start_date='2026-01-30'` and `end_date='2026-01-31'`.

**Example**: "Show me sleep history for the last week"

### Feeding Tracking

#### `log_breastfeeding`
Directly log a completed breastfeeding session without using the timer. Useful for retroactive logging or importing past feeding data.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_time` (string, required): Feeding start time in ISO format. If no timezone specified, interpreted as your configured timezone.
- `left_duration_minutes` (integer, optional): Duration on left breast in minutes
- `right_duration_minutes` (integer, optional): Duration on right breast in minutes
- `end_time` (string, optional): Feeding end time in ISO format (provide this OR durations)
- `last_side` (string, optional): Which side finished on ("left" or "right"). Required if using end_time.

**Usage patterns**:
- With durations: Provide `left_duration_minutes` and/or `right_duration_minutes`
- With end time: Provide `end_time` and `last_side` (calculates duration automatically)

**Timezone Note**: Times without timezone info are interpreted using your `HUCKLEBERRY_TIMEZONE` setting.

**Examples**:
- "Log a breastfeeding session from 2pm to 2:30pm yesterday on the left"
- "Log breastfeeding: 10 minutes left, 15 minutes right, starting at 3pm today"

#### `start_breastfeeding`
Begin a breastfeeding tracking session using real-time timer.

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

#### `get_feeding_history`
Get feeding history for a child within a date range (defaults to last 7 days).

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD), inclusive
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD), exclusive (data up to but not including this date)

**Important**: The `end_date` is exclusive. To get data for a single day (e.g., Jan 30), set `start_date='2026-01-30'` and `end_date='2026-01-31'`.

**Example**: "Show me today's feedings"

### Diaper Tracking

#### `log_diaper`
Log a diaper change with details. Supports retroactive logging with optional timestamp.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `mode` (string, optional): Diaper mode ("pee", "poo", "both", "dry"), default: "both"
- `pee_amount` (string, optional): Pee amount ("little", "medium", "big")
- `poo_amount` (string, optional): Poo amount ("little", "medium", "big")
- `color` (string, optional): Poo color if present ("yellow", "brown", "black", "green", "red", "gray")
- `consistency` (string, optional): Poo consistency if present ("solid", "loose", "runny", "mucousy", "hard", "pebbles", "diarrhea")
- `diaper_rash` (boolean, optional): Whether baby has diaper rash, default: false
- `notes` (string, optional): Optional notes about the diaper change
- `timestamp` (string, optional): Timestamp in ISO format for retroactive logging. If not provided, uses current time.

**Timezone Note**: Times without timezone info are interpreted using your `HUCKLEBERRY_TIMEZONE` setting.

**Examples**:
- "Log a diaper change with pee and poo"
- "Log a wet diaper from 2 hours ago" (with retroactive timestamp)

#### `get_diaper_history`
Get diaper change history for a child within a date range (defaults to last 7 days).

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD), inclusive
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD), exclusive (data up to but not including this date)

**Important**: The `end_date` is exclusive. To get data for a single day (e.g., Jan 30), set `start_date='2026-01-30'` and `end_date='2026-01-31'`.

**Example**: "Show me today's diaper changes"

### Growth Tracking

#### `log_growth`
Log growth measurements (weight, height, head circumference). Supports retroactive logging with optional timestamp.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `weight` (number, optional): Weight (lbs if imperial, kg if metric)
- `height` (number, optional): Height (inches if imperial, cm if metric)
- `head` (number, optional): Head circumference (inches if imperial, cm if metric)
- `units` (string, optional): Measurement system ("imperial" or "metric"), default: "imperial"
- `timestamp` (string, optional): Timestamp in ISO format for retroactive logging. If not provided, uses current time.

**Timezone Note**: Times without timezone info are interpreted using your `HUCKLEBERRY_TIMEZONE` setting.

**Examples**:
- "Log weight of 12.5 lbs and height of 24 inches"
- "Log weight measurement from yesterday's doctor visit" (with retroactive timestamp)

#### `get_latest_growth`
Get the latest growth measurements for a child.

**Parameters**:
- `child_uid` (string, required): The child's unique identifier

**Example**: "What are the latest growth measurements?"

#### `get_growth_history`
Get growth measurement history for a child within a date range (defaults to last 30 days).

**Parameters**:
- `child_uid` (string, required): The child's unique identifier
- `start_date` (string, optional): Start date in ISO format (YYYY-MM-DD), inclusive
- `end_date` (string, optional): End date in ISO format (YYYY-MM-DD), exclusive (data up to but not including this date)

**Important**: The `end_date` is exclusive. To get data for a single day (e.g., Jan 30), set `start_date='2026-01-30'` and `end_date='2026-01-31'`.

**Example**: "Show me growth history for the last month"

## Usage Examples

Once configured in Claude Desktop, you can interact with the server through natural conversation:

1. **List your children**:
   - "List my children"
   - "Show me all my kids"

2. **Track sleep**:
   - "Log a sleep session from 2pm to 4pm yesterday" (direct logging)
   - "Log that Alice slept for 90 minutes starting at 1pm today" (direct logging)
   - "Start a sleep session for Alice" (real-time timer)
   - "Alice is sleeping"
   - "Pause the sleep timer"
   - "Alice woke up, complete the sleep session"
   - "Show me sleep history for the last week"

3. **Track feeding**:
   - "Log a breastfeeding session from 2pm to 2:30pm on the left" (direct logging)
   - "Log breastfeeding: 10 minutes left, 15 minutes right, starting at 3pm" (direct logging)
   - "Start breastfeeding on the left side" (real-time timer)
   - "Switch to the right breast"
   - "Complete the feeding session"
   - "Show me today's feedings"

4. **Log diaper changes**:
   - "Log a diaper change with pee and poo"
   - "Log a wet diaper"
   - "Log a poopy diaper with loose yellow poo"
   - "Log a diaper change with medium poo and diaper rash"

5. **Track growth**:
   - "Log weight of 12.5 lbs"
   - "Log weight 12.5 lbs, height 24 inches, and head 16 inches"
   - "What are the latest growth measurements?"
   - "Show me growth history for the last month"

6. **View history**:
   - "Show me sleep history for last week"
   - "How many diaper changes today?"
   - "Show me all feedings from yesterday"

## Development

### Running Tests

All tests pass and accurately reflect the actual Huckleberry API:

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
├── tests/                         # Test suite (36 tests, all passing)
├── pyproject.toml                 # Project configuration
├── README.md                      # This file
├── .env.example                   # Example environment variables
└── .gitignore
```

## Implementation Notes

This server is fully refactored to match the actual [py-huckleberry-api](https://github.com/Woyken/py-huckleberry-api) library interface:

- All history methods use Unix timestamps internally and convert to/from ISO dates
- Timer operations (sleep/feeding) directly call API methods without status pre-checks
- Growth tracking uses `head` parameter instead of `head_circumference`
- Diaper logging includes amount fields (`pee_amount`, `poo_amount`) and uses `color` instead of `poo_color`
- The server starts successfully even with invalid credentials, returning helpful errors when tools are called

## Troubleshooting

### Authentication Errors

If you see authentication errors when calling tools:

1. Verify your credentials are correct in the Claude Desktop config
2. Ensure your Huckleberry account is active and you can log in via the app
3. Check that the timezone is valid (e.g., "America/New_York", "Europe/London")
4. The server will start successfully but authentication happens when you call a tool

### Server Not Appearing in Claude Desktop

1. Verify the configuration file path is correct for your OS
2. Check that the `--directory` path is absolute and correct
3. On macOS with Anaconda, use full path to uv: `/Users/your-username/anaconda3/bin/uv`
4. Restart Claude Desktop after making config changes
5. Check the Claude Desktop logs for error messages
6. Ensure `uv` is installed and accessible

### Server Fails to Start

If you see "Failed to spawn process: No such file or directory":

1. The `uv` command is not found - specify the full path to the `uv` executable
2. On macOS, find uv with: `which uv` or check `/Users/your-username/anaconda3/bin/uv`
3. Update the `command` field in your config to use the absolute path

### Tools Not Working

1. Make sure you've listed children first to get valid child UIDs
2. Verify the child UID is correct when using tools
3. Timer sessions can be started/stopped without checking status first
4. Review error messages for specific validation issues (invalid colors, amounts, etc.)

## Security Considerations

- Never commit your `.env` file or credentials to version control
- Store credentials only in environment variables or Claude Desktop config
- The `.gitignore` file excludes `.env` files by default
- Credentials are never logged by the server
- All API communication uses HTTPS

## Contributing

This is a personal project, but suggestions and bug reports are welcome!

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with the [Model Context Protocol](https://modelcontextprotocol.io/)
- Uses the [py-huckleberry-api](https://github.com/Woyken/py-huckleberry-api) Python library
- Powered by Claude from Anthropic

## Support

For issues with:
- **This MCP server**: Open an issue in this repository
- **The Huckleberry API library**: See [py-huckleberry-api](https://github.com/Woyken/py-huckleberry-api)
- **Huckleberry app**: Contact Huckleberry support
- **Claude Desktop**: See [Anthropic documentation](https://docs.anthropic.com/)
