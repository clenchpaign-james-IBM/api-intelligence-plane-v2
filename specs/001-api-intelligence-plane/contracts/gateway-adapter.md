# Gateway Adapter Contract: API Intelligence Plane

**Version**: 1.0  
**Pattern**: Strategy + Adapter  
**Date**: 2026-04-28

## Overview

Gateway adapters provide vendor-neutral integration with API Gateway products. Each adapter implements a standard interface while handling vendor-specific API calls, data formats, and capabilities. This enables the Intelligence Plane to work consistently across different gateway vendors.

## Architecture Pattern

### Strategy Pattern
Encapsulates vendor-specific algorithms for discovery, metrics collection, and policy application.

### Adapter Pattern
Normalizes vendor-specific APIs into a unified interface.

```python
# Abstract Base
class GatewayAdapter(ABC):
    """Base adapter interface that all gateway adapters must implement"""
    
    @abstractmethod
    async def discover_apis(self) -> List[API]:
        """Discover all APIs from the gateway"""
        pass
    
    @abstractmethod
    async def collect_metrics(self, api_id: str, time_range: TimeRange) -> List[Metric]:
        """Collect metrics for an API"""
        pass
    
    @abstractmethod
    async def apply_policy(self, api_id: str, policy: Policy) -> PolicyResult:
        """Apply a policy to an API"""
        pass
    
    @abstractmethod
    async def collect_transactional_logs(self, time_range: TimeRange) -> List[TransactionalLog]:
        """Collect transactional logs from the gateway"""
        pass
    
    @abstractmethod
    async def get_gateway_health(self) -> GatewayHealth:
        """Get gateway health status"""
        pass
```

---

## Core Interface Methods

### 1. discover_apis()

**Purpose**: Discover all APIs registered in the gateway

**Returns**: `List[API]` - List of discovered APIs in vendor-neutral format

**Vendor-Specific Behavior**:
- **WebMethods**: Calls `/rest/apigateway/apis` endpoint, transforms API definitions
- **Kong**: Calls `/services` and `/routes` endpoints, combines into API definitions
- **Apigee**: Calls `/organizations/{org}/apis` endpoint, transforms proxy definitions

**Normalization Requirements**:
- Convert vendor-specific API identifiers to UUIDs
- Transform endpoint definitions to standard format
- Normalize policy configurations to vendor-neutral format
- Extract OpenAPI specifications if available

**Example Implementation** (WebMethods):
```python
async def discover_apis(self) -> List[API]:
    # Call WebMethods API
    response = await self.client.get(
        f"{self.base_url}/rest/apigateway/apis"
    )
    
    # Transform to vendor-neutral format
    apis = []
    for wm_api in response.json()["apiResponse"]["api"]:
        api = API(
            api_id=str(uuid.uuid4()),
            gateway_id=self.gateway_id,
            name=wm_api["apiName"],
            version=wm_api["apiVersion"],
            base_path=wm_api["apiBasePath"],
            endpoints=self._normalize_endpoints(wm_api["resources"]),
            policies=self._normalize_policies(wm_api["policies"]),
            openapi_spec=self._extract_openapi(wm_api),
            maturity_state=self._map_maturity_state(wm_api["maturityState"])
        )
        apis.append(api)
    
    return apis
```

---

### 2. collect_metrics()

**Purpose**: Collect performance metrics for an API

**Parameters**:
- `api_id` (str): API identifier
- `time_range` (TimeRange): Time range for metrics

**Returns**: `List[Metric]` - Time-series metrics in vendor-neutral format

**Vendor-Specific Behavior**:
- **WebMethods**: Queries Analytics Server for metrics
- **Kong**: Queries Prometheus/StatsD for metrics
- **Apigee**: Queries Analytics API for metrics

**Normalization Requirements**:
- Convert timestamps to ISO 8601 format
- Normalize metric names (response_time, error_rate, throughput)
- Calculate percentiles if not provided by vendor
- Aggregate to requested time bucket

**Example Implementation** (WebMethods):
```python
async def collect_metrics(self, api_id: str, time_range: TimeRange) -> List[Metric]:
    # Get vendor-specific API ID
    wm_api_id = self._get_vendor_api_id(api_id)
    
    # Query WebMethods Analytics
    response = await self.analytics_client.post(
        f"{self.analytics_url}/rest/analytics/query",
        json={
            "apiId": wm_api_id,
            "startTime": time_range.start.isoformat(),
            "endTime": time_range.end.isoformat(),
            "metrics": ["responseTime", "errorRate", "throughput"]
        }
    )
    
    # Transform to vendor-neutral format
    metrics = []
    for data_point in response.json()["data"]:
        metric = Metric(
            metric_id=str(uuid.uuid4()),
            gateway_id=self.gateway_id,
            api_id=api_id,
            timestamp=data_point["timestamp"],
            time_bucket=time_range.bucket,
            response_time=self._normalize_response_time(data_point),
            error_rate=self._normalize_error_rate(data_point),
            throughput=self._normalize_throughput(data_point)
        )
        metrics.append(metric)
    
    return metrics
```

---

### 3. apply_policy()

**Purpose**: Apply a security or optimization policy to an API

**Parameters**:
- `api_id` (str): API identifier
- `policy` (Policy): Vendor-neutral policy configuration

**Returns**: `PolicyResult` - Result of policy application

**Vendor-Specific Behavior**:
- **WebMethods**: Creates policy action via `/rest/apigateway/policies`
- **Kong**: Creates plugin via `/services/{id}/plugins`
- **Apigee**: Creates policy via `/organizations/{org}/apis/{api}/policies`

**Policy Types**:
- `authentication`: OAuth2, API Key, Basic Auth
- `rate_limiting`: Request rate limits
- `caching`: Response caching
- `compression`: Response compression
- `encryption`: TLS/SSL enforcement

**Normalization Requirements**:
- Convert vendor-neutral policy to vendor-specific format
- Validate policy compatibility with gateway capabilities
- Handle vendor-specific policy parameters
- Return standardized result

**Example Implementation** (WebMethods):
```python
async def apply_policy(self, api_id: str, policy: Policy) -> PolicyResult:
    # Get vendor-specific API ID
    wm_api_id = self._get_vendor_api_id(api_id)
    
    # Convert to WebMethods policy format
    wm_policy = self._denormalize_policy(policy)
    
    # Apply policy via WebMethods API
    response = await self.client.post(
        f"{self.base_url}/rest/apigateway/apis/{wm_api_id}/policies",
        json=wm_policy
    )
    
    # Return standardized result
    return PolicyResult(
        success=response.status_code == 200,
        policy_id=response.json()["policyId"],
        message="Policy applied successfully",
        applied_at=datetime.now(timezone.utc).isoformat()
    )
```

---

### 4. collect_transactional_logs()

**Purpose**: Collect detailed transaction logs for drill-down analysis

**Parameters**:
- `time_range` (TimeRange): Time range for logs

**Returns**: `List[TransactionalLog]` - Individual transaction records

**Vendor-Specific Behavior**:
- **WebMethods**: Queries Analytics Server for transaction logs
- **Kong**: Queries log aggregation system (e.g., Elasticsearch)
- **Apigee**: Queries Analytics API for transaction details

**Normalization Requirements**:
- Convert timestamps to ISO 8601 format
- Normalize HTTP methods and status codes
- Extract external service call information
- Sanitize sensitive data (credentials, tokens)

**Example Implementation** (WebMethods):
```python
async def collect_transactional_logs(self, time_range: TimeRange) -> List[TransactionalLog]:
    # Query WebMethods Analytics for transaction logs
    response = await self.analytics_client.post(
        f"{self.analytics_url}/rest/analytics/transactions",
        json={
            "startTime": time_range.start.isoformat(),
            "endTime": time_range.end.isoformat(),
            "includeExternalCalls": True
        }
    )
    
    # Transform to vendor-neutral format
    logs = []
    for tx in response.json()["transactions"]:
        log = TransactionalLog(
            transaction_id=tx["transactionId"],
            gateway_id=self.gateway_id,
            api_id=self._map_api_id(tx["apiId"]),
            timestamp=tx["timestamp"],
            request=self._normalize_request(tx["request"]),
            response=self._normalize_response(tx["response"]),
            timing=self._normalize_timing(tx["timing"]),
            external_calls=self._normalize_external_calls(tx.get("externalCalls", []))
        )
        logs.append(log)
    
    return logs
```

---

### 5. get_gateway_health()

**Purpose**: Check gateway health and connectivity

**Returns**: `GatewayHealth` - Health status information

**Vendor-Specific Behavior**:
- **WebMethods**: Calls `/rest/apigateway/health` endpoint
- **Kong**: Calls `/status` endpoint
- **Apigee**: Calls `/organizations/{org}/environments/{env}/stats`

**Example Implementation** (WebMethods):
```python
async def get_gateway_health(self) -> GatewayHealth:
    try:
        start_time = time.time()
        response = await self.client.get(
            f"{self.base_url}/rest/apigateway/health",
            timeout=5.0
        )
        response_time = (time.time() - start_time) * 1000
        
        return GatewayHealth(
            status="connected" if response.status_code == 200 else "error",
            response_time=response_time,
            last_check=datetime.now(timezone.utc).isoformat(),
            error_message=None
        )
    except Exception as e:
        return GatewayHealth(
            status="disconnected",
            response_time=None,
            last_check=datetime.now(timezone.utc).isoformat(),
            error_message=str(e)
        )
```

---

## Policy Conversion

### Normalizer (Vendor → Vendor-Neutral)

**Purpose**: Convert vendor-specific policy configurations to vendor-neutral format

**Location**: `backend/app/utils/{vendor}/policy_normalizer.py`

**Example** (WebMethods Authentication Policy):
```python
def normalize_authentication_policy(wm_policy: dict) -> Policy:
    """Convert WebMethods authentication policy to vendor-neutral format"""
    return Policy(
        policy_type="authentication",
        policy_action="require_oauth2",
        configuration={
            "oauth2_provider": wm_policy["authServer"],
            "scopes": wm_policy["scopes"],
            "token_validation": "introspection"
        }
    )
```

### Denormalizer (Vendor-Neutral → Vendor)

**Purpose**: Convert vendor-neutral policy configurations to vendor-specific format

**Location**: `backend/app/utils/{vendor}/policy_denormalizer.py`

**Example** (Vendor-Neutral → WebMethods):
```python
def denormalize_authentication_policy(policy: Policy) -> dict:
    """Convert vendor-neutral authentication policy to WebMethods format"""
    return {
        "policyName": "OAuth2Authentication",
        "policyType": "AUTHENTICATION",
        "authServer": policy.configuration["oauth2_provider"],
        "scopes": policy.configuration["scopes"],
        "validationMethod": "INTROSPECTION"
    }
```

---

## Capability Detection

Each adapter must declare its capabilities:

```python
class GatewayAdapter(ABC):
    @property
    def capabilities(self) -> GatewayCapabilities:
        return GatewayCapabilities(
            supports_discovery=True,
            supports_metrics=True,
            supports_policy_application=True,
            supports_transactional_logs=True,
            supported_policy_types=[
                "authentication",
                "rate_limiting",
                "caching",
                "compression"
            ]
        )
```

---

## Error Handling

All adapter methods must handle errors gracefully:

```python
class AdapterError(Exception):
    """Base exception for adapter errors"""
    pass

class ConnectionError(AdapterError):
    """Gateway connection failed"""
    pass

class AuthenticationError(AdapterError):
    """Gateway authentication failed"""
    pass

class UnsupportedOperationError(AdapterError):
    """Operation not supported by this gateway"""
    pass
```

---

## Testing Requirements

Each adapter must include:

1. **Unit Tests**: Test normalization/denormalization logic
2. **Integration Tests**: Test against real or mock gateway
3. **Contract Tests**: Verify adapter implements all required methods
4. **Capability Tests**: Verify declared capabilities match actual support

---

## Adapter Factory

**Purpose**: Create appropriate adapter based on gateway vendor

```python
class GatewayAdapterFactory:
    @staticmethod
    def create_adapter(gateway: Gateway) -> GatewayAdapter:
        """Create adapter for gateway vendor"""
        adapters = {
            "webmethods": WebMethodsGatewayAdapter,
            "kong": KongGatewayAdapter,
            "apigee": ApigeeGatewayAdapter
        }
        
        adapter_class = adapters.get(gateway.vendor)
        if not adapter_class:
            raise ValueError(f"Unsupported gateway vendor: {gateway.vendor}")
        
        return adapter_class(gateway)
```

---

## Vendor-Specific Implementations

### WebMethods API Gateway (Initial Release)

**Status**: ✅ Implemented  
**API Version**: 10.15+  
**Endpoints**:
- Discovery: `/rest/apigateway/apis`
- Metrics: Analytics Server REST API
- Policies: `/rest/apigateway/policies`
- Logs: Analytics Server transaction logs

**Capabilities**:
- ✅ API Discovery
- ✅ Metrics Collection
- ✅ Policy Application
- ✅ Transactional Logs
- ✅ Shadow API Detection

### Kong Gateway (Future)

**Status**: 🔄 Planned  
**API Version**: 3.0+  
**Endpoints**:
- Discovery: `/services`, `/routes`
- Metrics: Prometheus/StatsD
- Policies: `/services/{id}/plugins`

### Apigee API Gateway (Future)

**Status**: 🔄 Planned  
**API Version**: X+  
**Endpoints**:
- Discovery: `/organizations/{org}/apis`
- Metrics: `/organizations/{org}/environments/{env}/stats`
- Policies: `/organizations/{org}/apis/{api}/policies`

---

## Versioning

Adapters follow semantic versioning:
- **Major**: Breaking changes to interface
- **Minor**: New capabilities added
- **Patch**: Bug fixes

Example: `WebMethodsGatewayAdapter v1.2.3`

---

## Documentation Requirements

Each adapter must include:
1. Supported gateway versions
2. Required permissions/credentials
3. API endpoint mappings
4. Policy type mappings
5. Known limitations
6. Configuration examples

---

**Gateway Adapter Contract Complete**: 2026-04-28  
**Contracts Phase Complete**