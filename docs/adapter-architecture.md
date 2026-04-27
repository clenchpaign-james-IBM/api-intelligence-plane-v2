# Gateway Adapter Architecture

**Last Updated**: 2026-04-10  
**Status**: Architecture Definition

## Overview

The API Intelligence Plane uses a **vendor-neutral architecture** with gateway-specific adapters that transform vendor data to standardized models. This document defines the adapter architecture and transformation requirements.

## Architecture Principles

### 1. Vendor-Neutral Core

All internal systems (services, agents, repositories, APIs) work with vendor-neutral models:
- **`api.py:API`** - API metadata with intelligence fields
- **`metric.py:Metric`** - Time-bucketed aggregated metrics
- **`transaction.py:TransactionalLog`** - Raw transactional events

### 2. Adapter Transformation Layer

Gateway adapters are responsible for:
1. **Collecting vendor-specific data** from gateway APIs
2. **Transforming to vendor-neutral models** with proper field mapping
3. **Populating `vendor_metadata`** with vendor-specific fields
4. **Bidirectional policy transformation** (vendor-neutral ↔ vendor-specific)

### 3. Consistent Intelligence

All intelligence plane features (predictions, security, compliance, optimization) work consistently regardless of source gateway vendor.

## BaseGatewayAdapter Interface

### Current Issues (To Be Fixed)

The current `BaseGatewayAdapter` (backend/app/adapters/base.py) has the following issues:

1. **Returns vendor-neutral models directly** - Should collect vendor data first, then transform
2. **Missing transformation methods** - No explicit transformation layer
3. **Missing transactional log collection** - No `collect_transactional_logs()` method
4. **Policy methods use generic dicts** - Should use `PolicyAction` model
5. **No `vendor_metadata` guidance** - No documentation on how to populate vendor-specific fields

### Required Changes

#### 1. Add Transformation Methods

```python
@abstractmethod
async def _transform_to_api(self, vendor_data: dict[str, Any]) -> API:
    """Transform vendor-specific API data to vendor-neutral API model.
    
    Args:
        vendor_data: Raw API data from vendor gateway
        
    Returns:
        API: Vendor-neutral API model with:
            - policy_actions: Transformed to vendor-neutral PolicyAction list
            - api_definition: OpenAPI/Swagger specification
            - endpoints: List of Endpoint objects
            - version_info: VersionInfo object
            - intelligence_metadata: IntelligenceMetadata wrapper
            - vendor_metadata: Dict with vendor-specific fields
    """
    pass

@abstractmethod
async def _transform_to_metric(
    self, 
    vendor_metrics: list[dict[str, Any]], 
    time_bucket: TimeBucket
) -> list[Metric]:
    """Transform vendor-specific metrics to time-bucketed Metric model.
    
    Args:
        vendor_metrics: Raw metrics from vendor gateway
        time_bucket: Target time bucket (1m, 5m, 1h, 1d)
        
    Returns:
        list[Metric]: Vendor-neutral metrics with:
            - gateway_id: Gateway identifier
            - api_id: API identifier
            - timestamp: Bucket timestamp
            - time_bucket: TimeBucket enum value
            - response_time_*: Timing metrics (avg/min/max/p50/p95/p99)
            - error_rate: Error percentage
            - throughput: Requests per second
            - cache_*: Cache metrics (hit/miss/bypass counts and rates)
            - gateway_time_avg: Gateway processing time
            - backend_time_avg: Backend service time
            - status_code_*: HTTP status breakdown (2xx/3xx/4xx/5xx)
            - vendor_metadata: Dict with vendor-specific fields
    """
    pass

@abstractmethod
async def _transform_to_transactional_log(
    self,
    vendor_logs: list[dict[str, Any]]
) -> list[TransactionalLog]:
    """Transform vendor-specific logs to vendor-neutral TransactionalLog model.
    
    Defined in backend/app/models/base/transaction.py.
    
    Args:
        vendor_logs: Raw transactional logs from vendor gateway
        
    Returns:
        list[TransactionalLog]: Vendor-neutral logs with:
            - gateway_id: Gateway identifier
            - api_id: API identifier
            - timestamp: Event timestamp
            - total_time_ms: Total request time
            - backend_time_ms: Backend service time
            - gateway_time_ms: Gateway processing time
            - request_*: Request details (method, path, headers, body)
            - response_*: Response details (status, headers, body)
            - client_*: Client information (id, ip, user_agent)
            - external_calls: List of ExternalCall objects
            - error_*: Error information if applicable
            - vendor_metadata: Dict with vendor-specific fields
    """
    pass

@abstractmethod
async def _transform_to_policy_action(
    self, 
    vendor_policy: dict[str, Any]
) -> PolicyAction:
    """Transform vendor-specific policy to vendor-neutral PolicyAction model.
    
    Args:
        vendor_policy: Raw policy from vendor gateway
        
    Returns:
        PolicyAction: Vendor-neutral policy with:
            - action_type: PolicyActionType enum
            - enabled: Boolean flag
            - vendor_config: Dict with vendor-specific configuration
    """
    pass

@abstractmethod
async def _transform_from_policy_action(
    self, 
    policy_action: PolicyAction
) -> dict[str, Any]:
    """Transform vendor-neutral PolicyAction to vendor-specific policy.
    
    Args:
        policy_action: Vendor-neutral policy action
        
    Returns:
        dict: Vendor-specific policy configuration ready for gateway API
    """
    pass
```

#### 2. Add Transactional Log Collection

```python
@abstractmethod
async def collect_transactional_logs(
    self,
    api_id: Optional[str] = None,
    time_range_minutes: int = 5,
    limit: int = 10000
) -> list[TransactionalLog]:
    """Collect transactional logs from the Gateway.
    
    Args:
        api_id: Optional API identifier to filter logs
        time_range_minutes: Time range for log collection (default: 5 minutes)
        limit: Maximum number of logs to collect
        
    Returns:
        list[TransactionalLog]: Vendor-neutral transactional logs
        
    Raises:
        RuntimeError: If not connected to Gateway
    """
    pass
```

#### 3. Update Policy Methods

Change policy methods to use `PolicyAction` model:

```python
@abstractmethod
async def apply_policy(
    self, 
    api_id: str, 
    policy_action: PolicyAction
) -> bool:
    """Apply a policy action to an API.
    
    Args:
        api_id: API identifier
        policy_action: Vendor-neutral policy action
        
    Returns:
        bool: True if policy applied successfully
        
    Implementation:
        1. Transform PolicyAction to vendor-specific format using _transform_from_policy_action()
        2. Apply to gateway via vendor API
        3. Verify application success
    """
    pass

@abstractmethod
async def remove_policy(
    self, 
    api_id: str, 
    policy_type: PolicyActionType
) -> bool:
    """Remove a policy from an API.
    
    Args:
        api_id: API identifier
        policy_type: Type of policy to remove
        
    Returns:
        bool: True if policy removed successfully
    """
    pass
```

#### 4. Update Discovery Methods

Update `discover_apis()` to use transformation:

```python
async def discover_apis(self) -> list[API]:
    """Discover all APIs registered in the Gateway.
    
    Returns:
        list[API]: List of vendor-neutral API entities
        
    Implementation:
        1. Collect vendor-specific API data from gateway
        2. Transform each API using _transform_to_api()
        3. Return list of vendor-neutral API models
    """
    # Collect vendor data
    vendor_apis = await self._collect_vendor_apis()
    
    # Transform to vendor-neutral
    apis = []
    for vendor_api in vendor_apis:
        api = await self._transform_to_api(vendor_api)
        apis.append(api)
    
    return apis
```

## Vendor-Specific Implementations

### WebMethodsGatewayAdapter

**Purpose**: Transform webMethods API Gateway data to vendor-neutral models

**Key Transformations**:
1. **API Transformation**:
   - webMethods `apiDefinition` → `api_definition` (OpenAPI)
   - webMethods `policyActions` → `policy_actions` (PolicyAction list)
   - webMethods-specific fields → `vendor_metadata`

2. **Metric Transformation**:
   - webMethods analytics → time-bucketed `Metric`
   - webMethods timing fields → `gateway_time_avg`, `backend_time_avg`
   - webMethods cache stats → `cache_hit_count`, `cache_miss_count`, etc.

3. **TransactionalLog Transformation**:
   - webMethods transactional events → vendor-neutral `TransactionalLog` (transaction.py)
   - webMethods `nativeService` → `backend_service`
   - webMethods `applicationName` → `client_id`

**vendor_metadata Fields**:
```python
{
    "api_version": "1.0.0",
    "system_version": "10.15",
    "owner": "API Team",
    "maturity_state": "Active",
    "groups": ["finance", "payments"],
    "native_service": "PaymentService",
    "provider_name": "PaymentProvider"
}
```

### NativeGatewayAdapter (Gateway)

**Purpose**: Transform Gateway data for development/testing

**Key Transformations**:
1. Simple transformation from Gateway REST API
2. Minimal `vendor_metadata` (demo-specific fields)
3. Support for all policy types for testing

### KongGatewayAdapter

**Purpose**: Transform Kong Gateway data to vendor-neutral models

**Key Transformations**:
1. Kong Admin API → vendor-neutral models
2. Kong plugins → `PolicyAction` list
3. Kong-specific fields → `vendor_metadata`

**vendor_metadata Fields**:
```python
{
    "kong_service_id": "uuid",
    "kong_route_id": "uuid",
    "kong_plugins": [...],
    "kong_tags": [...]
}
```

### ApigeeGatewayAdapter

**Purpose**: Transform Apigee Gateway data to vendor-neutral models

**Key Transformations**:
1. Apigee Management API → vendor-neutral models
2. Apigee policies → `PolicyAction` list
3. Apigee-specific fields → `vendor_metadata`

**vendor_metadata Fields**:
```python
{
    "apigee_proxy_name": "payment-api",
    "apigee_revision": "3",
    "apigee_environment": "prod",
    "apigee_policies": [...]
}
```

## Implementation Guidelines

### 1. Transformation Best Practices

- **Field Mapping**: Create explicit field mapping tables for each vendor
- **Default Values**: Provide sensible defaults for missing fields
- **Validation**: Validate transformed models before returning
- **Error Handling**: Log transformation errors with vendor context
- **Idempotency**: Ensure transformations are deterministic

### 2. vendor_metadata Population

**Rules**:
- Store ALL vendor-specific fields that don't map to vendor-neutral model
- Use consistent naming within vendor (e.g., all Kong fields prefixed with `kong_`)
- Document vendor_metadata schema for each adapter
- Keep vendor_metadata flat (no deep nesting)

**Example**:
```python
# Good
vendor_metadata = {
    "webmethods_api_version": "1.0.0",
    "webmethods_system_version": "10.15",
    "webmethods_owner": "API Team"
}

# Bad - inconsistent naming
vendor_metadata = {
    "apiVersion": "1.0.0",  # camelCase
    "system_version": "10.15",  # snake_case
    "Owner": "API Team"  # PascalCase
}
```

### 3. PolicyAction Transformation

**Vendor-Neutral → Vendor-Specific**:
```python
async def _transform_from_policy_action(
    self, 
    policy_action: PolicyAction
) -> dict[str, Any]:
    """Transform to vendor-specific policy."""
    
    # Extract vendor-specific config
    vendor_config = policy_action.vendor_config or {}
    
    # Build vendor policy structure
    if policy_action.action_type == PolicyActionType.RATE_LIMIT:
        return {
            "type": "RateLimiting",
            "enabled": policy_action.enabled,
            "configuration": {
                "requests_per_minute": vendor_config.get("rpm", 100),
                "burst_size": vendor_config.get("burst", 10),
                # ... vendor-specific fields
            }
        }
    # ... handle other policy types
```

**Vendor-Specific → Vendor-Neutral**:
```python
async def _transform_to_policy_action(
    self, 
    vendor_policy: dict[str, Any]
) -> PolicyAction:
    """Transform from vendor-specific policy."""
    
    # Map vendor policy type to PolicyActionType enum
    policy_type_map = {
        "RateLimiting": PolicyActionType.RATE_LIMIT,
        "Caching": PolicyActionType.CACHING,
        # ... other mappings
    }
    
    action_type = policy_type_map.get(vendor_policy["type"])
    
    # Extract vendor-specific config
    vendor_config = {
        "rpm": vendor_policy["configuration"]["requests_per_minute"],
        "burst": vendor_policy["configuration"]["burst_size"],
        # ... other vendor fields
    }
    
    return PolicyAction(
        action_type=action_type,
        enabled=vendor_policy["enabled"],
        vendor_config=vendor_config
    )
```

### 4. Time-Bucketed Metrics

**Aggregation Strategy**:
```python
async def _transform_to_metric(
    self, 
    vendor_metrics: list[dict[str, Any]], 
    time_bucket: TimeBucket
) -> list[Metric]:
    """Transform and aggregate to time buckets."""
    
    # Group by time bucket
    bucketed = self._group_by_time_bucket(vendor_metrics, time_bucket)
    
    metrics = []
    for bucket_time, bucket_metrics in bucketed.items():
        # Calculate aggregates
        metric = Metric(
            gateway_id=self.gateway.id,
            api_id=bucket_metrics[0]["api_id"],
            timestamp=bucket_time,
            time_bucket=time_bucket,
            
            # Aggregate response times
            response_time_avg=self._calculate_avg(bucket_metrics, "response_time"),
            response_time_min=self._calculate_min(bucket_metrics, "response_time"),
            response_time_max=self._calculate_max(bucket_metrics, "response_time"),
            response_time_p50=self._calculate_percentile(bucket_metrics, "response_time", 50),
            response_time_p95=self._calculate_percentile(bucket_metrics, "response_time", 95),
            response_time_p99=self._calculate_percentile(bucket_metrics, "response_time", 99),
            
            # Calculate error rate
            error_rate=self._calculate_error_rate(bucket_metrics),
            
            # Calculate throughput
            throughput=len(bucket_metrics) / time_bucket.seconds,
            
            # Aggregate cache metrics
            cache_hit_count=self._sum(bucket_metrics, "cache_hits"),
            cache_miss_count=self._sum(bucket_metrics, "cache_misses"),
            cache_bypass_count=self._sum(bucket_metrics, "cache_bypasses"),
            
            # Calculate timing breakdown
            gateway_time_avg=self._calculate_avg(bucket_metrics, "gateway_time"),
            backend_time_avg=self._calculate_avg(bucket_metrics, "backend_time"),
            
            # Status code breakdown
            status_code_2xx=self._count_status_range(bucket_metrics, 200, 299),
            status_code_3xx=self._count_status_range(bucket_metrics, 300, 399),
            status_code_4xx=self._count_status_range(bucket_metrics, 400, 499),
            status_code_5xx=self._count_status_range(bucket_metrics, 500, 599),
            
            # Vendor-specific fields
            vendor_metadata=self._extract_vendor_metadata(bucket_metrics[0])
        )
        
        metrics.append(metric)
    
    return metrics
```

## Testing Strategy

### 1. Transformation Tests

Test each transformation method independently:

```python
async def test_transform_to_api():
    """Test API transformation."""
    adapter = WebMethodsGatewayAdapter(gateway)
    
    # Mock vendor data
    vendor_data = {
        "apiName": "Payment API",
        "apiVersion": "1.0.0",
        "policyActions": [...],
        # ... vendor fields
    }
    
    # Transform
    api = await adapter._transform_to_api(vendor_data)
    
    # Verify vendor-neutral structure
    assert api.name == "Payment API"
    assert api.version_info.current == "1.0.0"
    assert len(api.policy_actions) > 0
    assert "webmethods_api_version" in api.vendor_metadata
```

### 2. Round-Trip Tests

Test bidirectional policy transformation:

```python
async def test_policy_round_trip():
    """Test PolicyAction round-trip transformation."""
    adapter = WebMethodsGatewayAdapter(gateway)
    
    # Start with vendor-neutral
    policy_action = PolicyAction(
        action_type=PolicyActionType.RATE_LIMIT,
        enabled=True,
        vendor_config={"rpm": 100}
    )
    
    # Transform to vendor-specific
    vendor_policy = await adapter._transform_from_policy_action(policy_action)
    
    # Transform back to vendor-neutral
    result = await adapter._transform_to_policy_action(vendor_policy)
    
    # Verify equivalence
    assert result.action_type == policy_action.action_type
    assert result.enabled == policy_action.enabled
    assert result.vendor_config["rpm"] == 100
```

### 3. Integration Tests

Test complete adapter workflows:

```python
async def test_discover_and_collect():
    """Test full discovery and metrics collection."""
    adapter = WebMethodsGatewayAdapter(gateway)
    await adapter.connect()
    
    # Discover APIs
    apis = await adapter.discover_apis()
    assert len(apis) > 0
    assert all(isinstance(api, API) for api in apis)
    
    # Collect metrics
    metrics = await adapter.collect_metrics(time_range_minutes=5)
    assert len(metrics) > 0
    assert all(isinstance(m, Metric) for m in metrics)
    
    # Collect logs
    logs = await adapter.collect_transactional_logs(time_range_minutes=5)
    assert len(logs) > 0
    assert all(isinstance(log, TransactionalLog) for log in logs)
```

## Migration Path

### Phase 1: Update BaseGatewayAdapter (Current)
- Add transformation method signatures
- Add `collect_transactional_logs()` method
- Update policy methods to use `PolicyAction`
- Add `vendor_metadata` documentation

### Phase 2: Implement WebMethodsGatewayAdapter
- Create new adapter file
- Implement all transformation methods
- Populate `vendor_metadata` correctly
- Test with real webMethods gateway

### Phase 3: Update Existing Adapters
- Update NativeGatewayAdapter for vendor-neutral models
- Implement KongGatewayAdapter transformations
- Implement ApigeeGatewayAdapter transformations

### Phase 4: Update Services
- Update discovery_service to use transformed models
- Update metrics_service for time-bucketed metrics
- Update all services to handle `vendor_metadata`

### Phase 5: Validation
- Integration tests across all adapters
- Verify vendor-neutral consistency
- Performance testing with multiple vendors

## References

- **Vendor-Neutral Models**: `backend/app/models/base/api.py`, `backend/app/models/base/metric.py`, `backend/app/models/base/transaction.py`
- **Current Adapter**: `backend/app/adapters/base.py`
- **Specification**: `specs/001-api-intelligence-plane/spec.md` (FR-053 through FR-087)
- **Tasks**: `specs/001-api-intelligence-plane/tasks.md` (Phase 0, Adapter Layer Refactoring)