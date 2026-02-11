"""
LLM Prompts Module

Centralized collection of all prompts used in the SQL Agent workflow.
Keeps prompts organized and easy to maintain/update.
"""


def get_scope_check_prompt(query: str) -> str:
    """Check if query is related to database/data."""
    return f"""Determine if this question is related to querying, analyzing, or understanding data in a database.

Question: {query}

Answer with ONLY 'yes' or 'no':
- 'yes' if the question is about data, database queries, statistics, or information that could be in a database
- 'no' if it's about unrelated topics like weather, jokes, general knowledge, code generation, etc.

Answer:"""


def get_question_type_prompt(query: str) -> str:
    """Detect if this is a summary/history question or new query."""
    return f"""Is this question asking for a SUMMARY or REFERENCE to previous conversation?

User query: {query}

Answer with ONLY 'SUMMARY_QUESTION' or 'NEW_QUERY':
- SUMMARY_QUESTION: if user wants to summarize, reference, or review previous discussion
  Examples: "summarize what we discussed", "what was the count?", "tell me about those results", "remind me..."
- NEW_QUERY: if user is asking a new question about the database
"""


def get_sql_generation_prompt(query: str, schema_info: str, history_context: str) -> str:
    """Generate SQL from natural language query."""
    return f"""Given the following database schema:
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


def get_summary_response_prompt(query: str, history_data: str) -> str:
    """Generate response for summary/history questions."""
    return f"""The user asked: {query}

Here is the conversation history:
{history_data}

Based on the conversation history above, provide a comprehensive summary answering the user's question.
"""


def get_response_formatting_prompt(query: str, sql_result: str) -> str:
    """Format SQL results into natural language response."""
    return f"""User asked: {query}

SQL Results: {sql_result}

Provide a clear, natural language answer to the user's question based on these results.
"""
