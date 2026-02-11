"""
Agent Workflow Nodes

Individual node functions for the LangGraph workflow.
Each node handles one step of the agent's processing pipeline.
"""

from typing import TypedDict, Annotated
from src.agent.prompts import (
    get_scope_check_prompt,
    get_question_type_prompt,
    get_sql_generation_prompt,
    get_summary_response_prompt,
    get_response_formatting_prompt,
)


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
        session_id: Session identifier for conversation tracking
    """
    messages: Annotated[list, "The messages in the conversation"]
    query: str
    sql_result: str
    next_action: str
    retry_count: int
    is_in_scope: bool
    session_id: str


class AgentNodes:
    """Collection of workflow node functions."""
    
    def __init__(self, llm, sql_tool, validator, memory):
        """
        Initialize node handler.
        
        Args:
            llm: Language model for prompt responses
            sql_tool: Database tool for executing queries
            validator: SQL validator for safety checks
            memory: Conversation memory manager
        """
        self.llm = llm
        self.sql_tool = sql_tool
        self.validator = validator
        self.memory = memory
    
    def check_scope(self, state: AgentState) -> AgentState:
        """
        Node 1: Check if query is within scope (data-related).
        
        Filters out irrelevant questions like "What's the weather?" or
        "Tell me a joke" that aren't related to the database.
        """
        query = state["query"]
        prompt = get_scope_check_prompt(query)
        
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
        """
        # Skip if out of scope
        if not state.get("is_in_scope", True):
            return state
        
        query = state["query"]
        session_id = state.get("session_id", "default")
        schema_info = self.sql_tool.get_schema_info()
        
        # Get conversation history for context
        history_context = self.memory.format_history_for_context(session_id, limit=5)
        has_no_history = "No previous conversation history" in history_context
        
        # Check if this is a summary question
        question_type_prompt = get_question_type_prompt(query)
        question_check = self.llm.invoke(question_type_prompt)
        is_summary_question = "SUMMARY_QUESTION" in question_check.content.strip().upper()
        
        # Handle summary questions
        if is_summary_question and has_no_history:
            state["next_action"] = "NO_HISTORY_ERROR"
            state["sql_result"] = "No previous queries in this session to summarize. Please ask a new question about the database, or start a fresh query."
            state["messages"] = [{"role": "assistant", "content": state["sql_result"]}]
            return state
        
        if is_summary_question and not has_no_history:
            state["next_action"] = "SUMMARY_REQUEST"
            state["sql_result"] = f"SUMMARY:{history_context}"
            state["messages"] = [{"role": "assistant", "content": "Using conversation history to answer..."}]
            return state
        
        # Generate SQL for new queries
        prompt = get_sql_generation_prompt(query, schema_info, history_context)
        response = self.llm.invoke(prompt)
        sql_query = response.content.strip()
        
        # Clean up markdown code blocks if present
        if sql_query.startswith("```"):
            sql_query = sql_query.split("\n", 1)[1]
            sql_query = sql_query.rsplit("```", 1)[0]
        
        state["messages"] = [{"role": "assistant", "content": f"Generated SQL: {sql_query}"}]
        state["next_action"] = sql_query
        return state
    
    def validate_sql(self, state: AgentState) -> AgentState:
        """
        Node 3: Validate SQL for safety.
        
        Checks SQL query for dangerous operations (DROP, DELETE, ALTER, etc.)
        and blocks execution if violations are found.
        """
        # Skip if out of scope or summary request
        if not state.get("is_in_scope", True) or state.get("next_action") == "SUMMARY_REQUEST":
            return state
        
        sql_query = state["next_action"]
        is_valid, message, violations = self.validator.validate(sql_query)
        
        if not is_valid:
            violation_report = self.validator.get_violation_report(sql_query)
            state["sql_result"] = f"BLOCKED: {message}"
            state["messages"].append({
                "role": "assistant",
                "content": f"🛑 Safety Check Failed:\n{violation_report}"
            })
        else:
            state["messages"].append({
                "role": "assistant",
                "content": f"✓ Safety validation passed"
            })
        
        return state
    
    def execute_sql(self, state: AgentState) -> AgentState:
        """
        Node 4: Execute the generated SQL query with retry logic.
        
        Runs the SQL query against Snowflake with up to 3 retry attempts
        for transient errors.
        """
        # Skip if already handled
        skip_conditions = (
            not state.get("is_in_scope", True) or 
            state.get("sql_result", "").startswith("BLOCKED") or
            state.get("next_action") == "SUMMARY_REQUEST" or
            state.get("next_action") == "NO_HISTORY_ERROR"
        )
        if skip_conditions:
            return state
        
        sql_query = state["next_action"]
        max_retries = 3
        retry_count = state.get("retry_count", 0)
        
        result = self.sql_tool.execute_query(sql_query)
        
        # Retry if error and retries remaining
        if result.startswith("Error") and retry_count < max_retries:
            state["retry_count"] = retry_count + 1
            state["messages"].append({
                "role": "assistant",
                "content": f"⚠️  Attempt {retry_count + 1} failed, retrying... ({max_retries - retry_count - 1} retries left)"
            })
            result = self.sql_tool.execute_query(sql_query)
        
        state["sql_result"] = result
        return state
    
    def format_results(self, state: AgentState) -> AgentState:
        """
        Node 5: Format large results with intelligent truncation.
        
        Handles large result sets by providing summary statistics.
        """
        # Skip if out of scope or blocked
        skip_conditions = (
            not state.get("is_in_scope", True) or 
            state.get("sql_result", "").startswith("BLOCKED") or
            state.get("sql_result", "").startswith("Error")
        )
        if skip_conditions:
            return state
        
        sql_result = state["sql_result"]
        
        # Check if results were auto-truncated
        if "showing 10 of" in sql_result.lower():
            state["messages"].append({
                "role": "assistant",
                "content": "📊 Large result set detected - showing first 10 rows"
            })
        
        return state
    
    def respond(self, state: AgentState) -> AgentState:
        """
        Node 6: Generate natural language response.
        
        Takes SQL results and formats them into a user-friendly answer.
        """
        query = state["query"]
        sql_result = state["sql_result"]
        session_id = state.get("session_id", "default")
        
        # Handle summary requests
        if sql_result.startswith("SUMMARY:"):
            history_data = sql_result.replace("SUMMARY:", "")
            prompt = get_summary_response_prompt(query, history_data)
            response = self.llm.invoke(prompt)
            state["messages"].append({"role": "assistant", "content": response.content})
            
            # Store in memory
            self.memory.add_interaction(
                session_id=session_id,
                user_query=query,
                generated_sql="SUMMARY_REQUEST",
                result_summary="Used conversation history",
                is_successful=True
            )
            return state
        
        # Check for error/out-of-scope conditions
        error_conditions = (
            not state.get("is_in_scope", True) or 
            sql_result.startswith("BLOCKED") or 
            sql_result.startswith("OUT_OF_SCOPE") or
            sql_result.startswith("Error")
        )
        if error_conditions:
            return state
        
        # Format response for successful query
        prompt = get_response_formatting_prompt(query, sql_result)
        response = self.llm.invoke(prompt)
        state["messages"].append({"role": "assistant", "content": response.content})
        
        # Store interaction in memory
        sql_query = state.get("next_action", "")
        is_successful = not (sql_result.startswith("Error") or sql_result.startswith("BLOCKED"))
        result_summary = sql_result[:500] if len(sql_result) > 500 else sql_result
        
        self.memory.add_interaction(
            session_id=session_id,
            user_query=query,
            generated_sql=sql_query,
            result_summary=result_summary,
            is_successful=is_successful
        )
        
        return state
