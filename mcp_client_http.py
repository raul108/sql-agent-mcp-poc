"""
MCP Client for HTTP Transport

Interactive client for the HTTP-based MCP server.
Tests the Streamable HTTP transport implementation.

This client:
- Connects to HTTP MCP server at configurable URL
- Sends JSON-RPC 2.0 requests
- Handles tool discovery and invocation
- Supports session tracking
- Provides interactive query interface

Usage:
    python mcp_client_http.py [--url http://localhost:8000]
"""

import asyncio
import json
import sys
import os
import argparse
from typing import Optional
import httpx
from datetime import datetime


class HTTPMCPClient:
    """MCP Client for HTTP transport."""
    
    def __init__(self, base_url: str = "http://localhost:8000", auth_token: Optional[str] = None):
        """
        Initialize HTTP MCP client.
        
        Args:
            base_url: Base URL of MCP HTTP server
            auth_token: Optional bearer token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.mcp_endpoint = f"{self.base_url}/mcp"
        self.health_endpoint = f"{self.base_url}/health"
        self.auth_token = auth_token
        self.session_id = f"http_session_{datetime.now().timestamp()}"
        self.request_counter = 0
        
        print(f"MCP HTTP Client initialized")
        print(f"  Server: {self.base_url}")
        print(f"  Session: {self.session_id}")
        print()
    
    async def health_check(self) -> bool:
        """Check if server is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(self.health_endpoint, timeout=5.0)
                if response.status_code == 200:
                    data = response.json()
                    print(f"✓ Server is healthy")
                    print(f"  Status: {data.get('status')}")
                    print(f"  Transport: {data.get('transport')}")
                    print(f"  Database: {data.get('database')}")
                    return True
                else:
                    print(f"✗ Server returned status {response.status_code}")
                    return False
        except Exception as e:
            print(f"✗ Health check failed: {str(e)}")
            return False
    
    async def list_tools(self) -> list[dict]:
        """List available tools from server."""
        self.request_counter += 1
        
        request_body = {
            "jsonrpc": "2.0",
            "id": f"tools_list_{self.request_counter}",
            "method": "tools/list",
            "params": {}
        }
        
        try:
            async with httpx.AsyncClient() as client:
                headers = self._build_headers()
                response = await client.post(
                    self.mcp_endpoint,
                    json=request_body,
                    headers=headers,
                    timeout=10.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    tools = data.get("result", {}).get("tools", [])
                    return tools
                else:
                    print(f"Error: Server returned {response.status_code}")
                    return []
        except Exception as e:
            print(f"Error listing tools: {str(e)}")
            return []
    
    async def call_tool(self, tool_name: str, query: str, user_role: str = "GLOBAL_ANALYST") -> Optional[str]:
        """
        Call a tool on the server.
        
        Args:
            tool_name: Name of tool to call
            query: Query/arguments for the tool
            user_role: User role for RBAC
            
        Returns:
            Tool response text or None on error
        """
        self.request_counter += 1
        
        request_body = {
            "jsonrpc": "2.0",
            "id": f"tool_call_{self.request_counter}",
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": {
                    "query": query,
                    "session_id": self.session_id,
                    "user_role": user_role
                }
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                headers = self._build_headers()
                response = await client.post(
                    self.mcp_endpoint,
                    json=request_body,
                    headers=headers,
                    timeout=30.0  # Longer timeout for SQL queries
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Extract content from response
                    result = data.get("result", {})
                    content = result.get("content", [])
                    
                    if content:
                        # Return combined text from all content items
                        text_parts = [item.get("text", "") for item in content if item.get("type") == "text"]
                        return "\n".join(text_parts)
                    else:
                        return "No response from server"
                else:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", "Unknown error")
                    print(f"Error: {error_msg}")
                    return None
        except httpx.TimeoutException:
            print("Error: Request timed out (query might be too slow)")
            return None
        except Exception as e:
            print(f"Error calling tool: {str(e)}")
            return None
    
    def _build_headers(self) -> dict:
        """Build HTTP headers with authentication if configured."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "MCP-HTTP-Client/1.0"
        }
        
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        return headers


async def interactive_session(client: HTTPMCPClient):
    """Run interactive query session."""
    
    # List available tools
    print("\n" + "="*70)
    print("Available Tools:")
    print("="*70)
    tools = await client.list_tools()
    for tool in tools:
        print(f"\n• {tool.get('name')}")
        print(f"  Description: {tool.get('description', 'N/A')}")
    
    print("\n" + "="*70)
    print("Interactive Query Mode")
    print("="*70)
    print("Enter SQL queries or questions about the database.")
    print("Type 'quit' or 'exit' to end session.")
    print("Type 'help' for more options.")
    print()
    
    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ["quit", "exit"]:
                print("Goodbye!")
                break
            
            if user_input.lower() == "help":
                print("""
Commands:
  quit, exit     - Exit the session
  help           - Show this help message
  clear          - Clear screen
  status         - Show server status
  
Normal queries will be sent to the SQL agent.
Examples:
  How many customers?
  Show me customers from ASIA
  What tables are available?
                """)
                continue
            
            if user_input.lower() == "clear":
                os.system("clear" if os.name == "posix" else "cls")
                continue
            
            if user_input.lower() == "status":
                await client.health_check()
                continue
            
            # Send query to tool
            print("\nAgent: Processing your query...")
            response = await client.call_tool("query_database", user_input)
            
            if response:
                print(f"\nAgent: {response}\n")
            else:
                print("Agent: Failed to process query\n")
        
        except KeyboardInterrupt:
            print("\nSession interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"Error: {str(e)}\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="MCP HTTP Client - Test the HTTP-based MCP server"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of MCP HTTP server (default: http://localhost:8000)"
    )
    parser.add_argument(
        "--token",
        default=os.getenv("HTTP_AUTH_TOKEN"),
        help="Bearer token for authentication (or set HTTP_AUTH_TOKEN env var)"
    )
    parser.add_argument(
        "--query",
        help="Single query to execute (non-interactive mode)"
    )
    
    args = parser.parse_args()
    
    # Create client
    client = HTTPMCPClient(base_url=args.url, auth_token=args.token)
    
    # Check server health
    print("Checking server health...")
    if not await client.health_check():
        print("\nServer is not available. Make sure to run:")
        print(f"  uvicorn mcp_server_http:app --host 127.0.0.1 --port 8000")
        sys.exit(1)
    
    print()
    
    # If single query provided, execute it and exit
    if args.query:
        print(f"Query: {args.query}\n")
        response = await client.call_tool("query_database", args.query)
        if response:
            print(f"Response:\n{response}")
    else:
        # Interactive session
        await interactive_session(client)


if __name__ == "__main__":
    asyncio.run(main())
