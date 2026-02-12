# LangGraph SQL Agent - MCP POC

**Natural Language to SQL Agent** with Model Context Protocol (MCP) integration for Snowflake.

**Status:** ✅ Production-Ready | 🔄 Actively Maintained | 📦 Fully Modularized

---

## 🎯 What This Does

AI-powered SQL agent that:
- Converts natural language questions to SQL queries
- Executes on Snowflake with safety validation
- Remembers conversation context for follow-ups
- Exposes tools via MCP for VS Code integration

**Data Source:** Snowflake TPC-H sample dataset (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)

---

## 📅 Recent Improvements (Feb 11, 2026)

### Code Quality & Architecture
- ✅ **Modularized Agent Package** - Organized `src/agent/` with clear separation of concerns:
  - `core.py` - Main agent orchestration
  - `nodes.py` - 6 workflow node implementations  
  - `prompts.py` - Centralized LLM prompts (easy to update)
  - `graph_builder.py` - LangGraph topology and compilation
- ✅ **Fixed Threading Issues** - SQLite in-memory database with persistent connections for multi-threaded execution
- ✅ **Session Management** - Fresh sessions by default, optional persistence

### Features & Reliability
- ✅ **History-Aware Queries** - Detects summary/reference questions and validates history availability
- ✅ **Smart Error Handling** - Prevents hallucination when no conversation history exists
- ✅ **Conversation Memory** - Both in-memory (default) and file-based persistence modes

---

## ✅ Implemented Features

### Session Management
- ✅ **Fresh Sessions by Default** - In-memory SQLite database clears on restart
- ✅ **Optional Persistence** - Set `PERSIST_MEMORY=true` to keep history across restarts
- ✅ **Thread-Safe Memory** - Multi-threaded LangGraph execution with persistent connections

### Core Agent (6-Node Workflow)
1. **Scope Detection** - Filters out non-data questions
2. **SQL Generation** - Natural language → SQL with schema context
3. **Safety Validation** - Blocks DROP/DELETE/ALTER/UPDATE operations
4. **Query Execution** - Snowflake integration with retry logic (max 3)
5. **Result Formatting** - Intelligent truncation for large datasets
6. **Response Generation** - User-friendly natural language answers

### Advanced Capabilities
- ✅ **Conversation Memory** - SQLite-based history tracking
- ✅ **Follow-up Questions** - Context from last 5 interactions
- ✅ **Schema Auto-Discovery** - Auto-queries INFORMATION_SCHEMA
- ✅ **Summary Support** - Answers from conversation history
- ✅ **MCP Integration** - Exposes tools to VS Code

---

## 📁 Project Structure

```
LangGraph/
├── main.py                    # Interactive CLI interface
├── README.md                  # This file
├── .gitignore                 # Git ignore rules (root level)
│
├── setup/                     # Configuration & dependencies
│   ├── .env                   # Credentials (gitignored)
│   ├── requirements.txt       # Python dependencies
│   └── SETUP.md               # Setup guide
│
├── data/                      # Runtime data & artifacts
│   └── conversation_history.db # Conversation history (when PERSIST_MEMORY=true)
│
├── src/                       # Core agent modules
│   ├── agent/                 # Agent package (modularized)
│   │   ├── __init__.py        # Package exports
│   │   ├── core.py            # Main SQLAgent class
│   │   ├── nodes.py           # 6-node workflow implementations
│   │   ├── prompts.py         # All LLM prompts (centralized)
│   │   └── graph_builder.py   # LangGraph construction & topology
│   ├── config.py              # Environment-based configuration
│   ├── memory.py              # SQLite conversation storage
│   ├── tools.py               # Snowflake integration + auto schema discovery
│   └── validator.py           # SQL safety validator
│
├── mcp_impl/                  # MCP HTTP Server & Flask Web UI
│   ├── app.py                 # Flask web interface (port 8001)
│   ├── server_http.py         # HTTP MCP server (port 8000)
│   ├── server_manager.py      # MCP server lifecycle management
│   └── response_formatter.py  # Response formatting for display
│
├── docs/                      # Documentation
│   ├── PROJECT_STRUCTURE.md   # Detailed codebase organization
│   ├── test_queries.md        # Example queries to test the agent
│   └── COMPLETE_WORKFLOW.md   # Workflow verification details
│
└── scripts/
    └── run.sh                 # Application launcher
```

---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r setup/requirements.txt
```

### 2. Configure Credentials

Create `setup/.env` file with your credentials:
```bash
# Snowflake
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=SNOWFLAKE_SAMPLE_DATA
SNOWFLAKE_SCHEMA=TPCH_SF1
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=ACCOUNTADMIN

# OpenAI
OPENAI_API_KEY=sk-...

# Optional: Persistent conversation history
PERSIST_MEMORY=false  # Set to true for file-based history
```

### 3. Run the Agent

**Web UI & MCP Server:**
```bash
.venv/bin/python mcp_impl/app.py
```

The application will start on:
- **Web UI**: http://localhost:8001 (Chat interface)
- **MCP Server**: http://localhost:8000 (JSON-RPC 2.0)

---

## 💡 Example Usage

### Interactive Mode

```
Enter your query: How many customers are there?

Generated SQL: SELECT COUNT(*) FROM CUSTOMER;
✓ Safety validation passed

There are 150,000 customers in the data.
```

### Follow-up Questions
```
Enter your query: How many orders?

Generated SQL: SELECT COUNT(*) FROM ORDERS;
✓ Safety validation passed

There are 1,500,000 orders in the database.

Enter your query: Summarize the key numbers we discussed

Using conversation history to answer...

Based on our conversation:
- Total customers: 150,000
- Total orders: 1,500,000
```

### Safety Features
```
Enter your query: Delete all old orders

Generated SQL: DELETE FROM ORDERS WHERE...
🛑 Safety Check Failed:
❌ BLOCKED: Query contains dangerous operations: DELETE

⚠️ Only SELECT queries are allowed for safety.
```

---

## 🏗️ Architecture

### 6-Node Workflow

```
┌─────────────┐
│ User Query  │
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Scope Detection │ ── Filter out-of-scope questions
└────────┬────────┘
         │
         ▼
┌──────────────────┐
│ SQL Generation   │ ── NL → SQL with schema context
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Safety Validator │ ── Block dangerous operations
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Execute Query    │ ── Snowflake execution (retry x3)
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Format Results   │ ── Intelligent truncation
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Generate Response│ ── Natural language answer
└──────────────────┘
```

### Data Flow

1. **Input:** Natural language question
2. **Scope Check:** Is it data-related?
3. **Schema Context:** Load table/column metadata
4. **SQL Generation:** GPT-4 with schema context
5. **Validation:** Safety checks (read-only enforcement)
6. **Execution:** Query Snowflake with retry logic
7. **Memory:** Store in SQLite for follow-ups
8. **Response:** Format results naturally

---

## 📊 Testing

### Quick Test Suite

**Test your connection:**
```bash
.venv/bin/python scripts/quick_test.py
```

**Try sample queries:**
See [docs/test_queries.md](docs/test_queries.md) for a list of example queries

---

## 🔧 Configuration

### Environment Variables (`.env`)
Sensitive credentials - never commit to git

### Session Management
- **Default Mode**: In-memory SQLite (fresh sessions on restart)
- **Persistent Mode**: Set `PERSIST_MEMORY=true` for file-based history

### Schema Discovery
Auto-queries `INFORMATION_SCHEMA` on first use

---

## 📚 Documentation

For more details, see the [docs](docs/) folder:

- [Project Structure](docs/PROJECT_STRUCTURE.md) - Detailed codebase organization
- [Test Queries](docs/test_queries.md) - Example queries to test the agent
- [Complete Workflow](docs/COMPLETE_WORKFLOW.md) - Workflow verification details

---

## 🎯 Key Features Summary

| Feature | Status | Description |
|---------|--------|-------------|
| Natural Language → SQL | ✅ | GPT-4 powered conversion |
| Safety Validation | ✅ | Blocks DROP/DELETE/ALTER |
| Schema Auto-Discovery | ✅ | Queries INFORMATION_SCHEMA |
| Conversation Memory | ✅ | SQLite-based history |
| Follow-up Questions | ✅ | Context from last 5 interactions |
| Retry Logic | ✅ | Max 3 attempts on errors |
| Fresh Sessions | ✅ | In-memory database by default |
| Persistent History | ✅ | Optional file-based storage |
| Scope Detection | ✅ | Filters non-data questions |

---

## 📝 License

MIT License - Open Source
