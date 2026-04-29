# MCP Server Contract: API Intelligence Plane

**Version**: 1.0  
**Transport**: Streamable HTTP  
**Base URL**: `http://localhost:8001`  
**Date**: 2026-04-28

## Overview

The MCP (Model Context Protocol) Server provides a unified external integration interface for AI agents and automation tools. It exposes all platform capabilities through MCP tools and resources, enabling programmatic access to gateway management, API discovery, metrics, security, compliance, predictions, and optimization features.

## MCP Protocol

The server implements the Model Context Protocol specification:
- **Protocol Version**: 2024-11-05
- **Transport**: Streamable HTTP (SSE)
- **Authentication**: Bearer token via HTTP headers
- **Content Type**: `application/json`

## Connection

### Endpoint
```
POST /sse
```

### Headers
```
Authorization: Bearer <token>
Content-Type: application/json
```

### Initialization
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": "2024-11-05",
    "capabilities": {
      "tools": {},
      "resources": {}
    },
    "clientInfo": {
      "name": "AI Agent",
      "version": "1.0.0"
    }
  }
}
```

---

## Available Tools

### 1. Gateway Management Tools

#### `register_gateway`
Register a new API Gateway for monitoring.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "name": {
      "type": "string",
      "description": "Gateway name"
    },
    "vendor": {
      "type": "string",
      "enum": ["webmethods", "kong", "apigee"],
      "description": "Gateway vendor"
    },
    "base_url": {
      "type": "string",
      "format": "uri",
      "description": "Gateway management API URL"
    },
    "connection_details": {
      "type": "object",
      "properties": {
        "host": {"type": "string"},
        "port": {"type": "integer"},
        "protocol": {"type": "string", "enum": ["http", "https"]},
        "auth_type": {"type": "string", "enum": ["basic", "token", "oauth2"]},
        "username": {"type": "string"},
        "password": {"type": "string"}
      },
      "required": ["host", "port", "protocol", "auth_type"]
    }
  },
  "required": ["name", "vendor", "base_url", "connection_details"]
}
```

**Example**:
```json
{
  "name": "Production WebMethods",
  "vendor": "webmethods",
  "base_url": "https://gateway.example.com",
  "connection_details": {
    "host": "gateway.example.com",
    "port": 443,
    "protocol": "https",
    "auth_type": "basic",
    "username": "admin",
    "password": "secret"
  }
}
```

**Output**:
```json
{
  "gateway_id": "uuid",
  "name": "Production WebMethods",
  "vendor": "webmethods",
  "status": "connected",
  "message": "Gateway registered successfully"
}
```

#### `list_gateways`
List all registered gateways.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "enum": ["connected", "disconnected", "error"],
      "description": "Filter by status"
    },
    "vendor": {
      "type": "string",
      "enum": ["webmethods", "kong", "apigee"],
      "description": "Filter by vendor"
    }
  }
}
```

**Output**:
```json
{
  "gateways": [
    {
      "gateway_id": "uuid",
      "name": "Production WebMethods",
      "vendor": "webmethods",
      "status": "connected",
      "statistics": {
        "total_apis": 150,
        "active_apis": 145,
        "shadow_apis": 5
      }
    }
  ],
  "total": 1
}
```

#### `get_gateway_status`
Get detailed status of a specific gateway.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "description": "Gateway identifier"
    }
  },
  "required": ["gateway_id"]
}
```

**Output**: Full gateway object with health and statistics

---

### 2. API Discovery Tools

#### `discover_apis`
Trigger API discovery for a gateway.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "description": "Gateway identifier"
    },
    "force_refresh": {
      "type": "boolean",
      "description": "Force full rediscovery",
      "default": false
    }
  },
  "required": ["gateway_id"]
}
```

**Output**:
```json
{
  "discovery_id": "uuid",
  "gateway_id": "uuid",
  "status": "in_progress",
  "started_at": "2026-04-28T16:20:00Z",
  "message": "Discovery started"
}
```

#### `list_apis`
List discovered APIs.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "description": "Filter by gateway"
    },
    "is_shadow_api": {
      "type": "boolean",
      "description": "Filter shadow APIs"
    },
    "maturity_state": {
      "type": "string",
      "enum": ["active", "deprecated", "beta", "alpha"],
      "description": "Filter by maturity state"
    },
    "search": {
      "type": "string",
      "description": "Search by name or description"
    }
  }
}
```

**Output**: List of API objects

#### `get_api_details`
Get detailed information about a specific API.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "description": "API identifier"
    }
  },
  "required": ["api_id"]
}
```

**Output**: Full API object with endpoints, policies, and health indicators

---

### 3. Metrics & Analytics Tools

#### `get_api_metrics`
Retrieve metrics for an API.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "description": "API identifier"
    },
    "time_bucket": {
      "type": "string",
      "enum": ["1min", "5min", "1hour", "1day"],
      "description": "Time resolution"
    },
    "start_time": {
      "type": "string",
      "format": "date-time",
      "description": "Start time (ISO 8601)"
    },
    "end_time": {
      "type": "string",
      "format": "date-time",
      "description": "End time (ISO 8601)"
    }
  },
  "required": ["api_id", "time_bucket", "start_time", "end_time"]
}
```

**Output**: Array of metric objects

#### `get_transactional_logs`
Retrieve transactional logs for drill-down analysis.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "description": "Gateway identifier"
    },
    "api_id": {
      "type": "string",
      "description": "API identifier (optional)"
    },
    "start_time": {
      "type": "string",
      "format": "date-time"
    },
    "end_time": {
      "type": "string",
      "format": "date-time"
    },
    "status_code": {
      "type": "integer",
      "description": "Filter by HTTP status code"
    }
  },
  "required": ["gateway_id", "start_time", "end_time"]
}
```

**Output**: Array of transactional log objects

---

### 4. Prediction Tools

#### `list_predictions`
List failure predictions.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "description": "Filter by API"
    },
    "gateway_id": {
      "type": "string",
      "description": "Filter by gateway"
    },
    "severity": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"],
      "description": "Filter by severity"
    },
    "status": {
      "type": "string",
      "enum": ["active", "resolved", "false_positive", "expired"],
      "description": "Filter by status"
    }
  }
}
```

**Output**: Array of prediction objects

#### `get_prediction_details`
Get detailed information about a prediction.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "prediction_id": {
      "type": "string",
      "description": "Prediction identifier"
    }
  },
  "required": ["prediction_id"]
}
```

**Output**: Full prediction object with AI-enhanced explanation

#### `update_prediction_status`
Update prediction status (e.g., mark as resolved).

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "prediction_id": {
      "type": "string",
      "description": "Prediction identifier"
    },
    "status": {
      "type": "string",
      "enum": ["resolved", "false_positive"],
      "description": "New status"
    },
    "notes": {
      "type": "string",
      "description": "Resolution notes"
    }
  },
  "required": ["prediction_id", "status"]
}
```

**Output**: Updated prediction object

---

### 5. Security Tools

#### `list_vulnerabilities`
List security vulnerabilities.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "description": "Filter by API"
    },
    "gateway_id": {
      "type": "string",
      "description": "Filter by gateway"
    },
    "severity": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"],
      "description": "Filter by severity"
    },
    "status": {
      "type": "string",
      "enum": ["open", "in_progress", "remediated", "verified", "false_positive"],
      "description": "Filter by remediation status"
    }
  }
}
```

**Output**: Array of vulnerability objects

#### `apply_security_remediation`
Apply automated security remediation.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "vulnerability_id": {
      "type": "string",
      "description": "Vulnerability identifier"
    },
    "remediation_type": {
      "type": "string",
      "enum": ["auto", "manual"],
      "description": "Remediation type"
    },
    "policy_config": {
      "type": "object",
      "description": "Policy configuration for auto remediation"
    }
  },
  "required": ["vulnerability_id", "remediation_type"]
}
```

**Output**: Updated vulnerability object with remediation status

#### `verify_remediation`
Verify that remediation resolved the vulnerability.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "vulnerability_id": {
      "type": "string",
      "description": "Vulnerability identifier"
    }
  },
  "required": ["vulnerability_id"]
}
```

**Output**: Verification result with updated vulnerability status

---

### 6. Compliance Tools

#### `list_compliance_violations`
List compliance violations.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "description": "Filter by API"
    },
    "gateway_id": {
      "type": "string",
      "description": "Filter by gateway"
    },
    "compliance_standard": {
      "type": "string",
      "enum": ["GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001"],
      "description": "Filter by standard"
    },
    "severity": {
      "type": "string",
      "enum": ["critical", "high", "medium", "low"],
      "description": "Filter by severity"
    }
  }
}
```

**Output**: Array of compliance violation objects

#### `generate_audit_report`
Generate compliance audit report.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "compliance_standard": {
      "type": "string",
      "enum": ["GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001"],
      "description": "Compliance standard"
    },
    "start_date": {
      "type": "string",
      "format": "date",
      "description": "Report start date"
    },
    "end_date": {
      "type": "string",
      "format": "date",
      "description": "Report end date"
    },
    "include_evidence": {
      "type": "boolean",
      "description": "Include evidence in report",
      "default": true
    }
  },
  "required": ["compliance_standard", "start_date", "end_date"]
}
```

**Output**:
```json
{
  "report_id": "uuid",
  "report_url": "/api/v1/compliance/reports/uuid",
  "generated_at": "2026-04-28T16:20:00Z",
  "summary": {
    "total_violations": 8,
    "critical": 2,
    "high": 3,
    "medium": 2,
    "low": 1
  }
}
```

---

### 7. Optimization Tools

#### `list_optimization_recommendations`
List performance optimization recommendations.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "description": "Filter by API"
    },
    "gateway_id": {
      "type": "string",
      "description": "Filter by gateway"
    },
    "recommendation_type": {
      "type": "string",
      "enum": ["caching", "compression", "rate_limiting"],
      "description": "Filter by type"
    },
    "status": {
      "type": "string",
      "enum": ["pending", "approved", "applied", "validated", "rejected"],
      "description": "Filter by status"
    }
  }
}
```

**Output**: Array of optimization recommendation objects

#### `apply_optimization`
Apply an optimization recommendation.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "recommendation_id": {
      "type": "string",
      "description": "Recommendation identifier"
    },
    "apply_immediately": {
      "type": "boolean",
      "description": "Apply immediately or schedule",
      "default": true
    },
    "custom_config": {
      "type": "object",
      "description": "Custom configuration overrides"
    }
  },
  "required": ["recommendation_id"]
}
```

**Output**: Updated recommendation object with application status

#### `list_rate_limit_policies`
List active rate limiting policies.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "description": "Filter by API"
    },
    "gateway_id": {
      "type": "string",
      "description": "Filter by gateway"
    }
  }
}
```

**Output**: Array of rate limit policy objects

---

### 8. Natural Language Query Tool

#### `query_natural_language`
Submit a natural language query.

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query_text": {
      "type": "string",
      "description": "Natural language query"
    },
    "context": {
      "type": "object",
      "description": "Query context (user_id, session_id, etc.)"
    }
  },
  "required": ["query_text"]
}
```

**Example**:
```json
{
  "query_text": "Which APIs are at risk of failure in the next 48 hours?",
  "context": {
    "user_id": "agent-123",
    "session_id": "session-456"
  }
}
```

**Output**:
```json
{
  "query_id": "uuid",
  "interpreted_intent": {
    "intent_type": "prediction",
    "confidence": 0.95
  },
  "results": {
    "result_count": 3,
    "result_data": [...]
  },
  "response": {
    "natural_language": "I found 3 APIs at risk...",
    "summary": "3 APIs require attention",
    "recommendations": [...]
  },
  "execution_time": 1250.5
}
```

---

## Available Resources

### 1. API Inventory Resource
```
api-inventory://gateway/{gateway_id}/apis
```

**Description**: Access to complete API inventory for a gateway

**Content Type**: `application/json`

**Example**:
```json
{
  "uri": "api-inventory://gateway/uuid-123/apis",
  "mimeType": "application/json",
  "text": "[{\"api_id\": \"...\", \"name\": \"...\"}]"
}
```

### 2. Metrics Resource
```
metrics://api/{api_id}/metrics?time_bucket={bucket}&start={start}&end={end}
```

**Description**: Time-series metrics for an API

**Content Type**: `application/json`

### 3. Security Findings Resource
```
security://gateway/{gateway_id}/vulnerabilities
```

**Description**: Security vulnerabilities for a gateway

**Content Type**: `application/json`

### 4. Compliance Resource
```
compliance://gateway/{gateway_id}/violations?standard={standard}
```

**Description**: Compliance violations for a gateway

**Content Type**: `application/json`

---

## Error Handling

### Error Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32000,
    "message": "Gateway not found",
    "data": {
      "gateway_id": "uuid",
      "details": "No gateway found with the specified ID"
    }
  }
}
```

### Error Codes
- `-32700`: Parse error
- `-32600`: Invalid request
- `-32601`: Method not found
- `-32602`: Invalid params
- `-32603`: Internal error
- `-32000`: Server error (custom)

---

## Health & Status

### Health Check
```
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "uptime": 3600,
  "connections": {
    "active": 5,
    "total": 100
  },
  "backend": {
    "status": "connected",
    "response_time": 50.5
  }
}
```

---

## Rate Limiting

- **Concurrent Connections**: 10 per client
- **Tool Calls**: 100 per minute per client
- **Resource Access**: 1000 per minute per client

---

## Security

- **Transport**: TLS 1.3 required
- **Authentication**: Bearer token (JWT)
- **Authorization**: Role-based access control
- **Audit Logging**: All tool calls logged

---

**MCP Server Contract Complete**: 2026-04-28  
**Next**: Gateway Adapter Contract