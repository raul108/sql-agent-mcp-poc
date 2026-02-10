#!/bin/bash

# HTTP MCP Server Launcher
# 
# Starts the HTTP-based MCP server with uvicorn.
# Provides an alternative to the stdio-based MCP server for remote/multi-user scenarios.
#
# Usage:
#   bash scripts/run_http_server.sh
#
# Environment Variables:
#   HTTP_HOST        - Bind address (default: 127.0.0.1)
#   HTTP_PORT        - Bind port (default: 8000)
#   HTTP_AUTH_TOKEN  - Optional bearer token for authentication
#   DEBUG            - Set to "true" for debug mode
#
# Examples:
#   # Local testing (default)
#   bash scripts/run_http_server.sh
#
#   # Listen on all interfaces for remote access
#   HTTP_HOST=0.0.0.0 bash scripts/run_http_server.sh
#
#   # Use custom port
#   HTTP_PORT=9000 bash scripts/run_http_server.sh
#
#   # Enable authentication
#   HTTP_AUTH_TOKEN="your-secret-token" bash scripts/run_http_server.sh
#
#   # Production deployment
#   HTTP_HOST=0.0.0.0 HTTP_PORT=8000 DEBUG=false uvicorn mcp_server_http:app --workers 4

set -e

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# Change to project directory
cd "$PROJECT_DIR"

# Default configuration
HTTP_HOST="${HTTP_HOST:-127.0.0.1}"
HTTP_PORT="${HTTP_PORT:-8000}"
DEBUG="${DEBUG:-true}"

echo "=================================================="
echo "MCP HTTP Server - Streamable HTTP Transport"
echo "=================================================="
echo ""
echo "Configuration:"
echo "  Host:        $HTTP_HOST"
echo "  Port:        $HTTP_PORT"
echo "  Debug:       $DEBUG"
echo "  Python:      $(python --version)"
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
python -c "import starlette" 2>/dev/null || {
    echo "❌ Missing required packages. Installing..."
    pip install -r requirements.txt
}
echo "✓ All dependencies installed"
echo ""

# Display server information
echo "Starting MCP HTTP Server..."
echo ""
echo "📍 Endpoints:"
echo "  Health Check:  http://$HTTP_HOST:$HTTP_PORT/health"
echo "  MCP Endpoint:  http://$HTTP_HOST:$HTTP_PORT/mcp"
echo ""

if [[ "$HTTP_HOST" == "127.0.0.1" || "$HTTP_HOST" == "localhost" ]]; then
    echo "✓ Local server (localhost only)"
    echo ""
    echo "To test with the HTTP client:"
    echo "  python mcp/client_http.py --url http://localhost:$HTTP_PORT"
    echo ""
else
    echo "⚠️  Listening on $HTTP_HOST (accessible remotely)"
    echo ""
    echo "Remote clients can connect to:"
    echo "  http://$HTTP_HOST:$HTTP_PORT"
    echo ""
    if [[ -n "$HTTP_AUTH_TOKEN" ]]; then
        echo "✓ Authentication enabled"
    else
        echo "⚠️  No authentication configured (set HTTP_AUTH_TOKEN for security)"
    fi
    echo ""
fi

echo "Press Ctrl+C to stop the server"
echo "=================================================="
echo ""

# Start the server
# Use uvicorn with the specified host and port
exec uvicorn mcp.server_http:app \
    --host "$HTTP_HOST" \
    --port "$HTTP_PORT" \
    --reload \
    --log-level info
