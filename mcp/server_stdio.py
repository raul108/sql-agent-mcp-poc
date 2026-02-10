"""
Model Context Protocol (MCP) Server for SQL Agent

Exposes SQL Agent tools to VS Code and other MCP clients via stdio transport.
Provides natural language to SQL capabilities through the MCP interface.

Tools exposed:
- query_database: Execute natural language queries
- get_schema: Get database schema information
- get_conversation_history: Retrieve recent conversation

Usage:
    python mcp_server.py
"""

# Fix sys.path if this script is run directly from mcp/ subdirectory
import sys
from pathlib import Path
_script_dir = Path(__file__).parent  # mcp/
_project_root = _script_dir.parent   # parent of mcp/
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import asyncio
import json
import warnings
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Suppress Pydantic v1 compatibility warning for Python 3.14
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)

from src.config import Config
from src.agent import SQLAgent
from src.memory import ConversationMemory


# Initialize agent components
config = Config()
agent = SQLAgent(config)
memory = ConversationMemory()

# Create MCP server
app = Server("sql-agent-mcp")

@app.list_tools()
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
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
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
        # Pass everything to the SQL Agent
        query = arguments.get("query")
        session_id = arguments.get("session_id", "mcp_session")
        
        try:
            result = agent.run(query, session_id=session_id)
            
            # Format response
            response_text = f"Query: {query}\n\n"
            
            for msg in result.get("messages", []):
                response_text += f"{msg['content']}\n\n"
            
            return [TextContent(
                type="text",
                text=response_text.strip()
            )]
            
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error executing query: {str(e)}"
            )]
    
    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]


async def main():
    """
    Start the MCP server with stdio transport.
    """
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
