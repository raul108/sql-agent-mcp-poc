#!/usr/bin/env python3
"""
HTTP MCP Chat UI

A modular Flask app that:
1. Automatically starts the HTTP MCP server on port 8000
2. Serves a ChatGPT-like UI on port 8001
3. Proxies queries to the MCP server

Usage:
    python app.py

Then open: http://localhost:8001
"""

import os
import sys
import logging
from pathlib import Path

# Add parent directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import modular components
from mcp_impl.server_manager import MCPServerManager
from mcp_impl.response_formatter import ResponseFormatter

from flask import Flask, render_template_string, request, jsonify
import httpx


# ============================================================================
# Flask UI App
# ============================================================================

app = Flask(__name__)
mcp_manager = MCPServerManager()

# HTML Template - ChatGPT-like interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SQL Agent Chat</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #fff;
            height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }

        header h1 {
            font-size: 1.5em;
            margin-bottom: 5px;
        }

        header p {
            font-size: 0.9em;
            opacity: 0.9;
        }

        .status {
            padding: 10px 20px;
            background: #f0f4ff;
            border-bottom: 1px solid #ddd;
            font-size: 0.9em;
            color: #333;
        }

        .status.healthy {
            background: #d4edda;
            color: #155724;
        }

        .status.error {
            background: #f8d7da;
            color: #721c24;
        }

        .container {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            margin: 0 auto;
            width: 100%;
            padding: 20px;
        }

        .chat-messages {
            flex: 1;
            overflow-y: auto;
            margin-bottom: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            background: #f9f9f9;
        }

        .message {
            margin-bottom: 20px;
            display: flex;
            animation: slideIn 0.3s ease-out;
        }

        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(10px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }

        .message.user {
            justify-content: flex-end;
        }

        .message.assistant {
            justify-content: flex-start;
        }

        .message-content {
            max-width: 70%;
            padding: 12px 16px;
            border-radius: 12px;
            word-wrap: break-word;
            font-size: 0.95em;
            line-height: 1.6;
            white-space: pre-wrap;
        }

        .message.user .message-content {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 4px;
        }

        .message.assistant .message-content {
            background: #e9ecef;
            color: #333;
            border-bottom-left-radius: 4px;
        }

        .message.error .message-content {
            background: #f8d7da;
            color: #721c24;
        }

        .message.loading .message-content {
            background: #f0f0f0;
            color: #666;
        }

        .input-area {
            display: flex;
            gap: 10px;
        }

        input[type="text"] {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 0.95em;
            transition: border-color 0.3s;
        }

        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }

        button {
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: background 0.3s;
            font-size: 0.95em;
        }

        button:hover {
            background: #5568d3;
        }

        button:active {
            transform: translateY(1px);
        }

        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }

        .loading {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
            margin: 0 2px;
            animation: bounce 1.4s infinite;
        }

        .loading:nth-child(2) {
            animation-delay: 0.2s;
        }

        .loading:nth-child(3) {
            animation-delay: 0.4s;
        }

        @keyframes bounce {
            0%, 80%, 100% {
                opacity: 0.3;
                transform: scale(0.8);
            }
            40% {
                opacity: 1;
                transform: scale(1);
            }
        }

        .examples {
            text-align: center;
            color: #999;
            padding: 20px;
            font-size: 0.9em;
        }

        .example-query {
            background: #f0f4ff;
            padding: 10px 15px;
            border-radius: 6px;
            margin: 10px 5px;
            cursor: pointer;
            display: inline-block;
            transition: background 0.3s;
        }

        .example-query:hover {
            background: #e5ecff;
        }

        .timestamp {
            font-size: 0.8em;
            color: #999;
            margin-top: 5px;
        }
    </style>
</head>
<body>
    <header>
        <h1>🚀 SQL Agent Chat</h1>
        <p>Ask questions about your Snowflake database using natural language</p>
    </header>

    <div id="status" class="status">
        Checking server status...
    </div>

    <div class="container">
        <!-- Welcome message -->
        <div id="welcomeMessage" class="examples" style="margin-top: auto;">
            <p style="margin-bottom: 15px;">👋 Welcome! Ask me anything about your database.</p>
            <p style="margin-bottom: 15px;">Try these examples:</p>
            <div id="exampleQueries">
                <div class="example-query" onclick="setQuery('How many tables are in the database?')">
                    How many tables?
                </div>
                <div class="example-query" onclick="setQuery('Show me the database schema')">
                    Show schema
                </div>
                <div class="example-query" onclick="setQuery('What columns does the ORDERS table have?')">
                    ORDERS columns
                </div>
            </div>
        </div>

        <!-- Chat messages -->
        <div class="chat-messages" id="chatMessages" style="display:none;"></div>

        <!-- Input area -->
        <div class="input-area">
            <input 
                type="text" 
                id="queryInput" 
                placeholder="Ask a question... (e.g., 'How many customers?')"
                onkeypress="if(event.key==='Enter') sendQuery()"
            >
            <button id="sendBtn" onclick="sendQuery()">Send</button>
        </div>
    </div>

    <script>
        const MCP_URL = 'http://127.0.0.1:8000';
        const statusEl = document.getElementById('status');
        const chatEl = document.getElementById('chatMessages');
        const queryInput = document.getElementById('queryInput');
        const sendBtn = document.getElementById('sendBtn');
        const welcomeEl = document.getElementById('welcomeMessage');

        let isServerReady = false;

        // Check server health on load
        async function checkServerHealth() {
            try {
                const response = await fetch(`${MCP_URL}/health`);
                if (response.ok) {
                    const data = await response.json();
                    statusEl.textContent = `✓ Server healthy - ${data.database}`;
                    statusEl.className = 'status healthy';
                    isServerReady = true;
                    queryInput.focus();
                    return;
                }
            } catch (e) {
                // Server not ready yet
            }
            
            statusEl.textContent = '⏳ Server starting... (this may take a moment)';
            statusEl.className = 'status';
            
            // Retry after 2 seconds
            setTimeout(checkServerHealth, 2000);
        }

        function setQuery(query) {
            queryInput.value = query;
            queryInput.focus();
        }

        function showWelcome() {
            chatEl.style.display = 'none';
            welcomeEl.style.display = 'block';
        }

        function hideWelcome() {
            chatEl.style.display = 'block';
            welcomeEl.style.display = 'none';
        }

        function addMessage(text, isUser = true, isError = false) {
            hideWelcome();
            
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user' : 'assistant'} ${isError ? 'error' : ''}`;
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.textContent = text;
            
            messageDiv.appendChild(contentDiv);
            chatEl.appendChild(messageDiv);
            
            // Auto-scroll to bottom
            chatEl.scrollTop = chatEl.scrollHeight;
        }

        function addLoadingMessage() {
            hideWelcome();
            
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message loading assistant';
            messageDiv.id = 'loadingMessage';
            
            const contentDiv = document.createElement('div');
            contentDiv.className = 'message-content';
            contentDiv.innerHTML = '<span class="loading"></span><span class="loading"></span><span class="loading"></span>';
            
            messageDiv.appendChild(contentDiv);
            chatEl.appendChild(messageDiv);
            chatEl.scrollTop = chatEl.scrollHeight;
        }

        function removeLoadingMessage() {
            const loadingEl = document.getElementById('loadingMessage');
            if (loadingEl) {
                loadingEl.remove();
            }
        }

        async function sendQuery() {
            const query = queryInput.value.trim();
            if (!query) return;

            if (!isServerReady) {
                alert('Server is still starting. Please wait...');
                return;
            }

            // Disable input while processing
            queryInput.disabled = true;
            sendBtn.disabled = true;

            // Show user message
            addMessage(query, true);
            queryInput.value = '';

            // Show loading indicator
            addLoadingMessage();

            try {
                // Send to Flask backend, not directly to MCP
                const response = await fetch('/api/query', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ query })
                });

                removeLoadingMessage();

                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }

                const data = await response.json();

                if (data.error) {
                    addMessage(data.error, false, true);
                } else if (data.response) {
                    addMessage(data.response, false);
                } else {
                    addMessage(JSON.stringify(data, null, 2), false);
                }
            } catch (error) {
                removeLoadingMessage();
                addMessage(`Error: ${error.message}`, false, true);
            } finally {
                queryInput.disabled = false;
                sendBtn.disabled = false;
                queryInput.focus();
            }
        }

        // Initialize on page load
        window.addEventListener('load', () => {
            checkServerHealth();
        });
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the chat UI"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/query', methods=['POST'])
def query():
    """
    Process query through the HTTP MCP server
    
    Flow:
    1. Receive query from UI
    2. Send to HTTP MCP server (port 8000)
    3. Get response from agent
    4. Format response
    5. Return to UI
    """
    try:
        data = request.json
        query_text = data.get('query')
        
        if not query_text:
            return jsonify({'error': 'No query provided'}), 400
        
        # Forward to MCP server
        mcp_response = httpx.post(
            'http://127.0.0.1:8000/mcp',
            json={
                'jsonrpc': '2.0',
                'id': str(hash(query_text)),
                'method': 'tools/call',
                'params': {
                    'name': 'query_database',
                    'arguments': {'query': query_text}
                }
            },
            timeout=30
        )
        
        if mcp_response.status_code != 200:
            return jsonify({'error': f'Server error: {mcp_response.status_code}'}), 500
        
        response_data = mcp_response.json()
        
        # Extract the formatted response from MCP result
        if response_data.get('result') and response_data['result'].get('content'):
            formatted_response = response_data['result']['content'][0]['text']
            return jsonify({'response': formatted_response})
        else:
            return jsonify({'error': 'Unexpected response format'}), 500
            
    except Exception as e:
        logger.error(f"Query error: {e}")
        return jsonify({'error': f'Error: {str(e)}'}), 500


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Start MCP server in background
    success = mcp_manager.start()
    
    if not success:
        logger.error("Failed to start MCP server. Exiting.")
        sys.exit(1)
    
    # Print startup info
    print("\n" + "="*60)
    print("🚀 SQL Agent Chat UI")
    print("="*60)
    print(f"\n✓ MCP Server: http://127.0.0.1:8000")
    print(f"✓ Chat UI: http://127.0.0.1:8001")
    print(f"\n👉 Open your browser and go to: http://localhost:8001\n")
    print("="*60 + "\n")
    
    try:
        app.run(host='127.0.0.1', port=8001, debug=False, use_reloader=False)
    except KeyboardInterrupt:
        print("\n✓ Shutting down...")
        mcp_manager.stop()
