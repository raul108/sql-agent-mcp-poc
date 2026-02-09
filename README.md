# LangGraph SQL Agent - MCP POC

**Natural Language to SQL Agent** with Model Context Protocol (MCP) integration for Snowflake.

---

## 🎯 What This Does

AI-powered SQL agent that:
- Converts natural language questions to SQL queries
- Executes on Snowflake with safety validation
- Remembers conversation context for follow-ups
- Exposes tools via MCP for VS Code integration

**Data Source:** Snowflake TPC-H sample dataset (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)

---

## ✅ Implemented Features

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
├── mcp_server.py             # MCP server for VS Code integration
├── mcp_client.py             # Interactive MCP client
├── requirements.txt          # Python dependencies
├── .env                      # All configuration (gitignored)
│
├── src/                      # Core agent modules
│   ├── agent.py              # 6-node LangGraph workflow
│   ├── config.py             # Environment-based configuration
│   ├── memory.py             # SQLite conversation storage
│   ├── tools.py              # Snowflake integration + auto schema discovery
│   └── validator.py          # SQL safety validator
│
├── docs/
│   ├── MCP_SETUP.md          # MCP integration guide
│   └── README.md             # Additional documentation
│
└── scripts/
    └── run.sh                # Quick launcher
```

**Note:** Schema is auto-discovered from Snowflake INFORMATION_SCHEMA - no YAML files needed!

---

## 🚀 Quick Start---

## 🚀 Quick Start

### 1. Setup Environment

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Credentials

Create `.env` file with your credentials:
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
```

### 3. Run the Agent

**Interactive CLI:**
```bash
.venv/bin/python main.py
```

**MCP Client (Interactive Chat):**
```bash
.venv/bin/python mcp_client.py
```

**MCP Server (for VS Code):**
```bash
.venv/bin/python mcp_server.py
```
See [docs/MCP_SETUP.md](docs/MCP_SETUP.md) for VS Code configuration.

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
```bash
.venv/bin/python scripts/quick_test.py
```

**Tests:**
- ✅ Module imports
- ✅ Configuration loading
- ✅ Snowflake connection
- ✅ Agent query execution
- ✅ Conversation memory

### Example Test Queries

**Data exploration:**
- "How many customers are there?"
- "What tables are available?"
- "Show me the top 5 nations by customer count"

**Follow-up questions:**
- "What about orders?"
- "How does ASIA compare to AMERICA?"
- "Summarize what we discussed"

**Safety tests:**
- "Drop the customer table"
- "Delete all orders from 2024"

**Scope tests:**
- "What's the weather today?"
- "Tell me a joke"

---

## 🔧 Configuration

### Environment Variables (`.env`)
Sensitive credentials - never commit to git

### YAML Config (`config/config.yaml`)
Non-sensitive metadata and settings

### Schema Discovery
Auto-queries `INFORMATION_SCHEMA` on first use, then caches

---

## 📚 Documentation

- [MCP_SETUP.md](docs/MCP_SETUP.md) - VS Code MCP integration guide
- [README.md](docs/README.md) - Additional technical details

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
| MCP Integration | ✅ | VS Code tool exposure |
| Scope Detection | ✅ | Filters non-data questions |

---

## 📝 License

MIT License - Open Source

- 🤖 Natural language to SQL conversion using ChatGPT
- 🗄️ Snowflake database integration
- 📊 Schema-aware query generation
- 🔄 Interactive query mode

## Testing

**Test your connection:**
```bash
python scripts/test_connection.py
```

**Try sample queries:**
See `docs/test_queries.md` for a list of example queries

## Configuration

### Environment Variables (.env)
- `OPENAI_API_KEY`: Your OpenAI API key
- `SNOWFLAKE_*`: Snowflake connection parameters

### Schema Configuration (config/config.yaml)
Define your database schema and relationships to help the agent generate better queries.

## Architecture

The agent uses LangGraph to create a workflow:
1. **Analyze Query**: Converts natural language to SQL
2. **Execute SQL**: Runs query on Snowflake
3. **Respond**: Formats results for the user
