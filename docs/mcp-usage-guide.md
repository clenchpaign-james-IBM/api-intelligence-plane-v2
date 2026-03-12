# MCP Servers Usage Guide

This guide provides examples for using the API Intelligence Plane MCP servers and configuration instructions for IBM Bob IDE.

## Table of Contents

1. [MCP Server Overview](#mcp-server-overview)
2. [Query Examples](#query-examples)
3. [Bob IDE Configuration](#bob-ide-configuration)
4. [Python Client Examples](#python-client-examples)

---

## MCP Server Overview

The API Intelligence Plane provides three MCP servers:

| Server | Port | Purpose | Tools |
|--------|------|---------|-------|
| **Discovery** | 8001 | API discovery and inventory management | 5 tools |
| **Metrics** | 8002 | API metrics collection and analysis | 5 tools |
| **Optimization** | 8004 | Predictions and optimization recommendations | 6 tools |

All servers use the **Streamable HTTP** transport protocol.

---

## Query Examples

### Discovery Server Examples

#### Example 1: Get Server Information
```
Query: "What capabilities does the discovery server have?"

Expected Tool Call: server_info()

Response: Server metadata including version, architecture, and capabilities
```

#### Example 2: Discover APIs from a Gateway
```
Query: "Discover all APIs from gateway abc123"

Expected Tool Call: discover_apis(gateway_id="abc123")

Response: List of discovered APIs with shadow API detection
```

#### Example 3: Search for Specific APIs
```
Query: "Find all payment-related APIs"

Expected Tool Call: search_apis(query="payment")

Response: Ranked list of APIs matching "payment" in name, path, or description
```

#### Example 4: Get API Inventory with Filters
```
Query: "Show me all active APIs with health score above 0.8"

Expected Tool Call: get_api_inventory(status="active", health_score_min=0.8)

Response: Filtered list of APIs meeting the criteria
```

#### Example 5: Check Server Health
```
Query: "Is the discovery server healthy?"

Expected Tool Call: health()

Response: Health status including backend connectivity
```

---

### Metrics Server Examples

#### Example 1: Collect Current Metrics
```
Query: "Collect metrics for all APIs in gateway xyz789"

Expected Tool Call: collect_metrics(gateway_id="xyz789")

Response: Aggregated metrics including response times, throughput, error rates
```

#### Example 2: Get Time-Series Data
```
Query: "Show me response time trends for API def456 over the last 24 hours"

Expected Tool Call: get_metrics_timeseries(
    api_id="def456",
    start_time="2026-03-11T14:00:00Z",
    end_time="2026-03-12T14:00:00Z",
    interval="1h",
    metrics=["response_time_p50", "response_time_p95"]
)

Response: Time-series data points with timestamps
```

#### Example 3: Analyze Performance Trends
```
Query: "Analyze error rate trends for API ghi789 over the past week"

Expected Tool Call: analyze_trends(
    api_id="ghi789",
    metric="error_rate",
    lookback_hours=168
)

Response: Trend analysis with direction, strength, and anomaly detection
```

#### Example 4: Monitor Multiple APIs
```
Query: "Get current metrics for APIs api1, api2, and api3"

Expected Tool Call: collect_metrics(api_ids=["api1", "api2", "api3"])

Response: Metrics summary for specified APIs
```

---

### Optimization Server Examples

#### Example 1: Generate Traffic Predictions
```
Query: "Predict traffic for API jkl012 for the next 7 days"

Expected Tool Call: generate_predictions(
    api_id="jkl012",
    prediction_type="traffic",
    horizon_hours=168
)

Response: Traffic predictions with confidence intervals
```

#### Example 2: Get Optimization Recommendations
```
Query: "What optimizations do you recommend for API mno345?"

Expected Tool Call: generate_optimization_recommendations(
    api_id="mno345",
    focus_areas=["performance", "cost", "reliability"]
)

Response: Prioritized list of optimization recommendations
```

#### Example 3: Create Rate Limit Policy
```
Query: "Set a rate limit of 1000 requests per minute for API pqr678"

Expected Tool Call: manage_rate_limit(
    api_id="pqr678",
    action="create",
    limit=1000,
    window="1m"
)

Response: Created rate limit policy details
```

#### Example 4: Analyze Rate Limit Effectiveness
```
Query: "How effective is the rate limit policy for API stu901?"

Expected Tool Call: analyze_rate_limit_effectiveness(api_id="stu901")

Response: Analysis of rate limit impact on traffic and errors
```

#### Example 5: Predict Error Rates
```
Query: "Predict error rates for API vwx234 for the next 24 hours"

Expected Tool Call: generate_predictions(
    api_id="vwx234",
    prediction_type="errors",
    horizon_hours=24
)

Response: Error rate predictions with anomaly alerts
```

---

## Bob IDE Configuration

### Configuration for IBM Bob IDE

To use these MCP servers in IBM Bob IDE, add the following configuration to your Bob settings:

#### Option 1: Using Bob's MCP Settings UI

1. Open Bob IDE Settings
2. Navigate to "MCP Servers" section
3. Click "Add Server" for each server below

#### Option 2: Manual Configuration (JSON)

Add this to your Bob IDE configuration file (typically `~/.bob/config.json` or workspace `.bob/mcp.json`):

```json
{
  "mcpServers": {
    "api-discovery": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-streamable-http",
        "http://localhost:8001/mcp"
      ],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    },
    "api-metrics": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-streamable-http",
        "http://localhost:8002/mcp"
      ],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    },
    "api-optimization": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-streamable-http",
        "http://localhost:8004/mcp"
      ],
      "env": {},
      "disabled": false,
      "alwaysAllow": []
    }
  }
}
```

### Alternative: Direct HTTP Configuration

If Bob supports direct HTTP MCP connections, use:

```json
{
  "mcpServers": {
    "api-discovery": {
      "url": "http://localhost:8001/mcp",
      "transport": "streamable-http",
      "disabled": false
    },
    "api-metrics": {
      "url": "http://localhost:8002/mcp",
      "transport": "streamable-http",
      "disabled": false
    },
    "api-optimization": {
      "url": "http://localhost:8004/mcp",
      "transport": "streamable-http",
      "disabled": false
    }
  }
}
```

### Configuration Notes

- **Ports**: Ensure Docker containers are running and ports 8001, 8002, 8004 are accessible
- **Network**: If Bob IDE is running in a container, use `host.docker.internal` instead of `localhost`
- **Auto-allow**: Add frequently used tools to `alwaysAllow` array to skip confirmation prompts

### Example with Auto-Allow

```json
{
  "mcpServers": {
    "api-discovery": {
      "url": "http://localhost:8001/mcp",
      "transport": "streamable-http",
      "disabled": false,
      "alwaysAllow": [
        "server_info",
        "health",
        "search_apis"
      ]
    }
  }
}
```

---

## Python Client Examples

### Basic Connection Example

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def query_discovery_server():
    """Connect to Discovery server and list APIs."""
    async with streamable_http_client("http://localhost:8001/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print(f"Available tools: {[t.name for t in tools.tools]}")
            
            # Call a tool
            result = await session.call_tool("search_apis", {
                "query": "payment",
                "filters": {"status": "active"}
            })
            print(f"Search results: {result.content}")

# Run the example
asyncio.run(query_discovery_server())
```

### Multi-Server Query Example

```python
import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

async def analyze_api_performance(api_id: str):
    """Analyze API performance using multiple MCP servers."""
    
    # Get API details from Discovery server
    async with streamable_http_client("http://localhost:8001/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            inventory = await session.call_tool("get_api_inventory", {
                "limit": 1
            })
            print(f"API Details: {inventory.content}")
    
    # Get metrics from Metrics server
    async with streamable_http_client("http://localhost:8002/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            metrics = await session.call_tool("collect_metrics", {
                "api_ids": [api_id]
            })
            print(f"Current Metrics: {metrics.content}")
    
    # Get recommendations from Optimization server
    async with streamable_http_client("http://localhost:8004/mcp") as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            recommendations = await session.call_tool(
                "generate_optimization_recommendations",
                {
                    "api_id": api_id,
                    "focus_areas": ["performance", "reliability"]
                }
            )
            print(f"Recommendations: {recommendations.content}")

# Run the analysis
asyncio.run(analyze_api_performance("your-api-id-here"))
```

---

## Natural Language Query Examples for Bob IDE

Once configured in Bob IDE, you can use natural language queries:

### Discovery Queries
```
"Show me all APIs in the system"
"Find APIs related to authentication"
"What shadow APIs have been detected?"
"List all deprecated APIs"
"Discover new APIs from gateway xyz"
```

### Metrics Queries
```
"What's the average response time for API abc123?"
"Show me error rate trends for the payment API"
"Get performance metrics for all APIs in the last hour"
"Which APIs have the highest latency?"
"Analyze traffic patterns for API def456"
```

### Optimization Queries
```
"Predict traffic for API ghi789 next week"
"What optimizations do you recommend for slow APIs?"
"Create a rate limit policy for API jkl012"
"How effective are the current rate limits?"
"Predict when API mno345 will experience high load"
```

---

## Troubleshooting

### Connection Issues

If Bob IDE cannot connect to MCP servers:

1. **Check Docker containers are running:**
   ```bash
   docker-compose ps | grep mcp
   ```
   All should show `(healthy)` status

2. **Test connectivity manually:**
   ```bash
   curl -s http://localhost:8001/mcp | grep jsonrpc
   ```

3. **Check firewall/network:**
   - Ensure ports 8001, 8002, 8004 are not blocked
   - If Bob is in Docker, use `host.docker.internal` instead of `localhost`

4. **View server logs:**
   ```bash
   docker-compose logs mcp-discovery
   docker-compose logs mcp-metrics
   docker-compose logs mcp-optimization
   ```

### Tool Execution Errors

If tools fail to execute:

1. **Check backend is running:**
   ```bash
   curl http://localhost:8000/api/v1/apis
   ```

2. **Verify data exists:**
   - MCP servers delegate to backend APIs
   - Ensure backend has data (APIs, metrics, etc.)

3. **Check tool parameters:**
   - Review tool schemas in server logs
   - Ensure required parameters are provided

---

## Additional Resources

- **MCP Protocol Specification**: https://modelcontextprotocol.io
- **FastMCP Documentation**: https://gofastmcp.com
- **API Intelligence Plane Architecture**: See `docs/mcp-architecture.md`
- **Backend API Documentation**: See `docs/query-service.md`

---

## Support

For issues or questions:
1. Check server logs: `docker-compose logs mcp-<server-name>`
2. Run connection tests: `python mcp-servers/tests/test_mcp_connection.py`
3. Review architecture docs: `docs/mcp-architecture.md`