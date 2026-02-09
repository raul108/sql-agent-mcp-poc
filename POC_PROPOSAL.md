# SQL Agent + MCP Integration - POC Proposal

**Timeline:** 5 days (Feb 10-14, 2026) | **Developer:** Raul Dhruva | **Mentor:** Sravya Batte

---

## Executive Summary

Build a working prototype enabling non-technical users to query Snowflake using natural language through VS Code terminal. Validates AI agent + MCP architecture for enterprise use.

**Deliverables:**
- Natural language SQL agent (70%+ accuracy)
- MCP server integration
- Safety controls (blocks DROP/DELETE/ALTER)
- Conversation memory
- 10 demo queries
- Code repository on Cisco GitHub

**Data Source:** Snowflake TPC-H sample dataset (`SNOWFLAKE_SAMPLE_DATA.TPCH_SF1`)  
**Business Impact:** Reduces 2-3 day data request wait to instant answers

---

## Problem & Solution

**Problem:** Non-technical teams wait days for simple data requests, creating bottlenecks.

**Solution:** AI agent converts questions like *"What were our top 5 customers last quarter?"* into SQL, executes on Snowflake, and returns formatted answers through an interactive terminal.

**Example:**
```
User: "How many customers are from China?"
Agent: "There are 19,050 customers from China."

User: "What about United States?"
Agent: "There are 15,023 customers from United States."
```

---

## Architecture Overview

```
┌──────────────────────────────────────────────┐
│         User Interfaces (Future)             │
│  Terminal | VS Code | Webex | Slack          │
└─────────────────┬────────────────────────────┘
                  │
           ┌──────▼──────┐
           │ MCP Server  │ ← Protocol adapter
           │  (1 tool)   │
           └──────┬──────┘
                  │
           ┌──────▼─────────────────────────┐
           │   SQL Agent (LangGraph)        │
           │  1. Scope Detection            │
           │  2. SQL Generation (GPT-4)     │
           │  3. Safety Validation          │
           │  4. Query Execution (retry 3x) │
           │  5. Result Formatting          │
           │  6. NL Response                │
           └──────┬───────────┬─────────────┘
                  │           │
      ┌───────────▼──┐   ┌────▼────────┐
      │ Conversation │   │ Snowflake   │
      │ Memory       │   │ TPC-H       │
      │ (SQLite)     │   │ (8 tables)  │
      └──────────────┘   └─────────────┘
```

**Component Flow:**
1. **MCP Client** (terminal/VS Code) sends user query
2. **MCP Server** routes to agent via `query_database` tool
3. **Agent** executes 6-node workflow
4. **Memory** provides last 5 interactions for context
5. **Snowflake** executes safe SELECT queries
6. **Response** returns formatted answer to user

---

## Key Features

**Safety & Intelligence:**
- Read-only enforcement (blocks DROP/DELETE/ALTER)
- Auto-retry on errors (max 3x)
- Out-of-scope detection ("Tell me a joke" → rejected)

**Schema Discovery:**
- Auto-discovers table structures from `INFORMATION_SCHEMA`
- Handles 8 TPC-H tables (CUSTOMER, ORDERS, LINEITEM, etc.)

**User Experience:**
- Conversation memory (understands follow-ups)
- Large result handling (>10 rows returns SQL)
- 3-5 second response time

**Integration:**
- MCP protocol standard (works with any MCP client)
- Single tool interface (`query_database`)
- Extensible to Webex/Slack/Web UI (zero agent changes)

---

## 5-Day Timeline

| Day | Focus | Deliverable |
|-----|-------|-------------|
| **1** | Foundation | Snowflake connector + schema discovery |
| **2** | SQL Generation | LangGraph workflow + GPT-4 integration |
| **3** | Safety & Execution | SQL validation + retry logic |
| **4** | Memory | Conversation history + follow-ups |
| **5** | MCP Integration | Server + client + demo polish |

**Checkpoints:** Day 3 mid-review | Day 5 final demo

---

## Success Criteria

✅ 70%+ accuracy on 10 test queries  
✅ 100% safety enforcement (blocks dangerous ops)  
✅ Multi-turn conversations work  
✅ MCP server validated  
✅ Response time < 10 seconds  

---

## Demo Scenarios

**1. Simple Queries:**
- "Top 5 customers by order count"
- "Average order value by region"

**2. Multi-Table Joins:**
- "Customers and their suppliers by nation"
- "Order revenue by product category"

**3. Conversation:**
- "Show Q4 orders" → "What about Q3?" (remembers context)

**4. Safety Tests:**
- "DROP TABLE customers" → **BLOCKED**
- "DELETE orders" → **BLOCKED**

**5. Large Results:**
- "Show all line items" → Returns SQL (600K+ rows)

---

## Technical Stack

**Core:** LangGraph | GPT-4 | Snowflake | MCP SDK | Python 3.10+  
**Storage:** SQLite (conversation memory)  
**Repository:** Cisco GitHub

---

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Timeline aggressive** | High | Skip memory if needed; focus on MVP |
| **SQL accuracy issues** | Medium | 3x retry logic + validation |
| **MCP complexity** | Medium | Fallback to HTTP if stdio fails |

**Contingency:** Minimum viable = CLI agent answering 5 queries + basic MCP server

---

## Business Value

**Immediate:**
- Validates agent + MCP architecture
- Proves 70%+ SQL accuracy achievable
- Demonstrates safe enterprise AI

**Future:**
- Extend to PostgreSQL, MongoDB
- Slack/Teams integration
- Custom business tools

---

## Scope & Limitations

**What POC Proves:**
✅ Pattern works  
✅ MCP integration viable  
✅ 70%+ SQL accuracy achievable  

**Known Limitations:**
❌ Not optimized for cost/scale  
❌ SQLite memory (not multi-user)  
❌ No caching  
❌ No RBAC (user authentication)  

---

## Final Deliverable (Feb 14)

📦 Live terminal demo answering 10 queries  
📦 MCP server validated  
📦 Working code on Cisco GitHub  
📦 Documentation (setup + architecture)  

---

**Prepared by:** Raul Dhruva | **Date:** February 8, 2026