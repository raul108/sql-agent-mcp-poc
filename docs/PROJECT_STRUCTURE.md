# Project Structure & Active Components

**Focused Flask HTTP Implementation** - All files in this directory are actively used by the Flask app.

## Core Components

### MCP Implementation (`mcp_impl/`)
- **app.py** - Flask web UI server (port 8001)
  - Serves ChatGPT-like web interface
  - Auto-starts HTTP MCP server on port 8000
  - Proxies queries to MCP server
  - Key dependencies: server_manager, response_formatter

- **server_http.py** - HTTP MCP server (port 8000) 
  - Starlette ASGI application
  - Streamable HTTP transport
  - JSON-RPC 2.0 compatible
  - Exposes `query_database` tool via `/mcp` endpoint
  - Health check at `/health`

- **server_manager.py** - MCP server lifecycle manager
  - Singleton pattern (one instance per application)
  - Auto-start server when Flask app launches
  - Health checks before marking ready

- **response_formatter.py** - Formats agent responses
  - Converts agent.messages array to display-friendly text
  - Extracts SQL and final answers

### SQL Agent (`src/agent/`)

**Modularized agent package** - Organized for maintainability and clarity.

- **core.py** - Main SQLAgent class
  - Orchestrates initialization and workflow execution
  - Handles memory setup (in-memory by default, optional persistence)
  - Builds and invokes the LangGraph workflow

- **nodes.py** - 6 Workflow node implementations
  - `check_scope()` - Filters non-data questions
  - `analyze_query()` - NLU to SQL with history context
  - `validate_sql()` - Safety validation (blocks dangerous ops)
  - `execute_sql()` - Snowflake execution with retries
  - `format_results()` - Handles large result sets
  - `respond()` - Natural language response generation
  - `AgentState` - Workflow state definition

- **prompts.py** - Centralized LLM prompts
  - `get_scope_check_prompt()` - Query relevance check
  - `get_question_type_prompt()` - Summary vs new query
  - `get_sql_generation_prompt()` - SQL generation
  - `get_summary_response_prompt()` - History summaries
  - `get_response_formatting_prompt()` - NL formatting

- **graph_builder.py** - LangGraph construction
  - Graph topology definition
  - Node connections and flow
  - Graph compilation

- **__init__.py** - Package exports
  - Exposes `SQLAgent` for clean imports
  - `from src.agent import SQLAgent`

- **config.py** - Environment-based configuration
  - Loads from `.env` file only
  - Snowflake credentials
  - OpenAI API key

- **tools.py** - Snowflake database integration
  - SQL query execution
  - Schema auto-discovery from INFORMATION_SCHEMA
  - Schema caching for performance

- **memory.py** - SQLite conversation history
  - Supports both in-memory (`:memory:`) and file-based storage
  - Persistent connection for in-memory mode (avoids threading issues)
  - `check_same_thread=False` for multi-threaded LangGraph execution
  - Session-based isolation
  - Enables follow-up questions with context
  - Methods: `add_interaction()`, `get_recent_history()`, `format_history_for_context()`, `clear_session()`

- **validator.py** - SQL safety validation
  - Blocks DROP, DELETE, ALTER, UPDATE, INSERT
  - Read-only enforcement
  - Pattern matching for dangerous operations

## Configuration
- **.env** - Credentials and API keys (git-ignored)
  - SNOWFLAKE_* settings
  - OPENAI_API_KEY
- **PERSIST_MEMORY** (optional env var) - Set to `true` to keep conversation history across restarts
  - Default: `false` (in-memory, fresh session each restart)

## Data Storage
- **conversation_history.db** - SQLite database
  - Auto-created on first run
  - Stores conversation history per session

## Documentation
- **README.md** - Project overview and quick start
- **requirements.txt** - Python dependencies
- **test_queries.md** - Example test queries
- **docs/COMPLETE_WORKFLOW.md** - Detailed workflow explanation

## Architecture

```
┌─────────────────────────────────────────┐
│  Browser (http://localhost:8001)        │
└────────────────┬────────────────────────┘
                 │
       ┌─────────▼─────────┐
       │  Flask App (8001) │
       │    - app.py       │
       └────────┬──────────┘
                │
       ┌────────▼───────────────┐
       │ HTTP MCP Server (8000) │
       │  - server_http.py      │
       │  - server_manager.py   │
       └────────┬───────────────┘
                │
       ┌────────▼────────────────┐
       │   SQL Agent Workflow    │
       │   - agent.py (6 nodes)  │
       └────────┬────────────────┘
                │
       ┌────────▼────────────────┐
       │   Snowflake Database    │
       │   - tools.py            │
       └─────────────────────────┘
```

## Execution Flow

1. User opens `http://localhost:8001`
2. Flask app auto-starts HTTP MCP server
3. User enters natural language query
4. Flask `/api/query` endpoint receives query
5. Flask forwards to HTTP MCP server at `http://localhost:8000/mcp`
6. MCP server calls agent.run()
7. Agent executes 6-node workflow:
   - Check scope (is it data-related?)
   - Analyze and generate SQL
   - Validate for safety
   - Execute on Snowflake
   - Format results
   - Generate natural language response
8. Response returned to Flask, formatted for display
9. UI shows agent response with message history

## No Longer Included
- Stdio implementation (removed for Flask-only focus)
- HTTP client utilities (not needed for web interface)
- Test scripts (moved to inline testing)
- Deployment scripts (use direct commands instead)

## Running the Application

```bash
# Make sure venv is activated
source .venv/bin/activate

# Start the Flask app (auto-starts MCP server)
python mcp_impl/app.py

# Opens at http://localhost:8001
```

Both servers start automatically:
- Flask UI: http://localhost:8001
- HTTP MCP: http://localhost:8000/mcp (internal use)

---

**Total Active Files:** 14 Python files + config/docs
**Lines of Code:** ~2,000 (agent, tools, server, UI)
**External Dependencies:** LangChain, LangGraph, Snowflake, Starlette, Flask, httpx
