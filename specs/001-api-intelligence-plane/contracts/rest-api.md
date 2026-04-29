# REST API Contract: API Intelligence Plane

**Version**: v1  
**Base URL**: `http://localhost:8000/api/v1`  
**Date**: 2026-04-28

## Overview

The REST API provides HTTP endpoints for the frontend application and external integrations. All endpoints return JSON responses and use standard HTTP status codes.

## Authentication

**Type**: Bearer Token (JWT)  
**Header**: `Authorization: Bearer <token>`

## Common Response Format

### Success Response
```json
{
  "success": true,
  "data": { ... },
  "timestamp": "2026-04-28T16:20:00Z"
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": { ... }
  },
  "timestamp": "2026-04-28T16:20:00Z"
}
```

## HTTP Status Codes

- `200 OK`: Successful request
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Missing or invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Resource conflict (e.g., duplicate)
- `500 Internal Server Error`: Server error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Endpoints

### 1. Gateway Management

#### List Gateways
```http
GET /api/v1/gateways
```

**Query Parameters**:
- `status` (optional): Filter by status ("connected", "disconnected", "error")
- `vendor` (optional): Filter by vendor ("webmethods", "kong", "apigee")

**Response**:
```json
{
  "success": true,
  "data": {
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
}
```

#### Get Gateway Details
```http
GET /api/v1/gateways/{gateway_id}
```

**Response**: Single gateway object with full details

#### Register Gateway
```http
POST /api/v1/gateways
```

**Request Body**:
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

**Response**: Created gateway object with `gateway_id`

#### Update Gateway
```http
PUT /api/v1/gateways/{gateway_id}
```

**Request Body**: Same as register, all fields optional

#### Delete Gateway
```http
DELETE /api/v1/gateways/{gateway_id}
```

**Response**: `204 No Content`

---

### 2. API Inventory

#### List APIs
```http
GET /api/v1/apis
```

**Query Parameters**:
- `gateway_id` (optional): Filter by gateway
- `maturity_state` (optional): Filter by state
- `is_shadow_api` (optional): Filter shadow APIs (true/false)
- `search` (optional): Search by name or description
- `page` (optional): Page number (default: 1)
- `page_size` (optional): Items per page (default: 20)

**Response**:
```json
{
  "success": true,
  "data": {
    "apis": [
      {
        "api_id": "uuid",
        "gateway_id": "uuid",
        "name": "User Service API",
        "version": "1.0.0",
        "base_path": "/api/v1/users",
        "maturity_state": "active",
        "is_shadow_api": false,
        "health_indicators": {
          "health_score": 95.5,
          "availability": 99.9,
          "avg_response_time": 150.5,
          "error_rate": 0.1
        }
      }
    ],
    "total": 150,
    "page": 1,
    "page_size": 20
  }
}
```

#### Get API Details
```http
GET /api/v1/apis/{api_id}
```

**Response**: Single API object with full details including endpoints, policies, and OpenAPI spec

#### Get API Metrics
```http
GET /api/v1/apis/{api_id}/metrics
```

**Query Parameters**:
- `time_bucket` (required): "1min", "5min", "1hour", "1day"
- `start_time` (required): ISO 8601 timestamp
- `end_time` (required): ISO 8601 timestamp

**Response**:
```json
{
  "success": true,
  "data": {
    "metrics": [
      {
        "timestamp": "2026-04-28T16:00:00Z",
        "response_time": {
          "avg": 150.5,
          "p95": 250.0,
          "p99": 500.0
        },
        "error_rate": {
          "error_percentage": 0.1,
          "total_requests": 10000,
          "failed_requests": 10
        },
        "throughput": {
          "requests_per_second": 100.5
        }
      }
    ]
  }
}
```

---

### 3. Predictions

#### List Predictions
```http
GET /api/v1/predictions
```

**Query Parameters**:
- `api_id` (optional): Filter by API
- `gateway_id` (optional): Filter by gateway
- `status` (optional): Filter by status
- `severity` (optional): Filter by severity
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response**:
```json
{
  "success": true,
  "data": {
    "predictions": [
      {
        "prediction_id": "uuid",
        "api_id": "uuid",
        "prediction_type": "failure",
        "predicted_failure_time": "2026-04-30T16:00:00Z",
        "confidence_score": 0.85,
        "severity": "high",
        "contributing_factors": [
          {
            "factor_type": "performance_degradation",
            "category": "performance",
            "description": "Response time increasing 15% daily",
            "impact_score": 0.7
          }
        ],
        "recommended_actions": [
          {
            "action_type": "scale_up",
            "priority": "high",
            "description": "Increase backend capacity by 50%"
          }
        ]
      }
    ],
    "total": 5
  }
}
```

#### Get Prediction Details
```http
GET /api/v1/predictions/{prediction_id}
```

**Response**: Single prediction object with full details including AI-enhanced explanation

---

### 4. Security

#### List Vulnerabilities
```http
GET /api/v1/security/vulnerabilities
```

**Query Parameters**:
- `api_id` (optional): Filter by API
- `gateway_id` (optional): Filter by gateway
- `severity` (optional): Filter by severity
- `status` (optional): Filter by remediation status
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response**:
```json
{
  "success": true,
  "data": {
    "vulnerabilities": [
      {
        "vulnerability_id": "uuid",
        "api_id": "uuid",
        "vulnerability_type": "authentication",
        "severity": "critical",
        "title": "Missing Authentication",
        "cvss_score": 9.8,
        "remediation": {
          "status": "open",
          "auto_remediable": true
        },
        "detected_at": "2026-04-28T10:00:00Z"
      }
    ],
    "total": 12
  }
}
```

#### Apply Remediation
```http
POST /api/v1/security/vulnerabilities/{vulnerability_id}/remediate
```

**Request Body**:
```json
{
  "remediation_type": "auto",
  "policy_config": {
    "policy_type": "authentication",
    "policy_action": "require_oauth2"
  }
}
```

**Response**: Updated vulnerability object with remediation status

---

### 5. Compliance

#### List Compliance Violations
```http
GET /api/v1/compliance/violations
```

**Query Parameters**:
- `api_id` (optional): Filter by API
- `gateway_id` (optional): Filter by gateway
- `compliance_standard` (optional): Filter by standard
- `severity` (optional): Filter by severity
- `status` (optional): Filter by remediation status
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response**:
```json
{
  "success": true,
  "data": {
    "violations": [
      {
        "violation_id": "uuid",
        "api_id": "uuid",
        "compliance_standard": "GDPR",
        "violation_type": "data_protection",
        "severity": "high",
        "title": "Missing Data Encryption",
        "requirement_reference": "GDPR Article 32",
        "remediation": {
          "status": "open"
        },
        "detected_at": "2026-04-28T10:00:00Z"
      }
    ],
    "total": 8
  }
}
```

#### Generate Audit Report
```http
POST /api/v1/compliance/audit-report
```

**Request Body**:
```json
{
  "compliance_standard": "GDPR",
  "start_date": "2026-01-01",
  "end_date": "2026-04-28",
  "include_evidence": true
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "report_id": "uuid",
    "report_url": "/api/v1/compliance/reports/uuid",
    "generated_at": "2026-04-28T16:20:00Z"
  }
}
```

---

### 6. Optimization

#### List Recommendations
```http
GET /api/v1/optimization/recommendations
```

**Query Parameters**:
- `api_id` (optional): Filter by API
- `gateway_id` (optional): Filter by gateway
- `recommendation_type` (optional): Filter by type
- `status` (optional): Filter by status
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response**:
```json
{
  "success": true,
  "data": {
    "recommendations": [
      {
        "recommendation_id": "uuid",
        "api_id": "uuid",
        "recommendation_type": "caching",
        "title": "Enable Response Caching",
        "priority": "high",
        "estimated_impact": {
          "response_time_improvement": 40.0,
          "bandwidth_reduction": 30.0
        },
        "implementation_effort": "low",
        "status": "pending"
      }
    ],
    "total": 15
  }
}
```

#### Apply Recommendation
```http
POST /api/v1/optimization/recommendations/{recommendation_id}/apply
```

**Request Body**:
```json
{
  "apply_immediately": true,
  "custom_config": {
    "cache_ttl": 300
  }
}
```

**Response**: Updated recommendation object with application status

#### List Rate Limit Policies
```http
GET /api/v1/optimization/rate-limits
```

**Query Parameters**:
- `api_id` (optional): Filter by API
- `gateway_id` (optional): Filter by gateway
- `status` (optional): Filter by status

**Response**:
```json
{
  "success": true,
  "data": {
    "rate_limits": [
      {
        "policy_id": "uuid",
        "api_id": "uuid",
        "policy_type": "rate_limiting",
        "configuration": {
          "requests_per_minute": 1000,
          "burst_size": 100,
          "client_tier_limits": {
            "premium": 2000,
            "standard": 1000,
            "free": 100
          }
        },
        "status": "active"
      }
    ],
    "total": 10
  }
}
```

---

### 7. Natural Language Query

#### Submit Query
```http
POST /api/v1/query
```

**Request Body**:
```json
{
  "query_text": "Which APIs are at risk of failure?",
  "context": {
    "user_id": "uuid",
    "session_id": "uuid"
  }
}
```

**Response**:
```json
{
  "success": true,
  "data": {
    "query_id": "uuid",
    "interpreted_intent": {
      "intent_type": "prediction",
      "confidence": 0.95
    },
    "results": {
      "result_count": 3,
      "result_data": [
        {
          "api_id": "uuid",
          "api_name": "Payment API",
          "prediction": {
            "predicted_failure_time": "2026-04-30T16:00:00Z",
            "confidence_score": 0.85
          }
        }
      ]
    },
    "response": {
      "natural_language": "I found 3 APIs at risk of failure in the next 48 hours...",
      "summary": "3 APIs require attention",
      "recommendations": [
        "Review Payment API capacity",
        "Check User Service dependencies"
      ]
    },
    "execution_time": 1250.5
  }
}
```

#### Submit Query Feedback
```http
POST /api/v1/query/{query_id}/feedback
```

**Request Body**:
```json
{
  "helpful": true,
  "feedback_text": "Very helpful, exactly what I needed"
}
```

**Response**: `204 No Content`

---

### 8. Analytics

#### Get Transactional Logs
```http
GET /api/v1/analytics/transactions
```

**Query Parameters**:
- `gateway_id` (required): Gateway identifier
- `api_id` (optional): Filter by API
- `start_time` (required): ISO 8601 timestamp
- `end_time` (required): ISO 8601 timestamp
- `status_code` (optional): Filter by HTTP status code
- `client_id` (optional): Filter by client
- `page` (optional): Page number
- `page_size` (optional): Items per page

**Response**:
```json
{
  "success": true,
  "data": {
    "transactions": [
      {
        "transaction_id": "uuid",
        "api_id": "uuid",
        "timestamp": "2026-04-28T16:15:30Z",
        "request": {
          "method": "GET",
          "path": "/api/v1/users/123"
        },
        "response": {
          "status_code": 200
        },
        "timing": {
          "total_duration": 150.5
        }
      }
    ],
    "total": 10000,
    "page": 1,
    "page_size": 20
  }
}
```

---

## Rate Limiting

All API endpoints are rate-limited:
- **Authenticated requests**: 1000 requests per minute
- **Unauthenticated requests**: 100 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1714320000
```

---

## Pagination

Paginated endpoints support:
- `page`: Page number (1-based)
- `page_size`: Items per page (max: 100)

Response includes:
```json
{
  "data": { ... },
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 150,
    "total_pages": 8
  }
}
```

---

## Filtering & Sorting

Most list endpoints support:
- **Filtering**: Query parameters for common fields
- **Sorting**: `sort_by` and `sort_order` (asc/desc)
- **Search**: `search` parameter for text search

Example:
```http
GET /api/v1/apis?search=payment&sort_by=health_score&sort_order=asc
```

---

## Webhooks (Future)

Webhook support for real-time notifications:
- Prediction alerts
- Security vulnerability detection
- Compliance violation detection
- Gateway status changes

---

**REST API Contract Complete**: 2026-04-28  
**Next**: MCP Server Contract