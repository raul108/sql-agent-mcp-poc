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

from langchain_openai import ChatOpenAI
from src.config import Config
from src.tools import SnowflakeSQLTool
from src.validator import SQLValidator
from src.memory import ConversationMemory
from src.agent.nodes import AgentNodes
from src.agent.graph_builder import GraphBuilder
import uuid


class SQLAgent:
    """
    SQL Agent with LangGraph workflow orchestration.
    
    Coordinates 6-node workflow:
    scope detection → query analysis → SQL validation → execution → 
    result formatting → natural language response
    """
    
    def __init__(self, config: Config, memory_type: str = "memory"):
        """
        Initialize the SQL Agent.
        
        Args:
            config: Configuration object with Snowflake and OpenAI settings
            memory_type: "memory" (in-memory, clears on restart) or 
                        "persistent" (file-based)
        """
        self.config = config
        
        # Initialize components
        self.llm = ChatOpenAI(model="gpt-4", temperature=0)
        self.sql_tool = SnowflakeSQLTool(config)
        self.validator = SQLValidator()
        
        # Use in-memory database by default (fresh session each restart)
        # Set to "persistent" for file-based storage across restarts
        if memory_type == "persistent":
            self.memory = ConversationMemory("data/conversation_history.db")
        else:
            # In-memory database - clears on app restart
            self.memory = ConversationMemory(":memory:")
        
        # Build the workflow graph
        self._build_graph()
    
    def _build_graph(self):
        """
        Build and compile the LangGraph workflow.
        
        Creates a 6-node graph with proper sequencing and conditional logic.
        """
        # Create node handlers
        nodes = AgentNodes(
            llm=self.llm,
            sql_tool=self.sql_tool,
            validator=self.validator,
            memory=self.memory
        )
        
        # Build and compile the graph
        builder = GraphBuilder(nodes)
        self.graph = builder.build()
    
    def run(self, query: str, session_id: str = None):
        """
        Execute the agent workflow for a given query.
        
        Runs through the complete 6-node pipeline:
        1. Check if query is in-scope
        2. Analyze and generate SQL
        3. Validate SQL for safety
        4. Execute against database
        5. Format large results
        6. Generate natural language response
        
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
