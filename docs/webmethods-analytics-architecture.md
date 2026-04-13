# WebMethods Analytics Architecture

**Version**: 1.0.0  
**Last Updated**: 2026-04-09  
**Status**: Design Document

---

## Table of Contents

1. [Overview](#overview)
2. [Data Models](#data-models)
3. [Multi-Gateway Architecture](#multi-gateway-architecture)
4. [Data Collection Pipeline](#data-collection-pipeline)
5. [Aggregation Logic](#aggregation-logic)
6. [Drill-Down Pattern](#drill-down-pattern)
7. [OpenSearch Indices](#opensearch-indices)
8. [Integration Points](#integration-points)
9. [Implementation Roadmap](#implementation-roadmap)

---

## Overview

The WebMethods Analytics integration enables the API Intelligence Plane to collect, aggregate, and analyze transactional logs from WebMethods API Gateway. This document describes the architecture for handling raw transactional events and aggregating them into time-series metrics for AI-driven insights.

### Key Concepts

- **TransactionalLog**: Raw event logs from WebMethods API Gateway containing complete request/response details
- **Metrics**: Aggregated time-series data derived from TransactionalLog for performance analysis
- **Multi-Gateway Support**: Architecture supports multiple gateway instances with `gateway_id` as primary dimension
- **Drill-Down**: Ability to trace from aggregated metrics back to raw transactional logs

---

## Data Models

### 1. TransactionalLog Model

**Location**: [`backend/app/models/webmethods/wm_transaction.py`](../backend/app/models/webmethods/wm_transaction.py)

**Purpose**: Represents raw transactional events from WebMethods API Gateway

**Key Fields**:

```python
class TransactionalLog(BaseModel):
    # Identification
    id: UUID                          # Unique identifier (auto-generated)
    event_type: EventType             # "Transactional", "Lifecycle", etc.
    
    # Gateway & API Context
    source_gateway: str               # Gateway identifier (e.g., "APIGateway")
    tenant_id: str                    # Tenant for multi-tenancy
    api_id: str                       # API identifier
    api_name: str                     # API name
    api_version: str                  # API version
    
    # Timing Metrics
    creation_date: int                # Event timestamp (epoch milliseconds)
    total_time: int                   # Total request time (ms)
    provider_time: int                # Backend service time (ms)
    gateway_time: int                 # Gateway processing time (ms)
    
    # Request/Response Details
    operation_name: str               # API operation/endpoint
    http_method: str                  # HTTP method (GET, POST, etc.)
    status: EventStatus               # SUCCESS, FAILURE, PARTIAL
    response_code: str                # HTTP response code
    
    # Application Context
    application_name: str             # Calling application
    application_ip: str               # Client IP address
    application_id: str               # Application identifier
    
    # Payloads & Headers
    req_payload: str                  # Request payload
    res_payload: str                  # Response payload
    request_headers: dict[str, str]   # Request headers
    response_headers: dict[str, str]  # Response headers
    query_parameters: dict[str, Any]  # Query parameters
    
    # Native Service Call Details
    native_url: str                   # Backend service URL
    native_http_method: str           # Backend HTTP method
    native_req_payload: str           # Backend request payload
    native_res_payload: str           # Backend response payload
    native_request_headers: dict      # Backend request headers
    native_response_headers: dict     # Backend response headers
    
    # External Calls
    external_calls: list[ExternalCall] # External service calls made
    
    # Metadata
    session_id: str                   # Session identifier
    correlation_id: str               # Correlation ID for tracking
    error_origin: Optional[ErrorOrigin] # Error origin if failed
    cached_response: CacheStatus      # Cache status
    server_id: str                    # Gateway server ID
    source_gateway_node: str          # Gateway node that processed request
    callback_request: bool            # Whether callback request
    total_data_size: int              # Total data size in bytes
    
    # Timestamps
    created_at: datetime              # Record creation timestamp
    metadata: Optional[dict[str, Any]] # Additional metadata
```

**Supporting Models**:

```python
class ExternalCall(BaseModel):
    external_call_type: ExternalCallType  # NATIVE_SERVICE_CALL, ROUTING_CALL, etc.
    external_url: str                     # External service URL
    call_start_time: int                  # Call start (epoch ms)
    call_end_time: int                    # Call end (epoch ms)
    call_duration: int                    # Duration (ms)
    response_code: str                    # HTTP response code

class EventType(str, Enum):
    TRANSACTIONAL = "Transactional"
    LIFECYCLE = "Lifecycle"
    POLICY_VIOLATION = "PolicyViolation"
    THREAT_PROTECTION = "ThreatProtection"

class EventStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"
    PARTIAL = "PARTIAL"

class ErrorOrigin(str, Enum):
    NATIVE = "NATIVE"
    GATEWAY = "GATEWAY"
    APPLICATION = "APPLICATION"

class CacheStatus(str, Enum):
    CACHED = "Cached"
    NOT_CACHED = "Not-Cached"
    CACHE_MISS = "Cache-Miss"
```

### 2. Metrics Model (To Be Implemented)

**Location**: [`backend/app/models/base/metric.py`](../backend/app/models/base/metric.py)

**Purpose**: Aggregated time-series metrics derived from TransactionalLog

**Key Fields**:

```python
class Metrics(BaseModel):
    # Identification
    id: UUID                          # Unique identifier
    
    # Dimensions (for drill-down)
    gateway_id: UUID                  # Gateway instance identifier
    api_id: str                       # API identifier
    application_id: Optional[str]     # Application identifier (optional)
    
    # Time Dimensions
    timestamp: datetime               # Metric timestamp
    time_bucket: str                  # Time bucket (5m, 1h, 1d)
    
    # Aggregated Metrics
    request_count: int                # Total requests in bucket
    success_count: int                # Successful requests
    failure_count: int                # Failed requests
    error_rate: float                 # Error rate (%)
    
    # Response Time Metrics (milliseconds)
    response_time_avg: float          # Average response time
    response_time_min: float          # Minimum response time
    response_time_max: float          # Maximum response time
    response_time_p50: float          # 50th percentile
    response_time_p95: float          # 95th percentile
    response_time_p99: float          # 99th percentile
    
    # Gateway & Provider Time
    gateway_time_avg: float           # Average gateway processing time
    provider_time_avg: float          # Average backend service time
    
    # Throughput
    throughput: float                 # Requests per second
    
    # Data Transfer
    total_data_size: int              # Total data transferred (bytes)
    avg_request_size: float           # Average request size
    avg_response_size: float          # Average response size
    
    # Cache Metrics
    cache_hit_count: int              # Cache hits
    cache_miss_count: int             # Cache misses
    cache_hit_rate: float             # Cache hit rate (%)
    
    # HTTP Status Codes
    status_2xx_count: int             # 2xx responses
    status_4xx_count: int             # 4xx responses
    status_5xx_count: int             # 5xx responses
    
    # Metadata
    created_at: datetime              # Record creation timestamp
    updated_at: datetime              # Last update timestamp
```

### 3. API Model (Existing - Already Implemented)

**Location**: [`backend/app/models/webmethods/wm_api.py`](../backend/app/models/webmethods/wm_api.py) (lines 385-480)

**Status**: ✅ **Already implemented and in use** - This comprehensive model already exists in the codebase

**Purpose**: Complete API definition from WebMethods API Gateway with full metadata

**Implementation Details**:
- **Total Fields**: 40+ fields covering all aspects of API Gateway APIs
- **Nested Models**: Includes APIDefinition, Endpoint, PolicyActions, Scope, MockService, etc.
- **Field Aliasing**: Uses Pydantic Field aliases for JSON compatibility (e.g., `api_id` with alias `"apiId"`)
- **Policy Support**: Comprehensive policy action types (authentication, throttling, caching, CORS, data masking, etc.)

**Key Fields** (subset of 40+ total fields):

```python
class API(BaseModel):
    """
    Unified API model combining Gateway API metadata and REST API definition.
    Represents a complete API Gateway API with all metadata and definition.
    """
    # Core identification
    api_id: Optional[str] = Field(None, alias="apiId")
    doc_type: Optional[str] = Field("apis", alias="_docType")
    
    # API definition (RestAPI embedded)
    api_definition: Optional[APIDefinition] = Field(None, alias="apiDefinition")
    
    # Endpoints
    native_endpoint: Optional[Set[Endpoint]] = Field(None, alias="nativeEndpoint")
    
    # Basic metadata
    api_name: Optional[str] = Field(None, alias="apiName")
    api_display_name: Optional[str] = Field(None, alias="apiDisplayName")
    api_version: Optional[str] = Field(None, alias="apiVersion")
    api_description: Optional[str] = Field(None, alias="apiDescription")
    
    # Status and classification
    maturity_state: Optional[str] = Field(None, alias="maturityState")
    is_active: Optional[bool] = Field(None, alias="isActive")
    type: str = Field("REST", description="API type (REST, SOAP, WEBSOCKET, GRAPHQL, ODATA)")
    
    # Ownership and policies
    owner: Optional[str] = None
    policies: Optional[List[str]] = None
    policy_actions: Optional[List[Union[
        EntryProtocolPolicy,
        EvaluatePolicy,
        AuthorizeUserPolicy,
        LogInvocationPolicy,
        ThrottlePolicy,
        ServiceResultCachePolicy,
        ValidateAPISpecPolicy,
        RequestDataMaskingPolicy,
        ResponseDataMaskingPolicy,
        CorsPolicy
    ]]] = Field(None, alias="policyActions")
    
    # Timestamps
    creation_date: Optional[str] = Field(None, alias="creationDate")
    last_modified: Optional[str] = Field(None, alias="lastModified")
    
    # Versioning
    prev_version: Optional[str] = Field(None, alias="prevVersion")
    next_version: Optional[str] = Field(None, alias="nextVersion")
    system_version: int = Field(1, alias="systemVersion")
    
    # Publishing and portals
    published_portals: Optional[List[str]] = Field(default_factory=list, alias="publishedPortals")
    published_to_registry: Optional[bool] = Field(None, alias="publishedToRegistry")
    
    # ... 20+ additional fields for deployments, documentation, catalog, organization, etc.
```

**Usage in Analytics Integration**:
- Each `TransactionalLog` references an API via `api_id` and `api_name` fields
- The API model provides rich metadata context for transaction analysis
- Policy configurations from API model correlate with policy enforcement in transactions
- API endpoints map to `operation_name` in transactional logs
- API versioning enables tracking metrics across API versions

**Note**: **No modifications needed** - This model is already complete and suitable for analytics integration. It will be used as-is to provide API metadata context for transactional logs and aggregated metrics.

---

## Multi-Gateway Architecture

### Gateway Identification

The architecture supports multiple gateway instances through a **gateway_id** dimension:

```
┌─────────────────────────────────────────────────────────────┐
│                    API Intelligence Plane                    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              Backend API (FastAPI)                    │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │         Discovery Service                       │  │  │
│  │  │  - Discovers APIs from all gateways            │  │  │
│  │  │  - Assigns gateway_id to each API              │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │         Metrics Collection Service             │  │  │
│  │  │  - Collects logs from all gateways            │  │  │
│  │  │  - Tags logs with gateway_id                  │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  │                                                        │  │
│  │  ┌────────────────────────────────────────────────┐  │  │
│  │  │         Aggregation Service                    │  │  │
│  │  │  - Aggregates by (gateway_id, api_id, time)   │  │  │
│  │  └────────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Gateway 1   │    │  Gateway 2   │    │  Gateway 3   │
│  (Native)    │    │  (Kong)      │    │  (Apigee)    │
│              │    │              │    │              │
│ gateway_id:  │    │ gateway_id:  │    │ gateway_id:  │
│ uuid-1       │    │ uuid-2       │    │ uuid-3       │
└──────────────┘    └──────────────┘    └──────────────┘
```

### Gateway Registry

Each gateway is registered with:

```python
class Gateway(BaseModel):
    id: UUID                    # Unique gateway identifier (gateway_id)
    name: str                   # Gateway name
    vendor: str                 # Vendor (native, kong, apigee)
    base_url: str               # Gateway base URL
    status: str                 # Status (active, inactive)
    api_count: int              # Number of APIs
    last_sync_at: datetime      # Last sync timestamp
```

### Data Segregation

All data is segregated by `gateway_id`:

- **APIs**: Each API has a `gateway_id` field
- **TransactionalLog**: Each log has `source_gateway` (mapped to `gateway_id`)
- **Metrics**: Each metric has `gateway_id` dimension

---

## Data Collection Pipeline

### Collection Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Collection Pipeline                       │
│                                                              │
│  Step 1: Periodic Collection (Every 5 minutes)              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Scheduler triggers collection job                  │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  Step 2: Fetch Raw Logs from Gateway                        │
│  ┌────────────────────────────────────────────────────┐    │
│  │  MetricsService.collect_transactional_logs()        │    │
│  │  - Connects to gateway via adapter                 │    │
│  │  - Fetches logs since last collection              │    │
│  │  - Parses JSON to TransactionalLog model           │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  Step 3: Store Raw Logs                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Store in OpenSearch index: transactional-logs     │    │
│  │  - Index by (gateway_id, api_id, timestamp)        │    │
│  │  - Retention: 90 days                              │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  Step 4: Trigger Aggregation                                │
│  ┌────────────────────────────────────────────────────┐    │
│  │  AggregationService.aggregate_metrics()             │    │
│  │  - Aggregates logs into time buckets               │    │
│  │  - Stores in metrics index                         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Collection Service

**Location**: [`backend/app/services/metrics_service.py`](../backend/app/services/metrics_service.py) (to be enhanced)

```python
class MetricsService:
    async def collect_transactional_logs(
        self,
        gateway_id: UUID,
        since: datetime
    ) -> List[TransactionalLog]:
        """
        Collect transactional logs from gateway since last collection.
        
        Args:
            gateway_id: Gateway to collect from
            since: Collect logs since this timestamp
            
        Returns:
            List of TransactionalLog objects
        """
        # 1. Get gateway adapter
        adapter = self.gateway_factory.get_adapter(gateway_id)
        
        # 2. Fetch raw logs from gateway
        raw_logs = await adapter.fetch_transactional_logs(since)
        
        # 3. Parse to TransactionalLog model
        logs = [TransactionalLog(**log) for log in raw_logs]
        
        # 4. Store in OpenSearch
        await self.log_repository.bulk_create(logs)
        
        # 5. Trigger aggregation
        await self.aggregation_service.aggregate_metrics(
            gateway_id=gateway_id,
            logs=logs
        )
        
        return logs
```

---

## Aggregation Logic

### Aggregation Strategy

Raw TransactionalLog events are aggregated into Metrics using time-series buckets:

**Time Buckets**:
- **1-minute buckets**: Ultra real-time monitoring (retained 24 hours)
- **5-minute buckets**: Real-time monitoring (retained 7 days)
- **1-hour buckets**: Short-term analysis (retained 30 days)
- **1-day buckets**: Long-term trends (retained 90 days)

### Aggregation Dimensions

Metrics are aggregated by:

1. **gateway_id**: Gateway instance
2. **api_id**: API identifier
3. **application_id**: Calling application (optional)
4. **time_bucket**: Time bucket (1m, 5m, 1h, 1d)
5. **timestamp**: Bucket start time

### Aggregation Service

**Location**: [`backend/app/services/aggregation_service.py`](../backend/app/services/aggregation_service.py) (to be created)

```python
class AggregationService:
    async def aggregate_metrics(
        self,
        gateway_id: UUID,
        logs: List[TransactionalLog]
    ) -> List[Metrics]:
        """
        Aggregate transactional logs into metrics.
        
        Args:
            gateway_id: Gateway identifier
            logs: List of transactional logs to aggregate
            
        Returns:
            List of aggregated Metrics
        """
        # 1. Group logs by dimensions
        grouped = self._group_logs(logs, dimensions=[
            'gateway_id',
            'api_id',
            'application_id',
            'time_bucket'
        ])
        
        # 2. Calculate metrics for each group
        metrics = []
        for key, group_logs in grouped.items():
            metric = self._calculate_metrics(key, group_logs)
            metrics.append(metric)
        
        # 3. Store metrics in OpenSearch
        await self.metrics_repository.bulk_create(metrics)
        
        return metrics
    
    def _calculate_metrics(
        self,
        key: tuple,
        logs: List[TransactionalLog]
    ) -> Metrics:
        """Calculate aggregated metrics from logs."""
        gateway_id, api_id, app_id, time_bucket, timestamp = key
        
        # Count metrics
        request_count = len(logs)
        success_count = sum(1 for log in logs if log.status == EventStatus.SUCCESS)
        failure_count = request_count - success_count
        error_rate = (failure_count / request_count * 100) if request_count > 0 else 0
        
        # Response time metrics
        response_times = [log.total_time for log in logs]
        response_time_avg = statistics.mean(response_times)
        response_time_min = min(response_times)
        response_time_max = max(response_times)
        response_time_p50 = statistics.median(response_times)
        response_time_p95 = self._percentile(response_times, 0.95)
        response_time_p99 = self._percentile(response_times, 0.99)
        
        # Gateway & provider time
        gateway_times = [log.gateway_time for log in logs]
        provider_times = [log.provider_time for log in logs]
        gateway_time_avg = statistics.mean(gateway_times)
        provider_time_avg = statistics.mean(provider_times)
        
        # Throughput (requests per second)
        bucket_duration = self._get_bucket_duration(time_bucket)
        throughput = request_count / bucket_duration
        
        # Cache metrics
        cache_hits = sum(1 for log in logs if log.cached_response == CacheStatus.CACHED)
        cache_misses = request_count - cache_hits
        cache_hit_rate = (cache_hits / request_count * 100) if request_count > 0 else 0
        
        # HTTP status codes
        status_2xx = sum(1 for log in logs if log.response_code.startswith('2'))
        status_4xx = sum(1 for log in logs if log.response_code.startswith('4'))
        status_5xx = sum(1 for log in logs if log.response_code.startswith('5'))
        
        return Metrics(
            gateway_id=gateway_id,
            api_id=api_id,
            application_id=app_id,
            timestamp=timestamp,
            time_bucket=time_bucket,
            request_count=request_count,
            success_count=success_count,
            failure_count=failure_count,
            error_rate=error_rate,
            response_time_avg=response_time_avg,
            response_time_min=response_time_min,
            response_time_max=response_time_max,
            response_time_p50=response_time_p50,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p99,
            gateway_time_avg=gateway_time_avg,
            provider_time_avg=provider_time_avg,
            throughput=throughput,
            cache_hit_count=cache_hits,
            cache_miss_count=cache_misses,
            cache_hit_rate=cache_hit_rate,
            status_2xx_count=status_2xx,
            status_4xx_count=status_4xx,
            status_5xx_count=status_5xx,
        )
```

---

## Drill-Down Pattern

### Drill-Down Flow

Users can drill down from aggregated metrics to raw transactional logs:

```
┌─────────────────────────────────────────────────────────────┐
│                    Drill-Down Flow                           │
│                                                              │
│  Step 1: User views Metrics Dashboard                       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Frontend displays aggregated metrics chart         │    │
│  │  - Shows error rate spike at 10:30 AM              │    │
│  │  - User clicks on spike point                      │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  Step 2: Extract Drill-Down Dimensions                      │
│  ┌────────────────────────────────────────────────────┐    │
│  │  From clicked metric:                               │    │
│  │  - gateway_id: uuid-1                              │    │
│  │  - api_id: payment-api                             │    │
│  │  - timestamp: 2026-04-09T10:30:00Z                 │    │
│  │  - time_bucket: 5m                                 │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  Step 3: Query Raw Logs                                     │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Query OpenSearch transactional-logs index:         │    │
│  │  WHERE gateway_id = uuid-1                         │    │
│  │    AND api_id = payment-api                        │    │
│  │    AND timestamp >= 2026-04-09T10:30:00Z           │    │
│  │    AND timestamp < 2026-04-09T10:35:00Z            │    │
│  └────────────────────────────────────────────────────┘    │
│                          │                                   │
│                          ▼                                   │
│  Step 4: Display Raw Logs                                   │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Frontend shows list of TransactionalLog events:    │    │
│  │  - Request/response details                        │    │
│  │  - Error messages                                  │    │
│  │  - Timing breakdown                                │    │
│  │  - External calls                                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Drill-Down API

**Endpoint**: `GET /api/v1/metrics/{metric_id}/logs`

```python
@router.get("/metrics/{metric_id}/logs")
async def get_metric_logs(
    metric_id: UUID,
    limit: int = 100,
    offset: int = 0
) -> List[TransactionalLog]:
    """
    Get raw transactional logs for a specific metric.
    
    Args:
        metric_id: Metric identifier
        limit: Maximum number of logs to return
        offset: Offset for pagination
        
    Returns:
        List of TransactionalLog objects
    """
    # 1. Get metric
    metric = await metrics_repository.get(metric_id)
    
    # 2. Extract dimensions
    gateway_id = metric.gateway_id
    api_id = metric.api_id
    timestamp = metric.timestamp
    time_bucket = metric.time_bucket
    
    # 3. Calculate time range
    bucket_duration = get_bucket_duration(time_bucket)
    start_time = timestamp
    end_time = timestamp + bucket_duration
    
    # 4. Query raw logs
    logs = await log_repository.query(
        gateway_id=gateway_id,
        api_id=api_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset
    )
    
    return logs
```

---

## OpenSearch Indices

### Index Structure

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenSearch Indices                        │
│                                                              │
│  1. apis (Permanent)                                         │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - API definitions from all gateways                │    │
│  │  - Indexed by: gateway_id, api_id                  │    │
│  │  - Size: ~1MB per 100 APIs                         │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  2. transactional-logs-YYYY.MM.DD (90 days retention)       │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - Raw TransactionalLog events                      │    │
│  │  - Indexed by: gateway_id, api_id, timestamp       │    │
│  │  - Daily rollover                                   │    │
│  │  - Size: ~100MB per day (estimated)                │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  3. metrics-1m-YYYY.MM.DD (24 hours retention)              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - 1-minute aggregated metrics                      │    │
│  │  - Indexed by: gateway_id, api_id, timestamp       │    │
│  │  - Daily rollover                                   │    │
│  │  - Size: ~50MB per day (estimated)                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  4. metrics-5m-YYYY.MM.DD (7 days retention)                │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - 5-minute aggregated metrics                      │    │
│  │  - Indexed by: gateway_id, api_id, timestamp       │    │
│  │  - Daily rollover                                   │    │
│  │  - Size: ~10MB per day (estimated)                 │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  5. metrics-1h-YYYY.MM.DD (30 days retention)               │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - 1-hour aggregated metrics                        │    │
│  │  - Indexed by: gateway_id, api_id, timestamp       │    │
│  │  - Daily rollover                                   │    │
│  │  - Size: ~5MB per day (estimated)                  │    │
│  └────────────────────────────────────────────────────┘    │
│                                                              │
│  6. metrics-1d-YYYY.MM (90 days retention)                  │
│  ┌────────────────────────────────────────────────────┐    │
│  │  - 1-day aggregated metrics                         │    │
│  │  - Indexed by: gateway_id, api_id, timestamp       │    │
│  │  - Monthly rollover                                 │    │
│  │  - Size: ~1MB per month (estimated)                │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Index Mappings

**transactional-logs Index**:

```json
{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "gateway_id": {"type": "keyword"},
      "api_id": {"type": "keyword"},
      "api_name": {"type": "text"},
      "creation_date": {"type": "date", "format": "epoch_millis"},
      "total_time": {"type": "integer"},
      "provider_time": {"type": "integer"},
      "gateway_time": {"type": "integer"},
      "status": {"type": "keyword"},
      "response_code": {"type": "keyword"},
      "operation_name": {"type": "keyword"},
      "http_method": {"type": "keyword"},
      "application_id": {"type": "keyword"},
      "error_origin": {"type": "keyword"},
      "created_at": {"type": "date"}
    }
  }
}
```

**metrics Index**:

```json
{
  "mappings": {
    "properties": {
      "id": {"type": "keyword"},
      "gateway_id": {"type": "keyword"},
      "api_id": {"type": "keyword"},
      "application_id": {"type": "keyword"},
      "timestamp": {"type": "date"},
      "time_bucket": {"type": "keyword"},
      "request_count": {"type": "integer"},
      "error_rate": {"type": "float"},
      "response_time_avg": {"type": "float"},
      "response_time_p95": {"type": "float"},
      "response_time_p99": {"type": "float"},
      "throughput": {"type": "float"},
      "created_at": {"type": "date"}
    }
  }
}
```

---

## Integration Points

### 1. Gateway Adapter

**Location**: [`backend/app/adapters/native_gateway.py`](../backend/app/adapters/native_gateway.py) (to be enhanced)

```python
class NativeGatewayAdapter(GatewayAdapter):
    async def fetch_transactional_logs(
        self,
        since: datetime
    ) -> List[dict]:
        """
        Fetch transactional logs from WebMethods API Gateway.
        
        Args:
            since: Fetch logs since this timestamp
            
        Returns:
            List of raw log dictionaries
        """
        # Query gateway's transactional log API
        response = await self.client.get(
            f"{self.base_url}/rest/apigateway/analytics/transactionalEvents",
            params={
                "from": int(since.timestamp() * 1000),
                "to": int(datetime.utcnow().timestamp() * 1000)
            }
        )
        
        return response.json()["events"]
```

### 2. Metrics Repository

**Location**: [`backend/app/db/repositories/metrics_repository.py`](../backend/app/db/repositories/metrics_repository.py) (to be created)

```python
class MetricsRepository:
    async def bulk_create(self, metrics: List[Metrics]) -> None:
        """Bulk create metrics in OpenSearch."""
        pass
    
    async def query(
        self,
        gateway_id: UUID,
        api_id: str,
        start_time: datetime,
        end_time: datetime,
        time_bucket: str = "5m"
    ) -> List[Metrics]:
        """Query metrics by dimensions and time range."""
        pass
```

### 3. Log Repository

**Location**: [`backend/app/db/repositories/log_repository.py`](../backend/app/db/repositories/log_repository.py) (to be created)

```python
class TransactionalLogRepository:
    async def bulk_create(self, logs: List[TransactionalLog]) -> None:
        """Bulk create logs in OpenSearch."""
        pass
    
    async def query(
        self,
        gateway_id: UUID,
        api_id: str,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[TransactionalLog]:
        """Query logs by dimensions and time range."""
        pass
```

---

## Implementation Roadmap

### Phase 1: Data Models (✅ Complete)

- [x] Create [`TransactionalLog`](../backend/app/models/webmethods/wm_transaction.py:70) model
- [x] Create supporting enums and nested models
- [x] Keep [`API`](../backend/app/models/wm_api.py:385) model as-is
- [x] Export models in [`__init__.py`](../backend/app/models/__init__.py)

### Phase 2: Metrics Model (Next)

- [x] `Metrics` model already exists in [`metric.py`](../backend/app/models/base/metric.py)
- [ ] Define aggregation dimensions
- [ ] Add field for drill-down support

### Phase 3: Collection Pipeline

- [ ] Enhance [`MetricsService`](../backend/app/services/metrics_service.py) with `collect_transactional_logs()`
- [ ] Enhance [`NativeGatewayAdapter`](../backend/app/adapters/native_gateway.py) with `fetch_transactional_logs()`
- [ ] Create `TransactionalLogRepository`
- [ ] Add scheduler job for periodic collection

### Phase 4: Aggregation Service

- [ ] Create `AggregationService`
- [ ] Implement time-bucket aggregation logic
- [ ] Create `MetricsRepository`
- [ ] Add scheduler job for periodic aggregation

### Phase 5: Drill-Down API

- [ ] Add `/api/v1/metrics/{metric_id}/logs` endpoint
- [ ] Implement drill-down query logic
- [ ] Add pagination support

### Phase 6: Frontend Integration

- [ ] Add metrics dashboard with drill-down
- [ ] Display aggregated metrics charts
- [ ] Enable click-to-drill-down
- [ ] Show raw log details

### Phase 7: Multi-Gateway Support

- [ ] Test with multiple gateway instances
- [ ] Verify data segregation by `gateway_id`
- [ ] Add gateway selector in UI

---

## References

- [TransactionalLog Model (webMethods-specific)](../backend/app/models/webmethods/wm_transaction.py)
- [TransactionalLog Model (vendor-neutral)](../backend/app/models/base/transaction.py)
- [API Model (webMethods-specific)](../backend/app/models/webmethods/wm_api.py)
- [API Model (vendor-neutral)](../backend/app/models/base/api.py)
- [Metric Model (vendor-neutral)](../backend/app/models/base/metric.py)
- [Architecture Documentation](./architecture.md)
- [WebMethods API Gateway Documentation](https://documentation.softwareag.com/webmethods/api_gateway/)

---

**Document Status**: ✅ Complete  
**Next Steps**: Implement Metrics model and collection pipeline  
**Last Updated**: 2026-04-09