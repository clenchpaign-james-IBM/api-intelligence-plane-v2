# Engineering Overview: API Intelligence Plane

**Version**: 1.0.0  
**Last Updated**: 2026-03-12  
**Status**: Production Ready

---

## 1. Product Overview

### What It Is

**API Intelligence Plane** is an AI-driven API management platform that transforms API operations from reactive firefighting to proactive, autonomous management. It acts as an intelligent companion layer that sits alongside existing API Gateways, providing continuous monitoring, predictive analytics, and automated optimization.

### Who It's For

- **Platform Engineers**: Managing large-scale API infrastructures
- **DevOps Teams**: Monitoring API health and performance
- **Security Teams**: Tracking vulnerabilities and compliance
- **API Product Managers**: Understanding API usage and optimization opportunities
- **AI/ML Engineers**: Integrating intelligent API management into development workflows

### Top Capabilities

1. **Autonomous API Discovery** - Automatically discovers all APIs including shadow/undocumented APIs across connected gateways
2. **Predictive Health Management** - Provides 24-48 hour advance failure predictions with AI-powered trend analysis
3. **Continuous Security Scanning** - Automated vulnerability detection with remediation recommendations
4. **Real-time Performance Optimization** - AI-driven performance recommendations with impact analysis
5. **Intelligent Rate Limiting** - Adaptive rate limiting based on usage patterns and consumer tiers
6. **Natural Language Query Interface** - Query API intelligence using conversational language
7. **Multi-Gateway Support** - Vendor-neutral design supporting Native, Kong, Apigee, and other gateways
8. **AI Agent Integration** - Optional MCP protocol support for external AI tools (Bob IDE, Claude Desktop)

---

## 2. Architecture at a Glance

### Main Components

The system follows a **microservices architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│  Frontend (React SPA)                                    │
│  - Dashboard, API Management, Query Interface            │
│  - Port: 3000                                            │
└────────────────────┬────────────────────────────────────┘
                     │ REST API (JSON)
┌────────────────────▼────────────────────────────────────┐
│  Backend API (FastAPI)                                   │
│  - Discovery, Metrics, Predictions, Security             │
│  - AI Agents (LangChain/LangGraph)                       │
│  - Gateway Adapters (Strategy Pattern)                   │
│  - Port: 8000                                            │
└────┬──────────────┬──────────────┬──────────────────────┘
     │              │              │
     ▼              ▼              ▼
┌─────────┐  ┌──────────┐  ┌──────────────┐
│OpenSearch│ │LLM Providers│ │Gateway  │
│Port: 9200│ │(via LiteLLM)│ │(Spring Boot) │
└─────────┘  └──────────┘  │Port: 8080    │
                            └──────────────┘

OPTIONAL: External AI Agent Integration
┌─────────────────────────────────────────────────────────┐
│  MCP Servers (Thin Protocol Adapters)                    │
│  - Discovery (8001), Metrics (8002), Optimization (8004) │
│  - Used by: Bob IDE, Claude Desktop, Custom AI Agents    │
└─────────────────────────────────────────────────────────┘
```

### How They Connect

**Core Application Flow**:
1. **Frontend** communicates with **Backend API** via REST endpoints
2. **Backend API** orchestrates all business logic, using:
   - **OpenSearch** for data persistence and search
   - **LLM Providers** (OpenAI, Anthropic, Azure) for AI-powered analysis
   - **Gateway** for API discovery and metrics collection
3. **Background Schedulers** run periodic jobs (discovery, metrics, predictions)
4. **Gateway Adapters** provide vendor-neutral interface to multiple gateway types

**Optional AI Agent Flow** (when MCP servers are enabled):
1. **AI Agents** (Bob IDE, Claude Desktop) connect to **MCP Servers** via MCP protocol
2. **MCP Servers** act as thin wrappers, delegating all operations to **Backend API**
3. This enables AI-assisted API management without modifying core application

### Key Design Principles

- **Single Source of Truth**: All business logic resides in Backend API
- **Vendor-Neutral**: Gateway adapters support multiple vendors (Strategy pattern)
- **Model-Agnostic**: LiteLLM provides unified interface to any LLM provider
- **Event-Driven**: Background schedulers for autonomous operations
- **Separation of Concerns**: Clear boundaries between discovery, monitoring, prediction, security, optimization

---

## 3. Key Flows

### Flow 1: User Views Dashboard

**Purpose**: User accesses the dashboard to view API health and metrics

**Steps**:
1. User navigates to frontend (http://localhost:3000)
2. Frontend fetches dashboard data from Backend API (`GET /api/v1/apis`, `/metrics`)
3. Backend queries OpenSearch for latest API inventory and metrics
4. Frontend renders dashboard with real-time visualizations (Recharts)

**Components**: Frontend → Backend API → OpenSearch

---

### Flow 2: Autonomous API Discovery

**Purpose**: System automatically discovers APIs from connected gateways

**Steps**:
1. **Scheduler** triggers discovery job (every 5 minutes)
2. **DiscoveryService** queries all registered gateways
3. **Gateway Adapter** (strategy pattern) connects to specific gateway type
4. Adapter retrieves API list and metadata from gateway
5. **DiscoveryService** compares with existing inventory, identifies:
   - New APIs (not in inventory)
   - Shadow APIs (undocumented/unregistered)
   - Changed APIs (metadata updates)
6. Results stored in OpenSearch `api-inventory` index
7. Frontend displays updated inventory automatically

**Components**: Scheduler → DiscoveryService → Gateway Adapter → Gateway → OpenSearch

---

### Flow 3: Predictive Failure Analysis

**Purpose**: Generate 24-48 hour advance failure predictions using AI

**Steps**:
1. **Scheduler** triggers prediction job (every 15 minutes)
2. **PredictionService** fetches recent metrics from OpenSearch
3. **PredictionAgent** (LangGraph workflow) analyzes metrics:
   - Detects anomalies and trends
   - Identifies contributing factors
   - Generates failure probability
4. **LLM Service** (via LiteLLM) provides AI-enhanced explanations
5. Predictions stored in OpenSearch `api-predictions` index
6. Frontend displays alerts with timeline and recommended actions

**Components**: Scheduler → PredictionService → PredictionAgent → LLM Service → OpenSearch → Frontend

---

### Flow 4: Natural Language Query

**Purpose**: User queries API intelligence using conversational language

**Steps**:
1. User enters query in frontend (e.g., "Show me APIs with high latency")
2. Frontend sends query to Backend API (`POST /api/v1/query`)
3. **QueryService** processes query:
   - Classifies query type (status, trend, prediction, security, performance)
   - Extracts entities (API names, metrics, time ranges)
4. **Query Agent** (LangChain) plans execution:
   - Generates OpenSearch queries
   - Aggregates data from multiple indices
5. **Response Generator** formats results with context
6. Frontend displays response with visualizations

**Components**: Frontend → QueryService → Query Agent → OpenSearch → Frontend

---

### Flow 5: Performance Optimization

**Purpose**: Generate AI-powered performance recommendations

**Steps**:
1. **Scheduler** triggers optimization job (every 30 minutes)
2. **OptimizationService** analyzes API performance metrics
3. **OptimizationAgent** (LangGraph) identifies bottlenecks:
   - High latency patterns
   - Resource inefficiencies
   - Configuration issues
4. **LLM Service** generates detailed recommendations with:
   - Estimated impact (% improvement)
   - Implementation steps
   - Priority ranking
5. Recommendations stored in OpenSearch `optimization-recommendations` index
6. Frontend displays actionable recommendations

**Components**: Scheduler → OptimizationService → OptimizationAgent → LLM Service → OpenSearch → Frontend

---

### Flow 6: Rate Limit Policy Application

**Purpose**: Apply intelligent rate limiting to APIs

**Steps**:
1. User creates/updates rate limit policy in frontend
2. Frontend sends policy to Backend API (`POST /api/v1/rate-limits`)
3. **RateLimitService** validates and stores policy in OpenSearch
4. Service pushes policy to **Gateway** via REST API
5. Gateway enforces rate limits on incoming requests
6. Metrics collected and analyzed for policy effectiveness
7. System can auto-adjust limits based on usage patterns

**Components**: Frontend → RateLimitService → OpenSearch → Gateway

---

## 4. Data & Integrations

### Data Storage (OpenSearch)

All system data is stored in OpenSearch with the following indices:

| Index | Purpose | Retention | Size Estimate |
|-------|---------|-----------|---------------|
| `api-inventory` | API catalog and metadata | Permanent | ~1MB per 100 APIs |
| `gateway-registry` | Gateway configurations | Permanent | ~10KB per gateway |
| `api-metrics-*` | Time-series metrics (daily rollover) | 90 days | ~100MB per day |
| `api-predictions` | Failure predictions | 90 days | ~10MB per day |
| `security-findings` | Vulnerability scan results | 90 days | ~50MB per day |
| `optimization-recommendations` | Performance recommendations | 90 days | ~5MB per day |
| `rate-limit-policies` | Rate limiting policies | Permanent | ~1MB total |
| `query-history` | Natural language query history | 30 days | ~10MB per day |

**Index Lifecycle**: Daily rollover for time-series data, automatic deletion after retention period, snapshot backups every 24 hours.

---

### External Systems & APIs

#### Core Integrations (Required)

1. **OpenSearch** (Port 9200)
   - **Purpose**: Primary data store for all system data
   - **Protocol**: HTTP REST API
   - **Authentication**: Basic auth (configurable)
   - **Usage**: Data persistence, search, aggregations, time-series analysis

2. **Gateway** (Port 8080)
   - **Purpose**: Native API Gateway implementation for testing
   - **Protocol**: HTTP REST API
   - **Technology**: Spring Boot 3.2, Java 17
   - **Usage**: API registration, metrics collection, rate limit enforcement

3. **LLM Providers** (via LiteLLM)
   - **Purpose**: AI-powered predictions and recommendations
   - **Supported**: OpenAI, Anthropic, Azure OpenAI, Ollama, etc.
   - **Protocol**: HTTPS REST (unified via LiteLLM)
   - **Usage**: Trend analysis, failure prediction explanations, optimization insights

#### Optional Integrations

4. **MCP Servers** (Ports 8001-8004)
   - **Purpose**: Enable external AI agent integration
   - **Protocol**: MCP over Streamable HTTP
   - **Technology**: FastMCP (Python)
   - **Usage**: Bob IDE, Claude Desktop, custom AI agents
   - **Note**: NOT required for core functionality

#### Future Gateway Integrations (Planned)

5. **Kong Gateway** - Via Kong Admin API
6. **Apigee Gateway** - Via Apigee Management API
7. **AWS API Gateway** - Via AWS SDK

---

## 5. Deployment & Environments

### Development Environment

**Docker Compose** setup with all services:

```bash
# Start all services
docker-compose up -d

# Initialize database
docker-compose exec backend python scripts/init_opensearch.py

# Access points
Frontend:    http://localhost:3000
Backend API: http://localhost:8000
Gateway:     http://localhost:8080
OpenSearch:  http://localhost:9200
Dashboards:  http://localhost:5601
```

**Services**:
- `opensearch` - Data store (9200)
- `backend` - FastAPI service (8000)
- `frontend` - React SPA (3000)
- `gateway` - Spring Boot gateway (8080)
- `mcp-unified` - Optional MCP server (8007)

---

### Production Environment (Kubernetes)

**Deployment Strategy**: Kubernetes with horizontal pod autoscaling

```yaml
Namespace: api-intelligence-plane
├── Deployments:
│   ├── backend (3 replicas, autoscale to 10)
│   ├── frontend (2 replicas, autoscale to 5)
│   └── gateway (2 replicas)
├── StatefulSet:
│   └── opensearch (3-node cluster)
├── Services:
│   ├── backend-service (ClusterIP)
│   ├── frontend-service (ClusterIP)
│   └── opensearch-service (Headless)
├── Ingress:
│   └── api-intelligence-ingress (TLS enabled)
└── ConfigMaps & Secrets:
    ├── app-config
    └── llm-api-keys
```

**Build & Deploy**:
```bash
# Build images
docker build -t api-intelligence/backend:latest ./backend
docker build -t api-intelligence/frontend:latest ./frontend
docker build -t api-intelligence/gateway:latest ./gateway

# Deploy to Kubernetes
kubectl apply -f k8s/

# Check status
kubectl get pods -n api-intelligence-plane
```

---

### CI/CD Pipeline

**Assumption**: Standard CI/CD workflow (not explicitly defined in codebase)

1. **Build**: Docker images built on commit to main
2. **Test**: Integration and E2E tests run in CI
3. **Deploy**: Automatic deployment to staging, manual promotion to production
4. **Monitoring**: Prometheus metrics, Grafana dashboards

---

## 6. Operational Notes

### Logging & Monitoring

**Logging**:
- **Backend**: Structured JSON logs via Python logging
- **Frontend**: Browser console (development), error tracking (production)
- **Gateway**: Spring Boot logging with Logback
- **Log Levels**: DEBUG (dev), INFO (staging), WARNING (production)
- **Audit Logging**: All operations logged with user, timestamp, resource, result

**Monitoring**:
- **Health Checks**: `/health` endpoint on all services
- **Metrics**: Prometheus-compatible metrics (planned)
- **Dashboards**: Grafana dashboards for key metrics (planned)
- **Alerts**: Failure predictions trigger alerts in frontend

---

### Common Failure Points & Risks

#### 1. OpenSearch Connection Failures
**Risk**: Backend cannot connect to OpenSearch  
**Impact**: All operations fail, no data persistence  
**Mitigation**: 
- Health checks on startup
- Retry logic with exponential backoff
- Graceful degradation (cache recent data)

#### 2. LLM API Rate Limits
**Risk**: Exceeding LLM provider rate limits  
**Impact**: AI-enhanced features fail, fallback to rule-based analysis  
**Mitigation**:
- Graceful fallback to non-AI predictions
- Rate limit tracking and throttling
- Multiple provider support via LiteLLM

#### 3. Gateway Discovery Failures
**Risk**: Cannot connect to API Gateway  
**Impact**: No new APIs discovered, stale inventory  
**Mitigation**:
- Gateway health checks before discovery
- Retry failed discoveries
- Alert on consecutive failures

#### 4. Scheduler Job Failures
**Risk**: Background jobs fail or hang  
**Impact**: No automatic discovery, metrics, or predictions  
**Mitigation**:
- Job timeout configuration
- Error logging and alerting
- Manual job trigger endpoints

#### 5. High Query Latency
**Risk**: Natural language queries take >5 seconds  
**Impact**: Poor user experience  
**Mitigation**:
- OpenSearch query optimization
- Result caching for common queries
- Query timeout limits

#### 6. Data Retention Overflow
**Risk**: OpenSearch storage fills up  
**Impact**: Cannot store new data  
**Mitigation**:
- Automatic index lifecycle management
- 90-day retention policy enforced
- Storage monitoring and alerts

---

### Performance Characteristics

| Metric | Target | Current | Notes |
|--------|--------|---------|-------|
| Query Latency | <5s | ~3s | Natural language queries |
| Discovery Cycle | <5min | ~3min | All gateways |
| Security Scan | <1hr | ~45min | Full vulnerability scan |
| API Support | 1000+ | Tested 1000+ | Concurrent APIs |
| Data Retention | 90 days | Configured | Time-series data |
| Concurrent Requests | Millions/min | Not tested | Design target |

---

## 7. Source Pointers

### Backend Services
- **Discovery**: [`backend/app/services/discovery_service.py`](../backend/app/services/discovery_service.py)
- **Metrics**: [`backend/app/services/metrics_service.py`](../backend/app/services/metrics_service.py)
- **Predictions**: [`backend/app/services/prediction_service.py`](../backend/app/services/prediction_service.py)
- **Optimization**: [`backend/app/services/optimization_service.py`](../backend/app/services/optimization_service.py)
- **Query**: [`backend/app/services/query_service.py`](../backend/app/services/query_service.py)
- **Rate Limiting**: [`backend/app/services/rate_limit_service.py`](../backend/app/services/rate_limit_service.py)

### AI Agents
- **Prediction Agent**: [`backend/app/agents/prediction_agent.py`](../backend/app/agents/prediction_agent.py)
- **Optimization Agent**: [`backend/app/agents/optimization_agent.py`](../backend/app/agents/optimization_agent.py)
- **LLM Service**: [`backend/app/services/llm_service.py`](../backend/app/services/llm_service.py)

### Gateway Adapters
- **Base Adapter**: [`backend/app/adapters/base.py`](../backend/app/adapters/base.py)
- **Native Gateway**: [`backend/app/adapters/native_gateway.py`](../backend/app/adapters/native_gateway.py)
- **Kong Gateway**: [`backend/app/adapters/kong_gateway.py`](../backend/app/adapters/kong_gateway.py)
- **Apigee Gateway**: [`backend/app/adapters/apigee_gateway.py`](../backend/app/adapters/apigee_gateway.py)
- **Factory**: [`backend/app/adapters/factory.py`](../backend/app/adapters/factory.py)

### API Endpoints
- **Main App**: [`backend/app/main.py`](../backend/app/main.py)
- **APIs**: [`backend/app/api/v1/apis.py`](../backend/app/api/v1/apis.py)
- **Gateways**: [`backend/app/api/v1/gateways.py`](../backend/app/api/v1/gateways.py)
- **Metrics**: [`backend/app/api/v1/metrics.py`](../backend/app/api/v1/metrics.py)
- **Predictions**: [`backend/app/api/v1/predictions.py`](../backend/app/api/v1/predictions.py)
- **Optimization**: [`backend/app/api/v1/optimization.py`](../backend/app/api/v1/optimization.py)
- **Query**: [`backend/app/api/v1/query.py`](../backend/app/api/v1/query.py)

### Frontend Components
- **Main App**: [`frontend/src/App.tsx`](../frontend/src/App.tsx)
- **Dashboard**: [`frontend/src/pages/Dashboard.tsx`](../frontend/src/pages/Dashboard.tsx)
- **APIs Page**: [`frontend/src/pages/APIs.tsx`](../frontend/src/pages/APIs.tsx)
- **Predictions**: [`frontend/src/pages/Predictions.tsx`](../frontend/src/pages/Predictions.tsx)
- **Query Interface**: [`frontend/src/pages/Query.tsx`](../frontend/src/pages/Query.tsx)

### Gateway
- **Main Application**: [`gateway/src/main/java/com/example/gateway/GatewayApplication.java`](../gateway/src/main/java/com/example/gateway/GatewayApplication.java)
- **API Service**: [`gateway/src/main/java/com/example/gateway/service/APIService.java`](../gateway/src/main/java/com/example/gateway/service/APIService.java)
- **Metrics Service**: [`gateway/src/main/java/com/example/gateway/service/MetricsService.java`](../gateway/src/main/java/com/example/gateway/service/MetricsService.java)

### MCP Server (Optional)
- **Unified Server**: [`mcp-servers/unified_server.py`](../mcp-servers/unified_server.py) - All MCP functionality in one server

### Database
- **OpenSearch Client**: [`backend/app/db/client.py`](../backend/app/db/client.py)
- **Repositories**: [`backend/app/db/repositories/`](../backend/app/db/repositories/)
- **Migrations**: [`backend/app/db/migrations/`](../backend/app/db/migrations/)

### Configuration
- **Docker Compose**: [`docker-compose.yml`](../docker-compose.yml)
- **Backend Config**: [`backend/app/config.py`](../backend/app/config.py)
- **Environment**: [`.env.example`](../.env.example)

### Documentation
- **Architecture**: [`docs/architecture.md`](./architecture.md)
- **API Reference**: [`docs/api-reference.md`](./api-reference.md)
- **Deployment**: [`docs/deployment.md`](./deployment.md)
- **MCP Architecture**: [`docs/mcp-architecture.md`](./mcp-architecture.md)

---

## Additional Resources

- **README**: [`README.md`](../README.md) - Quick start and overview
- **Contributing**: [`docs/contributing.md`](./contributing.md) - Development guidelines
- **AI Setup**: [`docs/ai-setup.md`](./ai-setup.md) - LLM provider configuration
- **Development Guidelines**: [`AGENTS.md`](../AGENTS.md) - Technology stack and standards

---

**Built with ❤️ by the API Intelligence Plane Team**