# Tasks: API Intelligence Plane

**Input**: Design documents from `/specs/001-api-intelligence-plane/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Tests are NOT required per project specification. Focus is on integration and end-to-end testing.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

This is a distributed web application with microservices architecture:
- **Backend**: `backend/app/`
- **Frontend**: `frontend/src/`
- **MCP Servers**: `mcp-servers/`
- **Demo Gateway**: `demo-gateway/src/main/java/`
- **Tests**: `tests/integration/` and `tests/e2e/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure per plan.md (backend/, frontend/, mcp-servers/, demo-gateway/, tests/, config/, k8s/, docs/)
- [X] T002 Initialize Python backend project with requirements.txt (FastAPI, LangChain, LangGraph, FastMCP, LiteLLM, OpenSearch client, APScheduler, pytest)
- [X] T003 [P] Initialize React frontend project with package.json (React 18, Vite, React Router, TanStack Query, Recharts, Tailwind CSS, TypeScript)
- [X] T004 [P] Initialize Java Demo Gateway project with pom.xml (Spring Boot 3.2, OpenSearch Java client, Micrometer)
- [X] T005 [P] Create Docker Compose configuration in docker-compose.yml for local development
- [X] T006 [P] Create environment configuration template in .env.example
- [X] T007 [P] Setup linting and formatting tools (Black, isort, flake8 for Python; ESLint, Prettier for TypeScript)
- [X] T008 [P] Create README.md with project overview and setup instructions
- [X] T009 [P] Initialize Git repository with .gitignore for Python, Node, Java, and IDE files

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### OpenSearch Setup

- [X] T010 Create OpenSearch initialization script in backend/scripts/init_opensearch.py
- [X] T011 Define OpenSearch index templates for api-inventory in backend/app/db/migrations/001_api_inventory.py
- [X] T012 [P] Define OpenSearch index templates for api-metrics-* in backend/app/db/migrations/002_api_metrics.py
- [X] T013 [P] Define OpenSearch index templates for api-predictions in backend/app/db/migrations/003_predictions.py
- [X] T014 [P] Define OpenSearch index templates for security-findings in backend/app/db/migrations/004_security.py
- [X] T015 [P] Define OpenSearch index templates for optimization-recommendations in backend/app/db/migrations/005_optimization.py
- [X] T016 [P] Define OpenSearch index templates for rate-limit-policies in backend/app/db/migrations/006_rate_limits.py
- [X] T017 [P] Define OpenSearch index templates for query-history in backend/app/db/migrations/007_queries.py

### Backend Core Infrastructure

- [X] T018 Create OpenSearch client wrapper in backend/app/db/client.py with connection pooling and error handling
- [X] T019 Create base repository class in backend/app/db/repositories/base.py with CRUD operations
- [X] T020 Create configuration management in backend/app/config.py using Pydantic Settings
- [X] T021 [P] Setup FastAPI application structure in backend/app/main.py with CORS, error handlers, and health endpoint
- [X] T022 [P] Create dependency injection setup in backend/app/api/deps.py for OpenSearch client and services
- [X] T023 [P] Implement error handling middleware in backend/app/middleware/error_handler.py
- [X] T024 [P] Setup logging configuration in backend/app/utils/logging.py with structured logging
- [X] T025 [P] Create APScheduler setup in backend/app/scheduler/__init__.py for background jobs

### Pydantic Models (Data Layer)

- [X] T026 [P] Create Gateway model in backend/app/models/gateway.py per data-model.md
- [X] T027 [P] Create API model in backend/app/models/api.py per data-model.md
- [X] T028 [P] Create Metric model in backend/app/models/metric.py per data-model.md
- [X] T029 [P] Create Prediction model in backend/app/models/prediction.py per data-model.md
- [X] T030 [P] Create Vulnerability model in backend/app/models/vulnerability.py per data-model.md
- [X] T031 [P] Create OptimizationRecommendation model in backend/app/models/recommendation.py per data-model.md
- [X] T032 [P] Create RateLimitPolicy model in backend/app/models/rate_limit.py per data-model.md
- [X] T033 [P] Create Query model in backend/app/models/query.py per data-model.md

### Gateway Adapter Pattern (Strategy + Adapter)

- [X] T034 Create base Gateway strategy interface in backend/app/adapters/base.py with abstract methods
- [X] T035 [P] Implement Native Gateway adapter in backend/app/adapters/native_gateway.py
- [X] T036 [P] Create Gateway adapter factory in backend/app/adapters/factory.py for strategy selection
- [X] T037 [P] Add Kong Gateway adapter stub in backend/app/adapters/kong_gateway.py (placeholder for future)
- [X] T038 [P] Add Apigee Gateway adapter stub in backend/app/adapters/apigee_gateway.py (placeholder for future)

### LLM Integration

- [X] T039 Setup LiteLLM configuration in backend/app/services/llm_service.py with provider fallback chain
- [X] T040 Create LLM testing script in backend/scripts/test_llm.py for validating provider connections

### MCP Server Foundation

- [X] T041 Create base MCP server class in mcp-servers/common/mcp_base.py using FastMCP
- [X] T042 [P] Create shared OpenSearch client for MCP servers in mcp-servers/common/opensearch.py
- [X] T043 [P] Setup MCP server health endpoint template in mcp-servers/common/health.py

### Demo Gateway Foundation

- [X] T044 Create Spring Boot application entry point in demo-gateway/src/main/java/com/example/gateway/GatewayApplication.java
- [X] T045 [P] Configure OpenSearch connection in demo-gateway/src/main/resources/application.yml
- [X] T046 [P] Create base API model in demo-gateway/src/main/java/com/example/gateway/model/API.java
- [X] T047 [P] Create base Policy model in demo-gateway/src/main/java/com/example/gateway/model/Policy.java
- [X] T048 [P] Setup OpenSearch repository in demo-gateway/src/main/java/com/example/gateway/repository/APIRepository.java

### Frontend Foundation

- [X] T049 Setup React Router configuration in frontend/src/App.tsx with route definitions
- [X] T050 [P] Create API client service in frontend/src/services/api.ts with Axios/Fetch wrapper
- [X] T051 [P] Setup TanStack Query configuration in frontend/src/main.tsx
- [X] T052 [P] Create common UI components in frontend/src/components/common/ (Button, Card, Table, Loading, Error)
- [X] T053 [P] Setup Tailwind CSS configuration in frontend/tailwind.config.ts

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Discover and Monitor All APIs (Priority: P1) 🎯 MVP

**Goal**: Automatically discover all APIs (including shadow APIs) and continuously monitor their health

**Independent Test**: Connect to Demo Gateway, observe automatic discovery of APIs, view real-time health metrics on dashboard

### Backend - Discovery Service

- [X] T054 [P] [US1] Create API repository in backend/app/db/repositories/api_repository.py with CRUD and search operations
- [X] T055 [P] [US1] Create Gateway repository in backend/app/db/repositories/gateway_repository.py with CRUD operations
- [X] T056 [P] [US1] Create Metrics repository in backend/app/db/repositories/metrics_repository.py with time-series operations
- [X] T057 [US1] Implement Discovery Service in backend/app/services/discovery_service.py with API discovery logic
- [X] T058 [US1] Implement Metrics Service in backend/app/services/metrics_service.py with metrics collection and aggregation
- [X] T059 [US1] Create discovery scheduler job in backend/app/scheduler/discovery_jobs.py (runs every 5 minutes)
- [X] T060 [US1] Create metrics collection scheduler job in backend/app/scheduler/metrics_jobs.py (runs every 1 minute)

### Backend - REST API Endpoints

- [X] T061 [P] [US1] Implement Gateway endpoints in backend/app/api/v1/gateways.py per backend-api.yaml (POST, GET, PUT, DELETE /gateways)
- [X] T062 [P] [US1] Implement API endpoints in backend/app/api/v1/apis.py per backend-api.yaml (GET /apis, GET /apis/{id})
- [X] T063 [P] [US1] Implement Metrics endpoints in backend/app/api/v1/metrics.py per backend-api.yaml (GET /apis/{id}/metrics)

### MCP - Discovery Server

- [X] T064 [US1] Create Discovery MCP server in mcp-servers/discovery_server.py with FastMCP
- [X] T065 [P] [US1] Implement discover_apis tool in mcp-servers/discovery_server.py per mcp-tools.md
- [X] T066 [P] [US1] Implement get_api_inventory tool in mcp-servers/discovery_server.py per mcp-tools.md
- [X] T067 [P] [US1] Implement search_apis tool in mcp-servers/discovery_server.py per mcp-tools.md

### MCP - Metrics Server

- [X] T068 [US1] Create Metrics MCP server in mcp-servers/metrics_server.py with FastMCP
- [X] T069 [P] [US1] Implement collect_metrics tool in mcp-servers/metrics_server.py per mcp-tools.md
- [X] T070 [P] [US1] Implement get_metrics_timeseries tool in mcp-servers/metrics_server.py per mcp-tools.md
- [X] T071 [P] [US1] Implement analyze_trends tool in mcp-servers/metrics_server.py per mcp-tools.md

### Demo Gateway - API Management

- [X] T072 [US1] Implement Gateway info endpoint in demo-gateway/src/main/java/com/example/gateway/controller/GatewayController.java (GET /gateway/info, GET /gateway/capabilities)
- [X] T073 [US1] Implement API management endpoints in demo-gateway/src/main/java/com/example/gateway/controller/APIController.java (POST, GET, PUT, DELETE /apis)
- [X] T074 [US1] Implement API service layer in demo-gateway/src/main/java/com/example/gateway/service/APIService.java
- [X] T075 [US1] Implement metrics collection in demo-gateway/src/main/java/com/example/gateway/service/MetricsService.java
- [X] T076 [US1] Implement metrics export endpoint in demo-gateway/src/main/java/com/example/gateway/controller/MetricsController.java (GET /metrics/apis, GET /metrics/apis/{id})

### Frontend - Dashboard & API Views

- [X] T077 [US1] Create Dashboard page in frontend/src/pages/Dashboard.tsx with overview widgets
- [X] T078 [US1] Create APIs page in frontend/src/pages/APIs.tsx with API list and filters
- [X] T079 [US1] Create Gateways page in frontend/src/pages/Gateways.tsx with gateway management
- [X] T080 [P] [US1] Create API list component in frontend/src/components/apis/APIList.tsx
- [X] T081 [P] [US1] Create API detail component in frontend/src/components/apis/APIDetail.tsx
- [X] T082 [P] [US1] Create health metrics chart component in frontend/src/components/metrics/HealthChart.tsx using Recharts
- [X] T083 [P] [US1] Create Gateway service client in frontend/src/services/gateway.ts
- [X] T084 [P] [US1] Create Metrics service client in frontend/src/services/metrics.ts
- [X] T085 [US1] Implement real-time metrics updates using WebSocket or SSE in frontend/src/hooks/useRealtimeMetrics.ts

### Frontend - Gateway Management UI

- [X] T086 [P] [US1] Create AddGatewayForm component in frontend/src/components/gateways/AddGatewayForm.tsx with form validation
- [X] T087 [P] [US1] Add "Add Gateway" button to Dashboard page in frontend/src/pages/Dashboard.tsx
- [X] T088 [P] [US1] Add "Add Gateway" button to Gateways page in frontend/src/pages/Gateways.tsx
- [X] T089 [US1] Implement gateway sync endpoint in backend/app/api/v1/gateways.py (POST /gateways/{id}/sync)
- [X] T090 [US1] Add gateway sync button handlers in frontend/src/pages/Gateways.tsx

### Integration & Validation

- [X] T091 [US1] Create integration test for discovery flow in tests/integration/test_discovery_flow.py
- [X] T092 [US1] Create integration test for metrics collection in tests/integration/test_metrics_collection.py
- [X] T093 [US1] Create traffic generator script in backend/scripts/generate_traffic.py for testing
- [X] T094 [US1] Validate User Story 1 using quickstart.md steps 1-4

**Checkpoint**: User Story 1 complete - APIs can be discovered and monitored independently

---

## Phase 4: User Story 2 - Predict and Prevent API Failures (Priority: P1)

**Goal**: Receive advance warnings of potential API failures 24-48 hours before they occur

**Independent Test**: Simulate degrading API conditions, verify predictions are generated 24-48 hours in advance

### Backend - Prediction Service

- [X] T095 [P] [US2] Create Prediction repository in backend/app/db/repositories/prediction_repository.py with CRUD and query operations
- [X] T096 [US2] Implement Prediction Service in backend/app/services/prediction_service.py with ML-based prediction logic
- [-] T097 [US2] Create Prediction Agent in backend/app/agents/prediction_agent.py using LangChain/LangGraph
- [X] T098 [US2] Implement prediction generation workflow in backend/app/agents/prediction_agent.py with contributing factors analysis
- [X] T099 [US2] Create prediction scheduler job in backend/app/scheduler/prediction_jobs.py (runs every 15 minutes)
- [X] T100 [US2] Implement prediction accuracy tracking in backend/app/services/prediction_service.py

### Backend - REST API Endpoints

- [X] T101 [P] [US2] Implement Prediction endpoints in backend/app/api/v1/predictions.py per backend-api.yaml (GET /predictions, GET /predictions/{id})

### MCP - Optimization Server (Predictions)

- [X] T102 [US2] Create Optimization MCP server in mcp-servers/optimization_server.py with FastMCP
- [X] T103 [P] [US2] Implement generate_predictions tool in mcp-servers/optimization_server.py per mcp-tools.md

### Frontend - Predictions View

- [X] T104 [US2] Create Predictions page in frontend/src/pages/Predictions.tsx with prediction list and filters
- [X] T105 [P] [US2] Create prediction card component in frontend/src/components/predictions/PredictionCard.tsx
- [X] T106 [P] [US2] Create prediction timeline component in frontend/src/components/predictions/PredictionTimeline.tsx
- [X] T107 [P] [US2] Create contributing factors visualization in frontend/src/components/predictions/FactorsChart.tsx

### Test Data Generation

- [X] T107a [P] [US2] Create mock prediction data generator in backend/scripts/generate_mock_predictions.py
- [X] T107b [P] [US2] Create test fixtures for prediction scenarios in backend/tests/fixtures/prediction_fixtures.py
- [X] T107c [P] [US2] Create degrading metrics generator utility in backend/tests/utils/metrics_generator.py

### Integration & Validation

- [X] T108 [US2] Create integration test for prediction generation in tests/integration/test_prediction_generation.py
- [X] T109 [US2] Create end-to-end test for prediction workflow in tests/e2e/test_prediction_workflow.py
- [X] T110 [US2] Validate User Story 2 independently with simulated degrading conditions

**Checkpoint**: User Story 2 complete - Predictions are generated and displayed independently

---

## Phase 5: User Story 3 - Automated Security Scanning and Remediation (Priority: P2)

**Goal**: Continuous security scanning with automated remediation of common vulnerabilities

**Independent Test**: Deploy APIs with known security issues, verify detection and automated remediation

### Backend - Security Service

- [ ] T111 [P] [US3] Create Vulnerability repository in backend/app/db/repositories/vulnerability_repository.py with CRUD and query operations
- [ ] T112 [US3] Implement Security Service in backend/app/services/security_service.py with vulnerability scanning logic
- [ ] T113 [US3] Create Security Agent in backend/app/agents/security_agent.py using LangChain/LangGraph
- [ ] T114 [US3] Implement automated remediation workflow in backend/app/agents/security_agent.py
- [ ] T115 [US3] Create security scanning scheduler job in backend/app/scheduler/security_jobs.py (runs every 1 hour)
- [ ] T116 [US3] Implement remediation verification in backend/app/services/security_service.py

### Backend - REST API Endpoints

- [ ] T117 [P] [US3] Implement Security endpoints in backend/app/api/v1/security.py per backend-api.yaml (GET /vulnerabilities, POST /vulnerabilities/{id}/remediate)

### MCP - Security Server

- [ ] T118 [US3] Create Security MCP server in mcp-servers/security_server.py with FastMCP
- [ ] T119 [P] [US3] Implement scan_api_security tool in mcp-servers/security_server.py per mcp-tools.md
- [ ] T120 [P] [US3] Implement remediate_vulnerability tool in mcp-servers/security_server.py per mcp-tools.md
- [ ] T121 [P] [US3] Implement get_security_posture tool in mcp-servers/security_server.py per mcp-tools.md

### Frontend - Security View

- [ ] T122 [US3] Create Security page in frontend/src/pages/Security.tsx with vulnerability list and security posture
- [ ] T123 [P] [US3] Create vulnerability card component in frontend/src/components/security/VulnerabilityCard.tsx
- [ ] T124 [P] [US3] Create security posture dashboard in frontend/src/components/security/SecurityDashboard.tsx
- [ ] T125 [P] [US3] Create remediation status tracker in frontend/src/components/security/RemediationTracker.tsx

### Integration & Validation

- [ ] T126 [US3] Create integration test for security scanning in tests/integration/test_security_scanning.py
- [ ] T127 [US3] Create end-to-end test for remediation workflow in tests/e2e/test_remediation_workflow.py
- [ ] T128 [US3] Validate User Story 3 independently with known vulnerabilities

**Checkpoint**: User Story 3 complete - Security scanning and remediation work independently

---

## Phase 6: User Story 4 - Real-time Performance Optimization (Priority: P2)

**Goal**: Real-time recommendations for optimizing API performance based on usage patterns

**Independent Test**: Monitor APIs under load, verify optimization recommendations are generated with estimated impact

### Backend - Optimization Service

- [x] T129 [P] [US4] Create OptimizationRecommendation repository in backend/app/db/repositories/recommendation_repository.py
- [x] T130 [US4] Implement Optimization Service in backend/app/services/optimization_service.py with recommendation generation
- [x] T131 [US4] Create Optimization Agent in backend/app/agents/optimization_agent.py using LangChain/LangGraph
- [x] T132 [US4] Implement optimization analysis workflow in backend/app/agents/optimization_agent.py
- [x] T133 [US4] Create optimization scheduler job in backend/app/scheduler/optimization_jobs.py (runs every 30 minutes)
- [x] T134 [US4] Implement recommendation validation and impact tracking in backend/app/services/optimization_service.py

### Backend - REST API Endpoints

- [x] T135 [P] [US4] Implement Optimization endpoints in backend/app/api/v1/optimization.py per backend-api.yaml (GET /recommendations)

### MCP - Optimization Server (Recommendations)

- [x] T136 [P] [US4] Implement generate_optimization_recommendations tool in mcp-servers/optimization_server.py per mcp-tools.md

### Frontend - Optimization View

- [x] T137 [US4] Create Optimization page in frontend/src/pages/Optimization.tsx with recommendations list
- [x] T138 [P] [US4] Create recommendation card component in frontend/src/components/optimization/RecommendationCard.tsx
- [x] T139 [P] [US4] Create impact estimation chart in frontend/src/components/optimization/ImpactChart.tsx
- [x] T140 [P] [US4] Create implementation tracker in frontend/src/components/optimization/ImplementationTracker.tsx

### Test Data & Fixtures

- [x] T140a [P] [US4] Create optimization test fixtures in backend/tests/fixtures/optimization_fixtures.py with sample recommendations
- [x] T140b [US4] Create mock optimization data generator in backend/scripts/generate_mock_optimizations.py for integration testing

### Integration & Validation

- [x] T141 [US4] Create integration test for optimization recommendations in tests/integration/test_optimization.py
- [x] T142 [US4] Validate User Story 4 independently with various load patterns

**Checkpoint**: User Story 4 complete - Optimization recommendations work independently

---

## Phase 7: User Story 5 - Intelligent Rate Limiting (Priority: P3)

**Goal**: Dynamic rate limiting that adapts to usage patterns and business priorities

**Independent Test**: Simulate various traffic patterns, verify rate limits adjust dynamically

### Backend - Rate Limiting Service

- [X] T143 [P] [US5] Create RateLimitPolicy repository in backend/app/db/repositories/rate_limit_repository.py
- [X] T144 [US5] Implement Rate Limiting Service in backend/app/services/rate_limit_service.py with adaptive logic
- [X] T145 [US5] Implement rate limit policy management in backend/app/services/rate_limit_service.py
- [X] T146 [US5] Create rate limit effectiveness tracking in backend/app/services/rate_limit_service.py

### Backend - REST API Endpoints

- [X] T147 [P] [US5] Implement Rate Limiting endpoints in backend/app/api/v1/rate_limits.py per backend-api.yaml (GET /rate-limits, POST /rate-limits)

### MCP - Optimization Server (Rate Limiting)

- [X] T148 [P] [US5] Implement manage_rate_limit tool in mcp-servers/optimization_server.py per mcp-tools.md
- [X] T149 [P] [US5] Implement analyze_rate_limit_effectiveness tool in mcp-servers/optimization_server.py per mcp-tools.md

### Demo Gateway - Rate Limiting

- [ ] T150 [US5] Implement rate limiting policy engine in demo-gateway/src/main/java/com/example/gateway/policy/RateLimitPolicy.java
- [ ] T151 [US5] Integrate rate limiting with API routing in demo-gateway/src/main/java/com/example/gateway/service/RoutingService.java

### Frontend - Rate Limiting View

- [X] T152 [US5] Add rate limiting section to Optimization page in frontend/src/pages/Optimization.tsx
- [X] T153 [P] [US5] Create rate limit policy component in frontend/src/components/optimization/RateLimitPolicy.tsx
- [X] T154 [P] [US5] Create rate limit effectiveness chart in frontend/src/components/optimization/RateLimitChart.tsx

### Integration & Validation

- [X] T154.5 [P] [US5] Create rate limit test fixtures in backend/tests/fixtures/rate_limit_fixtures.py
- [X] T155 [US5] Create integration test for rate limiting in backend/tests/integration/test_rate_limiting.py
- [X] T156 [US5] Validate User Story 5 independently with traffic simulation

**Checkpoint**: User Story 5 complete - Rate limiting works independently

---

## Phase 8: User Story 6 - Natural Language Query Interface (Priority: P3)

**Goal**: Query API intelligence using natural language questions

**Independent Test**: Ask various natural language questions, verify accurate contextual answers

### Backend - Query Service

- [X] T157 [P] [US6] Create Query repository in backend/app/db/repositories/query_repository.py
- [X] T158 [US6] Implement Query Service in backend/app/services/query_service.py with NLP processing
- [X] T159 [US6] Create Query Agent in backend/app/agents/query_agent.py using LangChain/LangGraph
- [X] T160 [US6] Implement query understanding workflow in backend/app/agents/query_agent.py with intent detection
- [X] T161 [US6] Implement OpenSearch query DSL generation in backend/app/services/query_service.py
- [X] T162 [US6] Implement response generation with LLM in backend/app/services/query_service.py

### Backend - REST API Endpoints

- [X] T163 [P] [US6] Implement Query endpoint in backend/app/api/v1/query.py per backend-api.yaml (POST /query)

### Frontend - Query Interface

- [X] T164 [US6] Create Query page in frontend/src/pages/Query.tsx with chat-like interface
- [X] T165 [P] [US6] Create query input component in frontend/src/components/query/QueryInput.tsx
- [X] T166 [P] [US6] Create query response component in frontend/src/components/query/QueryResponse.tsx
- [X] T167 [P] [US6] Create query history component in frontend/src/components/query/QueryHistory.tsx
- [X] T168 [P] [US6] Implement conversation context management in frontend/src/hooks/useQuerySession.ts

### Integration & Validation

- [X] T169 [US6] Create integration test for query processing in tests/integration/test_query_processing.py
- [X] T170 [US6] Create end-to-end test for complete query workflow in tests/e2e/test_query_workflow.py
- [X] T171 [US6] Validate User Story 6 independently with various query types

**Checkpoint**: All user stories complete - Full system functional

---

## Phase 9: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

### Documentation

- [ ] T172 [P] Create architecture documentation in docs/architecture.md
- [ ] T173 [P] Create API reference documentation in docs/api-reference.md
- [ ] T174 [P] Create deployment guide in docs/deployment.md
- [ ] T175 [P] Create contributing guidelines in docs/contributing.md
- [ ] T176 [P] Update README.md with comprehensive project information

### Security & Compliance

- [ ] T177 [P] Implement TLS 1.3 configuration for all services
- [ ] T178 [P] Configure FIPS 140-3 compliant cryptography in backend/app/utils/crypto.py
- [ ] T179 [P] Setup encryption at rest for OpenSearch
- [ ] T180 [P] Implement audit logging for all operations in backend/app/middleware/audit.py

### Monitoring & Observability

- [ ] T181 [P] Setup Prometheus exporters for all services
- [ ] T182 [P] Create Grafana dashboards in k8s/monitoring/dashboards/
- [ ] T183 [P] Implement OpenTelemetry tracing in backend/app/middleware/tracing.py
- [ ] T184 [P] Configure log aggregation to OpenSearch

### Deployment

- [ ] T185 [P] Create Kubernetes namespace manifest in k8s/namespace.yaml
- [ ] T186 [P] Create OpenSearch Kubernetes manifests in k8s/opensearch/
- [ ] T187 [P] Create Backend Kubernetes manifests in k8s/backend/
- [ ] T188 [P] Create Frontend Kubernetes manifests in k8s/frontend/
- [ ] T189 [P] Create MCP servers Kubernetes manifests in k8s/mcp-servers/
- [ ] T190 [P] Create Demo Gateway Kubernetes manifests in k8s/demo-gateway/
- [ ] T191 [P] Create production Docker Compose file in docker-compose.prod.yml

### Testing & Validation

- [ ] T192 [P] Create integration test for Gateway integration in tests/integration/test_gateway_integration.py
- [ ] T193 [P] Create end-to-end test fixtures in tests/e2e/fixtures/
- [ ] T194 [P] Run complete quickstart.md validation
- [ ] T195 [P] Perform load testing with 1000+ APIs
- [ ] T196 [P] Validate 90-day data retention policy

### Code Quality

- [ ] T197 [P] Code cleanup and refactoring across all components
- [ ] T198 [P] Performance optimization for query latency (<5s target)
- [ ] T199 [P] Security hardening review
- [ ] T200 [P] Update AGENTS.md with final technology stack

---

## Phase 10: AI-Enhanced Analysis (LLM Integration) 🤖

**Goal**: Enable LLM-powered intelligent analysis for predictions and optimizations

**Independent Test**: Generate AI-enhanced predictions and optimizations, verify LLM explanations and insights

### Dependencies & Configuration

- [X] T201 [P] [AI] Add LangGraph dependency to backend/requirements.txt (langgraph>=0.0.20)
- [X] T202 [P] [AI] Add LangChain dependencies to backend/requirements.txt (langchain>=0.1.0, langchain-openai>=0.0.5, langchain-anthropic>=0.1.0)
- [X] T203 [P] [AI] Update .env.example with LLM configuration (LLM_PROVIDER, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE)
- [X] T204 [AI] Update backend/app/config.py to include LLM settings with Pydantic validation

### LLM Service Enhancement

- [X] T205 [AI] Enhance backend/app/services/llm_service.py with async completion methods
- [X] T206 [P] [AI] Add streaming support to backend/app/services/llm_service.py
- [X] T207 [P] [AI] Implement token usage tracking in backend/app/services/llm_service.py
- [X] T208 [P] [AI] Add error handling and retry logic with exponential backoff in backend/app/services/llm_service.py
- [X] T209 [P] [AI] Create LLM testing script in backend/scripts/test_llm_agents.py for agent validation

### PredictionAgent Integration

- [X] T210 [AI] Update backend/app/agents/prediction_agent.py to fix LangGraph workflow initialization
- [X] T211 [AI] Integrate PredictionAgent into backend/app/services/prediction_service.py with use_ai_enhancement parameter
- [X] T212 [AI] Add fallback logic to backend/app/services/prediction_service.py (use rule-based if LLM fails)
- [ ] T213 [P] [AI] Create mock LLM responses for testing in backend/tests/fixtures/llm_fixtures.py
- [ ] T214 [AI] Add integration test for AI-enhanced predictions in backend/tests/integration/test_ai_predictions.py

### OptimizationAgent Integration

- [X] T215 [AI] Update backend/app/agents/optimization_agent.py to fix LangGraph workflow initialization
- [X] T216 [AI] Integrate OptimizationAgent into backend/app/services/optimization_service.py with use_ai_enhancement parameter
- [X] T217 [AI] Add fallback logic to backend/app/services/optimization_service.py (use rule-based if LLM fails)
- [ ] T218 [AI] Add integration test for AI-enhanced optimizations in backend/tests/integration/test_ai_optimizations.py

### API Endpoints for AI Features

- [X] T219 [P] [AI] Add POST /api/v1/predictions/ai-enhanced endpoint in backend/app/api/v1/predictions.py
- [X] T220 [P] [AI] Add GET /api/v1/predictions/{id}/explanation endpoint in backend/app/api/v1/predictions.py
- [X] T221 [P] [AI] Add query parameter ?use_ai=true to existing prediction endpoints in backend/app/api/v1/predictions.py
- [X] T222 [P] [AI] Add POST /api/v1/optimization/ai-enhanced endpoint in backend/app/api/v1/optimization.py
- [X] T223 [P] [AI] Add GET /api/v1/optimization/{id}/insights endpoint in backend/app/api/v1/optimization.py
- [X] T224 [P] [AI] Add query parameter ?use_ai=true to existing optimization endpoints in backend/app/api/v1/optimization.py

### Frontend AI Features

- [X] T225 [P] [AI] Add AI toggle switch to frontend/src/pages/Predictions.tsx
- [X] T226 [P] [AI] Display LLM explanations in frontend/src/components/predictions/PredictionCard.tsx
- [X] T227 [P] [AI] Add AI toggle switch to frontend/src/pages/Optimization.tsx
- [X] T228 [P] [AI] Display AI insights in frontend/src/components/optimization/RecommendationCard.tsx
- [X] T229 [P] [AI] Add loading states for AI processing in frontend components

### Testing & Validation

- [ ] T230 [AI] Create end-to-end test for AI prediction workflow in backend/tests/e2e/test_ai_prediction_workflow.py
- [ ] T231 [AI] Create end-to-end test for AI optimization workflow in backend/tests/e2e/test_ai_optimization_workflow.py
- [ ] T232 [AI] Test fallback behavior when LLM is unavailable in backend/tests/integration/test_ai_fallback.py
- [ ] T233 [AI] Validate token usage tracking and cost monitoring
- [ ] T234 [AI] Performance test: Compare AI-enhanced vs rule-based response times

### Documentation

- [X] T235 [P] [AI] Document AI features in README.md with setup instructions
- [X] T236 [P] [AI] Create AI configuration guide in docs/ai-setup.md
- [X] T237 [P] [AI] Document cost considerations and token usage in docs/ai-costs.md
- [ ] T238 [P] [AI] Add API examples for AI-enhanced endpoints in docs/api-reference.md

**Checkpoint**: Phase 10 complete - AI-enhanced analysis operational with fallback to rule-based

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-8)**: All depend on Foundational phase completion
  - User stories can proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 9)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational - No dependencies on other stories
- **User Story 2 (P1)**: Can start after Foundational - Depends on US1 for metrics data
- **User Story 3 (P2)**: Can start after Foundational - Depends on US1 for API inventory
- **User Story 4 (P2)**: Can start after Foundational - Depends on US1 for metrics data
- **User Story 5 (P3)**: Can start after Foundational - Depends on US1 for API inventory
- **User Story 6 (P3)**: Can start after Foundational - Can query data from all previous stories

### Within Each User Story

- Repositories before services
- Services before agents
- Agents before schedulers
- Backend endpoints before frontend components
- MCP tools can be developed in parallel with backend services
- Demo Gateway features can be developed in parallel with backend
- Frontend components marked [P] can be developed in parallel

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, User Stories 1, 3, 5 can start in parallel
- User Stories 2 and 4 can start after US1 completes (need metrics data)
- Within each story, all tasks marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members
- All Polish tasks marked [P] can run in parallel

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Discovery & Monitoring)
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Complete Phase 4: User Story 2 (Predictions)
6. **STOP and VALIDATE**: Test User Story 2 independently
7. Deploy/demo MVP with core capabilities

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (Basic MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo (Predictive MVP!)
4. Add User Story 3 → Test independently → Deploy/Demo (Security-aware)
5. Add User Story 4 → Test independently → Deploy/Demo (Performance-optimized)
6. Add User Story 5 → Test independently → Deploy/Demo (Rate-limited)
7. Add User Story 6 → Test independently → Deploy/Demo (Full system!)
8. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Discovery & Monitoring)
   - Developer B: User Story 3 (Security Scanning)
   - Developer C: User Story 5 (Rate Limiting)
3. After US1 completes:
   - Developer D: User Story 2 (Predictions) - needs US1 metrics
   - Developer E: User Story 4 (Optimization) - needs US1 metrics
4. After all P1/P2 stories:
   - Developer F: User Story 6 (Natural Language) - needs all data
5. Stories complete and integrate independently

---

## Task Count Summary

- **Phase 1 (Setup)**: 9 tasks
- **Phase 2 (Foundational)**: 44 tasks (CRITICAL PATH)
- **Phase 3 (US1 - Discovery & Monitoring)**: 36 tasks
- **Phase 4 (US2 - Predictions)**: 16 tasks
- **Phase 5 (US3 - Security)**: 18 tasks
- **Phase 6 (US4 - Optimization)**: 14 tasks
- **Phase 7 (US5 - Rate Limiting)**: 14 tasks
- **Phase 8 (US6 - Natural Language)**: 15 tasks
- **Phase 9 (Polish)**: 29 tasks

**Total**: 195 tasks

**Parallel Opportunities**: 89 tasks marked [P] can run in parallel with other tasks

**MVP Scope** (US1 + US2): 105 tasks (Setup + Foundational + US1 + US2)

---

## Notes

- [P] tasks = different files, no dependencies within their phase
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Tests are integration/e2e only per project requirements
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- Avoid: vague tasks, same file conflicts, cross-story dependencies that break independence
- All file paths are relative to repository root
- Follow project structure from plan.md exactly

---

**Generated**: 2026-03-09
**Updated**: 2026-03-11 (Added Phase 10: AI-Enhanced Analysis)
**Total Tasks**: 233
**MVP Tasks**: 105 (Setup + Foundational + US1 + US2)
**AI-Enhanced MVP**: 143 (MVP + AI Integration)
**Estimated MVP Duration**: 4-6 weeks with 2-3 developers
**Estimated AI-Enhanced MVP**: 6-8 weeks with 2-3 developers
**Full System Duration**: 10-14 weeks with 3-5 developers