# Shadow API Detection Analysis

## Overview
Analysis of the shadow API detection implementation in [`backend/app/scheduler/intelligence_metadata_jobs.py:560-650`](backend/app/scheduler/intelligence_metadata_jobs.py:560) based on observations about API path structure and matching logic.

**Date**: 2026-04-17  
**Status**: Analysis Complete

---

## Current Implementation Analysis

### 1. Current Shadow API Detection Flow

The [`detect_shadow_apis_job()`](backend/app/scheduler/intelligence_metadata_jobs.py:561) function currently:

```python
# Step 1: Fetch all registered APIs
registered_apis, _ = api_repo.list_all(size=10000)
registered_paths = {api.base_path for api in registered_apis}

# Step 2: Query transactional logs (last 5 minutes)
logs, _ = log_repo.find_logs(start_time=start_time, end_time=end_time, size=10000)

# Step 3: Extract observed paths from logs
observed_paths = set()
for log in logs:
    if hasattr(log, 'request_path') and log.request_path:
        observed_paths.add(log.request_path)

# Step 4: Find shadow paths (simple set difference)
shadow_paths = observed_paths - registered_paths

# Step 5: Check/create shadow API entries
for path in shadow_paths:
    existing_api = api_repo.find_by_base_path(path)
```

### 2. Key Issues Identified

#### Issue #1: Path Structure Mismatch
**Problem**: The current implementation compares full request paths against API base paths using simple set difference.

**Reality**:
- **API Model**: [`api.base_path`](backend/app/models/base/api.py:200) stores the base path (e.g., `/api/v1/users`)
- **Transactional Log**: [`log.request_path`](backend/app/models/base/transaction.py:110) contains the full request path including resource identifiers (e.g., `/gateway/users-api/v1/users/123/profile`)
- **Path Components**: `gateway/{apiName}/{apiVersion}/{resource_path}`

**Example**:
```
Registered API base_path: /api/v1/users
Actual request_path:      /gateway/users-api/v1/users/123/profile
                          └─────┬─────┘└──┬──┘└─┬─┘└────┬────────┘
                            gateway   apiName ver  resource_path
```

#### Issue #2: Multiple Resource Paths per API
**Problem**: A single API can have multiple resource paths/endpoints.

**Reality**:
- One API definition has multiple endpoints: `/users`, `/users/{id}`, `/users/{id}/profile`
- Each endpoint generates different `request_path` values in logs
- Current logic treats each unique path as a separate potential shadow API

**Example**:
```
API: "Users API" (base_path: /api/v1/users)
├── Endpoint 1: GET /users          → request_path: /gateway/users-api/v1/users
├── Endpoint 2: GET /users/{id}     → request_path: /gateway/users-api/v1/users/123
└── Endpoint 3: GET /users/{id}/profile → request_path: /gateway/users-api/v1/users/123/profile

Current behavior: All 3 paths flagged as potential shadow APIs
Expected behavior: All 3 paths recognized as belonging to "Users API"
```

#### Issue #3: Gateway-Specific Path Prefixes
**Problem**: Request paths include gateway-specific routing information.

**Reality**:
- Paths are prefixed with gateway routing: `/gateway/{apiName}/{apiVersion}/`
- Different gateways may use different routing schemes
- Base path comparison doesn't account for these prefixes

---

## Proposed Solution Architecture

### 1. Gateway-Aware Path Matching

#### Step 1: Fetch Gateways First
```python
async def detect_shadow_apis_job() -> None:
    gateway_repo = GatewayRepository()
    api_repo = APIRepository()
    log_repo = TransactionalLogRepository()
    
    # Fetch all connected gateways
    gateways, _ = gateway_repo.list_all(size=1000)
    
    for gateway in gateways:
        await detect_shadow_apis_for_gateway(gateway, api_repo, log_repo)
```

**Rationale**: Different gateways may have different routing schemes and path structures.

#### Step 2: Build Comprehensive Path Registry per Gateway
```python
async def detect_shadow_apis_for_gateway(gateway, api_repo, log_repo):
    # Fetch all APIs for this gateway
    registered_apis, _ = api_repo.find_by_gateway(gateway.id, size=10000)
    
    # Build path registry with all possible patterns
    path_registry = {}
    for api in registered_apis:
        # Extract all resource paths from API definition
        resource_paths = extract_resource_paths(api)
        
        for resource_path in resource_paths:
            # Construct full path pattern
            full_path_pattern = construct_full_path(
                gateway=gateway,
                api_name=api.name,
                api_version=api.version_info.current_version,
                resource_path=resource_path
            )
            path_registry[full_path_pattern] = api.id
```

**Key Functions**:

1. **`extract_resource_paths(api)`**: Extract all endpoint paths from API definition
   - Source: API endpoints/paths list
   - Returns: List of resource paths (e.g., `/users`, `/users/{id}`, `/users/{id}/profile`)

2. **`construct_full_path(gateway, api_name, api_version, resource_path)`**: Build complete path
   - Pattern: `/{gateway_prefix}/{api_name}/{api_version}{resource_path}`
   - Example: `/gateway/users-api/v1/users/123`

#### Step 3: Enhanced Path Matching
```python
# Query logs for this gateway
logs, _ = log_repo.find_logs(
    gateway_id=str(gateway.id),
    start_time=start_time,
    end_time=end_time,
    size=10000
)

# Extract observed paths
observed_paths = {log.request_path for log in logs if log.request_path}

# Match against registry using pattern matching
shadow_paths = []
for observed_path in observed_paths:
    if not matches_any_registered_pattern(observed_path, path_registry):
        shadow_paths.append(observed_path)
```

### 2. Enhanced `find_by_base_path()` Method

#### Current Implementation
```python
def find_by_base_path(self, base_path: str, gateway_id: Optional[UUID] = None) -> Optional[API]:
    query = {
        "bool": {
            "must": [
                {"term": {"base_path": base_path}}
            ]
        }
    }
    if gateway_id:
        query["bool"]["must"].append({"term": {"gateway_id": str(gateway_id)}})
    
    results, _ = self.search(query, size=1)
    return results[0] if results else None
```

#### Proposed Enhancement
```python
def find_by_request_path(
    self,
    request_path: str,
    gateway_id: UUID
) -> Optional[API]:
    """
    Find API by matching request path against registered patterns.
    
    Args:
        request_path: Full request path from transactional log
                     (e.g., /gateway/users-api/v1/users/123/profile)
        gateway_id: Gateway UUID
    
    Returns:
        Matching API if found, None otherwise
    
    Algorithm:
        1. Parse request_path to extract components:
           - gateway_prefix (e.g., /gateway)
           - api_name (e.g., users-api)
           - api_version (e.g., v1)
           - resource_path (e.g., /users/123/profile)
        
        2. Query APIs by gateway_id, api_name, and api_version
        
        3. For each candidate API:
           - Check if resource_path matches any endpoint pattern
           - Use path parameter matching (e.g., /users/{id}/profile)
        
        4. Return first matching API
    """
    # Parse path components
    components = parse_request_path(request_path)
    if not components:
        return None
    
    # Query candidate APIs
    query = {
        "bool": {
            "must": [
                {"term": {"gateway_id": str(gateway_id)}},
                {"term": {"name": components.api_name}},
                {"term": {"version_info.current_version": components.api_version}}
            ]
        }
    }
    
    candidates, _ = self.search(query, size=10)
    
    # Match resource path against API endpoints
    for api in candidates:
        if matches_api_endpoints(components.resource_path, api):
            return api
    
    return None
```

**Helper Functions**:

```python
def parse_request_path(request_path: str) -> Optional[PathComponents]:
    """
    Parse request path into components.
    
    Example:
        Input:  /gateway/users-api/v1/users/123/profile
        Output: PathComponents(
            gateway_prefix='/gateway',
            api_name='users-api',
            api_version='v1',
            resource_path='/users/123/profile'
        )
    """
    # Implementation: Split path and extract components
    pass

def matches_api_endpoints(resource_path: str, api: API) -> bool:
    """
    Check if resource_path matches any endpoint in API definition.
    
    Supports:
        - Exact matches: /users
        - Path parameters: /users/{id} matches /users/123
        - Nested paths: /users/{id}/profile matches /users/123/profile
    """
    # Implementation: Pattern matching with path parameters
    pass
```

---

## Implementation Recommendations

### Phase 1: Path Parsing and Matching (High Priority)
1. Implement `parse_request_path()` function
2. Implement `matches_api_endpoints()` function with path parameter support
3. Add `find_by_request_path()` method to [`APIRepository`](backend/app/db/repositories/api_repository.py:17)

### Phase 2: Gateway-Aware Detection (High Priority)
1. Modify [`detect_shadow_apis_job()`](backend/app/scheduler/intelligence_metadata_jobs.py:561) to iterate by gateway
2. Build comprehensive path registry per gateway
3. Use enhanced matching logic

### Phase 3: API Endpoint Extraction (Medium Priority)
1. Add endpoint extraction from API definitions
2. Support multiple endpoint patterns per API
3. Handle path parameters and wildcards

### Phase 4: Testing and Validation (High Priority)
1. Unit tests for path parsing
2. Integration tests for shadow API detection
3. Test with multiple gateway vendors
4. Validate against real transactional logs

---

## Data Model Considerations

### API Model Enhancement
Consider adding explicit endpoint definitions to [`API`](backend/app/models/base/api.py:1) model:

```python
class APIEndpoint(BaseModel):
    """Individual API endpoint definition."""
    path: str  # e.g., /users/{id}/profile
    method: str  # e.g., GET, POST
    description: Optional[str] = None

class API(BaseModel):
    # ... existing fields ...
    endpoints: List[APIEndpoint] = Field(
        default_factory=list,
        description="List of API endpoints/resource paths"
    )
```

**Benefits**:
- Explicit endpoint tracking
- Better shadow API detection
- Improved API documentation
- Enhanced metrics per endpoint

---

## Performance Considerations

### Current Bottlenecks
1. **Large Set Operations**: `observed_paths - registered_paths` with 10,000+ items
2. **Individual Path Lookups**: `find_by_base_path()` called for each shadow path
3. **No Caching**: Path registry rebuilt every 5 minutes

### Optimization Strategies
1. **In-Memory Path Registry**: Cache compiled path patterns
2. **Batch Operations**: Group shadow API creation/updates
3. **Incremental Updates**: Only process new logs since last run
4. **Gateway Parallelization**: Process gateways concurrently

---

## Security and Compliance

### Shadow API Risks
1. **Undocumented APIs**: Security vulnerabilities
2. **Unmonitored Traffic**: Compliance violations
3. **Unauthorized Access**: Data exposure

### Detection Improvements
1. **Real-time Alerts**: Immediate notification of shadow APIs
2. **Risk Scoring**: Prioritize shadow APIs by traffic volume
3. **Auto-Documentation**: Generate API specs from traffic patterns

---

## Conclusion

The current shadow API detection implementation has fundamental issues with path matching due to:
1. Mismatch between API base paths and transactional log request paths
2. Lack of support for multiple resource paths per API
3. No gateway-specific path parsing

**Recommended Approach**:
1. Implement gateway-aware path parsing
2. Build comprehensive path registry with all endpoint patterns
3. Use pattern matching with path parameter support
4. Enhance [`find_by_base_path()`](backend/app/db/repositories/api_repository.py:223) to [`find_by_request_path()`](backend/app/db/repositories/api_repository.py:223)

**Priority**: High - Current implementation may generate false positives and miss actual shadow APIs.

**Estimated Effort**: 3-5 days for complete implementation and testing.