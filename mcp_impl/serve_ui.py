#!/usr/bin/env python3
"""
Simple HTTP server to serve the test_http.html UI
Run: python serve_ui.py
Then open: http://localhost:8001
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
import sys

class MyHTTPRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow requests to localhost:8000
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_GET(self):
        if self.path == '/':
            self.path = '/test_http.html'
        return super().do_GET()

if __name__ == '__main__':
    # Change to mcp_impl directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    port = 8001
    server = HTTPServer(('127.0.0.1', port), MyHTTPRequestHandler)
    
    print(f"""
╔════════════════════════════════════════════════════════╗
║  HTTP MCP Test UI Server                              ║
╠════════════════════════════════════════════════════════╣
║  Open in browser: http://localhost:8001                ║
║  Make sure HTTP MCP server is running on :8000         ║
║  Press CTRL+C to stop                                  ║
╚════════════════════════════════════════════════════════╝
    """)
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✓ Server stopped")
        sys.exit(0)
