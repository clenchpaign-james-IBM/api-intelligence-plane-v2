# Implementation Plan: API Intelligence Plane

**Branch**: `001-api-intelligence-plane` | **Date**: 2026-04-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-api-intelligence-plane/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

API Intelligence Plane is an AI-driven API management application that transforms API operations from reactive firefighting to proactive, autonomous management. The system provides autonomous API discovery (including shadow APIs), predictive health management (24-48 hour advance warnings), continuous security scanning with automated remediation, real-time performance optimization (including caching, compression, and rate limiting), and natural language query interface.

**Technical Approach**: Built as a distributed web application using FastAPI (Python 3.11+) backend with LangChain/LangGraph for AI workflows, React.js frontend, OpenSearch for data storage, and FastMCP for external integration interface. The system uses vendor-neutral data models with vendor-specific gateway adapters (Strategy + Adapter patterns). Initial release focuses on WebMethods API Gateway integration, with multi-vendor support architecture in place for future expansion.

## Technical Context

**Language/Version**:
- Backend: Python 3.11+
- Frontend: TypeScript 5.3+ / JavaScript ES2022
- MCP Servers: Python 3.11+

**Primary Dependencies**:
- Backend: FastAPI 0.109+, LangChain 0.1+, LangGraph 0.0.20+, LiteLLM 1.17+, OpenSearch Python Client 2.4+, APScheduler 3.10+
- Frontend: React 18.2+, Vite 5.0+, TanStack Query 5.14+, Tailwind CSS 3.4+, Recharts 2.10+
- MCP: FastMCP 0.1+ with Streamable HTTP transport
- Testing: pytest 7.4+, pytest-asyncio 0.21+, Playwright/Cypress

**Storage**: OpenSearch 2.11+ for all data types (API inventory, metrics, predictions, security findings, compliance violations, optimization recommendations, transactional logs)

**Testing**: Integration and E2E testing focus (unit tests explicitly excluded per requirements). pytest for backend integration, Playwright/Cypress for E2E workflows.

**Target Platform**:
- Backend: Linux/macOS servers (containerized via Docker)
- Frontend: Modern web browsers (Chrome, Firefox, Safari, Edge)
- Deployment: Docker Compose (local), Kubernetes 1.28+ (production)

**Project Type**: Distributed web application with AI-driven intelligence layer

**Performance Goals**:
- Query latency: <5 seconds for natural language queries
- Discovery cycles: Complete within 5 minutes
- Security scans: Complete within 1 hour
- API support: 1000+ APIs
- Concurrent requests: Support millions per minute
- Real-time query response: <3 seconds for 90% of queries

**Constraints**:
- FedRAMP 140-3 compliance (NIST-approved algorithms, TLS 1.3, encryption in transit)
- Vendor-neutral architecture (no gateway vendor lock-in)
- Model-agnostic AI (support multiple LLM providers via LiteLLM)
- Data retention: 90 days minimum
- Initial release: WebMethods API Gateway only

**Scale/Scope**:
- 1000+ APIs per deployment
- Multiple gateway instances per deployment
- 90-day data retention with automatic cleanup
- Multi-resolution time-series data (1-min, 5-min, 1-hour, 1-day buckets)
- Support for millions of API requests per minute across all APIs

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Initial Status**: ⚠️ CONSTITUTION FILE IS TEMPLATE ONLY - No project-specific principles defined

The constitution file (`.specify/memory/constitution.md`) contains only template placeholders and has not been customized for this project. Therefore, no specific gates can be evaluated at this time.

**Default Assumptions** (in absence of constitution):
- ✅ Integration and E2E testing required (per spec requirements)
- ✅ Multi-vendor support architecture (Strategy + Adapter patterns)
- ✅ Security-first approach (FedRAMP compliance)
- ✅ Vendor-neutral data models
- ✅ Model-agnostic AI implementation

---

### Re-evaluation After Phase 1 Design (2026-04-28)

**Status**: ✅ DESIGN ARTIFACTS ALIGN WITH REQUIREMENTS

All Phase 1 design artifacts have been generated and reviewed against the feature specification and research decisions:

#### Data Model Compliance
- ✅ **Vendor-Neutral Schemas**: All entities use vendor-neutral data models (API, Gateway, Metric, Prediction, Vulnerability, ComplianceViolation, OptimizationRecommendation, Query, TransactionalLog)
- ✅ **Multi-Gateway Support**: Gateway entity supports multiple vendors with capability detection
- ✅ **Time-Series Data**: Metrics stored at multiple resolutions (1-min, 5-min, 1-hour, 1-day) with ILM policies
- ✅ **Compliance Separation**: Separate entities for security vulnerabilities and compliance violations
- ✅ **Audit Trail**: Complete audit logging for compliance violations and security remediation

#### Interface Contracts Compliance
- ✅ **REST API**: Comprehensive REST API contract with all required endpoints (gateways, apis, predictions, security, compliance, optimization, query, analytics)
- ✅ **MCP Server**: Complete MCP server contract with tools and resources for external integration
- ✅ **Gateway Adapters**: Well-defined adapter interface with Strategy + Adapter patterns, policy normalization/denormalization
- ✅ **Versioning**: All contracts include versioning strategy
- ✅ **Error Handling**: Standardized error responses across all interfaces

#### Architecture Pattern Compliance
- ✅ **Strategy Pattern**: Gateway adapters encapsulate vendor-specific algorithms
- ✅ **Adapter Pattern**: Unified interface with vendor-specific implementations
- ✅ **Repository Pattern**: Data access abstraction via OpenSearch
- ✅ **Service Layer**: Business logic separation in services
- ✅ **Agent Pattern**: LangChain/LangGraph for AI workflows

#### Testing Strategy Compliance
- ✅ **Integration Tests**: Focus on component interactions (per spec requirements)
- ✅ **E2E Tests**: Complete workflow validation (per spec requirements)
- ✅ **No Unit Tests**: Explicitly excluded per project specification
- ✅ **Contract Tests**: Gateway adapter contract verification

#### Security & Compliance
- ✅ **FedRAMP 140-3**: TLS 1.3, NIST-approved algorithms, encryption in transit
- ✅ **Multi-Standard Support**: GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001
- ✅ **Audit Logging**: Complete audit trail for all operations
- ✅ **Data Retention**: 90-day minimum with ILM policies

#### Performance & Scale
- ✅ **Query Latency**: <5 seconds for natural language queries (design supports)
- ✅ **Discovery Cycles**: 5-minute completion target (design supports)
- ✅ **API Support**: 1000+ APIs (design supports via OpenSearch scaling)
- ✅ **Data Retention**: 90 days with automatic cleanup (ILM policies defined)

**Conclusion**: All design artifacts align with feature specification requirements, research decisions, and architectural patterns. No violations or concerns identified. Ready to proceed to Phase 2 (Task Breakdown).

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
api-intelligence-plane/
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── config.py          # Configuration management
│   │   ├── api/               # REST API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── deps.py        # Dependency injection
│   │   │   └── v1/            # API version 1
│   │   │       ├── __init__.py
│   │   │       ├── apis.py    # API inventory endpoints
│   │   │       ├── gateways.py # Gateway management endpoints
│   │   │       └── optimization.py # Optimization endpoints (caching, compression, rate limiting)
│   │   ├── models/            # Pydantic models
│   │   │   └── prediction.py  # Prediction models
│   │   ├── services/          # Business logic layer
│   │   │   ├── compliance_service.py
│   │   │   ├── discovery_service.py
│   │   │   ├── llm_service.py
│   │   │   ├── metrics_service.py
│   │   │   ├── optimization_service.py  # Handles caching, compression, and rate limiting
│   │   │   ├── prediction_service.py
│   │   │   ├── query_service.py
│   │   │   ├── security_service.py
│   │   │   └── query/
│   │   │       └── concept_mapper.py
│   │   ├── agents/            # LangChain/LangGraph agents
│   │   │   ├── __init__.py
│   │   │   ├── compliance_agent.py
│   │   │   ├── optimization_agent.py
│   │   │   ├── prediction_agent.py
│   │   │   └── security_agent.py
│   │   ├── adapters/          # Gateway adapters (Strategy pattern)
│   │   │   ├── __init__.py
│   │   │   ├── base.py        # Abstract base adapter
│   │   │   ├── factory.py     # Adapter factory
│   │   │   ├── webmethods_gateway.py # WebMethods adapter
│   │   │   ├── kong_gateway.py       # Kong adapter (future)
│   │   │   ├── apigee_gateway.py     # Apigee adapter (future)
│   │   │   └── policy_converters.py  # Policy conversion utilities
│   │   ├── db/                # OpenSearch client and repositories
│   │   │   └── ilm_policies.py
│   │   ├── scheduler/         # APScheduler jobs
│   │   │   ├── __init__.py
│   │   │   ├── apis_discovery_jobs.py
│   │   │   ├── compliance_jobs.py
│   │   │   ├── intelligence_metadata_jobs.py
│   │   │   ├── optimization_jobs.py
│   │   │   ├── prediction_jobs.py
│   │   │   ├── security_jobs.py
│   │   │   └── transactional_logs_collection_jobs.py
│   │   ├── middleware/        # FastAPI middleware
│   │   └── utils/             # Utility functions
│   ├── tests/                 # Integration and E2E tests
│   │   ├── integration/
│   │   │   └── test_discovery_flow.py
│   │   └── e2e/
│   ├── scripts/               # Utility scripts
│   │   ├── init_opensearch.py
│   │   ├── generate_mock_predictions.py
│   │   └── test_*.py
│   ├── Dockerfile
│   ├── pyproject.toml
│   └── requirements.txt
│
├── frontend/                  # React.js frontend
│   ├── src/
│   │   ├── index.css
│   │   ├── components/        # Reusable components
│   │   │   └── optimization/
│   │   │       ├── ImplementationTracker.tsx
│   │   │       ├── RateLimitChart.tsx  # Rate limiting visualization (part of optimization)
│   │   │       ├── RecommendationCard.tsx
│   │   │       └── RecommendationDetail.tsx
│   │   ├── pages/             # Page components
│   │   │   ├── OptimizationGrouped.tsx
│   │   │   ├── Query.tsx
│   │   │   └── Security.tsx
│   │   ├── services/          # API client services
│   │   ├── hooks/             # Custom React hooks
│   │   └── types/             # TypeScript types
│   │       ├── index.ts
│   │       └── optimization.ts
│   ├── Dockerfile
│   ├── Dockerfile.dev
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.ts
│
├── mcp-servers/               # MCP server (FastMCP)
│   ├── unified_server.py      # Unified MCP server (all functionality)
│   ├── common/                # Shared utilities
│   │   ├── __init__.py
│   │   ├── backend_client.py
│   │   ├── health.py
│   │   ├── http_health.py
│   │   ├── mcp_base.py
│   │   └── opensearch.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README_UNIFIED_SERVER.md
│
├── tests/                     # Cross-component tests
│   └── integration/
│       └── test_discovery_flow.py
│
├── config/                    # Configuration files
├── k8s/                       # Kubernetes manifests
├── docs/                      # Documentation
├── specs/                     # Feature specifications
│   └── 001-api-intelligence-plane/
│       ├── spec.md
│       ├── plan.md            # This file
│       ├── research.md
│       ├── data-model.md      # To be generated
│       ├── quickstart.md      # To be generated
│       └── contracts/         # To be generated
├── certs/                     # TLS certificates
│   ├── backend/
│   ├── frontend/
│   ├── mcp/
│   └── ca/
├── docker-compose.yml
├── docker-compose-tls.yml
├── AGENTS.md
└── README.md
```

**Structure Decision**: Web application architecture (Option 2) with additional MCP server component. The project is organized as a distributed system with three main components:

1. **Backend**: FastAPI service providing REST API, business logic, AI agents, and gateway adapters
2. **Frontend**: React SPA for user interface and dashboards
3. **MCP Servers**: External integration interface for AI agents and automation tools

This structure supports:
- Clear separation of concerns (presentation, business logic, data access)
- Independent scaling of components
- Multi-vendor gateway support via adapter pattern
- Integration and E2E testing across components
- Docker containerization for each service

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
