# Integration Test Updates Needed

## Overview
Integration tests need to be updated to work with the new vendor-neutral model structures. This document outlines the required changes.

## Status
- ✅ Test fixtures updated (T090-R complete)
- ⚠️ Integration tests need updates (T091-R)
- ⚠️ E2E tests need updates (T092-R)

## Required Changes

### 1. Import Path Updates
All tests need to update imports from old paths to new vendor-neutral paths:

**Old:**
```python
from backend.app.models.api import API, APIStatus
from backend.app.models.metric import Metric
```

**New:**
```python
from backend.app.models.base.api import API, APIStatus, IntelligenceMetadata, VersionInfo
from backend.app.models.base.metric import Metric, TimeBucket
from backend.app.models.base.transaction import TransactionalLog
```

### 2. Repository Initialization
Repositories no longer take opensearch_client as constructor parameter:

**Old:**
```python
api_repository = APIRepository(opensearch_client)
```

**New:**
```python
api_repository = APIRepository()
```

### 3. Gateway Model Updates
Gateway model has new required fields:

**Required Fields:**
- `vendor`: GatewayVendor enum (WEBMETHODS, KONG, APIGEE, NATIVE)
- `version`: str
- `base_url`: str (renamed from connection_url)
- `transactional_logs_url`: Optional[str]
- `connection_type`: str
- `base_url_credentials`: Optional[dict]
- `transactional_logs_credentials`: Optional[dict]
- `last_connected_at`: Optional[datetime]
- `last_error`: Optional[str]
- `configuration`: dict

**Removed Fields:**
- `type` (replaced by `vendor`)
- `api_key` (moved to `base_url_credentials`)

### 4. API Model Updates
API model now uses vendor-neutral structure:

**Required Changes:**
- Add `display_name`: str
- Add `description`: Optional[str]
- Add `version_info`: VersionInfo (replaces `version` string)
- Add `type`: APIType enum
- Add `maturity_state`: MaturityState enum
- Add `intelligence_metadata`: IntelligenceMetadata wrapper
- Remove `current_metrics` (metrics stored separately)
- Remove direct `is_shadow`, `discovery_method`, `health_score` (moved to intelligence_metadata)

**Example:**
```python
api = API(
    id=uuid4(),
    gateway_id=gateway_id,
    name="Test API",
    display_name="Test API Display",
    description="Test API description",
    base_path="/api/v1",
    version_info=VersionInfo(
        current_version="1.0.0",
        previous_version=None,
        next_version=None,
        system_version=1,
        version_history=None,
    ),
    type=APIType.REST,
    maturity_state=MaturityState.PRODUCTIVE,
    endpoints=[...],
    methods=["GET", "POST"],
    authentication_type=AuthenticationType.BEARER,
    authentication_config={"scheme": "bearer"},
    policy_actions=[],
    tags=["test"],
    intelligence_metadata=IntelligenceMetadata(
        is_shadow=False,
        discovery_method=DiscoveryMethod.GATEWAY_SYNC,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        health_score=95.0,
        risk_score=5.0,
        security_score=90.0,
        compliance_status=None,
        usage_trend=None,
        has_active_predictions=False,
    ),
    status=APIStatus.ACTIVE,
    is_active=True,
    vendor_metadata={"test": True},
    created_at=datetime.utcnow(),
    updated_at=datetime.utcnow(),
)
```

### 5. Metric Model Updates
Metrics now use time-bucketed structure:

**Required Fields:**
- `time_bucket`: TimeBucket enum (ONE_MINUTE, FIVE_MINUTES, ONE_HOUR, ONE_DAY)
- `application_id`: Optional[str]
- `operation`: Optional[str]
- `success_count`: int
- `failure_count`: int
- `response_time_avg`: float
- `response_time_min`: float
- `response_time_max`: float
- `gateway_time_avg`: float
- `backend_time_avg`: float
- `total_data_size`: int
- `avg_request_size`: float
- `avg_response_size`: float
- `vendor_metadata`: Optional[dict]

**Removed Fields:**
- `error_count` (use `failure_count`)
- `metadata` (use `vendor_metadata`)

### 6. Service Initialization
Services may have updated constructor signatures:

**Example:**
```python
discovery_service = DiscoveryService(
    gateway_repository=gateway_repository,
    adapter_factory=adapter_factory,
)
```

### 7. Enum Value Changes
Some enum values have changed:

**DiscoveryMethod:**
- `GATEWAY_API` → `GATEWAY_SYNC`

**GatewayStatus:**
- `ACTIVE` → `CONNECTED`

**AuthenticationType:**
- `JWT` → `BEARER`

## Files Requiring Updates

### Integration Tests
1. `tests/integration/test_discovery_flow.py` - API discovery workflow
2. `tests/integration/test_metrics_collection.py` - Metrics collection
3. `tests/integration/test_security_scanning.py` - Security scanning
4. `tests/integration/test_compliance_scanning.py` - Compliance monitoring
5. `backend/tests/integration/test_prediction_generation.py` - Prediction generation
6. `backend/tests/integration/test_optimization.py` - Optimization recommendations
7. `backend/tests/integration/test_rate_limiting.py` - Rate limiting
8. `backend/tests/integration/test_query_processing.py` - Query processing
9. `backend/tests/integration/test_wm_*.py` - WebMethods integration tests

### E2E Tests
1. `tests/e2e/test_audit_workflow.py` - Audit workflow
2. `tests/e2e/test_remediation_workflow.py` - Remediation workflow
3. `backend/tests/e2e/test_prediction_workflow.py` - Prediction workflow
4. `backend/tests/e2e/test_query_workflow.py` - Query workflow
5. `backend/tests/e2e/test_user_story_2_validation.py` - User story validation
6. `backend/tests/e2e/test_wm_analytics_workflow.py` - WebMethods analytics

## Recommended Approach

1. **Use New Fixtures**: Import and use the new fixtures from `backend/tests/fixtures/`:
   - `api_fixtures.py` - For API test data
   - `metric_fixtures.py` - For metric test data
   - `wm_analytics_fixtures.py` - For WebMethods data

2. **Update One Test File at a Time**: Start with simpler tests and work up to complex workflows

3. **Run Tests Incrementally**: Test each file after updating to catch issues early

4. **Reference Working Examples**: Use the fixture files as examples of correct model usage

## Next Steps

1. Update integration test files with new imports and model structures
2. Update E2E test files with new imports and model structures
3. Run test suite: `pytest tests/integration/ -v`
4. Run E2E tests: `pytest tests/e2e/ -v`
5. Fix any remaining issues
6. Update tasks.md to mark T091-R and T092-R as complete

## Notes

- The vendor-neutral refactoring is a major architectural change
- Tests may need significant rewrites, not just import updates
- Consider the test fixtures as the source of truth for correct model usage
- Some tests may need to be redesigned to work with the new separation of concerns (e.g., metrics stored separately from APIs)

---
*Generated: 2026-04-11*
*Related Tasks: T090-R (complete), T091-R (in progress), T092-R (pending)*