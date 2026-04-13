# Feature Specification: API Intelligence Plane

**Feature Branch**: `001-api-intelligence-plane`
**Created**: 2026-03-09
**Updated**: 2026-04-10 (WebMethods-First Phase)
**Status**: Draft
**Input**: User description: "Build 'API Intelligence Plane', an AI-driven API management application, that transforms API management from reactive firefighting to proactive, autonomous operations. It acts as an always-on intelligent companion to your existing API Gateways that provides AI-driven visibility, decision-making and automation for APIs. The Core Capabilities includes Autonomous API discovery (including shadow APIs), Predictive Health Management (Predict API failures 24-48 hours in advance), Continuous security scanning and automated remediation, Real-time performance optimization recommendations, Real-time rate limiting and Natural language query interface. **The system uses vendor-neutral data models (`api.py:API`, `metric.py:Metric`, `transaction.py:TransactionalLog`) with vendor-specific gateway adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter) that transform vendor data to vendor-neutral format. For the initial release, ONLY WebMethodsGatewayAdapter is implemented using models from `backend/app/models/webmethods/`. Kong and Apigee adapters are deferred to future phases.**"

## WebMethods API Gateway Integration

### REST API Endpoints

The WebMethods API Gateway provides the following REST API endpoints for integration:

#### 1. API Discovery & Management
- **GET `/rest/apigateway/apis`**: List all APIs registered in the gateway
  - Returns: Array of API summaries with basic metadata (name, version, id, status)
  - Used for: Initial discovery and periodic synchronization

- **GET `/rest/apigateway/apis/{api_id}`**: Get detailed API information
  - Returns: Complete API details including OpenAPI specification, policies, endpoints, versions
  - Key fields: `apiDefinition` (OpenAPI spec), `nativeEndpoint` (backend URLs), `policies` (policy IDs), `gatewayEndPointList` (exposed endpoints)
  - Used for: Detailed API analysis, policy extraction, endpoint mapping

#### 2. Policy Management
- **GET `/rest/apigateway/policies/{policy_id}`**: Get policy configuration
  - Returns: Policy with enforcement stages and attached policy actions
  - Policy stages: `transport`, `requestPayloadProcessing`, `IAM`, `LMT`, `routing`, `responseProcessing`
  - Used for: Understanding current security/optimization policies

- **PUT `/rest/apigateway/policies/{policy_id}`**: Update policy configuration
  - Request: Modified policy with updated `policyEnforcements` array
  - Used for: Applying security fixes and optimization recommendations

#### 3. Policy Actions (Enforcement Objects)
- **GET `/rest/apigateway/policyActions/{policyaction_id}`**: Get policy action configuration
  - Returns: Policy action with `templateKey` (type) and `parameters` (configuration)
  - Template examples: `validateAPISpec`, `requireHTTPS`, `rateLimiting`, `authentication`
  - Used for: Understanding individual policy configurations

- **POST `/rest/apigateway/policyActions`**: Create new policy action
  - Request: Policy action with `templateKey` and `parameters`
  - Returns: Created policy action with assigned ID
  - Used for: Creating new security/optimization policies

#### 4. Transactional Logs (Analytics)
- **OpenSearch Query**: Query transactional event logs
  - Filter: `eventType: "Transactional"`
  - Returns: Raw transactional events with timing, request/response data, errors, cache metrics
  - Key fields: `totalTime`, `providerTime` (backend), `gatewayTime`, `statusCode`, `applicationId`, `cacheHit`, `externalCalls`
  - Used for: Metrics aggregation, performance analysis, drill-down queries

### Data Transformation Flow

1. **API Discovery**: `GET /apis` → Transform to vendor-neutral [`api.py:API`](../../backend/app/models/base/api.py)
2. **API Details**: `GET /apis/{id}` → Extract OpenAPI spec, policies, endpoints → Store in `api_definition`, `policy_actions`, `vendor_metadata`
3. **Policy Reading**: `GET /policies/{id}` → Transform to vendor-neutral [`PolicyAction`](../../backend/app/models/base/api.py:PolicyAction) with `vendor_config`
4. **Policy Application**: Create [`PolicyAction`](../../backend/app/models/base/api.py:PolicyAction) → `POST /policyActions` → `PUT /policies/{id}` to attach
5. **Analytics Collection**: OpenSearch query → Transform to vendor-neutral [`transaction.py:TransactionalLog`](../../backend/app/models/base/transaction.py) → Aggregate to [`metric.py:Metric`](../../backend/app/models/base/metric.py)

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

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Discover and Monitor All APIs (Priority: P1)

As an API operations manager, I need to automatically discover all APIs in my infrastructure (including undocumented shadow APIs) and continuously monitor their health, so that I have complete visibility into my API landscape and can prevent outages before they occur.

**Why this priority**: This is the foundation capability - without knowing what APIs exist and their current state, no other intelligent operations are possible. This delivers immediate value by revealing hidden APIs and providing baseline monitoring.

**Independent Test**: Can be fully tested by connecting to an API Gateway, observing automatic discovery of APIs (including intentionally undocumented ones), and viewing real-time health metrics on a dashboard. Delivers value by providing complete API inventory and health visibility.

**Acceptance Scenarios**:

1. **Given** webMethods API Gateway is connected (initial phase), **When** the system performs discovery, **Then** all registered APIs and shadow APIs are identified and cataloged with their comprehensive metadata including policy actions, API definitions, endpoints, methods, and OpenAPI specifications in vendor-neutral format via WebMethodsGatewayAdapter
2. **Given** APIs are being monitored, **When** an API's health degrades, **Then** the system displays real-time health metrics and trends on the dashboard
3. **Given** a new API is deployed to a connected Gateway, **When** the discovery cycle runs, **Then** the new API is automatically detected and added to the inventory within 5 minutes
4. **Given** an API has been removed from a Gateway, **When** the discovery cycle runs, **Then** the API is marked as inactive in the inventory

---

### User Story 2 - Predict and Prevent API Failures (Priority: P1)

As a DevOps engineer, I need to receive advance warnings of potential API failures 24-48 hours before they occur, so that I can take preventive action and avoid customer-impacting outages.

**Why this priority**: Predictive capabilities transform operations from reactive to proactive, directly addressing the core value proposition. This prevents revenue loss and customer dissatisfaction from API outages.

**Independent Test**: Can be tested by simulating degrading API conditions (increasing error rates, latency spikes, resource exhaustion patterns) and verifying that predictions are generated 24-48 hours before critical thresholds are reached. Delivers value by enabling proactive intervention.

**Prediction Architecture**: The system uses a **hybrid approach** combining rule-based predictions (fast, deterministic baseline) with optional AI-enhanced analysis (deep insights, natural language explanations). AI enhancement is automatically triggered based on prediction confidence thresholds and system configuration, ensuring reliability while providing intelligent insights when beneficial.

**Contributing Factors**: Predictions include strongly-typed contributing factors categorized into:
- **Performance** (7 types): error rates, response times, latency, timeouts
- **Availability** (2 types): declining availability, declining throughput
- **Capacity** (1 type): rapid request growth
- **Dependencies** (1 type): downstream service degradation
- **Traffic** (1 type): abnormal traffic patterns

**Acceptance Scenarios**:

1. **Given** an API shows patterns indicating potential failure, **When** the prediction engine analyzes the trends, **Then** a failure prediction alert is generated 24-48 hours in advance with confidence score, strongly-typed contributing factors, and recommended actions
2. **Given** multiple APIs are monitored, **When** resource contention patterns emerge, **Then** the system predicts which APIs will be affected and when, with categorized contributing factors
3. **Given** a prediction alert was issued, **When** the predicted time window arrives, **Then** the system tracks prediction accuracy and updates its models
4. **Given** seasonal traffic patterns exist, **When** analyzing predictions, **Then** the system accounts for expected variations and only alerts on anomalous patterns
5. **Given** a high-confidence prediction is generated, **When** AI enhancement is enabled, **Then** the system automatically provides natural language explanations and deeper insights without manual intervention

---

### User Story 3 - Automated Security Scanning and Remediation (Priority: P2)

As a security engineer, I need continuous security scanning of all APIs with automated remediation of common vulnerabilities, so that my API infrastructure remains secure without constant manual intervention and I can respond to active threats immediately.

**Why this priority**: Security is critical but builds on the foundation of API discovery. Automated remediation reduces security response time from hours/days to seconds/minutes. Security issues require immediate attention to prevent breaches.

**Audience**: Security engineers, DevOps teams, Application security teams

**Urgency**: IMMEDIATE - Active threats requiring rapid remediation

**Architecture**:
- **Hybrid Approach**: Single mode combining rule-based checks with intelligent AI enhancement
- **Multi-Source Analysis**: Uses API metadata, real-time metrics, and traffic patterns for accurate detection
- **Real Remediation**: Direct policy application to Gateway via adapter interface
- **Focus**: Active vulnerabilities and security threats

**Independent Test**: Can be tested by deploying APIs with known security issues (exposed credentials, missing authentication, vulnerable dependencies), verifying detection within scanning cycles, and confirming automated remediation actions are applied to the Gateway. Delivers value by reducing security exposure time.

**Acceptance Scenarios**:

1. **Given** an API is discovered, **When** security scanning runs, **Then** vulnerabilities are identified and categorized by severity (critical, high, medium, low) using hybrid analysis
2. **Given** a remediable vulnerability is detected, **When** automated remediation is enabled, **Then** the system applies security policies directly to the Gateway and verifies the vulnerability is resolved through re-scanning
3. **Given** a vulnerability requires manual intervention, **When** detected, **Then** the system creates a detailed remediation ticket with context and recommended actions
4. **Given** security scans run continuously, **When** new vulnerabilities are published, **Then** the system rescans affected APIs within 1 hour
5. **Given** security policies are applied, **When** verification runs, **Then** the system confirms fixes through real re-scanning and updates vulnerability status
6. **Given** critical vulnerabilities are detected, **When** alerts are sent, **Then** security teams receive immediate notifications with remediation priority

---

### User Story 4 - Compliance Monitoring and Audit Reporting (Priority: P2)

As a compliance officer, I need continuous compliance monitoring of all APIs with automated detection of regulatory violations and comprehensive audit reporting, so that I can maintain regulatory compliance and prepare for audits without manual data collection.

**Why this priority**: Compliance is essential for regulatory requirements but operates on audit schedules rather than immediate response. Automated compliance monitoring reduces audit preparation time from weeks to hours.

**Audience**: Compliance officers, Auditors, Legal teams, Risk management

**Urgency**: SCHEDULED - Audit preparation and regulatory reporting timelines

**Architecture**:
- **AI-Driven Analysis**: Intelligent detection of compliance violations across multiple standards
- **Multi-Source Analysis**: Uses API metadata, configuration, traffic patterns, and data handling for comprehensive assessment
- **Audit Trail**: Complete documentation of compliance status, violations, and remediation history
- **Standards Coverage**: GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001

**Independent Test**: Can be tested by deploying APIs with known compliance gaps (missing data retention policies, inadequate encryption, improper data handling), verifying detection of violations, and confirming comprehensive audit reports are generated. Delivers value by ensuring regulatory compliance and audit readiness.

**Acceptance Scenarios**:

1. **Given** an API is discovered, **When** compliance scanning runs, **Then** compliance violations are identified and categorized by standard (GDPR, HIPAA, SOC2, PCI-DSS) using AI-driven analysis
2. **Given** compliance violations are detected, **When** audit reports are generated, **Then** the system provides detailed evidence, affected APIs, and remediation recommendations
3. **Given** APIs handle sensitive data, **When** data protection compliance is assessed, **Then** the system verifies encryption, access controls, and data retention policies
4. **Given** compliance scans run continuously, **When** new regulations are published, **Then** the system updates compliance rules and rescans affected APIs
5. **Given** audit preparation is needed, **When** compliance reports are requested, **Then** the system generates comprehensive reports with evidence, timelines, and control effectiveness
6. **Given** compliance violations require remediation, **When** remediation is tracked, **Then** the system maintains complete audit trail with timestamps, actions, and verification

---

### User Story 5 - Performance Optimization & Intelligent Rate Limiting (Priority: P2)

**MERGED**: This user story combines real-time performance optimization recommendations with intelligent rate limiting, as both are gateway-level performance optimization techniques.

As a platform engineer, I need real-time recommendations for optimizing API performance (including caching, compression, and rate limiting) based on actual usage patterns, with the ability to apply these optimizations directly to the API Gateway, so that I can improve response times, prevent abuse, and ensure optimal resource utilization.

**Why this priority**: Performance optimization delivers measurable business value (improved user experience, abuse prevention, better resource utilization) but requires the monitoring foundation from P1 stories.

**Architecture**: 
- **API-Centric**: All optimizations are generated and applied per-API
- **Gateway-Level Scope**: Limited to proxy-level optimizations (caching, compression, rate limiting) that can be validated with gateway-observable metrics
- **Hybrid Approach**: Rule-based analysis with optional AI-enhanced recommendations
- **Real-time Application**: Recommendations can be applied directly to the Gateway via enhanced adapter interface
- **AI Control**: AI-driven mode enabled via OPTIMIZATION_AI_ENABLED environment variable

**Optimization Types** (Gateway-Level Only):
1. **Caching**: Response caching policies with TTL and invalidation strategies
2. **Compression**: Payload compression (gzip/brotli) for bandwidth optimization
3. **Rate Limiting**: Dynamic rate limiting that adapts to usage patterns and business priorities

**Independent Test**: Can be tested by monitoring APIs under various load conditions, verifying that optimization recommendations are generated based on observed patterns, applying recommendations to the Gateway, and measuring performance improvements. Delivers value through reduced latency, prevented abuse, and optimized resource usage.

**Acceptance Scenarios**:

1. **Given** an API shows inefficient patterns, **When** the optimization engine analyzes usage, **Then** specific recommendations are provided with estimated impact (caching, compression, or rate limiting)
2. **Given** caching opportunities are identified, **When** recommendations are applied to the Gateway, **Then** cache hit rates and response time improvements are measured and reported
3. **Given** compression opportunities are identified, **When** recommendations are applied to the Gateway, **Then** bandwidth reduction and response time improvements are measured
4. **Given** normal traffic patterns are established, **When** burst traffic occurs from legitimate users, **Then** rate limits temporarily adjust to accommodate the spike
5. **Given** abuse patterns are detected, **When** rate limiting activates, **Then** the abusive traffic is throttled while legitimate users maintain access
6. **Given** different API consumers have different priorities, **When** applying rate limits, **Then** higher priority consumers receive preferential treatment during contention
7. **Given** multiple optimization options exist, **When** presenting recommendations, **Then** they are prioritized by expected impact and implementation effort in a unified view
8. **Given** optimizations are applied, **When** monitoring continues, **Then** the system validates improvements and adjusts recommendations based on results
9. **Given** AI enhancement is enabled, **When** generating recommendations, **Then** the system provides detailed implementation guidance and success metrics

---

### User Story 6 - Natural Language Query Interface (Priority: P3)

As any user of the system, I need to query API intelligence using natural language questions, so that I can quickly get insights without learning complex query syntax or navigating multiple dashboards.

**Why this priority**: Natural language interface improves usability but all core functionality must work through traditional interfaces first. This is a convenience enhancement.

**Independent Test**: Can be tested by asking various natural language questions about API health, performance, security, and predictions, and verifying that accurate, contextual answers are provided with relevant data and visualizations. Delivers value through improved accessibility and faster insights.

**Acceptance Scenarios**:

1. **Given** the user asks "Which APIs are at risk of failure?", **When** the query is processed, **Then** a list of at-risk APIs with predictions and confidence scores is returned
2. **Given** the user asks "Show me security vulnerabilities from the last week", **When** the query is processed, **Then** relevant vulnerabilities are displayed with severity, affected APIs, and remediation status
3. **Given** the user asks "What's causing slow response times for the payment API?", **When** the query is processed, **Then** performance analysis with root cause indicators and optimization recommendations is provided
4. **Given** ambiguous queries are submitted, **When** processing, **Then** the system asks clarifying questions or provides multiple interpretations

---

### User Story 7 - WebMethods Analytics Integration (Priority: P2)

As an API operations manager using WebMethods API Gateway, I need to collect and analyze transactional event data from my gateway to gain deep insights into API performance, usage patterns, and operational metrics, so that I can make data-driven decisions and optimize my API infrastructure.

**Why this priority**: WebMethods Analytics integration extends the platform's multi-gateway support with deep transactional data collection and analysis capabilities. This enables drill-down from aggregated metrics to individual transaction logs, providing comprehensive visibility into API operations.

**Audience**: API operations managers, Platform engineers, DevOps teams, Business analysts

**Urgency**: OPERATIONAL - Continuous monitoring and analysis for operational excellence

**Architecture**:
- **ETL Pipeline**: Periodic collection (every 5 minutes) → Store raw logs → Aggregate into metrics
- **Multi-Gateway Support**: `gateway_id` as primary dimension for data segregation
- **Time-Series Aggregation**: 1-minute (24 hours), 5-minute (7 days), 1-hour (30 days), 1-day (90 days) buckets
- **Drill-Down Pattern**: Users can trace from aggregated metrics back to raw transactional logs
- **Three-Model Architecture**: API (metadata), TransactionalLog (raw events), Metrics (aggregated)

**Data Models**:
- **TransactionalLog**: 61-field model capturing complete transaction details including timing metrics (creation_date, total_time, provider_time, gateway_time), request/response data, external calls, and error information
- **Metrics**: Aggregated model with dimensions (gateway_id, api_id, application_id, timestamp, time_bucket) and calculated metrics (response times, error rates, throughput, cache metrics)
- **API**: Existing comprehensive API model from wm_api.py (keep as-is)

**Independent Test**: Connect to WebMethods API Gateway, verify transactional logs are collected every 5 minutes, confirm metrics are aggregated into time buckets, validate drill-down from metrics to raw logs, and verify multi-gateway data segregation.

**Acceptance Scenarios**:

1. **Given** a WebMethods API Gateway is connected, **When** the collection cycle runs, **Then** transactional logs are fetched and stored in OpenSearch with all 61 fields preserved
2. **Given** raw transactional logs are collected, **When** the aggregation service runs, **Then** metrics are calculated and stored in appropriate time buckets (1m, 5m, 1h, 1d) with gateway_id dimension
3. **Given** multiple gateway instances are connected, **When** viewing metrics, **Then** data is properly segregated by gateway_id and can be filtered independently
4. **Given** a user views aggregated metrics, **When** they click on a metric spike, **Then** the system displays the underlying raw transactional logs that contributed to that metric
5. **Given** transactional logs contain external service calls, **When** analyzing performance, **Then** the system tracks and displays external call durations and their impact on total response time
6. **Given** time-bucketed metrics exist, **When** retention periods expire, **Then** older buckets are automatically deleted (1m after 24 hours, 5m after 7 days, 1h after 30 days, 1d after 90 days)
7. **Given** transactional logs contain error information, **When** analyzing failures, **Then** the system categorizes errors by origin (NATIVE, GATEWAY) and provides detailed error context

---

### Edge Cases

- What happens when an API Gateway becomes temporarily unreachable during discovery?
- How does the system handle APIs that are intentionally hidden or require special authentication?
- What happens when prediction models encounter API patterns they haven't seen before?
- How does the system handle conflicting security remediation actions across different APIs?
- What happens when a security vulnerability also constitutes a compliance violation?
- How does the system prioritize between immediate security threats and scheduled compliance audits?
- What happens when compliance standards conflict or have overlapping requirements?
- How does the system handle compliance violations that cannot be automatically remediated?
- What happens when rate limiting decisions conflict with business-critical traffic?
- How does the system handle multi-vendor Gateway configurations with different capabilities?
- What happens when automated remediation fails or causes unintended side effects?
- How does the system handle APIs that change their behavior or endpoints without notification?
- What happens when natural language queries are ambiguous or request impossible operations?
- How does the system handle high-frequency API changes in dynamic environments?
- What happens when applying optimization policies to the Gateway fails?
- How does the system handle Gateway vendors that don't support certain optimization types?
- How does the system handle compliance audits that span multiple time periods?
- What happens when compliance rules change mid-audit cycle?
- What happens when WebMethods Gateway becomes unreachable during transactional log collection?
- How does the system handle incomplete or malformed transactional log data?
- What happens when aggregation service fails during metric calculation?
- How does the system handle time bucket transitions during data collection?
- What happens when drill-down queries span multiple time buckets with different retention periods?
- How does the system handle gateway_id conflicts when multiple gateways have the same ID?
- What happens when external call data is missing or incomplete in transactional logs?

## Requirements *(mandatory)*

### Functional Requirements

#### Discovery & Monitoring
- **FR-001**: System MUST automatically discover all APIs registered in connected API Gateways with comprehensive metadata including `policy_actions`, `api_definition`, OpenAPI specifications, and vendor-specific fields stored in `vendor_metadata`. **Initial phase: WebMethods integration via WebMethodsGatewayAdapter using models from `backend/app/models/webmethods/`.**
- **FR-002**: System MUST detect shadow APIs (undocumented or unregistered APIs) by analyzing traffic patterns and Gateway logs, marking them with `is_shadow` flag in `intelligence_metadata`
- **FR-003**: System MUST catalog discovered APIs with vendor-neutral structure including `policy_actions` (vendor-neutral types), `api_definition` (OpenAPI/Swagger), `endpoints`, `version_info`, `maturity_state`, `groups`, and intelligence plane fields in `intelligence_metadata` (`health_score`, `is_shadow`, `discovery_method`, `discovered_at`, `last_seen_at`)
- **FR-004**: System MUST continuously monitor API health metrics in time-bucketed format (1m, 5m, 1h, 1d) including response times (avg/min/max/p50/p95/p99), error rates, throughput, availability, cache metrics, and timing breakdown (`gateway_time_avg`, `backend_time_avg`)
- **FR-005**: System MUST support multiple API Gateway vendors through vendor-specific adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter) that transform vendor data to vendor-neutral models. **Initial phase: Only WebMethodsGatewayAdapter implemented; Kong and Apigee deferred.**
- **FR-006**: System MUST complete discovery cycles for new or changed APIs within 5 minutes of deployment
- **FR-077**: System MUST store metrics separately from API entities in time-bucketed OpenSearch indices (`metrics-1m`, `metrics-5m`, `metrics-1h`, `metrics-1d`) with `gateway_id` dimension
- **FR-078**: System MUST use vendor-neutral `policy_actions` with `PolicyAction` model supporting vendor-specific configurations via `vendor_config` field
- **FR-079**: System MUST NOT embed metrics in API entity; metrics queried separately from time-bucketed indices by `api_id` and `time_bucket`
- **FR-080**: System MUST store vendor-specific fields in `vendor_metadata` dict for API model and TransactionalLog model
- **FR-081**: System MUST use vendor-neutral field naming (`backend_time_avg` not `provider_time_avg`, `client_id` not `application_id`)

#### Predictive Health Management
- **FR-007**: System MUST analyze historical API performance data to identify patterns indicating potential failures using a hybrid approach (rule-based + AI-enhanced)
- **FR-008**: System MUST generate failure predictions 24-48 hours in advance with confidence scores and strongly-typed contributing factors
- **FR-009**: System MUST provide recommended preventive actions with each prediction, categorized by contributing factor type
- **FR-010**: System MUST track prediction accuracy and continuously improve prediction models
- **FR-011**: System MUST account for seasonal patterns, expected traffic variations, and scheduled maintenance when generating predictions
- **FR-012**: System MUST alert operations teams when prediction confidence exceeds configurable thresholds
- **FR-012a**: System MUST automatically trigger AI enhancement for high-confidence predictions (≥80% by default) when AI is enabled
- **FR-012b**: System MUST use 13 strongly-typed contributing factor categories: increasing_error_rate, degrading_response_time, gradual_response_time_increase, high_latency_under_load, spike_in_5xx_errors, spike_in_4xx_errors, timeout_rate_increasing, declining_availability, declining_throughput, rapid_request_growth, downstream_service_degradation, abnormal_traffic_pattern
- **FR-012c**: System MUST gracefully fallback to rule-based predictions when AI enhancement fails or is unavailable

#### Security Scanning & Remediation
- **FR-013**: System MUST continuously scan all discovered APIs for security vulnerabilities using hybrid approach (rule-based + AI-enhanced)
- **FR-014**: System MUST categorize vulnerabilities by severity (critical, high, medium, low) based on industry standards
- **FR-015**: System MUST automatically remediate common vulnerabilities by applying security policies directly to the Gateway when automated remediation is enabled
- **FR-016**: System MUST verify that automated remediation actions successfully resolve vulnerabilities through real re-scanning
- **FR-017**: System MUST create detailed remediation tickets for vulnerabilities requiring manual intervention
- **FR-018**: System MUST rescan affected APIs within 1 hour when new vulnerabilities are published
- **FR-019**: System MUST maintain an audit log of all security scans and remediation actions
- **FR-019a**: System MUST use multi-source data analysis (API metadata, real-time metrics, traffic patterns) for accurate vulnerability detection
- **FR-019b**: System MUST support applying 6 types of security policies to Gateway: authentication, authorization, TLS, CORS, validation, and security headers
- **FR-019c**: System MUST track remediation actions with status, timestamps, Gateway policy IDs, and error messages
- **FR-019d**: System MUST provide remediation actions that can be directly applied to Gateway APIs, policies, and configurations
- **FR-019e**: System MUST send immediate alerts to security teams for critical vulnerabilities
- **FR-019f**: System MUST prioritize vulnerabilities based on exploitability and business impact

#### Compliance Monitoring & Audit Reporting
- **FR-020**: System MUST continuously monitor all discovered APIs for compliance violations using AI-driven analysis
- **FR-021**: System MUST detect compliance violations for GDPR, HIPAA, SOC2, PCI-DSS, and ISO 27001 standards
- **FR-022**: System MUST categorize compliance violations by standard and severity
- **FR-023**: System MUST generate comprehensive audit reports with evidence, timelines, and control effectiveness
- **FR-024**: System MUST maintain complete audit trail of compliance status, violations, and remediation history
- **FR-025**: System MUST verify data protection controls including encryption, access controls, and data retention policies
- **FR-026**: System MUST update compliance rules when new regulations are published
- **FR-027**: System MUST provide compliance posture dashboard with coverage percentage and audit readiness score
- **FR-028**: System MUST support compliance report export for external auditors
- **FR-029**: System MUST track compliance remediation with documentation suitable for audit evidence
- **FR-030**: System MUST separate compliance violations from security vulnerabilities in reporting and UI

#### Performance Optimization & Rate Limiting (MERGED)
- **FR-031**: System MUST analyze API usage patterns to identify gateway-level optimization opportunities (caching, compression, rate limiting)
- **FR-032**: System MUST generate specific optimization recommendations with estimated impact for each API
- **FR-033**: System MUST prioritize recommendations by expected impact and implementation effort in a unified view
- **FR-034**: System MUST measure and report performance improvements after optimizations are applied
- **FR-035**: System MUST identify caching opportunities and estimate potential cache hit rates
- **FR-036**: System MUST validate optimization effectiveness and adjust recommendations based on results
- **FR-037**: System MUST support applying caching policies directly to the API Gateway via adapter interface
- **FR-038**: System MUST support applying compression policies directly to the API Gateway via adapter interface
- **FR-039**: System MUST support applying rate limiting policies directly to the API Gateway via adapter interface
- **FR-040**: System MUST implement dynamic rate limiting that adapts to actual usage patterns
- **FR-041**: System MUST detect and throttle abusive traffic patterns while maintaining legitimate user access
- **FR-042**: System MUST support priority-based rate limiting for different API consumer tiers
- **FR-043**: System MUST temporarily adjust rate limits to accommodate legitimate traffic bursts
- **FR-044**: System MUST learn from traffic patterns and refine rate limiting strategies over time
- **FR-045**: System MUST use hybrid approach (rule-based + AI-enhanced) for optimization recommendations
- **FR-046**: System MUST enable AI-driven optimization mode via OPTIMIZATION_AI_ENABLED environment variable
- **FR-047**: System MUST gracefully fallback to rule-based recommendations when AI enhancement fails
- **FR-048**: System MUST present all optimization types (caching, compression, rate limiting) in a unified interface

#### Natural Language Interface
- **FR-049**: System MUST accept natural language queries about API health, performance, security, compliance, and predictions
- **FR-050**: System MUST provide accurate, contextual answers with relevant data and visualizations
- **FR-051**: System MUST handle ambiguous queries by asking clarifying questions or providing multiple interpretations
- **FR-052**: System MUST support common query patterns including status checks, trend analysis, and root cause investigation

#### Analytics Integration (Vendor-Neutral)
- **FR-063**: System MUST collect transactional logs from connected API Gateways every 5 minutes using vendor-specific adapters. **Initial phase: WebMethodsGatewayAdapter only.**
- **FR-064**: System MUST store raw transactional logs in vendor-neutral format in OpenSearch with daily indices (transactional-logs-YYYY.MM.DD)
- **FR-065**: System MUST aggregate transactional logs into time-bucketed metrics (1-minute, 5-minute, 1-hour, 1-day)
- **FR-066**: System MUST calculate response time metrics (average, min, max, p50, p95, p99) from transactional data
- **FR-067**: System MUST calculate error rates and categorize by error origin (backend, gateway, client, network)
- **FR-068**: System MUST calculate throughput metrics (requests per second) per API and gateway
- **FR-069**: System MUST calculate cache effectiveness metrics (hit/miss/bypass counts and rates) from transactional data
- **FR-070**: System MUST track external service call performance with detailed timing and success metrics
- **FR-071**: System MUST support drill-down from aggregated metrics to raw transactional logs
- **FR-072**: System MUST segregate data by gateway_id dimension for multi-gateway deployments
- **FR-073**: System MUST apply retention policies (1m: 24 hours, 5m: 7 days, 1h: 30 days, 1d: 90 days, raw logs: 90 days)
- **FR-074**: System MUST provide API endpoints for querying metrics by gateway, API, client, operation, and time range
- **FR-075**: System MUST handle missing or incomplete transactional log fields gracefully using optional fields
- **FR-076**: System MUST validate transactional log data before storage and aggregation with field validators

#### Multi-Vendor Support (Vendor-Neutral with Adapters)
- **FR-053**: System MUST support multiple API Gateway vendors through vendor-specific adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter). **Initial phase: Only WebMethodsGatewayAdapter implemented.**
- **FR-054**: System MUST transform data from all gateway vendors into vendor-neutral structures: `api.py:API` (API metadata), `metric.py:Metric` (time-bucketed metrics), and `transaction.py:TransactionalLog` (raw events)
- **FR-055**: System MUST handle vendor-specific capabilities through `vendor_metadata` dict in API, Metric, and TransactionalLog models, and `vendor_config` in PolicyAction
- **FR-056**: System MUST maintain consistent intelligence plane functionality (predictions, security, compliance, optimization) regardless of source gateway vendor
- **FR-057**: System MUST provide policy application interface using vendor-neutral `PolicyAction` model with vendor-specific configurations in `vendor_config` field
- **FR-082**: System MUST use vendor-specific adapters (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter) for all gateway integration (no direct integration). **Initial phase: Only WebMethodsGatewayAdapter implemented; Kong and Apigee deferred.**
- **FR-083**: Gateway adapters MUST implement transformation methods that convert vendor-specific API data to vendor-neutral `API` model with proper `vendor_metadata` population. **Initial phase: WebMethodsGatewayAdapter transforms from wm_api.py models.**
- **FR-084**: Gateway adapters MUST implement transformation methods that convert vendor-specific metrics to vendor-neutral `Metric` model with time-bucketed structure
- **FR-085**: Gateway adapters MUST implement transformation methods that convert vendor-specific transactional logs to vendor-neutral `TransactionalLog` model. **Initial phase: WebMethodsGatewayAdapter transforms from wm_transaction.py.**
- **FR-086**: Gateway adapters MUST support collecting transactional logs from vendor gateways for analytics integration
- **FR-087**: Gateway adapters MUST transform vendor-specific policy configurations to vendor-neutral `PolicyAction` model and vice versa. **Initial phase: WebMethodsGatewayAdapter transforms from wm_policy_action.py models.**

#### Data & Persistence
- **FR-058**: System MUST persist API inventory, health metrics, predictions, security findings, compliance violations, and optimization recommendations
- **FR-059**: System MUST retain historical data for trend analysis and model training for at least 90 days
- **FR-060**: System MUST support data export for compliance and external analysis
- **FR-061**: System MUST ensure data integrity and consistency across all operations
- **FR-062**: System MUST maintain separate storage for security vulnerabilities and compliance violations

### Key Entities

- **API**: Represents a vendor-neutral API with comprehensive OpenAPI definition structure including `api_definition` (OpenAPI/Swagger), `policy_actions` (vendor-neutral types with `vendor_config`), `endpoints`, `version_info`, and vendor-specific metadata in `vendor_metadata`. Enhanced with intelligence plane fields in `intelligence_metadata`: `health_score`, `is_shadow`, `discovery_method`, `discovered_at`, `last_seen_at`, `risk_score`, `security_score`. **Does NOT include** embedded metrics (stored separately). All gateway vendors transform to this structure via adapters. **Initial phase: WebMethodsGatewayAdapter transforms from wm_api.py models.**
- **Gateway**: Represents a connected API Gateway with vendor information, connection details, capabilities, and associated APIs. Supports multiple vendors through adapter pattern (WebMethodsGatewayAdapter, KongGatewayAdapter, ApigeeGatewayAdapter). **Initial phase: Only webMethods gateways supported.** Credentials are optional and can be configured separately for `base_url` and `transactional_logs_url`, allowing for different authentication methods or no authentication for each endpoint.
- **Metric**: Represents time-bucketed aggregated metrics (1m, 5m, 1h, 1d) with dimensions (`gateway_id`, `api_id`, `application_id`, `operation`, `timestamp`, `time_bucket`) and calculated values (response times with avg/min/max/p50/p95/p99, error rates, throughput, cache metrics with hit/miss/bypass counts and rates, timing breakdown with `gateway_time_avg`/`backend_time_avg`, HTTP status code breakdown). Stored separately from API entities in time-bucketed OpenSearch indices. Includes optional per-endpoint breakdown via `endpoint_metrics`.
- **Prediction**: Represents a failure prediction with target API, predicted failure time, confidence score, contributing factors, and recommended actions
- **Vulnerability**: Represents a security vulnerability with affected API, severity level, description, remediation status, and remediation actions (excludes compliance violations)
- **ComplianceViolation**: Represents a compliance violation with affected API, compliance standard (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001), violation type, evidence, audit trail, and remediation documentation
- **Optimization Recommendation**: Represents a performance optimization opportunity (caching, compression, or rate limiting) with target API, recommendation type, estimated impact, implementation effort, and validation results
- **Query**: Represents a natural language query with original text, interpreted intent, results, and user feedback
- **TransactionalLog**: Represents a vendor-neutral raw transactional event with comprehensive fields including timing metrics (`timestamp`, `total_time_ms`, `backend_time_ms`, `gateway_time_ms`), request/response data, external calls, error information, client information, and gateway/API identifiers. Vendor-specific fields stored in `vendor_metadata`. Defined in `transaction.py`. **Initial phase: WebMethodsGatewayAdapter transforms from wm_transaction.py.**
- **ExternalCall**: Represents an external service call within a transaction with call type, URL, method, timing, status code, success flag, request/response sizes, and error message

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: System discovers 100% of registered APIs and at least 90% of shadow APIs within 24 hours of initial connection
- **SC-002**: Failure predictions achieve at least 80% accuracy with 24-48 hour advance notice
- **SC-003**: Critical security vulnerabilities are detected within 1 hour of discovery and remediated within 4 hours (automated) or 24 hours (manual)
- **SC-004**: Compliance violations are detected within 24 hours of API discovery and documented with complete audit trail
- **SC-005**: Compliance audit reports are generated within 1 hour of request with 100% evidence completeness
- **SC-006**: Performance optimization recommendations result in measurable improvements (at least 20% reduction in response time or 15% reduction in error rates) for 70% of implemented recommendations
- **SC-007**: Rate limiting prevents 95% of abusive traffic while maintaining 99.9% availability for legitimate users
- **SC-008**: Natural language queries return accurate results within 3 seconds for 90% of queries
- **SC-009**: System supports at least 3 different API Gateway vendors with consistent functionality. **Initial phase: 1 vendor (webMethods) supported; target 3 vendors in future phases.**
- **SC-010**: Operations teams report 50% reduction in time spent on reactive API troubleshooting
- **SC-011**: API-related incidents decrease by 60% within 3 months of deployment
- **SC-012**: System processes and analyzes data from at least 1000 APIs with less than 5 second latency for real-time queries
- **SC-013**: Optimization policies are successfully applied to Gateway within 5 seconds of user action
- **SC-014**: All optimization types (caching, compression, rate limiting) are presented in a unified interface with consistent interaction patterns
- **SC-015**: Compliance officers report 70% reduction in audit preparation time
- **SC-016**: Security and compliance violations are clearly separated in UI with distinct workflows
- **SC-017**: WebMethods transactional logs are collected within 5 minutes of generation with 100% field preservation
- **SC-018**: Metrics aggregation completes within 1 minute of log collection for all time buckets
- **SC-019**: Drill-down queries from metrics to raw logs return results within 2 seconds
- **SC-020**: Multi-gateway deployments maintain data segregation with zero cross-contamination
- **SC-021**: Retention policies are enforced automatically with 99.9% accuracy
- **SC-022**: System processes at least 10,000 transactional events per minute per gateway

## Assumptions

1. **Gateway Access**: Organizations have administrative access to their API Gateways and can provide necessary credentials for integration via vendor-specific adapters. **Initial phase: webMethods API Gateway access required.**
2. **Network Connectivity**: The API Intelligence Plane can establish network connections to connected API Gateways (webMethods, Kong, Apigee, etc.). **Initial phase: webMethods connectivity required.**
3. **Data Volume**: Individual APIs handle between 100 to 100,000 requests per minute, with total system capacity for millions of requests per minute across all APIs
4. **Historical Data**: At least 7 days of historical API metrics are available in time-bucketed format (1m, 5m, 1h, 1d) for initial model training
5. **Remediation Authority**: The system has appropriate permissions to apply automated remediation actions and optimization policies through vendor-specific adapters
6. **Gateway Capabilities**: All supported API Gateways provide REST APIs for API management, policy actions, metrics collection, and transactional logs. Vendor-specific adapters handle transformation to vendor-neutral models. **Initial phase: webMethods API Gateway REST APIs required.**
7. **User Expertise**: Users have basic understanding of API concepts and operations, though technical expertise is not required for natural language interface
8. **Deployment Model**: The system can be deployed as a cloud service, on-premises installation, or hybrid configuration based on organizational requirements
9. **Vendor Cooperation**: All supported API Gateway vendors provide stable APIs and documentation. Vendor-specific adapters maintained for each supported gateway. **Initial phase: webMethods API Gateway documentation and stable APIs required.**
10. **Compliance**: Organizations have appropriate data handling and privacy policies in place for API traffic analysis
11. **Policy Application**: All supported API Gateways support policy actions for security, optimization, and compliance. Vendor-specific adapters transform vendor-neutral `PolicyAction` to gateway-specific policies. **Initial phase: webMethods policy actions supported.**
12. **Vendor-Neutral Architecture**: The system uses vendor-neutral data models with vendor-specific adapters for gateway integration, ensuring consistent functionality across all vendors. **Initial phase: WebMethodsGatewayAdapter implemented using models from `backend/app/models/webmethods/`; Kong and Apigee adapters deferred.**

## Dependencies

1. **API Gateway Integrations**: Requires integration libraries or SDKs for each supported Gateway vendor with policy management capabilities. **Initial phase: webMethods integration libraries required.**
2. **Machine Learning Infrastructure**: Requires computational resources for training and running prediction models
3. **Time Series Database**: Requires high-performance time series database for storing and querying API metrics
4. **Natural Language Processing**: Requires NLP capabilities for query understanding and response generation
5. **Security Vulnerability Database**: Requires access to current vulnerability databases and security advisories
6. **Monitoring Infrastructure**: Requires infrastructure for continuous data collection and processing
7. **Authentication System**: Requires secure authentication and authorization for system access and Gateway connections
8. **Notification System**: Requires notification infrastructure for alerts and predictions

## Out of Scope

1. **API Development**: This system monitors and manages existing APIs but does not provide API development or design tools
2. **Gateway Replacement**: This system complements existing API Gateways but does not replace them
3. **Application Performance Monitoring**: This system focuses on API-level monitoring, not application-level code profiling
4. **Custom Gateway Development**: This system integrates with existing Gateways but does not provide custom Gateway implementation
5. **API Marketplace**: This system does not provide API discovery or marketplace features for external API consumers
6. **Billing and Monetization**: This system does not handle API billing, usage-based pricing, or revenue management
7. **API Documentation Generation**: This system catalogs APIs but does not generate or host API documentation
8. **Load Testing**: This system monitors production traffic but does not provide load testing or synthetic monitoring capabilities
9. **Backend Service Optimization**: This system focuses on gateway-level optimizations only; backend service optimizations (query optimization, connection pooling, resource allocation) are out of scope
10. **Cost Savings Calculation**: The system does not calculate or track cost savings from optimization recommendations