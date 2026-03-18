# Architecture Documentation: API Intelligence Plane

**Version**: 1.0.0  
**Last Updated**: 2026-03-12  
**Status**: Production Ready

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

API Intelligence Plane is an AI-driven API management platform that transforms API operations from reactive firefighting to proactive, autonomous management. The system uses a **microservices architecture** with clear separation between the core application and optional external agent integrations.

### Core Principles

- **Vendor-Neutral Design**: Support multiple API Gateway vendors through adapter pattern
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
| **Demo Gateway** | Native API Gateway implementation | Spring Boot 3.2, Java 17 | 8080 | Yes |
| **OpenSearch** | Data persistence, search, analytics | OpenSearch 2.11+ | 9200 | Yes |
| **LLM Providers** | AI-powered analysis and predictions | OpenAI, Anthropic, Azure | N/A | Optional |
| **MCP Servers** | Protocol adapters for external AI agents | FastMCP, Python 3.11+ | 8001-8004 | Optional |

**Note**: MCP servers are **optional** components that enable external AI agents (like Bob IDE or Claude Desktop) to interact with the platform. The core application (Frontend + Backend + Demo Gateway + OpenSearch) functions independently without MCP servers.

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

### 3. Demo Gateway (Spring Boot)

**Purpose**: Native API Gateway implementation for testing and demonstration

**Features**:
- API registration and routing
- Metrics collection and reporting
- Rate limiting enforcement
- OpenSearch integration for metrics storage

**Key Components**:
```java
com.example.gateway/
├── controller/
│   ├── APIController.java
│   ├── GatewayController.java
│   └── MetricsController.java
├── service/
│   ├── APIService.java
│   ├── MetricsService.java
│   └── RateLimitService.java
├── model/
│   ├── API.java
│   └── Policy.java
└── repository/
    └── APIRepository.java
```

### 4. OpenSearch (Data Store)

**Purpose**: Persistent storage for all system data

**Indices**:

| Index | Purpose | Retention |
|-------|---------|-----------|
| `api-inventory` | API catalog and metadata | Permanent |
| `gateway-registry` | Gateway configurations | Permanent |
| `api-metrics-*` | Time-series metrics data | 90 days |
| `api-predictions` | Failure predictions | 90 days |
| `security-findings` | Vulnerability scan results | 90 days |
| `optimization-recommendations` | Performance recommendations | 90 days |
| `rate-limit-policies` | Rate limiting policies | Permanent |
| `query-history` | Natural language query history | 30 days |

**Index Lifecycle Management**:
- Daily rollover for time-series indices
- Automatic deletion after retention period
- Snapshot backups every 24 hours

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

**Purpose**: Support multiple API Gateway vendors with consistent interface

```python
class GatewayAdapter(ABC):
    """Base strategy interface"""
    
    @abstractmethod
    async def discover_apis(self) -> List[API]:
        pass
    
    @abstractmethod
    async def collect_metrics(self, api_id: str) -> Metrics:
        pass

class NativeGatewayAdapter(GatewayAdapter):
    """Concrete strategy for Native Gateway"""
    
    async def discover_apis(self) -> List[API]:
        # Native Gateway specific implementation
        pass

class KongGatewayAdapter(GatewayAdapter):
    """Concrete strategy for Kong Gateway"""
    
    async def discover_apis(self) -> List[API]:
        # Kong specific implementation
        pass
```

**Benefits**:
- Easy to add new Gateway vendors
- Consistent interface across vendors
- Vendor-specific logic encapsulated

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
    """Metrics-specific repository"""
    
    async def get_time_series(
        self, 
        api_id: str, 
        start: datetime, 
        end: datetime
    ) -> List[Metric]:
        pass
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

1. **Kong Gateway**
   - Protocol: Kong Admin API
   - Status: Planned

2. **Apigee Gateway**
   - Protocol: Apigee Management API
   - Status: Planned

3. **AWS API Gateway**
   - Protocol: AWS SDK
   - Status: Future

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
