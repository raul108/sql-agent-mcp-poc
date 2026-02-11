"""
LangGraph Builder Module

Constructs and configures the LangGraph workflow.
Handles graph topology and node connections.
"""

from langgraph.graph import StateGraph, END
from src.agent.nodes import AgentNodes, AgentState


class GraphBuilder:
    """Builds the LangGraph workflow."""
    
    def __init__(self, nodes: AgentNodes):
        """
        Initialize graph builder.
        
        Args:
            nodes: AgentNodes instance with all node functions
        """
        self.nodes = nodes
        self.graph = None
    
    def build(self) -> StateGraph:
        """
        Build the 6-node workflow graph.
        
        Topology:
        1. check_scope → 2. analyze_query → 3. validate_sql → 
        4. execute_sql → 5. format_results → 6. respond → END
        
        Returns:
            Compiled StateGraph ready for execution
        """
        # Create graph
        graph = StateGraph(AgentState)
        
        # Add nodes
        graph.add_node("check_scope", self.nodes.check_scope)
        graph.add_node("analyze_query", self.nodes.analyze_query)
        graph.add_node("validate_sql", self.nodes.validate_sql)
        graph.add_node("execute_sql", self.nodes.execute_sql)
        graph.add_node("format_results", self.nodes.format_results)
        graph.add_node("respond", self.nodes.respond)
        
        # Define edges (workflow sequence)
        graph.add_edge("check_scope", "analyze_query")
        graph.add_edge("analyze_query", "validate_sql")
        graph.add_edge("validate_sql", "execute_sql")
        graph.add_edge("execute_sql", "format_results")
        graph.add_edge("format_results", "respond")
        graph.add_edge("respond", END)
        
        # Set entry point
        graph.set_entry_point("check_scope")
        
        # Compile and return
        self.graph = graph.compile()
        return self.graph
