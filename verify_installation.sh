#!/bin/bash
# Verification script for Huckleberry MCP Server installation

set -e

echo "=================================="
echo "Huckleberry MCP Server Verification"
echo "=================================="
echo ""

# Check Python version
echo "1. Checking Python version..."
python3 --version
if [ $? -eq 0 ]; then
    echo "   ✅ Python 3 is installed"
else
    echo "   ❌ Python 3 is not installed"
    exit 1
fi
echo ""

# Check uv installation
echo "2. Checking uv package manager..."
export PATH="$HOME/.local/bin:$PATH"
if command -v uv &> /dev/null; then
    uv --version
    echo "   ✅ uv is installed"
else
    echo "   ❌ uv is not installed"
    echo "   Install with: curl -LsSf https://astral.sh/uv/install.sh | sh"
    exit 1
fi
echo ""

# Check project structure
echo "3. Checking project structure..."
required_files=(
    "pyproject.toml"
    "README.md"
    ".gitignore"
    ".env.example"
    "src/huckleberry_mcp/server.py"
    "src/huckleberry_mcp/auth.py"
    "src/huckleberry_mcp/tools/children.py"
    "src/huckleberry_mcp/tools/sleep.py"
    "src/huckleberry_mcp/tools/feeding.py"
    "src/huckleberry_mcp/tools/diaper.py"
    "src/huckleberry_mcp/tools/growth.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file (missing)"
        exit 1
    fi
done
echo ""

# Check virtual environment
echo "4. Checking virtual environment..."
if [ -d ".venv" ]; then
    echo "   ✅ Virtual environment exists"
else
    echo "   ⚠️  Virtual environment not found"
    echo "   Creating virtual environment..."
    uv sync
fi
echo ""

# Run tests
echo "5. Running tests..."
uv run pytest tests/ -v --tb=short
if [ $? -eq 0 ]; then
    echo "   ✅ All tests passed"
else
    echo "   ❌ Some tests failed"
    exit 1
fi
echo ""

# Check module imports
echo "6. Checking module imports..."
uv run python -c "from huckleberry_mcp import server; print('✅ Server module imports successfully')"
uv run python -c "from huckleberry_mcp import auth; print('✅ Auth module imports successfully')"
uv run python -c "from huckleberry_mcp.tools import children, sleep, feeding, diaper, growth; print('✅ All tool modules import successfully')"
echo ""

# Summary
echo "=================================="
echo "✅ VERIFICATION COMPLETE"
echo "=================================="
echo ""
echo "The Huckleberry MCP Server is properly installed and configured."
echo ""
echo "Next steps:"
echo "1. Set up your credentials in Claude Desktop config"
echo "2. Restart Claude Desktop"
echo "3. Start tracking with: 'List my children'"
echo ""
echo "For more information, see README.md"
