# Data Model: API Intelligence Plane

**Date**: 2026-03-09  
**Feature**: API Intelligence Plane  
**Phase**: 1 - Design & Contracts

## Overview

This document defines the core entities, their attributes, relationships, validation rules, and state transitions for the API Intelligence Plane system. All entities are stored in OpenSearch with appropriate mappings and indices.

---

## Entity Definitions

### 1. API

Represents a discovered API with metadata, health metrics, security status, and performance characteristics.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `gateway_id` | string (UUID) | Yes | Reference to parent Gateway | Must exist in Gateway collection |
| `name` | string | Yes | API name | 1-255 characters, alphanumeric + spaces |
| `version` | string | No | API version | Semantic versioning (e.g., "1.2.3") |
| `base_path` | string | Yes | Base URL path | Valid URL path format |
| `endpoints` | array[Endpoint] | Yes | List of API endpoints | At least 1 endpoint |
| `methods` | array[string] | Yes | HTTP methods supported | Valid HTTP methods (GET, POST, etc.) |
| `authentication_type` | enum | Yes | Auth mechanism | One of: none, basic, bearer, oauth2, api_key, custom |
| `authentication_config` | object | No | Auth configuration | JSON object, encrypted if contains secrets |
| `ownership` | object | No | Ownership information | Contains: team, contact, repository |
| `tags` | array[string] | No | Categorization tags | Max 20 tags, each 1-50 characters |
| `is_shadow` | boolean | Yes | Shadow API flag | Default: false |
| `discovery_method` | enum | Yes | How API was found | One of: registered, traffic_analysis, log_analysis |
| `discovered_at` | timestamp | Yes | Discovery timestamp | ISO 8601 format |
| `last_seen_at` | timestamp | Yes | Last activity timestamp | ISO 8601 format |
| `status` | enum | Yes | Current status | One of: active, inactive, deprecated, failed |
| `health_score` | float | Yes | Overall health (0-100) | 0.0 to 100.0 |
| `current_metrics` | object | Yes | Latest metrics snapshot | See Metrics structure |
| `metadata` | object | No | Additional metadata | JSON object, max 10KB |
| `created_at` | timestamp | Yes | Creation timestamp | ISO 8601 format |
| `updated_at` | timestamp | Yes | Last update timestamp | ISO 8601 format |

#### Endpoint Structure

```json
{
  "path": "/users/{id}",
  "method": "GET",
  "description": "Get user by ID",
  "parameters": [
    {
      "name": "id",
      "type": "path",
      "data_type": "integer",
      "required": true
    }
  ],
  "response_codes": [200, 404, 500]
}
```

#### Current Metrics Structure

```json
{
  "response_time_p50": 45.2,
  "response_time_p95": 120.5,
  "response_time_p99": 250.0,
  "error_rate": 0.02,
  "throughput": 1500,
  "availability": 99.95,
  "last_error": "2026-03-09T10:30:00Z",
  "measured_at": "2026-03-09T15:00:00Z"
}
```

#### Relationships

- **Belongs to**: One Gateway (many-to-one)
- **Has many**: Metrics (one-to-many)
- **Has many**: Predictions (one-to-many)
- **Has many**: Vulnerabilities (one-to-many)
- **Has many**: Optimization Recommendations (one-to-many)
- **Has many**: Rate Limit Policies (one-to-many)

#### State Transitions

```
discovered → active → inactive
         ↓         ↓
    deprecated ← failed
```

- **discovered → active**: When API responds successfully
- **active → inactive**: When no traffic for 24 hours
- **active → failed**: When health score < 20 or error rate > 50%
- **active → deprecated**: Manual marking or Gateway indication
- **inactive → active**: When traffic resumes
- **failed → active**: When health restored

#### Validation Rules

1. `base_path` must start with `/`
2. `endpoints` array cannot be empty
3. `health_score` must be between 0 and 100
4. `error_rate` must be between 0 and 1
5. `availability` must be between 0 and 100
6. `last_seen_at` must be >= `discovered_at`
7. `updated_at` must be >= `created_at`

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "gateway_id": { "type": "keyword" },
      "name": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "version": { "type": "keyword" },
      "base_path": { "type": "keyword" },
      "endpoints": { "type": "nested" },
      "methods": { "type": "keyword" },
      "authentication_type": { "type": "keyword" },
      "tags": { "type": "keyword" },
      "is_shadow": { "type": "boolean" },
      "discovery_method": { "type": "keyword" },
      "discovered_at": { "type": "date" },
      "last_seen_at": { "type": "date" },
      "status": { "type": "keyword" },
      "health_score": { "type": "float" },
      "current_metrics": { "type": "object" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

---

### 2. Gateway

Represents a connected API Gateway with vendor information, connection details, capabilities, and associated APIs.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `name` | string | Yes | Gateway name | 1-255 characters |
| `vendor` | enum | Yes | Gateway vendor | One of: native, kong, apigee, aws, azure, custom |
| `version` | string | No | Gateway version | Semantic versioning |
| `connection_url` | string | Yes | Gateway API endpoint | Valid HTTPS URL |
| `connection_type` | enum | Yes | Connection method | One of: rest_api, grpc, graphql |
| `credentials` | object | Yes | Authentication credentials | Encrypted, contains: type, username, password, api_key, token |
| `capabilities` | array[string] | Yes | Supported features | List of capability names |
| `status` | enum | Yes | Connection status | One of: connected, disconnected, error, maintenance |
| `last_connected_at` | timestamp | No | Last successful connection | ISO 8601 format |
| `last_error` | string | No | Last error message | Max 1000 characters |
| `api_count` | integer | Yes | Number of APIs | Non-negative integer |
| `metrics_enabled` | boolean | Yes | Metrics collection enabled | Default: true |
| `security_scanning_enabled` | boolean | Yes | Security scanning enabled | Default: true |
| `rate_limiting_enabled` | boolean | Yes | Rate limiting enabled | Default: false |
| `configuration` | object | No | Vendor-specific config | JSON object, max 50KB |
| `metadata` | object | No | Additional metadata | JSON object, max 10KB |
| `created_at` | timestamp | Yes | Creation timestamp | ISO 8601 format |
| `updated_at` | timestamp | Yes | Last update timestamp | ISO 8601 format |

#### Capabilities List

```
- api_discovery
- metrics_collection
- log_streaming
- policy_management
- rate_limiting
- authentication_management
- ssl_termination
- caching
- transformation
- monitoring
```

#### Relationships

- **Has many**: APIs (one-to-many)
- **Has many**: Metrics (one-to-many, aggregated)

#### State Transitions

```
disconnected → connected → maintenance
     ↑              ↓
     └──── error ←──┘
```

- **disconnected → connected**: Successful connection established
- **connected → error**: Connection failure or timeout
- **connected → maintenance**: Manual maintenance mode
- **error → connected**: Connection restored
- **maintenance → connected**: Maintenance complete

#### Validation Rules

1. `connection_url` must be HTTPS (except localhost)
2. `credentials` must be encrypted at rest
3. `api_count` must match actual API count
4. `capabilities` must be non-empty
5. `last_connected_at` must be <= current time

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "vendor": { "type": "keyword" },
      "version": { "type": "keyword" },
      "connection_url": { "type": "keyword" },
      "connection_type": { "type": "keyword" },
      "capabilities": { "type": "keyword" },
      "status": { "type": "keyword" },
      "last_connected_at": { "type": "date" },
      "api_count": { "type": "integer" },
      "metrics_enabled": { "type": "boolean" },
      "security_scanning_enabled": { "type": "boolean" },
      "rate_limiting_enabled": { "type": "boolean" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

---

### 3. Metric

Represents time-series performance metrics for APIs.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `api_id` | string (UUID) | Yes | Reference to API | Must exist in API collection |
| `gateway_id` | string (UUID) | Yes | Reference to Gateway | Must exist in Gateway collection |
| `timestamp` | timestamp | Yes | Metric timestamp | ISO 8601 format |
| `response_time_p50` | float | Yes | 50th percentile (ms) | Non-negative |
| `response_time_p95` | float | Yes | 95th percentile (ms) | Non-negative |
| `response_time_p99` | float | Yes | 99th percentile (ms) | Non-negative |
| `error_rate` | float | Yes | Error rate (0-1) | 0.0 to 1.0 |
| `error_count` | integer | Yes | Total errors | Non-negative |
| `request_count` | integer | Yes | Total requests | Positive |
| `throughput` | float | Yes | Requests per second | Non-negative |
| `availability` | float | Yes | Availability % | 0.0 to 100.0 |
| `status_codes` | object | Yes | Status code distribution | Key: code, Value: count |
| `endpoint_metrics` | array[object] | No | Per-endpoint metrics | Optional breakdown |
| `metadata` | object | No | Additional metrics | JSON object |

#### Relationships

- **Belongs to**: One API (many-to-one)
- **Belongs to**: One Gateway (many-to-one)

#### Validation Rules

1. `response_time_p99` >= `response_time_p95` >= `response_time_p50`
2. `error_rate` = `error_count` / `request_count`
3. `request_count` > 0
4. `timestamp` must be within last 90 days (retention policy)

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "api_id": { "type": "keyword" },
      "gateway_id": { "type": "keyword" },
      "timestamp": { "type": "date" },
      "response_time_p50": { "type": "float" },
      "response_time_p95": { "type": "float" },
      "response_time_p99": { "type": "float" },
      "error_rate": { "type": "float" },
      "error_count": { "type": "integer" },
      "request_count": { "type": "integer" },
      "throughput": { "type": "float" },
      "availability": { "type": "float" },
      "status_codes": { "type": "object" }
    }
  }
}
```

**Index Pattern**: `api-metrics-{YYYY.MM}` (monthly rotation)

---

### 4. Prediction

Represents a failure prediction with target API, predicted failure time, confidence score, contributing factors, and recommended actions.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `api_id` | string (UUID) | Yes | Target API | Must exist in API collection |
| `prediction_type` | enum | Yes | Type of prediction | One of: failure, degradation, capacity, security |
| `predicted_at` | timestamp | Yes | When prediction made | ISO 8601 format |
| `predicted_time` | timestamp | Yes | When event expected | ISO 8601 format, 24-48h from predicted_at |
| `confidence_score` | float | Yes | Confidence (0-1) | 0.0 to 1.0 |
| `severity` | enum | Yes | Impact severity | One of: critical, high, medium, low |
| `status` | enum | Yes | Prediction status | One of: active, resolved, false_positive, expired |
| `contributing_factors` | array[object] | Yes | Factors leading to prediction | At least 1 factor |
| `recommended_actions` | array[string] | Yes | Suggested remediation | At least 1 action |
| `actual_outcome` | enum | No | What actually happened | One of: occurred, prevented, false_alarm |
| `actual_time` | timestamp | No | When event occurred | ISO 8601 format |
| `accuracy_score` | float | No | Prediction accuracy | 0.0 to 1.0, calculated post-event |
| `model_version` | string | Yes | ML model version | Semantic versioning |
| `metadata` | object | No | Additional data | JSON object |
| `created_at` | timestamp | Yes | Creation timestamp | ISO 8601 format |
| `updated_at` | timestamp | Yes | Last update timestamp | ISO 8601 format |

#### Contributing Factor Structure

```json
{
  "factor": "increasing_error_rate",
  "current_value": 0.15,
  "threshold": 0.10,
  "trend": "increasing",
  "weight": 0.35
}
```

#### Relationships

- **Belongs to**: One API (many-to-one)

#### State Transitions

```
active → resolved
   ↓
false_positive
   ↓
expired
```

- **active → resolved**: Preventive action taken or event occurred
- **active → false_positive**: Prediction did not materialize
- **active → expired**: Prediction window passed without event

#### Validation Rules

1. `predicted_time` must be 24-48 hours after `predicted_at`
2. `confidence_score` must be between 0 and 1
3. `contributing_factors` array must not be empty
4. `recommended_actions` array must not be empty
5. If `actual_outcome` is set, `actual_time` must be set
6. `accuracy_score` calculated as: 1 - |predicted_time - actual_time| / 48h

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "api_id": { "type": "keyword" },
      "prediction_type": { "type": "keyword" },
      "predicted_at": { "type": "date" },
      "predicted_time": { "type": "date" },
      "confidence_score": { "type": "float" },
      "severity": { "type": "keyword" },
      "status": { "type": "keyword" },
      "contributing_factors": { "type": "nested" },
      "recommended_actions": { "type": "text" },
      "actual_outcome": { "type": "keyword" },
      "actual_time": { "type": "date" },
      "accuracy_score": { "type": "float" },
      "model_version": { "type": "keyword" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

---

### 5. Vulnerability

Represents a security vulnerability with affected API, severity level, description, remediation status, and remediation actions.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `api_id` | string (UUID) | Yes | Affected API | Must exist in API collection |
| `vulnerability_type` | enum | Yes | Type of vulnerability | One of: authentication, authorization, injection, exposure, configuration, dependency |
| `cve_id` | string | No | CVE identifier | CVE-YYYY-NNNNN format |
| `severity` | enum | Yes | Severity level | One of: critical, high, medium, low |
| `title` | string | Yes | Vulnerability title | 1-255 characters |
| `description` | string | Yes | Detailed description | 1-5000 characters |
| `affected_endpoints` | array[string] | No | Specific endpoints | List of endpoint paths |
| `detection_method` | enum | Yes | How detected | One of: automated_scan, manual_review, external_report |
| `detected_at` | timestamp | Yes | Detection timestamp | ISO 8601 format |
| `status` | enum | Yes | Remediation status | One of: open, in_progress, remediated, accepted_risk, false_positive |
| `remediation_type` | enum | No | Remediation approach | One of: automated, manual, configuration, upgrade |
| `remediation_actions` | array[object] | No | Actions taken/planned | List of remediation steps |
| `remediated_at` | timestamp | No | Remediation timestamp | ISO 8601 format |
| `verification_status` | enum | No | Verification result | One of: verified, failed, pending |
| `cvss_score` | float | No | CVSS score | 0.0 to 10.0 |
| `references` | array[string] | No | External references | URLs to documentation |
| `metadata` | object | No | Additional data | JSON object |
| `created_at` | timestamp | Yes | Creation timestamp | ISO 8601 format |
| `updated_at` | timestamp | Yes | Last update timestamp | ISO 8601 format |

#### Remediation Action Structure

```json
{
  "action": "Update authentication middleware",
  "type": "code_change",
  "status": "completed",
  "performed_at": "2026-03-09T14:30:00Z",
  "performed_by": "automated_system"
}
```

#### Relationships

- **Belongs to**: One API (many-to-one)

#### State Transitions

```
open → in_progress → remediated → verified
  ↓                       ↓
accepted_risk      false_positive
```

- **open → in_progress**: Remediation started
- **in_progress → remediated**: Fix applied
- **remediated → verified**: Fix confirmed effective
- **open → accepted_risk**: Risk accepted by security team
- **open → false_positive**: Not a real vulnerability

#### Validation Rules

1. `severity` must match CVSS score ranges if provided
2. If `status` is `remediated`, `remediated_at` must be set
3. If `remediation_type` is `automated`, remediation must complete within 4 hours
4. If `remediation_type` is `manual`, remediation must complete within 24 hours
5. `cvss_score` must be between 0 and 10

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "api_id": { "type": "keyword" },
      "vulnerability_type": { "type": "keyword" },
      "cve_id": { "type": "keyword" },
      "severity": { "type": "keyword" },
      "title": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "description": { "type": "text" },
      "affected_endpoints": { "type": "keyword" },
      "detection_method": { "type": "keyword" },
      "detected_at": { "type": "date" },
      "status": { "type": "keyword" },
      "remediation_type": { "type": "keyword" },
      "remediation_actions": { "type": "nested" },
      "remediated_at": { "type": "date" },
      "verification_status": { "type": "keyword" },
      "cvss_score": { "type": "float" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

---

### 6. OptimizationRecommendation

Represents a performance optimization opportunity with target API, recommendation type, estimated impact, implementation effort, and validation results.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `api_id` | string (UUID) | Yes | Target API | Must exist in API collection |
| `recommendation_type` | enum | Yes | Type of optimization | One of: caching, query_optimization, resource_allocation, rate_limiting, compression, connection_pooling |
| `title` | string | Yes | Recommendation title | 1-255 characters |
| `description` | string | Yes | Detailed description | 1-5000 characters |
| `priority` | enum | Yes | Implementation priority | One of: critical, high, medium, low |
| `estimated_impact` | object | Yes | Expected improvements | Contains: metric, current_value, expected_value, improvement_percentage |
| `implementation_effort` | enum | Yes | Effort required | One of: low, medium, high |
| `implementation_steps` | array[string] | Yes | How to implement | At least 1 step |
| `status` | enum | Yes | Implementation status | One of: pending, in_progress, implemented, rejected, expired |
| `implemented_at` | timestamp | No | Implementation timestamp | ISO 8601 format |
| `validation_results` | object | No | Post-implementation metrics | Contains: actual_impact, success |
| `cost_savings` | float | No | Estimated cost savings | USD per month |
| `metadata` | object | No | Additional data | JSON object |
| `created_at` | timestamp | Yes | Creation timestamp | ISO 8601 format |
| `updated_at` | timestamp | Yes | Last update timestamp | ISO 8601 format |
| `expires_at` | timestamp | No | Recommendation expiry | ISO 8601 format |

#### Estimated Impact Structure

```json
{
  "metric": "response_time_p95",
  "current_value": 250.0,
  "expected_value": 150.0,
  "improvement_percentage": 40.0,
  "confidence": 0.85
}
```

#### Validation Results Structure

```json
{
  "actual_impact": {
    "metric": "response_time_p95",
    "before_value": 250.0,
    "after_value": 160.0,
    "actual_improvement": 36.0
  },
  "success": true,
  "measured_at": "2026-03-09T16:00:00Z"
}
```

#### Relationships

- **Belongs to**: One API (many-to-one)

#### State Transitions

```
pending → in_progress → implemented
   ↓                         ↓
rejected                 validated
   ↓
expired
```

- **pending → in_progress**: Implementation started
- **in_progress → implemented**: Changes deployed
- **implemented → validated**: Results measured and confirmed
- **pending → rejected**: Recommendation declined
- **pending → expired**: Recommendation no longer relevant

#### Validation Rules

1. `estimated_impact.improvement_percentage` must be positive
2. If `status` is `implemented`, `implemented_at` must be set
3. If `status` is `implemented`, `validation_results` should be set within 24 hours
4. `priority` should correlate with `estimated_impact.improvement_percentage`
5. `expires_at` must be > `created_at`

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "api_id": { "type": "keyword" },
      "recommendation_type": { "type": "keyword" },
      "title": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "description": { "type": "text" },
      "priority": { "type": "keyword" },
      "estimated_impact": { "type": "object" },
      "implementation_effort": { "type": "keyword" },
      "implementation_steps": { "type": "text" },
      "status": { "type": "keyword" },
      "implemented_at": { "type": "date" },
      "validation_results": { "type": "object" },
      "cost_savings": { "type": "float" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" },
      "expires_at": { "type": "date" }
    }
  }
}
```

---

### 7. RateLimitPolicy

Represents a rate limiting configuration with target API, limit thresholds, priority rules, and adaptation parameters.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `api_id` | string (UUID) | Yes | Target API | Must exist in API collection |
| `policy_name` | string | Yes | Policy name | 1-255 characters |
| `policy_type` | enum | Yes | Type of policy | One of: fixed, adaptive, priority_based, burst_allowance |
| `status` | enum | Yes | Policy status | One of: active, inactive, testing |
| `limit_thresholds` | object | Yes | Rate limit values | Contains: requests_per_second, requests_per_minute, requests_per_hour |
| `priority_rules` | array[object] | No | Priority-based rules | List of priority configurations |
| `burst_allowance` | integer | No | Burst request allowance | Non-negative |
| `adaptation_parameters` | object | No | Adaptive policy config | Contains: learning_rate, adjustment_frequency |
| `consumer_tiers` | array[object] | No | Consumer tier definitions | List of tier configurations |
| `enforcement_action` | enum | Yes | Action on limit breach | One of: throttle, reject, queue |
| `applied_at` | timestamp | No | When policy activated | ISO 8601 format |
| `last_adjusted_at` | timestamp | No | Last adaptation | ISO 8601 format |
| `effectiveness_score` | float | No | Policy effectiveness | 0.0 to 1.0 |
| `metadata` | object | No | Additional data | JSON object |
| `created_at` | timestamp | Yes | Creation timestamp | ISO 8601 format |
| `updated_at` | timestamp | Yes | Last update timestamp | ISO 8601 format |

#### Limit Thresholds Structure

```json
{
  "requests_per_second": 100,
  "requests_per_minute": 5000,
  "requests_per_hour": 250000,
  "concurrent_requests": 50
}
```

#### Priority Rule Structure

```json
{
  "tier": "premium",
  "multiplier": 2.0,
  "guaranteed_throughput": 200,
  "burst_multiplier": 1.5
}
```

#### Consumer Tier Structure

```json
{
  "tier_name": "premium",
  "tier_level": 1,
  "rate_multiplier": 2.0,
  "priority_score": 100
}
```

#### Relationships

- **Belongs to**: One API (many-to-one)

#### State Transitions

```
inactive → testing → active
              ↓         ↓
           inactive ← inactive
```

- **inactive → testing**: Policy being evaluated
- **testing → active**: Policy proven effective
- **testing → inactive**: Policy ineffective
- **active → inactive**: Policy disabled

#### Validation Rules

1. At least one threshold must be defined in `limit_thresholds`
2. `burst_allowance` must be <= `requests_per_second` * 10
3. `priority_rules` tier names must be unique
4. `effectiveness_score` must be between 0 and 1
5. If `policy_type` is `adaptive`, `adaptation_parameters` must be set

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "api_id": { "type": "keyword" },
      "policy_name": { "type": "text", "fields": { "keyword": { "type": "keyword" } } },
      "policy_type": { "type": "keyword" },
      "status": { "type": "keyword" },
      "limit_thresholds": { "type": "object" },
      "priority_rules": { "type": "nested" },
      "burst_allowance": { "type": "integer" },
      "adaptation_parameters": { "type": "object" },
      "consumer_tiers": { "type": "nested" },
      "enforcement_action": { "type": "keyword" },
      "applied_at": { "type": "date" },
      "last_adjusted_at": { "type": "date" },
      "effectiveness_score": { "type": "float" },
      "created_at": { "type": "date" },
      "updated_at": { "type": "date" }
    }
  }
}
```

---

### 8. Query

Represents a natural language query with original text, interpreted intent, results, and user feedback.

#### Attributes

| Field | Type | Required | Description | Validation |
|-------|------|----------|-------------|------------|
| `id` | string (UUID) | Yes | Unique identifier | UUID v4 format |
| `session_id` | string (UUID) | Yes | Conversation session | UUID v4 format |
| `user_id` | string | No | User identifier | 1-255 characters |
| `query_text` | string | Yes | Original query | 1-5000 characters |
| `query_type` | enum | Yes | Classified query type | One of: status, trend, prediction, security, performance, comparison, general |
| `interpreted_intent` | object | Yes | Parsed intent | Contains: action, entities, filters |
| `opensearch_query` | object | No | Generated query DSL | OpenSearch query object |
| `results` | object | Yes | Query results | Contains: data, count, execution_time |
| `response_text` | string | Yes | Natural language response | 1-10000 characters |
| `confidence_score` | float | Yes | Intent confidence | 0.0 to 1.0 |
| `execution_time_ms` | integer | Yes | Query execution time | Non-negative |
| `feedback` | enum | No | User feedback | One of: helpful, not_helpful, partially_helpful |
| `feedback_comment` | string | No | Feedback details | Max 1000 characters |
| `follow_up_queries` | array[string] | No | Suggested follow-ups | Max 5 suggestions |
| `metadata` | object | No | Additional data | JSON object |
| `created_at` | timestamp | Yes | Query timestamp | ISO 8601 format |

#### Interpreted Intent Structure

```json
{
  "action": "list",
  "entities": ["api", "vulnerability"],
  "filters": {
    "severity": "critical",
    "status": "open"
  },
  "time_range": {
    "start": "2026-03-02T00:00:00Z",
    "end": "2026-03-09T23:59:59Z"
  }
}
```

#### Results Structure

```json
{
  "data": [...],
  "count": 15,
  "execution_time": 245,
  "aggregations": {...}
}
```

#### Relationships

- **Belongs to**: One Session (many-to-one, via session_id)
- **May reference**: Multiple APIs, Predictions, Vulnerabilities, etc.

#### Validation Rules

1. `query_text` must not be empty
2. `confidence_score` must be between 0 and 1
3. `execution_time_ms` must be non-negative
4. If `feedback` is set, query must have been executed
5. `follow_up_queries` max 5 items

#### OpenSearch Mapping

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "session_id": { "type": "keyword" },
      "user_id": { "type": "keyword" },
      "query_text": { "type": "text" },
      "query_type": { "type": "keyword" },
      "interpreted_intent": { "type": "object" },
      "response_text": { "type": "text" },
      "confidence_score": { "type": "float" },
      "execution_time_ms": { "type": "integer" },
      "feedback": { "type": "keyword" },
      "feedback_comment": { "type": "text" },
      "created_at": { "type": "date" }
    }
  }
}
```

---

## Entity Relationships Diagram

```
Gateway (1) ──────< (N) API
                      │
                      ├──< (N) Metric
                      ├──< (N) Prediction
                      ├──< (N) Vulnerability
                      ├──< (N) OptimizationRecommendation
                      └──< (N) RateLimitPolicy

Session (1) ──────< (N) Query
```

---

## Index Strategy

### Primary Indices

1. **api-inventory**: API catalog (single index)
2. **gateway-registry**: Gateway configurations (single index)
3. **api-metrics-{YYYY.MM}**: Time-series metrics (monthly rotation)
4. **api-predictions**: Failure predictions (single index)
5. **security-findings**: Vulnerabilities (single index)
6. **optimization-recommendations**: Performance recommendations (single index)
7. **rate-limit-policies**: Rate limiting configurations (single index)
8. **query-history**: Natural language queries (single index)

### Index Lifecycle Management

- **Metrics**: Monthly rotation, 90-day retention
- **Queries**: 30-day retention
- **All others**: No automatic deletion, manual archival

### Backup Strategy

- Daily snapshots of all indices
- 30-day snapshot retention
- Point-in-time recovery capability

---

## Data Validation Summary

All entities include:
- **Type validation**: Field types enforced
- **Range validation**: Numeric ranges checked
- **Format validation**: Dates, UUIDs, URLs validated
- **Relationship validation**: Foreign keys verified
- **Business rule validation**: Domain-specific rules enforced

---

**Data Model Complete**: 2026-03-09  
**Next Phase**: Define interface contracts in /contracts/