"""
Model Context Protocol (MCP) Implementation Module

Provides both stdio (local) and HTTP (remote) transport implementations for the SQL Agent.

Servers:
  - mcp_impl.server_stdio: Stdio-based MCP server (for VS Code integration)
  - mcp_impl.server_http: HTTP-based MCP server (for remote/multi-user deployments)

Clients:
  - mcp_impl.client_stdio: Stdio-based MCP client
  - mcp_impl.client_http: HTTP-based MCP client

Documentation:
  - mcp_impl/README.md: MCP server setup and configuration
  - mcp_impl/HTTP.md: HTTP transport setup and deployment
"""

import sys
from pathlib import Path

# Add parent directory to path so relative imports work when running from mcp/ subdirectory
_parent_dir = str(Path(__file__).parent.parent)
if _parent_dir not in sys.path:
    sys.path.insert(0, _parent_dir)

__version__ = "1.0.0"
__all__ = ["server_stdio", "server_http", "client_stdio", "client_http"]
