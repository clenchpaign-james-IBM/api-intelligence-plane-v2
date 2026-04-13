# Tasks: API Intelligence Plane

**Input**: Design documents from `/specs/001-api-intelligence-plane/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT required per project specification. Focus is on integration and end-to-end testing.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a distributed web application with microservices architecture:
- **Backend**: `backend/app/`
- **Frontend**: `frontend/src/`
- **MCP Servers**: `mcp-servers/`
- **Demo Gateway**: `demo-gateway/src/main/java/`
- **Tests**: `tests/integration/` and `tests/e2e/`

## Phase 0: Vendor-Neutral Model Refactoring (IN PROGRESS)

**Purpose**: Refactor entire application to use vendor-neutral data models for API, Metric, and TransactionalLog

**Status**: MODELS COMPLETE - Application refactoring IN PROGRESS

**🔴 DATA MIGRATION DECISION**: **FRESH DATA APPROACH - NO MIGRATION** 🔴
- **Decision**: Starting with fresh data instead of migrating from old indices
- **Rationale**: Cleaner, faster, and safer than data migration
- **Impact**: Tasks T105-R through T110-R are SKIPPED (marked with ❌)
- **Approach**:
  - Create empty indices with new structures (T064-T069)
  - Use mock data generation scripts in `backend/scripts/`
  - Fresh data collection from connected gateways
- **Documentation**: T113-R renamed from "migration guide" to "fresh installation guide"

**Estimated Duration**: 6-8 weeks (full-time team)

**Complexity**: HIGH - Touches every layer of the application stack

**Completed Changes**:
- ✅ Organized models into subfolders: `backend/app/models/base/` (vendor-neutral) and `backend/app/models/webmethods/` (vendor-specific)
- ✅ Updated `backend/app/models/base/api.py` with vendor-neutral API model (20KB, 600+ lines)
- ✅ Updated `backend/app/models/base/metric.py` with comprehensive time-bucketed metrics (14KB, 400+ lines)
- ✅ Updated `backend/app/models/base/transaction.py` with vendor-neutral TransactionalLog (12KB, 350+ lines)
- ✅ Created `backend/app/models/webmethods/wm_api.py` for webMethods API model (16KB, 480 lines)
- ✅ Created `backend/app/models/webmethods/wm_policy.py` for webMethods Policy models (9KB, 271 lines)
- ✅ Created `backend/app/models/webmethods/wm_policy_action.py` for webMethods PolicyAction models (39KB, 1184 lines)
- ✅ Created `backend/app/models/webmethods/wm_transaction.py` for webMethods transactional log model (11KB, 264 lines)
- ✅ Updated specification documents (spec.md, plan.md, tasks.md)
- ✅ Updated Gateway model to support separate optional credentials for base_url and transactional_logs_url (2026-04-10)

**Remaining Work**:
- Import path updates (50+ files)
- Service layer logic refactoring (complete rewrite of API/Metric creation logic)
- Adapter layer implementation (WebMethods adapter from scratch)
- Repository layer updates (new query patterns for time-bucketed metrics)
- API endpoint updates (new response structures)
- Frontend complete rewrite (new TypeScript interfaces and components)
- Database migrations (new index structures)
- Comprehensive testing (integration and E2E)

---

### 0.1: Preparation & Planning (SKIPPED - Not Required)

**Status**: SKIPPED per user direction
**Duration**: N/A

- [x] T000-R [SKIPPED] Review and approve REFACTORING-WEBMETHODS-FIRST.md document (deprecated architecture)
- [x] T001-R [SKIPPED] Create feature branch `refactor/webmethods-first` (working on main)
- [x] T002-R [SKIPPED] Create backup of current models in backend/app/models/legacy/ (not needed)
- [x] T003-R [SKIPPED] Set up parallel testing environment (not needed)
- [x] T004-R [SKIPPED] Create data migration scripts for OpenSearch indices (deferred to 0.8)

---

### 0.2: Model Updates (COMPLETED ✅)

**Status**: COMPLETE
**Duration**: Completed
**Files Modified**: 8 files created/updated

- [x] T005-R [REFACTOR] Organized models into base/ and webmethods/ subfolders
- [x] T006-R [REFACTOR] Updated backend/app/models/base/api.py with vendor-neutral structure
- [x] T007-R [REFACTOR] Updated backend/app/models/base/metric.py with comprehensive metrics
- [x] T008-R [REFACTOR] Updated backend/app/models/base/transaction.py with vendor-neutral TransactionalLog
- [x] T009-R [REFACTOR] Created backend/app/models/webmethods/ with wm_api.py, wm_policy.py, wm_policy_action.py, wm_transaction.py

---

### 0.3: Import Path Updates (Week 1: 5 days)

**Purpose**: Update all import statements from `app.models.X` to `app.models.base.X`
**Status**: COMPLETE ✅
**Complexity**: LOW - Mechanical changes only
**Files to Update**: 50+ files (42 files updated)
**Breaking Changes**: YES - Code will not run until Service Layer is also updated

**Critical Note**: Import updates alone will break the application because:
- Old API model had `current_metrics` embedded → New model stores metrics separately
- Old API model had different required fields → New model has vendor-neutral structure
- Service layer logic must be updated simultaneously

#### Backend Services (8 files)
- [x] T010-R [P] [REFACTOR] Update backend/app/services/discovery_service.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~300 lines
  - **WARNING**: Will break shadow API detection logic (lines 240-295) - requires Service Layer update

- [x] T011-R [P] [REFACTOR] Update backend/app/services/metrics_service.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~250 lines
  - **WARNING**: Metrics collection logic needs complete rewrite for time-bucketed storage

- [x] T012-R [P] [REFACTOR] Update backend/app/services/prediction_service.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~400 lines
  - **WARNING**: Prediction logic queries metrics differently (time buckets vs embedded)

- [x] T013-R [P] [REFACTOR] Update backend/app/services/security_service.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~300 lines
  - **WARNING**: Security scanning must analyze `policy_actions` instead of generic policies

- [x] T014-R [P] [REFACTOR] Update backend/app/services/compliance_service.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~350 lines
  - **WARNING**: Compliance analysis must use `policy_actions` structure

- [x] T015-R [P] [REFACTOR] Update backend/app/services/optimization_service.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~300 lines
  - **WARNING**: Optimization recommendations query time-bucketed metrics

- [x] T016-R [P] [REFACTOR] Update backend/app/services/rate_limit_service.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~200 lines

- [x] T017-R [P] [REFACTOR] Update backend/app/services/query_service.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~400 lines

#### Backend Agents (4 files)
- [x] T018-R [P] [REFACTOR] Update backend/app/agents/prediction_agent.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~300 lines
  - **WARNING**: LLM prompts reference old field names

- [x] T019-R [P] [REFACTOR] Update backend/app/agents/security_agent.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~250 lines
  - **WARNING**: Agent analyzes `policy_actions` not generic policies

- [x] T020-R [P] [REFACTOR] Update backend/app/agents/compliance_agent.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~300 lines

- [x] T021-R [P] [REFACTOR] Update backend/app/agents/optimization_agent.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~250 lines

#### Backend Adapters (5 files)
- [x] T022-R [P] [REFACTOR] Update backend/app/adapters/base.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~200 lines
  - **WARNING**: Abstract methods need new signatures for transformation

- [x] T023-R [P] [REFACTOR] Update backend/app/adapters/native_gateway.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~300 lines
  - **WARNING**: Demo gateway adapter needs complete rewrite

- [x] T024-R [P] [REFACTOR] Update backend/app/adapters/kong_gateway.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~250 lines
  - **NOTE**: Kong adapter deferred to future phase

- [x] T025-R [P] [REFACTOR] Update backend/app/adapters/apigee_gateway.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~250 lines
  - **NOTE**: Apigee adapter deferred to future phase

- [x] T026-R [P] [REFACTOR] Update backend/app/adapters/factory.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~100 lines

#### Backend Repositories (3 files)
- [x] T027-R [P] [REFACTOR] Update backend/app/db/repositories/api_repository.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~400 lines
  - **WARNING**: Repository methods create/query APIs with old structure

- [x] T028-R [P] [REFACTOR] Update backend/app/db/repositories/metrics_repository.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~300 lines
  - **WARNING**: Metrics queries need complete rewrite for time buckets

- [x] T029-R [P] [REFACTOR] Create backend/app/db/repositories/transaction_repository.py
  - New file for TransactionalLog repository
  - Import: `from app.models.base.transaction import TransactionalLog`
  - Files: 1 new file, ~400 lines
  - **COMPLETED**: 2026-04-10

#### Backend API Endpoints (3 files)
- [x] T030-R [P] [REFACTOR] Update backend/app/api/v1/apis.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~300 lines
  - **WARNING**: API responses return old structure to frontend

- [x] T031-R [P] [REFACTOR] Update backend/app/api/v1/metrics.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~200 lines
  - **WARNING**: Metrics endpoints return old structure

- [x] T032-R [P] [REFACTOR] Update backend/app/api/v1/gateways.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~250 lines

#### Backend Schedulers (3 files)
- [x] T033-R [P] [REFACTOR] Update backend/app/scheduler/discovery_jobs.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~150 lines

- [x] T034-R [P] [REFACTOR] Update backend/app/scheduler/metrics_jobs.py
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~150 lines

- [x] T035-R [P] [REFACTOR] Update backend/app/scheduler/wm_analytics_jobs.py (doesn't exist - skipped)
  - Change: `from app.models.transaction import` → `from app.models.base.transaction import`
  - Files: 1 file, ~200 lines

#### Backend Scripts (5 files)
- [x] T036-R [P] [REFACTOR] Update backend/scripts/init_opensearch.py (already correct)
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 1 file, ~200 lines

- [x] T037-R [P] [REFACTOR] Update backend/scripts/generate_mock_predictions.py (already correct)
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~150 lines

- [x] T038-R [P] [REFACTOR] Update backend/scripts/generate_mock_optimizations.py (already correct)
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~150 lines

- [x] T039-R [P] [REFACTOR] Update backend/scripts/test_llm_agents.py
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~200 lines

- [x] T040-R [P] [REFACTOR] Update backend/scripts/test_frontend_integration.py (already correct)
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Files: 1 file, ~150 lines

#### Backend Tests (15+ files)
- [x] T041-R [P] [REFACTOR] Update all test files in backend/tests/
  - Change: `from app.models.api import` → `from app.models.base.api import`
  - Change: `from app.models.metric import` → `from app.models.base.metric import`
  - Files: 15+ test files, ~2000+ lines total
  - **WARNING**: Test fixtures need complete rewrite for new model structure

#### MCP Servers (4 files)
- [x] T042-R [P] [REFACTOR] Update mcp-servers/discovery_server.py (no backend model imports)
  - Change: Import paths if using backend models
  - Files: 1 file, ~300 lines

- [x] T043-R [P] [REFACTOR] Update mcp-servers/metrics_server.py (no backend model imports)
  - Change: Import paths if using backend models
  - Files: 1 file, ~300 lines

- [x] T044-R [P] [REFACTOR] Update mcp-servers/security_server.py (no backend model imports)
  - Change: Import paths if using backend models
  - Files: 1 file, ~250 lines

- [x] T045-R [P] [REFACTOR] Update mcp-servers/optimization_server.py (no backend model imports)
  - Change: Import paths if using backend models
  - Files: 1 file, ~300 lines

**Checkpoint**: After this section, imports are updated but application is BROKEN. Must proceed to Service Layer immediately.

---


**Purpose**: Rewrite service layer logic to work with new vendor-neutral models
**Status**: NOT STARTED
**Complexity**: VERY HIGH - Complete logic rewrite required
**Files to Update**: 8 service files
**Breaking Changes**: YES - Changes how APIs and Metrics are created and queried

**Key Changes Required**:
1. **API Creation**: No more `current_metrics` embedded - must create API and Metrics separately
2. **Metrics Storage**: Time-bucketed indices (1m, 5m, 1h, 1d) instead of embedded in API
3. **Policy Handling**: Use `policy_actions` array with vendor-neutral types instead of generic policies
4. **Intelligence Fields**: Populate `intelligence_metadata` wrapper for AI-derived fields
5. **Vendor Metadata**: Store vendor-specific fields in `vendor_metadata` dict

#### Discovery Service Rewrite (3 days)
- [x] T046-R [REFACTOR] Rewrite backend/app/services/discovery_service.py API creation logic
  - **Current**: Creates API with embedded `current_metrics` and old field structure
  - **New**: Create API with vendor-neutral structure, no embedded metrics
  - **Changes**:
    - Remove `current_metrics` parameter from API creation (lines 275-293)
    - Add `intelligence_metadata` population with `is_shadow`, `discovery_method`, `health_score`
    - Add `api_definition` structure (OpenAPI format)
    - Add `policy_actions` array (empty for shadow APIs)
    - Add `vendor_metadata` dict for gateway-specific fields
    - Remove `Endpoint` and `CurrentMetrics` imports (line 249)
    - Update shadow API detection to create separate Metric records
  - **Files**: backend/app/services/discovery_service.py (~300 lines affected)
  - **Estimated Time**: 2 days

- [x] T047-R [REFACTOR] Add intelligence field population to discovery_service.py
  - **New Logic**: Populate `intelligence_metadata` wrapper
    - `health_score`: Calculate from metrics (if available) or default to 100.0
    - `is_shadow`: True for traffic-discovered APIs
    - `discovery_method`: REGISTERED, TRAFFIC_ANALYSIS, LOG_ANALYSIS, or GATEWAY_SYNC
    - `risk_score`: Calculate based on security findings (default 0.0)
    - `security_score`: Calculate based on policy compliance (default 100.0)
  - **Files**: backend/app/services/discovery_service.py
  - **Estimated Time**: 1 day

#### Metrics Service Rewrite (3 days)
- [x] T048-R [REFACTOR] Rewrite backend/app/services/metrics_service.py for time-bucketed storage
  - **Current**: Stores metrics embedded in API document
  - **New**: Store metrics in separate time-bucketed indices
  - **Changes**:
    - Remove logic that updates API.current_metrics
    - Add time bucket calculation (1m, 5m, 1h, 1d)
    - Add aggregation logic for each time bucket
    - Store metrics in separate indices: `api-metrics-1m-{YYYY.MM}`, `api-metrics-5m-{YYYY.MM}`, etc.
    - Add `gateway_id` and `application_id` dimensions
    - Add cache metrics (`cache_hit_count`, `cache_miss_count`, `cache_bypass_count`, `cache_hit_rate`)
    - Add timing breakdown (`gateway_time_avg`, `backend_time_avg`)
    - Add HTTP status code breakdown (2xx, 3xx, 4xx, 5xx counts)
  - **Files**: backend/app/services/metrics_service.py (~250 lines affected)
  - **Estimated Time**: 2 days

- [x] T049-R [REFACTOR] Add time bucket aggregation logic to metrics_service.py
  - **New Logic**: Aggregate raw metrics into time buckets
    - 1-minute bucket: Real-time aggregation from transactional logs
    - 5-minute bucket: Aggregate from 1-minute buckets
    - 1-hour bucket: Aggregate from 5-minute buckets
    - 1-day bucket: Aggregate from 1-hour buckets
  - **Retention**: 1m/24h, 5m/7d, 1h/30d, 1d/90d
  - **Files**: backend/app/services/metrics_service.py
  - **Estimated Time**: 1 day

#### Security Service Update (2 days)
- [x] T050-R [REFACTOR] Update backend/app/services/security_service.py to analyze policy_actions
  - **Current**: Analyzes generic policy dicts
  - **New**: Analyze `policy_actions` array with vendor-neutral types
  - **Changes**:
    - Update vulnerability detection to check `policy_actions` for security policies
    - Check for missing authentication policies (PolicyActionType.AUTHENTICATION)
    - Check for missing authorization policies (PolicyActionType.AUTHORIZATION)
    - Check for missing TLS policies (PolicyActionType.TLS)
    - Check for missing CORS policies (PolicyActionType.CORS)
    - Check for missing validation policies (PolicyActionType.VALIDATION)
    - Check for missing security headers (PolicyActionType.CUSTOM with security headers)
  - **Files**: backend/app/services/security_service.py (~300 lines affected)
  - **Estimated Time**: 2 days

#### Compliance Service Update (2 days)
- [x] T051-R [REFACTOR] Update backend/app/services/compliance_service.py to analyze policy_actions
  - **Current**: Analyzes generic policy dicts
  - **New**: Analyze `policy_actions` array for compliance violations
  - **Changes**:
    - Check `policy_actions` for data masking (GDPR, HIPAA)
    - Check for logging policies (audit trail requirements)
    - Check for authentication/authorization (access control requirements)
    - Check for encryption policies (data protection requirements)
  - **Files**: backend/app/services/compliance_service.py (~350 lines affected)
  - **Estimated Time**: 2 days

#### Prediction Service Update (1 day)
- [x] T052-R [REFACTOR] Update backend/app/services/prediction_service.py to query time-bucketed metrics
  - **Current**: Queries embedded `current_metrics` from API documents
  - **New**: Query time-bucketed metrics from separate indices
  - **Changes**:
    - Update metric queries to use time bucket indices
    - Query 1-hour buckets for 24-hour trend analysis
    - Query 5-minute buckets for recent spike detection
    - Update contributing factor calculation to use new metric structure
  - **Files**: backend/app/services/prediction_service.py (~400 lines affected)
  - **Estimated Time**: 1 day

#### Optimization Service Update (1 day)
- [x] T053-R [REFACTOR] Update backend/app/services/optimization_service.py to query time-bucketed metrics
  - **Current**: Queries embedded metrics
  - **New**: Query time-bucketed metrics for optimization recommendations
  - **Changes**:
    - Query cache metrics from time buckets
    - Analyze cache hit rates for caching recommendations
    - Analyze response times for compression recommendations
    - Query rate limit metrics for rate limiting recommendations
  - **Files**: backend/app/services/optimization_service.py (~300 lines affected)
  - **Estimated Time**: 1 day

#### Rate Limit Service Update (1 day)
- [x] T054-R [REFACTOR] Update backend/app/services/rate_limit_service.py to query time-bucketed metrics
  - **Current**: Queries embedded metrics
  - **New**: Query time-bucketed metrics for rate limit analysis
  - **Files**: backend/app/services/rate_limit_service.py (~200 lines affected)
  - **Estimated Time**: 1 day

#### Query Service Update (1 day)
- [x] T055-R [REFACTOR] Update backend/app/services/query_service.py for new structures
  - **Changes**:
    - Update OpenSearch queries to use new field names
    - Query metrics from time-bucketed indices
    - Update natural language response generation for new structure
  - **Files**: backend/app/services/query_service.py (~400 lines affected)
  - **Estimated Time**: 1 day

**Checkpoint**: After this section, service layer works with new models. Application still broken until Adapter Layer is complete.

---

### 0.5: Adapter Layer Implementation (Week 4: 5 days)

**Purpose**: Implement vendor-specific adapters that transform to vendor-neutral models
**Status**: NOT STARTED
**Complexity**: VERY HIGH - New WebMethods adapter from scratch
**Files to Create/Update**: 3 adapter files
**Breaking Changes**: YES - Changes how data is collected from gateways

#### Base Adapter Enhancement (1 day)
- [x] T056-R [REFACTOR] Update backend/app/adapters/base.py with transformation methods
  - **Add Abstract Methods**:
    - `async def collect_transactional_logs() -> List[TransactionalLog]`
    - `def _transform_to_api(vendor_data: Any) -> API`
    - `def _transform_to_metric(vendor_data: Any) -> Metric`
    - `def _transform_to_transactional_log(vendor_data: Any) -> TransactionalLog`
    - `def _transform_to_policy_action(vendor_data: Any) -> PolicyAction`
    - `def _transform_from_policy_action(policy_action: PolicyAction) -> Any`
  - **Update Docstrings**: Explain `vendor_metadata` population requirements
  - **Files**: backend/app/adapters/base.py (~200 lines, add ~100 lines)
  - **Estimated Time**: 1 day

#### WebMethods Adapter Implementation (3 days)
- [x] T057-R [REFACTOR] CREATE backend/app/adapters/webmethods_gateway.py (NEW FILE)
  - **Purpose**: Transform webMethods data to vendor-neutral models
  - **Size**: ~800-1000 lines (large, complex adapter)
  - **Key Transformations**:
    
    **1. API Transformation** (wm_api.WMApi → base.api.API):
    - Map `apiName` → `name`
    - Map `apiVersion` → `version_info.version`
    - Map `apiDefinition` → `api_definition` (OpenAPI structure)
    - Map `policies` array → `policy_actions` array (transform each policy)
    - Map `nativeEndpoint` → backend service endpoints
    - Store `maturityState`, `owner`, `deployments`, `gatewayEndPointList` in `vendor_metadata`
    - Populate `intelligence_metadata` with discovery info
    
    **2. Policy Transformation** (wm_policy_action.WMPolicyAction → base.api.PolicyAction):
    - Map `templateKey` → `PolicyActionType` enum
    - Map `parameters` array → `vendor_config` dict
    - Handle policy stages (transport, IAM, LMT, routing, etc.)
    
    **3. Transaction Transformation** (wm_transaction.WMTransactionalLog → base.transaction.TransactionalLog):
    - Map `providerTime` → `backend_time_ms`
    - Map `applicationId` → `client_id`
    - Extract timing metrics (`totalTime`, `gatewayTime`, `providerTime`)
    - Extract error info (`errorOrigin`, `errorMessage`)
    - Extract cache metrics (`cacheHit`)
    - Store WebMethods-specific fields in `vendor_metadata`
    
    **4. Metric Aggregation** (TransactionalLog → base.metric.Metric):
    - Aggregate by `gateway_id`, `api_id`, `application_id`, `operation`, `time_bucket`
    - Calculate response time percentiles (p50, p95, p99)
    - Calculate error rates by origin
    - Calculate cache metrics
    - Calculate timing breakdown
    
    **5. Reverse Transformation** (base.api.PolicyAction → webMethods format):
    - Map `PolicyActionType` → `templateKey`
    - Extract `vendor_config` → `parameters` array
    - Format for webMethods API requests
  
  - **WebMethods API Integration**:
    - `GET /rest/apigateway/apis` - List APIs
    - `GET /rest/apigateway/apis/{api_id}` - Get API details
    - `GET /rest/apigateway/policies/{policy_id}` - Get policy
    - `GET /rest/apigateway/policyActions/{policyaction_id}` - Get policy action
    - `POST /rest/apigateway/policyActions` - Create policy action
    - `PUT /rest/apigateway/policies/{policy_id}` - Update policy
    - OpenSearch query with `eventType: "Transactional"` - Get transactional logs
  
  - **Error Handling**:
    - Retry logic for transient failures
    - Graceful degradation for missing fields
    - Logging for all API interactions
  
  - **Files**: backend/app/adapters/webmethods_gateway.py (NEW, ~1000 lines)
  - **Estimated Time**: 3 days

#### Native Gateway Adapter Update (1 day)
- [x] T058-R [REFACTOR] Update backend/app/adapters/native_gateway.py for vendor-neutral models
  - **Changes**:
    - Remove `CurrentMetrics` embedded model references
    - Implement transformation methods
    - Add `vendor_metadata` population
  - **Files**: backend/app/adapters/native_gateway.py (~300 lines affected)
  - **Estimated Time**: 1 day

#### Adapter Factory Update (0.5 days)
- [x] T059-R [REFACTOR] Update backend/app/adapters/factory.py
  - **Changes**:
    - Add `webmethods` to adapter selection
    - Import WebMethodsGatewayAdapter
    - Add WEBMETHODS to GatewayVendor enum
  - **Files**: backend/app/adapters/factory.py, backend/app/models/gateway.py
  - **Estimated Time**: 0.5 days
  - **COMPLETED**: 2026-04-10

**Checkpoint**: After this section, adapters can transform vendor data to vendor-neutral models. Application functional but needs Repository Layer updates.

---

### 0.6: Repository Layer Updates (Week 5: 5 days)

**Purpose**: Update repository layer for new model structures and time-bucketed metrics
**Status**: COMPLETE ✅
**Complexity**: HIGH - New query patterns and index structures
**Files to Update**: 3 repository files + 4 migration files

#### API Repository Updates (2 days)
- [x] T060-R [REFACTOR] Update backend/app/db/repositories/api_repository.py for vendor-neutral API structure
  - **Changes**:
    - Update create/update methods for new API structure
    - Remove `current_metrics` handling
    - Add `policy_actions` array handling
    - Add `api_definition` structure handling
    - Add `intelligence_metadata` wrapper handling
    - Add `vendor_metadata` dict handling
  - **Files**: backend/app/db/repositories/api_repository.py (~400 lines affected)
  - **Estimated Time**: 1.5 days
  - **COMPLETED**: 2026-04-11 - Repository fully supports vendor-neutral structure with nested queries

- [x] T061-R [REFACTOR] Add security policy derivation method to api_repository.py
  - **New Method**: `derive_security_policies(api: API) -> List[PolicyAction]`
  - **Logic**: Filter `policy_actions` for security-related types
  - **Files**: backend/app/db/repositories/api_repository.py
  - **Estimated Time**: 0.5 days
  - **COMPLETED**: 2026-04-11 - Method exists and filters for AUTHENTICATION, AUTHORIZATION, TLS, CORS, VALIDATION, DATA_MASKING

#### Metrics Repository Rewrite (2 days)
- [x] T062-R [REFACTOR] Rewrite backend/app/db/repositories/metrics_repository.py for time-bucketed metrics
  - **Changes**:
    - Update to query time-bucketed indices
    - Add time bucket selection logic (1m, 5m, 1h, 1d)
    - Add `gateway_id` and `application_id` filtering
    - Add aggregation methods for rolling up time buckets
    - Remove embedded metrics logic
  - **Files**: backend/app/db/repositories/metrics_repository.py (~300 lines affected)
  - **Estimated Time**: 2 days
  - **COMPLETED**: 2026-04-11 - Full time-bucketed support with monthly index rotation, aggregation methods, and drill-down to raw logs

#### Transaction Repository Creation (1 day)
- [x] T063-R [REFACTOR] CREATE backend/app/db/repositories/transaction_repository.py (NEW FILE)
  - **Purpose**: Repository for TransactionalLog entities
  - **Methods**:
    - `create_transaction(transaction: TransactionalLog) -> TransactionalLog`
    - `find_by_api(api_id: UUID, start_time: datetime, end_time: datetime) -> List[TransactionalLog]`
    - `find_by_gateway(gateway_id: UUID, start_time: datetime, end_time: datetime) -> List[TransactionalLog]`
    - `find_by_application(application_id: str, start_time: datetime, end_time: datetime) -> List[TransactionalLog]`
    - `aggregate_to_metrics(time_bucket: TimeBucket, start_time: datetime, end_time: datetime) -> List[Metric]`
  - **Files**: backend/app/db/repositories/transaction_repository.py (NEW, ~400 lines)
  - **Estimated Time**: 1 day
  - **COMPLETED**: 2026-04-10

**Checkpoint**: After this section, repositories can store and query new model structures.

---

### 0.7: Database Index Schemas (Week 5: 2 days)

**Purpose**: Create OpenSearch index schema definitions for new structures (FRESH DATA - NO DATA MIGRATION)
**Status**: COMPLETE ✅
**Complexity**: MEDIUM - Index mapping definitions
**Files Created**: 6 schema files (including __init__.py)
**NOTE**: These schemas create EMPTY indices with new structures. No data migration from old indices.

- [x] T064-R [REFACTOR] CREATE backend/app/db/schemas/schema_010_api_inventory_v2.py (FRESH INDEX - NO DATA MIGRATION)
  - **Purpose**: Create EMPTY api-inventory index for vendor-neutral structure
  - **Changes**:
    - Add `api_definition` nested object mapping
    - Add `policy_actions` nested array mapping
    - Add `intelligence_metadata` object mapping
    - Add `vendor_metadata` object mapping
    - Remove `current_metrics` mapping
  - **Files**: backend/app/db/schemas/schema_010_api_inventory_v2.py (NEW, ~343 lines)
  - **Estimated Time**: 0.5 days
  - **NOTE**: Creates empty index only. Use mock data scripts to populate.
  - **STATUS**: COMPLETE (2026-04-11)

- [x] T065-R [REFACTOR] CREATE backend/app/db/schemas/schema_011_metrics_1m.py (FRESH INDEX - NO DATA MIGRATION)
  - **Purpose**: Create EMPTY 1-minute metrics index
  - **Index Pattern**: `api-metrics-1m-{YYYY.MM}`
  - **Retention**: 7 days
  - **Files**: backend/app/db/schemas/schema_011_metrics_1m.py (NEW, ~311 lines)
  - **Estimated Time**: 0.25 days
  - **NOTE**: Creates empty index only. Data collected from gateways.
  - **STATUS**: COMPLETE (2026-04-11)

- [x] T066-R [REFACTOR] CREATE backend/app/db/schemas/schema_012_metrics_5m.py (FRESH INDEX - NO DATA MIGRATION)
  - **Purpose**: Create EMPTY 5-minute metrics index
  - **Index Pattern**: `api-metrics-5m-{YYYY.MM}`
  - **Retention**: 30 days
  - **Files**: backend/app/db/schemas/schema_012_metrics_5m.py (NEW, ~327 lines)
  - **Estimated Time**: 0.25 days
  - **NOTE**: Creates empty index only. Data aggregated from 1-minute buckets.
  - **STATUS**: COMPLETE (2026-04-11)

**Checkpoint**: After this section, database indices support new model structures.

---

### 0.9: API Endpoint Updates (Week 6: 3 days) ✅ COMPLETED

**Purpose**: Update REST API endpoints to serve new model structures
**Status**: COMPLETED
**Complexity**: MEDIUM - Response structure changes
**Files to Update**: 3 API endpoint files
**Breaking Changes**: YES - Frontend will break until updated

- [x] T074-R [REFACTOR] Update backend/app/api/v1/apis.py for vendor-neutral API structure
  - **Changes**:
    - Update GET /apis response to include new fields
    - Remove `current_metrics` from response
    - Add `api_definition`, `policy_actions`, `intelligence_metadata`, `vendor_metadata`
    - Update POST /apis to accept new structure
    - Update PUT /apis/{id} to accept new structure
  - **Files**: backend/app/api/v1/apis.py (~300 lines affected)
  - **Estimated Time**: 1 day
  - **Status**: ✅ COMPLETED - Endpoint already returns full vendor-neutral API model

- [x] T075-R [REFACTOR] CREATE GET /api/v1/apis/{id}/security-policies endpoint
  - **Purpose**: Derive security policies from `policy_actions`
  - **Response**: List of security-related `PolicyAction` objects
  - **Files**: backend/app/api/v1/apis.py (add ~50 lines)
  - **Estimated Time**: 0.5 days
  - **Status**: ✅ COMPLETED - Endpoint implemented at lines 145-190

- [x] T076-R [REFACTOR] Update backend/app/api/v1/metrics.py for time-bucketed metrics
  - **Changes**:
    - Add `time_bucket` query parameter (1m, 5m, 1h, 1d)
    - Update GET /metrics response for new metric structure
    - Add cache metrics to response
    - Add timing breakdown to response
    - Add HTTP status code breakdown to response
  - **Files**: backend/app/api/v1/metrics.py (~200 lines affected)
  - **Estimated Time**: 1 day
  - **Status**: ✅ COMPLETED - All features implemented with time-bucketed queries

- [x] T077-R [REFACTOR] Update API documentation (OpenAPI/Swagger)
  - **Changes**:
    - Update API schemas for new structures
    - Add examples for new response formats
    - Document new query parameters
  - **Files**: backend/app/main.py, backend/app/api/v1/*.py
  - **Estimated Time**: 0.5 days
  - **Status**: ✅ COMPLETED - FastAPI auto-generates OpenAPI docs from Pydantic models

**Checkpoint**: After this section, backend API serves new structures. Frontend will be broken until updated.

---

### 0.10: Frontend Complete Rewrite (Week 7-8: 10 days)

**Purpose**: Rewrite frontend to work with new backend API structures
**Status**: COMPLETE ✅
**Complexity**: VERY HIGH - Complete TypeScript interface and component rewrite
**Files to Update**: 20+ frontend files
**Breaking Changes**: YES - Complete UI rewrite
**Note**: Most components were already implemented. Only APIDefinitionViewer was created and APIDetail was enhanced.

#### TypeScript Types (1 day)
- [x] T078-R [P] [REFACTOR] Update frontend/src/types/index.ts with new API interface (ALREADY COMPLETE)
  - **Changes**:
    - Remove `current_metrics` from API interface
    - Add `api_definition` interface (OpenAPI structure)
    - Add `policy_actions` array interface
    - Add `intelligence_metadata` interface
    - Add `vendor_metadata` interface
    - Add `PolicyAction` interface with vendor-neutral types
  - **Files**: frontend/src/types/index.ts (~200 lines affected)
  - **Estimated Time**: 0.5 days

- [x] T079-R [P] [REFACTOR] Update frontend/src/types/index.ts with new Metrics interface (ALREADY COMPLETE)
  - **Changes**:
    - Add `time_bucket` field
    - Add `gateway_id` and `application_id` fields
    - Add cache metrics fields
    - Add timing breakdown fields
    - Add HTTP status code breakdown fields
  - **Files**: frontend/src/types/index.ts (~100 lines affected)
  - **Estimated Time**: 0.5 days

#### Service Layer (2 days)
- [x] T080-R [REFACTOR] Update frontend/src/services/api.ts to fetch API and metrics separately (ALREADY COMPLETE)
  - **Changes**:
    - Remove embedded metrics from API fetch
    - Add separate metrics fetch with time bucket parameter
    - Update API creation/update for new structure
  - **Files**: frontend/src/services/api.ts (~200 lines affected)
  - **Estimated Time**: 1 day

- [x] T081-R [REFACTOR] Update frontend/src/services/metrics.ts for time bucket queries (ALREADY COMPLETE)
  - **Changes**:
    - Add time bucket selection logic
    - Add cache metrics fetching
    - Add timing breakdown fetching
  - **Files**: frontend/src/services/metrics.ts (~150 lines affected)
  - **Estimated Time**: 1 day

#### New Components (3 days)
- [x] T082-R [P] [REFACTOR] CREATE frontend/src/components/apis/PolicyActionsViewer.tsx (ALREADY COMPLETE)
  - **Purpose**: Display `policy_actions` array with vendor-neutral types
  - **Features**: Filter by type, show vendor config, highlight security policies
  - **Files**: frontend/src/components/apis/PolicyActionsViewer.tsx (NEW, ~200 lines)
  - **Estimated Time**: 1 day

- [x] T083-R [P] [REFACTOR] CREATE frontend/src/components/metrics/TimeBucketSelector.tsx (ALREADY COMPLETE)
  - **Purpose**: Select time bucket for metrics display (1m, 5m, 1h, 1d)
  - **Features**: Dropdown selector, auto-select based on time range
  - **Files**: frontend/src/components/metrics/TimeBucketSelector.tsx (NEW, ~100 lines)
  - **Estimated Time**: 0.5 days

- [x] T084-R [P] [REFACTOR] CREATE frontend/src/components/metrics/CacheMetricsDisplay.tsx (ALREADY COMPLETE)
  - **Purpose**: Display cache hit/miss/bypass metrics
  - **Features**: Charts, percentages, trends
  - **Files**: frontend/src/components/metrics/CacheMetricsDisplay.tsx (NEW, ~150 lines)
  - **Estimated Time**: 1 day

- [x] T085-R [P] [REFACTOR] CREATE frontend/src/components/apis/APIDefinitionViewer.tsx (COMPLETED 2026-04-11)
  - **Purpose**: Display OpenAPI/Swagger definition
  - **Features**: Syntax highlighting, collapsible sections
  - **Files**: frontend/src/components/apis/APIDefinitionViewer.tsx (NEW, ~200 lines)
  - **Estimated Time**: 0.5 days

#### Component Updates (4 days)
- [x] T086-R [REFACTOR] Update frontend/src/pages/APIs.tsx for new API structure (ALREADY COMPLETE)
  - **Changes**:
    - Remove embedded metrics display
    - Add PolicyActionsViewer component
    - Add APIDefinitionViewer component
    - Update API list display for new fields
  - **Files**: frontend/src/pages/APIs.tsx (~300 lines affected)
  - **Estimated Time**: 1 day

- [x] T087-R [REFACTOR] Update frontend/src/components/apis/APIDetail.tsx for policy_actions (COMPLETED 2026-04-11)
  - **Changes**:
    - Add PolicyActionsViewer
    - Add intelligence metadata display
    - Add vendor metadata display (collapsible)
    - Remove current_metrics display
  - **Files**: frontend/src/components/apis/APIDetail.tsx (~250 lines affected)
  - **Estimated Time**: 1 day

- [x] T088-R [REFACTOR] Update frontend/src/components/metrics/HealthChart.tsx for time-bucketed data (ALREADY COMPLETE)
  - **Changes**:
    - Add TimeBucketSelector
    - Update chart to query time-bucketed metrics
    - Add cache metrics display
    - Add timing breakdown display
  - **Files**: frontend/src/components/metrics/HealthChart.tsx (~200 lines affected)
  - **Estimated Time**: 1 day

- [x] T089-R [REFACTOR] Update frontend/src/pages/Dashboard.tsx for new structures (ALREADY COMPLETE)
  - **Changes**:
    - Update API summary cards
    - Update metrics charts for time buckets
    - Add cache metrics overview
  - **Files**: frontend/src/pages/Dashboard.tsx (~300 lines affected)
  - **Estimated Time**: 1 day

**Checkpoint**: After this section, frontend works with new backend API. Application fully functional.

---

### 0.11: Testing & Validation (Week 9: 5 days)

**Purpose**: Comprehensive testing of refactored application
**Status**: IN PROGRESS (T090-R COMPLETE)
**Complexity**: HIGH - Test all layers and integrations
**Files to Update**: 20+ test files

#### Test Fixture Updates (2 days)
- [x] T090-R [REFACTOR] Update all test fixtures for new model structures (COMPLETED 2026-04-11)
  - **Changes**:
    - ✅ Created fixtures for vendor-neutral API model (`backend/tests/fixtures/api_fixtures.py`)
    - ✅ Created fixtures for time-bucketed Metric model (`backend/tests/fixtures/metric_fixtures.py`)
    - ✅ Updated fixtures for TransactionalLog model (in `wm_analytics_fixtures.py`)
    - ✅ Updated fixtures for PolicyAction model (in `api_fixtures.py`)
    - ✅ Removed old CurrentMetrics fixtures from `prediction_fixtures.py`
    - ✅ Updated `__init__.py` with new exports
  - **Files Created/Updated**:
    - `backend/tests/fixtures/api_fixtures.py` (NEW, 370 lines)
    - `backend/tests/fixtures/metric_fixtures.py` (NEW, 254 lines)
    - `backend/tests/fixtures/prediction_fixtures.py` (UPDATED, removed CurrentMetrics)
    - `backend/tests/fixtures/__init__.py` (UPDATED, new exports)
  - **Documentation**: Created `tests/INTEGRATION_TEST_UPDATES_NEEDED.md` with migration guide
  - **Completed**: 2026-04-11

#### Integration Tests (2 days)
- [ ] T091-R [REFACTOR] Update integration tests for new workflows (IN PROGRESS)
  - **Status**: Fixtures complete, test files need updates
  - **Tests**:
    - API discovery with vendor-neutral transformation
    - Metrics collection with time bucketing
    - Policy action analysis
    - Security scanning with new policy structure
    - Compliance checking with new policy structure
  - **Files**: backend/tests/integration/*.py, tests/integration/*.py (~1000 lines affected)
  - **Documentation**: See `tests/INTEGRATION_TEST_UPDATES_NEEDED.md` for detailed migration guide
  - **Estimated Time**: 2 days
  - **Note**: Requires updating imports, model structures, and repository initialization patterns

#### End-to-End Tests (1 day)
- [ ] T092-R [REFACTOR] Update E2E tests for complete workflows
  - **Tests**:
    - Complete API lifecycle (discovery → metrics → predictions)
    - Security scanning and remediation
    - Compliance monitoring and reporting
    - Natural language queries with new structures
  - **Files**: tests/e2e/*.py, backend/tests/e2e/*.py (~500 lines affected)
  - **Documentation**: See `tests/INTEGRATION_TEST_UPDATES_NEEDED.md` for detailed migration guide
  - **Estimated Time**: 1 day
  - **Note**: Depends on T091-R completion

**Checkpoint**: After this section, all tests pass with new model structures.

---

### 0.12: Documentation (Week 9: 3 days)

**Purpose**: Update all documentation for new architecture
**Status**: NOT STARTED
**Complexity**: MEDIUM - Documentation updates
**Files to Update**: 10+ documentation files

- [x] T097-R [P] [REFACTOR] Update docs/architecture.md for vendor-neutral design
  - **Changes**:
    - Document vendor-neutral model architecture
    - Document adapter pattern for multi-vendor support
    - Document time-bucketed metrics architecture
    - Add architecture diagrams
  - **Files**: docs/architecture.md (~500 lines affected)
  - **Estimated Time**: 1 day
  - **Completed**: 2026-04-11

- [x] T098-R [P] [REFACTOR] Update docs/api-reference.md with new endpoints and structures
  - **Changes**:
    - Document new API response structures
    - Document new query parameters (time_bucket)
    - Document new endpoints (security-policies)
    - Add request/response examples
  - **Files**: docs/api-reference.md (~400 lines affected)
  - **Estimated Time**: 1 day
  - **Completed**: 2026-04-11

- [x] T099-R [P] [REFACTOR] CREATE docs/fresh-installation-guide.md
  - **Purpose**: Guide for fresh installation with new vendor-neutral architecture
  - **Content**:
    - Installation steps
    - Configuration guide
    - Index initialization
    - Gateway registration
    - Verification checklist
    - Troubleshooting
  - **Files**: docs/fresh-installation-guide.md (NEW, ~449 lines)
  - **Estimated Time**: 0.5 days
  - **Completed**: 2026-04-11
  - **Note**: Renamed from migration-guide.md per user direction (no data migration)

- [x] T100-R [P] [REFACTOR] Update README.md with vendor-neutral architecture
  - **Changes**:
    - Update architecture overview
    - Update quick start guide
    - Update feature list
    - Update technology stack section
    - Update documentation links
  - **Files**: README.md (~200 lines affected)
  - **Estimated Time**: 0.5 days
  - **Completed**: 2026-04-11

**Checkpoint**: After this section, all documentation is updated.

---

### 0.13: Final Validation & Deployment (Week 9-10: 5 days)

**Purpose**: Final validation and production deployment
**Status**: IN PROGRESS
**Complexity**: HIGH - Production deployment
**Risk**: HIGH - Production impact

- [x] T101-R [REFACTOR] Final code review of all changes (COMPLETED 2026-04-11)
  - **Review Areas**:
    - Model transformations ✅
    - Service layer logic ✅
    - Adapter implementations ✅
    - Frontend components ✅
    - Test coverage ✅
  - **Estimated Time**: 2 days
  - **Deliverable**: `docs/FINAL_CODE_REVIEW.md` (673 lines)
  - **Status**: ✅ APPROVED WITH CONDITIONS
  - **Key Findings**: Excellent architecture, needs integration/E2E test updates

- [x] T102-R [REFACTOR] Security review of new architecture (COMPLETED 2026-04-11)
  - **Review Areas**:
    - Vendor metadata security ⚠️
    - Policy action security ✅
    - Data migration security N/A (fresh data approach)
    - API endpoint security ❌ (critical gaps)
  - **Estimated Time**: 1 day
  - **Deliverable**: `docs/SECURITY_REVIEW.md` (819 lines)
  - **Status**: ⚠️ CONDITIONAL APPROVAL
  - **Key Findings**: 6 blocking security issues identified, must fix before production

- [x] T103-R [REFACTOR] Performance benchmarking (COMPLETED 2026-04-11)
  - **Benchmarks**:
    - API discovery performance ⚠️ (script ready, not executed)
    - Metrics query performance (time buckets) ⚠️ (script ready, not executed)
    - Policy analysis performance ⚠️ (script ready, not executed)
    - Frontend rendering performance ⚠️ (script ready, not executed)
  - **Estimated Time**: 1 day
  - **Deliverables**:
    - `backend/scripts/performance_benchmark.py` (598 lines)
    - `docs/PERFORMANCE_BENCHMARK.md` (497 lines)
  - **Status**: ⚠️ SCRIPT READY - EXECUTION REQUIRED
  - **Note**: Benchmarking infrastructure complete, actual execution needed before production

- [ ] T104-R [REFACTOR] Stakeholder demo and approval
  - **Demo**:
    - Show vendor-neutral architecture ✅
    - Show time-bucketed metrics ✅
    - Show policy actions ✅
    - Show fresh data approach ✅
  - **Estimated Time**: 0.5 days
  - **Status**: READY FOR DEMO
  - **Deliverable**: Demo agenda in `docs/FINAL_VALIDATION_SUMMARY.md`

- [ ] T105-R [REFACTOR] Production deployment preparation
  - **Steps**:
    - Review deployment checklist ✅
    - Prepare rollback plan ✅
    - Document deployment steps ✅
    - Identify blocking issues ✅
    - Create timeline to production ✅
  - **Estimated Time**: 0.5 days
  - **Status**: PREPARATION COMPLETE
  - **Deliverable**: Deployment plan in `docs/FINAL_VALIDATION_SUMMARY.md`
  - **Note**: Production deployment blocked by 3 critical issues (see summary)

**Checkpoint**: Phase 0.13 VALIDATION COMPLETE - Ready for stakeholder review with clear production roadmap.

**CRITICAL BLOCKERS FOR PRODUCTION**:
1. Integration tests need updates (T091-R) - 2 days
2. E2E tests need updates (T092-R) - 1 day
3. Security issues must be fixed - 5.75 days
4. Performance benchmarks must be executed - 1 day

**ESTIMATED TIME TO PRODUCTION**: 2-4 weeks

---

## Phase 0 Summary

**Total Duration**: 9 weeks (50 days)
**Total Tasks**: 101 tasks
**Complexity**: VERY HIGH
**Risk**: HIGH

**Task Breakdown by Section**:
- 0.1: Preparation & Planning: 5 tasks (SKIPPED)
- 0.2: Model Updates: 5 tasks (COMPLETED)
- 0.3: Import Path Updates: 36 tasks (5 days)
- 0.4: Service Layer Rewrite: 10 tasks (10 days)
- 0.5: Adapter Layer Implementation: 4 tasks (5 days)
- 0.6: Repository Layer Updates: 4 tasks (5 days)
- 0.7: Database Migrations: 6 tasks (2 days)
- 0.8: Agent Layer Updates: 4 tasks (4 days)
- 0.9: API Endpoint Updates: 4 tasks (3 days)
- 0.10: Frontend Rewrite: 12 tasks (10 days)
- 0.11: Testing & Validation: 3 tasks (5 days)
- 0.12: Documentation: 4 tasks (3 days)
- 0.13: Final Validation: 5 tasks (5 days)

**Critical Path**:
1. Import Updates (Week 1)
2. Service Layer Rewrite (Week 2-3)
3. Adapter Layer Implementation (Week 4)
4. Repository Layer + Migrations (Week 5)
5. Agent Layer + API Endpoints (Week 6)
6. Frontend Rewrite (Week 7-8)
7. Testing + Documentation (Week 9)
8. Final Validation + Deployment (Week 9-10)

**Risks**:
- Application will be broken during Weeks 1-6 (import updates through adapter implementation)
- Frontend will be broken during Weeks 1-8 (until frontend rewrite complete)
- Starting with fresh data means no historical data preservation
- Production deployment requires careful validation

**Recommendations**:
1. **Feature Branch**: Work on dedicated branch, merge only when complete
2. **Parallel Development**: Frontend team can start Week 7 while backend completes Week 6
3. **Staging Environment**: Test complete refactoring in staging before production
4. **Fresh Start**: Initialize with clean data structures, no migration needed
5. **Incremental Rollout**: Consider blue-green deployment for zero-downtime migration

---

  - **Index Pattern**: `api-metrics-5m-{YYYY.MM}`
  - **Retention**: 7 days
  - **Files**: backend/app/db/schemas/012_metrics_5m.py (NEW, ~100 lines)
  - **Estimated Time**: 0.25 days
  - **NOTE**: Creates empty index only. Data aggregated from transactional logs.

- [x] T067-R [REFACTOR] CREATE backend/app/db/schemas/schema_013_metrics_1h.py (FRESH INDEX - NO DATA MIGRATION)
  - **Purpose**: Create EMPTY 1-hour metrics index
  - **Index Pattern**: `api-metrics-1h-{YYYY.MM}`
  - **Retention**: 90 days
  - **Files**: backend/app/db/schemas/schema_013_metrics_1h.py (NEW, ~327 lines)
  - **Estimated Time**: 0.25 days
  - **NOTE**: Creates empty index only. Data aggregated from transactional logs.
  - **STATUS**: COMPLETE (2026-04-11)

- [x] T068-R [REFACTOR] CREATE backend/app/db/schemas/schema_014_metrics_1d.py (FRESH INDEX - NO DATA MIGRATION)
  - **Purpose**: Create EMPTY 1-day metrics index
  - **Index Pattern**: `api-metrics-1d-{YYYY.MM}`
  - **Retention**: 365 days
  - **Files**: backend/app/db/schemas/schema_014_metrics_1d.py (NEW, ~327 lines)
  - **Estimated Time**: 0.25 days
  - **NOTE**: Creates empty index only. Data aggregated from transactional logs.
  - **STATUS**: COMPLETE (2026-04-11)

- [x] T069-R [REFACTOR] CREATE backend/app/db/schemas/schema_015_transactional_logs.py (FRESH INDEX - NO DATA MIGRATION)
  - **Purpose**: Create EMPTY transactional logs index
  - **Index Pattern**: `api-transactional-logs-{YYYY.MM}`
  - **Retention**: 7 days (raw logs)
  - **Files**: backend/app/db/schemas/schema_015_transactional_logs.py (NEW, ~365 lines)
  - **Estimated Time**: 0.5 days
  - **NOTE**: Creates empty index only. Data collected from gateways.
  - **STATUS**: COMPLETE (2026-04-11)

**Checkpoint**: After this section, database indices support new model structures.

---

### 0.8: Agent Layer Updates (Week 6: 4 days)

**Purpose**: Update AI agents to work with new model structures
**Status**: COMPLETE ✅
**Complexity**: MEDIUM - Update prompts and data access patterns
**Files to Update**: 4 agent files

- [x] T070-R [REFACTOR] Update backend/app/agents/prediction_agent.py for time-bucketed metrics
  - **Changes**:
    - Update LLM prompts to reference new field names
    - Update metric queries to use time-bucketed indices
    - Update contributing factor analysis for new metric structure
  - **Files**: backend/app/agents/prediction_agent.py (~300 lines affected)
  - **Estimated Time**: 1 day

- [x] T071-R [REFACTOR] Update backend/app/agents/security_agent.py to analyze policy_actions
  - **Changes**:
    - Update LLM prompts to analyze `policy_actions` array
    - Update vulnerability detection logic for vendor-neutral policy types
    - Update remediation recommendations for `PolicyAction` structure
  - **Files**: backend/app/agents/security_agent.py (~250 lines affected)
  - **Estimated Time**: 1 day

- [x] T072-R [REFACTOR] Update backend/app/agents/compliance_agent.py to analyze policy_actions
  - **Changes**:
    - Update LLM prompts for compliance analysis
    - Update policy checking logic for `policy_actions`
    - Update audit report generation for new structure
  - **Files**: backend/app/agents/compliance_agent.py (~300 lines affected)
  - **Estimated Time**: 1 day

- [x] T073-R [REFACTOR] Update backend/app/agents/optimization_agent.py for time-bucketed metrics
  - **Changes**:
    - Update LLM prompts for optimization recommendations
    - Update metric analysis for time buckets
    - Update cache analysis for new cache metrics
  - **Files**: backend/app/agents/optimization_agent.py (~250 lines affected)
  - **Estimated Time**: 1 day

**Checkpoint**: After this section, AI agents work with new model structures.

---

### 0.4: Service Layer Complete Rewrite (Week 2-3: 10 days) ✅ COMPLETED

- [X] T013-R [P] [REFACTOR] Update imports in backend/app/services/discovery_service.py
- [X] T014-R [P] [REFACTOR] Update imports in backend/app/services/metrics_service.py
- [X] T015-R [P] [REFACTOR] Update imports in backend/app/services/prediction_service.py
- [X] T016-R [P] [REFACTOR] Update imports in backend/app/services/security_service.py
- [X] T017-R [P] [REFACTOR] Update imports in backend/app/services/compliance_service.py
- [X] T018-R [P] [REFACTOR] Update imports in backend/app/services/optimization_service.py
- [X] T019-R [P] [REFACTOR] Update imports in backend/app/services/rate_limit_service.py
- [X] T020-R [P] [REFACTOR] Update imports in backend/app/services/query_service.py
- [X] T021-R [P] [REFACTOR] Update imports in backend/app/agents/prediction_agent.py
- [X] T022-R [P] [REFACTOR] Update imports in backend/app/agents/security_agent.py
- [X] T023-R [P] [REFACTOR] Update imports in backend/app/agents/compliance_agent.py
- [X] T024-R [P] [REFACTOR] Update imports in backend/app/agents/optimization_agent.py
- [X] T025-R [P] [REFACTOR] Update imports in backend/app/adapters/base.py
- [X] T026-R [P] [REFACTOR] Update imports in backend/app/adapters/kong_gateway.py
- [X] T027-R [P] [REFACTOR] Update imports in backend/app/adapters/apigee_gateway.py
- [X] T028-R [P] [REFACTOR] Update imports in backend/app/db/repositories/api_repository.py
- [X] T029-R [P] [REFACTOR] Update imports in backend/app/db/repositories/metrics_repository.py
- [X] T030-R [P] [REFACTOR] Update imports in backend/app/api/v1/apis.py
- [X] T031-R [P] [REFACTOR] Update imports in backend/app/api/v1/metrics.py
- [X] T032-R [P] [REFACTOR] Update imports in backend/app/scheduler/discovery_jobs.py
- [X] T033-R [P] [REFACTOR] Update imports in backend/app/scheduler/metrics_jobs.py
- [X] T034-R [P] [REFACTOR] Update imports in all test files (15+ files)

### Adapter Layer Refactoring (PENDING - Next Phase)

**Note**: Adapter implementation deferred until model validation complete

**BaseGatewayAdapter Changes Required**:
- Add transformation methods for vendor-specific → vendor-neutral conversion
- Add `collect_transactional_logs()` method for analytics integration
- Update policy methods to use `PolicyAction` model instead of generic dicts
- Add `vendor_metadata` population guidance in docstrings
- Add transformation methods: `_transform_to_api()`, `_transform_to_metric()`, `_transform_to_transactional_log()`, `_transform_to_policy_action()`, `_transform_from_policy_action()`

**Adapter Implementation Tasks**:
- [X] T034-R [REFACTOR] UPDATE backend/app/adapters/base.py (BaseGatewayAdapter)
  - Add abstract transformation methods for vendor-neutral model conversion
  - Add `collect_transactional_logs()` method signature
  - Update policy methods to accept/return `PolicyAction` model
  - Add docstrings explaining `vendor_metadata` population
  - Define transformation method signatures: `_transform_to_api()`, `_transform_to_metric()`, `_transform_to_transactional_log()`
- [X] T035-R [REFACTOR] CREATE backend/app/adapters/webmethods_gateway.py (WebMethodsGatewayAdapter)
  - Implement vendor-specific data collection from webMethods API Gateway REST API
  - **API Discovery**: Implement `GET /rest/apigateway/apis` for listing APIs
  - **API Details**: Implement `GET /rest/apigateway/apis/{api_id}` for detailed API information
  - **Policy Reading**: Implement `GET /rest/apigateway/policies/{policy_id}` for policy configuration
  - **Policy Actions**: Implement `GET /rest/apigateway/policyActions/{policyaction_id}` for policy action details
  - **Policy Creation**: Implement `POST /rest/apigateway/policyActions` for creating new policy actions
  - **Policy Update**: Implement `PUT /rest/apigateway/policies/{policy_id}` for updating policies
  - **Transactional Logs**: Implement OpenSearch query with filter `eventType: "Transactional"` for analytics
  - Implement transformation from webMethods API response to vendor-neutral `API` model
    - Map `apiDefinition` → `api_definition` (OpenAPI structure)
    - Extract policy IDs from `policies` array → transform to `policy_actions` with vendor-neutral types
    - Map `nativeEndpoint` → backend service endpoints
    - Store WebMethods-specific fields (`maturityState`, `owner`, `deployments`, `gatewayEndPointList`) in `vendor_metadata`
    - Populate `intelligence_metadata` with discovery information
  - Implement transformation from webMethods Policy/PolicyAction to vendor-neutral `PolicyAction`
    - Map `templateKey` to vendor-neutral policy type
    - Store WebMethods `parameters` array in `vendor_config`
    - Handle policy stage mapping (transport, requestPayloadProcessing, IAM, LMT, routing, responseProcessing)
  - Implement transformation from webMethods TransactionalLog to vendor-neutral `TransactionalLog`
    - Map `providerTime` → `backend_time_ms` (vendor-neutral naming)
    - Map `applicationId` → `client_id` (vendor-neutral naming)
    - Extract timing metrics (`totalTime`, `gatewayTime`, `providerTime`)
    - Extract error information (`errorOrigin`, `errorMessage`)
    - Extract cache metrics (`cacheHit`)
    - Extract external call data
    - Store WebMethods-specific fields in `vendor_metadata`
  - Implement transformation to time-bucketed `Metric` model from TransactionalLog data
    - Aggregate by `gateway_id`, `api_id`, `application_id`, `operation`, `time_bucket`
    - Calculate response time metrics (avg, min, max, p50, p95, p99)
    - Calculate error rates by origin (backend, gateway, client, network)
    - Calculate cache metrics (hit/miss/bypass counts and rates)
    - Calculate timing breakdown (`gateway_time_avg`, `backend_time_avg`)
  - Implement reverse transformation from vendor-neutral `PolicyAction` to WebMethods API format
    - Map vendor-neutral policy type to `templateKey`
    - Extract `vendor_config` to WebMethods `parameters` array
    - Format for `POST /policyActions` and `PUT /policies` requests
  - Add error handling for WebMethods API failures
  - Add retry logic for transient failures
  - Add logging for all API interactions
- [ ] T036-R [REFACTOR] REMOVED FROM CURRENT SCOPE backend/app/adapters/native_gateway.py (NativeGatewayAdapter)
  - Native gateway implementation explicitly excluded
  - Vendor-neutral approach remains, but active adapter scope is webMethods-first only
  - No native-gateway refactor should be performed in this phase
- [ ] T037-R [REFACTOR] **DEFERRED** UPDATE backend/app/adapters/kong_gateway.py (KongGatewayAdapter)
  - **DEFERRED TO FUTURE PHASE**: Implement Kong Admin API data collection
  - **DEFERRED TO FUTURE PHASE**: Implement transformation to vendor-neutral models
  - **DEFERRED TO FUTURE PHASE**: Add Kong-specific `vendor_metadata` fields
- [ ] T038-R [REFACTOR] **DEFERRED** UPDATE backend/app/adapters/apigee_gateway.py (ApigeeGatewayAdapter)
  - **DEFERRED TO FUTURE PHASE**: Implement Apigee Management API data collection
  - **DEFERRED TO FUTURE PHASE**: Implement transformation to vendor-neutral models
  - **DEFERRED TO FUTURE PHASE**: Add Apigee-specific `vendor_metadata` fields
- [X] T039-R [REFACTOR] UPDATE backend/app/adapters/factory.py
  - Add webmethods_gateway adapter to factory
  - Update adapter selection logic (webMethods only for initial phase; Kong and Apigee deferred)
  - Remove native gateway from active adapter architecture for this phase
- [X] T040-R [REFACTOR] Validate active adapter transformation behavior for current implementation phase
  - Verified active webMethods-first adapter path produces vendor-neutral model transformations in implementation
  - Verified `vendor_metadata` population paths are present in active adapter transformations
  - Verified `PolicyAction` transformation is implemented bidirectionally for the active webMethods adapter
  - Deferred adapters remain out of scope for this phase; native gateway remains excluded from active architecture

### Repository Layer Updates (4 days) ✅ COMPLETED

- [X] T045-R [REFACTOR] Update backend/app/db/repositories/api_repository.py for wm_api.API structure
- [X] T046-R [REFACTOR] Add derive_security_policies() method to api_repository.py
- [X] T047-R [REFACTOR] Remove current_metrics handling from api_repository.py
- [X] T048-R [REFACTOR] Update backend/app/db/repositories/metrics_repository.py for time-bucketed metrics
- [X] T049-R [REFACTOR] Add time_bucket query methods to metrics_repository.py
- [X] T050-R [REFACTOR] Add gateway_id and application_id filtering to metrics_repository.py
- [X] T051-R [REFACTOR] Create OpenSearch schema for api-inventory index (policy_actions, api_definition)
- [X] T052-R [REFACTOR] Create OpenSearch schema for metrics-5m index
- [X] T053-R [REFACTOR] Create OpenSearch schema for metrics-1h index
- [X] T054-R [REFACTOR] Create OpenSearch schema for metrics-1d index
- [X] T055-R [REFACTOR] Test repository storage and retrieval with new structures

### Service Layer Updates (6 days) ✅ COMPLETED

- [X] T056-R [REFACTOR] Update backend/app/services/discovery_service.py to add intelligence fields to API
- [X] T057-R [REFACTOR] Remove current_metrics embedding logic from discovery_service.py
- [X] T058-R [REFACTOR] Update backend/app/services/metrics_service.py for time-bucketed collection
- [X] T059-R [REFACTOR] Add time bucket aggregation logic to metrics_service.py
- [X] T060-R [REFACTOR] Update backend/app/services/security_service.py to derive policies from policy_actions
- [X] T061-R [REFACTOR] Update backend/app/services/compliance_service.py to analyze policy_actions
- [X] T062-R [REFACTOR] Update backend/app/services/prediction_service.py to query time-bucketed metrics
- [X] T063-R [REFACTOR] Update backend/app/services/optimization_service.py to query time-bucketed metrics
- [X] T064-R [REFACTOR] Update backend/app/services/rate_limit_service.py to query time-bucketed metrics
- [X] T065-R [REFACTOR] Update backend/app/services/query_service.py for new structures
- [ ] T066-R [REFACTOR] Test all service layer changes with integration tests

### Agent Layer Updates (4 days) ✅ COMPLETED

- [X] T067-R [REFACTOR] Update backend/app/agents/prediction_agent.py for time-bucketed metrics analysis
- [X] T068-R [REFACTOR] Update backend/app/agents/security_agent.py to analyze policy_actions
- [X] T069-R [REFACTOR] Update backend/app/agents/compliance_agent.py to analyze policy_actions
- [X] T070-R [REFACTOR] Update backend/app/agents/optimization_agent.py for time-bucketed metrics
- [X] T071-R [REFACTOR] Update LLM prompts for new field names and structures
- [ ] T072-R [REFACTOR] Test all agent workflows with new models

### API Layer Updates (3 days)

- [X] T073-R [REFACTOR] Update backend/app/api/v1/apis.py to serve wm_api.API structure
- [X] T074-R [REFACTOR] Remove current_metrics from API response in apis.py
- [X] T075-R [REFACTOR] Update backend/app/api/v1/metrics.py to serve time-bucketed metrics
- [X] T076-R [REFACTOR] Add time_bucket query parameter to metrics endpoints
- [X] T077-R [REFACTOR] CREATE new endpoint GET /api/v1/apis/{id}/security-policies in apis.py
- [X] T078-R [REFACTOR] Implement security policy derivation in new endpoint
- [X] T079-R [REFACTOR] Update API documentation for new structures
- [ ] T080-R [REFACTOR] Test all REST API endpoints with new responses

### Frontend Updates (8 days)

- [X] T081-R [P] [REFACTOR] Update frontend/src/types/index.ts with new API interface
- [X] T082-R [P] [REFACTOR] Update frontend/src/types/index.ts with new Metrics interface
- [X] T083-R [P] [REFACTOR] Add PolicyAction interface to frontend/src/types/index.ts
- [X] T084-R [P] [REFACTOR] Add TimeBucket enum to frontend/src/types/index.ts
- [X] T085-R [REFACTOR] Update frontend/src/services/api.ts to fetch API and metrics separately
- [X] T086-R [REFACTOR] Update frontend/src/services/metrics.ts for time bucket queries
- [X] T087-R [P] [REFACTOR] Create PolicyActionsViewer component in frontend/src/components/apis/
- [X] T088-R [P] [REFACTOR] Create TimeBucketSelector component in frontend/src/components/metrics/
- [X] T089-R [P] [REFACTOR] Create CacheMetricsDisplay component in frontend/src/components/metrics/
- [X] T090-R [REFACTOR] Update frontend/src/pages/APIs.tsx to use new API structure
- [X] T091-R [REFACTOR] Update frontend/src/components/apis/APIDetail.tsx for policy_actions display
- [X] T092-R [REFACTOR] Update frontend/src/components/metrics/HealthChart.tsx for time-bucketed data
- [X] T093-R [REFACTOR] Remove current_metrics display from all components
- [X] T094-R [REFACTOR] Add security policies derivation UI (client-side or API call)
- [X] T095-R [REFACTOR] Test all frontend components with new data structures

### Testing & Validation (8 days)

- [ ] T096-R [REFACTOR] Update all integration tests for new models
- [ ] T097-R [REFACTOR] Update all E2E tests for new workflows
- [ ] T098-R [REFACTOR] Create transformation adapter tests (Kong, Apigee)
- [ ] T099-R [REFACTOR] Test data collection flow with webMethods direct integration
- [ ] T100-R [REFACTOR] Test data serving flow with new REST API structures
- [ ] T101-R [REFACTOR] Performance test time-bucketed metrics queries
- [ ] T102-R [REFACTOR] Test policy_actions derivation logic
- [ ] T103-R [REFACTOR] Validate all 39+ files are updated correctly
- [ ] T104-R [REFACTOR] Run full regression test suite

### Data Migration ✅ SKIPPED - FRESH DATA APPROACH

**DECISION**: Starting with fresh data instead of migrating from old indices.
**RATIONALE**: Cleaner, faster, and safer than data migration. Use mock data scripts and fresh gateway collection.

- [X] T105-R [SKIPPED] ~~Create data migration script for api-inventory index~~ (NOT NEEDED - Fresh start)
- [X] T106-R [SKIPPED] ~~Create data migration script for metrics indices~~ (NOT NEEDED - Fresh start)
- [X] T107-R [SKIPPED] ~~Test migration scripts on staging environment~~ (NOT NEEDED - Fresh start)
- [X] T108-R [SKIPPED] ~~Execute migration on production data (with backup)~~ (NOT NEEDED - Fresh start)
- [X] T109-R [SKIPPED] ~~Validate migrated data integrity~~ (NOT NEEDED - Fresh start)
- [X] T110-R [SKIPPED] ~~Create rollback scripts in case of issues~~ (NOT NEEDED - Fresh start)

**ALTERNATIVE APPROACH** (IMPLEMENTED):
- Use existing mock data generation scripts in `backend/scripts/`:
  - `generate_mock_data.py` - Generate APIs and metrics
  - `generate_mock_predictions.py` - Generate predictions
  - `generate_mock_security_data.py` - Generate security findings
  - `generate_mock_compliance.py` - Generate compliance violations
  - `generate_mock_optimizations.py` - Generate optimization recommendations
- Fresh data collection from connected gateways via adapters
- Initialize empty indices with new structures using schema files

### Documentation (4 days)

- [X] T111-R [P] [REFACTOR] Update docs/architecture.md for webMethods-first design
- [X] T112-R [P] [REFACTOR] Update docs/api-reference.md with new endpoints and structures
- [ ] T113-R [P] [REFACTOR] Create fresh installation guide in docs/fresh-installation-webmethods-first.md
- [X] T114-R [P] [REFACTOR] Update README.md with webMethods-first architecture
- [ ] T115-R [P] [REFACTOR] Update all architecture diagrams
- [ ] T116-R [P] [REFACTOR] Create training materials for team

**NOTE**: No data migration guide needed - using fresh data approach with mock data scripts and fresh gateway collection.

### Final Validation & Deployment (PENDING)

- [ ] T117-R [REFACTOR] Final code review of all changes
- [ ] T118-R [REFACTOR] Security review of new architecture
- [ ] T119-R [REFACTOR] Performance benchmarking
- [ ] T120-R [REFACTOR] Stakeholder demo and approval
- [ ] T121-R [REFACTOR] Merge changes to main
- [ ] T122-R [REFACTOR] Deploy to production with monitoring

**Checkpoint**: Phase 0 models complete - Vendor-neutral data models implemented. Adapter and service layer updates pending.

---

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md (backend/, frontend/, mcp-servers/, demo-gateway/, tests/, config/, k8s/, docs/)
- [X] T002 Initialize Python backend project with requirements.txt (FastAPI, LangChain, LangGraph, FastMCP, LiteLLM, OpenSearch client, APScheduler, pytest)
- [X] T003 [P] Initialize React frontend project with package.json (React 18, Vite, React Router, TanStack Query, Recharts, Tailwind CSS, TypeScript)
- [X] T004 [P] Initialize Java Demo Gateway project with pom.xml (Spring Boot 3.2, OpenSearch Java client, Micrometer)
- [X] T005 [P] Create Docker Compose configuration in docker-compose.yml for local development
- [X] T006 [P] Create environment configuration template in .env.example
- [X] T007 [P] Setup linting and formatting tools (Black, isort, flake8 for Python; ESLint, Prettier for TypeScript)
- [X] T008 [P] Create README.md with project overview and setup instructions
- [X] T009 [P] Initialize Git repository with .gitignore for Python, Node, Java, and IDE files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### OpenSearch Setup

- [X] T010 Create OpenSearch initialization script in backend/scripts/init_opensearch.py
- [X] T011 Define OpenSearch index templates for api-inventory in backend/app/db/migrations/001_api_inventory.py
- [X] T012 [P] Define OpenSearch index templates for api-metrics-* in backend/app/db/migrations/002_api_metrics.py
- [X] T013 [P] Define OpenSearch index templates for api-predictions in backend/app/db/migrations/003_predictions.py
- [X] T014 [P] Define OpenSearch index templates for security-findings in backend/app/db/migrations/004_security.py
- [X] T015 [P] Define OpenSearch index templates for optimization-recommendations in backend/app/db/migrations/005_optimization.py
- [X] T016 [P] Define OpenSearch index templates for rate-limit-policies in backend/app/db/migrations/006_rate_limits.py
- [X] T017 [P] Define OpenSearch index templates for query-history in backend/app/db/migrations/007_queries.py

### Backend Core Infrastructure

- [X] T018 Create OpenSearch client wrapper in backend/app/db/client.py with connection pooling and error handling
- [X] T019 Create base repository class in backend/app/db/repositories/base.py with CRUD operations
- [X] T020 Create configuration management in backend/app/config.py using Pydantic Settings
- [X] T021 [P] Setup FastAPI application structure in backend/app/main.py with CORS, error handlers, and health endpoint
- [X] T022 [P] Create dependency injection setup in backend/app/api/deps.py for OpenSearch client and services
- [X] T023 [P] Implement error handling middleware in backend/app/middleware/error_handler.py
- [X] T024 [P] Setup logging configuration in backend/app/utils/logging.py with structured logging
- [X] T025 [P] Create APScheduler setup in backend/app/scheduler/__init__.py for background jobs

### Pydantic Models (Data Layer)

- [X] T026 [P] Create Gateway model in backend/app/models/gateway.py per data-model.md
- [X] T027 [P] Create API model in backend/app/models/base/api.py per data-model.md (vendor-neutral)
- [X] T028 [P] Create Metric model in backend/app/models/base/metric.py per data-model.md (vendor-neutral)
- [X] T029 [P] Create Prediction model in backend/app/models/prediction.py per data-model.md
- [X] T030 [P] Create Vulnerability model in backend/app/models/vulnerability.py per data-model.md
- [X] T031 [P] Create OptimizationRecommendation model in backend/app/models/recommendation.py per data-model.md
- [X] T032 [P] Create RateLimitPolicy model in backend/app/models/rate_limit.py per data-model.md
- [X] T033 [P] Create Query model in backend/app/models/query.py per data-model.md

### Gateway Adapter Pattern (Strategy + Adapter)

- [X] T034 Create base Gateway strategy interface in backend/app/adapters/base.py with abstract methods
- [X] T035 [P] Implement Native Gateway adapter in backend/app/adapters/native_gateway.py
- [X] T036 [P] Create Gateway adapter factory in backend/app/adapters/factory.py for strategy selection
- [X] T037 [P] Add Kong Gateway adapter stub in backend/app/adapters/kong_gateway.py (placeholder for future)
- [X] T038 [P] Add Apigee Gateway adapter stub in backend/app/adapters/apigee_gateway.py (placeholder for future)

### LLM Integration

- [X] T039 Setup LiteLLM configuration in backend/app/services/llm_service.py with provider fallback chain
- [X] T040 Create LLM testing script in backend/scripts/test_llm.py for validating provider connections

### MCP Server Foundation

- [X] T041 Create base MCP server class in mcp-servers/common/mcp_base.py using FastMCP
- [X] T042 [P] Create shared OpenSearch client for MCP servers in mcp-servers/common/opensearch.py
- [X] T043 [P] Setup MCP server health endpoint template in mcp-servers/common/health.py

### Demo Gateway Foundation

- [X] T044 Create Spring Boot application entry point in demo-gateway/src/main/java/com/example/gateway/GatewayApplication.java
- [X] T045 [P] Configure OpenSearch connection in demo-gateway/src/main/resources/application.yml
- [X] T046 [P] Create base API model in demo-gateway/src/main/java/com/example/gateway/model/API.java
- [X] T047 [P] Create base Policy model in demo-gateway/src/main/java/com/example/gateway/model/Policy.java
- [X] T048 [P] Setup OpenSearch repository in demo-gateway/src/main/java/com/example/gateway/repository/APIRepository.java

### Frontend Foundation

- [X] T049 Setup React Router configuration in frontend/src/App.tsx with route definitions
- [X] T050 [P] Create API client service in frontend/src/services/api.ts with Axios/Fetch wrapper
- [X] T051 [P] Setup TanStack Query configuration in frontend/src/main.tsx
- [X] T052 [P] Create common UI components in frontend/src/components/common/ (Button, Card, Table, Loading, Error)
- [X] T053 [P] Setup Tailwind CSS configuration in frontend/tailwind.config.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Discover and Monitor All APIs (Priority: P1) 🎯 MVP

**Goal**: Automatically discover all APIs (including shadow APIs) and continuously monitor their health

**Independent Test**: Connect to Demo Gateway, observe automatic discovery of APIs, view real-time health metrics on dashboard

### Backend - Discovery Service

- [X] T054 [P] [US1] Create API repository in backend/app/db/repositories/api_repository.py with CRUD and search operations
- [X] T055 [P] [US1] Create Gateway repository in backend/app/db/repositories/gateway_repository.py with CRUD operations
- [X] T056 [P] [US1] Create Metrics repository in backend/app/db/repositories/metrics_repository.py with time-series operations
- [X] T057 [US1] Implement Discovery Service in backend/app/services/discovery_service.py with API discovery logic
- [X] T058 [US1] Implement Metrics Service in backend/app/services/metrics_service.py with metrics collection and aggregation
- [X] T059 [US1] Create discovery scheduler job in backend/app/scheduler/discovery_jobs.py (runs every 5 minutes)
- [X] T060 [US1] Create metrics collection scheduler job in backend/app/scheduler/metrics_jobs.py (runs every 1 minute)

### Backend - REST API Endpoints

- [X] T061 [P] [US1] Implement Gateway endpoints in backend/app/api/v1/gateways.py per backend-api.yaml (POST, GET, PUT, DELETE /gateways)
- [X] T062 [P] [US1] Implement API endpoints in backend/app/api/v1/apis.py per backend-api.yaml (GET /apis, GET /apis/{id})
- [X] T063 [P] [US1] Implement Metrics endpoints in backend/app/api/v1/metrics.py per backend-api.yaml (GET /apis/{id}/metrics)

### MCP - Discovery Server

- [X] T064 [US1] Create Discovery MCP server in mcp-servers/discovery_server.py with FastMCP
- [X] T065 [P] [US1] Implement discover_apis tool in mcp-servers/discovery_server.py per mcp-tools.md
- [X] T066 [P] [US1] Implement get_api_inventory tool in mcp-servers/discovery_server.py per mcp-tools.md
- [X] T067 [P] [US1] Implement search_apis tool in mcp-servers/discovery_server.py per mcp-tools.md

### MCP - Metrics Server

- [X] T068 [US1] Create Metrics MCP server in mcp-servers/metrics_server.py with FastMCP
- [X] T069 [P] [US1] Implement collect_metrics tool in mcp-servers/metrics_server.py per mcp-tools.md
- [X] T070 [P] [US1] Implement get_metrics_timeseries tool in mcp-servers/metrics_server.py per mcp-tools.md
- [X] T071 [P] [US1] Implement analyze_trends tool in mcp-servers/metrics_server.py per mcp-tools.md

### Demo Gateway - API Management

- [X] T072 [US1] Implement Gateway info endpoint in demo-gateway/src/main/java/com/example/gateway/controller/GatewayController.java (GET /gateway/info, GET /gateway/capabilities)
- [X] T073 [US1] Implement API management endpoints in demo-gateway/src/main/java/com/example/gateway/controller/APIController.java (POST, GET, PUT, DELETE /apis)
- [X] T074 [US1] Implement API service layer in demo-gateway/src/main/java/com/example/gateway/service/APIService.java
- [X] T075 [US1] Implement metrics collection in demo-gateway/src/main/java/com/example/gateway/service/MetricsService.java
- [X] T076 [US1] Implement metrics export endpoint in demo-gateway/src/main/java/com/example/gateway/controller/MetricsController.java (GET /metrics/apis, GET /metrics/apis/{id})

### Frontend - Dashboard & API Views

- [X] T077 [US1] Create Dashboard page in frontend/src/pages/Dashboard.tsx with overview widgets
- [X] T078 [US1] Create APIs page in frontend/src/pages/APIs.tsx with API list and filters
- [X] T079 [US1] Create Gateways page in frontend/src/pages/Gateways.tsx with gateway management
- [X] T080 [P] [US1] Create API list component in frontend/src/components/apis/APIList.tsx
- [X] T081 [P] [US1] Create API detail component in frontend/src/components/apis/APIDetail.tsx
- [X] T082 [P] [US1] Create health metrics chart component in frontend/src/components/metrics/HealthChart.tsx using Recharts
- [X] T083 [P] [US1] Create Gateway service client in frontend/src/services/gateway.ts
- [X] T084 [P] [US1] Create Metrics service client in frontend/src/services/metrics.ts
- [X] T085 [US1] Implement real-time metrics updates using WebSocket or SSE in frontend/src/hooks/useRealtimeMetrics.ts

### Frontend - Gateway Management UI

- [X] T086 [P] [US1] Create AddGatewayForm component in frontend/src/components/gateways/AddGatewayForm.tsx with form validation
- [X] T087 [P] [US1] Add "Add Gateway" button to Dashboard page in frontend/src/pages/Dashboard.tsx
- [X] T088 [P] [US1] Add "Add Gateway" button to Gateways page in frontend/src/pages/Gateways.tsx
- [X] T089 [US1] Implement gateway sync endpoint in backend/app/api/v1/gateways.py (POST /gateways/{id}/sync)
- [X] T090 [US1] Add gateway sync button handlers in frontend/src/pages/Gateways.tsx
- [X] T090a [P] [US1] Create GatewayCard component in frontend/src/components/gateways/GatewayCard.tsx with detailed gateway information display
- [X] T090b [US1] Integrate GatewayCard component into Gateways page detail view in frontend/src/pages/Gateways.tsx

### Integration & Validation

- [X] T091 [US1] Create integration test for discovery flow in tests/integration/test_discovery_flow.py
- [X] T092 [US1] Create integration test for metrics collection in tests/integration/test_metrics_collection.py
- [X] T093 [US1] Create traffic generator script in backend/scripts/generate_traffic.py for testing
- [X] T094 [US1] Validate User Story 1 using quickstart.md steps 1-4

**Checkpoint**: User Story 1 complete - APIs can be discovered and monitored independently

---

## Phase 4: User Story 2 - Predict and Prevent API Failures (Priority: P1)

**Goal**: Receive advance warnings of potential API failures 24-48 hours before they occur

**Architecture**: Hybrid approach combining rule-based predictions (fast, deterministic) with optional AI-enhanced analysis (deep insights, natural language explanations). AI enhancement automatically triggered based on prediction confidence (≥80% default) and system configuration.

**Contributing Factors**: 13 strongly-typed categories across Performance (7), Availability (2), Capacity (1), Dependencies (1), and Traffic (1) patterns.

**Independent Test**: Simulate degrading API conditions, verify predictions are generated 24-48 hours in advance with strongly-typed contributing factors

### Backend - Prediction Service

- [X] T095 [P] [US2] Create Prediction repository in backend/app/db/repositories/prediction_repository.py with CRUD and query operations
- [X] T096 [US2] Implement Prediction Service in backend/app/services/prediction_service.py with hybrid prediction logic (rule-based + AI-enhanced)
- [X] T097 [US2] Create Prediction Agent in backend/app/agents/prediction_agent.py using LangChain/LangGraph
- [X] T098 [US2] Implement prediction generation workflow in backend/app/agents/prediction_agent.py with contributing factors analysis
- [X] T099 [US2] Create prediction scheduler job in backend/app/scheduler/prediction_jobs.py (runs every 15 minutes)
- [X] T100 [US2] Implement prediction accuracy tracking in backend/app/services/prediction_service.py
- [X] T100a [US2] Add ContributingFactorType enum to backend/app/models/prediction.py with 13 strongly-typed categories
- [X] T100b [US2] Implement _should_use_ai_enhancement() method in backend/app/services/prediction_service.py for intelligent AI triggering
- [X] T100c [US2] Add PREDICTION_AI_ENABLED and PREDICTION_AI_THRESHOLD configuration to backend/app/config.py
- [X] T100d [US2] Update all contributing factor references to use ContributingFactorType enum across codebase

### Backend - REST API Endpoints

- [X] T101 [P] [US2] Implement Prediction endpoints in backend/app/api/v1/predictions.py per backend-api.yaml (GET /predictions, GET /predictions/{id})

### MCP - Optimization Server (Predictions)

- [X] T102 [US2] Create Optimization MCP server in mcp-servers/optimization_server.py with FastMCP
- [X] T103 [P] [US2] Implement generate_predictions tool in mcp-servers/optimization_server.py per mcp-tools.md

### Frontend - Predictions View

- [X] T104 [US2] Create Predictions page in frontend/src/pages/Predictions.tsx with prediction list and filters
- [X] T105 [P] [US2] Create prediction card component in frontend/src/components/predictions/PredictionCard.tsx
- [X] T106 [P] [US2] Create prediction timeline component in frontend/src/components/predictions/PredictionTimeline.tsx
- [X] T107 [P] [US2] Create contributing factors visualization in frontend/src/components/predictions/FactorsChart.tsx

### Test Data Generation

- [X] T107a [P] [US2] Create mock prediction data generator in backend/scripts/generate_mock_predictions.py
- [X] T107b [P] [US2] Create test fixtures for prediction scenarios in backend/tests/fixtures/prediction_fixtures.py
- [X] T107c [P] [US2] Create degrading metrics generator utility in backend/tests/utils/metrics_generator.py

### Integration & Validation

- [X] T108 [US2] Create integration test for prediction generation in tests/integration/test_prediction_generation.py
- [X] T109 [US2] Create end-to-end test for prediction workflow in tests/e2e/test_prediction_workflow.py
- [X] T110 [US2] Validate User Story 2 independently with simulated degrading conditions

**Checkpoint**: User Story 2 complete - Predictions are generated and displayed independently

---

## Phase 5: User Story 3 - Automated Security Scanning and Remediation (Priority: P2)

**Goal**: Continuous security scanning with automated remediation of common vulnerabilities (immediate threat response)

**Audience**: Security engineers, DevOps teams, Application security teams

**Independent Test**: Deploy APIs with known security issues, verify detection and automated remediation

### Backend - Security Service

- [X] T111 [P] [US3] Create Vulnerability repository in backend/app/db/repositories/vulnerability_repository.py with CRUD and query operations
- [X] T112 [US3] Implement Security Service in backend/app/services/security_service.py with vulnerability scanning logic (Enhanced with hybrid approach, multi-source analysis, REMOVED compliance detection)
- [X] T113 [US3] Create Security Agent in backend/app/agents/security_agent.py using LangChain/LangGraph (Enhanced with all security checks, REMOVED compliance methods)
- [X] T114 [US3] Implement automated remediation workflow in backend/app/agents/security_agent.py (Real Gateway adapter integration)
- [X] T115 [US3] Create security scanning scheduler job in backend/app/scheduler/security_jobs.py (runs every 1 hour)
- [X] T116 [US3] Implement remediation verification in backend/app/services/security_service.py (Real re-scanning verification)

### Backend - REST API Endpoints

- [X] T117 [P] [US3] Implement Security endpoints in backend/app/api/v1/security.py per backend-api.yaml (GET /vulnerabilities, POST /vulnerabilities/{id}/remediate)

### Backend - Gateway Adapter Enhancement

- [X] T117a [US3] Add 6 abstract security policy methods to backend/app/adapters/base.py (authentication, authorization, TLS, CORS, validation, security headers)
- [X] T117b [US3] Implement 6 security policy methods in backend/app/adapters/native_gateway.py

### Demo Gateway - Security Policies

- [X] T117c [US3] Create AuthenticationPolicy.java in demo-gateway/src/main/java/com/example/gateway/policy/
- [X] T117d [US3] Create AuthorizationPolicy.java in demo-gateway/src/main/java/com/example/gateway/policy/
- [X] T117e [US3] Create TlsPolicy.java in demo-gateway/src/main/java/com/example/gateway/policy/
- [X] T117f [US3] Create CorsPolicy.java in demo-gateway/src/main/java/com/example/gateway/policy/
- [X] T117g [US3] Create ValidationPolicy.java in demo-gateway/src/main/java/com/example/gateway/policy/
- [X] T117h [US3] Create SecurityHeadersPolicy.java in demo-gateway/src/main/java/com/example/gateway/policy/
- [X] T117i [US3] Create SecurityPolicyController.java with 6 REST endpoints in demo-gateway/src/main/java/com/example/gateway/controller/

### MCP - Security Server

- [X] T118 [US3] Create Security MCP server in mcp-servers/security_server.py with FastMCP
- [X] T119 [P] [US3] Implement scan_api_security tool in mcp-servers/security_server.py per mcp-tools.md
- [X] T120 [P] [US3] Implement remediate_vulnerability tool in mcp-servers/security_server.py per mcp-tools.md
- [X] T121 [P] [US3] Implement get_security_posture tool in mcp-servers/security_server.py per mcp-tools.md

### Frontend - Security View

- [X] T122 [US3] Create Security page in frontend/src/pages/Security.tsx with vulnerability list and security posture (REMOVE compliance violations display)
- [X] T123 [P] [US3] Create vulnerability card component in frontend/src/components/security/VulnerabilityCard.tsx (REMOVE compliance violations display)
- [X] T124 [P] [US3] Create security posture dashboard in frontend/src/components/security/SecurityDashboard.tsx (REMOVE compliance issues section)
- [X] T125 [P] [US3] Create remediation status tracker in frontend/src/components/security/RemediationTracker.tsx

### Frontend - TypeScript Types

- [X] T125b [US3] Add RemediationAction interface to frontend/src/types/index.ts
- [X] T125d [US3] Update Vulnerability interface with remediation_actions field (REMOVE compliance_violations)

### Integration & Validation

- [X] T126 [US3] Create integration test for security scanning in tests/integration/test_security_scanning.py (REMOVE compliance detection tests)
- [X] T127 [US3] Create end-to-end test for remediation workflow in tests/e2e/test_remediation_workflow.py
- [X] T128 [US3] Validate User Story 3 independently with known vulnerabilities

### Documentation

- [X] T128a [US3] Create comprehensive implementation summary in research/security_service_improvements_summary.md
- [X] T128b [US3] Create deployment guide in research/IMPLEMENTATION_COMPLETE.md

**Checkpoint**: User Story 3 complete - Security scanning and remediation work independently with hybrid approach, real Gateway integration, and immediate threat response focus

---

## Phase 6: User Story 4 - Compliance Monitoring and Audit Reporting (Priority: P2)

**Goal**: Continuous compliance monitoring with automated detection of regulatory violations and comprehensive audit reporting

**Audience**: Compliance officers, Auditors, Legal teams, Risk management

**Independent Test**: Deploy APIs with known compliance gaps, verify detection of violations, confirm comprehensive audit reports are generated

### Pydantic Models

- [X] T128c [P] [US4] Create ComplianceViolation model in backend/app/models/compliance.py per data-model.md

### Backend - Compliance Service

- [X] T128d [P] [US4] Create ComplianceViolation repository in backend/app/db/repositories/compliance_repository.py with CRUD and query operations
- [X] T128e [US4] Implement Compliance Service in backend/app/services/compliance_service.py with AI-driven compliance detection logic
- [X] T128f [US4] Create Compliance Agent in backend/app/agents/compliance_agent.py using LangChain/LangGraph (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
- [X] T128g [US4] Implement compliance scanning workflow in backend/app/agents/compliance_agent.py with multi-source analysis
- [X] T128h [US4] Create compliance scanning scheduler job in backend/app/scheduler/compliance_jobs.py (runs every 24 hours)
- [X] T128i [US4] Implement audit report generation in backend/app/services/compliance_service.py

### Backend - REST API Endpoints

- [X] T128j [P] [US4] Implement Compliance endpoints in backend/app/api/v1/compliance.py per backend-api.yaml (GET /compliance/violations, GET /compliance/reports, GET /compliance/posture)

### MCP - Compliance Server

- [X] T128k [US4] Create Compliance MCP server in mcp-servers/compliance_server.py with FastMCP
- [X] T128l [P] [US4] Implement scan_api_compliance tool in mcp-servers/compliance_server.py per mcp-tools.md
- [X] T128m [P] [US4] Implement generate_audit_report tool in mcp-servers/compliance_server.py per mcp-tools.md
- [X] T128n [P] [US4] Implement get_compliance_posture tool in mcp-servers/compliance_server.py per mcp-tools.md

### Frontend - Compliance View

- [X] T128o [US4] Create Compliance page in frontend/src/pages/Compliance.tsx with violation list and compliance posture
- [X] T128p [P] [US4] Create compliance violation card component in frontend/src/components/compliance/ComplianceViolationCard.tsx
- [X] T128q [P] [US4] Create compliance posture dashboard in frontend/src/components/compliance/ComplianceDashboard.tsx
- [X] T128r [P] [US4] Create audit report generator component in frontend/src/components/compliance/AuditReportGenerator.tsx

### Frontend - TypeScript Types

- [X] T128s [P] [US4] Add ComplianceStandard enum to frontend/src/types/index.ts
- [X] T128t [P] [US4] Add ComplianceViolation interface to frontend/src/types/index.ts
- [X] T128u [P] [US4] Add AuditReport interface to frontend/src/types/index.ts

### Integration & Validation

- [X] T128v [US4] Create integration test for compliance scanning in tests/integration/test_compliance_scanning.py
- [X] T128w [US4] Create end-to-end test for audit report generation in tests/e2e/test_audit_workflow.py
- [X] T128x [US4] Validate User Story 4 independently with known compliance gaps

### Documentation

- [X] T128y [P] [US4] Document compliance monitoring in docs/compliance-monitoring.md
- [X] T128z [P] [US4] Document audit report generation in docs/audit-reporting.md

**Checkpoint**: User Story 4 complete - Compliance monitoring and audit reporting work independently with AI-driven analysis, comprehensive audit trails, and scheduled reporting focus

---

## Phase 7: User Story 5 - Performance Optimization & Intelligent Rate Limiting (Priority: P2)

**MERGED**: This phase combines real-time performance optimization and intelligent rate limiting into a unified feature, as both are gateway-level performance optimization techniques.

**Goal**: Real-time recommendations for optimizing API performance (caching, compression, rate limiting) with ability to apply policies directly to the Gateway

**Architecture**:
- API-centric: All optimizations generated per-API
- Gateway-level scope: Caching, compression, rate limiting only
- Hybrid approach: Rule-based + AI-enhanced (controlled by OPTIMIZATION_AI_ENABLED)
- Real-time policy application via enhanced Gateway adapter interface
- Unified UI: Single view for all optimization types

**Independent Test**: Monitor APIs under load, verify optimization recommendations are generated, apply policies to Gateway, measure improvements

### Backend - Unified Optimization Service

- [x] T129 [P] [US4] Create OptimizationRecommendation repository in backend/app/db/repositories/recommendation_repository.py
- [x] T130 [US4] Implement Optimization Service in backend/app/services/optimization_service.py with unified recommendation generation (caching, compression, rate limiting)
- [x] T131 [US4] Create Optimization Agent in backend/app/agents/optimization_agent.py using LangChain/LangGraph
- [x] T132 [US4] Implement optimization analysis workflow in backend/app/agents/optimization_agent.py
- [x] T133 [US4] Create optimization scheduler job in backend/app/scheduler/optimization_jobs.py (runs every 30 minutes)
- [x] T134 [US4] Implement recommendation validation and impact tracking in backend/app/services/optimization_service.py
- [x] T134a [US4] Add OPTIMIZATION_AI_ENABLED configuration to backend/app/config.py
- [x] T134b [US4] Add OPTIMIZATION_AI_THRESHOLD configuration to backend/app/config.py (default: 0.8)
- [x] T134c [US4] Implement _should_use_ai_enhancement() method in backend/app/services/optimization_service.py
- [x] T134d [US4] Integrate rate limiting analysis into backend/app/services/optimization_service.py (move from rate_limit_service.py)
- [x] T134e [US4] Remove cost_savings field usage from backend/app/services/optimization_service.py

### Backend - REST API Endpoints

- [x] T135 [P] [US4] Implement Optimization endpoints in backend/app/api/v1/optimization.py per backend-api.yaml (GET /recommendations)
- [x] T135a [P] [US4] Add POST /api/v1/recommendations/{id}/apply endpoint for applying policies to Gateway
- [x] T135b [P] [US4] Update GET /recommendations to include rate limiting recommendations

### MCP - Unified Optimization Server

- [x] T136 [P] [US4] Implement generate_optimization_recommendations tool in mcp-servers/optimization_server.py per mcp-tools.md
- [X] T136a [P] [US4] Implement manage_rate_limit tool in mcp-servers/optimization_server.py (already exists)
- [X] T136b [P] [US4] Implement analyze_rate_limit_effectiveness tool in mcp-servers/optimization_server.py (already exists)

### Frontend - Unified Optimization View

- [x] T137 [US4] Create Optimization page in frontend/src/pages/Optimization.tsx with unified recommendations list
- [x] T137a [US4] Remove tab navigation from frontend/src/pages/Optimization.tsx (merge rate limiting into recommendations)
- [x] T137b [US4] Update recommendation type filter to include rate_limiting option
- [x] T137c [US4] Add "Apply to Gateway" button for all recommendation types
- [x] T137d [US4] Remove cost savings display from frontend/src/pages/Optimization.tsx
- [x] T138 [P] [US4] Create recommendation card component in frontend/src/components/optimization/RecommendationCard.tsx
- [x] T138a [P] [US4] Update RecommendationCard to handle rate limiting recommendations
- [x] T138b [P] [US4] Add policy application UI to RecommendationCard
- [x] T139 [P] [US4] Create impact estimation chart in frontend/src/components/optimization/ImpactChart.tsx
- [x] T140 [P] [US4] Create implementation tracker in frontend/src/components/optimization/ImplementationTracker.tsx
- [x] T140a [P] [US4] Keep RateLimitPolicy component for detailed view in frontend/src/components/optimization/RateLimitPolicy.tsx
- [x] T140b [P] [US4] Keep RateLimitChart component for effectiveness visualization in frontend/src/components/optimization/RateLimitChart.tsx

### Test Data & Fixtures

- [x] T140a [P] [US4] Create optimization test fixtures in backend/tests/fixtures/optimization_fixtures.py with sample recommendations
- [x] T140b [US4] Create mock optimization data generator in backend/scripts/generate_mock_optimizations.py for integration testing

### Integration & Validation

- [x] T141 [US4] Create integration test for unified optimization recommendations in tests/integration/test_optimization.py
- [x] T141a [US4] Add test cases for rate limiting recommendations in tests/integration/test_optimization.py
- [x] T141b [US4] Add test cases for policy application in tests/integration/test_optimization.py
- [x] T142 [US4] Validate User Story 4 independently with various load patterns and traffic simulation

### Gateway Adapter Enhancement (CRITICAL)

- [x] T143 [US4] Add apply_caching_policy() abstract method to backend/app/adapters/base.py
- [x] T144 [US4] Add apply_compression_policy() abstract method to backend/app/adapters/base.py
- [x] T145 [US4] Add remove_caching_policy() abstract method to backend/app/adapters/base.py
- [x] T146 [US4] Add remove_compression_policy() abstract method to backend/app/adapters/base.py
- [x] T147 [US4] Implement apply_caching_policy() in backend/app/adapters/native_gateway.py
- [x] T148 [US4] Implement apply_compression_policy() in backend/app/adapters/native_gateway.py
- [x] T149 [US4] Implement remove_caching_policy() in backend/app/adapters/native_gateway.py
- [x] T150 [US4] Implement remove_compression_policy() in backend/app/adapters/native_gateway.py
- [x] T151 [US4] Add caching policy endpoint to demo-gateway/src/main/java/com/example/gateway/controller/PolicyController.java
- [x] T152 [US4] Add compression policy endpoint to demo-gateway/src/main/java/com/example/gateway/controller/PolicyController.java
- [x] T153 [US4] Implement caching policy engine in demo-gateway/src/main/java/com/example/gateway/policy/CachingPolicy.java
- [x] T154 [US4] Implement compression policy engine in demo-gateway/src/main/java/com/example/gateway/policy/CompressionPolicy.java

**Checkpoint**: User Story 5 complete - Unified performance optimization with policy application works independently

**Note**: Previous Phase 7 (Intelligent Rate Limiting) has been MERGED into this phase. All rate limiting functionality is now part of the unified performance optimization feature.

---

## Phase 8: User Story 6 - Natural Language Query Interface (Priority: P3)

**Note**: Renumbered due to separation of Security and Compliance into distinct phases.

**Goal**: Query API intelligence using natural language questions

**Independent Test**: Ask various natural language questions, verify accurate contextual answers

### Backend - Query Service

- [X] T157 [P] [US5] Create Query repository in backend/app/db/repositories/query_repository.py
- [X] T158 [US5] Implement Query Service in backend/app/services/query_service.py with NLP processing
- [X] T159 [US5] Create Query Agent in backend/app/agents/query_agent.py using LangChain/LangGraph
- [X] T160 [US5] Implement query understanding workflow in backend/app/agents/query_agent.py with intent detection
- [X] T161 [US5] Implement OpenSearch query DSL generation in backend/app/services/query_service.py
- [X] T162 [US5] Implement response generation with LLM in backend/app/services/query_service.py

### Backend - REST API Endpoints

- [X] T163 [P] [US5] Implement Query endpoint in backend/app/api/v1/query.py per backend-api.yaml (POST /query)

### Frontend - Query Interface

- [X] T164 [US5] Create Query page in frontend/src/pages/Query.tsx with chat-like interface
- [X] T165 [P] [US5] Create query input component in frontend/src/components/query/QueryInput.tsx
- [X] T166 [P] [US5] Create query response component in frontend/src/components/query/QueryResponse.tsx
- [X] T167 [P] [US5] Create query history component in frontend/src/components/query/QueryHistory.tsx
- [X] T168 [P] [US5] Implement conversation context management in frontend/src/hooks/useQuerySession.ts

### Integration & Validation

- [X] T169 [US5] Create integration test for query processing in tests/integration/test_query_processing.py
- [X] T170 [US5] Create end-to-end test for complete query workflow in tests/e2e/test_query_workflow.py
- [X] T171 [US5] Validate User Story 5 independently with various query types

**Checkpoint**: User Story 6 complete - All user stories complete - Full system functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Documentation

- [X] T172 [P] Create architecture documentation in docs/architecture.md
- [X] T173 [P] Create API reference documentation in docs/api-reference.md
- [X] T174 [P] Create deployment guide in docs/deployment.md
- [X] T175 [P] Create contributing guidelines in docs/contributing.md
- [X] T176 [P] Update README.md with comprehensive project information

### Security & Compliance

- [X] T177 [P] Implement TLS 1.3 configuration for all services
- [X] T178 [P] Configure FIPS 140-3 compliant cryptography in backend/app/utils/crypto.py
- [X] T179 [P] Setup encryption at rest for OpenSearch
- [X] T180 [P] Implement audit logging for all operations in backend/app/middleware/audit.py

### Monitoring & Observability

- [ ] T181 [P] Setup Prometheus exporters for all services
- [ ] T182 [P] Create Grafana dashboards in k8s/monitoring/dashboards/
- [ ] T183 [P] Implement OpenTelemetry tracing in backend/app/middleware/tracing.py
- [ ] T184 [P] Configure log aggregation to OpenSearch

### Deployment

- [ ] T185 [P] Create Kubernetes namespace manifest in k8s/namespace.yaml
- [ ] T186 [P] Create OpenSearch Kubernetes manifests in k8s/opensearch/
- [ ] T187 [P] Create Backend Kubernetes manifests in k8s/backend/
- [ ] T188 [P] Create Frontend Kubernetes manifests in k8s/frontend/
- [ ] T189 [P] Create MCP servers Kubernetes manifests in k8s/mcp-servers/
- [ ] T190 [P] Create Demo Gateway Kubernetes manifests in k8s/demo-gateway/
- [ ] T191 [P] Create production Docker Compose file in docker-compose.prod.yml

### Testing & Validation

- [ ] T192 [P] Create integration test for Gateway integration in tests/integration/test_gateway_integration.py
- [ ] T193 [P] Create end-to-end test fixtures in tests/e2e/fixtures/
- [ ] T194 [P] Run complete quickstart.md validation
- [ ] T195 [P] Perform load testing with 1000+ APIs
- [ ] T196 [P] Validate 90-day data retention policy

### Code Quality

- [X] T197 [P] Code cleanup and refactoring across all components
- [X] T198 [P] Performance optimization for query latency (<5s target)
- [X] T199 [P] Security hardening review
- [X] T200 [P] Update AGENTS.md with final technology stack

---

## Phase 10: AI-Enhanced Analysis (LLM Integration) 🤖

**Goal**: Enable LLM-powered intelligent analysis for predictions and optimizations

**Independent Test**: Generate AI-enhanced predictions and optimizations, verify LLM explanations and insights

### Dependencies & Configuration

- [X] T201 [P] [AI] Add LangGraph dependency to backend/requirements.txt (langgraph>=0.0.20)
- [X] T202 [P] [AI] Add LangChain dependencies to backend/requirements.txt (langchain>=0.1.0, langchain-openai>=0.0.5, langchain-anthropic>=0.1.0)
- [X] T203 [P] [AI] Update .env.example with LLM configuration (LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE)
- [X] T204 [AI] Update backend/app/config.py to include LLM settings with Pydantic validation

### LLM Service Enhancement

- [X] T205 [AI] Enhance backend/app/services/llm_service.py with async completion methods
- [X] T206 [P] [AI] Add streaming support to backend/app/services/llm_service.py
- [X] T207 [P] [AI] Implement token usage tracking in backend/app/services/llm_service.py
- [X] T208 [P] [AI] Add error handling and retry logic with exponential backoff in backend/app/services/llm_service.py
- [X] T209 [P] [AI] Create LLM testing script in backend/scripts/test_llm_agents.py for agent validation

### PredictionAgent Integration

- [X] T210 [AI] Update backend/app/agents/prediction_agent.py to fix LangGraph workflow initialization
- [X] T211 [AI] Integrate PredictionAgent into backend/app/services/prediction_service.py with use_ai_enhancement parameter
- [X] T212 [AI] Add fallback logic to backend/app/services/prediction_service.py (use rule-based if LLM fails)
- [ ] T213 [P] [AI] Create mock LLM responses for testing in backend/tests/fixtures/llm_fixtures.py
- [ ] T214 [AI] Add integration test for AI-enhanced predictions in backend/tests/integration/test_ai_predictions.py

### OptimizationAgent Integration

- [X] T215 [AI] Update backend/app/agents/optimization_agent.py to fix LangGraph workflow initialization
- [X] T216 [AI] Integrate OptimizationAgent into backend/app/services/optimization_service.py with use_ai_enhancement parameter
- [X] T217 [AI] Add fallback logic to backend/app/services/optimization_service.py (use rule-based if LLM fails)
- [ ] T218 [AI] Add integration test for AI-enhanced optimizations in backend/tests/integration/test_ai_optimizations.py

### API Endpoints for AI Features

- [X] T219 [P] [AI] Add POST /api/v1/predictions/ai-enhanced endpoint in backend/app/api/v1/predictions.py
- [X] T220 [P] [AI] Add GET /api/v1/predictions/{id}/explanation endpoint in backend/app/api/v1/predictions.py
- [X] T221 [P] [AI] Add query parameter ?use_ai=true to existing prediction endpoints in backend/app/api/v1/predictions.py
- [X] T222 [P] [AI] Add POST /api/v1/optimization/ai-enhanced endpoint in backend/app/api/v1/optimization.py
- [X] T223 [P] [AI] Add GET /api/v1/optimization/{id}/insights endpoint in backend/app/api/v1/optimization.py
- [X] T224 [P] [AI] Add query parameter ?use_ai=true to existing optimization endpoints in backend/app/api/v1/optimization.py

### Frontend AI Features

- [X] T225 [P] [AI] Add AI toggle switch to frontend/src/pages/Predictions.tsx
- [X] T226 [P] [AI] Display LLM explanations in frontend/src/components/predictions/PredictionCard.tsx
- [X] T227 [P] [AI] Add AI toggle switch to frontend/src/pages/Optimization.tsx
- [X] T228 [P] [AI] Display AI insights in frontend/src/components/optimization/RecommendationCard.tsx
- [X] T229 [P] [AI] Add loading states for AI processing in frontend components

### Testing & Validation

- [ ] T230 [AI] Create end-to-end test for AI prediction workflow in backend/tests/e2e/test_ai_prediction_workflow.py
- [ ] T231 [AI] Create end-to-end test for AI optimization workflow in backend/tests/e2e/test_ai_optimization_workflow.py
- [ ] T232 [AI] Test fallback behavior when LLM is unavailable in backend/tests/integration/test_ai_fallback.py
- [ ] T233 [AI] Validate token usage tracking and cost monitoring
- [ ] T234 [AI] Performance test: Compare AI-enhanced vs rule-based response times

### Documentation

- [X] T235 [P] [AI] Document AI features in README.md with setup instructions
- [X] T236 [P] [AI] Create AI configuration guide in docs/ai-setup.md
- [X] T237 [P] [AI] Document cost considerations and token usage in docs/ai-costs.md
- [ ] T238 [P] [AI] Add API examples for AI-enhanced endpoints in docs/api-reference.md


---

## Phase 11: Query Service Agent Integration 🔗

**Goal**: Enhance QueryService with PredictionAgent and OptimizationAgent for AI-driven query responses

**Independent Test**: Execute natural language queries about predictions and performance, verify AI agent insights are included in responses

### Service Enhancement

- [X] T239 [P] [QS] Add optional prediction_agent parameter to QueryService.__init__ in backend/app/services/query_service.py
- [X] T240 [P] [QS] Add optional optimization_agent parameter to QueryService.__init__ in backend/app/services/query_service.py
- [X] T241 [QS] Create _enhance_with_prediction_agent() method in backend/app/services/query_service.py
- [X] T242 [QS] Create _enhance_with_optimization_agent() method in backend/app/services/query_service.py
- [X] T243 [QS] Update _execute_query() to call agent enhancement for PREDICTION query type in backend/app/services/query_service.py
- [X] T244 [QS] Update _execute_query() to call agent enhancement for PERFORMANCE query type in backend/app/services/query_service.py

### Response Generation Enhancement

- [X] T245 [QS] Update _generate_response() to detect agent insights in results in backend/app/services/query_service.py
- [X] T246 [QS] Create enhanced system prompt for responses with agent insights in backend/app/services/query_service.py
- [X] T247 [P] [QS] Update _generate_follow_ups() to suggest agent-specific follow-up queries in backend/app/services/query_service.py

### API Integration

- [X] T248 [QS] Update query endpoint to initialize agents when available in backend/app/api/v1/query.py
- [X] T249 [P] [QS] Add use_ai_agents query parameter to query endpoint in backend/app/api/v1/query.py
- [X] T250 [P] [QS] Add agent_timeout configuration parameter in backend/app/config.py

### Performance Optimization

- [X] T251 [P] [QS] Implement result caching for agent analysis (5-minute TTL) in backend/app/services/query_service.py
- [X] T252 [P] [QS] Add parallel agent execution for multiple APIs in backend/app/services/query_service.py
- [X] T253 [P] [QS] Limit agent enhancement to top 3 results to avoid latency in backend/app/services/query_service.py
- [X] T254 [P] [QS] Add token usage tracking for agent calls in backend/app/services/query_service.py

### Error Handling & Fallback

- [X] T255 [QS] Add graceful fallback when agents fail in backend/app/services/query_service.py
- [X] T256 [P] [QS] Add agent availability check before enhancement in backend/app/services/query_service.py
- [X] T257 [P] [QS] Log agent failures without breaking query execution in backend/app/services/query_service.py

### Testing & Validation

- [X] T258 [QS] Create integration test for prediction query with agent enhancement in backend/tests/integration/test_query_agent_integration.py
- [X] T259 [QS] Create integration test for performance query with agent enhancement in backend/tests/integration/test_query_agent_integration.py
- [X] T260 [QS] Test agent fallback behavior when agents unavailable in backend/tests/integration/test_query_agent_integration.py
- [X] T261 [P] [QS] Test parallel agent execution performance in backend/tests/integration/test_query_agent_integration.py
- [X] T262 [P] [QS] Validate token usage tracking for agent calls in backend/tests/integration/test_query_agent_integration.py

### Documentation

- [X] T263 [P] [QS] Document agent integration in docs/query-service.md
- [X] T264 [P] [QS] Add examples of AI-enhanced query responses in docs/query-service.md
- [X] T265 [P] [QS] Document configuration options (use_ai_agents, agent_timeout) in docs/query-service.md

**Checkpoint**: Phase 11 complete - QueryService provides AI-enhanced responses with agent insights and AI-enhanced analysis operational with fallback to rule-based

---

## Phase 12: User Story 7 - WebMethods Analytics Integration (Priority: P2)

**Goal**: Collect and analyze transactional event data from WebMethods API Gateway with drill-down capabilities

**Architecture**: ETL pipeline (collect → store → aggregate), multi-gateway support via gateway_id, time-series aggregation (1m/5m/1h/1d), drill-down from metrics to raw logs

**Independent Test**: Connect to WebMethods Gateway, verify log collection every 5 minutes, confirm metric aggregation, validate drill-down queries, verify multi-gateway data segregation

### Pydantic Models (Data Layer)

- [X] T266 [P] [US7] Create TransactionalLog model in backend/app/models/wm_analytics.py with all 61 fields per architecture doc
- [X] T267 [P] [US7] Create ExternalCall nested model in backend/app/models/wm_analytics.py for external service tracking
- [X] T268 [P] [US7] Create Metrics model in backend/app/models/wm_analytics.py with aggregation dimensions and calculated metrics
- [X] T269 [P] [US7] Add EventType, EventStatus, ErrorOrigin, CacheStatus, ExternalCallType enums to backend/app/models/wm_analytics.py
- [X] T270 [P] [US7] Update backend/app/models/__init__.py to export TransactionalLog, Metrics, ExternalCall, and enums

### OpenSearch Indices

- [X] T271 [P] [US7] Define transactional-logs-* index template in backend/app/db/migrations/010_wm_transactional_logs.py (daily indices, 90-day retention)
- [X] T272 [P] [US7] Define metrics-1m index template in backend/app/db/migrations/011_wm_metrics_1m.py (24-hour retention)
- [X] T273 [P] [US7] Define metrics-5m index template in backend/app/db/migrations/012_wm_metrics_5m.py (7-day retention)
- [X] T274 [P] [US7] Define metrics-1h index template in backend/app/db/migrations/013_wm_metrics_1h.py (30-day retention)
- [X] T275 [P] [US7] Define metrics-1d index template in backend/app/db/migrations/014_wm_metrics_1d.py (90-day retention)

### Backend - Repositories

- [X] T276 [P] [US7] Create TransactionalLogRepository in backend/app/db/repositories/transactional_log_repository.py with CRUD and query operations
- [X] T277 [P] [US7] Create MetricsRepository in backend/app/db/repositories/metrics_repository.py with time-bucket operations
- [X] T278 [US7] Implement bulk insert for transactional logs in TransactionalLogRepository (performance optimization)
- [X] T279 [US7] Implement drill-down query method in MetricsRepository (get_raw_logs_for_metric)

### Backend - WebMethods Analytics Service

- [X] T280 [US7] Create WMAnalyticsService in backend/app/services/wm_analytics_service.py with collection and aggregation logic
- [X] T281 [US7] Implement collect_transactional_logs() method in WMAnalyticsService (fetch from Gateway, validate, store)
- [X] T282 [US7] Implement aggregate_to_1m_bucket() method in WMAnalyticsService (calculate metrics from raw logs)
- [X] T283 [US7] Implement aggregate_to_5m_bucket() method in WMAnalyticsService (aggregate from 1m buckets)
- [X] T284 [US7] Implement aggregate_to_1h_bucket() method in WMAnalyticsService (aggregate from 5m buckets)
- [X] T285 [US7] Implement aggregate_to_1d_bucket() method in WMAnalyticsService (aggregate from 1h buckets)
- [X] T286 [US7] Implement get_metrics() method in WMAnalyticsService (query with gateway_id, api_id, time_range filters)
- [X] T287 [US7] Implement drill_down_to_logs() method in WMAnalyticsService (trace from metric to raw logs)
- [X] T288 [P] [US7] Add data validation logic in WMAnalyticsService (handle missing/incomplete fields)
- [X] T289 [P] [US7] Add error handling for Gateway connection failures in WMAnalyticsService

### Backend - Scheduler Jobs

- [X] T290 [US7] Create WMAnalyticsJobs in backend/app/scheduler/wm_analytics_jobs.py
- [X] T291 [US7] Implement collect_logs_job() in WMAnalyticsJobs (runs every 5 minutes)
- [X] T292 [US7] Implement aggregate_1m_job() in WMAnalyticsJobs (runs every 1 minute)
- [X] T293 [US7] Implement aggregate_5m_job() in WMAnalyticsJobs (runs every 5 minutes)
- [X] T294 [US7] Implement aggregate_1h_job() in WMAnalyticsJobs (runs every hour)
- [X] T295 [US7] Implement aggregate_1d_job() in WMAnalyticsJobs (runs daily at midnight)
- [X] T296 [US7] Implement cleanup_expired_data_job() in WMAnalyticsJobs (runs daily, enforces retention policies)

### Backend - Gateway Adapter Enhancement

- [X] T297 [US7] Add get_transactional_logs() abstract method to backend/app/adapters/base.py
- [X] T298 [US7] Implement get_transactional_logs() in backend/app/adapters/native_gateway.py (fetch from WebMethods)
- [X] T299 [P] [US7] Add pagination support to get_transactional_logs() for large result sets

### Backend - REST API Endpoints

- [X] T300 [P] [US7] Create Analytics endpoints in backend/app/api/v1/analytics.py per backend-api.yaml
- [X] T301 [P] [US7] Implement GET /api/v1/analytics/metrics endpoint (query aggregated metrics)
- [X] T302 [P] [US7] Implement GET /api/v1/analytics/metrics/{metric_id}/logs endpoint (drill-down to raw logs)
- [X] T303 [P] [US7] Implement GET /api/v1/analytics/logs endpoint (query raw transactional logs)
- [X] T304 [P] [US7] Add gateway_id, api_id, application_id, time_range query parameters to all endpoints

### Demo Gateway - Transactional Logs API

- [X] T305 [US7] Create TransactionalLogController in demo-gateway/src/main/java/com/example/gateway/controller/TransactionalLogController.java
- [X] T306 [US7] Implement GET /gateway/logs endpoint (return transactional events)
- [X] T307 [US7] Implement TransactionalLogService in demo-gateway/src/main/java/com/example/gateway/service/TransactionalLogService.java
- [X] T308 [US7] Add transactional event generation logic to demo-gateway (capture all API requests)
- [X] T309 [P] [US7] Store transactional events in OpenSearch from demo-gateway

### Frontend - Analytics Dashboard

- [X] T310 [US7] Create Analytics page in frontend/src/pages/Analytics.tsx with metrics visualization
- [X] T311 [P] [US7] Create MetricsChart component in frontend/src/components/analytics/MetricsChart.tsx (time-series visualization)
- [X] T312 [P] [US7] Create MetricsTable component in frontend/src/components/analytics/MetricsTable.tsx (tabular view with drill-down)
- [X] T313 [P] [US7] Create TransactionalLogViewer component in frontend/src/components/analytics/TransactionalLogViewer.tsx (raw log display)
- [X] T314 [P] [US7] Create GatewayFilter component in frontend/src/components/analytics/GatewayFilter.tsx (multi-gateway selection)
- [X] T315 [P] [US7] Create TimeBucketSelector component in frontend/src/components/analytics/TimeBucketSelector.tsx (1m/5m/1h/1d selection)

### Frontend - Drill-Down Functionality

- [X] T316 [US7] Implement drill-down click handler in MetricsChart component (navigate to raw logs)
- [X] T317 [US7] Implement drill-down click handler in MetricsTable component (navigate to raw logs)
- [X] T318 [P] [US7] Add breadcrumb navigation in Analytics page (metrics → logs → back)
- [X] T319 [P] [US7] Add context preservation during drill-down (maintain filters and time range)

### Frontend - Service Clients

- [X] T320 [P] [US7] Create Analytics service client in frontend/src/services/analytics.ts
- [X] T321 [P] [US7] Implement getMetrics() method in analytics service (fetch aggregated metrics)
- [X] T322 [P] [US7] Implement getLogsForMetric() method in analytics service (drill-down query)
- [X] T323 [P] [US7] Implement getTransactionalLogs() method in analytics service (raw log query)

### Frontend - TypeScript Types

- [X] T324 [P] [US7] Add TransactionalLog interface to frontend/src/types/index.ts
- [X] T325 [P] [US7] Add Metrics interface to frontend/src/types/index.ts
- [X] T326 [P] [US7] Add ExternalCall interface to frontend/src/types/index.ts
- [X] T327 [P] [US7] Add TimeBucket enum to frontend/src/types/index.ts

### Integration & Validation

- [X] T328 [US7] Create integration test for log collection in tests/integration/test_wm_log_collection.py
- [X] T329 [US7] Create integration test for metric aggregation in tests/integration/test_wm_aggregation.py
- [X] T330 [US7] Create integration test for drill-down queries in tests/integration/test_wm_drilldown.py
- [X] T331 [US7] Create integration test for multi-gateway segregation in tests/integration/test_wm_multi_gateway.py
- [X] T332 [US7] Create end-to-end test for complete analytics workflow in tests/e2e/test_wm_analytics_workflow.py
- [X] T333 [US7] Validate User Story 7 independently with WebMethods Gateway connection

### Test Data & Fixtures

- [X] T334 [P] [US7] Create mock transactional log generator in backend/scripts/generate_wm_logs.py
- [X] T335 [P] [US7] Create test fixtures for transactional logs in backend/tests/fixtures/wm_analytics_fixtures.py
- [X] T336 [P] [US7] Create test fixtures for aggregated metrics in backend/tests/fixtures/wm_analytics_fixtures.py

### Documentation

- [X] T337 [P] [US7] Document WebMethods Analytics integration in docs/webmethods-analytics.md (reference architecture doc)
- [X] T338 [P] [US7] Add API examples for analytics endpoints in docs/api-reference.md
- [X] T339 [P] [US7] Document drill-down pattern in docs/webmethods-analytics.md
- [X] T340 [P] [US7] Document multi-gateway configuration in docs/webmethods-analytics.md

**Checkpoint**: Phase 12 complete - WebMethods Analytics integration operational with ETL pipeline, time-series aggregation, and drill-down capabilities

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Depends on US1 for metrics data
- **User Story 3 (P2)**: Can start after Foundational - Depends on US1 for API inventory (Security scanning)
- **User Story 4 (P2)**: Can start after Foundational - Depends on US1 for API inventory (Compliance monitoring)
- **User Story 5 (P2)**: Can start after Foundational - Depends on US1 for metrics data (Performance optimization, includes rate limiting)
- **User Story 6 (P3)**: Can start after Foundational - Can query data from all previous stories (Natural language queries)
- **User Story 7 (P2)**: Can start after Foundational - Depends on US1 for Gateway connections (WebMethods Analytics)

### Within Each User Story

- Repositories before services
- Services before agents
- Agents before schedulers
- Backend endpoints before frontend components
- MCP tools can be developed in parallel with backend services
- Demo Gateway features can be developed in parallel with backend
- Frontend components marked [P] can be developed in parallel

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1, 3, 4 can start in parallel
- User Stories 2 and 5 can start after US1 completes (need metrics data)
- Within each story, all tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- All Polish tasks marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Discovery & Monitoring)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Complete Phase 4: User Story 2 (Predictions)
6. **STOP and VALIDATE**: Test User Story 2 independently
7. Deploy/demo MVP with core capabilities

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Basic MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Predictive MVP!)
4. Add User Story 3 → Test independently → Deploy/Demo (Security-aware)
5. Add User Story 4 → Test independently → Deploy/Demo (Compliance-ready)
6. Add User Story 5 → Test independently → Deploy/Demo (Performance-optimized with rate limiting)
7. Add User Story 6 → Test independently → Deploy/Demo (Full system with natural language!)
8. Add User Story 7 → Test independently → Deploy/Demo (WebMethods Analytics with drill-down!)
9. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Discovery & Monitoring)
   - Developer B: User Story 3 (Security Scanning)
   - Developer C: User Story 4 (Compliance Monitoring)
3. After US1 completes:
   - Developer D: User Story 2 (Predictions) - needs US1 metrics
   - Developer E: User Story 5 (Performance Optimization) - needs US1 metrics
4. After all P1/P2 stories:
   - Developer F: User Story 6 (Natural Language) - needs all data
5. Stories complete and integrate independently

---

## Task Count Summary

- **Phase 1 (Setup)**: 9 tasks
- **Phase 2 (Foundational)**: 44 tasks (CRITICAL PATH)
- **Phase 3 (US1 - Discovery & Monitoring)**: 36 tasks
- **Phase 4 (US2 - Predictions)**: 16 tasks
- **Phase 5 (US3 - Security)**: 16 tasks (compliance removed)
- **Phase 6 (US4 - Compliance)**: 23 tasks (NEW - separated from security)
- **Phase 7 (US5 - Performance Optimization)**: 42 tasks (includes rate limiting)
- **Phase 8 (US6 - Natural Language)**: 15 tasks
- **Phase 9 (Polish)**: 29 tasks
- **Phase 10 (AI-Enhanced Analysis)**: 38 tasks
- **Phase 11 (Query Service Agent Integration)**: 27 tasks
- **Phase 12 (US7 - WebMethods Analytics)**: 76 tasks (NEW - transactional data collection and drill-down with 1m bucket)

**Total**: 371 tasks (increased with WebMethods Analytics integration including 1m time bucket)

**Parallel Opportunities**: 100+ tasks marked [P] can run in parallel with other tasks

**MVP Scope** (US1 + US2): 105 tasks (Setup + Foundational + US1 + US2)

---

## Notes

- [P] tasks = different files, no dependencies within their phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are integration/e2e only per project requirements
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All file paths are relative to repository root
- Follow project structure from plan.md exactly

---

**Generated**: 2026-03-09
**Updated**: 2026-04-09 (Added WebMethods Analytics Integration)
**Total Tasks**: 371
**MVP Tasks**: 105 (Setup + Foundational + US1 + US2)
**AI-Enhanced MVP**: 143 (MVP + AI Integration)
**Full System with Analytics**: 371 tasks
**Estimated MVP Duration**: 4-6 weeks with 2-3 developers
**Estimated AI-Enhanced MVP**: 6-8 weeks with 2-3 developers
**Full System Duration**: 12-16 weeks with 3-5 developers

**Key Changes (2026-04-09)**:
- Added Phase 12 (US7) - WebMethods Analytics Integration with 76 tasks
- ETL pipeline for transactional log collection (every 5 minutes)
- Time-series aggregation into 1m/5m/1h/1d buckets with retention policies (1m: 24h, 5m: 7d, 1h: 30d, 1d: 90d)
- Drill-down pattern from aggregated metrics to raw transactional logs
- Multi-gateway support via gateway_id dimension
- Three-model architecture: API (metadata), TransactionalLog (raw events), Metrics (aggregated)
- 61-field transactional event model with timing metrics and external call tracking
- Added 1-minute time bucket for ultra real-time monitoring (24-hour retention)

**Previous Changes (2026-03-29)**:
- Merged Phase 6 (US4) and Phase 7 (US5) into unified Performance Optimization feature
- Added 14 new tasks for gateway adapter policy application methods
- Added 5 new tasks for OPTIMIZATION_AI_ENABLED configuration
- Removed cost savings tracking per requirements
- Unified frontend UI - single view for all optimization types
- Enhanced gateway adapters with caching, compression, and rate limiting policy methods