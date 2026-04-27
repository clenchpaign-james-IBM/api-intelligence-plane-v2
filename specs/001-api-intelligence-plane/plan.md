# Implementation Plan: API Intelligence Plane

**Branch**: `001-api-intelligence-plane` | **Date**: 2026-03-09 | **Updated**: 2026-04-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-api-intelligence-plane/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

API Intelligence Plane is an AI-driven API management application that transforms API management from reactive firefighting to proactive, autonomous operations. **Built with vendor-neutral data models** and vendor-specific gateway adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter). It acts as an always-on intelligent companion to API Gateways, providing AI-driven visibility, decision-making, and automation for APIs. Core capabilities include autonomous API discovery (including shadow APIs), predictive health management (24-48 hours advance failure prediction), **separate security scanning and compliance monitoring features**, **unified performance optimization (caching, compression, and rate limiting)**, **vendor-neutral analytics integration with transactional data collection and drill-down capabilities**, and natural language query interface. **Gateway connections support flexible authentication with separate optional credentials for base_url and transactional_logs_url endpoints.**

**Latest Update (2026-04-10)**: **WebMethods-First Implementation Phase**. The system maintains vendor-neutral data models (`api.py:API`, `metric.py:Metric`, `transaction.py:TransactionalLog`) with vendor-specific adapters. **For the initial release, ONLY WebMethodsGatewayAdapter is implemented** using transformation from webMethods native models in `backend/app/models/webmethods/` (wm_api.py, wm_policy.py, wm_policy_action.py, wm_transaction.py). Kong and Apigee adapters are deferred to future phases. Vendor-specific fields stored in `vendor_metadata`. Metrics stored separately from API entities in time-bucketed indices (1m, 5m, 1h, 1d). Intelligence fields separated in `intelligence_metadata`.

**Key Architecture Update (2026-04-02)**: Security and Compliance have been separated into distinct features (User Stories 3 and 4) to address different audiences and urgency levels. Security focuses on immediate threat response for security engineers, while Compliance focuses on scheduled audit preparation for compliance officers.

**Previous Update (2026-03-29)**: Performance optimization and rate limiting have been merged into a single unified feature (User Story 5), as both are gateway-level performance optimization techniques. All optimization types (caching, compression, rate limiting) are now presented in a unified interface with consistent interaction patterns.

## Technical Context

**Language/Version**: Python 3.11+ (Backend), JavaScript/TypeScript (Frontend), Java (Demo API Gateway)
**Primary Dependencies**:
- Backend: FastAPI, LangChain, LangGraph, FastMCP, LiteLLM, OpenSearch Python client
- Frontend: React.js, React Router, Axios/Fetch API
- AI Framework: LangChain for agent orchestration, LangGraph for workflow management
- MCP: FastMCP for server/client implementation with Streamable HTTP transport
- Gateway: Spring Boot, OpenSearch Java client

**Prediction Architecture**: Single hybrid approach combining rule-based predictions (fast, deterministic baseline) followed by AI-enhanced analysis (deep insights, natural language explanations). AI enhancement is always applied to all predictions produced by the scheduler-driven prediction workflow, with graceful fallback metadata retained on each prediction if AI enhancement fails.

**Security Architecture**: Hybrid approach combining rule-based security checks with AI-enhanced analysis. Uses multi-source data analysis (API metadata, real-time metrics, traffic patterns) for accurate vulnerability detection. Real remediation via Gateway adapter with 6 security policy types: authentication, authorization, TLS, CORS, validation, and security headers. Focuses on immediate threat response.

**Compliance Architecture**: AI-driven compliance monitoring separate from security scanning. Detects violations for GDPR, HIPAA, SOC2, PCI-DSS, and ISO 27001. Maintains complete audit trails and generates comprehensive reports for external auditors. Focuses on scheduled audit preparation and regulatory reporting.

**Analytics Architecture**: ETL pipeline for vendor-neutral transactional data collection and aggregation. Three-model architecture (API metadata from `api.py:API`, TransactionalLog raw events from `transaction.py:TransactionalLog`, Metrics aggregated from `metric.py:Metric`). Multi-gateway support via gateway_id dimension. Time-series aggregation into 1-minute, 5-minute, 1-hour, and 1-day buckets with retention policies (1m/24h, 5m/7d, 1h/30d, 1d/90d). Drill-down pattern from aggregated metrics to raw transactional logs. Supports comprehensive vendor-neutral transactional event model with timing metrics, request/response data, external calls, and error tracking. **Initial phase: WebMethodsGatewayAdapter transforms from wm_transaction.py to vendor-neutral TransactionalLog.**

**WebMethods Integration Architecture**:
- **API Discovery**: Uses `GET /rest/apigateway/apis` for listing and `GET /rest/apigateway/apis/{api_id}` for detailed information
- **Policy Management**: Uses `GET /rest/apigateway/policies/{policy_id}` to read policies and `PUT /rest/apigateway/policies/{policy_id}` to update
- **Policy Actions**: Uses `GET /rest/apigateway/policyActions/{policyaction_id}` to read and `POST /rest/apigateway/policyActions` to create enforcement objects
- **Transactional Logs**: Queries OpenSearch with filter `eventType: "Transactional"` for analytics data
- **Policy Stages**: Supports multi-stage pipeline (transport, requestPayloadProcessing, IAM, LMT, routing, responseProcessing)
- **Data Transformation**: All WebMethods data transformed to vendor-neutral models with WebMethods-specific fields in `vendor_metadata`

**Data Model Architecture**:
- **API Model**: Uses vendor-neutral `base/api.py:API` with comprehensive structure including `policy_actions` (vendor-neutral types with `vendor_config`), `api_definition` (OpenAPI/Swagger), `endpoints`, `version_info`, `maturity_state`, `groups`, and intelligence plane fields in `intelligence_metadata` (`health_score`, `is_shadow`, `discovery_method`, `risk_score`, `security_score`). Vendor-specific fields in `vendor_metadata`. **Does NOT include** embedded metrics (stored separately). **Initial phase: WebMethodsGatewayAdapter transforms from webmethods/wm_api.py (480 lines) to vendor-neutral API model.**
- **Metric Model**: Uses vendor-neutral `base/metric.py:Metric` with time-bucketed structure (1m, 5m, 1h, 1d), `gateway_id` dimension, cache metrics (`cache_hit_count`, `cache_miss_count`, `cache_bypass_count`, `cache_hit_rate`), timing breakdown (`gateway_time_avg`, `backend_time_avg`), HTTP status code breakdown (2xx/3xx/4xx/5xx), and optional per-endpoint breakdown. Stored separately from API entities in time-bucketed OpenSearch indices. **Initial phase: Derived from webMethods TransactionalLog data.**
- **TransactionalLog Model**: Uses vendor-neutral `base/transaction.py:TransactionalLog` with comprehensive fields for timing, request/response, client info, caching, backend service details, error information, and external calls. Vendor-specific fields in `vendor_metadata`. **Initial phase: WebMethodsGatewayAdapter transforms from webmethods/wm_transaction.py (264 lines, 61 fields) to vendor-neutral TransactionalLog.**

**Storage**: OpenSearch (API inventory, metrics, AI insights, security findings, compliance violations, predictions, transactional logs, aggregated metrics)
**Testing**: pytest (Backend), Jest/React Testing Library (Frontend), JUnit (Gateway), Integration tests across all components, End-to-end tests using Demo API Gateway
**Target Platform**: Linux/macOS servers (Docker containers), Web browsers (Chrome, Firefox, Safari, Edge)
**Project Type**: Distributed web application with microservices architecture (Backend API + Frontend SPA + MCP Servers + Gateway)
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
- **Vendor-neutral architecture**: All gateways use vendor-specific adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter) that transform to vendor-neutral models. **Initial phase: Only WebMethodsGatewayAdapter implemented.**
- Background scheduler for periodic data collection
- Metrics stored separately from API entities (no embedded metrics)
- Intelligence fields separated in `intelligence_metadata` wrapper
- Vendor-specific fields stored in `vendor_metadata` dict

**Scale/Scope**:
- Support 1000+ APIs across multiple Gateway vendors
- 90-day historical data retention
- Multi-vendor Gateway integration (minimum 3 vendors). **Initial phase: 1 vendor (webMethods); Kong and Apigee deferred.**
- Real-time monitoring and prediction capabilities
- Automated remediation workflows

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Architecture Principles

**✓ PASS**: Microservices Architecture
- Backend API, Frontend SPA, MCP Servers, and Gateway are independently deployable
- Each component has clear boundaries and responsibilities
- Components communicate via well-defined interfaces (REST APIs, MCP protocol)

**✓ PASS**: Vendor-Neutral with Gateway Adapters
- All API Gateways use vendor-specific adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter)
- All adapters transform vendor-specific data to vendor-neutral models (`api.py:API`, `metric.py:Metric`, `transaction.py:TransactionalLog`)
- Vendor-specific fields stored in `vendor_metadata` dict for extensibility
- Consistent intelligence plane functionality (predictions, security, compliance, optimization) regardless of source gateway
- **Initial phase: Only WebMethodsGatewayAdapter implemented; Kong and Apigee deferred**

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
│   └── gateway-api.yaml  # Gateway API specification
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
│   │   │   │   ├── compliance.py
│   │   │   │   ├── optimization.py
│   │   │   │   ├── rate_limits.py
│   │   │   │   └── query.py
│   │   │   └── deps.py        # Dependency injection
│   │   ├── models/            # Pydantic models
│   │   │   ├── api.py         # Vendor-neutral API model
│   │   │   ├── gateway.py
│   │   │   ├── metric.py      # Vendor-neutral Metric model
│   │   │   ├── prediction.py  # Includes ContributingFactorType enum (13 types)
│   │   │   ├── vulnerability.py  # Security vulnerabilities only
│   │   │   ├── compliance.py  # Compliance violations (separate from security)
│   │   │   ├── recommendation.py
│   │   │   ├── rate_limit.py
│   │   │   ├── query.py
│   │   │   ├── transaction.py  # Vendor-neutral TransactionalLog model (raw events)
│   │   │   └── webmethods/    # WebMethods native models (for transformation)
│   │   │       ├── __init__.py
│   │   │       ├── wm_api.py  # WebMethods API model (480 lines, comprehensive OpenAPI structure)
│   │   │       ├── wm_policy.py  # WebMethods Policy models (271 lines)
│   │   │       ├── wm_policy_action.py  # WebMethods Policy Action models (1184 lines, 10 policy types)
│   │   │       └── wm_transaction.py  # WebMethods TransactionalLog model (264 lines, 61 fields)
│   │   ├── services/          # Business logic
│   │   │   ├── discovery_service.py
│   │   │   ├── metrics_service.py
│   │   │   ├── prediction_service.py  # Hybrid: rule-based + AI enhancement
│   │   │   ├── security_service.py  # Security scanning and remediation (immediate response)
│   │   │   ├── compliance_service.py  # Compliance monitoring and audit reporting (scheduled)
│   │   │   ├── optimization_service.py
│   │   │   ├── query_service.py
│   │   │   ├── llm_service.py  # LiteLLM integration with fallback
│   │   │   └── wm_analytics_service.py  # WebMethods transactional log collection and aggregation
│   │   ├── agents/            # LangChain/LangGraph agents
│   │   │   ├── prediction_agent.py
│   │   │   ├── security_agent.py  # Security vulnerability detection and remediation
│   │   │   ├── compliance_agent.py  # Compliance violation detection (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
│   │   │   ├── optimization_agent.py
│   │   │   └── query_agent.py
│   │   ├── adapters/          # Gateway adapters (Strategy + Adapter pattern)
│   │   │   ├── base.py        # Base adapter interface defining transformation methods
│   │   │   ├── webmethods_gateway.py  # WebMethods → vendor-neutral transformation (INITIAL PHASE)
│   │   │   ├── gateway.py        # Gateway (development/testing)
│   │   │   ├── kong_gateway.py        # Kong → vendor-neutral transformation (DEFERRED)
│   │   │   ├── apigee_gateway.py      # Apigee → vendor-neutral transformation (DEFERRED)
│   │   │   └── factory.py     # Adapter factory for vendor selection
│   │   ├── db/                # OpenSearch client and operations
│   │   │   ├── client.py
│   │   │   ├── repositories/
│   │   │   └── migrations/
│   │   ├── scheduler/         # APScheduler jobs
│   │   │   ├── discovery_jobs.py
│   │   │   ├── metrics_jobs.py
│   │   │   ├── security_jobs.py
│   │   │   ├── compliance_jobs.py
│   │   │   └── wm_analytics_jobs.py  # WebMethods log collection and aggregation (every 5 minutes)
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
│   │   │   ├── compliance/
│   │   │   ├── query/
│   │   │   └── analytics/  # WebMethods Analytics components
│   │   ├── pages/           # Page components
│   │   │   ├── Dashboard.tsx
│   │   │   ├── APIs.tsx
│   │   │   ├── Gateways.tsx
│   │   │   ├── Predictions.tsx
│   │   │   ├── Security.tsx
│   │   │   ├── Compliance.tsx
│   │   │   ├── Optimization.tsx
│   │   │   ├── Query.tsx
│   │   │   └── Analytics.tsx  # WebMethods Analytics dashboard
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
├── mcp-servers/              # MCP server (FastMCP)
│   ├── unified_server.py     # Unified MCP server (all functionality)
│   ├── common/
│   │   ├── mcp_base.py      # Base MCP server class
│   │   └── opensearch.py    # Shared OpenSearch client
│   ├── requirements.txt
│   └── Dockerfile
│
├── gateway/             # Native API Gateway (Java/Spring Boot)
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
│   └── gateway/
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
1. **Clear Separation**: Backend, Frontend, MCP Servers, and Gateway are independently deployable
2. **Microservices**: Each MCP server is a separate service with specific responsibilities
3. **Scalability**: Components can be scaled independently based on load
4. **Technology Diversity**: Supports Python (Backend/MCP), JavaScript/TypeScript (Frontend), and Java (Gateway)
5. **Testing Strategy**: Separate integration and e2e test directories for cross-component testing
6. **Configuration Management**: Centralized config directory with environment-specific files
7. **Deployment Flexibility**: Docker Compose for local dev, Kubernetes manifests for production
8. **Vendor-Neutral Design**: WebMethods native models in `backend/app/models/webmethods/` for transformation to vendor-neutral models

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
- **Initial phase: Only WebMethodsGatewayAdapter implemented**

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
