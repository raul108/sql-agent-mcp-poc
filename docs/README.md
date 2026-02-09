# LangGraph SQL Agent

A basic LangGraph agent for executing SQL queries on Snowflake using ChatGPT.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure credentials:**
   - Copy `.env.example` to `.env`
   - Fill in your actual credentials in `.env`
   - Update `config.yaml` with your database schema

3. **Run the agent:**
   ```bash
   python main.py
   ```

## Features

- 🤖 Natural language to SQL conversion using ChatGPT
- 🗄️ Snowflake database integration
- 📊 Schema-aware query generation
- 🔄 Interactive query mode

## Configuration

### Environment Variables (.env)
- `OPENAI_API_KEY`: Your OpenAI API key
- `SNOWFLAKE_*`: Snowflake connection parameters

### Schema Configuration (config.yaml)
Define your database schema and relationships in `config.yaml` to help the agent generate better queries.

## Example Usage

```
Enter your query: Show me all customers
🤖 Processing your query...

Generated SQL: SELECT * FROM customers LIMIT 10
Results: [...]
```

## Architecture

The agent uses LangGraph to create a workflow:
1. **Analyze Query**: Converts natural language to SQL
2. **Execute SQL**: Runs query on Snowflake
3. **Respond**: Formats results for the user
