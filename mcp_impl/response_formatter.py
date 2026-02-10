"""
Response Formatter

Formats agent responses for display in the UI
Handles the messages array from agent.run()
"""

from typing import Dict, List, Any


class ResponseFormatter:
    """Formats agent responses for UI display"""
    
    @staticmethod
    def format_agent_response(agent_result: Dict[str, Any]) -> str:
        """
        Format the agent response for display in chat UI
        
        Args:
            agent_result: Dictionary returned from agent.run()
        
        Returns:
            Formatted string for display
        """
        if not isinstance(agent_result, dict):
            return str(agent_result)
        
        # Extract messages from agent result
        messages = agent_result.get('messages', [])
        sql_result = agent_result.get('sql_result', '')
        
        # Build formatted output
        output_parts = []
        
        # Add all messages from the agent
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get('content', '')
            else:
                content = str(msg)
            
            if content:
                output_parts.append(content)
        
        # Combine all parts
        formatted = '\n\n'.join(output_parts)
        
        return formatted.strip()
    
    @staticmethod
    def format_error(error_message: str) -> str:
        """Format error message for display"""
        return f"❌ Error: {error_message}"
    
    @staticmethod
    def extract_sql(agent_result: Dict[str, Any]) -> str:
        """Extract and return just the SQL query"""
        messages = agent_result.get('messages', [])
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get('content', '')
                if 'SELECT' in content or 'INSERT' in content or 'UPDATE' in content:
                    return content
        return ""
    
    @staticmethod
    def extract_final_answer(agent_result: Dict[str, Any]) -> str:
        """Extract just the final answer"""
        messages = agent_result.get('messages', [])
        if messages:
            # Usually the last message is the answer
            last_msg = messages[-1]
            if isinstance(last_msg, dict):
                return last_msg.get('content', '')
            return str(last_msg)
        return ""
