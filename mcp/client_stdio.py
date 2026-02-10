#!/usr/bin/env python3
"""
Interactive MCP Client for SQL Agent

This MCP client connects to mcp_server.py and provides a simple interface
to chat with your SQL Agent using natural language.

The SQL Agent handles everything internally:
- Schema questions: "What tables exist?", "Show me the schema"
- Data queries: "How many customers?", "Top 5 nations by revenue"
- Follow-up questions: "What about orders?"

Usage:
    python mcp_client.py

Commands:
    - Type any question and press Enter
    - 'quit' or 'exit' - Exit the client
"""

import asyncio
import sys
import warnings
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters
from datetime import datetime

# Suppress Pydantic v1 compatibility warning for Python 3.14
warnings.filterwarnings("ignore", message=".*Pydantic V1.*", category=UserWarning)

# Generate a unique session ID for this chat
SESSION_ID = f"mcp_client_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

async def run_interactive_client():
    """Run an interactive MCP client that connects to the SQL Agent."""
    
    print("=" * 70)
    print("🔌 SQL Agent MCP Client")
    print("=" * 70)
    print("\nConnecting to MCP server...")
    
    # Connect to the MCP server
    server_params = StdioServerParameters(
        command=".venv/bin/python",
        args=["mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            
            # Initialize the session
            await session.initialize()
            print("✓ Connected to sql-agent MCP server")
            
            # List available tools
            tools = await session.list_tools()
            print(f"✓ Found {len(tools.tools)} available tools\n")
            
            print("=" * 70)
            print("Ask any question about your TPC-H database!")
            print("-" * 70)
            print("Examples: 'How many customers?', 'Show the schema', 'Top 5 nations'")
            print("Type 'quit' to exit")
            print("=" * 70)
            print()
            
            # Interactive loop
            while True:
                try:
                    # Get user input
                    user_input = input("You: ").strip()
                    
                    if not user_input:
                        continue
                    
                    # Handle quit command
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("\n👋 Goodbye!")
                        break
                    
                    # Send all queries to the SQL Agent
                    print()
                    result = await session.call_tool(
                        name="query_database",
                        arguments={
                            "query": user_input,
                            "session_id": SESSION_ID
                        }
                    )
                    
                    # Print the response
                    for content in result.content:
                        print(f"Agent: {content.text}")
                    print()
                
                except KeyboardInterrupt:
                    print("\n\n👋 Goodbye!")
                    break
                except Exception as e:
                    print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    asyncio.run(run_interactive_client())
