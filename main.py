"""
LangGraph SQL Agent - Main Entry Point

Interactive terminal interface for the SQL Agent.
Users can ask natural language questions about data in Snowflake,
and the agent converts them to SQL and returns formatted results.

Usage:
    python main.py

Example queries:
    - "How many customers are there?"
    - "Show me the top 5 orders by revenue"
    - "Which customers are from ASIA region?"
"""

# Suppress Pydantic v1 compatibility warning for Python 3.14+
import warnings
warnings.filterwarnings('ignore', message='.*Pydantic V1 functionality.*')

from src.config import Config
from src.agent import SQLAgent
import uuid


def main():
    """
    Main function to run the SQL agent in interactive mode.
    
    Provides a command-line interface where users can:
    - Enter natural language queries
    - See generated SQL and results
    - Exit with 'quit' or 'exit'
    - Maintains conversation history within session
    """
    
    # Load configuration from config.yaml and .env
    config = Config()
    
    # Initialize the agent
    agent = SQLAgent(config)
    
    # Generate session ID for this interactive session
    session_id = str(uuid.uuid4())
    
    # Display welcome message
    print("=" * 60)
    print("LangGraph SQL Agent - Ready!")
    print("=" * 60)
    print("\nAsk questions about your Snowflake data in natural language.")
    print("💾 Conversation memory enabled - follow-up questions supported!")
    print("Type 'quit' to exit.\n")
    
    # Interactive query loop
    while True:
        user_query = input("\nEnter your query (or 'quit' to exit): ").strip()
        
        # Check for exit commands
        if user_query.lower() in ['quit', 'exit', 'q']:
            print("Goodbye!")
            break
        
        # Skip empty inputs
        if not user_query:
            continue
        
        # Process the query
        print("\n🤖 Processing your query...")
        try:
            result = agent.run(user_query, session_id=session_id)
            
            # Display results
            print("\n" + "=" * 60)
            print("RESULT:")
            print("=" * 60)
            for msg in result["messages"]:
                print(f"\n{msg['content']}")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    main()
