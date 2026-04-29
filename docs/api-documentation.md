# API Documentation: API Intelligence Plane

**Version**: 1.0.0  
**Last Updated**: 2026-04-29  
**Base URL**: `http://localhost:8000` (development) | `https://api.intelligence-plane.example.com` (production)

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [API Endpoints](#api-endpoints)
   - [Health](#health)
   - [Gateways](#gateways)
   - [APIs](#apis)
   - [Metrics](#metrics)
   - [Predictions](#predictions)
   - [Security](#security)
   - [Compliance](#compliance)
   - [Optimization](#optimization)
   - [Query](#query)
5. [Data Models](#data-models)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Versioning](#versioning)

---

## Overview

The API Intelligence Plane REST API provides programmatic access to all platform capabilities:

- **API Discovery**: Manage discovered APIs and shadow API detection
- **Gateway Management**: Register and configure API gateways
- **Metrics & Analytics**: Access real-time and historical performance data
- **Predictive Intelligence**: Retrieve failure predictions and health forecasts
- **Security Scanning**: Access vulnerability reports and trigger remediation
- **Compliance Monitoring**: Track compliance violations and audit trails
- **Performance Optimization**: Get AI-driven optimization recommendations
- **Natural Language Queries**: Query API intelligence using natural language

### API Characteristics

- **RESTful Design**: Standard HTTP methods (GET, POST, PUT, DELETE)
- **JSON Format**: All requests and responses use JSON
- **Pagination**: List endpoints support cursor-based pagination
- **Filtering**: Query parameters for filtering and searching
- **Versioning**: URL-based versioning (`/api/v1/`)
- **CORS Enabled**: Cross-origin requests supported for frontend integration

---

## Authentication

### Development Mode

For local development, authentication is **disabled** by default:

```bash
# No authentication required
curl http://localhost:8000/api/v1/gateways
```

### Production Mode

Production deployments should implement one of the following authentication methods:

#### API Key Authentication (Recommended)

```bash
curl -H "X-API-Key: your-api-key" \
  https://api.intelligence-plane.example.com/api/v1/gateways
```

#### Bearer Token Authentication

```bash
curl -H "Authorization: Bearer your-jwt-token" \
  https://api.intelligence-plane.example.com/api/v1/gateways
```

**Note**: Authentication implementation is environment-specific and should be configured via middleware.

---

## Common Patterns

### Pagination

List endpoints support pagination using `page` and `page_size` parameters:

```bash
GET /api/v1/apis?page=1&page_size=20
```

**Response Structure**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20,
  "pages": 8
}
```

### Filtering

Most list endpoints support filtering via query parameters:

```bash
# Filter APIs by gateway
GET /api/v1/apis?gateway_id=550e8400-e29b-41d4-a716-446655440000

# Filter by status
GET /api/v1/predictions?severity=critical&status=active

# Filter by time range
GET /api/v1/apis/123/metrics?start_time=2026-04-01T00:00:00Z&end_time=2026-04-29T23:59:59Z
```

### Time Ranges

Time-based queries use ISO 8601 format:

```bash
GET /api/v1/apis/123/metrics?start_time=2026-04-29T00:00:00Z&end_time=2026-04-29T23:59:59Z&interval=5m
```

**Supported Intervals**: `1m`, `5m`, `15m`, `1h`, `1d`

---

## API Endpoints

### Health

#### GET /health

Check service health status.

**Response** (200 OK):
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2026-04-29T12:00:00Z",
  "components": {
    "opensearch": "healthy",
    "llm_service": "healthy",
    "scheduler": "healthy"
  }
}
```

---

### Gateways

#### GET /api/v1/gateways

List all registered API gateways.

**Query Parameters**:
- `page` (integer): Page number (default: 1)
- `page_size` (integer): Items per page (default: 20, max: 100)
- `status` (string): Filter by status (`connected`, `disconnected`, `error`, `maintenance`)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Production Gateway",
      "vendor": "webmethods",
      "base_url": "https://gateway.example.com:5555",
      "status": "connected",
      "version": "10.15",
      "capabilities": ["discovery", "metrics", "policies"],
      "api_count": 245,
      "last_sync": "2026-04-29T11:55:00Z",
      "created_at": "2026-04-01T10:00:00Z",
      "updated_at": "2026-04-29T11:55:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

#### POST /api/v1/gateways

Register a new API gateway.

**Request Body**:
```json
{
  "name": "Production Gateway",
  "vendor": "webmethods",
  "base_url": "https://gateway.example.com:5555",
  "credentials": {
    "username": "admin",
    "password": "secure-password"
  },
  "config": {
    "sync_interval": 300,
    "enable_discovery": true,
    "enable_metrics": true
  }
}
```

**Response** (201 Created):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production Gateway",
  "vendor": "webmethods",
  "base_url": "https://gateway.example.com:5555",
  "status": "connected",
  "created_at": "2026-04-29T12:00:00Z"
}
```

#### GET /api/v1/gateways/{gateway_id}

Get gateway details.

**Response** (200 OK):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Production Gateway",
  "vendor": "webmethods",
  "base_url": "https://gateway.example.com:5555",
  "status": "connected",
  "version": "10.15",
  "capabilities": ["discovery", "metrics", "policies"],
  "api_count": 245,
  "health_score": 92.5,
  "last_sync": "2026-04-29T11:55:00Z",
  "statistics": {
    "total_requests_24h": 1500000,
    "avg_response_time_ms": 125,
    "error_rate": 0.02,
    "active_apis": 245
  },
  "created_at": "2026-04-01T10:00:00Z",
  "updated_at": "2026-04-29T11:55:00Z"
}
```

#### PUT /api/v1/gateways/{gateway_id}

Update gateway configuration.

**Request Body**:
```json
{
  "name": "Production Gateway - Updated",
  "config": {
    "sync_interval": 600,
    "enable_discovery": true
  }
}
```

**Response** (200 OK): Returns updated gateway object.

#### DELETE /api/v1/gateways/{gateway_id}

Remove a gateway.

**Response** (204 No Content)

---

### APIs

#### GET /api/v1/apis

List all discovered APIs.

**Query Parameters**:
- `page` (integer): Page number
- `page_size` (integer): Items per page
- `gateway_id` (uuid): Filter by gateway
- `status` (string): Filter by status (`active`, `inactive`, `deprecated`, `failed`)
- `is_shadow` (boolean): Filter shadow APIs

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "api-123",
      "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "User Service API",
      "version": "v2",
      "base_path": "/api/users",
      "status": "active",
      "is_shadow": false,
      "health_score": 95.2,
      "risk_score": 12.5,
      "security_score": 88.0,
      "request_count_24h": 50000,
      "avg_response_time_ms": 85,
      "error_rate": 0.01,
      "last_seen": "2026-04-29T11:59:00Z",
      "discovered_at": "2026-04-01T10:00:00Z"
    }
  ],
  "total": 245,
  "page": 1,
  "page_size": 20,
  "pages": 13
}
```

#### GET /api/v1/apis/{api_id}

Get detailed API information.

**Response** (200 OK):
```json
{
  "id": "api-123",
  "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "User Service API",
  "version": "v2",
  "base_path": "/api/users",
  "status": "active",
  "is_shadow": false,
  "health_score": 95.2,
  "risk_score": 12.5,
  "security_score": 88.0,
  "endpoints": [
    {
      "path": "/api/users",
      "method": "GET",
      "request_count_24h": 30000
    },
    {
      "path": "/api/users/{id}",
      "method": "GET",
      "request_count_24h": 15000
    }
  ],
  "policies": {
    "authentication": ["oauth2"],
    "rate_limiting": {
      "enabled": true,
      "limit": 1000,
      "window": "1m"
    }
  },
  "metrics_summary": {
    "request_count_24h": 50000,
    "avg_response_time_ms": 85,
    "error_rate": 0.01,
    "p95_response_time_ms": 150,
    "p99_response_time_ms": 250
  },
  "discovered_at": "2026-04-01T10:00:00Z",
  "last_seen": "2026-04-29T11:59:00Z"
}
```

---

### Metrics

#### GET /api/v1/apis/{api_id}/metrics

Get time-series metrics for an API.

**Query Parameters**:
- `start_time` (ISO 8601): Start of time range
- `end_time` (ISO 8601): End of time range
- `interval` (string): Data resolution (`1m`, `5m`, `15m`, `1h`, `1d`)

**Response** (200 OK):
```json
{
  "api_id": "api-123",
  "interval": "5m",
  "start_time": "2026-04-29T00:00:00Z",
  "end_time": "2026-04-29T23:59:59Z",
  "data_points": [
    {
      "timestamp": "2026-04-29T12:00:00Z",
      "request_count": 850,
      "avg_response_time_ms": 82,
      "error_count": 5,
      "error_rate": 0.006,
      "p95_response_time_ms": 145,
      "p99_response_time_ms": 230
    }
  ]
}
```

#### GET /api/v1/gateways/{gateway_id}/metrics

Get aggregated metrics for all APIs on a gateway.

**Query Parameters**: Same as API metrics endpoint.

**Response** (200 OK):
```json
{
  "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
  "interval": "1h",
  "start_time": "2026-04-29T00:00:00Z",
  "end_time": "2026-04-29T23:59:59Z",
  "data_points": [
    {
      "timestamp": "2026-04-29T12:00:00Z",
      "total_requests": 125000,
      "avg_response_time_ms": 95,
      "total_errors": 250,
      "error_rate": 0.002,
      "active_apis": 245
    }
  ]
}
```

---

### Predictions

#### GET /api/v1/predictions

List failure predictions.

**Query Parameters**:
- `page`, `page_size`: Pagination
- `api_id` (uuid): Filter by API
- `gateway_id` (uuid): Filter by gateway
- `severity` (string): Filter by severity (`critical`, `high`, `medium`, `low`)
- `status` (string): Filter by status (`active`, `resolved`, `false_positive`, `expired`)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "pred-456",
      "api_id": "api-123",
      "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "performance_degradation",
      "severity": "high",
      "confidence": 0.87,
      "predicted_at": "2026-04-29T12:00:00Z",
      "predicted_time": "2026-04-30T14:30:00Z",
      "status": "active",
      "description": "Response time expected to exceed 500ms threshold",
      "evidence": [
        "Increasing trend in response time over 6 hours",
        "Memory usage at 85% capacity",
        "Similar pattern observed before previous incident"
      ],
      "recommendations": [
        "Scale backend service instances",
        "Review database query performance",
        "Enable caching for frequently accessed endpoints"
      ]
    }
  ],
  "total": 12,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

#### GET /api/v1/predictions/{prediction_id}

Get detailed prediction information.

**Response** (200 OK): Returns detailed prediction object with full evidence and recommendations.

---

### Security

#### GET /api/v1/vulnerabilities

List security vulnerabilities.

**Query Parameters**:
- `page`, `page_size`: Pagination
- `api_id` (uuid): Filter by API
- `gateway_id` (uuid): Filter by gateway
- `severity` (string): Filter by severity
- `status` (string): Filter by status (`open`, `in_progress`, `remediated`, `accepted_risk`, `false_positive`)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "vuln-789",
      "api_id": "api-123",
      "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "missing_authentication",
      "severity": "critical",
      "status": "open",
      "title": "Endpoint lacks authentication",
      "description": "GET /api/users endpoint is publicly accessible without authentication",
      "cve_ids": [],
      "cvss_score": 9.1,
      "affected_endpoints": ["/api/users"],
      "detected_at": "2026-04-29T10:00:00Z",
      "remediation": {
        "automated": true,
        "steps": [
          "Enable OAuth2 authentication policy",
          "Configure token validation",
          "Update API documentation"
        ]
      }
    }
  ],
  "total": 8,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

#### POST /api/v1/vulnerabilities/{vulnerability_id}/remediate

Trigger automated remediation for a vulnerability.

**Response** (202 Accepted):
```json
{
  "vulnerability_id": "vuln-789",
  "remediation_id": "rem-101",
  "status": "initiated",
  "estimated_completion": "2026-04-29T12:15:00Z"
}
```

#### GET /api/v1/security/posture

Get overall security posture.

**Query Parameters**:
- `gateway_id` (uuid): Filter by gateway

**Response** (200 OK):
```json
{
  "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
  "overall_score": 82.5,
  "vulnerabilities": {
    "critical": 2,
    "high": 5,
    "medium": 12,
    "low": 8
  },
  "compliance_violations": {
    "critical": 1,
    "high": 3,
    "medium": 7,
    "low": 4
  },
  "trends": {
    "score_change_7d": 5.2,
    "new_vulnerabilities_7d": 3,
    "remediated_7d": 8
  },
  "last_scan": "2026-04-29T11:00:00Z"
}
```

---

### Compliance

#### GET /api/v1/compliance/violations

List compliance violations.

**Query Parameters**:
- `page`, `page_size`: Pagination
- `api_id` (uuid): Filter by API
- `gateway_id` (uuid): Filter by gateway
- `framework` (string): Filter by framework (`pci_dss`, `hipaa`, `gdpr`, `sox`)
- `severity` (string): Filter by severity

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "comp-321",
      "api_id": "api-123",
      "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
      "framework": "pci_dss",
      "requirement": "6.5.10",
      "severity": "high",
      "status": "open",
      "title": "Insufficient logging for payment transactions",
      "description": "Payment API does not log all transaction details as required by PCI DSS 6.5.10",
      "detected_at": "2026-04-29T09:00:00Z",
      "remediation_steps": [
        "Enable comprehensive transaction logging",
        "Include all required PCI DSS fields",
        "Configure log retention for 1 year"
      ]
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "pages": 1
}
```

---

### Optimization

#### GET /api/v1/optimization/recommendations

List performance optimization recommendations.

**Query Parameters**:
- `page`, `page_size`: Pagination
- `api_id` (uuid): Filter by API
- `gateway_id` (uuid): Filter by gateway
- `type` (string): Filter by type (`caching`, `compression`, `rate_limiting`, `routing`)
- `priority` (string): Filter by priority (`critical`, `high`, `medium`, `low`)

**Response** (200 OK):
```json
{
  "items": [
    {
      "id": "opt-654",
      "api_id": "api-123",
      "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "caching",
      "priority": "high",
      "status": "pending",
      "title": "Enable response caching for GET /api/users",
      "description": "Endpoint serves mostly static data with high request volume",
      "impact": {
        "estimated_latency_reduction_ms": 65,
        "estimated_load_reduction_percent": 40,
        "estimated_cost_savings_monthly": 250
      },
      "configuration": {
        "cache_ttl": 300,
        "cache_key": "path+query",
        "invalidation_strategy": "time_based"
      },
      "created_at": "2026-04-29T08:00:00Z"
    }
  ],
  "total": 23,
  "page": 1,
  "page_size": 20,
  "pages": 2
}
```

#### POST /api/v1/optimization/recommendations/{recommendation_id}/apply

Apply an optimization recommendation.

**Response** (202 Accepted):
```json
{
  "recommendation_id": "opt-654",
  "application_id": "app-987",
  "status": "applying",
  "estimated_completion": "2026-04-29T12:10:00Z"
}
```

---

### Query

#### POST /api/v1/query

Execute a natural language query.

**Request Body**:
```json
{
  "query": "Show me all APIs with high error rates in the last 24 hours",
  "context": {
    "gateway_id": "550e8400-e29b-41d4-a716-446655440000"
  }
}
```

**Response** (200 OK):
```json
{
  "query_id": "q-111",
  "query": "Show me all APIs with high error rates in the last 24 hours",
  "intent": "list_apis_by_error_rate",
  "results": {
    "apis": [
      {
        "id": "api-123",
        "name": "User Service API",
        "error_rate": 0.05,
        "error_count_24h": 2500
      }
    ],
    "summary": "Found 3 APIs with error rates above 2% in the last 24 hours"
  },
  "executed_at": "2026-04-29T12:00:00Z",
  "execution_time_ms": 1250
}
```

#### GET /api/v1/query/history

Get query history.

**Query Parameters**:
- `page`, `page_size`: Pagination
- `start_time`, `end_time`: Time range filter

**Response** (200 OK):
```json
{
  "items": [
    {
      "query_id": "q-111",
      "query": "Show me all APIs with high error rates",
      "intent": "list_apis_by_error_rate",
      "executed_at": "2026-04-29T12:00:00Z",
      "execution_time_ms": 1250
    }
  ],
  "total": 45,
  "page": 1,
  "page_size": 20,
  "pages": 3
}
```

---

## Data Models

### Gateway

```json
{
  "id": "uuid",
  "name": "string",
  "vendor": "webmethods | kong | apigee",
  "base_url": "string",
  "status": "connected | disconnected | error | maintenance",
  "version": "string",
  "capabilities": ["string"],
  "api_count": "integer",
  "health_score": "float",
  "last_sync": "datetime",
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### API

```json
{
  "id": "string",
  "gateway_id": "uuid",
  "name": "string",
  "version": "string",
  "base_path": "string",
  "status": "active | inactive | deprecated | failed",
  "is_shadow": "boolean",
  "health_score": "float",
  "risk_score": "float",
  "security_score": "float",
  "discovered_at": "datetime",
  "last_seen": "datetime"
}
```

### Prediction

```json
{
  "id": "string",
  "api_id": "string",
  "gateway_id": "uuid",
  "type": "string",
  "severity": "critical | high | medium | low",
  "confidence": "float",
  "predicted_at": "datetime",
  "predicted_time": "datetime",
  "status": "active | resolved | false_positive | expired",
  "description": "string",
  "evidence": ["string"],
  "recommendations": ["string"]
}
```

---

## Error Handling

### Error Response Format

All errors follow a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {
      "field": "Additional context"
    },
    "timestamp": "2026-04-29T12:00:00Z",
    "request_id": "req-123"
  }
}
```

### HTTP Status Codes

| Code | Meaning | Usage |
|------|---------|-------|
| 200 | OK | Successful GET, PUT requests |
| 201 | Created | Successful POST requests |
| 202 | Accepted | Async operation initiated |
| 204 | No Content | Successful DELETE requests |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 409 | Conflict | Resource conflict (e.g., duplicate) |
| 422 | Unprocessable Entity | Validation errors |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Service temporarily unavailable |

### Common Error Codes

- `GATEWAY_NOT_FOUND`: Gateway ID does not exist
- `API_NOT_FOUND`: API ID does not exist
- `INVALID_PARAMETERS`: Request parameters are invalid
- `VALIDATION_ERROR`: Request body validation failed
- `RATE_LIMIT_EXCEEDED`: Too many requests
- `OPENSEARCH_ERROR`: Database operation failed
- `LLM_SERVICE_ERROR`: AI service unavailable

---

## Rate Limiting

### Default Limits

| Endpoint Type | Limit | Window |
|--------------|-------|--------|
| Read (GET) | 1000 requests | 1 minute |
| Write (POST/PUT/DELETE) | 100 requests | 1 minute |
| Query (Natural Language) | 50 requests | 1 minute |

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1714392000
```

### Rate Limit Exceeded Response

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry after 60 seconds.",
    "details": {
      "limit": 1000,
      "window": "1m",
      "retry_after": 60
    }
  }
}
```

---

## Versioning

### URL-Based Versioning

The API uses URL-based versioning:

```
/api/v1/gateways
/api/v2/gateways  (future)
```

### Version Support Policy

- **Current Version**: v1 (stable)
- **Deprecation Notice**: 6 months before version retirement
- **Support Period**: Minimum 12 months after deprecation notice

### Version Header

Optionally specify version via header:

```
Accept: application/vnd.api-intelligence-plane.v1+json
```

---

## Examples

### Complete Workflow Example

```bash
# 1. Register a gateway
curl -X POST http://localhost:8000/api/v1/gateways \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Gateway",
    "vendor": "webmethods",
    "base_url": "https://gateway.example.com:5555",
    "credentials": {
      "username": "admin",
      "password": "password"
    }
  }'

# Response: {"id": "550e8400-e29b-41d4-a716-446655440000", ...}

# 2. List discovered APIs
curl http://localhost:8000/api/v1/apis?gateway_id=550e8400-e29b-41d4-a716-446655440000

# 3. Get API metrics
curl "http://localhost:8000/api/v1/apis/api-123/metrics?start_time=2026-04-29T00:00:00Z&end_time=2026-04-29T23:59:59Z&interval=1h"

# 4. Check predictions
curl http://localhost:8000/api/v1/predictions?severity=critical&status=active

# 5. Natural language query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Which APIs have the highest error rates today?"
  }'
```

---

## Additional Resources

- **OpenAPI Specification**: See [`specs/001-api-intelligence-plane/contracts/backend-api.yaml`](../specs/001-api-intelligence-plane/contracts/backend-api.yaml)
- **Architecture Documentation**: See [`docs/architecture.md`](./architecture.md)
- **Deployment Guide**: See [`docs/deployment.md`](./deployment.md)
- **User Guide**: See [`docs/user-guide.md`](./user-guide.md)

---

## Support

For API support and questions:
- **Documentation**: [https://docs.intelligence-plane.example.com](https://docs.intelligence-plane.example.com)
- **GitHub Issues**: [https://github.com/your-org/api-intelligence-plane/issues](https://github.com/your-org/api-intelligence-plane/issues)
- **Email**: support@intelligence-plane.example.com