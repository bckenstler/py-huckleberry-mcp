# macOS Installation Guide

## Install uv

On macOS, install uv using the official installer:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

After installation, `uv` will be in `~/.cargo/bin/uv` or `~/.local/bin/uv`.

## Find uv Path

After installing, find where uv is located:

```bash
which uv
```

Common locations:
- `~/.cargo/bin/uv`
- `~/.local/bin/uv`
- `/opt/homebrew/bin/uv` (if installed via Homebrew on Apple Silicon)
- `/usr/local/bin/uv` (if installed via Homebrew on Intel Mac)

## Update Claude Desktop Config

Once you know the path to `uv`, update your Claude Desktop config.

**Config Location**: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Option 1: Use Full Path to uv

```json
{
  "mcpServers": {
    "huckleberry": {
      "command": "/Users/YOUR_USERNAME/.cargo/bin/uv",
      "args": [
        "--directory",
        "/Users/YOUR_USERNAME/projects/py-huckleberry-mcp",
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

### Option 2: Use Python Directly (Alternative)

If you prefer not to use uv, you can run with Python directly:

```json
{
  "mcpServers": {
    "huckleberry": {
      "command": "/usr/bin/python3",
      "args": [
        "-m",
        "huckleberry_mcp.server"
      ],
      "cwd": "/Users/YOUR_USERNAME/projects/py-huckleberry-mcp",
      "env": {
        "HUCKLEBERRY_EMAIL": "your-email@example.com",
        "HUCKLEBERRY_PASSWORD": "your-password",
        "HUCKLEBERRY_TIMEZONE": "America/New_York"
      }
    }
  }
}
```

**Note**: For Option 2, you'll need to install dependencies first:

```bash
cd /Users/YOUR_USERNAME/projects/py-huckleberry-mcp
pip3 install -e .
```

## Setup Steps

1. **Clone the repository**:
   ```bash
   cd ~/projects
   git clone https://github.com/bckenstler/py-huckleberry-mcp.git
   cd py-huckleberry-mcp
   ```

2. **Install dependencies**:
   ```bash
   # If using uv:
   uv sync

   # OR if using pip:
   pip3 install -e .
   ```

3. **Update Claude Desktop config** with your credentials and correct paths

4. **Restart Claude Desktop**

5. **Test it**:
   - Open Claude
   - Ask: "List my children"
   - The server should connect and respond

## Troubleshooting

### Check if uv is installed:
```bash
which uv
uv --version
```

### Test the server manually:
```bash
cd ~/projects/py-huckleberry-mcp

# With uv:
HUCKLEBERRY_EMAIL="test@example.com" \
HUCKLEBERRY_PASSWORD="password" \
HUCKLEBERRY_TIMEZONE="America/New_York" \
uv run huckleberry-mcp

# With Python:
HUCKLEBERRY_EMAIL="test@example.com" \
HUCKLEBERRY_PASSWORD="password" \
HUCKLEBERRY_TIMEZONE="America/New_York" \
python3 -m huckleberry_mcp.server
```

The server should start and wait for JSON-RPC messages. Press Ctrl+C to exit.

### Common Issues

**"uv: command not found"**:
- Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Add to PATH: `export PATH="$HOME/.cargo/bin:$PATH"`
- Or use the full path in the config

**"No module named 'huckleberry_mcp'"**:
- Install dependencies: `uv sync` or `pip3 install -e .`

**"Authentication error"**:
- Check your Huckleberry credentials in the config
- Ensure HUCKLEBERRY_EMAIL and HUCKLEBERRY_PASSWORD are correct

**"Server disconnected"**:
- Check Claude Desktop logs: `~/Library/Logs/Claude/mcp*.log`
- Verify the directory path in the config matches where you cloned the repo
