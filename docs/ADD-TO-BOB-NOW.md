# Add MCP Servers to Current Bob IDE Instance

## Quick Setup Instructions

### Method 1: Using Bob's MCP Settings UI (Recommended)

1. **Open Bob Settings**
   - Click the Bob icon in VSCode sidebar
   - Click the gear icon (⚙️) or go to Settings
   - Navigate to "MCP Servers" section

2. **Add Each Server**

#### Server 1: API Discovery
```
Name: api-discovery
Command: npx
Arguments: -y @modelcontextprotocol/server-streamable-http http://localhost:8001/mcp
Description: API Discovery and Inventory Management
```

#### Server 2: API Metrics  
```
Name: api-metrics
Command: npx
Arguments: -y @modelcontextprotocol/server-streamable-http http://localhost:8002/mcp
Description: API Metrics Collection and Analysis
```

#### Server 3: API Optimization
```
Name: api-optimization
Command: npx
Arguments: -y @modelcontextprotocol/server-streamable-http http://localhost:8004/mcp
Description: API Optimization and Predictions
```

3. **Save and Reload**
   - Click "Save" or "Apply"
   - Reload Bob IDE window if needed

---

### Method 2: Direct JSON Configuration

If Bob supports direct JSON configuration, copy this entire block:

```json
{
  "mcpServers": {
    "api-discovery": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-streamable-http", "http://localhost:8001/mcp"],
      "disabled": false
    },
    "api-metrics": {
      "command": "npx", 
      "args": ["-y", "@modelcontextprotocol/server-streamable-http", "http://localhost:8002/mcp"],
      "disabled": false
    },
    "api-optimization": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-streamable-http", "http://localhost:8004/mcp"],
      "disabled": false
    }
  }
}
```

---

### Method 3: Alternative HTTP Configuration

If the above doesn't work, try this simpler format:

```json
{
  "mcpServers": {
    "api-discovery": {
      "url": "http://localhost:8001/mcp",
      "transport": "streamable-http"
    },
    "api-metrics": {
      "url": "http://localhost:8002/mcp",
      "transport": "streamable-http"
    },
    "api-optimization": {
      "url": "http://localhost:8004/mcp",
      "transport": "streamable-http"
    }
  }
}
```

---

## Verification

After adding the servers, verify they're working:

### Test Query 1: Check Server Info
```
"What MCP servers are available?"
```

### Test Query 2: Use Discovery Server
```
"Show me all APIs in the system"
```

### Test Query 3: Use Metrics Server
```
"What are the current API metrics?"
```

### Test Query 4: Use Optimization Server
```
"Generate traffic predictions for the next week"
```

---

## Troubleshooting

### If servers don't appear:
1. Check Docker containers are running:
   ```bash
   docker-compose ps | grep mcp
   ```
   All should show `(healthy)`

2. Test connectivity:
   ```bash
   curl -s http://localhost:8001/mcp | grep jsonrpc
   curl -s http://localhost:8002/mcp | grep jsonrpc
   curl -s http://localhost:8004/mcp | grep jsonrpc
   ```

3. Check Bob logs for connection errors

### If tools don't work:
1. Ensure backend is running:
   ```bash
   curl http://localhost:8000/api/v1/apis
   ```

2. Check server logs:
   ```bash
   docker-compose logs mcp-discovery
   ```

---

## Available Tools After Setup

### Discovery Server (5 tools)
- `health` - Check server health
- `server_info` - Get server information
- `discover_apis` - Discover APIs from gateways
- `get_api_inventory` - Get API inventory with filters
- `search_apis` - Search APIs by query

### Metrics Server (5 tools)
- `health` - Check server health
- `server_info` - Get server information
- `collect_metrics` - Collect current metrics
- `get_metrics_timeseries` - Get time-series data
- `analyze_trends` - Analyze metric trends

### Optimization Server (6 tools)
- `health` - Check server health
- `server_info` - Get server information
- `generate_predictions` - Generate predictions
- `generate_optimization_recommendations` - Get recommendations
- `manage_rate_limit` - Manage rate limits
- `analyze_rate_limit_effectiveness` - Analyze rate limits

---

## Example Queries to Try

Once configured, you can use natural language:

```
"Find all payment APIs"
"What's the response time for API abc123?"
"Predict traffic for next week"
"Show me APIs with high error rates"
"Create a rate limit policy"
"What optimizations do you recommend?"
```

---

## Need Help?

- Full documentation: `docs/mcp-usage-guide.md`
- Configuration file: `docs/bob-ide-mcp-config.json`
- Test script: `mcp-servers/tests/test_mcp_connection.py`