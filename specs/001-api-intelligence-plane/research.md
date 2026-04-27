# Research & Technology Decisions: API Intelligence Plane

**Date**: 2026-03-09  
**Feature**: API Intelligence Plane  
**Phase**: 0 - Research & Outline

## Overview

This document captures research findings, technology decisions, and architectural patterns for the API Intelligence Plane project. All "NEEDS CLARIFICATION" items from the Technical Context have been resolved through research and analysis.

---

## 1. Backend Framework: FastAPI

### Decision
Use **FastAPI** (Python 3.11+) as the primary backend framework.

### Rationale
- **High Performance**: ASGI-based, comparable to Node.js and Go
- **Async Support**: Native async/await for concurrent API Gateway polling
- **Auto Documentation**: Built-in OpenAPI/Swagger generation
- **Type Safety**: Pydantic models for data validation
- **Ecosystem**: Excellent integration with Python ML/AI libraries
- **Developer Experience**: Fast development with automatic validation

### Alternatives Considered
- **Flask**: Rejected - lacks native async support, slower performance
- **Django**: Rejected - too heavyweight for API-focused service, slower
- **Node.js/Express**: Rejected - Python ecosystem better for ML/AI integration

### Implementation Notes
- Use FastAPI 0.104+ for latest async improvements
- Leverage dependency injection for service management
- Use Pydantic V2 for enhanced performance
- Background tasks via BackgroundTasks or APScheduler

---

## 2. AI Framework: LangChain + LangGraph

### Decision
Use **LangChain** for agent orchestration and **LangGraph** for workflow management.

### Rationale
- **LangChain**: Industry-standard framework for LLM applications
  - Rich ecosystem of tools and integrations
  - Memory management for conversational AI
  - Chain composition for complex workflows
  - Built-in support for multiple LLM providers
- **LangGraph**: State machine for complex agent workflows
  - Explicit state management for multi-step processes
  - Cycle detection and error handling
  - Visualization of agent workflows
  - Better control flow than pure LangChain chains

### Alternatives Considered
- **AutoGPT/BabyAGI**: Rejected - less production-ready, harder to control
- **Semantic Kernel**: Rejected - less mature Python support
- **Custom Implementation**: Rejected - reinventing the wheel, maintenance burden

### Implementation Notes
- LangChain 0.1.0+ for latest features
- LangGraph for prediction, security analysis, optimization workflows
- Custom tools for OpenSearch integration
- Memory stores for conversation context

---

## 3. MCP Framework: FastMCP

### Decision
Use **FastMCP** for MCP server and client implementation with **Streamable HTTP** transport.

### Rationale
- **FastMCP**: Python-native MCP framework
  - Simple decorator-based tool definition
  - Built-in validation and error handling
  - Async support for concurrent operations
  - Easy integration with FastAPI
- **Streamable HTTP**: Production-ready transport
  - Works across network boundaries
  - Better for distributed deployments
  - Supports load balancing and scaling
  - Standard HTTP infrastructure compatibility

### Alternatives Considered
- **Stdio Transport**: Rejected - limited to local processes, harder to scale
- **SSE Transport**: Rejected - less mature, browser-focused
- **Custom Protocol**: Rejected - unnecessary complexity

### Implementation Notes
- FastMCP 0.2+ for latest features
- Custom health endpoints for monitoring
- Tool categories: discovery, metrics, security, optimization
- Resource endpoints for API inventory access

---

## 4. LLM Provider: LiteLLM

### Decision
Use **LiteLLM** as the unified LLM interface layer.

### Rationale
- **Provider Agnostic**: Single API for 100+ LLM providers
- **Fallback Support**: Automatic failover between providers
- **Cost Tracking**: Built-in usage and cost monitoring
- **Caching**: Response caching to reduce costs
- **Rate Limiting**: Provider-specific rate limit handling
- **Streaming**: Unified streaming interface

### Supported Providers (Initial)
1. OpenAI (GPT-4, GPT-3.5)
2. Anthropic (Claude 3)
3. Google (Gemini Pro)
4. Azure OpenAI
5. Local models via Ollama

### Alternatives Considered
- **Direct Provider SDKs**: Rejected - vendor lock-in, inconsistent APIs
- **LangChain LLM Wrappers**: Rejected - less flexible, harder to switch
- **Custom Abstraction**: Rejected - maintenance burden

### Implementation Notes
- LiteLLM 1.0+ for production stability
- Configuration-driven provider selection
- Environment variables for API keys
- Fallback chain: Primary → Secondary → Local

---

## 5. Data Storage: OpenSearch

### Decision
Use **OpenSearch** as the primary data store for all data types.

### Rationale
- **Time Series Data**: Excellent for API metrics and logs
- **Full-Text Search**: Natural language query support
- **Aggregations**: Real-time analytics and dashboards
- **Scalability**: Horizontal scaling for large datasets
- **Open Source**: No vendor lock-in, active community
- **ML Features**: Built-in anomaly detection capabilities

### Data Organization
```
Indices:
- api-inventory: API catalog and metadata
- api-metrics-{YYYY.MM}: Time-series metrics (monthly rotation)
- api-predictions: Failure predictions and confidence scores
- security-findings: Vulnerabilities and remediation status
- optimization-recommendations: Performance recommendations
- rate-limit-policies: Rate limiting configurations
- query-history: Natural language query logs
```

### Alternatives Considered
- **PostgreSQL + TimescaleDB**: Rejected - less flexible for unstructured data
- **MongoDB**: Rejected - weaker analytics capabilities
- **InfluxDB**: Rejected - limited to time series, need broader functionality
- **Elasticsearch**: Considered equivalent, OpenSearch chosen for open-source commitment

### Implementation Notes
- OpenSearch 2.11+ for latest features
- Index templates for consistent mapping
- ILM policies for data retention (90 days)
- Snapshot/restore for backups
- Security plugin for encryption at rest

---

## 6. Frontend Framework: React.js

### Decision
Use **React.js** with modern tooling for the frontend SPA.

### Rationale
- **Component Model**: Reusable UI components
- **Ecosystem**: Rich library ecosystem (charts, forms, routing)
- **Performance**: Virtual DOM for efficient updates
- **Developer Experience**: Hot reload, debugging tools
- **Community**: Large community, extensive resources

### Tech Stack
- **React 18+**: Concurrent features, automatic batching
- **Vite**: Fast build tool and dev server
- **React Router 6**: Client-side routing
- **TanStack Query**: Server state management and caching
- **Recharts**: Data visualization
- **Tailwind CSS**: Utility-first styling
- **TypeScript**: Type safety

### Alternatives Considered
- **Vue.js**: Rejected - smaller ecosystem, team familiarity
- **Angular**: Rejected - too heavyweight, steeper learning curve
- **Svelte**: Rejected - smaller ecosystem, less mature

### Implementation Notes
- Create React App alternative: Vite for faster builds
- Component library: Headless UI or Radix UI for accessibility
- State management: React Context + TanStack Query (no Redux needed)
- Real-time updates: WebSocket or Server-Sent Events

---

## 7. Demo API Gateway: Spring Boot + OpenSearch

### Decision
Build demo "Native API Gateway" using **Spring Boot** (Java) with **OpenSearch** backend.

### Rationale
- **Spring Boot**: Production-grade Java framework
  - Mature ecosystem for API development
  - Built-in security, monitoring, metrics
  - Easy integration with OpenSearch
- **OpenSearch**: Consistent with main application
  - Unified data storage approach
  - Simplified deployment and operations

### Gateway Features
- REST API support
- Policy engine: Protocol translation, Authentication, Request/Response validation
- Routing and load balancing
- Rate limiting and throttling
- Logging and monitoring
- Metrics export for Intelligence Plane

### Alternatives Considered
- **Kong**: Rejected - external dependency, harder to customize
- **Tyk**: Rejected - Go-based, different tech stack
- **Custom Python Gateway**: Rejected - Java better demonstrates vendor diversity

### Implementation Notes
- Spring Boot 3.2+ with Java 17+
- Spring WebFlux for reactive APIs
- OpenSearch Java client for data storage
- Micrometer for metrics export
- REST API for Intelligence Plane integration

---

## 8. Background Scheduling: APScheduler

### Decision
Use **APScheduler** for periodic data collection from API Gateways.

### Rationale
- **Python Native**: Integrates seamlessly with FastAPI
- **Flexible Scheduling**: Cron-like, interval, and one-time jobs
- **Persistence**: Job state persistence across restarts
- **Async Support**: Works with async functions
- **Monitoring**: Job execution tracking and error handling

### Scheduling Strategy
- **Discovery Jobs**: Every 5 minutes
- **Metrics Collection**: Every 1 minute
- **Security Scans**: Every 1 hour
- **Prediction Updates**: Every 15 minutes
- **Optimization Analysis**: Every 30 minutes

### Alternatives Considered
- **Celery**: Rejected - too heavyweight, requires message broker
- **Cron Jobs**: Rejected - external dependency, harder to manage
- **Custom Scheduler**: Rejected - unnecessary complexity

### Implementation Notes
- APScheduler 3.10+ with AsyncIOScheduler
- Job persistence via OpenSearch
- Error handling and retry logic
- Job monitoring dashboard

---

## 9. API Gateway Integration Patterns

### Decision
Use **Strategy Pattern** with **Adapter Pattern** for vendor-neutral Gateway support.

### Rationale
- **Strategy Pattern**: Encapsulates Gateway-specific algorithms
  - Discovery strategies per vendor
  - Metrics collection strategies
  - Configuration management strategies
- **Adapter Pattern**: Normalizes vendor-specific APIs
  - Unified interface for all Gateways
  - Vendor-specific adapters translate to common format
  - Easy to add new vendors

### Architecture
```python
# Strategy Pattern
class GatewayStrategy(ABC):
    @abstractmethod
    async def discover_apis(self) -> List[API]: ...
    @abstractmethod
    async def collect_metrics(self) -> List[Metric]: ...
    @abstractmethod
    async def apply_policy(self, policy: Policy) -> bool: ...

# Adapter Pattern
class GatewayAdapter(ABC):
    def __init__(self, strategy: GatewayStrategy): ...
    async def get_apis(self) -> List[API]: ...  # Normalized interface

# Concrete Implementations
class NativeGatewayStrategy(GatewayStrategy): ...
class KongGatewayStrategy(GatewayStrategy): ...
class ApigeeGatewayStrategy(GatewayStrategy): ...
```

### Alternatives Considered
- **Plugin System**: Rejected - more complex, harder to maintain
- **Direct Integration**: Rejected - tight coupling, hard to extend
- **Proxy Pattern**: Rejected - doesn't address algorithm variation

### Implementation Notes
- Factory pattern for strategy selection
- Configuration-driven strategy instantiation
- Capability detection per Gateway
- Graceful degradation for missing features

---

## 10. Testing Strategy

### Decision
Focus on **Integration** and **End-to-End** testing, skip unit tests per requirements.

### Rationale
- **Integration Tests**: Verify component interactions
  - Backend ↔ OpenSearch
  - Backend ↔ MCP Servers
  - Backend ↔ AI Agents
  - Frontend ↔ Backend
- **End-to-End Tests**: Verify complete workflows
  - API discovery flow
  - Prediction generation flow
  - Security scanning flow
  - Natural language query flow

### Testing Tools
- **Backend Integration**: pytest with pytest-asyncio
- **API Testing**: httpx for async HTTP testing
- **E2E Testing**: Playwright or Cypress
- **Mock Data**: Factory pattern for test data generation
- **Test Containers**: Docker containers for OpenSearch, Gateway

### Test Data Strategy
- Mock API Gateway responses
- Synthetic metrics data
- Known vulnerability patterns
- Predictable failure scenarios

### Alternatives Considered
- **Unit Tests**: Explicitly excluded per requirements
- **Manual Testing Only**: Rejected - not scalable, error-prone
- **Selenium**: Rejected - slower than Playwright/Cypress

### Implementation Notes
- pytest fixtures for test setup
- Separate test database indices
- CI/CD integration for automated testing
- Test coverage reporting (integration/e2e only)

---

## 11. Deployment Strategy: Docker Containers

### Decision
Deploy all components as **Docker containers** with Docker Compose for local development.

### Rationale
- **Consistency**: Same environment across dev, test, prod
- **Isolation**: Each component in separate container
- **Scalability**: Easy to scale individual components
- **Portability**: Deploy anywhere Docker runs
- **Orchestration**: Kubernetes-ready for production

### Container Architecture
```
Services:
- backend: FastAPI application
- frontend: Nginx serving React build
- opensearch: OpenSearch cluster
- mcp-unified: Unified MCP server for all functionality
- gateway: Native API Gateway
```

### Alternatives Considered
- **Virtual Machines**: Rejected - heavier, slower, less portable
- **Bare Metal**: Rejected - harder to manage, less portable
- **Serverless**: Rejected - stateful components, cost concerns

### Implementation Notes
- Multi-stage Docker builds for optimization
- Docker Compose for local development
- Kubernetes manifests for production
- Health checks for all containers
- Volume mounts for data persistence

---

## 12. Security & Compliance: FedRAMP 140-3

### Decision
Implement **NIST-approved algorithms** and **encryption in transit** for FedRAMP compliance.

### Rationale
- **FIPS 140-3**: Federal standard for cryptographic modules
- **NIST Algorithms**: AES-256, SHA-256, RSA-2048+
- **TLS 1.3**: Modern encryption for all communications
- **Certificate Management**: Automated cert rotation

### Implementation Requirements
- **Encryption in Transit**:
  - TLS 1.3 for all HTTP communications
  - mTLS for service-to-service communication
  - Encrypted WebSocket connections
- **Cryptographic Operations**:
  - Use cryptography library (FIPS-validated)
  - AES-256-GCM for data encryption
  - SHA-256 for hashing
  - RSA-2048 or ECDSA P-256 for signatures
- **Key Management**:
  - Secure key storage (environment variables, secrets manager)
  - Key rotation policies
  - Audit logging for key access

### Alternatives Considered
- **Basic TLS**: Rejected - insufficient for FedRAMP
- **Custom Crypto**: Rejected - dangerous, non-compliant
- **Older Algorithms**: Rejected - not NIST-approved

### Implementation Notes
- Use Python cryptography library (FIPS mode)
- Configure OpenSearch for encryption at rest
- TLS certificates via Let's Encrypt or internal CA
- Regular security audits and penetration testing

---

## 13. Natural Language Processing: LangChain + LLM

### Decision
Use **LangChain** with **LLM-based query understanding** for natural language interface.

### Rationale
- **LangChain**: Built-in NLP capabilities
  - Query parsing and intent detection
  - Context management for conversations
  - Tool selection based on intent
- **LLM**: Flexible query understanding
  - Handles ambiguous queries
  - Generates clarifying questions
  - Produces natural language responses

### Query Processing Pipeline
```
User Query → LLM Intent Detection → Tool Selection → 
OpenSearch Query → Result Formatting → LLM Response Generation
```

### Query Types Supported
- Status queries: "Which APIs are down?"
- Trend queries: "Show me error rate trends"
- Prediction queries: "What APIs might fail soon?"
- Security queries: "List critical vulnerabilities"
- Performance queries: "Why is the payment API slow?"
- Comparison queries: "Compare API performance"

### Alternatives Considered
- **Rule-Based NLP**: Rejected - inflexible, hard to maintain
- **spaCy/NLTK**: Rejected - requires extensive training data
- **Rasa**: Rejected - overkill for query interface

### Implementation Notes
- LangChain agents with custom tools
- OpenSearch query DSL generation
- Response templates for common queries
- Conversation memory for context
- Feedback loop for query improvement

---

## 14. Monitoring & Observability

### Decision
Implement comprehensive monitoring using **Prometheus** + **Grafana** + **OpenSearch**.

### Rationale
- **Prometheus**: Metrics collection and alerting
- **Grafana**: Visualization and dashboards
- **OpenSearch**: Log aggregation and analysis
- **Distributed Tracing**: OpenTelemetry for request tracing

### Monitoring Strategy
- **Application Metrics**: Request rates, latency, errors
- **System Metrics**: CPU, memory, disk, network
- **Business Metrics**: APIs discovered, predictions generated, vulnerabilities found
- **Custom Metrics**: Prediction accuracy, remediation success rate

### Alternatives Considered
- **ELK Stack**: Rejected - OpenSearch already chosen
- **Datadog**: Rejected - cost, vendor lock-in
- **CloudWatch**: Rejected - AWS-specific

### Implementation Notes
- Prometheus exporters for all services
- Grafana dashboards for each component
- Alert rules for critical conditions
- OpenTelemetry SDK for tracing
- Log correlation with trace IDs

---

## 15. Configuration Management

### Decision
Use **environment variables** + **configuration files** for settings management.

### Rationale
- **12-Factor App**: Environment-based configuration
- **Flexibility**: Different configs per environment
- **Security**: Secrets via environment variables
- **Validation**: Pydantic models for config validation

### Configuration Categories
- **Component Endpoints**: Backend, Frontend, MCP servers, OpenSearch
- **Gateway Connections**: URLs, credentials, capabilities
- **LLM Providers**: API keys, model selection, fallback chain
- **Scheduling**: Job intervals, retry policies
- **Security**: TLS certificates, encryption keys
- **Performance**: Timeouts, connection pools, cache settings

### Configuration Files
```
config/
├── default.yaml          # Default settings
├── development.yaml      # Dev overrides
├── production.yaml       # Prod overrides
└── test.yaml            # Test overrides
```

### Alternatives Considered
- **Database Config**: Rejected - adds dependency, slower
- **Consul/etcd**: Rejected - unnecessary complexity for MVP
- **Hardcoded Values**: Rejected - violates requirements

### Implementation Notes
- Pydantic Settings for validation
- Environment variable precedence
- Config reload without restart
- Secrets management via environment
- Config validation on startup

---

## Summary of Resolved Clarifications

All "NEEDS CLARIFICATION" items from Technical Context have been resolved:

1. ✅ **Language/Version**: Python 3.11+, JavaScript/TypeScript, Java
2. ✅ **Primary Dependencies**: FastAPI, LangChain, LangGraph, FastMCP, LiteLLM, React, Spring Boot
3. ✅ **Storage**: OpenSearch for all data types
4. ✅ **Testing**: pytest, Jest, Playwright/Cypress, JUnit
5. ✅ **Target Platform**: Linux/macOS servers, web browsers
6. ✅ **Project Type**: Distributed web application
7. ✅ **Performance Goals**: Defined and measurable
8. ✅ **Constraints**: FedRAMP compliance, vendor-neutral, model-agnostic
9. ✅ **Scale/Scope**: 1000+ APIs, 90-day retention, multi-vendor support

---

## Next Steps

With research complete, proceed to Phase 1:
1. Generate data-model.md (entity definitions)
2. Define interface contracts in /contracts/
3. Create quickstart.md (setup instructions)
4. Update agent context with new technologies

---

**Research Complete**: 2026-03-09  
**Approved By**: [Pending]  
**Next Phase**: Phase 1 - Design & Contracts