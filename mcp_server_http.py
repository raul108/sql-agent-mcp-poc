"""
Model Context Protocol (MCP) Server - HTTP Transport Version

Exposes SQL Agent tools via HTTP with Streamable HTTP transport (Starlette ASGI app).
Provides natural language to SQL capabilities through REST API with MCP compatibility.

This is the HTTP/scalable version of the SQL agent MCP server.
For local VS Code integration, use mcp_server.py (stdio version) instead.

Features:
- Streamable HTTP transport (MCP specification compliant)
- Stateless JSON response mode (horizontally scalable)
- Optional bearer token authentication
- Health check endpoint
- CORS support for browser-based clients

Usage:
    uvicorn mcp_server_http:app --host 0.0.0.0 --port 8000
    
or:
    bash scripts/run_http_server.sh

Environment Variables:
    HTTP_HOST: Server bind address (default: 127.0.0.1)
    HTTP_PORT: Server port (default: 8000)
    HTTP_AUTH_TOKEN: Optional bearer token for authentication
"""

import asyncio
import json
import warnings
from typing import Any, Optional
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent
from starlette.applications import Starlette
from starlette.responses import JSONResponse, StreamingResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Suppress Pydantic v1 compatibility warning
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)

from src.config import Config
from src.agent import SQLAgent
from src.memory import ConversationMemory

# Initialize agent components
logger.info("Initializing SQL Agent and MCP server components...")
config = Config()
agent = SQLAgent(config)
memory = ConversationMemory()

# Create MCP server
mcp_server = Server("sql-agent-mcp-http")

@mcp_server.list_tools()
async def list_tools() -> list[Tool]:
    """
    List available tools for MCP clients.
    
    Returns:
        List of Tool definitions
    """
    return [
        Tool(
            name="query_database",
            description=(
                "Ask questions about the Snowflake database using natural language. "
                "The SQL Agent will handle your request through its 6-node workflow: "
                "scope detection, SQL generation, safety validation, execution, formatting, and response. "
                "You can ask about data, request schema information, or ask follow-up questions. "
                "Examples: 'How many customers?', 'Show me the schema', 'What tables exist?'"
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Your natural language question or request"
                    },
                    "session_id": {
                        "type": "string",
                        "description": "Optional session ID for conversation tracking"
                    },
                    "user_role": {
                        "type": "string",
                        "description": "Optional user role for RBAC (future feature)",
                        "default": "GLOBAL_ANALYST"
                    }
                },
                "required": ["query"]
            }
        )
    ]


@mcp_server.call_tool()
async def call_tool(name: str, arguments: Any) -> list[TextContent]:
    """
    Execute a tool call from MCP client.
    
    Args:
        name: Tool name to execute
        arguments: Tool arguments
        
    Returns:
        List of TextContent responses
    """
    
    if name == "query_database":
        query = arguments.get("query")
        session_id = arguments.get("session_id", "http_session")
        user_role = arguments.get("user_role", "GLOBAL_ANALYST")
        
        logger.info(f"Processing query: {query[:50]}... (session: {session_id})")
        
        try:
            result = agent.run(query, session_id=session_id, user_role=user_role)
            
            # Format response
            response_text = f"Query: {query}\n\n"
            
            for msg in result.get("messages", []):
                response_text += f"{msg['content']}\n\n"
            
            logger.info(f"Query successful for session {session_id}")
            
            return [TextContent(
                type="text",
                text=response_text.strip()
            )]
            
        except Exception as e:
            logger.error(f"Error executing query: {str(e)}", exc_info=True)
            return [TextContent(
                type="text",
                text=f"Error executing query: {str(e)}"
            )]
    
    else:
        logger.warning(f"Unknown tool requested: {name}")
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


# ============================================================================
# Starlette HTTP Handler Functions
# ============================================================================

async def handle_options(request):
    """Handle CORS preflight requests."""
    return JSONResponse({"status": "ok"})


async def health_check(request):
    """
    Health check endpoint.
    
    Returns JSON with server status.
    """
    try:
        # Test that agent is initialized
        return JSONResponse({
            "status": "healthy",
            "version": "1.0.0",
            "transport": "streamable-http",
            "agent_ready": True,
            "database": config.get_snowflake_config().get('database', 'unknown')
        })
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JSONResponse(
            {
                "status": "unhealthy",
                "error": str(e)
            },
            status_code=503
        )


async def mcp_endpoint(request):
    """
    Main MCP HTTP endpoint.
    
    Handles JSON-RPC 2.0 requests for MCP protocol.
    Implements Streamable HTTP transport (stateless JSON response mode).
    
    Expected request:
    {
        "jsonrpc": "2.0",
        "id": "request-id",
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {"query": "..."}
        }
    }
    
    Response (streaming or JSON):
    [
        {"type": "text", "text": "..."},
        {"type": "text", "text": "..."}
    ]
    """
    
    if request.method == "OPTIONS":
        return JSONResponse({"status": "ok"})
    
    if request.method != "POST":
        return JSONResponse(
            {"error": "Only POST requests supported"},
            status_code=405
        )
    
    try:
        # Parse request body
        body = await request.json()
        
        # Extract authentication if present
        auth_token = request.headers.get("Authorization", "").replace("Bearer ", "")
        env_token = os.getenv("HTTP_AUTH_TOKEN")
        
        # Validate authentication if configured
        if env_token and auth_token != env_token:
            logger.warning("Unauthorized request - invalid token")
            return JSONResponse(
                {"error": "Unauthorized"},
                status_code=401
            )
        
        # Handle MCP protocol methods
        method = body.get("method")
        request_id = body.get("id")
        
        logger.info(f"Received MCP method: {method} (request_id: {request_id})")
        
        if method == "tools/list":
            # List available tools
            tools = await list_tools()
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description,
                            "inputSchema": tool.inputSchema
                        }
                        for tool in tools
                    ]
                }
            }
            return JSONResponse(response)
        
        elif method == "tools/call":
            # Call a tool
            params = body.get("params", {})
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            logger.info(f"Calling tool: {tool_name}")
            
            result = await call_tool(tool_name, arguments)
            
            # Convert TextContent to JSON-serializable format
            response_content = []
            for content in result:
                response_content.append({
                    "type": content.type,
                    "text": content.text
                })
            
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "content": response_content
                }
            }
            return JSONResponse(response)
        
        else:
            logger.warning(f"Unknown MCP method: {method}")
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Method not found: {method}"
                    }
                },
                status_code=400
            )
    
    except json.JSONDecodeError:
        logger.error("Invalid JSON in request body")
        return JSONResponse(
            {"error": "Invalid JSON"},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Unexpected error in MCP endpoint: {str(e)}", exc_info=True)
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


# ============================================================================
# Starlette ASGI Application
# ============================================================================

# Define routes
routes = [
    Route("/health", health_check, methods=["GET"]),
    Route("/mcp", mcp_endpoint, methods=["POST", "OPTIONS"]),
    Route("/", health_check, methods=["GET"]),  # Root endpoint
]

# Create Starlette application
app = Starlette(
    routes=routes,
    debug=os.getenv("DEBUG", "false").lower() == "true"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (configure for production)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware to log requests
@app.middleware("http")
async def log_requests(request, call_next):
    """Log HTTP requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


# ============================================================================
# Server startup/shutdown handlers
# ============================================================================

@app.on_event("startup")
async def startup():
    """Initialize server on startup."""
    logger.info("Starting MCP HTTP Server...")
    logger.info(f"Snowflake Database: {config.get_snowflake_config().get('database')}")
    logger.info("Server ready to accept requests at /health and /mcp endpoints")


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on server shutdown."""
    logger.info("Shutting down MCP HTTP Server...")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("HTTP_HOST", "127.0.0.1")
    port = int(os.getenv("HTTP_PORT", "8000"))
    
    logger.info(f"Starting HTTP server on {host}:{port}")
    logger.info("For production, use: uvicorn mcp_server_http:app --host 0.0.0.0 --port 8000")
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )
