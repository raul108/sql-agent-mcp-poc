#!/bin/bash

# Stdio MCP Server Launcher
#
# Starts the stdio-based MCP server for VS Code Claude Desktop integration.
# This is the default and recommended server for local development.
#
# Usage:
#   bash scripts/run_stdio_server.sh
#   or: python mcp/server_stdio.py
#
# This server uses stdin/stdout for communication (no network ports).
# Perfect for VS Code integration with Claude Desktop.

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

echo "=================================================="
echo "MCP Stdio Server - VS Code Integration"
echo "=================================================="
echo ""

# Check if virtual environment is activated
if [[ -z "$VIRTUAL_ENV" ]]; then
    echo "⚠️  Virtual environment not activated!"
    echo "Please run: source .venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment: $VIRTUAL_ENV"
echo ""

# Check if required packages are installed
echo "Checking dependencies..."
python -c "import mcp" 2>/dev/null || {
    echo "❌ Missing required packages. Installing..."
    pip install -r requirements.txt
}
echo "✓ All dependencies installed"
echo ""

echo "Starting MCP Stdio Server..."
echo ""
echo "📍 Transport: stdio (stdin/stdout)"
echo "📍 Use case: VS Code Claude Desktop integration"
echo ""
echo "Configuration for VS Code:"
echo "  Set this in VS Code settings (settings.json):"
echo ""
echo '  "modelContextProtocol.mcpServers": {'
echo '    "sql-agent": {'
echo '      "command": "python",'
echo '      "args": ["mcp/server_stdio.py"],'
echo '      "env": {'
echo '        "SNOWFLAKE_ACCOUNT": "your_account",'
echo '        "SNOWFLAKE_USER": "your_user",'
echo '        "OPENAI_API_KEY": "sk-..."'
echo '      }'
echo '    }'
echo '  }'
echo ""
echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

# Start the server
exec python mcp/server_stdio.py
