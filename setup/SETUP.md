# Setup Guide

## Configuration

### 1. Environment Variables (.env)

Copy the template below and update with your credentials:

```bash
# Snowflake Credentials
SNOWFLAKE_ACCOUNT=your_account.region
SNOWFLAKE_USER=your_username
SNOWFLAKE_PASSWORD=your_password
SNOWFLAKE_DATABASE=SNOWFLAKE_SAMPLE_DATA
SNOWFLAKE_SCHEMA=TPCH_SF1
SNOWFLAKE_WAREHOUSE=COMPUTE_WH
SNOWFLAKE_ROLE=ACCOUNTADMIN

# OpenAI
OPENAI_API_KEY=sk-...

# Optional: Persistent conversation history (default: false)
PERSIST_MEMORY=false
```

**Note:** `.env` file is gitignored and should never be committed.

### 2. Dependencies

Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 3. Virtual Environment Setup

```bash
# Create virtual environment
python3 -m venv .venv

# Activate it
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Snowflake Setup

1. Get your Snowflake account information
2. Create a user and warehouse
3. Grant necessary permissions
4. Update `.env` with credentials

## Verification

Test your setup:

```bash
.venv/bin/python -c "from src.agent import SQLAgent; from src.config import Config; print('✓ Setup OK')"
```

## Troubleshooting

- **"Module not found"**: Ensure virtual environment is activated and dependencies installed
- **"Connection failed"**: Check Snowflake credentials in `.env`
- **"API key invalid"**: Verify OpenAI key in `.env`
