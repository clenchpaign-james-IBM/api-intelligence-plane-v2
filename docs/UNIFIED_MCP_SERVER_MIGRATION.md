# Unified MCP Server Migration

**Date**: 2026-04-27  
**Status**: Complete

## Overview

The API Intelligence Plane has migrated from multiple specialized MCP servers to a single **Unified MCP Server** that provides all functionality through one interface.

## What Changed

### Removed Servers

The following individual MCP servers have been **removed**:

1. `mcp-servers/discovery_server.py` (Port 8001)
2. `mcp-servers/metrics_server.py` (Port 8002)
3. `mcp-servers/security_server.py` (Port 8003)
4. `mcp-servers/optimization_server.py` (Port 8004)
5. `mcp-servers/compliance_server.py` (Port 8005)
6. `mcp-servers/prediction_server.py` (Port 8006)

### New Server

**Unified MCP Server**: `mcp-servers/unified_server.py` (Port 8007)

- Provides **all** functionality from the removed servers
- Single connection point for external AI agents
- 80+ tools covering all domains
- Consistent interface and error handling

## Migration Guide

### For Users

**Before** (connecting to multiple servers):
```python
# Had to connect to 6 different servers
discovery_client = connect_to_mcp("localhost:8001")
metrics_client = connect_to_mcp("localhost:8002")
security_client = connect_to_mcp("localhost:8003")
# ... etc
```

**After** (single unified server):
```python
# Connect to one server for everything
unified_client = connect_to_mcp("localhost:8007")
```

### For Developers

All tools from individual servers are now available in the unified server:

- **Gateway Management**: create_gateway, list_gateways, sync_gateway, etc.
- **API Discovery**: list_apis, search_apis, get_api, etc.
- **Metrics**: get_api_metrics, get_analytics_metrics, drill_down_to_logs, etc.
- **Security**: scan_api_security, list_vulnerabilities, remediate_vulnerability, etc.
- **Compliance**: scan_api_compliance, generate_audit_report, get_compliance_posture, etc.
- **Optimization**: generate_recommendations, apply_recommendation, etc.
- **Rate Limiting**: create_rate_limit_policy, analyze_rate_limit_effectiveness, etc.
- **Predictions**: list_predictions, get_prediction, get_prediction_explanation, etc.
- **Natural Language Query**: execute_query, create_query_session, etc.

## Documentation Updates Required

The following documentation files contain references to the old individual servers and should be considered **historical**:

### Analysis Documents (Historical Reference)
- `docs/discovery-mcp-server-analysis.md`
- `docs/security-mcp-server-vendor-neutral-analysis.md`
- `docs/security-mcp-server-comprehensive-analysis.md`
- `docs/optimization-mcp-server-vendor-neutral-analysis.md`
- `docs/prediction-mcp-server-analysis.md`
- `docs/compliance-mcp-server-comprehensive-analysis.md`
- `docs/security-remediation-plan-analysis.md`

### Architecture Documents (Update Required)
- `docs/mcp-architecture.md` - Update to reflect unified server
- `docs/business-context.md` - Update MCP server section
- `docs/engineering.md` - Update MCP server references

### Specification Documents (Update Required)
- `specs/001-api-intelligence-plane/plan.md` - Update architecture section
- `specs/001-api-intelligence-plane/tasks.md` - Mark old server tasks as obsolete
- `specs/001-api-intelligence-plane/quickstart.md` - Update startup instructions

## Current Documentation

For up-to-date information on the Unified MCP Server, see:

- **Primary Documentation**: `mcp-servers/README_UNIFIED_SERVER.md`
- **Tool Reference**: All 80+ tools documented in unified_server.py
- **Usage Examples**: See README_UNIFIED_SERVER.md

## Docker Compose

### Development (`docker-compose.yml`)
```yaml
mcp-unified:
  container_name: aip-mcp-unified
  ports:
    - "8007:8000"
  environment:
    - BACKEND_URL=http://backend:8000
    - MCP_SERVER_NAME=unified
```

### Production with TLS (`docker-compose-tls.yml`)
```yaml
mcp-unified:
  container_name: aip-mcp-unified-tls
  ports:
    - "8007:8000"
  environment:
    - TLS_ENABLED=true
    - BACKEND_URL=https://backend:8000
    - MCP_SERVER_NAME=unified
```

## Benefits

1. **Simplified Architecture**: One server instead of six
2. **Easier Maintenance**: Single codebase to maintain
3. **Better Performance**: Reduced connection overhead
4. **Consistent Interface**: Uniform error handling and responses
5. **Complete Coverage**: All 80+ tools in one place

## Backward Compatibility

**Note**: The individual MCP servers are **no longer available**. All integrations must migrate to the unified server.

## Support

For questions or issues:
- Check `mcp-servers/README_UNIFIED_SERVER.md`
- Review tool documentation in `unified_server.py`
- Check server logs: `docker-compose logs mcp-unified`

---

**Migration Complete**: All individual MCP servers have been removed. Use the Unified MCP Server for all functionality.