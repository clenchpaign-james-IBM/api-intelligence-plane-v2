# API Intelligence Plane v2 - Vendor-Neutral Migration Guide

**Version:** 2.0.0  
**Date:** 2026-04-11  
**Status:** Phase 0 Complete (Backend & Services) - Frontend Components Pending

## Overview

This guide documents the migration from the original API Intelligence Plane architecture to the new vendor-neutral, time-bucketed metrics system. The refactoring enables support for multiple API gateway vendors (Kong, Apigee, webMethods, AWS, Azure) while maintaining a unified intelligence layer.

## Migration Status: 49% Complete (20/41 tasks)

### ✅ Completed (20 tasks)
- Backend repository layer (6 tasks)
- Backend agent layer (4 tasks)
- Backend API endpoints (3 tasks)
- Frontend TypeScript types (2 tasks)
- Frontend service layer (2 tasks)
- Database migrations (3 tasks - SKIPPED, fresh data)

### 🚧 Pending (21 tasks)
- React components (4 tasks)
- Page/component updates (4 tasks)
- Testing (3 tasks)
- Documentation (5 tasks)
- Final validation (5 tasks)

---

## Architecture Changes

### 1. Vendor-Neutral Data Model

#### Before (Original)
```python
class API:
    id: UUID
    name: str
    is_shadow: bool
    health_score: float
    current_metrics: CurrentMetrics  # Embedded
    security_policies: dict  # Vendor-specific
```

#### After (Vendor-Neutral)
```python
class API:
    id: UUID
    name: str
    
    # Vendor-neutral policy actions
    policy_actions: List[PolicyAction]
    
    # AI-derived intelligence metadata
    intelligence_metadata: IntelligenceMetadata
    
    # OpenAPI definition
    api_definition: Optional[APIDefinition]
    
    # Vendor-specific data isolated
    vendor_metadata: Optional[Dict[str, Any]]
```

**Key Changes:**
- `current_metrics` removed - metrics now fetched separately
- `is_shadow`, `health_score`, `discovery_method` moved to `intelligence_metadata`
- Security policies replaced with vendor-neutral `policy_actions`
- Added `api_definition` for OpenAPI spec storage
- Added `vendor_metadata` for vendor-specific extensions

### 2. Time-Bucketed Metrics

#### Before (Original)
```python
class Metric:
    api_id: UUID
    timestamp: datetime
    response_time_p95: float
    error_rate: float
    # Single metric point
```

#### After (Time-Bucketed)
```python
class Metric:
    api_id: UUID
    timestamp: datetime
    time_bucket: TimeBucket  # 1m, 5m, 1h, 1d
    
    # Request counts
    request_count: int
    success_count: int
    failure_count: int
    
    # Response times
    response_time_avg: float
    response_time_p50: float
    response_time_p95: float
    response_time_p99: float
    
    # Timing breakdown
    gateway_time_avg: float
    backend_time_avg: float
    
    # Cache metrics
    cache_hit_rate: float
    cache_hit_count: int
    cache_miss_count: int
    cache_bypass_count: int
    
    # HTTP status breakdown
    status_2xx_count: int
    status_3xx_count: int
    status_4xx_count: int
    status_5xx_count: int
```

**Key Changes:**
- Added `time_bucket` field for granularity selection
- Separated timing into gateway vs backend
- Added comprehensive cache metrics
- Added HTTP status code breakdown
- Separate indices per time bucket with different retention

### 3. Policy Actions (Vendor-Neutral)

```python
class PolicyAction:
    action_type: PolicyActionType  # Enum with 18 types
    enabled: bool
    priority: Optional[int]
    vendor_config: Optional[Dict[str, Any]]
    description: Optional[str]

class PolicyActionType(str, Enum):
    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    RATE_LIMITING = "RATE_LIMITING"
    CACHING = "CACHING"
    COMPRESSION = "COMPRESSION"
    TLS = "TLS"
    CORS = "CORS"
    VALIDATION = "VALIDATION"
    TRANSFORMATION = "TRANSFORMATION"
    LOGGING = "LOGGING"
    MONITORING = "MONITORING"
    CIRCUIT_BREAKER = "CIRCUIT_BREAKER"
    RETRY = "RETRY"
    TIMEOUT = "TIMEOUT"
    IP_FILTERING = "IP_FILTERING"
    WAF = "WAF"
    DLP = "DLP"
    CUSTOM = "CUSTOM"
```

---

## API Endpoint Changes

### APIs Endpoint

#### Before
```
GET /api/v1/apis/{id}
Response: {
  "id": "...",
  "name": "...",
  "is_shadow": true,
  "current_metrics": { ... }  // Embedded
}
```

#### After
```
GET /api/v1/apis/{id}
Response: {
  "id": "...",
  "name": "...",
  "policy_actions": [ ... ],
  "intelligence_metadata": {
    "is_shadow": true,
    "health_score": 85.5,
    "risk_score": 12.3
  },
  "api_definition": { ... }  // OpenAPI spec
}

// Metrics fetched separately
GET /api/v1/apis/{id}/metrics?time_bucket=5m
```

#### New Endpoint
```
GET /api/v1/apis/{id}/security-policies
Response: [
  {
    "action_type": "AUTHENTICATION",
    "enabled": true,
    "vendor_config": { ... }
  }
]
```

### Metrics Endpoint

#### Before
```
GET /api/v1/apis/{id}/metrics?interval=5m
Response: {
  "metrics": [
    {
      "timestamp": "...",
      "response_time_p95": 250,
      "error_rate": 0.02
    }
  ]
}
```

#### After
```
GET /api/v1/apis/{id}/metrics?time_bucket=5m&start_time=...&end_time=...
Response: {
  "api_id": "...",
  "time_bucket": "5m",
  "time_series": [ ... ],
  "aggregated": {
    "total_requests": 10000,
    "success_rate": 98.5,
    "avg_response_time": 245
  },
  "cache_metrics": {
    "avg_hit_rate": 75.2,
    "total_hits": 7520,
    "total_misses": 2480
  },
  "timing_breakdown": {
    "avg_gateway_time": 45,
    "avg_backend_time": 200,
    "gateway_overhead_pct": 18.4
  },
  "status_breakdown": {
    "2xx": 9850,
    "3xx": 50,
    "4xx": 80,
    "5xx": 20
  }
}
```

---

## Frontend Migration

### TypeScript Types

#### API Interface Changes
```typescript
// OLD
interface API {
  is_shadow: boolean;
  health_score: number;
  current_metrics: CurrentMetrics;
}

// NEW
interface API {
  policy_actions?: PolicyAction[];
  intelligence_metadata: IntelligenceMetadata;
  api_definition?: APIDefinition;
  vendor_metadata?: Record<string, any>;
}

interface IntelligenceMetadata {
  is_shadow: boolean;
  health_score: number;
  risk_score: number;
  discovery_method: DiscoveryMethod;
}
```

#### Metrics Interface Changes
```typescript
// OLD
interface Metric {
  response_time_p95: number;
  error_rate: number;
}

// NEW
interface Metric {
  time_bucket: TimeBucket;
  gateway_time_avg: number;
  backend_time_avg: number;
  cache_hit_rate: number;
  cache_hit_count: number;
  status_2xx_count: number;
  status_3xx_count: number;
  status_4xx_count: number;
  status_5xx_count: number;
}

type TimeBucket = '1m' | '5m' | '1h' | '1d';
```

### Service Layer Changes

#### API Service
```typescript
// NEW METHOD
api.apis.getSecurityPolicies(id: string): Promise<PolicyAction[]>
```

#### Metrics Service
```typescript
// OLD (deprecated)
metricsService.getCurrent(apiId: string): Promise<Metric>
metricsService.getTimeSeries(apiId, params): Promise<MetricsTimeSeriesResponse>

// NEW (primary)
metricsService.getMetrics(apiId: string, params?: {
  start_time?: string;
  end_time?: string;
  time_bucket?: TimeBucket;
}): Promise<MetricsResponse>

// HELPER
metricsService.getOptimalTimeBucket(startTime: Date, endTime: Date): TimeBucket
```

---

## Database Schema Changes

### OpenSearch Indices

#### Before
```
api-inventory-v1
api-metrics
```

#### After
```
api-inventory          # Vendor-neutral API data
transactional-logs        # Raw transaction logs
api-metrics-1m            # 1-minute buckets (1 hour retention)
api-metrics-5m            # 5-minute buckets (6 hours retention)
api-metrics-1h            # 1-hour buckets (48 hours retention)
api-metrics-1d            # 1-day buckets (long-term retention)
```

### Index Mappings

#### api-inventory
```json
{
  "mappings": {
    "properties": {
      "policy_actions": {
        "type": "nested",
        "properties": {
          "action_type": { "type": "keyword" },
          "enabled": { "type": "boolean" },
          "vendor_config": { "type": "object", "enabled": false }
        }
      },
      "intelligence_metadata": {
        "properties": {
          "is_shadow": { "type": "boolean" },
          "health_score": { "type": "float" },
          "risk_score": { "type": "float" }
        }
      }
    }
  }
}
```

#### api-metrics-{bucket}
```json
{
  "mappings": {
    "properties": {
      "time_bucket": { "type": "keyword" },
      "gateway_time_avg": { "type": "float" },
      "backend_time_avg": { "type": "float" },
      "cache_hit_rate": { "type": "float" },
      "cache_hit_count": { "type": "long" },
      "status_2xx_count": { "type": "long" },
      "status_3xx_count": { "type": "long" },
      "status_4xx_count": { "type": "long" },
      "status_5xx_count": { "type": "long" }
    }
  }
}
```

---

## Remaining Implementation Tasks

### 1. React Components (4 tasks)

#### T082: PolicyActionsViewer Component
**Purpose:** Display vendor-neutral policy actions for an API  
**Location:** `frontend/src/components/apis/PolicyActionsViewer.tsx`

```typescript
interface PolicyActionsViewerProps {
  policyActions: PolicyAction[];
}

// Features:
// - Group by action type
// - Show enabled/disabled status
// - Display vendor-specific config
// - Filter by action type
```

#### T083: TimeBucketSelector Component
**Purpose:** Allow users to select time bucket granularity  
**Location:** `frontend/src/components/metrics/TimeBucketSelector.tsx`

```typescript
interface TimeBucketSelectorProps {
  value: TimeBucket;
  onChange: (bucket: TimeBucket) => void;
  timeRange?: { start: Date; end: Date };
}

// Features:
// - Radio buttons or dropdown for 1m, 5m, 1h, 1d
// - Auto-suggest optimal bucket based on time range
// - Show retention period for each bucket
```

#### T084: CacheMetricsDisplay Component
**Purpose:** Visualize cache performance metrics  
**Location:** `frontend/src/components/metrics/CacheMetricsDisplay.tsx`

```typescript
interface CacheMetricsDisplayProps {
  cacheMetrics: CacheMetrics;
}

// Features:
// - Hit rate gauge/chart
// - Hits vs misses vs bypasses breakdown
// - Trend over time
// - Optimization suggestions
```

#### T085: APIDefinitionViewer Component
**Purpose:** Display OpenAPI specification  
**Location:** `frontend/src/components/apis/APIDefinitionViewer.tsx`

```typescript
interface APIDefinitionViewerProps {
  apiDefinition: APIDefinition;
}

// Features:
// - Formatted JSON/YAML view
// - Endpoint list with methods
// - Schema viewer
// - Try-it-out functionality (optional)
```

### 2. Page/Component Updates (4 tasks)

#### T086: Update APIs.tsx Page
**Changes:**
- Remove `current_metrics` display
- Add link to separate metrics view
- Display `intelligence_metadata.is_shadow` badge
- Show policy actions count
- Update filters for new structure

#### T087: Update APIDetail.tsx Component
**Changes:**
- Add PolicyActionsViewer component
- Add APIDefinitionViewer component
- Remove embedded metrics
- Add "View Metrics" button linking to metrics page
- Display intelligence metadata

#### T088: Update HealthChart.tsx
**Changes:**
- Add TimeBucketSelector
- Fetch metrics with time_bucket parameter
- Display cache metrics
- Show timing breakdown
- Update chart to handle new data structure

#### T089: Update Dashboard.tsx
**Changes:**
- Update API list to use `intelligence_metadata`
- Remove embedded metrics
- Add cache performance summary
- Update health score calculation
- Add time bucket selector for dashboard metrics

### 3. Testing (3 tasks)

#### T090: Update Test Fixtures
**Files:** `backend/tests/fixtures/*.py`
- Create fixtures for PolicyAction
- Create fixtures for IntelligenceMetadata
- Create fixtures for time-bucketed Metric
- Update API fixtures to use new structure

#### T091: Update Integration Tests
**Files:** `backend/tests/integration/*.py`
- Test security-policies endpoint
- Test time-bucketed metrics endpoint
- Test policy action filtering
- Test cache metrics aggregation

#### T092: Update E2E Tests
**Files:** `backend/tests/e2e/*.py`
- Test complete API discovery flow
- Test metrics collection and aggregation
- Test policy action derivation
- Test time bucket selection

### 4. Documentation (4 remaining)

#### T077: Update API Documentation (OpenAPI/Swagger)
- Update API endpoint schemas
- Add security-policies endpoint
- Update metrics endpoint with time_bucket parameter
- Document new response structures

#### T097: Update architecture.md
- Document vendor-neutral architecture
- Explain time-bucketed metrics design
- Add policy actions architecture
- Update diagrams

#### T098: Update api-reference.md
- Document all endpoint changes
- Add examples for new endpoints
- Update request/response schemas
- Add migration examples

#### T100: Update README.md
- Update feature list
- Add vendor support matrix
- Update quick start guide
- Add migration notes

---

## Migration Checklist

### For Developers

- [ ] Review new TypeScript types in `frontend/src/types/index.ts`
- [ ] Update components to use `intelligence_metadata` instead of direct fields
- [ ] Replace `current_metrics` with separate metrics fetch
- [ ] Use `metricsService.getMetrics()` instead of legacy methods
- [ ] Implement PolicyActionsViewer component
- [ ] Implement TimeBucketSelector component
- [ ] Implement CacheMetricsDisplay component
- [ ] Implement APIDefinitionViewer component
- [ ] Update all pages to use new data structures
- [ ] Update tests to use new fixtures
- [ ] Run integration tests
- [ ] Run E2E tests

### For DevOps

- [ ] Create new OpenSearch indices (api-inventory, api-metrics-*)
- [ ] Set up index lifecycle policies for time-bucketed metrics
- [ ] Configure retention periods (1h, 6h, 48h, long-term)
- [ ] Update monitoring dashboards
- [ ] Update alerting rules
- [ ] Test backup/restore procedures

### For QA

- [ ] Test API discovery with multiple gateway vendors
- [ ] Verify metrics aggregation accuracy
- [ ] Test cache metrics calculation
- [ ] Verify timing breakdown accuracy
- [ ] Test policy action derivation
- [ ] Verify time bucket selection logic
- [ ] Test UI with new components
- [ ] Verify backward compatibility

---

## Breaking Changes

### API Responses

1. **API Entity:**
   - `is_shadow` moved to `intelligence_metadata.is_shadow`
   - `health_score` moved to `intelligence_metadata.health_score`
   - `current_metrics` removed (fetch separately)
   - `security_policies` replaced with `policy_actions`

2. **Metrics Entity:**
   - Added required `time_bucket` field
   - Added cache metrics fields
   - Added timing breakdown fields
   - Added HTTP status breakdown fields

3. **Endpoints:**
   - `/api/v1/apis/{id}/metrics` now requires `time_bucket` parameter
   - New endpoint: `/api/v1/apis/{id}/security-policies`

### Frontend

1. **Type Changes:**
   - `CurrentMetrics` interface removed
   - `API` interface restructured
   - `Metric` interface expanded

2. **Service Methods:**
   - `metricsService.getCurrent()` deprecated
   - `metricsService.getTimeSeries()` deprecated
   - Use `metricsService.getMetrics()` instead

---

## Rollback Plan

If issues arise during migration:

1. **Backend:** Keep old endpoints active with deprecation warnings
2. **Frontend:** Use feature flags to toggle between old/new UI
3. **Database:** Maintain both old and new indices during transition
4. **Monitoring:** Track error rates and performance metrics

---

## Support

For questions or issues during migration:
- **Technical Lead:** Review architecture.md
- **API Documentation:** See api-reference.md
- **Code Examples:** Check tests/ directory
- **Slack Channel:** #api-intelligence-plane

---

## Appendix: Code Examples

### Example: Fetching API with Metrics

```typescript
// OLD
const api = await api.apis.get(apiId);
const metrics = api.current_metrics;

// NEW
const api = await api.apis.get(apiId);
const metricsResponse = await metricsService.getMetrics(apiId, {
  time_bucket: '5m',
  start_time: new Date(Date.now() - 3600000).toISOString(),
  end_time: new Date().toISOString()
});
const { aggregated, cache_metrics, timing_breakdown } = metricsResponse;
```

### Example: Displaying Policy Actions

```typescript
// Access policy actions
const api = await api.apis.get(apiId);
const securityPolicies = api.policy_actions?.filter(pa => 
  ['AUTHENTICATION', 'AUTHORIZATION', 'TLS', 'WAF'].includes(pa.action_type)
);

// Or use dedicated endpoint
const securityPolicies = await api.apis.getSecurityPolicies(apiId);
```

### Example: Time Bucket Selection

```typescript
// Auto-select optimal bucket
const startTime = new Date(Date.now() - 86400000); // 24 hours ago
const endTime = new Date();
const optimalBucket = metricsService.getOptimalTimeBucket(startTime, endTime);
// Returns '1h' for 24-hour range

const metrics = await metricsService.getMetrics(apiId, {
  start_time: startTime.toISOString(),
  end_time: endTime.toISOString(),
  time_bucket: optimalBucket
});
```

---

**Document Version:** 1.0  
**Last Updated:** 2026-04-11  
**Next Review:** After component implementation complete