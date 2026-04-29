# Data Model: API Intelligence Plane

**Date**: 2026-04-28  
**Feature**: API Intelligence Plane  
**Phase**: 1 - Design & Contracts

## Overview

This document defines the core data entities for the API Intelligence Plane system. All entities are stored in OpenSearch with vendor-neutral schemas that support multi-gateway deployments.

---

## Core Entities

### 1. API

Represents a discovered API with its definition, endpoints, version information, policies, and health indicators.

**Index**: `api-inventory`

**Schema**:
```python
{
    "api_id": str,                    # Unique identifier (UUID)
    "gateway_id": str,                # Reference to Gateway entity
    "name": str,                      # API name
    "version": str,                   # API version (e.g., "1.0.0")
    "description": str,               # API description
    "base_path": str,                 # Base URL path (e.g., "/api/v1/users")
    "endpoints": [                    # List of endpoints
        {
            "path": str,              # Endpoint path
            "method": str,            # HTTP method (GET, POST, etc.)
            "description": str,       # Endpoint description
            "parameters": [...]       # Request parameters
        }
    ],
    "maturity_state": str,            # "active", "deprecated", "beta", "alpha"
    "groups": [str],                  # API groups/tags
    "policies": [                     # Applied policies
        {
            "policy_id": str,
            "policy_type": str,       # "authentication", "rate_limit", etc.
            "policy_action": str,     # Vendor-neutral action name
            "configuration": dict     # Vendor-neutral config
        }
    ],
    "openapi_spec": dict,             # OpenAPI 3.0 specification
    "health_indicators": {
        "health_score": float,        # 0-100 health score
        "availability": float,        # Percentage uptime
        "avg_response_time": float,   # Milliseconds
        "error_rate": float,          # Percentage
        "last_check": str             # ISO 8601 timestamp
    },
    "is_shadow_api": bool,            # True if undocumented/unregistered
    "shadow_detection": {
        "confidence": float,          # 0-1 confidence score
        "detection_method": str,      # "traffic_analysis", "log_analysis"
        "detected_at": str            # ISO 8601 timestamp
    },
    "risk_assessment": {
        "risk_level": str,            # "critical", "high", "medium", "low"
        "risk_factors": [str],        # List of risk factors
        "last_assessed": str          # ISO 8601 timestamp
    },
    "created_at": str,                # ISO 8601 timestamp
    "updated_at": str,                # ISO 8601 timestamp
    "discovered_at": str              # ISO 8601 timestamp
}
```

**Relationships**:
- Belongs to one Gateway
- Has many Metrics
- Has many Predictions
- Has many Vulnerabilities
- Has many ComplianceViolations
- Has many OptimizationRecommendations
- Has many TransactionalLogs

**Validation Rules**:
- `api_id` must be unique
- `gateway_id` must reference existing Gateway
- `version` must follow semantic versioning
- `health_score` must be 0-100
- `maturity_state` must be one of: "active", "deprecated", "beta", "alpha"

**State Transitions**:
- New → Active (after successful discovery)
- Active → Deprecated (manual or automated deprecation)
- Active → Inactive (API removed from gateway)
- Beta/Alpha → Active (promotion)

---

### 2. Gateway

Represents a connected API Gateway instance with vendor information, connection details, and capabilities.

**Index**: `gateway-registry`

**Schema**:
```python
{
    "gateway_id": str,                # Unique identifier (UUID)
    "name": str,                      # Gateway name
    "vendor": str,                    # "webmethods", "kong", "apigee"
    "version": str,                   # Gateway version
    "base_url": str,                  # Gateway management API URL
    "connection_details": {
        "host": str,
        "port": int,
        "protocol": str,              # "http", "https"
        "auth_type": str,             # "basic", "token", "oauth2"
        "credentials_ref": str        # Reference to secure credential store
    },
    "capabilities": {
        "supports_discovery": bool,
        "supports_metrics": bool,
        "supports_policy_application": bool,
        "supports_transactional_logs": bool,
        "supported_policy_types": [str]
    },
    "status": str,                    # "connected", "disconnected", "error"
    "health": {
        "last_check": str,            # ISO 8601 timestamp
        "response_time": float,       # Milliseconds
        "error_message": str          # If status is "error"
    },
    "statistics": {
        "total_apis": int,
        "active_apis": int,
        "shadow_apis": int,
        "total_requests_24h": int
    },
    "created_at": str,                # ISO 8601 timestamp
    "updated_at": str,                # ISO 8601 timestamp
    "last_sync": str                  # ISO 8601 timestamp
}
```

**Relationships**:
- Has many APIs
- Has many Metrics
- Has many TransactionalLogs

**Validation Rules**:
- `gateway_id` must be unique
- `vendor` must be one of supported vendors
- `base_url` must be valid URL
- `status` must be one of: "connected", "disconnected", "error"

---

### 3. Metric

Represents performance measurements for APIs at multiple time resolutions.

**Indices**: 
- `api-metrics-1min-{YYYY.MM}` (1-minute resolution, 7-day retention)
- `api-metrics-5min-{YYYY.MM}` (5-minute resolution, 30-day retention)
- `api-metrics-1hour-{YYYY.MM}` (1-hour resolution, 90-day retention)
- `api-metrics-1day-{YYYY.MM}` (1-day resolution, 365-day retention)

**Schema**:
```python
{
    "metric_id": str,                 # Unique identifier (UUID)
    "gateway_id": str,                # Reference to Gateway
    "api_id": str,                    # Reference to API
    "timestamp": str,                 # ISO 8601 timestamp (bucket start)
    "time_bucket": str,               # "1min", "5min", "1hour", "1day"
    "response_time": {
        "avg": float,                 # Average response time (ms)
        "p50": float,                 # 50th percentile
        "p95": float,                 # 95th percentile
        "p99": float,                 # 99th percentile
        "max": float,                 # Maximum response time
        "min": float                  # Minimum response time
    },
    "error_rate": {
        "total_requests": int,
        "failed_requests": int,
        "error_percentage": float,
        "errors_by_code": {           # HTTP status code distribution
            "4xx": int,
            "5xx": int
        }
    },
    "throughput": {
        "requests_per_second": float,
        "total_requests": int,
        "bytes_sent": int,
        "bytes_received": int
    },
    "availability": {
        "uptime_percentage": float,
        "downtime_seconds": int
    },
    "cache_effectiveness": {
        "cache_hits": int,
        "cache_misses": int,
        "cache_hit_rate": float       # Percentage
    },
    "external_calls": {               # Calls to external services
        "total_calls": int,
        "avg_duration": float,
        "failed_calls": int
    }
}
```

**Relationships**:
- Belongs to one API
- Belongs to one Gateway

**Validation Rules**:
- `timestamp` must be aligned to time bucket boundary
- All percentages must be 0-100
- All counts must be non-negative

---

### 4. Prediction

Represents a failure prediction with target API, predicted failure time, confidence score, and recommended actions.

**Index**: `api-predictions`

**Schema**:
```python
{
    "prediction_id": str,             # Unique identifier (UUID)
    "api_id": str,                    # Reference to API
    "gateway_id": str,                # Reference to Gateway
    "prediction_type": str,           # "failure", "performance_degradation", "capacity_exhaustion"
    "predicted_at": str,              # ISO 8601 timestamp (when prediction was made)
    "predicted_failure_time": str,    # ISO 8601 timestamp (when failure expected)
    "time_window": {
        "start": str,                 # ISO 8601 timestamp
        "end": str                    # ISO 8601 timestamp
    },
    "confidence_score": float,        # 0-1 confidence level
    "severity": str,                  # "critical", "high", "medium", "low"
    "contributing_factors": [         # Strongly-typed factors
        {
            "factor_type": str,       # "performance_degradation", "capacity_issues", etc.
            "category": str,          # "performance", "capacity", "dependency", "pattern"
            "description": str,
            "impact_score": float,    # 0-1 impact on prediction
            "metrics": dict           # Supporting metrics
        }
    ],
    "recommended_actions": [
        {
            "action_type": str,       # "scale_up", "optimize_cache", "investigate_dependency"
            "priority": str,          # "immediate", "high", "medium", "low"
            "description": str,
            "estimated_impact": str   # Expected outcome
        }
    ],
    "ai_enhanced_explanation": {
        "summary": str,               # Natural language summary
        "detailed_analysis": str,     # Detailed explanation
        "root_cause_analysis": str,   # Root cause explanation
        "prevention_guidance": str,   # How to prevent
        "enhanced_at": str,           # ISO 8601 timestamp
        "model_used": str             # LLM model identifier
    },
    "status": str,                    # "active", "resolved", "false_positive", "expired"
    "actual_outcome": {
        "occurred": bool,
        "occurred_at": str,           # ISO 8601 timestamp
        "accuracy_score": float       # 0-1 prediction accuracy
    },
    "created_at": str,                # ISO 8601 timestamp
    "updated_at": str                 # ISO 8601 timestamp
}
```

**Relationships**:
- Belongs to one API
- Belongs to one Gateway

**Validation Rules**:
- `confidence_score` must be 0-1
- `predicted_failure_time` must be 24-48 hours in future
- `severity` must be one of: "critical", "high", "medium", "low"
- `status` must be one of: "active", "resolved", "false_positive", "expired"

---

### 5. Vulnerability

Represents a security vulnerability with affected API, severity level, and remediation status.

**Index**: `security-findings`

**Schema**:
```python
{
    "vulnerability_id": str,          # Unique identifier (UUID)
    "api_id": str,                    # Reference to API
    "gateway_id": str,                # Reference to Gateway
    "vulnerability_type": str,        # "authentication", "encryption", "injection", etc.
    "severity": str,                  # "critical", "high", "medium", "low"
    "title": str,                     # Vulnerability title
    "description": str,               # Detailed description
    "cve_id": str,                    # CVE identifier (if applicable)
    "cvss_score": float,              # 0-10 CVSS score
    "detection_method": str,          # "rule_based", "ai_analysis", "hybrid"
    "affected_endpoints": [str],      # List of affected endpoint paths
    "evidence": {
        "finding_details": str,
        "sample_request": str,
        "sample_response": str,
        "log_references": [str]
    },
    "remediation": {
        "status": str,                # "open", "in_progress", "remediated", "verified", "false_positive"
        "auto_remediable": bool,
        "remediation_type": str,      # "policy_application", "configuration_change", "manual"
        "applied_policies": [         # If auto-remediated
            {
                "policy_id": str,
                "policy_type": str,
                "applied_at": str
            }
        ],
        "verification": {
            "verified": bool,
            "verified_at": str,
            "verification_method": str # "rescan", "manual_review"
        },
        "manual_ticket": {
            "ticket_id": str,
            "ticket_url": str,
            "assigned_to": str
        }
    },
    "priority": str,                  # "immediate", "high", "medium", "low"
    "exploitability": str,            # "high", "medium", "low"
    "business_impact": str,           # "critical", "high", "medium", "low"
    "detected_at": str,               # ISO 8601 timestamp
    "resolved_at": str,               # ISO 8601 timestamp (if resolved)
    "created_at": str,                # ISO 8601 timestamp
    "updated_at": str                 # ISO 8601 timestamp
}
```

**Relationships**:
- Belongs to one API
- Belongs to one Gateway

**Validation Rules**:
- `severity` must be one of: "critical", "high", "medium", "low"
- `cvss_score` must be 0-10
- `remediation.status` must be one of: "open", "in_progress", "remediated", "verified", "false_positive"

---

### 6. ComplianceViolation

Represents a compliance violation with affected API, compliance standard, and audit trail.

**Index**: `compliance-violations`

**Schema**:
```python
{
    "violation_id": str,              # Unique identifier (UUID)
    "api_id": str,                    # Reference to API
    "gateway_id": str,                # Reference to Gateway
    "compliance_standard": str,       # "GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001"
    "violation_type": str,            # "data_protection", "access_control", "encryption", etc.
    "severity": str,                  # "critical", "high", "medium", "low"
    "title": str,                     # Violation title
    "description": str,               # Detailed description
    "requirement_reference": str,     # Specific requirement violated (e.g., "GDPR Article 32")
    "detection_method": str,          # "rule_based", "ai_analysis", "hybrid"
    "affected_data_types": [str],     # Types of data affected (e.g., "PII", "PHI")
    "evidence": {
        "finding_details": str,
        "policy_gaps": [str],
        "configuration_issues": [str],
        "log_references": [str]
    },
    "remediation": {
        "status": str,                # "open", "in_progress", "remediated", "accepted_risk", "false_positive"
        "remediation_plan": str,
        "applied_controls": [
            {
                "control_id": str,
                "control_type": str,
                "applied_at": str
            }
        ],
        "verification": {
            "verified": bool,
            "verified_at": str,
            "verification_method": str,
            "auditor_notes": str
        }
    },
    "audit_trail": [
        {
            "timestamp": str,
            "action": str,
            "actor": str,
            "details": str
        }
    ],
    "risk_acceptance": {
        "accepted": bool,
        "accepted_by": str,
            "accepted_at": str,
        "justification": str,
        "review_date": str
    },
    "detected_at": str,               # ISO 8601 timestamp
    "resolved_at": str,               # ISO 8601 timestamp (if resolved)
    "created_at": str,                # ISO 8601 timestamp
    "updated_at": str                 # ISO 8601 timestamp
}
```

**Relationships**:
- Belongs to one API
- Belongs to one Gateway

**Validation Rules**:
- `compliance_standard` must be one of: "GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001"
- `severity` must be one of: "critical", "high", "medium", "low"
- `remediation.status` must be one of: "open", "in_progress", "remediated", "accepted_risk", "false_positive"

---

### 7. OptimizationRecommendation

Represents a performance optimization opportunity with estimated impact and validation results.

**Index**: `optimization-recommendations`

**Schema**:
```python
{
    "recommendation_id": str,         # Unique identifier (UUID)
    "api_id": str,                    # Reference to API
    "gateway_id": str,                # Reference to Gateway
    "recommendation_type": str,       # "caching", "compression", "rate_limiting"
    "title": str,                     # Recommendation title
    "description": str,               # Detailed description
    "priority": str,                  # "high", "medium", "low"
    "estimated_impact": {
        "response_time_improvement": float,  # Percentage
        "bandwidth_reduction": float,        # Percentage
        "error_rate_reduction": float,       # Percentage
        "cost_savings": float                # Estimated cost savings
    },
    "implementation_effort": str,     # "low", "medium", "high"
    "configuration": {                # Recommended configuration
        "policy_type": str,
        "policy_action": str,
        "parameters": dict            # Vendor-neutral parameters
    },
    "ai_enhancement": {
        "implementation_guidance": str,
        "success_metrics": [str],
        "potential_risks": [str],
        "enhanced_at": str,
        "model_used": str
    },
    "status": str,                    # "pending", "approved", "applied", "validated", "rejected"
    "application": {
        "applied_at": str,
        "applied_by": str,
        "policy_id": str,             # Reference to applied policy
        "rollback_available": bool
    },
    "validation": {
        "validated": bool,
        "validated_at": str,
        "actual_impact": {
            "response_time_improvement": float,
            "bandwidth_reduction": float,
            "error_rate_reduction": float
        },
        "success": bool,
        "notes": str
    },
    "created_at": str,                # ISO 8601 timestamp
    "updated_at": str                 # ISO 8601 timestamp
}
```

**Relationships**:
- Belongs to one API
- Belongs to one Gateway

**Validation Rules**:
- `recommendation_type` must be one of: "caching", "compression", "rate_limiting"
- `priority` must be one of: "high", "medium", "low"
- `status` must be one of: "pending", "approved", "applied", "validated", "rejected"
- All impact percentages must be 0-100

---

### 8. Query

Represents a natural language query with interpreted intent and results.

**Index**: `query-history`

**Schema**:
```python
{
    "query_id": str,                  # Unique identifier (UUID)
    "user_id": str,                   # User identifier
    "query_text": str,                # Original natural language query
    "interpreted_intent": {
        "intent_type": str,           # "status", "trend", "prediction", "security", etc.
        "entities": [                 # Extracted entities
            {
                "entity_type": str,   # "api", "gateway", "time_range", etc.
                "entity_value": str
            }
        ],
        "confidence": float           # 0-1 confidence in interpretation
    },
    "opensearch_query": dict,         # Generated OpenSearch query DSL
    "results": {
        "result_count": int,
        "result_data": dict,          # Query results
        "visualizations": [           # Suggested visualizations
            {
                "type": str,          # "chart", "table", "metric"
                "config": dict
            }
        ]
    },
    "response": {
        "natural_language": str,      # Generated natural language response
        "summary": str,               # Brief summary
        "recommendations": [str]      # Follow-up recommendations
    },
    "feedback": {
        "helpful": bool,
        "feedback_text": str,
        "submitted_at": str
    },
    "execution_time": float,          # Milliseconds
    "created_at": str,                # ISO 8601 timestamp
    "updated_at": str                 # ISO 8601 timestamp
}
```

**Validation Rules**:
- `interpreted_intent.confidence` must be 0-1
- `execution_time` must be non-negative

---

### 9. TransactionalLog

Represents an individual API transaction with timing, request/response data, and external service calls.

**Index**: `transactional-logs-{gateway_id}-{YYYY.MM.DD}`

**Schema**:
```python
{
    "transaction_id": str,            # Unique identifier (UUID)
    "gateway_id": str,                # Reference to Gateway
    "api_id": str,                    # Reference to API
    "timestamp": str,                 # ISO 8601 timestamp
    "request": {
        "method": str,                # HTTP method
        "path": str,                  # Request path
        "headers": dict,              # Request headers (sanitized)
        "query_params": dict,         # Query parameters
        "client_ip": str,             # Client IP address
        "user_agent": str             # User agent string
    },
    "response": {
        "status_code": int,           # HTTP status code
        "headers": dict,              # Response headers
        "body_size": int              # Response body size in bytes
    },
    "timing": {
        "total_duration": float,      # Total request duration (ms)
        "gateway_duration": float,    # Time spent in gateway (ms)
        "backend_duration": float,    # Time spent in backend (ms)
        "queue_time": float           # Time spent in queue (ms)
    },
    "external_calls": [               # Calls to external services
        {
            "service_name": str,
            "service_url": str,
            "method": str,
            "duration": float,        # Milliseconds
            "status_code": int,
            "error": str              # If call failed
        }
    ],
    "error": {
        "occurred": bool,
        "error_type": str,            # "client_error", "server_error", "gateway_error"
        "error_code": str,
        "error_message": str,
        "stack_trace": str            # If available
    },
    "cache": {
        "cache_hit": bool,
        "cache_key": str
    },
    "client_info": {
        "client_id": str,             # API consumer identifier
        "client_tier": str,           # "premium", "standard", "free"
        "authentication_method": str  # "oauth2", "api_key", "basic"
    }
}
```

**Relationships**:
- Belongs to one API
- Belongs to one Gateway
- Has many ExternalCalls (embedded)

**Validation Rules**:
- `timestamp` must be valid ISO 8601
- `response.status_code` must be valid HTTP status code
- All durations must be non-negative

---

### 10. ExternalCall

Represents an external service call made during an API transaction (embedded in TransactionalLog).

**Schema** (embedded in TransactionalLog):
```python
{
    "service_name": str,              # External service name
    "service_url": str,               # External service URL
    "method": str,                    # HTTP method
    "duration": float,                # Call duration in milliseconds
    "status_code": int,               # HTTP status code
    "error": str,                     # Error message (if failed)
    "retry_count": int,               # Number of retries
    "circuit_breaker_state": str      # "closed", "open", "half_open"
}
```

**Validation Rules**:
- `duration` must be non-negative
- `status_code` must be valid HTTP status code
- `retry_count` must be non-negative

---

## Index Lifecycle Management (ILM)

### Retention Policies

1. **API Inventory**: No automatic deletion (manual cleanup)
2. **Gateway Registry**: No automatic deletion (manual cleanup)
3. **Metrics**:
   - 1-minute: 7 days
   - 5-minute: 30 days
   - 1-hour: 90 days
   - 1-day: 365 days
4. **Predictions**: 90 days
5. **Security Findings**: 365 days (compliance requirement)
6. **Compliance Violations**: 7 years (regulatory requirement)
7. **Optimization Recommendations**: 90 days
8. **Query History**: 30 days
9. **Transactional Logs**: 30 days

### Rollover Policies

- **Metrics**: Monthly rollover (index per month)
- **Transactional Logs**: Daily rollover (index per day per gateway)
- **Other indices**: No rollover (single index)

---

## Data Relationships

```
Gateway (1) ──< (N) API
API (1) ──< (N) Metric
API (1) ──< (N) Prediction
API (1) ──< (N) Vulnerability
API (1) ──< (N) ComplianceViolation
API (1) ──< (N) OptimizationRecommendation
API (1) ──< (N) TransactionalLog
TransactionalLog (1) ──< (N) ExternalCall (embedded)
```

---

## Vendor-Neutral Design

All entities use vendor-neutral schemas. Gateway-specific data is transformed by adapters:

1. **Discovery**: Vendor-specific API metadata → Vendor-neutral API entity
2. **Metrics**: Vendor-specific metrics → Vendor-neutral Metric entity
3. **Policies**: Vendor-neutral policy config → Vendor-specific policy application
4. **Logs**: Vendor-specific log format → Vendor-neutral TransactionalLog entity

This ensures consistent data models regardless of gateway vendor.

---

## Next Steps

1. ✅ Data model defined
2. → Define interface contracts in `/contracts/`
3. → Create quickstart.md
4. → Update agent context

---

**Data Model Complete**: 2026-04-28  
**Next Phase**: Interface Contracts