# MCP Server Integration Guide

## Setup MCP Server for VS Code

### 1. Install MCP SDK (if not already installed)
```bash
.venv/bin/pip install mcp
```

### 2. Configure VS Code Settings

Add to your VS Code `settings.json` (or user MCP config):

```json
{
  "mcpServers": {
    "sql-agent": {
      "command": "/Users/radhruva/Desktop/LangGraph/.venv/bin/python",
      "args": [
        "/Users/radhruva/Desktop/LangGraph/mcp_server.py"
      ],
      "env": {
        "PYTHONPATH": "/Users/radhruva/Desktop/LangGraph"
      }
    }
  }
}
```

### 3. Test MCP Server

**Test standalone:**
```bash
.venv/bin/python mcp_server.py
```

**Test from VS Code:**
- Open GitHub Copilot Chat
- Use the `@sql-agent` mention to access tools

### 4. Available Tools

#### `query_database`
Execute natural language queries against Snowflake.

**Example:**
```
@sql-agent query_database "How many customers are in ASIA region?"
```

**Parameters:**
- `query` (required): Natural language question
- `session_id` (optional): Session ID for conversation tracking

#### `get_schema`
Retrieve database schema information.

**Example:**
```
@sql-agent get_schema
```

**Parameters:**
- `refresh` (optional): Force schema cache refresh

#### `get_conversation_history`
View recent conversation history.

**Example:**
```
@sql-agent get_conversation_history session_id="my_session" limit=5
```

**Parameters:**
- `session_id` (required): Session to retrieve
- `limit` (optional): Max interactions (default: 5)

### 5. Usage Examples

**Simple query:**
```
How many total orders do we have?
```

**Follow-up question:**
```
What's the average value of those orders?
```

**Schema exploration:**
```
What tables are available in the database?
```

**Summary request:**
```
Summarize the key metrics we discussed
```

### 6. Features

- ✅ Natural language to SQL conversion
- ✅ Safety validation (blocks DROP/DELETE/ALTER)
- ✅ Conversation memory across sessions
- ✅ Schema auto-discovery
- ✅ Follow-up question support
- ✅ Intelligent result formatting

### 7. Troubleshooting

**Server not starting:**
- Check Python path in config
- Verify .env file exists with credentials
- Test: `.venv/bin/python mcp_server.py`

**Import errors:**
- Ensure PYTHONPATH is set correctly
- Run: `.venv/bin/pip install -r requirements.txt`

**Connection errors:**
- Verify Snowflake credentials in `.env`
- Test connection: `.venv/bin/python scripts/quick_test.py`
