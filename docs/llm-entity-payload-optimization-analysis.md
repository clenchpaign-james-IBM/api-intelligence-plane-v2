# LLM Entity Payload Optimization Analysis

**Date**: 2026-04-20  
**Context**: Query Service sends entity results to LLM for natural language response generation  
**Issue**: Large entity payloads (especially APIs) can exceed LLM context limits and increase costs

## Executive Summary

The query service at [`backend/app/services/query_service.py:218-220`](backend/app/services/query_service.py:218) retrieves full entity objects from OpenSearch and sends them to LLMs for response generation. Some entities, particularly APIs, contain large nested structures that are unnecessary for LLM processing. This analysis identifies trimmable fields across all entity types to optimize LLM payload size while maintaining response quality.

## Current Flow

```python
# Line 863-961: _execute_query method
results = await self._execute_query(opensearch_query, interpreted_intent, query_type)

# Line 886-925: Full entity serialization
data = [api.model_dump(mode="json") for api in results]  # Full payload!

# Line 963-1078: _generate_response sends to LLM
results_summary = f"Found {results.count} results..."
if results.data:
    results_summary += f"\n\nSample results:\n{results.data[:3]}"  # First 3 results
```

**Problem**: `model_dump(mode="json")` serializes the entire entity with all nested structures.

---

## Entity-by-Entity Analysis

### 1. API Entity (Largest Payload)

**Model**: [`backend/app/models/base/api.py`](backend/app/models/base/api.py)

#### Fields to KEEP for LLM (Essential Context)
- `id` - Unique identifier
- `gateway_id` - Gateway reference
- `name` - API name
- `display_name` - Human-readable name
- `description` - API description
- `base_path` - URL path
- `type` - API protocol (REST, SOAP, etc.)
- `maturity_state` - Lifecycle state
- `groups` - Categories
- `tags` - Classification tags
- `methods` - HTTP methods
- `authentication_type` - Auth mechanism
- `status` - Current status
- `is_active` - Active flag
- `created_at` - Creation timestamp
- `updated_at` - Last update timestamp

#### Fields to TRIM (Large/Redundant)

**Critical Trims (Largest Impact)**:

1. **`api_definition`** (Lines 479-481)
   - Contains full OpenAPI/Swagger spec
   - Includes `openapi_spec` dict (can be 100KB+)
   - Includes `paths`, `schemas`, `security_schemes` dicts
   - **Impact**: Can reduce payload by 50-90%
   - **Keep**: Only `type`, `version`, `base_path` from definition

2. **`endpoints`** (Lines 486-487)
   - Array of endpoint objects with parameters
   - Each endpoint has `parameters` array with full schema
   - **Impact**: 10-30KB for APIs with many endpoints
   - **Keep**: Only count and sample (first 3 endpoints with simplified structure)

3. **`policy_actions`** (Lines 500-502)
   - Array of policy configurations
   - Each has nested `config` objects (RateLimitConfig, AuthenticationConfig, etc.)
   - **Impact**: 5-20KB depending on policy complexity
   - **Keep**: Only `action_type`, `enabled`, `name` (drop full `config` and `vendor_config`)

4. **`vendor_metadata`** (Lines 535-537)
   - Vendor-specific extensions
   - Can contain large nested structures
   - **Impact**: 5-50KB depending on vendor
   - **Keep**: Drop entirely or keep only top-level keys

**Moderate Trims**:

5. **`authentication_config`** (Lines 493-495)
   - May contain encrypted secrets and complex OAuth configs
   - **Keep**: Drop entirely (auth type is sufficient)

6. **`deployments`** (Lines 515-517)
   - Array of deployment info with gateway endpoints
   - **Keep**: Only count and environment names

7. **`publishing`** (Lines 512-514)
   - Portal and catalog information
   - **Keep**: Only `published_portals` count

8. **`ownership`** (Lines 507)
   - Team and contact info
   - **Keep**: Only `team` and `organization`

9. **`version_info.version_history`** (Line 314)
   - Full version history array
   - **Keep**: Only `current_version`, `system_version`

10. **`intelligence_metadata`** (Lines 522-524)
    - Keep most fields but trim:
    - `compliance_status` dict - Keep only count of compliant standards
    - `usage_trend` - Keep as-is (small)

**Estimated Reduction**: 60-85% for typical API entities

---

### 2. Vulnerability Entity

**Model**: [`backend/app/models/vulnerability.py`](backend/app/models/vulnerability.py)

#### Fields to KEEP
- `id`, `gateway_id`, `api_id`
- `vulnerability_type`, `configuration_type`
- `cve_id`, `severity`, `title`, `description`
- `affected_endpoints` (first 3 only)
- `detection_method`, `detected_at`
- `status`, `remediation_type`
- `cvss_score`
- `created_at`, `updated_at`

#### Fields to TRIM

1. **`remediation_actions`** (Lines 314-316)
   - Full action history with timestamps and metadata
   - **Keep**: Only count and latest action status

2. **`references`** (Line 324)
   - Array of URLs
   - **Keep**: Only count

3. **`metadata`** (Line 325)
   - Vendor-specific data
   - **Keep**: Drop entirely

4. **`recommended_remediation`** (Lines 328-330)
   - Large structured dict with detailed plans
   - **Keep**: Only summary fields (`recommended_priority`, `recommended_estimated_time_hours`)

5. **`recommended_verification_steps`** (Lines 334-336)
   - Array of detailed steps
   - **Keep**: Only count

**Estimated Reduction**: 40-60%

---

### 3. Prediction Entity

**Model**: [`backend/app/models/prediction.py`](backend/app/models/prediction.py)

#### Fields to KEEP
- `id`, `gateway_id`, `api_id`, `api_name`
- `prediction_type`, `predicted_at`, `predicted_time`
- `confidence_score`, `severity`, `status`
- `contributing_factors` (simplified)
- `recommended_actions` (first 3 only)
- `actual_outcome`, `actual_time`, `accuracy_score`
- `model_version`

#### Fields to TRIM

1. **`contributing_factors`** (Lines 210-212)
   - Array of detailed factor objects
   - Each has `factor`, `current_value`, `threshold`, `trend`, `weight`
   - **Keep**: Only `factor`, `current_value`, `trend` (drop `threshold`, `weight`)

2. **`metadata`** (Line 224)
   - Additional data
   - **Keep**: Drop entirely

**Estimated Reduction**: 20-30%

---

### 4. OptimizationRecommendation Entity

**Model**: [`backend/app/models/recommendation.py`](backend/app/models/recommendation.py)

#### Fields to KEEP
- `id`, `gateway_id`, `api_id`
- `recommendation_type`, `title`, `description`
- `priority`, `implementation_effort`, `status`
- `estimated_impact` (simplified)
- `implementation_steps` (first 3 only)
- `cost_savings`
- `created_at`, `updated_at`

#### Fields to TRIM

1. **`estimated_impact`** (Line 352)
   - Full EstimatedImpact object with all metrics
   - **Keep**: Only `metric`, `improvement_percentage`, `confidence`
   - **Drop**: `current_value`, `expected_value`

2. **`validation_results`** (Lines 363-365)
   - Full validation with ActualImpact
   - **Keep**: Only `success` boolean and `actual_improvement` percentage

3. **`remediation_actions`** (Lines 366-369)
   - Full action history
   - **Keep**: Only count and latest action status

4. **`vendor_metadata`** (Lines 374-377)
   - Gateway-specific data
   - **Keep**: Drop entirely

5. **`ai_context`** (Lines 378-381)
   - AI-generated insights (can be large)
   - **Keep**: Only `performance_analysis` (first 200 chars)
   - **Drop**: `implementation_guidance`, `prioritization`

6. **`metadata`** (Line 373)
   - Additional data
   - **Keep**: Drop entirely

**Estimated Reduction**: 50-70%

---

### 5. Metric Entity

**Model**: [`backend/app/models/base/metric.py`](backend/app/models/base/metric.py)

#### Fields to KEEP
- `id`, `gateway_id`, `api_id`
- `timestamp`, `time_bucket`
- `request_count`, `success_count`, `failure_count`
- `error_rate`, `availability`
- `response_time_avg`, `response_time_p95`, `response_time_p99`
- `throughput`
- `cache_hit_rate`
- `status_2xx_count`, `status_4xx_count`, `status_5xx_count`

#### Fields to TRIM

1. **`endpoint_metrics`** (Lines 195-197)
   - Per-endpoint breakdown array
   - Can be very large for APIs with many endpoints
   - **Keep**: Only count and top 3 endpoints by request_count

2. **`status_codes`** (Lines 188-190)
   - Detailed status code distribution dict
   - **Keep**: Drop entirely (aggregated counts are sufficient)

3. **`vendor_metadata`** (Lines 202-204)
   - Vendor-specific fields
   - **Keep**: Drop entirely

4. **Redundant timing fields**:
   - `response_time_min`, `response_time_max` (Lines 149-150)
   - `response_time_p50` (Line 152)
   - `gateway_time_avg`, `backend_time_avg` (Lines 158-159)
   - **Keep**: Only avg, p95, p99

5. **Redundant data transfer fields**:
   - `total_data_size`, `avg_request_size`, `avg_response_size` (Lines 169-171)
   - **Keep**: Drop entirely (not critical for LLM context)

6. **Redundant cache fields**:
   - `cache_hit_count`, `cache_miss_count`, `cache_bypass_count` (Lines 176-178)
   - **Keep**: Only `cache_hit_rate`

**Estimated Reduction**: 40-60%

---

### 6. ComplianceViolation Entity

**Model**: [`backend/app/models/compliance.py`](backend/app/models/compliance.py)

#### Fields to KEEP
- `id`, `gateway_id`, `api_id`
- `compliance_standard`, `violation_type`, `severity`
- `title`, `description`
- `affected_endpoints` (first 3 only)
- `detection_method`, `detected_at`, `status`
- `regulatory_reference`, `risk_level`
- `remediation_deadline`, `remediated_at`

#### Fields to TRIM

1. **`evidence`** (Lines 320-322)
   - Array of Evidence objects with full data payloads
   - **Keep**: Only count and types

2. **`audit_trail`** (Lines 324-326)
   - Complete chronological history
   - **Keep**: Only count and latest entry

3. **`remediation_documentation`** (Lines 328-330)
   - Full remediation action history
   - **Keep**: Only count and latest action status

4. **`metadata`** (Lines 356-359)
   - Additional flexible data
   - **Keep**: Drop entirely

**Estimated Reduction**: 50-70%

---

### 7. Gateway Entity

**Model**: [`backend/app/models/gateway.py`](backend/app/models/gateway.py)

#### Fields to KEEP
- `id`, `name`, `vendor`, `version`
- `base_url`, `connection_type`
- `capabilities` (list)
- `status`, `last_connected_at`
- `api_count`
- `metrics_enabled`, `security_scanning_enabled`, `rate_limiting_enabled`

#### Fields to TRIM

1. **`base_url_credentials`** (Lines 215-218)
   - Encrypted authentication data
   - **Keep**: Drop entirely (security risk and unnecessary)

2. **`transactional_logs_credentials`** (Lines 219-222)
   - Encrypted authentication data
   - **Keep**: Drop entirely

3. **`transactional_logs_url`** (Lines 207-210)
   - Separate endpoint URL
   - **Keep**: Drop (not needed for LLM context)

4. **`configuration`** (Lines 258-261)
   - Vendor-specific config dict
   - **Keep**: Drop entirely

5. **`metadata`** (Lines 262-265)
   - Additional flexible data
   - **Keep**: Drop entirely

6. **`last_error`** (Lines 236-240)
   - Error message (can be long)
   - **Keep**: Only first 100 characters if present

**Estimated Reduction**: 40-60%

---


## Implementation Strategy

### Option 1: Create Trimmed Serialization Methods (Recommended)

Add a `to_llm_dict()` method to each entity model. This provides maximum control and clarity.

### Option 2: Create Utility Function

Create a centralized utility function that handles trimming for all entity types.

### Option 3: Use Pydantic's `model_dump` with `exclude`

Use Pydantic's built-in exclusion mechanism, though this is less flexible for complex trimming logic.

**Recommendation**: Use **Option 1** for maximum control and clarity.

---

## Expected Impact

### Payload Size Reduction
- **API entities**: 60-85% reduction (from ~50-200KB to ~5-30KB)
- **Vulnerability entities**: 40-60% reduction
- **Recommendation entities**: 50-70% reduction
- **Metric entities**: 40-60% reduction
- **Compliance entities**: 50-70% reduction
- **Gateway entities**: 40-60% reduction

### Benefits
1. **Reduced LLM costs**: Smaller token counts = lower API costs
2. **Faster response times**: Less data to serialize and transmit
3. **Better context utilization**: More entities fit in context window
4. **Improved response quality**: LLM focuses on relevant data

### Risks
- **Information loss**: Ensure trimmed data still provides sufficient context
- **Maintenance overhead**: Need to keep trimming logic in sync with models
- **Testing complexity**: Need to verify LLM responses remain high quality

---

## Rollout Plan

### Phase 1: API Entity (Highest Impact)
1. Implement `API.to_llm_dict()`
2. Update query service to use trimmed serialization
3. Test and validate response quality
4. Monitor payload sizes and LLM costs

### Phase 2: High-Volume Entities
1. Implement for Vulnerability, Recommendation, Metric
2. Deploy and monitor

### Phase 3: Remaining Entities
1. Implement for Compliance, Gateway, Prediction
2. Complete rollout

---

## Monitoring Metrics

Track these metrics before and after implementation:

1. **Average payload size per entity type**
2. **LLM token count per query**
3. **LLM API costs per query**
4. **Query response time**
5. **User satisfaction with responses** (if available)

---

## Conclusion

Implementing entity payload trimming will significantly reduce LLM costs and improve response times while maintaining response quality. The API entity offers the highest impact opportunity, with potential 60-85% payload reduction. A phased rollout starting with API entities is recommended.

---

**Next Steps**:
1. Review and approve this analysis
2. Implement `to_llm_dict()` for API entity
3. Test with real queries
4. Measure impact
5. Proceed with remaining entities