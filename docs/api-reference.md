# API Reference: API Intelligence Plane

**Version**: 1.0.0  
**Last Updated**: 2026-03-12  
**Base URL**: `http://localhost:8000` (Development) | `https://api.yourdomain.com` (Production)

## Table of Contents

1. [Overview](#overview)
2. [Authentication](#authentication)
3. [Common Patterns](#common-patterns)
4. [API Endpoints](#api-endpoints)
   - [APIs](#apis)
   - [Gateways](#gateways)
   - [Metrics](#metrics)
   - [Predictions](#predictions)
   - [Optimization](#optimization)
   - [Query](#query)
5. [Response Codes](#response-codes)
6. [Error Handling](#error-handling)
7. [Rate Limiting](#rate-limiting)
8. [Examples](#examples)

---

## Overview

The API Intelligence Plane provides a RESTful API for managing API discovery, monitoring, predictions, security, optimization, and natural language queries. All endpoints return JSON responses and follow REST conventions.

### API Versioning

All endpoints are versioned under `/api/v1/`. Future versions will be available at `/api/v2/`, etc.

### Content Type

All requests and responses use `application/json` content type unless otherwise specified.

---

## Authentication

**MVP**: No authentication required for development.

**Production** (Future): OAuth 2.0 / OpenID Connect with Bearer tokens.

```http
Authorization: Bearer <token>
```

---

## Common Patterns

### Pagination

List endpoints support pagination with the following query parameters:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `page` | integer | 1 | Page number (1-based) |
| `page_size` | integer | 20 | Items per page (max: 100) |

**Response Format**:
```json
{
  "items": [...],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

### Filtering

Many list endpoints support filtering via query parameters:

```http
GET /api/v1/apis?status=active&is_shadow=false
GET /api/v1/predictions?severity=critical&status=active
```

### Timestamps

All timestamps are in ISO 8601 format (UTC):

```json
{
  "created_at": "2026-03-12T10:30:00Z",
  "updated_at": "2026-03-12T15:45:00Z"
}
```

### UUIDs

All resource IDs are UUIDs in standard format:

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## API Endpoints

### APIs

Manage discovered APIs and their metadata.

#### List APIs

```http
GET /api/v1/apis
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20, max: 100) |
| `gateway_id` | UUID | No | Filter by gateway ID |
| `status` | string | No | Filter by status (active, inactive, deprecated, failed) |
| `is_shadow` | boolean | No | Filter shadow APIs |

**Response**: `200 OK`

```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "gateway_id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "User Service API",
      "version": "1.2.3",
      "base_path": "/api/users",
      "endpoints": [
        {
          "path": "/users/{id}",
          "method": "GET",
          "description": "Get user by ID"
        }
      ],
      "methods": ["GET", "POST", "PUT", "DELETE"],
      "authentication_type": "bearer",
      "is_shadow": false,
      "discovery_method": "registered",
      "status": "active",
      "health_score": 95.5,
      "created_at": "2026-03-01T10:00:00Z",
      "updated_at": "2026-03-12T15:30:00Z"
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

#### Get API Details

```http
GET /api/v1/apis/{api_id}
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | Yes | API identifier |

**Response**: `200 OK`

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "gateway_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "User Service API",
  "version": "1.2.3",
  "base_path": "/api/users",
  "endpoints": [...],
  "methods": ["GET", "POST", "PUT", "DELETE"],
  "authentication_type": "bearer",
  "ownership": {
    "team": "Platform Team",
    "contact": "platform@example.com",
    "repository": "https://github.com/example/user-service"
  },
  "tags": ["user-management", "core-service"],
  "is_shadow": false,
  "discovery_method": "registered",
  "discovered_at": "2026-03-01T10:00:00Z",
  "last_seen_at": "2026-03-12T15:30:00Z",
  "status": "active",
  "health_score": 95.5,
  "current_metrics": {
    "response_time_p50": 45.2,
    "response_time_p95": 120.5,
    "response_time_p99": 250.0,
    "error_rate": 0.5,
    "throughput": 1500.0,
    "availability": 99.95
  },
  "created_at": "2026-03-01T10:00:00Z",
  "updated_at": "2026-03-12T15:30:00Z"
}
```

**Error Responses**:
- `404 Not Found`: API not found
- `500 Internal Server Error`: Server error

---

### Gateways

Manage API Gateway registrations.

#### List Gateways

```http
GET /api/v1/gateways
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20) |
| `vendor` | string | No | Filter by vendor (native, kong, apigee) |
| `status` | string | No | Filter by status (active, inactive) |

**Response**: `200 OK`

```json
{
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "Production Gateway",
      "vendor": "native",
      "base_url": "http://gateway:8080",
      "status": "active",
      "api_count": 45,
      "last_sync_at": "2026-03-12T15:30:00Z",
      "created_at": "2026-03-01T10:00:00Z"
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 20
}
```

#### Register Gateway

```http
POST /api/v1/gateways
```

**Request Body**:

```json
{
  "name": "Production Gateway",
  "vendor": "native",
  "base_url": "http://gateway:8080",
  "credentials": {
    "type": "basic",
    "username": "admin",
    "password": "secret"
  }
}
```

**Response**: `201 Created`

```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "Production Gateway",
  "vendor": "native",
  "base_url": "http://gateway:8080",
  "status": "active",
  "created_at": "2026-03-12T15:30:00Z"
}
```

---

### Metrics

Retrieve API metrics and performance data.

#### Get API Metrics

```http
GET /api/v1/apis/{api_id}/metrics
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | Yes | API identifier |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `start_time` | datetime | No | Start time (ISO 8601, default: 24h ago) |
| `end_time` | datetime | No | End time (ISO 8601, default: now) |
| `interval` | string | No | Aggregation interval (1m, 5m, 15m, 1h, 1d, default: 5m) |

**Response**: `200 OK`

```json
{
  "api_id": "550e8400-e29b-41d4-a716-446655440000",
  "time_series": [
    {
      "timestamp": "2026-03-12T15:00:00Z",
      "response_time_p50": 45.2,
      "response_time_p95": 120.5,
      "response_time_p99": 250.0,
      "error_rate": 0.5,
      "throughput": 1500.0,
      "availability": 99.95
    }
  ],
  "aggregated": {
    "avg_response_time": 52.3,
    "max_response_time": 450.0,
    "min_response_time": 12.5,
    "total_requests": 150000,
    "total_errors": 750,
    "avg_throughput": 1450.0,
    "uptime_percentage": 99.92
  },
  "total_data_points": 288
}
```

**Error Responses**:
- `404 Not Found`: API not found
- `500 Internal Server Error`: Server error

---

### Predictions

Manage API failure predictions.

#### List Predictions

```http
GET /api/v1/predictions
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | No | Filter by API ID |
| `severity` | string | No | Filter by severity (critical, high, medium, low) |
| `status` | string | No | Filter by status (active, resolved, false_positive) |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20) |

**Response**: `200 OK`

```json
{
  "predictions": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440002",
      "api_id": "550e8400-e29b-41d4-a716-446655440000",
      "prediction_type": "failure",
      "predicted_at": "2026-03-12T15:30:00Z",
      "predicted_time": "2026-03-14T10:00:00Z",
      "confidence_score": 0.85,
      "severity": "high",
      "status": "active",
      "contributing_factors": [
        {
          "factor": "error_rate",
          "current_value": 2.5,
          "threshold": 1.0,
          "trend": "increasing",
          "weight": 0.4
        },
        {
          "factor": "response_time_p95",
          "current_value": 450.0,
          "threshold": 300.0,
          "trend": "increasing",
          "weight": 0.3
        }
      ],
      "recommended_actions": [
        "Scale up service instances",
        "Review recent code changes",
        "Check database connection pool"
      ],
      "model_version": "1.0.0",
      "created_at": "2026-03-12T15:30:00Z",
      "updated_at": "2026-03-12T15:30:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20
}
```

#### Get Prediction Details

```http
GET /api/v1/predictions/{prediction_id}
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prediction_id` | UUID | Yes | Prediction identifier |

**Response**: `200 OK`

```json
{
  "id": "770e8400-e29b-41d4-a716-446655440002",
  "api_id": "550e8400-e29b-41d4-a716-446655440000",
  "prediction_type": "failure",
  "predicted_at": "2026-03-12T15:30:00Z",
  "predicted_time": "2026-03-14T10:00:00Z",
  "confidence_score": 0.85,
  "severity": "high",
  "status": "active",
  "contributing_factors": [...],
  "recommended_actions": [...],
  "actual_outcome": null,
  "actual_time": null,
  "accuracy_score": null,
  "model_version": "1.0.0",
  "created_at": "2026-03-12T15:30:00Z",
  "updated_at": "2026-03-12T15:30:00Z"
}
```

#### Generate Predictions

```http
POST /api/v1/predictions/generate
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | No | Generate for specific API (all if not provided) |
| `min_confidence` | float | No | Minimum confidence threshold (0-1, default: 0.7) |
| `use_ai` | boolean | No | Use AI-enhanced generation (default: false) |

**Response**: `202 Accepted`

```json
{
  "status": "accepted",
  "message": "Generated 3 predictions for API 550e8400-e29b-41d4-a716-446655440000",
  "predictions_generated": 3
}
```

#### Generate AI-Enhanced Predictions

```http
POST /api/v1/predictions/ai-enhanced
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | Yes | API ID to generate predictions for |
| `min_confidence` | float | No | Minimum confidence threshold (0-1, default: 0.7) |

**Response**: `200 OK`

```json
{
  "status": "success",
  "result": {
    "predictions": [...],
    "ai_analysis": {
      "trend_analysis": "Error rate showing exponential growth pattern",
      "risk_assessment": "High probability of service degradation within 48 hours",
      "confidence_factors": [...]
    }
  }
}
```

#### Get Prediction Explanation

```http
GET /api/v1/predictions/{prediction_id}/explanation
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `prediction_id` | UUID | Yes | Prediction identifier |

**Response**: `200 OK`

```json
{
  "status": "success",
  "prediction_id": "770e8400-e29b-41d4-a716-446655440002",
  "explanation": "This prediction indicates a high probability of API failure within the next 48 hours. The primary contributing factors are: 1) Error rate has increased by 150% over the past 6 hours, exceeding the threshold of 1%. 2) Response time at 95th percentile has degraded to 450ms, 50% above the normal baseline. 3) Database connection pool utilization is at 85%, indicating potential resource exhaustion. Recommended immediate actions include scaling up service instances and reviewing recent deployments."
}
```

#### Get Prediction Accuracy Statistics

```http
GET /api/v1/predictions/stats/accuracy
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | No | Filter by API ID |
| `days` | integer | No | Days to look back (1-90, default: 30) |

**Response**: `200 OK`

```json
{
  "status": "success",
  "stats": {
    "total_predictions": 150,
    "accurate_predictions": 127,
    "false_positives": 18,
    "false_negatives": 5,
    "accuracy_rate": 0.847,
    "precision": 0.876,
    "recall": 0.962,
    "avg_confidence": 0.82
  },
  "period_days": 30
}
```

---

### Optimization

Manage performance optimization recommendations.

#### List Recommendations

```http
GET /api/v1/recommendations
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | No | Filter by API ID |
| `priority` | string | No | Filter by priority (critical, high, medium, low) |
| `status` | string | No | Filter by status (pending, implemented, rejected, expired) |
| `recommendation_type` | string | No | Filter by type (caching, query_optimization, resource_allocation, etc.) |
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 20) |

**Response**: `200 OK`

```json
{
  "recommendations": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "api_id": "550e8400-e29b-41d4-a716-446655440000",
      "recommendation_type": "caching",
      "title": "Implement Redis caching for user profile endpoints",
      "description": "Analysis shows 85% of requests are for the same user profiles. Implementing Redis caching can significantly reduce database load and improve response times.",
      "priority": "high",
      "estimated_impact": {
        "metric": "response_time_p95",
        "current_value": 450.0,
        "expected_value": 120.0,
        "improvement_percentage": 73.3,
        "confidence": 0.9
      },
      "implementation_effort": "medium",
      "implementation_steps": [
        "Set up Redis cluster",
        "Implement cache-aside pattern",
        "Configure TTL policies",
        "Add cache invalidation logic"
      ],
      "status": "pending",
      "cost_savings": 1200.0,
      "created_at": "2026-03-12T15:30:00Z",
      "updated_at": "2026-03-12T15:30:00Z",
      "expires_at": "2026-03-19T15:30:00Z"
    }
  ],
  "total": 25,
  "page": 1,
  "page_size": 20
}
```

#### Get Recommendation Details

```http
GET /api/v1/recommendations/{recommendation_id}
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `recommendation_id` | UUID | Yes | Recommendation identifier |

**Response**: `200 OK`

```json
{
  "id": "880e8400-e29b-41d4-a716-446655440003",
  "api_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendation_type": "caching",
  "title": "Implement Redis caching for user profile endpoints",
  "description": "...",
  "priority": "high",
  "estimated_impact": {...},
  "implementation_effort": "medium",
  "implementation_steps": [...],
  "status": "pending",
  "cost_savings": 1200.0,
  "created_at": "2026-03-12T15:30:00Z",
  "updated_at": "2026-03-12T15:30:00Z",
  "expires_at": "2026-03-19T15:30:00Z"
}
```

#### Generate Recommendations

```http
POST /api/v1/recommendations/generate
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | Yes | API ID to generate recommendations for |
| `min_impact` | float | No | Minimum expected improvement % (0-100, default: 10.0) |
| `use_ai` | boolean | No | Use AI-enhanced generation (default: false) |

**Response**: `200 OK`

```json
{
  "api_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendations_generated": 5,
  "recommendations": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440003",
      "type": "caching",
      "title": "Implement Redis caching",
      "priority": "high",
      "expected_improvement": 73.3
    }
  ]
}
```

#### Generate AI-Enhanced Recommendations

```http
POST /api/v1/recommendations/ai-enhanced
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | Yes | API ID to generate recommendations for |
| `min_impact` | float | No | Minimum expected improvement % (default: 10.0) |

**Response**: `200 OK`

```json
{
  "status": "success",
  "result": {
    "recommendations": [...],
    "ai_insights": {
      "performance_analysis": "API shows consistent high latency during peak hours",
      "optimization_strategy": "Prioritize caching and query optimization",
      "implementation_guidance": "Start with low-effort, high-impact changes"
    }
  }
}
```

#### Get Recommendation Insights

```http
GET /api/v1/recommendations/{recommendation_id}/insights
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `recommendation_id` | UUID | Yes | Recommendation identifier |

**Response**: `200 OK`

```json
{
  "status": "success",
  "recommendation_id": "880e8400-e29b-41d4-a716-446655440003",
  "insights": {
    "detailed_analysis": "...",
    "implementation_tips": [...],
    "potential_risks": [...],
    "success_metrics": [...]
  }
}
```

#### Get Recommendation Statistics

```http
GET /api/v1/recommendations/stats
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_id` | UUID | No | Filter by API ID |
| `days` | integer | No | Days to look back (1-365, default: 30) |

**Response**: `200 OK`

```json
{
  "total_recommendations": 125,
  "by_status": [
    {"status": "pending", "count": 45},
    {"status": "implemented", "count": 65},
    {"status": "rejected", "count": 10},
    {"status": "expired", "count": 5}
  ],
  "by_priority": [
    {"priority": "critical", "count": 5},
    {"priority": "high", "count": 25},
    {"priority": "medium", "count": 60},
    {"priority": "low", "count": 35}
  ],
  "by_type": [
    {"type": "caching", "count": 30},
    {"type": "query_optimization", "count": 25},
    {"type": "resource_allocation", "count": 20}
  ],
  "avg_improvement": 45.2,
  "total_cost_savings": 15000.0
}
```

---

### Query

Natural language query interface.

#### Execute Query

```http
POST /api/v1/query
```

**Request Body**:

```json
{
  "query_text": "Show me APIs with high error rates in the last 24 hours",
  "session_id": "990e8400-e29b-41d4-a716-446655440004",
  "use_ai_agents": true
}
```

**Response**: `200 OK`

```json
{
  "query_id": "aa0e8400-e29b-41d4-a716-446655440005",
  "query_text": "Show me APIs with high error rates in the last 24 hours",
  "response_text": "I found 3 APIs with elevated error rates in the last 24 hours: User Service API (error rate: 2.5%), Payment API (error rate: 1.8%), and Notification API (error rate: 1.2%). The User Service API shows the most concerning trend with errors increasing by 150% over the past 6 hours.",
  "confidence_score": 0.92,
  "results": {
    "query_type": "health",
    "apis": [
      {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "User Service API",
        "error_rate": 2.5,
        "trend": "increasing"
      }
    ],
    "total_count": 3
  },
  "follow_up_queries": [
    "What are the specific errors in User Service API?",
    "Show me predictions for these APIs",
    "What optimizations are recommended?"
  ],
  "execution_time_ms": 1250
}
```

#### Get Query by ID

```http
GET /api/v1/query/{query_id}
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query_id` | UUID | Yes | Query identifier |

**Response**: `200 OK`

```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440005",
  "session_id": "990e8400-e29b-41d4-a716-446655440004",
  "query_text": "Show me APIs with high error rates",
  "response_text": "...",
  "confidence_score": 0.92,
  "results": {...},
  "follow_up_queries": [...],
  "execution_time_ms": 1250,
  "user_feedback": null,
  "created_at": "2026-03-12T15:30:00Z"
}
```

#### Get Session Queries

```http
GET /api/v1/query/session/{session_id}
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | UUID | Yes | Session identifier |

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `page` | integer | No | Page number (default: 1) |
| `page_size` | integer | No | Items per page (default: 50) |

**Response**: `200 OK`

```json
{
  "items": [
    {
      "id": "aa0e8400-e29b-41d4-a716-446655440005",
      "query_text": "Show me APIs with high error rates",
      "response_text": "...",
      "confidence_score": 0.92,
      "created_at": "2026-03-12T15:30:00Z"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 50
}
```

#### Get Recent Queries

```http
GET /api/v1/query/recent
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `user_id` | string | No | Filter by user ID |
| `hours` | integer | No | Hours to look back (default: 24) |
| `size` | integer | No | Maximum results (default: 20) |

**Response**: `200 OK`

```json
[
  {
    "id": "aa0e8400-e29b-41d4-a716-446655440005",
    "query_text": "Show me APIs with high error rates",
    "confidence_score": 0.92,
    "created_at": "2026-03-12T15:30:00Z"
  }
]
```

#### Submit Query Feedback

```http
POST /api/v1/query/{query_id}/feedback
```

**Path Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query_id` | UUID | Yes | Query identifier |

**Request Body**:

```json
{
  "feedback": "helpful",
  "comment": "Exactly what I needed"
}
```

**Feedback Values**: `helpful`, `not_helpful`, `partially_helpful`

**Response**: `200 OK`

```json
{
  "id": "aa0e8400-e29b-41d4-a716-446655440005",
  "query_text": "Show me APIs with high error rates",
  "user_feedback": "helpful",
  "feedback_comment": "Exactly what I needed",
  "updated_at": "2026-03-12T15:35:00Z"
}
```

#### Get Query Statistics

```http
GET /api/v1/query/statistics
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `session_id` | UUID | No | Filter by session |
| `hours` | integer | No | Hours to look back (default: 24) |

**Response**: `200 OK`

```json
{
  "total_queries": 150,
  "avg_confidence": 0.87,
  "avg_execution_time_ms": 1350,
  "by_query_type": [
    {"type": "health", "count": 45},
    {"type": "prediction", "count": 35},
    {"type": "performance", "count": 30},
    {"type": "security", "count": 25},
    {"type": "general", "count": 15}
  ],
  "feedback_distribution": [
    {"feedback": "helpful", "count": 120},
    {"feedback": "partially_helpful", "count": 20},
    {"feedback": "not_helpful", "count": 10}
  ]
}
```

---

## Response Codes

| Code | Description |
|------|-------------|
| `200 OK` | Request successful |
| `201 Created` | Resource created successfully |
| `202 Accepted` | Request accepted for processing |
| `400 Bad Request` | Invalid request parameters |
| `401 Unauthorized` | Authentication required |
| `403 Forbidden` | Insufficient permissions |
| `404 Not Found` | Resource not found |
| `422 Unprocessable Entity` | Validation error |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Server error |
| `503 Service Unavailable` | Service temporarily unavailable |

---

## Error Handling

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong",
  "status_code": 404,
  "timestamp": "2026-03-12T15:30:00Z"
}
```

### Validation Errors

```json
{
  "detail": [
    {
      "loc": ["body", "query_text"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ],
  "status_code": 422
}
```

---

## Rate Limiting

**MVP**: No rate limiting

**Production** (Future):
- Rate limits will be enforced per API key
- Headers will indicate rate limit status:
  - `X-RateLimit-Limit`: Maximum requests per window
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Time when limit resets (Unix timestamp)

---

## Examples

### Example 1: Discover APIs with High Error Rates

```bash
# Execute natural language query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Show me APIs with error rates above 1% in the last hour",
    "use_ai_agents": true
  }'

# Response
{
  "query_id": "...",
  "response_text": "Found 2 APIs with error rates above 1%...",
  "results": {
    "apis": [...]
  }
}
```

### Example 2: Generate AI-Enhanced Predictions

```bash
# Generate predictions with AI analysis
curl -X POST "http://localhost:8000/api/v1/predictions/ai-enhanced?api_id=550e8400-e29b-41d4-a716-446655440000" \
  -H "Content-Type: application/json"

# Response
{
  "status": "success",
  "result": {
    "predictions": [...],
    "ai_analysis": {
      "trend_analysis": "...",
      "risk_assessment": "..."
    }
  }
}
```

### Example 3: Get Optimization Recommendations

```bash
# Generate recommendations for an API
curl -X POST "http://localhost:8000/api/v1/recommendations/generate?api_id=550e8400-e29b-41d4-a716-446655440000&min_impact=20" \
  -H "Content-Type: application/json"

# Response
{
  "api_id": "550e8400-e29b-41d4-a716-446655440000",
  "recommendations_generated": 3,
  "recommendations": [...]
}
```

### Example 4: Monitor API Metrics

```bash
# Get metrics for the last 6 hours with 15-minute intervals
curl "http://localhost:8000/api/v1/apis/550e8400-e29b-41d4-a716-446655440000/metrics?start_time=2026-03-12T09:00:00Z&end_time=2026-03-12T15:00:00Z&interval=15m"

# Response
{
  "api_id": "550e8400-e29b-41d4-a716-446655440000",
  "time_series": [...],
  "aggregated": {...}
}
```

---

## Additional Resources

- [Architecture Documentation](./architecture.md)
- [Deployment Guide](./deployment.md)
- [AI Setup Guide](./ai-setup.md)
- [MCP Integration](./mcp-architecture.md)

---

**Need Help?**

- 📧 Email: support@api-intelligence-plane.com
- 💬 Discord: [Join our community](https://discord.gg/api-intelligence-plane)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/api-intelligence-plane-v2/issues)