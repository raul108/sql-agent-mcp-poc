# HTTP Transport for MCP Server

This document covers the **HTTP-based MCP server** - an alternative to the stdio-based server for remote/multi-user deployments.

## Quick Start

### Run the HTTP Server

```bash
# Activate virtual environment
source .venv/bin/activate

# Install dependencies (includes starlette, uvicorn, httpx)
pip install -r requirements.txt

# Start HTTP server (local testing)
bash scripts/run_http_server.sh

# Or directly with uvicorn:
uvicorn mcp_server_http:app --host 127.0.0.1 --port 8000
```

### Test with HTTP Client

In a new terminal:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run interactive client
python mcp_client_http.py

# Or execute single query
python mcp_client_http.py --query "How many customers?"

# Connect to remote server
python mcp_client_http.py --url http://your-server:8000
```

## Server Endpoints

### Health Check
```bash
GET http://localhost:8000/health
```

**Response:**
```json
{
    "status": "healthy",
    "version": "1.0.0",
    "transport": "streamable-http",
    "agent_ready": true,
    "database": "SNOWFLAKE_SAMPLE_DATA"
}
```

### MCP Endpoint (JSON-RPC 2.0)
```bash
POST http://localhost:8000/mcp
Content-Type: application/json
```

**List Tools Request:**
```json
{
    "jsonrpc": "2.0",
    "id": "tools_list_1",
    "method": "tools/list",
    "params": {}
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": "tools_list_1",
    "result": {
        "tools": [
            {
                "name": "query_database",
                "description": "Ask questions about the Snowflake database...",
                "inputSchema": {...}
            }
        ]
    }
}
```

**Call Tool Request:**
```json
{
    "jsonrpc": "2.0",
    "id": "tool_call_1",
    "method": "tools/call",
    "params": {
        "name": "query_database",
        "arguments": {
            "query": "How many customers?",
            "session_id": "my_session_123",
            "user_role": "GLOBAL_ANALYST"
        }
    }
}
```

**Response:**
```json
{
    "jsonrpc": "2.0",
    "id": "tool_call_1",
    "result": {
        "content": [
            {
                "type": "text",
                "text": "Query: How many customers?\n\nGenerated SQL: SELECT COUNT(*) FROM CUSTOMER\n\nThere are 150,000 customers."
            }
        ]
    }
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `HTTP_HOST` | `127.0.0.1` | Server bind address |
| `HTTP_PORT` | `8000` | Server port |
| `HTTP_AUTH_TOKEN` | None | Optional bearer token for authentication |
| `DEBUG` | `true` | Enable debug mode (uvicorn reload) |

### Examples

```bash
# Local server (default)
bash scripts/run_http_server.sh

# Listen on all interfaces (remote access)
HTTP_HOST=0.0.0.0 bash scripts/run_http_server.sh

# Custom port
HTTP_PORT=9000 bash scripts/run_http_server.sh

# With authentication
HTTP_AUTH_TOKEN="your-secret-token" bash scripts/run_http_server.sh

# Production deployment (no reload, 4 workers)
HTTP_HOST=0.0.0.0 HTTP_PORT=8000 DEBUG=false \
    uvicorn mcp_server_http:app --workers 4
```

## Authentication

### Optional Bearer Token

If `HTTP_AUTH_TOKEN` environment variable is set, all requests must include:

```bash
curl -X POST http://localhost:8000/mcp \
    -H "Authorization: Bearer your-secret-token" \
    -H "Content-Type: application/json" \
    -d '{...}'
```

### Python Client

```python
client = HTTPMCPClient(
    base_url="http://localhost:8000",
    auth_token="your-secret-token"  # Optional
)
```

## curl Examples

### Health Check

```bash
curl http://localhost:8000/health
```

### List Tools

```bash
curl -X POST http://localhost:8000/mcp \
    -H "Content-Type: application/json" \
    -d '{
        "jsonrpc": "2.0",
        "id": "1",
        "method": "tools/list",
        "params": {}
    }'
```

### Execute Query

```bash
curl -X POST http://localhost:8000/mcp \
    -H "Content-Type: application/json" \
    -d '{
        "jsonrpc": "2.0",
        "id": "2",
        "method": "tools/call",
        "params": {
            "name": "query_database",
            "arguments": {
                "query": "How many customers?",
                "session_id": "session_123"
            }
        }
    }' | jq
```

### With Authentication

```bash
curl -X POST http://localhost:8000/mcp \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer my-token" \
    -d '{...}'
```

## Comparison: Stdio vs HTTP

| Feature | Stdio | HTTP |
|---------|-------|------|
| **Transport** | Process pipes | HTTP POST |
| **Concurrency** | Single client | Multiple clients |
| **Remote access** | No | Yes |
| **Deployment** | Local subprocess | Server (uvicorn, Docker, cloud) |
| **Authentication** | None | Bearer token, OAuth |
| **Latency** | ~1-2ms (IPC) | ~50-200ms (network) |
| **VS Code integration** | Native (claude.ai config) | Manual URL config |
| **Scaling** | Single server/client | Horizontal scaling |
| **Complexity** | Low | Medium |

**Use Stdio when:** Local single-user, VS Code integration, minimal dependencies
**Use HTTP when:** Multi-user, remote access, cloud deployment, enterprise auth

## Migration Path

### From Stdio to HTTP

If you want to migrate from stdio-based to HTTP-based:

#### Phase 1: Parallel Operation
- Keep `mcp_server.py` running (existing setup)
- Run `mcp_server_http.py` on different port
- Test HTTP version independently

#### Phase 2: Gradual Switchover
```bash
# Terminal 1: Start HTTP server
bash scripts/run_http_server.sh

# Terminal 2: Test with HTTP client
python mcp_client_http.py
```

#### Phase 3: Replace Stdio
Once HTTP version is validated:
- Remove `stdio_server()` from configuration
- Switch clients to HTTP client
- Update deployment scripts

#### Phase 4: Cloud Deployment
```bash
# Example: Deploy to Heroku
heroku create my-sql-agent
git push heroku main

# Example: Deploy to AWS
aws elasticbeanstalk create-environment \
    --application-name sql-agent \
    --environment-name sql-agent-prod
```

## Production Deployment

### Using Gunicorn + Nginx

```bash
# Install production dependencies
pip install gunicorn

# Start with gunicorn
gunicorn mcp_server_http:app \
    --workers 4 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "mcp_server_http:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# Build and run
docker build -t sql-agent-http .
docker run -p 8000:8000 \
    -e SNOWFLAKE_ACCOUNT=your_account \
    -e SNOWFLAKE_USER=your_user \
    -e SNOWFLAKE_PASSWORD=your_password \
    -e OPENAI_API_KEY=your_key \
    sql-agent-http
```

### Cloud Platform Examples

#### Heroku
```bash
git push heroku main
heroku config:set SNOWFLAKE_ACCOUNT=your_account
heroku logs --tail
```

#### AWS Lambda (with API Gateway)
```bash
# Use serverless framework or AWS SAM
sam build
sam deploy --guided
```

#### Google Cloud Run
```bash
gcloud run deploy sql-agent \
    --source . \
    --platform managed \
    --region us-central1
```

## Troubleshooting

### Server Won't Start

```bash
# Check if port is in use
lsof -i :8000

# Use different port
HTTP_PORT=9000 bash scripts/run_http_server.sh
```

### Connection Refused

```bash
# Verify server is running
curl http://localhost:8000/health

# Check if listening on correct interface
netstat -an | grep 8000
```

### Slow Queries

- HTTP adds ~50-200ms latency compared to stdio
- SQL query execution time dominates for complex queries
- Acceptable for interactive use

### Authentication Errors

```bash
# Without token (if not configured)
curl http://localhost:8000/mcp -X POST -H "Content-Type: application/json" -d '{...}'

# With token (if configured)
curl -H "Authorization: Bearer my-token" http://localhost:8000/mcp -X POST ...
```

## Performance Notes

### Benchmarks (vs stdio)

- Health check: ~5-10ms (HTTP) vs <1ms (stdio)
- Query execution: 100-500ms (dominated by SQL + LLM, not transport)
- Throughput: 100+ concurrent clients with HTTP vs 1 with stdio

### Optimization Tips

1. **Connection pooling:** Enabled by default in uvicorn
2. **Worker processes:** Use multiple workers for production
3. **Caching:** SQL schema cache reduces Snowflake calls
4. **Monitoring:** Enable logging to track performance

## Support

For issues or questions:
1. Check logs: `tail -f mcp_server_http.log`
2. Enable debug mode: `DEBUG=true bash scripts/run_http_server.sh`
3. Verify configuration: `curl http://localhost:8000/health`
4. Test with curl before testing with client

## Next Steps

- [Return to README](../README.md)
- [Stdio MCP Server Setup](../docs/MCP_SETUP.md)
- [SQL Agent Configuration](../src/config.py)
