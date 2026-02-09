# Complete Project Workflow - SQL Agent + MCP Integration

**Purpose:** End-to-end explanation of how the SQL Agent works from user input to response, with all features and Python code mappings.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Complete Workflow (Step-by-Step)](#complete-workflow)
3. [Feature Breakdown](#feature-breakdown)
4. [Code Architecture](#code-architecture)
5. [Example Execution Trace](#example-execution-trace)

---

## System Overview

### Architecture Layers

```
┌─────────────────────────────────────────────────────┐
│  Layer 1: User Interface                            │
│  - MCP Client (mcp_client.py)                       │
│  - Terminal/VS Code                                 │
└─────────────────┬───────────────────────────────────┘
                  │ stdio transport
┌─────────────────▼───────────────────────────────────┐
│  Layer 2: Protocol Adapter                          │
│  - MCP Server (mcp_server.py)                       │
│  - Tool: query_database                             │
└─────────────────┬───────────────────────────────────┘
                  │ function call
┌─────────────────▼───────────────────────────────────┐
│  Layer 3: Agent Orchestration                       │
│  - SQLAgent (src/agent.py)                          │
│  - 6-node LangGraph workflow                        │
└──┬──────┬──────┬──────┬──────┬──────────────────────┘
   │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼
┌────┐ ┌────┐ ┌────┐ ┌────┐ ┌────────┐
│LLM │ │SF  │ │Val │ │Mem │ │Config  │
│GPT4│ │Tool│ │idr │ │ory │ │.env    │
└────┘ └────┘ └────┘ └────┘ └────────┘
  │      │      │      │
  │      │      │      └─> SQLite DB
  │      │      └─> src/validator.py
  │      └─> src/tools.py (Snowflake)
  └─> OpenAI API
```

**Data Flow:** User → MCP Client → MCP Server → Agent → [LLM + Snowflake + Memory] → Response

---

## Complete Workflow

### End-to-End Flow (Example: "How many customers?")

```
┌──────────────────────────────────────────────────────┐
│ STEP 1: User Input                                   │
├──────────────────────────────────────────────────────┤
│ Location: Terminal or VS Code                        │
│ User types: "How many customers?"                    │
│ File: mcp_client.py, line 78                         │
│ Function: run_interactive_client()                   │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ STEP 2: MCP Client Sends Request                     │
├──────────────────────────────────────────────────────┤
│ File: mcp_client.py, lines 83-88                     │
│ Function: session.call_tool()                        │
│                                                      │
│ Code:                                                │
│   result = await session.call_tool(                 │
│       "query_database",                             │
│       {"query": "How many customers?",              │
│        "session_id": SESSION_ID}                    │
│   )                                                  │
│                                                      │
│ Transport: stdio (stdin/stdout pipes)               │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ STEP 3: MCP Server Receives Request                  │
├──────────────────────────────────────────────────────┤
│ File: mcp_server.py, lines 61-95                     │
│ Function: call_tool()                                │
│                                                      │
│ Code:                                                │
│   @app.call_tool()                                  │
│   async def call_tool(name: str, arguments: dict):  │
│       if name == "query_database":                  │
│           query = arguments["query"]                │
│           session_id = arguments.get("session_id")  │
│           result = agent.run(query, session_id)     │
│                                                      │
│ Action: Routes to SQLAgent.run()                    │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ STEP 4: Agent Initialization                         │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, lines 423-450                    │
│ Function: SQLAgent.run()                             │
│                                                      │
│ Code:                                                │
│   def run(self, query: str, session_id: str):       │
│       if session_id is None:                        │
│           session_id = str(uuid.uuid4())            │
│                                                      │
│       initial_state = {                             │
│           "messages": [],                           │
│           "query": query,                           │
│           "sql_result": "",                         │
│           "next_action": "",                        │
│           "retry_count": 0,                         │
│           "is_in_scope": True,                      │
│           "session_id": session_id                  │
│       }                                              │
│                                                      │
│       result = self.graph.invoke(initial_state)     │
│                                                      │
│ Action: Starts LangGraph workflow                   │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ NODE 1: Scope Detection                              │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, lines 119-156                    │
│ Function: check_scope()                              │
│                                                      │
│ Purpose: Filter out non-data questions              │
│                                                      │
│ Code:                                                │
│   prompt = f"""Determine if this question is        │
│   related to querying database...                   │
│   Question: {query}                                 │
│   Answer with ONLY 'yes' or 'no'"""                │
│                                                      │
│   response = self.llm.invoke(prompt)                │
│   is_in_scope = response.content == "yes"           │
│                                                      │
│ LLM Call: GPT-4 (temperature=0)                     │
│ Input: "How many customers?"                        │
│ Output: "yes"                                       │
│                                                      │
│ State Update: is_in_scope = True                    │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ NODE 2: SQL Generation                               │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, lines 158-240                    │
│ Function: analyze_query()                            │
│                                                      │
│ Sub-Step 2.1: Get Schema Info                       │
│   File: src/tools.py, lines 119-127                 │
│   Function: get_schema_info()                       │
│                                                      │
│   Code:                                              │
│     if use_cache and self._schema_cache:            │
│         return self._schema_cache                   │
│     schema_info = self._discover_schema()           │
│     self._schema_cache = schema_info                │
│                                                      │
│   ✓ Cache Check: Returns cached schema (fast)      │
│                                                      │
│ Sub-Step 2.2: Get Conversation History              │
│   File: src/memory.py, lines 94-130                 │
│   Function: format_history_for_context()            │
│                                                      │
│   Code:                                              │
│     history = self.get_recent_history(              │
│         session_id, limit=5                         │
│     )                                                │
│                                                      │
│   Query SQLite:                                     │
│     SELECT * FROM conversations                     │
│     WHERE session_id = ?                            │
│     ORDER BY timestamp DESC LIMIT 5                 │
│                                                      │
│   Result: Last 5 interactions (if any)              │
│                                                      │
│ Sub-Step 2.3: Generate SQL with GPT-4               │
│   File: src/agent.py, lines 190-215                 │
│                                                      │
│   Prompt Construction:                              │
│     - User query: "How many customers?"            │
│     - Database schema: (8 TPC-H tables)            │
│     - Conversation history: (previous queries)      │
│     - Instructions: Generate valid SQL             │
│                                                      │
│   LLM Call: GPT-4                                   │
│   Output: "SELECT COUNT(*) FROM CUSTOMER"          │
│                                                      │
│ State Update: next_action = SQL query              │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ NODE 3: Safety Validation                            │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, lines 242-278                    │
│ Function: validate_sql()                             │
│                                                      │
│ Calls: src/validator.py                             │
│   File: src/validator.py, lines 1-69                │
│   Function: is_safe_query()                         │
│                                                      │
│   Code:                                              │
│     DANGEROUS_KEYWORDS = [                          │
│         'DROP', 'DELETE', 'ALTER', 'UPDATE',       │
│         'INSERT', 'TRUNCATE', 'CREATE', 'GRANT'    │
│     ]                                                │
│                                                      │
│     sql_upper = sql.upper()                         │
│     for keyword in DANGEROUS_KEYWORDS:              │
│         if keyword in sql_upper:                    │
│             return False, f"Blocked: {keyword}"     │
│                                                      │
│   Check: "SELECT COUNT(*) FROM CUSTOMER"           │
│   Result: ✓ SAFE (no dangerous keywords)           │
│                                                      │
│ If BLOCKED:                                         │
│   state["sql_result"] = "BLOCKED: <reason>"        │
│   Skip execution                                    │
│                                                      │
│ If SAFE:                                            │
│   Continue to execution                             │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ NODE 4: Query Execution                              │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, lines 280-320                    │
│ Function: execute_sql_node()                         │
│                                                      │
│ Retry Logic (max 3 attempts):                       │
│                                                      │
│ Attempt 1:                                          │
│   File: src/tools.py, lines 40-90                   │
│   Function: SnowflakeSQLTool.execute_query()        │
│                                                      │
│   Code:                                              │
│     conn = snowflake.connector.connect(             │
│         account=config['account'],                  │
│         user=config['user'],                        │
│         password=config['password'],                │
│         warehouse=config['warehouse'],              │
│         database=config['database'],                │
│         schema=config['schema']                     │
│     )                                                │
│                                                      │
│     cursor = conn.cursor()                          │
│     cursor.execute(sql_query)                       │
│     results = cursor.fetchall()                     │
│                                                      │
│   Snowflake Query:                                  │
│     SELECT COUNT(*) FROM CUSTOMER                   │
│                                                      │
│   Result: [(150000,)]                               │
│                                                      │
│ If Error (connection timeout, syntax error):        │
│   retry_count += 1                                  │
│   if retry_count < 3:                               │
│       Re-execute from Node 4                        │
│   else:                                              │
│       state["sql_result"] = "Error: ..."           │
│                                                      │
│ If Success:                                         │
│   state["sql_result"] = "150000"                   │
│   Continue to formatting                            │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ NODE 5: Result Formatting                            │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, lines 322-348                    │
│ Function: format_results()                           │
│                                                      │
│ Purpose: Handle large results intelligently         │
│                                                      │
│ Code:                                                │
│   sql_result = state["sql_result"]                 │
│   results = eval(sql_result)  # or parse           │
│                                                      │
│   if len(results) > 10:                             │
│       # Return SQL instead of data                  │
│       formatted = f"Too many rows. SQL:\\n{sql}"   │
│   else:                                              │
│       # Format as table                             │
│       formatted = tabulate(results)                 │
│                                                      │
│ Example Result:                                     │
│   "150000" → Keep as is (single value)             │
│                                                      │
│ State Update: sql_result = formatted result         │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ NODE 6: Natural Language Response                    │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, lines 350-421                    │
│ Function: respond()                                  │
│                                                      │
│ Sub-Step 6.1: Generate NL Response                  │
│   LLM Call: GPT-4                                   │
│                                                      │
│   Prompt:                                            │
│     User asked: "How many customers?"              │
│     SQL Results: "150000"                           │
│     Provide clear, natural language answer.        │
│                                                      │
│   Output: "There are 150,000 customers in the      │
│            database."                               │
│                                                      │
│ Sub-Step 6.2: Save to Memory                        │
│   File: src/memory.py, lines 62-92                 │
│   Function: add_interaction()                       │
│                                                      │
│   Code:                                              │
│     conn = sqlite3.connect("conversation_history.db")│
│     cursor.execute("""                              │
│         INSERT INTO conversations                   │
│         (session_id, timestamp, user_query,        │
│          generated_sql, result_summary)            │
│         VALUES (?, ?, ?, ?, ?)                     │
│     """, (session_id, timestamp, query, sql,       │
│               result))                              │
│                                                      │
│   SQLite Insert:                                    │
│     session_id: "mcp_client_20260209_143022"       │
│     user_query: "How many customers?"              │
│     generated_sql: "SELECT COUNT(*) FROM CUSTOMER" │
│     result_summary: "150000"                        │
│     timestamp: "2026-02-09T14:30:45"               │
│                                                      │
│ State Update:                                       │
│   messages.append({                                 │
│       "role": "assistant",                         │
│       "content": "There are 150,000 customers..."  │
│   })                                                │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ STEP 5: Agent Returns Result                         │
├──────────────────────────────────────────────────────┤
│ File: src/agent.py, line 448                         │
│                                                      │
│ Code:                                                │
│   return result  # Final state with messages        │
│                                                      │
│ Returned State:                                     │
│   {                                                  │
│     "messages": [                                   │
│       {"role": "assistant",                        │
│        "content": "There are 150,000 customers..."}│
│     ],                                               │
│     "query": "How many customers?",                │
│     "sql_result": "150000",                        │
│     "next_action": "SELECT COUNT(*) FROM CUSTOMER",│
│     "retry_count": 0,                              │
│     "is_in_scope": True,                           │
│     "session_id": "mcp_client_20260209_143022"     │
│   }                                                  │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ STEP 6: MCP Server Returns to Client                 │
├──────────────────────────────────────────────────────┤
│ File: mcp_server.py, lines 80-95                     │
│                                                      │
│ Code:                                                │
│   response = result['messages'][-1]['content']      │
│   return [TextContent(                              │
│       type="text",                                  │
│       text=response                                 │
│   )]                                                 │
│                                                      │
│ MCP Response:                                       │
│   "There are 150,000 customers in the database."   │
│                                                      │
│ Transport: stdio back to client                     │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│ STEP 7: Client Displays Response                     │
├──────────────────────────────────────────────────────┤
│ File: mcp_client.py, lines 90-92                     │
│                                                      │
│ Code:                                                │
│   for content in result.content:                    │
│       print(f"\\n{content.text}\\n")                │
│                                                      │
│ Terminal Output:                                    │
│   Agent: There are 150,000 customers in the        │
│          database.                                  │
└──────────────────────────────────────────────────────┘
```

**Total Time:** ~3-5 seconds (1s schema cache, 2s GPT-4, 1s Snowflake, 1s formatting)

---

## Feature Breakdown

### Feature 1: Scope Detection

**Purpose:** Reject non-data questions ("Tell me a joke", "What's the weather?")

**Implementation:**
- **File:** [src/agent.py](../src/agent.py) lines 119-156
- **Function:** `check_scope(state)`
- **Technique:** LLM classification (yes/no)
- **Prompt:** "Is this question related to database queries?"

**Example:**
```python
# User: "Tell me a joke"
is_in_scope = False
response = "I'm a SQL agent designed to answer database questions."
```

**Benefits:**
- Prevents wasted Snowflake queries
- Clear user expectations
- Saves API costs

---

### Feature 2: Safety Validation

**Purpose:** Block dangerous operations (DROP, DELETE, ALTER)

**Implementation:**
- **File:** [src/validator.py](../src/validator.py) lines 1-69
- **Function:** `is_safe_query(sql)`
- **Technique:** Keyword detection + regex

**Code:**
```python
DANGEROUS_KEYWORDS = [
    'DROP', 'DELETE', 'ALTER', 'UPDATE',
    'INSERT', 'TRUNCATE', 'CREATE', 'GRANT'
]

def is_safe_query(sql: str) -> tuple[bool, str]:
    sql_upper = sql.upper()
    for keyword in DANGEROUS_KEYWORDS:
        if keyword in sql_upper:
            return False, f"BLOCKED: {keyword} operations not allowed"
    return True, "Safe"
```

**Example:**
```python
# User: "DELETE all customers"
# Generated SQL: "DELETE FROM CUSTOMER"
is_safe, reason = validator.is_safe_query(sql)
# Result: (False, "BLOCKED: DELETE operations not allowed")
```

**Triple-Layer Protection:**
1. **Layer 1:** Keyword validation (Python code)
2. **Layer 2:** Scope detection (LLM filter)
3. **Layer 3:** Database permissions (Snowflake GRANT SELECT only)

---

### Feature 3: Conversation Memory

**Purpose:** Enable follow-up questions with context

**Implementation:**
- **Storage:** SQLite database (`conversation_history.db`)
- **File:** [src/memory.py](../src/memory.py)
- **Functions:**
  - `add_interaction()` - Save query/SQL/result
  - `get_recent_history()` - Retrieve last N interactions
  - `format_history_for_context()` - Format for LLM prompt

**Database Schema:**
```sql
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    user_query TEXT NOT NULL,
    generated_sql TEXT,
    result_summary TEXT,
    is_successful BOOLEAN DEFAULT 1
)
```

**Example Flow:**
```python
# Turn 1
User: "How many customers?"
→ Saves: query="How many customers?", sql="SELECT COUNT(*) FROM CUSTOMER", result="150000"

# Turn 2
User: "What about orders?"
→ Retrieves: Last 5 interactions (includes Turn 1)
→ LLM sees: "Previous query was about customer count, now asking about orders"
→ Generates: "SELECT COUNT(*) FROM ORDERS"
```

**Code:**
```python
# Save interaction (src/memory.py:62-92)
def add_interaction(self, session_id, user_query, generated_sql, result_summary):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO conversations 
        (session_id, timestamp, user_query, generated_sql, result_summary)
        VALUES (?, ?, ?, ?, ?)
    """, (session_id, datetime.now().isoformat(), user_query, 
          generated_sql, result_summary))
    conn.commit()
    conn.close()

# Retrieve history (src/memory.py:94-130)
def get_recent_history(self, session_id, limit=5):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM conversations
        WHERE session_id = ?
        ORDER BY timestamp DESC LIMIT ?
    """, (session_id, limit))
    results = cursor.fetchall()
    conn.close()
    return results
```

**Session Isolation:**
- Each client gets unique `session_id`
- No cross-contamination between users
- Multiple concurrent sessions supported

---

### Feature 4: Schema Auto-Discovery

**Purpose:** Dynamically learn database structure (no manual config)

**Implementation:**
- **File:** [src/tools.py](../src/tools.py) lines 92-117
- **Function:** `_discover_schema_from_snowflake()`
- **Technique:** Query `INFORMATION_SCHEMA` system tables

**Code:**
```python
def _discover_schema_from_snowflake(self) -> str:
    """Query Snowflake to get table/column information."""
    conn = snowflake.connector.connect(**config)
    cursor = conn.cursor()
    
    # Get all tables in schema
    cursor.execute("""
        SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'TPCH_SF1'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """)
    
    results = cursor.fetchall()
    
    # Format as text
    schema_info = "Database Schema:\\n\\n"
    for table, column, dtype in results:
        schema_info += f"{table}.{column} ({dtype})\\n"
    
    return schema_info
```

**Output Example:**
```
Database Schema:

CUSTOMER.C_CUSTKEY (NUMBER)
CUSTOMER.C_NAME (VARCHAR)
CUSTOMER.C_ADDRESS (VARCHAR)
CUSTOMER.C_NATIONKEY (NUMBER)
...
ORDERS.O_ORDERKEY (NUMBER)
ORDERS.O_CUSTKEY (NUMBER)
ORDERS.O_TOTALPRICE (NUMBER)
...
```

**Caching:**
- **File:** [src/tools.py](../src/tools.py) line 28
- **Variable:** `self._schema_cache = None`
- First call: 2-3 seconds (queries Snowflake)
- Subsequent calls: <1ms (returns cached)

**Benefits:**
- No YAML configuration needed
- Adapts to schema changes automatically
- Works with any Snowflake database

---

### Feature 5: Error Retry Logic

**Purpose:** Handle transient failures (timeouts, locks)

**Implementation:**
- **File:** [src/agent.py](../src/agent.py) lines 280-320
- **Function:** `execute_sql_node()`
- **Max Retries:** 3 attempts

**Code:**
```python
def execute_sql_node(self, state: AgentState):
    retry_count = state.get("retry_count", 0)
    
    try:
        result = self.sql_tool.execute_query(sql)
        state["sql_result"] = result
        return state
        
    except Exception as e:
        if retry_count < 3:
            # Retry
            state["retry_count"] = retry_count + 1
            print(f"⚠️  Retry {retry_count + 1}/3...")
            return self.execute_sql_node(state)  # Recursive retry
        else:
            # Max retries exceeded
            state["sql_result"] = f"Error after 3 attempts: {str(e)}"
            return state
```

**Handles:**
- Network timeouts
- Connection pool exhaustion
- Temporary Snowflake unavailability
- Database locks

**Example:**
```
Attempt 1: Connection timeout
  ↓
Attempt 2: Connection timeout
  ↓
Attempt 3: ✓ Success
  ↓
Returns result
```

---

### Feature 6: Large Result Handling

**Purpose:** Don't return 600,000 rows to user

**Implementation:**
- **File:** [src/agent.py](../src/agent.py) lines 322-348
- **Function:** `format_results()`
- **Threshold:** 10 rows

**Code:**
```python
def format_results(self, state):
    results = state["sql_result"]
    
    if isinstance(results, list) and len(results) > 10:
        # Too many rows - return SQL instead
        sql = state["next_action"]
        formatted = f"""This query returns {len(results)} rows.
        
Instead of showing all data, here's the SQL:
```sql
{sql}
```

You can use this SQL to explore the data further."""
        
        state["sql_result"] = formatted
    else:
        # Format as table
        formatted = tabulate(results, headers="keys")
        state["sql_result"] = formatted
    
    return state
```

**Example:**
```python
# User: "Show all line items"
# Result: 6,001,215 rows

Response:
"This query returns 6,001,215 rows. Instead of showing all data,
here's the SQL:

SELECT * FROM LINEITEM

You can use this SQL to explore the data further."
```

---

### Feature 7: MCP Protocol Integration

**Purpose:** Universal interface for any MCP client

**Implementation:**
- **Server File:** [mcp_server.py](../mcp_server.py)
- **Client File:** [mcp_client.py](../mcp_client.py)
- **Protocol:** Model Context Protocol (stdio transport)

**Server Code:**
```python
from mcp.server import Server
from mcp.server.stdio import stdio_server

app = Server("sql-agent-mcp")

@app.list_tools()
async def list_tools():
    return [
        Tool(
            name="query_database",
            description="Execute natural language queries on Snowflake",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "session_id": {"type": "string"}
                },
                "required": ["query"]
            }
        )
    ]

@app.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query_database":
        result = agent.run(
            arguments["query"],
            arguments.get("session_id")
        )
        response = result['messages'][-1]['content']
        return [TextContent(type="text", text=response)]
```

**Client Code:**
```python
from mcp.client.session import ClientSession
from mcp.client.stdio import stdio_client

# Connect to server
server_params = StdioServerParameters(
    command=".venv/bin/python",
    args=["mcp_server.py"]
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        await session.initialize()
        
        # Call tool
        result = await session.call_tool(
            "query_database",
            {"query": "How many customers?"}
        )
        
        print(result.content[0].text)
```

**Benefits:**
- **Write once, use everywhere:** Single agent works with unlimited clients
- **Future interfaces:** VS Code, Webex, Slack (zero agent changes)
- **Standard protocol:** Industry-standard communication

---

## Code Architecture

### File Structure & Responsibilities

```
LangGraph/
│
├── mcp_server.py (134 lines)
│   ├── Purpose: MCP protocol adapter
│   ├── Exposes: query_database tool
│   ├── Depends on: src/agent.py, src/config.py
│   └── Transport: stdio
│
├── mcp_client.py (104 lines)
│   ├── Purpose: Interactive terminal client
│   ├── Connects to: mcp_server.py
│   └── Features: Chat loop, session management
│
├── main.py
│   ├── Purpose: Direct CLI (no MCP)
│   └── Usage: python main.py
│
├── src/
│   ├── agent.py (450 lines) ⭐ CORE ORCHESTRATION
│   │   ├── Class: SQLAgent
│   │   ├── Workflow: 6 LangGraph nodes
│   │   ├── Functions:
│   │   │   ├── check_scope() - Node 1
│   │   │   ├── analyze_query() - Node 2
│   │   │   ├── validate_sql() - Node 3
│   │   │   ├── execute_sql_node() - Node 4
│   │   │   ├── format_results() - Node 5
│   │   │   └── respond() - Node 6
│   │   └── Dependencies: tools, validator, memory, LLM
│   │
│   ├── tools.py (193 lines) ⭐ SNOWFLAKE INTEGRATION
│   │   ├── Class: SnowflakeSQLTool
│   │   ├── Functions:
│   │   │   ├── execute_query() - Run SQL
│   │   │   ├── get_schema_info() - Schema discovery
│   │   │   ├── _discover_schema_from_snowflake() - Query INFORMATION_SCHEMA
│   │   │   └── clear_schema_cache() - Reset cache
│   │   └── Caching: _schema_cache (in-memory)
│   │
│   ├── memory.py (202 lines) ⭐ CONVERSATION STORAGE
│   │   ├── Class: ConversationMemory
│   │   ├── Database: SQLite (conversation_history.db)
│   │   ├── Functions:
│   │   │   ├── add_interaction() - Save query/SQL/result
│   │   │   ├── get_recent_history() - Retrieve last N
│   │   │   ├── format_history_for_context() - Format for LLM
│   │   │   └── _init_database() - Create tables
│   │   └── Isolation: session_id based
│   │
│   ├── validator.py (69 lines) ⭐ SAFETY CHECKS
│   │   ├── Class: SQLValidator
│   │   ├── Functions:
│   │   │   ├── is_safe_query() - Keyword detection
│   │   │   ├── check_keywords() - Pattern matching
│   │   │   └── validate_structure() - Syntax checks
│   │   └── Blocks: DROP, DELETE, ALTER, UPDATE, INSERT
│   │
│   └── config.py (84 lines) ⭐ CONFIGURATION
│       ├── Class: Config
│       ├── Source: .env file only (no YAML)
│       ├── Functions:
│       │   ├── get_snowflake_config() - DB credentials
│       │   └── get_openai_config() - API key + model
│       └── Validation: Checks required vars
│
├── .env
│   ├── SNOWFLAKE_ACCOUNT
│   ├── SNOWFLAKE_USER
│   ├── SNOWFLAKE_PASSWORD
│   ├── SNOWFLAKE_WAREHOUSE
│   ├── SNOWFLAKE_DATABASE
│   ├── SNOWFLAKE_SCHEMA
│   ├── OPENAI_API_KEY
│   └── OPENAI_MODEL
│
└── conversation_history.db (SQLite)
    └── Table: conversations
        ├── id (PK)
        ├── session_id
        ├── timestamp
        ├── user_query
        ├── generated_sql
        ├── result_summary
        └── is_successful
```

### Dependency Graph

```
mcp_client.py
    └─> mcp_server.py (stdio)
            └─> src/agent.py (SQLAgent.run)
                    ├─> src/config.py (Config)
                    ├─> src/tools.py (SnowflakeSQLTool)
                    │       └─> snowflake.connector
                    ├─> src/validator.py (SQLValidator)
                    ├─> src/memory.py (ConversationMemory)
                    │       └─> sqlite3
                    └─> langchain_openai (ChatOpenAI)
                            └─> OpenAI API (GPT-4)
```

---

## Example Execution Trace

### Scenario: Follow-Up Question

**Conversation:**
```
User: "How many customers are from China?"
Agent: "There are 19,050 customers from China."

User: "What about United States?"
Agent: "There are 15,023 customers from United States."
```

### Detailed Trace

**Turn 1: "How many customers are from China?"**

```
1. mcp_client.py:83
   - Sends: {"query": "How many customers are from China?", "session_id": "abc123"}

2. mcp_server.py:75
   - Receives MCP request
   - Calls: agent.run(query, session_id)

3. agent.py:435
   - Initializes state with query
   - Invokes: self.graph.invoke(initial_state)

4. agent.py:119 (Node 1: check_scope)
   - LLM Call: "Is this about database?"
   - Response: "yes"
   - is_in_scope = True

5. agent.py:158 (Node 2: analyze_query)
   - tools.get_schema_info() → Returns cached schema
   - memory.format_history_for_context("abc123", 5) → "No previous history"
   - LLM Call: Generate SQL
   - Prompt:
     ```
     Database schema: CUSTOMER.C_CUSTKEY, C_NAME, C_NATIONKEY...
     Question: How many customers are from China?
     Generate SQL:
     ```
   - Response: 
     ```sql
     SELECT COUNT(*) 
     FROM CUSTOMER C
     JOIN NATION N ON C.C_NATIONKEY = N.N_NATIONKEY
     WHERE N.N_NAME = 'CHINA'
     ```

6. agent.py:242 (Node 3: validate_sql)
   - validator.is_safe_query(sql)
   - Check: No DROP/DELETE/ALTER
   - Result: ✓ SAFE

7. agent.py:280 (Node 4: execute_sql)
   - tools.execute_query(sql)
   - Snowflake connection → Execute
   - Result: [(19050,)]
   - retry_count = 0 (no errors)

8. agent.py:322 (Node 5: format_results)
   - Results: 1 row (< 10)
   - Keeps as-is: "19050"

9. agent.py:350 (Node 6: respond)
   - LLM Call: "Provide natural language answer"
   - Prompt:
     ```
     User asked: How many customers are from China?
     SQL Results: 19050
     Answer:
     ```
   - Response: "There are 19,050 customers from China."
   
   - memory.add_interaction():
     ```sql
     INSERT INTO conversations VALUES (
       'abc123',
       '2026-02-09T14:30:00',
       'How many customers are from China?',
       'SELECT COUNT(*) FROM CUSTOMER C JOIN NATION N...',
       '19050'
     )
     ```

10. mcp_server.py:90
    - Extracts: result['messages'][-1]['content']
    - Returns: [TextContent(text="There are 19,050 customers from China.")]

11. mcp_client.py:91
    - Prints: "Agent: There are 19,050 customers from China."
```

**Turn 2: "What about United States?"**

```
1. mcp_client.py:83
   - Sends: {"query": "What about United States?", "session_id": "abc123"}
   ⚠️  SAME session_id (memory will be used)

2. agent.py:158 (Node 2: analyze_query)
   - memory.format_history_for_context("abc123", 5)
   - SQLite Query:
     ```sql
     SELECT * FROM conversations
     WHERE session_id = 'abc123'
     ORDER BY timestamp DESC LIMIT 5
     ```
   - Result:
     ```
     Previous Q: "How many customers are from China?"
     Previous SQL: "SELECT COUNT(*) FROM CUSTOMER C JOIN NATION N..."
     Previous Result: "19050"
     ```
   
   - LLM Prompt:
     ```
     Conversation History:
     User: How many customers are from China?
     SQL: SELECT COUNT(*) FROM CUSTOMER C JOIN NATION N...
     Result: 19050
     
     Database schema: CUSTOMER.C_CUSTKEY, C_NAME, C_NATIONKEY...
     
     User question: What about United States?
     
     Generate SQL:
     ```
   
   - LLM Response:
     ```sql
     SELECT COUNT(*) 
     FROM CUSTOMER C
     JOIN NATION N ON C.C_NATIONKEY = N.N_NATIONKEY
     WHERE N.N_NAME = 'UNITED STATES'
     ```
     
     ✓ LLM understood "What about" = same pattern, different country

3-9. [Same validation, execution, formatting, response steps]

10. memory.add_interaction():
    ```sql
    INSERT INTO conversations VALUES (
      'abc123',  ← Same session
      '2026-02-09T14:30:15',
      'What about United States?',
      'SELECT COUNT(*) FROM CUSTOMER C JOIN NATION N WHERE N.N_NAME = ''UNITED STATES''',
      '15023'
    )
    ```

11. Returns: "There are 15,023 customers from United States."
```

**Key Insight:** Turn 2 works because:
- Same `session_id` retrieves Turn 1 from SQLite
- LLM sees previous query pattern
- Understands "What about" refers to same question structure

---

## Summary: All Features Mapped to Code

| Feature | File | Function | Lines |
|---------|------|----------|-------|
| **Scope Detection** | agent.py | check_scope() | 119-156 |
| **SQL Generation** | agent.py | analyze_query() | 158-240 |
| **Safety Validation** | validator.py | is_safe_query() | 15-40 |
| **Query Execution** | tools.py | execute_query() | 40-90 |
| **Retry Logic** | agent.py | execute_sql_node() | 280-320 |
| **Result Formatting** | agent.py | format_results() | 322-348 |
| **NL Response** | agent.py | respond() | 350-421 |
| **Conversation Memory** | memory.py | add_interaction() | 62-92 |
| | memory.py | get_recent_history() | 94-130 |
| **Schema Discovery** | tools.py | _discover_schema() | 92-117 |
| **Schema Caching** | tools.py | get_schema_info() | 119-127 |
| **MCP Server** | mcp_server.py | call_tool() | 61-95 |
| **MCP Client** | mcp_client.py | run_interactive() | 35-104 |
| **Configuration** | config.py | get_snowflake_config() | 30-50 |

---

**Total Code:** ~1,300 lines across 7 Python files  
**External Dependencies:** LangChain, LangGraph, OpenAI, Snowflake, MCP SDK, SQLite  
**Architecture:** 3-layer (UI → Protocol → Agent) with 6-node workflow

