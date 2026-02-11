"""
LangGraph SQL Agent

Enhanced 6-node agent workflow with safety validation:
1. Scope Detection - filters out non-SQL questions
2. Analyzes user queries and generates SQL
3. Validates SQL for safety (blocks DROP/DELETE/ALTER)
4. Executes SQL on Snowflake with retry logic
5. Formats results with intelligent truncation
6. Responds in natural language

Features:
- Scope detection (rejects off-topic questions)
- Safety validation (read-only enforcement)
- Schema auto-discovery
- Enhanced response formatting (handles large results)
- Conversation memory (SQLite-based history)
"""

from typing import TypedDict, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from src.config import Config
from src.tools import SnowflakeSQLTool
from src.validator import SQLValidator
from src.memory import ConversationMemory
import uuid


# Define the agent state structure
class AgentState(TypedDict):
    """
    State maintained throughout the agent workflow.
    
    Attributes:
        messages: List of conversation messages
        query: Current user query
        sql_result: Result from SQL execution
        next_action: Next SQL query to execute
        retry_count: Number of execution retries attempted
        is_in_scope: Whether query is data-related
    """
    messages: Annotated[list, "The messages in the conversation"]
    query: str
    sql_result: str
    next_action: str
    retry_count: int
    is_in_scope: bool
    session_id: str


class SQLAgent:
    """
    LangGraph-based SQL Agent for natural language to SQL conversion.
    
    Current workflow (6 nodes):
        User Query → Scope Check → Analyze & Generate SQL → Validate SQL (Safety) 
        → Execute (with retry) → Format Results → Respond
    
    Safety Features:
        - Scope detection for data-related questions only
        - Blocks DROP, DELETE, ALTER, UPDATE, INSERT operations
        - Read-only enforcement
        - Retry logic for transient errors (max 3 attempts)
    """
    
    def __init__(self, config: Config, memory_type: str = "memory"):
        """
        Initialize the SQL Agent.
        
        Args:
            config: Configuration object with Snowflake and OpenAI settings
            memory_type: "memory" (in-memory, clears on restart) or "persistent" (file-based)
        """
        self.config = config
        self.sql_tool = SnowflakeSQLTool(config)
        self.validator = SQLValidator()
        
        # Use in-memory database by default (fresh session each restart)
        # Set to "persistent" for file-based storage across restarts
        if memory_type == "persistent":
            self.memory = ConversationMemory("conversation_history.db")
        else:
            # In-memory database - clears on app restart
            self.memory = ConversationMemory(":memory:")
        
        # Initialize OpenAI language model
        openai_config = config.get_openai_config()
        self.llm = ChatOpenAI(
            api_key=openai_config['api_key'],
            model=openai_config['model'],
            temperature=0  # Deterministic output for SQL generation
        )
        
        # Build the LangGraph workflow
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """
        Build the LangGraph workflow.
        
        Current flow (6 nodes):
            check_scope → analyze_query → validate_sql → execute_sql → format_results → respond → END
        
        Returns:
            Compiled LangGraph workflow
        """
        workflow = StateGraph(AgentState)
        
        # Add nodes to the workflow
        workflow.add_node("check_scope", self.check_scope)
        workflow.add_node("analyze_query", self.analyze_query)
        workflow.add_node("validate_sql", self.validate_sql)
        workflow.add_node("execute_sql", self.execute_sql_node)
        workflow.add_node("format_results", self.format_results)
        workflow.add_node("respond", self.respond)
        
        # Define the workflow edges (transitions)
        workflow.set_entry_point("check_scope")
        workflow.add_edge("check_scope", "analyze_query")
        workflow.add_edge("analyze_query", "validate_sql")
        workflow.add_edge("validate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "format_results")
        workflow.add_edge("format_results", "respond")
        workflow.add_edge("respond", END)
        
        return workflow.compile()
    
    def check_scope(self, state: AgentState) -> AgentState:
        """
        Node 1: Check if query is within scope (data-related).
        
        Filters out irrelevant questions like "What's the weather?" or
        "Tell me a joke" that aren't related to the database.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with is_in_scope flag
        """
        query = state["query"]
        
        prompt = f"""Determine if this question is related to querying, analyzing, or understanding data in a database.

Question: {query}

Answer with ONLY 'yes' or 'no':
- 'yes' if the question is about data, database queries, statistics, or information that could be in a database
- 'no' if it's about unrelated topics like weather, jokes, general knowledge, code generation, etc.

Answer:"""
        
        response = self.llm.invoke(prompt)
        is_in_scope = response.content.strip().lower() == "yes"
        
        state["is_in_scope"] = is_in_scope
        
        if not is_in_scope:
            state["sql_result"] = "OUT_OF_SCOPE"
            state["messages"].append({
                "role": "assistant",
                "content": "⚠️  I'm a SQL agent designed to answer questions about your database. Your question doesn't appear to be data-related."
            })
        
        return state
    
    def analyze_query(self, state: AgentState) -> AgentState:
        """
        Node 2: Analyze user query and generate SQL.
        
        Takes natural language query and converts it to SQL using the LLM,
        providing database schema as context.
        
        Args:
            state: Current agent state
            
        Returns:
            Updated state with generated SQL in next_action
        """
        # Skip if out of scope
        if not state.get("is_in_scope", True):
            return state
        
        query = state["query"]
        session_id = state.get("session_id", "default")
        schema_info = self.sql_tool.get_schema_info()
        
        # Get conversation history for context
        history_context = self.memory.format_history_for_context(session_id, limit=5)
        
        # Check if this is a summary/reference question vs new data query
        check_prompt = f"""Does this question require NEW data from the database, or can it be answered using conversation history?

Conversation History:
{history_context}

User query: {query}

Answer with ONLY 'NEW_DATA' or 'HISTORY':
- NEW_DATA: if user wants fresh information from database
- HISTORY: if user wants summary/reference to previous discussion (e.g., "summarize what we discussed", "what was the total?", "remind me...")
"""
        
        needs_check = self.llm.invoke(check_prompt)
        needs_new_data = "NEW_DATA" in needs_check.content.strip().upper()
        
        # If user wants summary of conversation, provide it directly
        if not needs_new_data and "No previous conversation history" not in history_context:
            state["next_action"] = "SUMMARY_REQUEST"
            state["sql_result"] = f"SUMMARY:{history_context}"
            state["messages"] = [{"role": "assistant", "content": "Using conversation history to answer..."}]
            return state
        
        # Construct prompt with schema and history context
        prompt = f"""Given the following database schema:
{schema_info}

{history_context}

User query: {query}

Instructions:
- If the user is asking about previous results or wants a summary of what was discussed, you can reference the conversation history above
- If the user needs new data from the database, generate a SQL query
- Use conversation history to understand references like "those orders", "them", "the previous table", etc.
- Return ONLY the SQL query, nothing else

Generate a SQL query to answer this question:
"""
        
        # Get SQL from LLM
        response = self.llm.invoke(prompt)
        sql_query = response.content.strip()
        
        # Clean up markdown code blocks if present
        if sql_query.startswith("```"):
            sql_query = sql_query.split("\n", 1)[1]
            sql_query = sql_query.rsplit("```", 1)[0]
        
        # Store generated SQL and add to messages
        state["messages"] = [{"role": "assistant", "content": f"Generated SQL: {sql_query}"}]
        state["next_action"] = sql_query
        return state
    
    def validate_sql(self, state: AgentState) -> AgentState:
        """
        Node 3: Validate SQL for safety.
        
        Checks SQL query for dangerous operations (DROP, DELETE, ALTER, etc.)
        and blocks execution if violations are found.
        
        Args:
            state: Current agent state with SQL in next_action
            
        Returns:
            Updated state with validation results
        """
        # Skip if out of scope or summary request
        if not state.get("is_in_scope", True) or state.get("next_action") == "SUMMARY_REQUEST":
            return state
        
        sql_query = state["next_action"]
        
        # Validate the SQL query
        is_valid, message, violations = self.validator.validate(sql_query)
        
        if not is_valid:
            # SQL is dangerous - block execution
            violation_report = self.validator.get_violation_report(sql_query)
            state["sql_result"] = f"BLOCKED: {message}"
            state["messages"].append({
                "role": "assistant",
                "content": f"🛑 Safety Check Failed:\n{violation_report}"
            })
        else:
            # SQL is safe - add confirmation message
            state["messages"].append({
                "role": "assistant",
                "content": f"✓ Safety validation passed"
            })
        
        return state
    
    def execute_sql_node(self, state: AgentState) -> AgentState:
        """
        Node 4: Execute the generated SQL query with retry logic.
        
        Runs the SQL query against Snowflake with up to 3 retry attempts
        for transient errors. Stores results or error messages.
        
        Args:
            state: Current agent state with SQL in next_action
            
        Returns:
            Updated state with query results in sql_result
        """
        # Skip if out of scope, blocked by validator, or summary request
        if (not state.get("is_in_scope", True) or 
            state.get("sql_result", "").startswith("BLOCKED") or
            state.get("next_action") == "SUMMARY_REQUEST"):
            return state
        
        sql_query = state["next_action"]
        max_retries = 3
        retry_count = state.get("retry_count", 0)
        
        result = self.sql_tool.execute_query(sql_query)
        
        # Check if error occurred and retry if needed
        if result.startswith("Error") and retry_count < max_retries:
            state["retry_count"] = retry_count + 1
            state["messages"].append({
                "role": "assistant",
                "content": f"⚠️  Attempt {retry_count + 1} failed, retrying... ({max_retries - retry_count - 1} retries left)"
            })
            # Retry the query
            result = self.sql_tool.execute_query(sql_query)
        
        state["sql_result"] = result
        return state
    
    def format_results(self, state: AgentState) -> AgentState:
        """
        Node 5: Format large results with intelligent truncation.
        
        Handles large result sets by providing summary statistics
        and truncating appropriately.
        
        Args:
            state: Current agent state with SQL results
            
        Returns:
            Updated state with formatted results
        """
        # Skip if out of scope, blocked, or already has error
        if (not state.get("is_in_scope", True) or 
            state.get("sql_result", "").startswith("BLOCKED") or
            state.get("sql_result", "").startswith("Error")):
            return state
        
        sql_result = state["sql_result"]
        
        # Check if results are truncated (from tools.py execute_query)
        if "showing 10 of" in sql_result.lower():
            # Results were auto-truncated - add helpful context
            state["messages"].append({
                "role": "assistant",
                "content": "📊 Large result set detected - showing first 10 rows"
            })
        
        return state
    
    def respond(self, state: AgentState) -> AgentState:
        """
        Node 6: Generate natural language response.
        
        Takes SQL results and formats them into a user-friendly answer.
        Handles both successful queries and blocked queries.
        
        Args:
            state: Current agent state with SQL results
            
        Returns:
            Updated state with final response in messages
        """
        query = state["query"]
        sql_result = state["sql_result"]
        
        # Handle summary requests (from conversation history)
        if sql_result.startswith("SUMMARY:"):
            history_data = sql_result.replace("SUMMARY:", "")
            summary_prompt = f"""The user asked: {query}

Here is the conversation history:
{history_data}

Based on the conversation history above, provide a comprehensive summary answering the user's question.
"""
            response = self.llm.invoke(summary_prompt)
            state["messages"].append({"role": "assistant", "content": response.content})
            
            # Store summary interaction in memory
            session_id = state.get("session_id", "default")
            self.memory.add_interaction(
                session_id=session_id,
                user_query=query,
                generated_sql="SUMMARY_REQUEST",
                result_summary="Used conversation history",
                is_successful=True
            )
            return state
        
        # Check if query was out of scope, blocked, or errored
        if (not state.get("is_in_scope", True) or 
            sql_result.startswith("BLOCKED") or 
            sql_result.startswith("OUT_OF_SCOPE") or
            sql_result.startswith("Error")):
            # Don't format - appropriate message already added
            return state
        
        # Construct prompt for response formatting
        prompt = f"""User asked: {query}

SQL Results: {sql_result}

Provide a clear, natural language answer to the user's question based on these results.
"""
        
        response = self.llm.invoke(prompt)
        state["messages"].append({"role": "assistant", "content": response.content})
        
        # Store interaction in memory
        session_id = state.get("session_id", "default")
        sql_query = state.get("next_action", "")
        is_successful = not (sql_result.startswith("Error") or sql_result.startswith("BLOCKED"))
        
        # Create result summary (truncate if too long)
        result_summary = sql_result[:500] if len(sql_result) > 500 else sql_result
        
        self.memory.add_interaction(
            session_id=session_id,
            user_query=query,
            generated_sql=sql_query,
            result_summary=result_summary,
            is_successful=is_successful
        )
        
        return state
    
    def run(self, query: str, session_id: str = None):
        """
        Execute the agent workflow for a given query.
        
        Args:
            query: Natural language question from the user
            session_id: Optional session ID for conversation tracking
            
        Returns:
            dict: Final state containing messages with agent responses
        """
        # Generate session ID if not provided
        if session_id is None:
            session_id = str(uuid.uuid4())
        
        initial_state = {
            "messages": [],
            "query": query,
            "sql_result": "",
            "next_action": "",
            "retry_count": 0,
            "is_in_scope": True,
            "session_id": session_id
        }
        
        result = self.graph.invoke(initial_state)
        return result
