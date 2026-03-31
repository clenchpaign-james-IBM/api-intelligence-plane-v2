# Implementation Plan: API Intelligence Plane

**Branch**: `001-api-intelligence-plane` | **Date**: 2026-03-09 | **Updated**: 2026-03-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-api-intelligence-plane/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

API Intelligence Plane is an AI-driven API management application that transforms API management from reactive firefighting to proactive, autonomous operations. It acts as an always-on intelligent companion to existing API Gateways, providing AI-driven visibility, decision-making, and automation for APIs. Core capabilities include autonomous API discovery (including shadow APIs), predictive health management (24-48 hours advance failure prediction), continuous security scanning with automated remediation, **unified performance optimization (caching, compression, and rate limiting)**, and natural language query interface. The system is vendor-neutral, supporting API Gateways from multiple vendors.

**Key Architecture Update (2026-03-29)**: Performance optimization and rate limiting have been merged into a single unified feature (User Story 4), as both are gateway-level performance optimization techniques. All optimization types (caching, compression, rate limiting) are now presented in a unified interface with consistent interaction patterns.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), JavaScript/TypeScript (Frontend), Java (Demo API Gateway)
**Primary Dependencies**:
- Backend: FastAPI, LangChain, LangGraph, FastMCP, LiteLLM, OpenSearch Python client
- Frontend: React.js, React Router, Axios/Fetch API
- AI Framework: LangChain for agent orchestration, LangGraph for workflow management
- MCP: FastMCP for server/client implementation with Streamable HTTP transport
- Demo Gateway: Spring Boot, OpenSearch Java client

**Prediction Architecture**: Hybrid approach combining rule-based predictions (fast, deterministic baseline) with optional AI-enhanced analysis (deep insights, natural language explanations). AI enhancement is automatically triggered based on prediction confidence thresholds (default: ≥80%) and system configuration (PREDICTION_AI_ENABLED, PREDICTION_AI_THRESHOLD).

**Storage**: OpenSearch (API inventory, metrics, AI insights, security findings, predictions)
**Testing**: pytest (Backend), Jest/React Testing Library (Frontend), JUnit (Demo Gateway), Integration tests across all components, End-to-end tests using Demo API Gateway
**Target Platform**: Linux/macOS servers (Docker containers), Web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Distributed web application with microservices architecture (Backend API + Frontend SPA + MCP Servers + Demo Gateway)
**Performance Goals**:
- Process data from 1000+ APIs with <5s latency for real-time queries
- Discovery cycles complete within 5 minutes
- Security scans complete within 1 hour for new vulnerabilities
- Natural language queries return results within 3 seconds
- Support millions of API requests per minute across all monitored APIs

**Constraints**:
- FedRAMP 140-3 compliance (NIST-approved algorithms, encryption in transit)
- No authentication required for MVP
- Model-agnostic LLM architecture
- Vendor-neutral API Gateway support
- Background scheduler for periodic data collection

**Scale/Scope**:
- Support 1000+ APIs across multiple Gateway vendors
- 90-day historical data retention
- Multi-vendor Gateway integration (minimum 3 vendors)
- Real-time monitoring and prediction capabilities
- Automated remediation workflows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Architecture Principles

**✓ PASS**: Microservices Architecture
- Backend API, Frontend SPA, MCP Servers, and Demo Gateway are independently deployable
- Each component has clear boundaries and responsibilities
- Components communicate via well-defined interfaces (REST APIs, MCP protocol)

**✓ PASS**: Vendor-Neutral Design
- Strategy and Adapter patterns for multi-vendor Gateway support
- Standardized integration interfaces abstract vendor-specific implementations
- Consistent functionality across different Gateway vendors

**✓ PASS**: Model-Agnostic AI Architecture
- LiteLLM provides unified interface to multiple LLM providers
- Configuration-driven provider selection enables runtime flexibility
- No hard dependencies on specific LLM vendors

### Testing Requirements

**✓ PASS**: Integration Testing Strategy
- Integration tests required across all components
- End-to-end tests using Demo API Gateway
- Mock data generation for testing scenarios
- Unit tests explicitly not required per project requirements

**⚠️ JUSTIFIED**: No Unit Tests
- Project explicitly states "Unit tests not required"
- Focus on integration and end-to-end testing
- Justification: MVP prioritizes system-level validation over component isolation

### Security & Compliance

**✓ PASS**: FedRAMP 140-3 Compliance
- NIST-approved algorithms for cryptographic operations
- Encryption in transit for all communications
- Security scanning and automated remediation capabilities built-in

**⚠️ JUSTIFIED**: No Authentication for MVP
- Project explicitly states "Authentication not required for MVP"
- Justification: Accelerates initial development and testing
- Must be addressed before production deployment

### Code Quality Standards

**✓ PASS**: Avoid Hardcoded Values
- Configuration-driven design for all components
- Settings for endpoints, Gateway connections, LLM providers
- Environment-based configuration management

**✓ PASS**: DRY Principle
- Shared libraries for common functionality
- Reusable MCP tools and AI agents
- Normalized data models across vendors

**✓ PASS**: Error Handling
- Comprehensive error handling for Gateway failures
- Graceful degradation when components unavailable
- Audit logging for all operations

**✓ PASS**: Modularity and Reusability
- FastMCP framework for standardized MCP server development
- LangChain/LangGraph for reusable AI workflows
- Component-based React architecture

### Violations Requiring Justification

None - all architectural decisions align with stated requirements and best practices.

## Project Structure

### Documentation (this feature)

```text
specs/001-api-intelligence-plane/
├── plan.md              # This file (implementation plan)
├── research.md          # Technology decisions and research findings
├── data-model.md        # Entity definitions and relationships
├── quickstart.md        # Setup and getting started guide
├── contracts/           # Interface contracts
│   ├── backend-api.yaml       # Backend REST API specification
│   ├── mcp-tools.md           # MCP server tools specification
│   └── demo-gateway-api.yaml  # Demo Gateway API specification
└── tasks.md             # Phase 2 output (NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
api-intelligence-plane-v2/
├── backend/                    # FastAPI backend service
│   ├── app/
│   │   ├── main.py            # FastAPI application entry point
│   │   ├── api/               # REST API endpoints
│   │   │   ├── v1/
│   │   │   │   ├── gateways.py
│   │   │   │   ├── apis.py
│   │   │   │   ├── metrics.py
│   │   │   │   ├── predictions.py
│   │   │   │   ├── security.py
│   │   │   │   ├── optimization.py
│   │   │   │   ├── rate_limits.py
│   │   │   │   └── query.py
│   │   │   └── deps.py        # Dependency injection
│   │   ├── models/            # Pydantic models
│   │   │   ├── api.py
│   │   │   ├── gateway.py
│   │   │   ├── metric.py
│   │   │   ├── prediction.py  # Includes ContributingFactorType enum (13 types)
│   │   │   ├── vulnerability.py
│   │   │   ├── recommendation.py
│   │   │   ├── rate_limit.py
│   │   │   └── query.py
│   │   ├── services/          # Business logic
│   │   │   ├── discovery_service.py
│   │   │   ├── metrics_service.py
│   │   │   ├── prediction_service.py  # Hybrid: rule-based + AI enhancement
│   │   │   ├── security_service.py
│   │   │   ├── optimization_service.py
│   │   │   ├── query_service.py
│   │   │   └── llm_service.py  # LiteLLM integration with fallback
│   │   ├── agents/            # LangChain/LangGraph agents
│   │   │   ├── prediction_agent.py
│   │   │   ├── security_agent.py
│   │   │   ├── optimization_agent.py
│   │   │   └── query_agent.py
│   │   ├── adapters/          # Gateway adapters (Strategy pattern)
│   │   │   ├── base.py  # Enhanced with policy application methods
│   │   │   ├── native_gateway.py  # Implements caching, compression, rate limit policies
│   │   │   ├── kong_gateway.py
│   │   │   └── apigee_gateway.py
│   │   ├── db/                # OpenSearch client and operations
│   │   │   ├── client.py
│   │   │   ├── repositories/
│   │   │   └── migrations/
│   │   ├── scheduler/         # APScheduler jobs
│   │   │   ├── discovery_jobs.py
│   │   │   ├── metrics_jobs.py
│   │   │   └── security_jobs.py
│   │   └── config.py          # Configuration management
│   ├── tests/
│   │   ├── integration/       # Integration tests
│   │   └── e2e/              # End-to-end tests
│   ├── scripts/              # Utility scripts
│   │   ├── init_opensearch.py
│   │   ├── generate_traffic.py
│   │   └── test_llm.py
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/                  # React.js frontend
│   ├── src/
│   │   ├── components/       # Reusable components
│   │   │   ├── common/
│   │   │   ├── dashboard/
│   │   │   ├── apis/
│   │   │   ├── metrics/
│   │   │   ├── predictions/
│   │   │   ├── security/
│   │   │   └── query/
│   │   ├── pages/           # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── APIs.tsx
│   │   │   ├── Gateways.tsx
│   │   │   ├── Predictions.tsx
│   │   │   ├── Security.tsx
│   │   │   ├── Optimization.tsx
│   │   │   └── Query.tsx
│   │   ├── services/        # API client services
│   │   │   ├── api.ts
│   │   │   ├── gateway.ts
│   │   │   ├── metrics.ts
│   │   │   └── query.ts
│   │   ├── hooks/          # Custom React hooks
│   │   ├── utils/          # Utility functions
│   │   ├── types/          # TypeScript types
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── tests/
│   │   └── components/
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
│
├── mcp-servers/              # MCP servers (FastMCP)
│   ├── discovery_server.py   # API discovery tools
│   ├── metrics_server.py     # Metrics collection tools
│   ├── security_server.py    # Security scanning tools
│   ├── optimization_server.py # Unified optimization tools (caching, compression, rate limiting)
│   ├── common/
│   │   ├── mcp_base.py      # Base MCP server class
│   │   └── opensearch.py    # Shared OpenSearch client
│   ├── requirements.txt
│   └── Dockerfile
│
├── demo-gateway/             # Native API Gateway (Java/Spring Boot)
│   ├── src/
│   │   └── main/
│   │       ├── java/
│   │       │   └── com/example/gateway/
│   │       │       ├── GatewayApplication.java
│   │       │       ├── controller/
│   │       │       │   ├── GatewayController.java
│   │       │       │   ├── APIController.java
│   │       │       │   ├── PolicyController.java
│   │       │       │   └── MetricsController.java
│   │       │       ├── service/
│   │       │       │   ├── APIService.java
│   │       │       │   ├── PolicyService.java
│   │       │       │   ├── MetricsService.java
│   │       │       │   └── RoutingService.java
│   │       │       ├── model/
│   │       │       ├── repository/
│   │       │       ├── policy/          # Policy engine
│   │       │       │   ├── PolicyEngine.java
│   │       │       │   ├── AuthenticationPolicy.java
│   │       │       │   ├── RateLimitPolicy.java
│   │       │       │   └── ValidationPolicy.java
│   │       │       └── config/
│   │       └── resources/
│   │           └── application.yml
│   ├── src/test/java/
│   ├── pom.xml
│   └── Dockerfile
│
├── tests/                    # Cross-component tests
│   ├── integration/         # Integration tests
│   │   ├── test_discovery_flow.py
│   │   ├── test_metrics_collection.py
│   │   ├── test_prediction_generation.py
│   │   └── test_security_scanning.py
│   └── e2e/                # End-to-end tests
│       ├── test_complete_workflow.py
│       ├── test_gateway_integration.py
│       └── fixtures/
│
├── config/                  # Configuration files
│   ├── default.yaml
│   ├── development.yaml
│   ├── production.yaml
│   └── test.yaml
│
├── k8s/                    # Kubernetes manifests
│   ├── namespace.yaml
│   ├── opensearch/
│   ├── backend/
│   ├── frontend/
│   ├── mcp-servers/
│   └── demo-gateway/
│
├── docs/                   # Additional documentation
│   ├── architecture.md
│   ├── api-reference.md
│   ├── deployment.md
│   └── contributing.md
│
├── .specify/              # Spec framework files
├── specs/                 # Feature specifications
├── docker-compose.yml     # Local development
├── docker-compose.prod.yml # Production deployment
├── .env.example
├── .gitignore
├── README.md
└── AGENTS.md             # Agent context (auto-updated)
```

**Structure Decision**: Web application with microservices architecture

This structure was chosen because:
1. **Clear Separation**: Backend, Frontend, MCP Servers, and Demo Gateway are independently deployable
2. **Microservices**: Each MCP server is a separate service with specific responsibilities
3. **Scalability**: Components can be scaled independently based on load
4. **Technology Diversity**: Supports Python (Backend/MCP), JavaScript/TypeScript (Frontend), and Java (Demo Gateway)
5. **Testing Strategy**: Separate integration and e2e test directories for cross-component testing
6. **Configuration Management**: Centralized config directory with environment-specific files
7. **Deployment Flexibility**: Docker Compose for local dev, Kubernetes manifests for production

## Complexity Tracking

No violations requiring justification. All architectural decisions align with project requirements and best practices.

## Constitution Check Re-evaluation (Post-Design)

After completing Phase 1 design, re-evaluating constitution compliance:

### Architecture Principles ✅

**✓ CONFIRMED**: Microservices Architecture
- Design artifacts confirm independent deployability
- Clear service boundaries defined in contracts
- Well-defined communication protocols (REST, MCP)

**✓ CONFIRMED**: Vendor-Neutral Design
- Gateway adapters implement Strategy pattern (see backend/app/adapters/)
- Standardized interfaces defined in contracts
- Multiple vendor support validated in design

**✓ CONFIRMED**: Model-Agnostic AI Architecture
- LiteLLM integration confirmed in research.md
- Configuration-driven provider selection designed
- No hard LLM dependencies in architecture

### Testing Requirements ✅

**✓ CONFIRMED**: Integration Testing Strategy
- Integration test structure defined in project layout
- End-to-end test scenarios documented
- Mock data generation approach specified

**✓ CONFIRMED**: No Unit Tests (Justified)
- Design focuses on integration and e2e testing
- Test structure reflects this priority
- Rationale remains valid for MVP

### Security & Compliance ✅

**✓ CONFIRMED**: FedRAMP 140-3 Compliance
- NIST algorithms specified in research.md
- TLS 1.3 for all communications
- Encryption strategy documented

**✓ CONFIRMED**: No Authentication for MVP (Justified)
- Design includes authentication placeholders
- Future authentication strategy documented
- MVP scope remains appropriate

### Code Quality Standards ✅

**✓ CONFIRMED**: All Standards Met
- Configuration-driven design throughout
- DRY principle applied (shared libraries, adapters)
- Comprehensive error handling in design
- Modular architecture with clear boundaries

### Final Assessment

**Status**: ✅ ALL GATES PASSED

All constitution principles are satisfied by the design. The architecture is sound, scalable, and aligned with project requirements. Ready to proceed to Phase 2 (Task Breakdown).

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
