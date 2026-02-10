# MCP (Model Context Protocol) Integration

This folder contains all MCP-related implementations for the SQL Agent.

## Directory Structure

```
mcp/
├── __init__.py          # Module initialization
├── README.md            # Stdio server documentation
├── HTTP.md              # HTTP server documentation
├── server_stdio.py      # Stdio-based MCP server (local, VS Code)
├── server_http.py       # HTTP-based MCP server (remote, scalable)
├── client_stdio.py      # Stdio-based client for testing
└── client_http.py       # HTTP-based client for testing
```

## Quick Start

### Stdio Server (Default - Local Use)

For VS Code Claude Desktop integration:

```bash
# Terminal 1: Start stdio server
python mcp/server_stdio.py

# Terminal 2: Test with client
python mcp/client_stdio.py
```

See [README.md](README.md) for full setup.

### HTTP Server (Remote Use)

For multi-user or cloud deployments:

```bash
# Terminal 1: Start HTTP server
bash scripts/run_http_server.sh
# or: python mcp/server_http.py

# Terminal 2: Test with client
python mcp/client_http.py --url http://localhost:8000
```

See [HTTP.md](HTTP.md) for full setup and deployment options.

## When to Use Each

| Use Case | Server | Documentation |
|----------|--------|---------------|
| Local development | stdio | [README.md](README.md) |
| VS Code integration | stdio | [README.md](README.md) |
| Remote access | http | [HTTP.md](HTTP.md) |
| Multi-user | http | [HTTP.md](HTTP.md) |
| Cloud deployment | http | [HTTP.md](HTTP.md) |

## Architecture

Both implementations expose the same tools and functionality, just via different transports:

- **Stdio:** Process pipes (IPC) - fast, local-only
- **HTTP:** REST API (JSON-RPC 2.0) - slower, remote-capable

The agent core (src/agent.py) is transport-agnostic and works with both.

## References

- [MCP Specification](https://modelcontextprotocol.io/)
- [Main README](../README.md)
- [Project Source](../src/)
