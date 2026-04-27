# Unified MCP Server - API Intelligence Plane

## Overview

The Unified MCP Server provides a **single interface** for external AI agents to interact with the entire API Intelligence Plane platform. It exposes all backend REST API endpoints as MCP tools, eliminating the need to connect to multiple specialized servers.

**Port**: 8007 (external) → 8000 (internal)  
**Transport**: Streamable HTTP  
**Architecture**: Thin wrapper delegating to backend API at `http://backend:8000/api/v1`

## Why Unified Server?

While the project includes specialized MCP servers (discovery, metrics, security, etc.), the unified server offers:

1. **Single Connection Point**: AI agents connect to one server instead of six
2. **Complete Coverage**: Access to all 25+ tools across all domains
3. **Simplified Configuration**: One endpoint to configure in AI agent tools
4. **Consistent Interface**: Uniform error handling and response formats
5. **External Workflow Support**: Designed for standalone external agentic workflows

## Available Tools (25+)

### 1. Health & Server Info (2 tools)

#### `health`
Check server health and backend connectivity.

**Returns:**
```json
{
  "status": "healthy",
  "server": "unified-server",
  "version": "1.0.0",
  "backend_status": "connected",
  "timestamp": "2026-04-22T04:00:00Z"
}
```

#### `server_info`
Get server metadata and capabilities.

**Returns:**
```json
{
  "name": "unified-server",
  "version": "1.0.0",
  "port": 8007,
  "transport": "streamable-http",
  "capabilities": [
    "gateway_management",
    "api_discovery",
    "metrics_collection",
    "security_scanning",
    "compliance_monitoring",
    "optimization_recommendations",
    "rate_limiting",
    "predictions",
    "natural_language_query"
  ]
}
```

---

### 2. Gateway Management (6 tools)

#### `create_gateway`
Register a new API Gateway.

**Parameters:**
- `name` (string, required): Gateway name
- `vendor` (string, required): Gateway vendor (native, kong, apigee, aws, azure, mulesoft, webmethods)
- `base_url` (string, required): Gateway base URL
- `version` (string, optional): Gateway version
- `connection_type` (string, optional): Connection method (default: "rest_api")
- `credentials` (dict, optional): Authentication credentials

**Example:**
```python
result = await create_gateway(
    name="Production Gateway",
    vendor="kong",
    base_url="https://api.example.com",
    credentials={
        "type": "api_key",
        "api_key": "your-api-key"
    }
)
```

#### `list_gateways`
List all registered gateways with pagination.

**Parameters:**
- `page` (int, optional): Page number (default: 1)
- `page_size` (int, optional): Items per page (default: 20)
- `status` (string, optional): Filter by status (connected, disconnected, error)

#### `get_gateway`
Get details of a specific gateway.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID

#### `connect_gateway`
Establish connection to a gateway.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID

#### `disconnect_gateway`
Disconnect from a gateway.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID

#### `sync_gateway`
Trigger API discovery/sync from a gateway.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `force_refresh` (bool, optional): Force refresh (default: false)

---

### 3. API Discovery (3 tools)

#### `list_apis`
List APIs with optional filtering.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `page` (int, optional): Page number (default: 1)
- `page_size` (int, optional): Items per page (default: 20)
- `status` (string, optional): Filter by status
- `is_shadow` (bool, optional): Filter shadow APIs
- `health_score_min` (float, optional): Minimum health score (0.0-1.0)

#### `search_apis`
Search APIs using full-text search.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `query` (string, required): Search query
- `limit` (int, optional): Maximum results (default: 100)

**Example:**
```python
results = await search_apis(
    gateway_id="550e8400-e29b-41d4-a716-446655440000",
    query="payment",
    limit=10
)
```

#### `get_api`
Get details of a specific API.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, required): API UUID

---

### 4. Metrics (1 tool)

#### `get_api_metrics`
Get time-bucketed metrics for an API.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, required): API UUID
- `start_time` (string, optional): Start time (ISO 8601)
- `end_time` (string, optional): End time (ISO 8601)
- `time_bucket` (string, optional): Bucket size (1m, 5m, 1h, 1d) (default: "5m")

**Example:**
```python
metrics = await get_api_metrics(
    gateway_id="550e8400-e29b-41d4-a716-446655440000",
    api_id="660e8400-e29b-41d4-a716-446655440001",
    time_bucket="1h"
)
```

---

### 5. Security (3 tools)

#### `scan_api_security`
Scan API for security vulnerabilities using hybrid analysis.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, required): API UUID

**Returns:**
```json
{
  "scan_id": "...",
  "api_id": "...",
  "vulnerabilities_found": 3,
  "severity_breakdown": {
    "critical": 1,
    "high": 2
  },
  "vulnerabilities": [...],
  "remediation_plan": {...}
}
```

#### `list_vulnerabilities`
List vulnerabilities with optional filters.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, optional): Filter by API
- `status` (string, optional): Filter by status
- `severity` (string, optional): Filter by severity
- `limit` (int, optional): Maximum results (default: 100)

#### `remediate_vulnerability`
Automatically remediate a vulnerability.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `vulnerability_id` (string, required): Vulnerability UUID
- `remediation_strategy` (string, optional): Specific strategy

---

### 6. Compliance (2 tools)

#### `scan_api_compliance`
Scan API for compliance violations across 5 regulatory standards.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, required): API UUID
- `standards` (list, optional): Specific standards (GDPR, HIPAA, SOC2, PCI_DSS, ISO_27001)

**Example:**
```python
result = await scan_api_compliance(
    gateway_id="550e8400-e29b-41d4-a716-446655440000",
    api_id="660e8400-e29b-41d4-a716-446655440001",
    standards=["GDPR", "HIPAA"]
)
```

#### `generate_audit_report`
Generate comprehensive audit report.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, optional): Filter by API
- `standard` (string, optional): Filter by standard
- `start_date` (string, optional): Report start date (ISO 8601)
- `end_date` (string, optional): Report end date (ISO 8601)

---

### 7. Optimization (2 tools)

#### `generate_recommendations`
Generate AI-driven optimization recommendations.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, required): API UUID
- `min_impact` (float, optional): Minimum improvement % (default: 10.0)

#### `list_recommendations`
List optimization recommendations.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, optional): Filter by API
- `priority` (string, optional): Filter by priority
- `status` (string, optional): Filter by status
- `page` (int, optional): Page number (default: 1)
- `page_size` (int, optional): Items per page (default: 20)

---

### 8. Rate Limiting (1 tool)

#### `create_rate_limit_policy`
Create intelligent rate limit policy.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, required): API UUID
- `policy_name` (string, required): Policy name
- `policy_type` (string, required): Policy type (fixed, adaptive, priority_based)
- `limit_thresholds` (dict, required): Threshold configuration
- `enforcement_action` (string, optional): Action (throttle, reject, queue)

**Example:**
```python
policy = await create_rate_limit_policy(
    gateway_id="550e8400-e29b-41d4-a716-446655440000",
    api_id="660e8400-e29b-41d4-a716-446655440001",
    policy_name="Production Rate Limit",
    policy_type="adaptive",
    limit_thresholds={
        "requests_per_second": 100,
        "requests_per_minute": 5000
    },
    enforcement_action="throttle"
)
```

---

### 9. Predictions (2 tools)

#### `list_predictions`
List failure predictions with filters.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `api_id` (string, optional): Filter by API
- `severity` (string, optional): Filter by severity
- `status` (string, optional): Filter by status
- `page` (int, optional): Page number (default: 1)
- `page_size` (int, optional): Items per page (default: 20)

#### `get_prediction`
Get detailed prediction information.

**Parameters:**
- `gateway_id` (string, required): Gateway UUID
- `prediction_id` (string, required): Prediction UUID

---

### 10. Natural Language Query (1 tool)

#### `execute_query`
Execute natural language query across all data.

**Parameters:**
- `query_text` (string, required): Natural language query
- `session_id` (string, optional): Conversation session ID

**Example:**
```python
result = await execute_query(
    query_text="Show me APIs with high error rates in the last 24 hours"
)
```

**Returns:**
```json
{
  "query_id": "...",
  "query_text": "...",
  "response_text": "Found 3 APIs with error rates above 5%...",
  "confidence_score": 0.92,
  "results": {...},
  "follow_up_queries": [
    "What is causing the errors?",
    "Show me the affected endpoints"
  ],
  "execution_time_ms": 1234
}
```

---

## Usage Examples

### Python (using MCP SDK)

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# Connect to unified server
server_params = StdioServerParameters(
    command="docker",
    args=["exec", "-i", "aip-mcp-unified", "python", "unified_server.py"],
)

async with stdio_client(server_params) as (read, write):
    async with ClientSession(read, write) as session:
        # Initialize
        await session.initialize()
        
        # List available tools
        tools = await session.list_tools()
        print(f"Available tools: {len(tools.tools)}")
        
        # Create a gateway
        result = await session.call_tool(
            "create_gateway",
            arguments={
                "name": "Production Gateway",
                "vendor": "kong",
                "base_url": "https://api.example.com"
            }
        )
        
        gateway_id = result.content[0].text["id"]
        
        # Sync APIs
        await session.call_tool(
            "sync_gateway",
            arguments={"gateway_id": gateway_id}
        )
        
        # List APIs
        apis = await session.call_tool(
            "list_apis",
            arguments={
                "gateway_id": gateway_id,
                "page_size": 50
            }
        )
        
        # Execute natural language query
        query_result = await session.call_tool(
            "execute_query",
            arguments={
                "query_text": "Which APIs have the highest error rates?"
            }
        )
        
        print(query_result.content[0].text["response_text"])
```

### JavaScript/TypeScript (using MCP SDK)

```typescript
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

// Connect to unified server
const transport = new StdioClientTransport({
  command: "docker",
  args: ["exec", "-i", "aip-mcp-unified", "python", "unified_server.py"],
});

const client = new Client(
  {
    name: "api-intelligence-client",
    version: "1.0.0",
  },
  {
    capabilities: {},
  }
);

await client.connect(transport);

// List tools
const tools = await client.listTools();
console.log(`Available tools: ${tools.tools.length}`);

// Execute query
const result = await client.callTool({
  name: "execute_query",
  arguments: {
    query_text: "Show me all critical security vulnerabilities",
  },
});

console.log(result.content[0].text);
```

---

## HTTP/REST Access

The unified server also exposes an HTTP endpoint for direct REST access:

```bash
# Health check
curl http://localhost:8007/health

# List tools (MCP protocol)
curl -X POST http://localhost:8007/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
  }'

# Call a tool
curl -X POST http://localhost:8007/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "list_gateways",
      "arguments": {
        "page": 1,
        "page_size": 10
      }
    }
  }'
```

---

## Deployment

### Docker Compose (Included)

The unified server is already configured in `docker-compose.yml`:

```yaml
mcp-unified:
  build:
    context: ./mcp-servers
    dockerfile: Dockerfile
  container_name: aip-mcp-unified
  environment:
    - BACKEND_URL=http://backend:8000
    - MCP_SERVER_NAME=unified
  ports:
    - "8007:8000"
  networks:
    - aip-network
  depends_on:
    - backend
```

### Start the Server

```bash
# Start all services including unified server
docker-compose up -d

# Check server health
curl http://localhost:8007/health

# View logs
docker-compose logs -f mcp-unified
```

### Standalone Deployment

```bash
# Set environment variables
export BACKEND_URL=http://backend:8000

# Install dependencies
pip install -r requirements.txt

# Run server
python unified_server.py
```

---

## Error Handling

All tools return consistent error responses:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {...}
}
```

Common error codes:
- `INVALID_INPUT`: Invalid parameters
- `NOT_FOUND`: Resource not found
- `BACKEND_ERROR`: Backend API error
- `CONNECTION_ERROR`: Backend connection failed

---

## Best Practices

1. **Use Session IDs**: For natural language queries, maintain session IDs for context
2. **Pagination**: Always use pagination for list operations
3. **Error Handling**: Check for error fields in responses
4. **Health Checks**: Monitor server health before operations
5. **Rate Limiting**: Be mindful of backend API rate limits
6. **Batch Operations**: Use bulk operations when available (e.g., bulk gateway sync)

---

## Comparison with Specialized Servers

| Feature | Unified Server | Specialized Servers |
|---------|---------------|---------------------|
| **Connection Points** | 1 (port 8007) | 6 (ports 8001-8006) |
| **Tool Count** | 25+ | 3-5 per server |
| **Coverage** | Complete | Domain-specific |
| **Use Case** | External workflows | Internal microservices |
| **Complexity** | Low | Medium |
| **Maintenance** | Single codebase | Multiple codebases |

**Recommendation**: Use the unified server for external AI agents and standalone workflows. Use specialized servers for internal microservices that only need specific domains.

---

## Support

For issues or questions:
- Check server logs: `docker-compose logs mcp-unified`
- Verify backend connectivity: `curl http://localhost:8000/health`
- Review tool documentation in this file
- Check MCP protocol specification: https://modelcontextprotocol.io

---

## Version History

- **v1.0.0** (2026-04-22): Initial release with 25+ tools across 9 domains

---

Made with Bob 🤖