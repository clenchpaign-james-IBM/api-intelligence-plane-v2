# WebMethods-First Architecture Refactoring

**Created**: 2026-04-09  
**Status**: Planning  
**Impact**: MAJOR - 39+ files affected  
**Estimated Effort**: 38-51 days (8-10 weeks) with 2-3 developers

## Executive Summary

This document outlines the major refactoring to transform API Intelligence Plane from a vendor-neutral architecture to a **webMethods-first architecture** with extension support for other vendors through transformation adapters.

### Business Rationale

API Intelligence Plane will be deployed first in the **webMethods API Management platform product suite**, making webMethods API Gateway the primary/native platform. Support for Kong and Apigee is provided as an extension capability through transformation adapters.

## Architecture Changes

### Before (Vendor-Neutral)
```
Gateway (Any Vendor) → Adapter → Service → Repository → OpenSearch
                                                      ↓
                                          REST API → Frontend/Backend Services
```
- Simple `API` model (intelligence plane focused)
- Simple `Metric` model (basic time-series)
- Native gateway adapter for demo purposes
- Vendor-agnostic data structures

### After (WebMethods-First)
```
DATA COLLECTION (via GatewayAdapter):
webMethods Gateway → WebMethodsAdapter.get_apis() → DiscoveryService → APIRepository → OpenSearch
webMethods Gateway → WebMethodsAdapter.get_transactional_logs() → WMAnalyticsService → Aggregation → Metrics → MetricsRepository → OpenSearch

Kong Gateway → KongAdapter.get_apis() [transforms to wm_api.API] → DiscoveryService → APIRepository → OpenSearch
Kong Gateway → KongAdapter.get_metrics() [transforms to wm_analytics.Metrics] → MetricsService → MetricsRepository → OpenSearch

DATA RETRIEVAL (from OpenSearch):
Frontend → REST API → Service → Repository → OpenSearch (query stored APIs and Metrics)
Backend AI Services → Repository → OpenSearch (query stored APIs and Metrics for analysis)
```
- Comprehensive `wm_api.API` model (webMethods native structure)
- Time-bucketed `wm_analytics.Metrics` model (5m, 1h, 1d)
- **WebMethodsAdapter** collects TransactionalLogs and aggregates to Metrics
- **Kong/Apigee adapters** transform their data to webMethods structure during collection
- All data stored in OpenSearch, then retrieved by frontend and backend services

## Model Changes

### 1. API Model Replacement

**From**: `backend/app/models/base/api.py:API` (Vendor-neutral intelligence plane model)

**To**: `backend/app/models/webmethods/wm_api.py:API` (webMethods-specific) → Transforms to `backend/app/models/base/api.py:API` (vendor-neutral)

**Key Additions**:
- `api_definition: APIDefinition` - Full RestAPI OpenAPI structure
- `policy_actions: List[PolicyAction]` - 10+ policy types (authentication, authorization, TLS, CORS, validation, security headers, throttle, cache, masking, log)
- `native_endpoint: Set[Endpoint]` - webMethods endpoint structure
- `scopes: List[Scope]` - OAuth scopes
- `maturity_state: str` - webMethods maturity tracking
- `api_groups: List[str]` - webMethods grouping
- `published_portals: List[str]` - Portal publishing status
- `referenced_files: Dict[str, str]` - File references
- Intelligence plane fields: `health_score`, `is_shadow`, `discovery_method`, `discovered_at`, `last_seen_at`, `status`

**Key Removals**:
- `current_metrics` - Metrics stored separately in time-bucketed indices
- `security_policies` - Derived from `policy_actions` field

**Field Naming**: camelCase with snake_case aliases for compatibility

### 2. Metrics Model Replacement

**From**: `backend/app/models/base/metric.py:Metric` (Vendor-neutral time-series model)

**To**: Derived from `backend/app/models/webmethods/wm_transaction.py:TransactionalLog` → Aggregated to `backend/app/models/base/metric.py:Metric`

**Key Additions**:
- `time_bucket: TimeBucket` - Enum (5m, 1h, 1d) for aggregation level
- `gateway_id: UUID` - Primary dimension for multi-gateway support
- `application_id: Optional[str]` - Application-level metrics
- `cache_hit_count: int`, `cache_miss_count: int`, `cache_hit_rate: float` - Cache metrics
- `gateway_time_avg: float` - Gateway processing time
- `provider_time_avg: float` - Backend service time
- `status_2xx_count`, `status_4xx_count`, `status_5xx_count` - Separate status counters
- `created_at`, `updated_at` - Audit timestamps

**Key Removals**:
- `endpoint_metrics` - Simplified design, no per-endpoint breakdown
- `status_codes: dict` - Replaced with separate counters

**Storage**: Time-bucketed OpenSearch indices (`metrics-5m`, `metrics-1h`, `metrics-1d`)

## Data Flow Changes

### API Discovery Flow

**Before**:
```
Gateway → NativeAdapter.get_apis() → DiscoveryService → APIRepository → OpenSearch (api-inventory)
```

**After**:
```
webMethods Gateway → WebMethodsAdapter.get_apis() → DiscoveryService → APIRepository → OpenSearch (api-inventory)
Kong Gateway → KongAdapter.get_apis() [transforms to wm_api.API] → DiscoveryService → APIRepository → OpenSearch
Apigee Gateway → ApigeeAdapter.get_apis() [transforms to wm_api.API] → DiscoveryService → APIRepository → OpenSearch
```

### Metrics Collection Flow

**Before**:
```
Gateway → NativeAdapter.get_metrics() → MetricsService → MetricsRepository → OpenSearch (api-metrics-*)
```

**After**:
```
webMethods Gateway → WebMethodsAdapter.get_transactional_logs() → WMAnalyticsService → Aggregation → Metrics → MetricsRepository → OpenSearch (metrics-5m/1h/1d)
Kong Gateway → KongAdapter.get_metrics() [transforms to wm_analytics.Metrics] → MetricsService → MetricsRepository → OpenSearch
Apigee Gateway → ApigeeAdapter.get_metrics() [transforms to wm_analytics.Metrics] → MetricsService → MetricsRepository → OpenSearch
```

### Data Retrieval Flow (Unchanged Concept, New Structure)

**Before & After**:
```
Frontend → REST API → Service → Repository → OpenSearch (query stored data)
Backend AI Services (Agents) → Repository → OpenSearch (query stored data for analysis)
```

**Change**: REST API and Backend Services now query `wm_api.API` and `wm_analytics.Metrics` structures from OpenSearch

## File Impact Analysis

### Models (Organized into subfolders)
- **Base Models** (vendor-neutral):
  - `backend/app/models/base/api.py` - Vendor-neutral API model
  - `backend/app/models/base/metric.py` - Vendor-neutral metrics model
  - `backend/app/models/base/transaction.py` - Vendor-neutral transactional log model
- **WebMethods Models** (vendor-specific):
  - `backend/app/models/webmethods/wm_api.py` - webMethods API Gateway API model
  - `backend/app/models/webmethods/wm_policy.py` - webMethods Policy models
  - `backend/app/models/webmethods/wm_policy_action.py` - webMethods PolicyAction models
  - `backend/app/models/webmethods/wm_transaction.py` - webMethods transactional log model

### Adapters (4 files - REMOVE 1, ADD 1, UPDATE 3)
- **REMOVE**: `backend/app/adapters/native_gateway.py`
- **ADD**: `backend/app/adapters/webmethods_gateway.py` - WebMethods adapter (collects APIs and TransactionalLogs)
- **UPDATE**: `backend/app/adapters/base.py` - Interface for all adapters
- **UPDATE**: `backend/app/adapters/kong_gateway.py` - Add transformation logic to webMethods structure
- **UPDATE**: `backend/app/adapters/apigee_gateway.py` - Add transformation logic to webMethods structure
- **UPDATE**: `backend/app/adapters/factory.py` - Replace native with webmethods adapter

### Services (8 files - UPDATE)
- `backend/app/services/discovery_service.py` - Use new API model, add intelligence fields
- `backend/app/services/metrics_service.py` - Use time-bucketed metrics, remove current_metrics
- `backend/app/services/prediction_service.py` - Query time-bucketed metrics
- `backend/app/services/security_service.py` - Derive security policies from policy_actions
- `backend/app/services/compliance_service.py` - Analyze policy_actions for compliance
- `backend/app/services/optimization_service.py` - Use time-bucketed metrics
- `backend/app/services/rate_limit_service.py` - Use time-bucketed metrics
- `backend/app/services/query_service.py` - Query new structures

### Agents (4 files - UPDATE)
- `backend/app/agents/prediction_agent.py` - Analyze time-bucketed metrics
- `backend/app/agents/security_agent.py` - Analyze policy_actions
- `backend/app/agents/compliance_agent.py` - Analyze policy_actions
- `backend/app/agents/optimization_agent.py` - Analyze time-bucketed metrics

### Repositories (2 files - UPDATE)
- `backend/app/db/repositories/api_repository.py` - Store/query wm_api.API structure
- `backend/app/db/repositories/metrics_repository.py` - Store/query time-bucketed metrics

### API Endpoints (3 files - UPDATE)
- `backend/app/api/v1/apis.py` - Serve wm_api.API structure
- `backend/app/api/v1/metrics.py` - Serve time-bucketed metrics
- Add new endpoint: `GET /apis/{id}/security-policies` - Derive from policy_actions

### Schedulers (2 files - UPDATE)
- `backend/app/scheduler/discovery_jobs.py` - Use new API model
- `backend/app/scheduler/metrics_jobs.py` - Collect time-bucketed metrics

### Tests (15+ files - UPDATE)
- All integration tests
- All E2E tests
- Update fixtures for new models

### Frontend (20+ files - UPDATE)
- TypeScript interfaces for new structures
- Components to display policy_actions
- Separate API and metrics fetching
- Time bucket selector for metrics
- Cache metrics display

## Migration Strategy

### Phase 0: Preparation (3 days)
1. Create feature branch: `refactor/webmethods-first`
2. Backup current models to `legacy/` directory
3. Create migration scripts
4. Set up parallel testing environment

### Phase 1: Model Migration (5 days)
1. Rename `wm_api.py` → `api.py`
2. Rename `wm_analytics.py` → `metric.py`
3. Add intelligence plane fields to API model
4. Remove `current_metrics` and `security_policies` fields
5. Update all imports across codebase (39+ files)

### Phase 2: Adapter Layer (5 days)
1. Delete `native_gateway.py`
2. Create `webmethods_gateway.py` adapter (collects APIs and TransactionalLogs via REST API)
3. Update `base.py` interface for all adapters
4. Implement Kong transformation logic (transform to webMethods structure)
5. Implement Apigee transformation logic (transform to webMethods structure)
6. Update factory to replace native with webmethods adapter

### Phase 3: Repository Layer (4 days)
1. Update APIRepository for new structure
2. Update MetricsRepository for time buckets
3. Create OpenSearch index migrations
4. Test data storage and retrieval

### Phase 4: Service Layer (6 days)
1. Update all 8 services
2. Add policy derivation logic
3. Remove current_metrics handling
4. Add time bucket query logic

### Phase 5: Agent Layer (4 days)
1. Update all 4 agents
2. Update LLM prompts
3. Add policy_actions analysis

### Phase 6: API Layer (3 days)
1. Update REST endpoints
2. Add security-policies endpoint
3. Update response schemas

### Phase 7: Frontend (8 days)
1. Update TypeScript interfaces
2. Update all components
3. Add time bucket selector
4. Add policy_actions display

### Phase 8: Testing (8 days)
1. Update all tests
2. Test transformations
3. E2E validation
4. Performance testing

### Phase 9: Data Migration (6 days)
1. Migrate existing API data
2. Migrate existing metrics data
3. Validate data integrity
4. Rollback plan

### Phase 10: Documentation (4 days)
1. Update all documentation
2. Create migration guide
3. Update API reference
4. Update architecture diagrams

## Breaking Changes

### Database Schema
- `api-inventory` index: Complete restructure with policy_actions, api_definition
- `api-metrics-*` indices: Replaced with `metrics-5m`, `metrics-1h`, `metrics-1d`
- All existing data requires migration

### REST API Contracts
- `/apis` response: New structure with policy_actions
- `/apis/{id}/metrics`: New query parameters for time buckets
- New endpoint: `/apis/{id}/security-policies`

### Code Architecture
- Native gateway adapter removed
- All imports changed from `models.api` to new structure
- Transformation logic required for Kong/Apigee

## Rollback Plan

1. Keep legacy models in `backend/app/models/legacy/`
2. Feature flag: `USE_WEBMETHODS_MODELS` (default: false during migration)
3. Parallel data storage during transition period
4. Ability to switch back to legacy models if issues arise

## Success Criteria

- [ ] All 39+ files updated and tested
- [ ] Kong transformation adapter working
- [ ] Apigee transformation adapter working
- [ ] All integration tests passing
- [ ] All E2E tests passing
- [ ] Data migration completed successfully
- [ ] Performance targets met
- [ ] Documentation updated
- [ ] Team trained on new architecture

## Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Data loss during migration | HIGH | Backup all data, parallel storage, rollback plan |
| Performance degradation | MEDIUM | Load testing, optimization, caching |
| Kong/Apigee transformation bugs | MEDIUM | Comprehensive testing, gradual rollout |
| Frontend breaking changes | MEDIUM | API versioning, backward compatibility layer |
| Team learning curve | LOW | Documentation, training sessions, pair programming |

## Timeline

- **Week 1-2**: Preparation & Model Migration
- **Week 3-4**: Adapter & Repository Layer
- **Week 5-6**: Service & Agent Layer
- **Week 7-8**: API & Frontend Layer
- **Week 9-10**: Testing, Migration, Documentation

**Total**: 8-10 weeks with 2-3 developers

## Approval Required

- [ ] Architecture review approved
- [ ] Timeline approved
- [ ] Resource allocation approved
- [ ] Risk assessment approved
- [ ] Rollback plan approved

---

**Document Owner**: Development Team  
**Last Updated**: 2026-04-09  
**Next Review**: Before Phase 0 execution