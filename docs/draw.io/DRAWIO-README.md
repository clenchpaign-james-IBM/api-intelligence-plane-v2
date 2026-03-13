# Draw.io Architecture Diagrams

This directory contains all architecture diagrams from `architecture.md` converted to draw.io format.

## Available Diagrams

### 1. Core Application Architecture (from README)
**File**: `10-readme-core-architecture.drawio`
**Description**: Simplified core application architecture showing the essential components from the README.md overview.

**Key Components**:
- Frontend (React) - Dashboard, APIs, Security, Query UI
- Backend API (FastAPI) - Single source of truth
- OpenSearch - Data store
- Demo Gateway - Spring Boot native API Gateway

**Flow**: Frontend → Backend → (OpenSearch + Demo Gateway)

---

### 2. MCP External Agent Integration (from README)
**File**: `11-readme-mcp-integration.drawio`
**Description**: Optional MCP server architecture for external AI agent integration from README.md.

**Key Components**:
- MCP Servers: Discovery (8001), Metrics (8002), Optimization (8004)
- Backend API (8000)
- AI Agents (Bob IDE, Claude Desktop)

**Flow**: AI Agents → Backend API (via MCP Protocol) ← MCP Servers

---

### 3. High-Level System Architecture
**File**: `01-high-level-architecture.drawio`  
**Description**: Complete system overview showing Frontend, Backend (with Services/Agents/Adapters), data stores, LLM providers, Demo Gateway, and optional MCP integration for external AI agents.

**Key Components**:
- Frontend (React SPA) - Port 3000
- Backend API (FastAPI) - Port 8000
- OpenSearch - Port 9200
- LLM Providers (via LiteLLM)
- Demo Gateway - Port 8080
- Optional: MCP Servers (8001-8004) for AI agent integration

---

### 4. Backend Architecture Layers
**File**: `02-backend-layers.drawio`
**Description**: Layered architecture of the Backend API showing the five-layer structure from API endpoints down to data access.

**Layers** (top to bottom):
1. API Layer (REST endpoints)
2. Service Layer (Business logic)
3. Agent Layer (AI workflows)
4. Adapter Layer (Gateway strategy pattern)
5. Data Layer (OpenSearch repositories)

---

### 5. Core Application Data Flow
**File**: `03-core-data-flow.drawio`
**Description**: Primary data flow from user through frontend to backend, then branching to OpenSearch and Demo Gateway.

**Flow**: User → Frontend → Backend → (OpenSearch + Demo Gateway)

---

### 6. Optional External Agent Flow
**File**: `04-external-agent-flow.drawio`
**Description**: Data flow for external AI agents (Bob IDE, Claude Desktop) accessing the platform via MCP servers.

**Flow**: AI Agent → MCP Server → Backend API → OpenSearch

---

### 7. API Discovery Flow
**File**: `05-api-discovery-flow.drawio`
**Description**: Automated API discovery workflow triggered by scheduler every 5 minutes.

**Flow**: Scheduler → DiscoveryService → Gateway Adapter → OpenSearch (api-inventory)

---

### 8. Prediction Generation Flow
**File**: `06-prediction-flow.drawio`
**Description**: AI-powered failure prediction workflow triggered every 15 minutes.

**Flow**: Scheduler → PredictionService → PredictionAgent (LangGraph) → OpenSearch (api-predictions) → Frontend

---

### 9. Natural Language Query Flow
**File**: `07-query-flow.drawio`
**Description**: Complete workflow for processing natural language queries using AI agents.

**Flow**: User Query → QueryService → Query Agent (LangChain) → OpenSearch → Response Generator → Frontend

---

### 10. Development Deployment Architecture
**File**: `08-deployment-dev.drawio`
**Description**: Docker Compose deployment structure for local development environment.

**Core Services**:
- opensearch (9200)
- backend (8000)
- frontend (3000)
- demo-gateway (8080)

**Optional Services** (for AI agent integration):
- mcp-discovery (8001)
- mcp-metrics (8002)
- mcp-optimization (8004)

---

### 11. Production Kubernetes Architecture
**File**: `09-deployment-k8s.drawio`
**Description**: Kubernetes production deployment with namespace, deployments, services, and monitoring.

**Components**:
- **Deployments**: backend (3 replicas), frontend (2 replicas), demo-gateway (2 replicas)
- **StatefulSet**: opensearch (3 nodes)
- **Services**: backend-service, frontend-service, opensearch-service
- **Infrastructure**: Ingress, ConfigMap
- **Optional**: mcp-servers deployment
- **Monitoring**: Prometheus, Grafana

---

## How to Use These Diagrams

### Opening in draw.io

1. **Online**: Go to https://app.diagrams.net/
2. **Desktop**: Download draw.io desktop app from https://www.drawio.com/
3. Open any `.drawio` file from this directory

### Editing

1. Open the file in draw.io
2. All components are fully editable
3. Colors, sizes, and positions can be adjusted
4. Export as PNG, SVG, or PDF for documentation

### Color Scheme

The diagrams use a consistent color palette:

- **Frontend**: Light Blue (#E3F2FD, #BBDEFB)
- **Backend**: Light Green (#E8F5E9, #C8E6C9)
- **Database**: Light Orange (#FFF3E0, #FFCCBC)
- **AI/ML**: Light Purple (#E1BEE7, #F3E5F5)
- **Gateway**: Light Yellow (#FFF9C4)
- **MCP/Optional**: Light Cyan (#B2EBF2, #E0F7FA)
- **Infrastructure**: Light Gray (#F5F5F5)
- **Monitoring**: Light Red (#FFCDD2, #FFEBEE)

### Shape Guidelines

- **Services/Applications**: Rectangle (rounded corners)
- **Databases**: Cylinder
- **Users**: Actor icon
- **Schedulers/Triggers**: Hexagon
- **Kubernetes Services**: Hexagon
- **Ingress**: Trapezoid
- **ConfigMap**: Document/Note shape
- **Optional Components**: Dashed border

### Exporting

**For Documentation**:
- Format: PNG or SVG
- Resolution: 300 DPI (for PNG)
- Background: White
- Include border padding

**For Presentations**:
- Format: PNG with transparent background
- Resolution: 150-300 DPI
- Optimize for screen display

---

## Diagram Relationships

```
README Diagrams:
10-readme-core-architecture.drawio (Simplified Overview)
11-readme-mcp-integration.drawio (Optional MCP)

Architecture.md Diagrams:
01-high-level-architecture.drawio (System Overview)
    ├── 02-backend-layers.drawio (Backend Detail)
    ├── 03-core-data-flow.drawio (Primary Flow)
    ├── 04-external-agent-flow.drawio (Optional MCP Flow)
    └── Data Flows:
        ├── 05-api-discovery-flow.drawio
        ├── 06-prediction-flow.drawio
        └── 07-query-flow.drawio
    
Deployment:
    ├── 08-deployment-dev.drawio (Docker Compose)
    └── 09-deployment-k8s.drawio (Kubernetes)
```

---

## Maintenance

When updating diagrams:

1. Keep color scheme consistent
2. Maintain shape conventions
3. Update version numbers in diagram properties
4. Export updated PNG/SVG for documentation
5. Update this README if adding new diagrams

---

## Source

All diagrams are based on the ASCII diagrams in [`docs/architecture.md`](../architecture.md).

For detailed component descriptions and technical specifications, refer to the main architecture documentation.

---

## Quick Reference

| Diagram | File | Type | Complexity |
|---------|------|------|------------|
| README Core Architecture | 10-readme-core-architecture.drawio | System Context | Low |
| README MCP Integration | 11-readme-mcp-integration.drawio | System Context | Low |
| High-Level Architecture | 01-high-level-architecture.drawio | System Context | High |
| Backend Layers | 02-backend-layers.drawio | Component | Medium |
| Core Data Flow | 03-core-data-flow.drawio | Sequence | Low |
| External Agent Flow | 04-external-agent-flow.drawio | Sequence | Low |
| API Discovery | 05-api-discovery-flow.drawio | Workflow | Medium |
| Prediction Generation | 06-prediction-flow.drawio | Workflow | Medium |
| Query Processing | 07-query-flow.drawio | Workflow | Medium |
| Dev Deployment | 08-deployment-dev.drawio | Deployment | Low |
| K8s Production | 09-deployment-k8s.drawio | Deployment | High |

---

## License

These diagrams are part of the API Intelligence Plane project documentation.