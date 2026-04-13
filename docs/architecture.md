# Architecture Documentation: API Intelligence Plane

**Version**: 2.0.0
**Last Updated**: 2026-04-11
**Status**: Production Ready - Vendor-Neutral Architecture

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Component Details](#component-details)
4. [Data Flow](#data-flow)
5. [Design Patterns](#design-patterns)
6. [Technology Stack](#technology-stack)
7. [Security Architecture](#security-architecture)
8. [Scalability & Performance](#scalability--performance)
9. [Integration Points](#integration-points)

---

## Overview

API Intelligence Plane is an AI-driven API management platform that transforms API operations from reactive firefighting to proactive, autonomous management. The system uses a **microservices architecture** with **vendor-neutral data models** and **vendor-specific gateway adapters**, ensuring consistent intelligence capabilities regardless of the underlying API Gateway vendor.

### Core Principles

- **Vendor-Neutral Architecture**: All data stored in vendor-neutral models (`API`, `Metric`, `TransactionalLog`) with vendor-specific fields in `vendor_metadata`
- **Adapter Pattern**: Gateway-specific adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter) transform vendor data to vendor-neutral models
- **Time-Bucketed Metrics**: Metrics stored separately from API entities in time-bucketed indices (1m, 5m, 1h, 1d) for efficient querying
- **Separated Intelligence**: Intelligence fields (`health_score`, `risk_score`, `security_score`) stored in `intelligence_metadata` wrapper
- **Model-Agnostic AI**: LiteLLM provides unified interface to multiple LLM providers
- **Single Source of Truth**: Backend services contain all business logic
- **Separation of Concerns**: Clear boundaries between discovery, monitoring, prediction, security, and optimization
- **Event-Driven Architecture**: Background schedulers for periodic data collection and analysis
- **External Agent Support**: Optional MCP servers for AI agent integration (Bob IDE, Claude Desktop, etc.)

---

## System Architecture

### High-Level Architecture

<img alt="image" src="./diagrams/APIIP-High-Level Architecture-Combined.drawio.png">

### Component Responsibilities

| Component | Responsibility | Technology | Port | Required |
|-----------|---------------|------------|------|----------|
| **Frontend** | User interface, visualization, interaction | React 18, TypeScript, Vite | 3000 | Yes |
| **Backend API** | Business logic, orchestration, data processing | FastAPI, Python 3.11+ | 8000 | Yes |
| **Gateway Integrations** | Vendor adapters for connected gateways, with webMethods as the current primary integration | Python adapters, vendor APIs | Varies | Yes |
| **OpenSearch** | Data persistence, search, analytics | OpenSearch 2.11+ | 9200 | Yes |
| **LLM Providers** | AI-powered analysis and predictions | OpenAI, Anthropic, Azure | N/A | Optional |
| **MCP Servers** | Protocol adapters for external AI agents | FastMCP, Python 3.11+ | 8001-8004 | Optional |

**Note**: MCP servers are **optional** components that enable external AI agents (like Bob IDE or Claude Desktop) to interact with the platform. The core application (Frontend + Backend + Gateway Integrations + OpenSearch) functions independently without MCP servers.

---

## Component Details

### 1. Frontend (React SPA)

**Purpose**: User interface for API intelligence visualization and interaction

**Key Features**:
- Dashboard with real-time metrics
- API inventory and health monitoring
- Predictive failure alerts
- Security vulnerability tracking
- Performance optimization recommendations
- Natural language query interface

**Technology Stack**:
- React 18.2+ with TypeScript
- Vite 5.0+ for build tooling
- React Router 6.20+ for navigation
- TanStack Query 5.14+ for server state management
- Recharts 2.10+ for data visualization
- Tailwind CSS 3.4+ for styling
- Axios for HTTP client

**Key Components**:
```
src/
├── pages/           # Route-level components
│   ├── Dashboard.tsx
│   ├── APIs.tsx
│   ├── Gateways.tsx
│   ├── Predictions.tsx
│   ├── Optimization.tsx
│   └── Query.tsx
├── components/      # Reusable UI components
│   ├── metrics/
│   ├── predictions/
│   └── common/
├── services/        # API client services
│   ├── api.ts
│   ├── gateway.ts
│   └── metrics.ts
└── hooks/          # Custom React hooks
    ├── useQuerySession.ts
    └── useRealtimeMetrics.ts
```

### 2. Backend API (FastAPI)

**Purpose**: Core business logic, orchestration, and data processing

**Architecture Layers**:

<img alt="image" src="./diagrams/APIIP-Backend Architecture Layers.drawio.png" width="400px">

**Key Services**:

| Service | Purpose | Key Methods |
|---------|---------|-------------|
| `DiscoveryService` | API discovery and inventory management | `discover_apis()`, `detect_shadow_apis()` |
| `MetricsService` | Metrics collection and aggregation | `collect_metrics()`, `aggregate_metrics()` |
| `PredictionService` | Failure prediction and analysis | `generate_predictions()`, `analyze_trends()` |
| `OptimizationService` | Performance optimization recommendations | `generate_recommendations()`, `analyze_performance()` |
| `QueryService` | Natural language query processing | `process_query()`, `generate_response()` |
| `RateLimitService` | Rate limit policy management | `apply_policy()`, `adjust_limits()` |

**Background Schedulers**:
- Discovery jobs: Every 5 minutes
- Metrics collection: Every 1 minute
- Prediction generation: Every 15 minutes
- Security scans: Every 1 hour
- Optimization analysis: Every 30 minutes

### 3. Gateway Integration Layer

**Purpose**: Provide a vendor-neutral ingestion and normalization layer for external API gateways through the adapter pattern.

**Architecture**: Strategy Pattern with Vendor-Specific Adapters

```
┌─────────────────────────────────────────────────────────────┐
│                    Backend Services                          │
│  (Discovery, Metrics, Prediction, Security, Optimization)   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Vendor-Neutral Data Models                      │
│  • API (base/api.py)                                        │
│  • Metric (base/metric.py) - Time-bucketed                  │
│  • TransactionalLog (base/transaction.py)                   │
│  • PolicyAction (base/api.py)                               │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Gateway Adapters                            │
│  ┌──────────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ WebMethods       │  │ Kong         │  │ Apigee       │  │
│  │ Adapter          │  │ Adapter      │  │ Adapter      │  │
│  │ (IMPLEMENTED)    │  │ (PLANNED)    │  │ (PLANNED)    │  │
│  └──────────────────┘  └──────────────┘  └──────────────┘  │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Vendor-Specific Models                          │
│  • webmethods/wm_api.py (480 lines)                         │
│  • webmethods/wm_policy.py (271 lines)                      │
│  • webmethods/wm_policy_action.py (1184 lines)              │
│  • webmethods/wm_transaction.py (264 lines)                 │
└─────────────────────────────────────────────────────────────┘
```

**Current Implementation Status**:
- ✅ **WebMethodsGatewayAdapter**: Fully implemented for discovery, policies, analytics, and metrics
- 🔜 **KongGatewayAdapter**: Planned for future release
- 🔜 **ApigeeGatewayAdapter**: Planned for future release

**Vendor-Neutral Data Models**:

1. **API Model** (`backend/app/models/base/api.py`):
   - Comprehensive structure with `policy_actions`, `api_definition`, `endpoints`, `version_info`
   - Intelligence fields in `intelligence_metadata` wrapper (`health_score`, `is_shadow`, `risk_score`, `security_score`)
   - Vendor-specific fields in `vendor_metadata` dict
   - **Does NOT include** embedded metrics (stored separately)

2. **Metric Model** (`backend/app/models/base/metric.py`):
   - Time-bucketed structure (1m, 5m, 1h, 1d)
   - `gateway_id` dimension for multi-gateway support
   - Cache metrics (`cache_hit_count`, `cache_miss_count`, `cache_hit_rate`)
   - Timing breakdown (`gateway_time_avg`, `backend_time_avg`)
   - HTTP status code breakdown (2xx/3xx/4xx/5xx)
   - Optional per-endpoint breakdown
   - Stored separately from API entities in time-bucketed OpenSearch indices

3. **TransactionalLog Model** (`backend/app/models/base/transaction.py`):
   - Comprehensive fields for timing, request/response, client info
   - Caching details, backend service information
   - Error tracking and external call details
   - Vendor-specific fields in `vendor_metadata`

4. **PolicyAction Model** (`backend/app/models/base/api.py`):
   - Vendor-neutral policy types (AUTHENTICATION, AUTHORIZATION, TLS, CORS, VALIDATION, etc.)
   - `vendor_config` dict for vendor-specific configuration
   - Stage-based execution (request, routing, response)

**Adapter Responsibilities**:

Each adapter implements the following transformations:

1. **API Transformation**: Vendor API → Vendor-Neutral API
   - Map vendor-specific fields to standard fields
   - Store vendor-specific data in `vendor_metadata`
   - Populate `intelligence_metadata` with discovery info

2. **Policy Transformation**: Vendor Policy → PolicyAction
   - Map vendor policy types to standard `PolicyActionType` enum
   - Extract configuration to `vendor_config`

3. **Transaction Transformation**: Vendor Log → TransactionalLog
   - Extract timing metrics, error info, cache metrics
   - Normalize field names and structures

4. **Metric Aggregation**: TransactionalLog → Metric
   - Aggregate by time bucket, gateway, API, application
   - Calculate percentiles, error rates, cache metrics

5. **Reverse Transformation**: PolicyAction → Vendor Format
   - For policy enforcement and updates
   - Map standard types back to vendor-specific format

**WebMethods Integration Details**:

- **API Discovery**: `GET /rest/apigateway/apis` and `GET /rest/apigateway/apis/{api_id}`
- **Policy Management**: `GET /rest/apigateway/policies/{policy_id}` and `PUT /rest/apigateway/policies/{policy_id}`
- **Policy Actions**: `GET /rest/apigateway/policyActions/{policyaction_id}` and `POST /rest/apigateway/policyActions`
- **Transactional Logs**: OpenSearch query with filter `eventType: "Transactional"`
- **Policy Stages**: Multi-stage pipeline (transport, requestPayloadProcessing, IAM, LMT, routing, responseProcessing)

**Benefits of Vendor-Neutral Architecture**:
- Consistent intelligence capabilities across all gateway vendors
- Easy addition of new gateway vendors through adapter implementation
- Vendor-agnostic frontend and business logic
- Simplified testing with mock adapters
- Future-proof against vendor API changes

### 4. OpenSearch (Data Store)

**Purpose**: Persistent storage for all system data

**Indices**:

| Index Pattern | Purpose | Retention | Rollover |
|---------------|---------|-----------|----------|
| `api-inventory` | API catalog and metadata (vendor-neutral) | Permanent | N/A |
| `gateway-registry` | Gateway configurations | Permanent | N/A |
| `api-metrics-1m-{YYYY.MM}` | 1-minute time-bucketed metrics | 24 hours | Monthly |
| `api-metrics-5m-{YYYY.MM}` | 5-minute time-bucketed metrics | 7 days | Monthly |
| `api-metrics-1h-{YYYY.MM}` | 1-hour time-bucketed metrics | 30 days | Monthly |
| `api-metrics-1d-{YYYY.MM}` | 1-day time-bucketed metrics | 90 days | Monthly |
| `transactional-logs-{YYYY.MM}` | Raw transactional events | 7 days | Monthly |
| `api-predictions` | Failure predictions | 90 days | N/A |
| `security-findings` | Vulnerability scan results | 90 days | N/A |
| `compliance-violations` | Compliance violations | 90 days | N/A |
| `optimization-recommendations` | Performance recommendations | 90 days | N/A |
| `rate-limit-policies` | Rate limiting policies | Permanent | N/A |
| `query-history` | Natural language query history | 30 days | N/A |

**Time-Bucketed Metrics Architecture**:
- Metrics stored separately from API entities for efficient querying
- Four time bucket sizes (1m, 5m, 1h, 1d) for different query patterns
- Automatic aggregation from raw transactional logs
- Monthly index rotation with automatic retention cleanup
- Drill-down pattern: Aggregated metrics → Raw transactional logs

**Index Lifecycle Management**:
- Monthly rollover for time-series indices
- Automatic deletion after retention period
- Snapshot backups every 24 hours
- Index templates for consistent mapping across time periods

### 5. MCP Servers (Optional - External Agent Integration)

**Purpose**: Enable external AI agents (Bob IDE, Claude Desktop, etc.) to interact with the platform

**Important**: MCP servers are **NOT** part of the core application flow. They are optional protocol adapters that:
- Expose backend functionality to external AI agents
- Use the MCP (Model Context Protocol) for communication
- Delegate all business logic to the backend API
- Are only needed when integrating with AI development tools

**Architecture Pattern**: Thin Wrapper
- MCP servers are thin protocol adapters
- All business logic remains in the backend API
- MCP servers only handle protocol translation

**Available Servers** (when needed):

| Server | Port | Purpose | Tools Exposed |
|--------|------|---------|---------------|
| Discovery | 8001 | API discovery operations | `discover_apis`, `list_shadow_apis` |
| Metrics | 8002 | Metrics collection | `collect_metrics`, `get_health_status` |
| Optimization | 8004 | Performance optimization | `generate_recommendations`, `analyze_performance` |

**Transport**: Streamable HTTP (FastMCP)

**Example Tool Implementation**:
```python
@mcp.tool()
async def discover_apis(gateway_id: str) -> dict:
    """Thin wrapper - delegates to backend service"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BACKEND_URL}/api/v1/discovery/discover",
            json={"gateway_id": gateway_id}
        )
        return response.json()
```

**Use Cases**:
- AI-assisted API management from Bob IDE
- Automated operations via Claude Desktop
- Custom AI agent integrations
- Development workflow automation

**Not Required For**:
- Core application functionality
- Frontend user interface
- Backend operations
- Standard API management tasks

---

## Data Flow

### 1. Core Application Flow (Frontend → Backend → Gateway)

<img alt="image" src="./diagrams/APIIP-Core Application Data Flow.drawio.png" width="500px">

### 2. Optional External Agent Flow (AI Agents → MCP → Backend)

<img alt="image" src="./diagrams/APIIP-External Agent Flow.drawio.png" width="250px">

### 3. API Discovery Flow

<img alt="image" src="./diagrams/APIIP-API Discovery Flow.drawio.png" width="300px">

### 4. Prediction Generation Flow

<img alt="image" src="./diagrams/APIIP-Prediction Generation Flow.drawio.png" width="300px">

### 5. Natural Language Query Flow

<img alt="image" src="./diagrams/APIIP-Natural Language Query Flow.drawio.png" width="300px">

---

## Design Patterns

### 1. Strategy Pattern (Gateway Adapters)

**Purpose**: Support multiple API Gateway vendors with consistent vendor-neutral interface

```python
from abc import ABC, abstractmethod
from typing import List, Any
from app.models.base.api import API, PolicyAction
from app.models.base.metric import Metric
from app.models.base.transaction import TransactionalLog

class GatewayAdapter(ABC):
    """Base strategy interface for vendor-neutral gateway integration"""
    
    @abstractmethod
    async def discover_apis(self) -> List[API]:
        """Discover APIs and transform to vendor-neutral API model"""
        pass
    
    @abstractmethod
    async def collect_transactional_logs(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> List[TransactionalLog]:
        """Collect raw transactional logs in vendor-neutral format"""
        pass
    
    @abstractmethod
    def _transform_to_api(self, vendor_data: Any) -> API:
        """Transform vendor-specific API data to vendor-neutral API"""
        pass
    
    @abstractmethod
    def _transform_to_metric(self, vendor_data: Any) -> Metric:
        """Transform vendor-specific metrics to vendor-neutral Metric"""
        pass
    
    @abstractmethod
    def _transform_to_transactional_log(self, vendor_data: Any) -> TransactionalLog:
        """Transform vendor-specific log to vendor-neutral TransactionalLog"""
        pass
    
    @abstractmethod
    def _transform_to_policy_action(self, vendor_data: Any) -> PolicyAction:
        """Transform vendor-specific policy to vendor-neutral PolicyAction"""
        pass
    
    @abstractmethod
    def _transform_from_policy_action(self, policy_action: PolicyAction) -> Any:
        """Transform vendor-neutral PolicyAction to vendor-specific format"""
        pass

class WebMethodsGatewayAdapter(GatewayAdapter):
    """Concrete strategy for webMethods API Gateway"""
    
    async def discover_apis(self) -> List[API]:
        # Fetch from webMethods REST API
        wm_apis = await self._fetch_webmethods_apis()
        # Transform to vendor-neutral API model
        return [self._transform_to_api(wm_api) for wm_api in wm_apis]
    
    def _transform_to_api(self, wm_api: WMApi) -> API:
        # Map webMethods fields to vendor-neutral API
        # Store webMethods-specific fields in vendor_metadata
        return API(
            name=wm_api.apiName,
            version_info={"version": wm_api.apiVersion},
            policy_actions=[
                self._transform_to_policy_action(p)
                for p in wm_api.policies
            ],
            intelligence_metadata={
                "discovery_method": "registered",
                "health_score": 100.0
            },
            vendor_metadata={
                "vendor": "webmethods",
                "maturity_state": wm_api.maturityState,
                "owner": wm_api.owner
            }
        )

class KongGatewayAdapter(GatewayAdapter):
    """Concrete strategy for Kong Gateway (Planned)"""
    
    async def discover_apis(self) -> List[API]:
        # Kong-specific implementation
        pass

class ApigeeGatewayAdapter(GatewayAdapter):
    """Concrete strategy for Apigee Gateway (Planned)"""
    
    async def discover_apis(self) -> List[API]:
        # Apigee-specific implementation
        pass
```

**Benefits**:
- Easy to add new Gateway vendors through adapter implementation
- Consistent vendor-neutral interface across all vendors
- Vendor-specific logic encapsulated in adapters
- Vendor-specific fields preserved in `vendor_metadata`
- Business logic remains vendor-agnostic

### 2. Repository Pattern (Data Access)

**Purpose**: Abstract data access logic from business logic

```python
class BaseRepository(ABC):
    """Base repository with common CRUD operations"""
    
    async def create(self, entity: BaseModel) -> str:
        pass
    
    async def get(self, id: str) -> Optional[BaseModel]:
        pass
    
    async def update(self, id: str, entity: BaseModel) -> bool:
        pass
    
    async def delete(self, id: str) -> bool:
        pass

class MetricsRepository(BaseRepository):
    """Metrics-specific repository with time-bucketed queries"""
    
    async def get_time_series(
        self,
        api_id: str,
        start: datetime,
        end: datetime,
        time_bucket: str = "5m"
    ) -> List[Metric]:
        """Query time-bucketed metrics from appropriate index"""
        index = self._get_index_for_bucket(time_bucket)
        # Query from time-bucketed index
        pass
    
    def _get_index_for_bucket(self, time_bucket: str) -> str:
        """Select appropriate index based on time bucket"""
        bucket_to_index = {
            "1m": "api-metrics-1m-*",
            "5m": "api-metrics-5m-*",
            "1h": "api-metrics-1h-*",
            "1d": "api-metrics-1d-*"
        }
        return bucket_to_index.get(time_bucket, "api-metrics-5m-*")
```

### 3. Agent Pattern (AI Workflows)

**Purpose**: Encapsulate AI-powered analysis workflows

```python
class PredictionAgent:
    """LangGraph-based prediction agent"""
    
    def __init__(self, llm_service: LLMService):
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> StateGraph:
        workflow = StateGraph(PredictionState)
        workflow.add_node("analyze_trends", self._analyze_trends)
        workflow.add_node("generate_prediction", self._generate_prediction)
        workflow.add_node("explain_reasoning", self._explain_reasoning)
        # ... workflow definition
        return workflow.compile()
    
    async def predict(self, metrics: List[Metric]) -> Prediction:
        result = await self.workflow.ainvoke({
            "metrics": metrics
        })
        return result["prediction"]
```

### 4. Dependency Injection

**Purpose**: Manage component dependencies and enable testing

```python
# FastAPI dependency injection
async def get_opensearch_client() -> OpenSearchClient:
    return OpenSearchClient(settings.opensearch_host)

async def get_discovery_service(
    client: OpenSearchClient = Depends(get_opensearch_client)
) -> DiscoveryService:
    return DiscoveryService(client)

# Usage in endpoint
@router.post("/discover")
async def discover_apis(
    service: DiscoveryService = Depends(get_discovery_service)
):
    return await service.discover_apis()
```

---

## Technology Stack

### Backend
- **Framework**: FastAPI 0.109+
- **AI/ML**: LangChain 0.1+, LangGraph 0.0.20+, LiteLLM 1.17+
- **MCP** (Optional): FastMCP 0.1+
- **Database**: OpenSearch Python Client 2.4+
- **Scheduling**: APScheduler 3.10+
- **Testing**: pytest 7.4+, pytest-asyncio 0.21+
- **Code Quality**: Black, isort, flake8, mypy

### Frontend
- **Framework**: React 18.2+, Vite 5.0+
- **Routing**: React Router 6.20+
- **State Management**: TanStack Query 5.14+
- **UI Components**: Tailwind CSS 3.4+
- **Charts**: Recharts 2.10+
- **HTTP Client**: Axios 1.6+
- **Code Quality**: ESLint 8.56+, Prettier 3.1+, TypeScript 5.3+

### Demo Gateway
- **Framework**: Spring Boot 3.2+
- **Database**: OpenSearch Java Client 2.8+
- **Metrics**: Micrometer 1.12+
- **Build Tool**: Maven 3.9+
- **Testing**: JUnit 5.10+

### Infrastructure
- **Container**: Docker 24+, Docker Compose 2.23+
- **Orchestration**: Kubernetes 1.28+
- **Storage**: OpenSearch 2.11+
- **Monitoring**: Prometheus, Grafana

---

## Security Architecture

### Encryption

**In Transit**:
- TLS 1.3 for all HTTP communications
- Certificate-based authentication between services
- Mutual TLS (mTLS) for service-to-service communication

**At Rest**:
- OpenSearch encryption at rest enabled
- Encrypted environment variables for secrets
- No hardcoded credentials in source code

### Compliance

**FedRAMP 140-3**:
- NIST-approved cryptographic algorithms
- FIPS 140-3 compliant cryptography module
- Audit logging for all operations
- Encryption key management

### Authentication & Authorization

**MVP**: No authentication required (development only)

**Production** (Future):
- OAuth 2.0 / OpenID Connect
- Role-based access control (RBAC)
- API key management
- JWT token validation

### Audit Logging

All operations are logged with:
- User identity (when auth enabled)
- Timestamp
- Operation type
- Resource affected
- Result (success/failure)
- IP address

---

## Scalability & Performance

### Performance Targets

| Metric | Target | Current |
|--------|--------|---------|
| Query latency | <5 seconds | ~3 seconds |
| Discovery cycle | <5 minutes | ~3 minutes |
| Security scan | <1 hour | ~45 minutes |
| API support | 1000+ APIs | Tested with 1000+ |
| Concurrent requests | Millions/minute | Not yet tested |
| Data retention | 90 days | Configured |

### Scalability Strategies

**Horizontal Scaling**:
- Stateless backend services (scale with replicas)
- Load balancing across backend instances
- OpenSearch cluster for distributed storage

**Vertical Scaling**:
- Increase resources for compute-intensive operations
- Optimize LLM token usage
- Cache frequently accessed data

**Caching**:
- Redis for session data (future)
- In-memory caching for static data
- OpenSearch query result caching

**Async Processing**:
- Background schedulers for periodic tasks
- Async/await for I/O operations
- Message queue for long-running tasks (future)

---

## Integration Points

### Core Application Integrations

1. **Frontend ↔ Backend**
   - Protocol: REST API (JSON)
   - Authentication: None (MVP)
   - Transport: HTTP/HTTPS
   - Purpose: User interface interactions

2. **Backend ↔ OpenSearch**
   - Protocol: OpenSearch REST API
   - Authentication: Basic auth
   - Transport: HTTP/HTTPS
   - Purpose: Data persistence and search

3. **Backend ↔ Demo Gateway**
   - Protocol: REST API (JSON)
   - Authentication: None (MVP)
   - Transport: HTTP/HTTPS
   - Purpose: API discovery and metrics collection

4. **Backend ↔ LLM Providers**
   - Protocol: HTTP/REST via LiteLLM
   - Authentication: API keys
   - Transport: HTTPS
   - Purpose: AI-powered predictions and optimizations

### Optional External Integrations

1. **AI Agents ↔ MCP Servers**
   - Protocol: MCP over Streamable HTTP
   - Authentication: None (MVP)
   - Transport: HTTP/HTTPS
   - Purpose: External AI agent access
   - Examples: Bob IDE, Claude Desktop

2. **MCP Servers ↔ Backend**
   - Protocol: HTTP REST API
   - Authentication: None (MVP)
   - Transport: HTTP/HTTPS
   - Purpose: Delegate operations to backend

### Future Gateway Integrations

All future gateway integrations will follow the adapter pattern with vendor-neutral data models:

1. **Kong Gateway**
   - Protocol: Kong Admin API
   - Status: Planned
   - Adapter: `KongGatewayAdapter` (to be implemented)
   - Transformation: Kong entities → Vendor-neutral API/Metric/TransactionalLog

2. **Apigee Gateway**
   - Protocol: Apigee Management API
   - Status: Planned
   - Adapter: `ApigeeGatewayAdapter` (to be implemented)
   - Transformation: Apigee proxies → Vendor-neutral API/Metric/TransactionalLog

3. **AWS API Gateway**
   - Protocol: AWS SDK
   - Status: Future
   - Adapter: `AWSGatewayAdapter` (to be implemented)
   - Transformation: AWS API Gateway resources → Vendor-neutral models

4. **Azure API Management**
   - Protocol: Azure Management API
   - Status: Future
   - Adapter: `AzureGatewayAdapter` (to be implemented)

**Adapter Implementation Guide**:
1. Create vendor-specific models in `backend/app/models/{vendor}/`
2. Implement adapter in `backend/app/adapters/{vendor}_gateway.py`
3. Implement transformation methods for all vendor-neutral models
4. Add vendor to `GatewayVendor` enum
5. Register adapter in `AdapterFactory`
6. Add integration tests

---

## Deployment Architecture

### Development Environment

```
Docker Compose (Core Application)
├── opensearch (9200)
├── backend (8000)
├── frontend (3000)
└── demo-gateway (8080)

Optional (for AI agent integration):
├── mcp-discovery (8001)
├── mcp-metrics (8002)
└── mcp-optimization (8004)
```

### Production Environment (Kubernetes)

```
Kubernetes Cluster
├── Namespace: api-intelligence-plane
│   ├── Deployment: backend (3 replicas)
│   ├── Deployment: frontend (2 replicas)
│   ├── Deployment: demo-gateway (2 replicas)
│   ├── StatefulSet: opensearch (3 nodes)
│   ├── Service: backend-service
│   ├── Service: frontend-service
│   ├── Service: opensearch-service
│   ├── Ingress: api-intelligence-ingress
│   └── ConfigMap: app-config
│
│   Optional (for AI agent integration):
│   └── Deployment: mcp-servers (1 replica each)
│
└── Monitoring
    ├── Prometheus
    └── Grafana
```

---

## Future Enhancements

1. **Authentication & Authorization**
   - OAuth 2.0 / OpenID Connect integration
   - Role-based access control
   - API key management

2. **Multi-Tenancy**
   - Tenant isolation
   - Resource quotas
   - Billing integration

3. **Advanced Analytics**
   - Machine learning model training
   - Anomaly detection improvements
   - Cost optimization recommendations

4. **Additional Gateway Support**
   - AWS API Gateway
   - Azure API Management
   - Google Cloud API Gateway

5. **Enhanced Monitoring**
   - Distributed tracing (OpenTelemetry)
   - Advanced alerting rules
   - Custom dashboards

---

## References

- [API Reference](./api-reference.md)
- [Deployment Guide](./deployment.md)
- [Contributing Guidelines](./contributing.md)
- [MCP Architecture](./mcp-architecture.md) - For external AI agent integration
- [AI Setup Guide](./ai-setup.md)
