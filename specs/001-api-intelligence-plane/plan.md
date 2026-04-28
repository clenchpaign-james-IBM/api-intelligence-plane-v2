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

**Architecture**: Vendor-neutral with gateway-specific adapters

**Data Models**:
- **Vendor-Neutral**: `base/api.py`, `base/metric.py`, `base/transaction.py`
- **WebMethods-Specific**: `webmethods/wm_api.py`, `webmethods/wm_policy_action.py`, `webmethods/wm_transaction.py`

**Policy System**:
- **Structured Configs**: 11 Pydantic models for type-safe configurations
- **Normalizer**: WebMethods → Vendor-Neutral transformation
- **Denormalizer**: Vendor-Neutral → WebMethods transformation

**Metrics Architecture**:
- **Time-Bucketed**: 1m, 5m, 1h, 1d with monthly index rotation
- **Separate Storage**: Not embedded in API documents
- **Drill-Down**: Trace from metrics to raw transactional logs

**WebMethods Integration**:
- **REST API**: Complete integration with WebMethods API Gateway
- **OpenSearch**: Transactional log collection
- **Policy Application**: Real Gateway policy changes
- **Analytics**: Full analytics pipeline with aggregation

### Architecture Overview

**Vendor-Neutral Design**: The system uses vendor-neutral data models with gateway-specific adapters:

- **Vendor-Neutral Models**:
  - [`base/api.py:API`](../../backend/app/models/base/api.py) (600+ lines) - API metadata
  - [`base/metric.py:Metric`](../../backend/app/models/base/metric.py) (400+ lines) - Time-bucketed metrics
  - [`base/transaction.py:TransactionalLog`](../../backend/app/models/base/transaction.py) (350+ lines) - Raw transactional events
  - [`base/policy_configs.py`](../../backend/app/models/base/policy_configs.py) - 11 structured policy configuration models

- **Gateway Adapters**:
  - [`WebMethodsGatewayAdapter`](../../backend/app/adapters/webmethods_gateway.py) (800+ lines) - **IMPLEMENTED**
  - KongGatewayAdapter - **DEFERRED**
  - ApigeeGatewayAdapter - **DEFERRED**

- **Policy Conversion**: Normalizer/denormalizer pattern for bidirectional transformation
  - [`policy_normalizer.py`](../../backend/app/utils/webmethods/policy_normalizer.py) - Vendor-specific → Vendor-neutral (structured Pydantic configs)
  - [`policy_denormalizer.py`](../../backend/app/utils/webmethods/policy_denormalizer.py) - Vendor-neutral → Vendor-specific (supports both dict and structured)

- **Time-Bucketed Metrics**: Separate storage with 4 time buckets (1m, 5m, 1h, 1d) with monthly index rotation
- **Gateway-First Operations**: All operations scoped by gateway_id

**WebMethods-Specific Models** (Initial Phase):
- [`webmethods/wm_api.py`](../../backend/app/models/webmethods/wm_api.py) (480 lines) - Native WebMethods API structure
- [`webmethods/wm_policy_action.py`](../../backend/app/models/webmethods/wm_policy_action.py) (1184 lines) - Native policy action models
- [`webmethods/wm_transaction.py`](../../backend/app/models/webmethods/wm_transaction.py) (264 lines, 61 fields) - Native transactional log structure

**MCP Server Architecture**:
- **Implementation**: Single unified server ([`mcp-servers/unified_server.py`](../../mcp-servers/unified_server.py), 2000+ lines, port 8007)
- **Previous**: 6 individual servers (ports 8001-8006) - **DEPRECATED**
- **Features**: 80+ tools across 10 categories, thin wrapper over backend REST API, single connection point
- **Migration**: See [`docs/UNIFIED_MCP_SERVER_MIGRATION.md`](../../docs/UNIFIED_MCP_SERVER_MIGRATION.md)

**Model Architecture Details**:

1. **API Model** (`base/api.py:API`):
   ```python
   class API(BaseModel):
       id: UUID
       gateway_id: UUID  # Gateway association
       name: str
       version_info: VersionInfo  # Structured version
       api_definition: Optional[APIDefinition]  # OpenAPI spec
       policy_actions: List[PolicyAction]  # Type-safe policies
       intelligence_metadata: IntelligenceMetadata  # AI-derived fields
       vendor_metadata: Dict[str, Any]  # Vendor extensibility
   ```
   - ❌ Removed: `current_metrics` (now separate)
   - ✅ Added: `gateway_id`, `policy_actions`, `intelligence_metadata`, `vendor_metadata`
   - ✅ Enhanced: Structured `version_info` and `api_definition`

2. **Metric Model** (`base/metric.py:Metric`):
   - **Storage**: Separate time-bucketed indices `api-metrics-{bucket}-{YYYY.MM}`
   - **Time Buckets**: 1m (24h), 5m (7d), 1h (30d), 1d (90d)
   - **Dimensions**: gateway_id, api_id, application_id, operation, timestamp, time_bucket
   - **Metrics**: Response times (avg/min/max/p50/p95/p99), error rates, throughput, cache metrics, timing breakdown

3. **TransactionalLog Model** (`base/transaction.py:TransactionalLog`):
   - **Purpose**: Raw transactional event storage for analytics and drill-down
   - **Fields**: 61 comprehensive fields including timing, request/response, client info, caching, backend service details, error information, external calls
   - **Storage**: Daily indices `transactional-logs-YYYY.MM.DD`

4. **Policy Configuration Models** (`base/policy_configs.py`):
   - 11 Pydantic models for type-safe policy configurations:
     1. AuthenticationConfig, 2. AuthorizationConfig, 3. RateLimitConfig, 4. CachingConfig, 5. CompressionConfig, 6. TLSConfig, 7. CORSConfig, 8. ValidationConfig, 9. SecurityHeadersConfig, 10. LoggingConfig, 11. TransformationConfig

**Prediction Architecture**: Single hybrid approach combining rule-based predictions (fast, deterministic baseline) followed by AI-enhanced analysis (deep insights, natural language explanations). AI enhancement is always applied to all predictions produced by the scheduler-driven prediction workflow, with graceful fallback metadata retained on each prediction if AI enhancement fails.

**Security Architecture**: Hybrid approach combining rule-based security checks with AI-enhanced analysis. Uses multi-source data analysis (API metadata, real-time metrics, traffic patterns) for accurate vulnerability detection. Real remediation via Gateway adapter with 6 security policy types: authentication, authorization, TLS, CORS, validation, and security headers. Focuses on immediate threat response.

**Compliance Architecture**: AI-driven compliance monitoring separate from security scanning. Detects violations for GDPR, HIPAA, SOC2, PCI-DSS, and ISO 27001. Maintains complete audit trails and generates comprehensive reports for external auditors. Focuses on scheduled audit preparation and regulatory reporting.

**Analytics Architecture**: ETL pipeline for vendor-neutral transactional data collection and aggregation. Three-model architecture (API metadata from `api.py:API`, TransactionalLog raw events from `transaction.py:TransactionalLog`, Metrics aggregated from `metric.py:Metric`). Multi-gateway support via gateway_id dimension. Time-series aggregation into 1-minute, 5-minute, 1-hour, and 1-day buckets with retention policies (1m/24h, 5m/7d, 1h/30d, 1d/90d). Drill-down pattern from aggregated metrics to raw transactional logs. Supports comprehensive vendor-neutral transactional event model with timing metrics, request/response data, external calls, and error tracking. **Initial phase: WebMethodsGatewayAdapter transforms from wm_transaction.py to vendor-neutral TransactionalLog.**

**WebMethods Integration Architecture**:

### REST API Endpoints

1. **API Discovery & Management**:
   - `GET /rest/apigateway/apis` - List all APIs registered in the gateway
     - Returns: Array of API summaries with basic metadata (name, version, id, status)
     - Used for: Initial discovery and periodic synchronization
   
   - `GET /rest/apigateway/apis/{api_id}` - Get detailed API information
     - Returns: Complete API details including OpenAPI specification, policies, endpoints, versions
     - Key fields: `apiDefinition` (OpenAPI spec), `nativeEndpoint` (backend URLs), `policies` (policy IDs), `gatewayEndPointList` (exposed endpoints)
     - Used for: Detailed API analysis, policy extraction, endpoint mapping

2. **Policy Management**:
   - `GET /rest/apigateway/policies/{policy_id}` - Get policy configuration
     - Returns: Policy with enforcement stages and attached policy actions
     - Policy stages: `transport`, `requestPayloadProcessing`, `IAM`, `LMT`, `routing`, `responseProcessing`
     - Used for: Understanding current security/optimization policies
   
   - `PUT /rest/apigateway/policies/{policy_id}` - Update policy configuration
     - Request: Modified policy with updated `policyEnforcements` array
     - Used for: Applying security fixes and optimization recommendations

3. **Policy Actions (Enforcement Objects)**:
   - `GET /rest/apigateway/policyActions/{policyaction_id}` - Get policy action configuration
     - Returns: Policy action with `templateKey` (type) and `parameters` (configuration)
     - Template examples: `validateAPISpec`, `requireHTTPS`, `rateLimiting`, `authentication`
     - Used for: Understanding individual policy configurations
   
   - `POST /rest/apigateway/policyActions` - Create new policy action
     - Request: Policy action with `templateKey` and `parameters`
     - Returns: Created policy action with assigned ID
     - Used for: Creating new security/optimization policies

4. **Transactional Logs (Analytics)**:
   - OpenSearch Query - Query transactional event logs
     - Filter: `eventType: "Transactional"`
     - Returns: Raw transactional events with timing, request/response data, errors, cache metrics
     - Key fields: `totalTime`, `providerTime` (backend), `gatewayTime`, `statusCode`, `applicationId`, `cacheHit`, `externalCalls`
     - Used for: Metrics aggregation, performance analysis, drill-down queries

### Data Transformation Flow

1. **API Discovery**: `GET /apis` → Transform to vendor-neutral `api.py:API`
2. **API Details**: `GET /apis/{id}` → Extract OpenAPI spec, policies, endpoints → Store in `api_definition`, `policy_actions`, `vendor_metadata`
3. **Policy Reading**: `GET /policies/{id}` → Transform to vendor-neutral `PolicyAction` with `vendor_config`
4. **Policy Application**: Create `PolicyAction` → `POST /policyActions` → `PUT /policies/{id}` to attach
5. **Analytics Collection**: OpenSearch query → Transform to vendor-neutral `TransactionalLog` → Aggregate to `Metric`

### WebMethodsGatewayAdapter Responsibilities

The [`WebMethodsGatewayAdapter`](../../backend/app/adapters/webmethods_gateway.py) implements the following transformations:

1. **API Transformation**: WebMethods API response → Vendor-neutral API model
   - Maps `apiDefinition` to `api_definition` (OpenAPI structure)
   - Extracts policy IDs and transforms to `policy_actions` array
   - Stores WebMethods-specific fields in `vendor_metadata`
   - Populates `intelligence_metadata` with discovery information

2. **Policy Transformation**: WebMethods Policy/PolicyAction → Vendor-neutral PolicyAction
   - Maps `templateKey` to vendor-neutral policy type
   - Stores WebMethods parameters in `vendor_config`
   - Handles policy stage mapping (transport, IAM, LMT, etc.)

3. **Transactional Log Collection**: OpenSearch query → Vendor-neutral TransactionalLog
   - Transforms WebMethods field names to vendor-neutral names (`providerTime` → `backend_time_ms`)
   - Extracts timing metrics, error information, cache data
   - Stores WebMethods-specific fields in `vendor_metadata`

4. **Policy Application**: Vendor-neutral PolicyAction → WebMethods API calls
   - Creates policy actions via `POST /policyActions`
   - Attaches to policies via `PUT /policies/{id}`
   - Verifies application through re-reading

See [`research/webmethods-api-endpoints-summary.md`](../../research/webmethods-api-endpoints-summary.md) for detailed API documentation.

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
- All gateways use vendor-specific adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter)
- All adapters transform to vendor-neutral models (`base/api.py:API`, `base/metric.py:Metric`, `base/transaction.py:TransactionalLog`)
- Vendor-specific fields in `vendor_metadata` for extensibility
- Consistent intelligence plane functionality (predictions, security, compliance, optimization) regardless of gateway vendor
- **Initial phase**: Only WebMethodsGatewayAdapter implemented; Kong and Apigee deferred to future phases

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
│   │   │   ├── base/                    # Vendor-neutral models
│   │   │   │   ├── api.py
│   │   │   │   ├── metric.py
│   │   │   │   ├── transaction.py
│   │   │   │   ├── policy_configs.py   # 11 structured configs
│   │   │   │   └── policy_helpers.py
│   │   │   ├── webmethods/             # WebMethods-specific
│   │   │   │   ├── wm_api.py
│   │   │   │   ├── wm_policy.py
│   │   │   │   ├── wm_policy_action.py
│   │   │   │   └── wm_transaction.py
│   │   │   ├── gateway.py
│   │   │   ├── prediction.py  # Includes ContributingFactorType enum (13 types)
│   │   │   ├── vulnerability.py  # Security vulnerabilities only
│   │   │   ├── compliance.py  # Compliance violations (separate from security)
│   │   │   ├── recommendation.py
│   │   │   ├── rate_limit.py
│   │   │   └── query.py
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
