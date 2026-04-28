# MCP Server Architecture

> 📊 **Enhanced Diagrams**: See [MCP Architecture Diagrams](diagrams/mcp-architecture.md) for comprehensive visual documentation including:
> - MCP Server Architecture Overview
> - Thin Wrapper Pattern (Before/After)
> - Discovery, Metrics, and Optimization Server Architecture
> - MCP Communication Flow
> - Backend Client Architecture
> - Health Check Architecture
> - Error Handling Flow
> - Configuration & Environment
> - Integration with AI Agents

## Overview

The MCP (Model Context Protocol) servers in the API Intelligence Plane have been refactored to follow a **thin wrapper architecture pattern**. This document describes the new architecture, its benefits, and implementation details.

## Architecture Pattern: Thin Wrapper

### Before Refactoring

Previously, MCP servers directly accessed OpenSearch, creating architectural redundancy:

```
┌─────────────┐
│ AI Agents   │
└──────┬──────┘
       │ MCP Protocol
       ▼
┌─────────────────┐
│  MCP Servers    │
│  - Discovery    │
│  - Metrics      │──────┐
│  - Optimization │      │ Direct Access
└─────────────────┘      │
                         ▼
       ┌─────────────────────────┐
       │     OpenSearch          │
       └─────────────────────────┘
                         ▲
                         │ Direct Access
┌─────────────────┐      │
│ Backend Services│──────┘
└─────────────────┘
```

**Problems:**
- Duplicate business logic in MCP servers and backend
- Data consistency risks
- Maintenance overhead (changes needed in multiple places)
- No centralized validation or security enforcement

### After Refactoring

MCP servers now act as thin protocol adapters that delegate to backend services:

```
┌─────────────┐
│ AI Agents   │
└──────┬──────┘
       │ MCP Protocol
       ▼
┌─────────────────┐
│  MCP Servers    │
│  (Thin Wrapper) │
│  - Discovery    │
│  - Metrics      │
│  - Optimization │
└────────┬────────┘
         │ HTTP/REST
         ▼
┌─────────────────┐
│ Backend Services│
│ (Single Source  │
│  of Truth)      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   OpenSearch    │
└─────────────────┘
```

**Benefits:**
- ✅ Single source of truth for business logic
- ✅ Consistent data validation and security
- ✅ Easier maintenance and testing
- ✅ Centralized audit logging and rate limiting
- ✅ Clear separation of concerns

## Components

### 1. Backend Client (`mcp-servers/common/backend_client.py`)

A reusable HTTP client that provides methods for communicating with the FastAPI backend REST API.

**Key Features:**
- Async HTTP client using `httpx`
- Automatic error handling and logging
- Type-safe method signatures
- Configurable base URL and timeouts

**Example Usage:**
```python
from common.backend_client import BackendClient

# Initialize client
client = BackendClient(base_url="http://backend:8000")

# List APIs
response = await client.list_apis(
    gateway_id="uuid-here",
    page_size=100
)

# Get metrics
metrics = await client.get_api_metrics(
    api_id="uuid-here",
    start_time="2024-01-01T00:00:00Z",
    end_time="2024-01-02T00:00:00Z",
    interval="5m"
)

# Close client
await client.close()
```

### 2. Unified MCP Server (`mcp-servers/unified_server.py`)

**Note**: Individual MCP servers have been consolidated into a single Unified MCP Server. See `mcp-servers/README_UNIFIED_SERVER.md` for details.

The Unified MCP Server provides all functionality previously split across multiple servers:

**Port:** 8001  
**Transport:** Streamable HTTP

**Tools Provided:**
- `health()` - Check server health and backend connectivity
- `server_info()` - Get server metadata and capabilities
- `discover_apis(gateway_id, force_refresh)` - Discover APIs from a gateway
- `get_api_inventory(gateway_id, status, is_shadow, health_score_min, limit)` - Get API inventory with filters
- `search_apis(query, filters)` - Search APIs by name, path, or tags

**Implementation:**
- Delegates to backend `/api/v1/apis` endpoints
- Performs client-side filtering for advanced queries
- No direct OpenSearch access


**Port:** 8002  
**Transport:** Streamable HTTP

**Tools Provided:**
- `health()` - Check server health and backend connectivity
- `server_info()` - Get server metadata and capabilities
- `collect_metrics(gateway_id, api_ids)` - Collect metrics from a gateway
- `get_metrics_timeseries(api_id, start_time, end_time, interval, metrics)` - Get time-series metrics
- `analyze_trends(api_id, metric, lookback_hours)` - Analyze metric trends

**Implementation:**
- Delegates to backend `/api/v1/apis/{api_id}/metrics` endpoints
- Performs client-side trend analysis
- No direct OpenSearch access


**Port:** 8004  
**Transport:** Streamable HTTP

**Tools Provided:**
- `health()` - Check server health and backend connectivity
- `server_info()` - Get server metadata and capabilities
- `generate_predictions(api_id, prediction_window_hours, min_confidence)` - Generate failure predictions
- `generate_optimization_recommendations(api_id, focus_areas, min_impact_percentage)` - Generate optimization recommendations
- `manage_rate_limit(api_id, policy_type, limit_thresholds, enforcement_action)` - Create/update rate limit policy
- `analyze_rate_limit_effectiveness(api_id, policy_id, analysis_period_hours)` - Analyze rate limit effectiveness

**Implementation:**
- Delegates to backend `/api/v1/predictions`, `/api/v1/recommendations`, and `/api/v1/rate-limits` endpoints
- No direct OpenSearch access
- All business logic handled by backend services

## Configuration

### Environment Variables

MCP servers use the following environment variables:

```bash
# Backend API URL (default: http://backend:8000)
BACKEND_URL=http://backend:8000

# Server ports (defaults shown)
DISCOVERY_PORT=8001
METRICS_PORT=8002
OPTIMIZATION_PORT=8004

# HTTP client settings
HTTP_TIMEOUT=30.0
VERIFY_SSL=true
```

### Docker Compose Configuration

```yaml
services:
  mcp-discovery:
    build: ./mcp-servers
    command: python discovery_server.py
    environment:
      - BACKEND_URL=http://backend:8000
    ports:
      - "8001:8001"
    depends_on:
      - backend

  mcp-metrics:
    build: ./mcp-servers
    command: python metrics_server.py
    environment:
      - BACKEND_URL=http://backend:8000
    ports:
      - "8002:8002"
    depends_on:
      - backend

  mcp-optimization:
    build: ./mcp-servers
    command: python optimization_server.py
    environment:
      - BACKEND_URL=http://backend:8000
    ports:
      - "8004:8004"
    depends_on:
      - backend
```

## Data Flow

### Example: Discovering APIs

1. **AI Agent** sends MCP request to Discovery Server:
   ```json
   {
     "tool": "discover_apis",
     "arguments": {
       "gateway_id": "550e8400-e29b-41d4-a716-446655440000"
     }
   }
   ```

2. **Discovery MCP Server** receives request and calls Backend Client:
   ```python
   response = await self.backend_client.list_apis(
       gateway_id=gateway_id,
       page_size=1000
   )
   ```

3. **Backend Client** makes HTTP request to Backend API:
   ```
   GET /api/v1/apis?gateway_id=550e8400-e29b-41d4-a716-446655440000&page_size=1000
   ```

4. **Backend Service** processes request:
   - Validates gateway_id
   - Queries OpenSearch via repository
   - Applies business logic
   - Returns formatted response

5. **Discovery MCP Server** formats response for AI agent:
   ```json
   {
     "discovered_count": 42,
     "shadow_apis_count": 3,
     "apis": [...],
     "discovery_time_ms": 150
   }
   ```

## Testing

### Unit Tests

Test MCP servers with mocked backend client:

```python
import pytest
from unittest.mock import AsyncMock, patch
from discovery_server import DiscoveryMCPServer

@pytest.mark.asyncio
async def test_discover_apis():
    server = DiscoveryMCPServer()
    
    # Mock backend client
    server.backend_client.list_apis = AsyncMock(return_value={
        "items": [{"id": "1", "name": "API 1"}],
        "total": 1
    })
    
    # Test tool
    result = await server._discover_apis_impl("gateway-id", False)
    
    assert result["discovered_count"] == 1
    assert len(result["apis"]) == 1
```

### Integration Tests

Test end-to-end flow with real backend:

```python
import pytest
import httpx
from discovery_server import DiscoveryMCPServer

@pytest.mark.asyncio
async def test_discover_apis_integration():
    # Start backend and MCP server
    server = DiscoveryMCPServer()
    await server.initialize()
    
    try:
        # Test discovery
        result = await server._discover_apis_impl("test-gateway-id", False)
        
        assert "discovered_count" in result
        assert "apis" in result
    finally:
        await server.cleanup()
```

## Migration Guide

### For Developers

If you need to add a new MCP tool:

1. **Add backend endpoint first** (if needed):
   ```python
   # backend/app/api/v1/my_endpoint.py
   @router.get("/my-endpoint")
   async def my_endpoint():
       # Implementation
       pass
   ```

2. **Add method to BackendClient**:
   ```python
   # mcp-servers/common/backend_client.py
   async def my_endpoint(self, param: str) -> Dict[str, Any]:
       return await self._request("GET", "/my-endpoint", params={"param": param})
   ```

3. **Add tool to MCP server**:
   ```python
   # mcp-servers/my_server.py
   @self.tool(description="My new tool")
   async def my_tool(param: str) -> dict[str, Any]:
       return await self.backend_client.my_endpoint(param)
   ```

### For Operations

No changes required to deployment or infrastructure. The refactored MCP servers are drop-in replacements with the same:
- Port numbers
- Transport protocols
- Tool signatures
- Response formats

## Performance Considerations

### Latency

- **Added latency:** ~10-50ms per request (HTTP overhead)
- **Mitigated by:** Connection pooling, keep-alive, async I/O
- **Trade-off:** Acceptable for consistency and maintainability benefits

### Scalability

- MCP servers can scale independently of backend
- Backend handles all heavy lifting (OpenSearch queries, business logic)
- MCP servers are stateless and lightweight

### Caching

Future optimization: Add caching layer in MCP servers for frequently accessed data:

```python
from functools import lru_cache
from datetime import datetime, timedelta

class CachedBackendClient(BackendClient):
    def __init__(self):
        super().__init__()
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)
    
    async def list_apis(self, **kwargs):
        cache_key = f"list_apis:{kwargs}"
        
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if datetime.utcnow() - cached_time < self._cache_ttl:
                return cached_data
        
        result = await super().list_apis(**kwargs)
        self._cache[cache_key] = (result, datetime.utcnow())
        return result
```

## Troubleshooting

### MCP Server Can't Connect to Backend

**Symptoms:**
- Health check returns "degraded" status
- Tools return connection errors

**Solutions:**
1. Check `BACKEND_URL` environment variable
2. Verify backend service is running
3. Check network connectivity between containers
4. Review backend logs for errors

### Slow Response Times

**Symptoms:**
- Tools take >5 seconds to respond
- Timeout errors

**Solutions:**
1. Check backend performance
2. Review OpenSearch query performance
3. Increase `HTTP_TIMEOUT` setting
4. Consider adding caching layer

### Data Inconsistency

**Symptoms:**
- MCP tools return different data than frontend
- Stale data in responses

**Solutions:**
1. Verify all services use same backend API
2. Check for caching issues
3. Review backend data validation logic

## Future Enhancements

1. **Response Caching:** Add intelligent caching in MCP servers
2. **Request Batching:** Batch multiple backend requests
3. **Circuit Breaker:** Add circuit breaker pattern for backend failures
4. **Metrics Collection:** Add detailed performance metrics
5. **GraphQL Support:** Consider GraphQL for more efficient data fetching

## References

- [Model Context Protocol Specification](https://modelcontextprotocol.io/)
- [FastMCP Documentation](https://github.com/jlowin/fastmcp)
- [Backend API Documentation](../backend/README.md)
- [Architecture Decision Records](./adr/)

---

**Last Updated:** 2026-03-12  
**Version:** 2.0.0  
**Status:** Implemented