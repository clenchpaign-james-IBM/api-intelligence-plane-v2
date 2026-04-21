# MCP Tools Contract: API Intelligence Plane

**Date**: 2026-03-09  
**Version**: 1.0.0  
**Transport**: Streamable HTTP  
**Framework**: FastMCP

## Overview

This document defines the MCP (Model Context Protocol) tools provided by the API Intelligence Plane MCP servers. These tools enable AI agents to interact with the system's data and capabilities.

---

## MCP Server Architecture

### Server Organization

```
MCP Servers:
├── discovery-server (Port: 8001)
│   └── Tools: API discovery and inventory management
├── metrics-server (Port: 8002)
│   └── Tools: Metrics collection and analysis
├── security-server (Port: 8003)
│   └── Tools: Security scanning and remediation
└── optimization-server (Port: 8004)
    └── Tools: Performance optimization and rate limiting
```

### Health Endpoints

Each MCP server exposes a custom health endpoint:

```
GET /health
Response: {
  "status": "healthy" | "degraded" | "unhealthy",
  "server_name": "discovery-server",
  "version": "1.0.0",
  "uptime_seconds": 3600,
  "tools_available": 5
}
```

---

## Discovery Server Tools

### 1. discover_apis

**Description**: Discover APIs from a connected Gateway

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "format": "uuid",
      "description": "Gateway ID to discover APIs from"
    },
    "force_refresh": {
      "type": "boolean",
      "default": false,
      "description": "Force immediate discovery instead of using cache"
    }
  },
  "required": ["gateway_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "discovered_count": {
      "type": "integer",
      "description": "Number of APIs discovered"
    },
    "shadow_apis_count": {
      "type": "integer",
      "description": "Number of shadow APIs found"
    },
    "apis": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" },
          "base_path": { "type": "string" },
          "is_shadow": { "type": "boolean" }
        }
      }
    },
    "discovery_time_ms": {
      "type": "integer"
    }
  }
}
```

**Example Usage**:
```json
{
  "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
  "force_refresh": true
}
```

---

### 2. get_api_inventory

**Description**: Retrieve complete API inventory with filtering

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "format": "uuid",
      "description": "Filter by gateway"
    },
    "status": {
      "type": "string",
      "enum": ["active", "inactive", "deprecated", "failed"],
      "description": "Filter by status"
    },
    "is_shadow": {
      "type": "boolean",
      "description": "Filter shadow APIs"
    },
    "health_score_min": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Minimum health score"
    },
    "limit": {
      "type": "integer",
      "default": 100,
      "maximum": 1000
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "total_count": { "type": "integer" },
    "filtered_count": { "type": "integer" },
    "apis": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/API" }
    }
  }
}
```

---

### 3. search_apis

**Description**: Search APIs using natural language or structured queries

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search query (name, path, tags)"
    },
    "filters": {
      "type": "object",
      "description": "Additional filters"
    }
  },
  "required": ["query"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "results": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "api": { "$ref": "#/components/schemas/API" },
          "relevance_score": { "type": "number" }
        }
      }
    },
    "total_results": { "type": "integer" }
  }
}
```

---

## Metrics Server Tools

### 4. collect_metrics

**Description**: Collect current metrics from Gateway

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "format": "uuid",
      "description": "Gateway to collect from"
    },
    "api_ids": {
      "type": "array",
      "items": { "type": "string", "format": "uuid" },
      "description": "Specific APIs (empty = all)"
    }
  },
  "required": ["gateway_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "collected_count": { "type": "integer" },
    "collection_time_ms": { "type": "integer" },
    "metrics_summary": {
      "type": "object",
      "properties": {
        "avg_response_time": { "type": "number" },
        "total_requests": { "type": "integer" },
        "avg_error_rate": { "type": "number" }
      }
    }
  }
}
```

---

### 5. get_metrics_timeseries

**Description**: Retrieve time-series metrics for analysis

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target API"
    },
    "start_time": {
      "type": "string",
      "format": "date-time",
      "description": "Start of time range"
    },
    "end_time": {
      "type": "string",
      "format": "date-time",
      "description": "End of time range"
    },
    "interval": {
      "type": "string",
      "enum": ["1m", "5m", "15m", "1h", "1d"],
      "default": "5m",
      "description": "Aggregation interval"
    },
    "metrics": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["response_time", "error_rate", "throughput", "availability"]
      },
      "description": "Specific metrics to retrieve"
    }
  },
  "required": ["api_id", "start_time", "end_time"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": { "type": "string" },
    "time_range": {
      "type": "object",
      "properties": {
        "start": { "type": "string", "format": "date-time" },
        "end": { "type": "string", "format": "date-time" }
      }
    },
    "data_points": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "timestamp": { "type": "string", "format": "date-time" },
          "response_time_p50": { "type": "number" },
          "response_time_p95": { "type": "number" },
          "response_time_p99": { "type": "number" },
          "error_rate": { "type": "number" },
          "throughput": { "type": "number" },
          "availability": { "type": "number" }
        }
      }
    }
  }
}
```

---

### 6. analyze_trends

**Description**: Analyze metric trends and patterns

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "format": "uuid"
    },
    "metric": {
      "type": "string",
      "enum": ["response_time", "error_rate", "throughput", "availability"]
    },
    "lookback_hours": {
      "type": "integer",
      "default": 24,
      "minimum": 1,
      "maximum": 720
    }
  },
  "required": ["api_id", "metric"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "trend": {
      "type": "string",
      "enum": ["increasing", "decreasing", "stable", "volatile"]
    },
    "trend_strength": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "anomalies_detected": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "timestamp": { "type": "string", "format": "date-time" },
          "value": { "type": "number" },
          "severity": { "type": "string", "enum": ["low", "medium", "high"] }
        }
      }
    },
    "forecast": {
      "type": "object",
      "properties": {
        "next_24h_trend": { "type": "string" },
        "confidence": { "type": "number" }
      }
    }
  }
}
```

---

## Security Server Tools

### 7. scan_api_security

**Description**: Perform security scan on an API

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "format": "uuid",
      "description": "API to scan"
    },
    "scan_type": {
      "type": "string",
      "enum": ["full", "quick", "targeted"],
      "default": "full",
      "description": "Scan depth"
    },
    "focus_areas": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["authentication", "authorization", "injection", "exposure", "configuration", "dependency"]
      },
      "description": "Specific areas to scan"
    }
  },
  "required": ["api_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "scan_id": { "type": "string", "format": "uuid" },
    "api_id": { "type": "string", "format": "uuid" },
    "scan_completed_at": { "type": "string", "format": "date-time" },
    "vulnerabilities_found": { "type": "integer" },
    "severity_breakdown": {
      "type": "object",
      "properties": {
        "critical": { "type": "integer" },
        "high": { "type": "integer" },
        "medium": { "type": "integer" },
        "low": { "type": "integer" }
      }
    },
    "vulnerabilities": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/Vulnerability" }
    }
  }
}
```

---

### 8. remediate_vulnerability

**Description**: Trigger automated remediation for a vulnerability

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "vulnerability_id": {
      "type": "string",
      "format": "uuid",
      "description": "Vulnerability to remediate"
    },
    "remediation_strategy": {
      "type": "string",
      "enum": ["automated", "manual", "configuration"],
      "default": "automated"
    },
    "dry_run": {
      "type": "boolean",
      "default": false,
      "description": "Test without applying changes"
    }
  },
  "required": ["vulnerability_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "remediation_id": { "type": "string", "format": "uuid" },
    "vulnerability_id": { "type": "string", "format": "uuid" },
    "status": {
      "type": "string",
      "enum": ["initiated", "in_progress", "completed", "failed"]
    },
    "actions_taken": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "action": { "type": "string" },
          "status": { "type": "string" },
          "timestamp": { "type": "string", "format": "date-time" }
        }
      }
    },
    "verification_required": { "type": "boolean" }
  }
}
```

---

### 9. get_security_posture

**Description**: Get overall security posture for APIs

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "gateway_id": {
      "type": "string",
      "format": "uuid",
      "description": "Filter by gateway"
    },
    "include_remediated": {
      "type": "boolean",
      "default": false
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "overall_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 100
    },
    "total_apis": { "type": "integer" },
    "apis_with_vulnerabilities": { "type": "integer" },
    "total_vulnerabilities": { "type": "integer" },
    "severity_distribution": {
      "type": "object",
      "properties": {
        "critical": { "type": "integer" },
        "high": { "type": "integer" },
        "medium": { "type": "integer" },
        "low": { "type": "integer" }
      }
    },
    "remediation_rate": {
      "type": "number",
      "description": "Percentage of vulnerabilities remediated"
    },
    "top_vulnerabilities": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/Vulnerability" }
    }
  }
}
```

---

## Optimization Server Tools

### 10. generate_predictions

**Description**: Generate failure predictions for APIs

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "format": "uuid",
      "description": "Specific API (empty = all)"
    },
    "prediction_window_hours": {
      "type": "integer",
      "default": 48,
      "minimum": 24,
      "maximum": 72,
      "description": "Prediction time window"
    },
    "min_confidence": {
      "type": "number",
      "default": 0.7,
      "minimum": 0,
      "maximum": 1,
      "description": "Minimum confidence threshold"
    }
  }
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "predictions_generated": { "type": "integer" },
    "predictions": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/Prediction" }
    },
    "model_version": { "type": "string" },
    "generated_at": { "type": "string", "format": "date-time" }
  }
}
```

---

### 11. generate_optimization_recommendations

**Description**: Generate performance optimization recommendations

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "format": "uuid",
      "description": "Target API"
    },
    "focus_areas": {
      "type": "array",
      "items": {
        "type": "string",
        "enum": ["caching", "compression", "rate_limiting"]
      },
      "description": "Optional optimization areas to include in the response. If omitted, all generated optimization recommendation types are returned."
    },
    "min_impact_percentage": {
      "type": "number",
      "default": 10,
      "minimum": 0,
      "maximum": 100,
      "description": "Minimum expected improvement"
    }
  },
  "required": ["api_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "recommendations_count": { "type": "integer" },
    "recommendations": {
      "type": "array",
      "items": { "$ref": "#/components/schemas/OptimizationRecommendation" }
    },
    "total_potential_savings": {
      "type": "number",
      "description": "USD per month"
    }
  }
}
```

---

### 12. manage_rate_limit

**Description**: Create or update rate limit policy

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "format": "uuid"
    },
    "policy_type": {
      "type": "string",
      "enum": ["fixed", "adaptive", "priority_based", "burst_allowance"]
    },
    "limit_thresholds": {
      "type": "object",
      "properties": {
        "requests_per_second": { "type": "integer" },
        "requests_per_minute": { "type": "integer" },
        "requests_per_hour": { "type": "integer" }
      }
    },
    "enforcement_action": {
      "type": "string",
      "enum": ["throttle", "reject", "queue"],
      "default": "throttle"
    }
  },
  "required": ["api_id", "policy_type", "limit_thresholds"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "policy_id": { "type": "string", "format": "uuid" },
    "status": {
      "type": "string",
      "enum": ["created", "updated", "activated"]
    },
    "policy": { "$ref": "#/components/schemas/RateLimitPolicy" }
  }
}
```

---

### 13. analyze_rate_limit_effectiveness

**Description**: Analyze effectiveness of rate limiting policies

**Input Schema**:
```json
{
  "type": "object",
  "properties": {
    "api_id": {
      "type": "string",
      "format": "uuid"
    },
    "policy_id": {
      "type": "string",
      "format": "uuid"
    },
    "analysis_period_hours": {
      "type": "integer",
      "default": 24,
      "minimum": 1
    }
  },
  "required": ["api_id"]
}
```

**Output Schema**:
```json
{
  "type": "object",
  "properties": {
    "effectiveness_score": {
      "type": "number",
      "minimum": 0,
      "maximum": 1
    },
    "metrics": {
      "type": "object",
      "properties": {
        "requests_throttled": { "type": "integer" },
        "requests_rejected": { "type": "integer" },
        "legitimate_users_affected": { "type": "integer" },
        "abuse_prevented": { "type": "integer" }
      }
    },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "string"
      }
    }
  }
}
```

---

## Common Response Patterns

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "metadata": {
    "execution_time_ms": 150,
    "timestamp": "2026-03-09T16:00:00Z"
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "INVALID_INPUT",
    "message": "Gateway ID is required",
    "details": { ... }
  },
  "metadata": {
    "timestamp": "2026-03-09T16:00:00Z"
  }
}
```

---

## Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_INPUT` | Invalid input parameters | 400 |
| `NOT_FOUND` | Resource not found | 404 |
| `GATEWAY_UNREACHABLE` | Cannot connect to Gateway | 503 |
| `SCAN_FAILED` | Security scan failed | 500 |
| `REMEDIATION_FAILED` | Remediation action failed | 500 |
| `INSUFFICIENT_DATA` | Not enough data for analysis | 422 |
| `RATE_LIMIT_EXCEEDED` | Too many requests | 429 |

---

## Authentication

For MVP, no authentication is required. Future versions will implement:
- API key authentication
- OAuth 2.0 for user-based access
- mTLS for service-to-service communication

---

## Rate Limiting

MCP servers implement rate limiting:
- 100 requests per minute per client
- 1000 requests per hour per client
- Burst allowance: 20 requests

---

## Versioning

MCP tools follow semantic versioning:
- Tool names include version suffix for breaking changes
- Example: `discover_apis_v2` for breaking changes
- Backward compatibility maintained for 2 major versions

---

**Contract Version**: 1.0.0  
**Last Updated**: 2026-03-09  
**Next Review**: Phase 2 - Implementation