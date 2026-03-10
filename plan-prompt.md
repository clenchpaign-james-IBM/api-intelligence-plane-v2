Back-end: FastAPI + OpenSearch;
Front-end: React.js
Components: Backend, Frontend, MCP servers, Database, Demo API Gateway
Agentic AI Framework: LangChain, LangGraph
MCP servers:
- Famework: FastMCP for servers and clients
- Trasport: Streamable HTTP
- Custom health endpoints
Data:
- Backgroud scheduler jobs fetch APIs and Metrics from multi-vendor API Gateways periodically and store in local OpenSearch
- AI-driven insights stored in OpenSearch
API Endpoints:
- REST endopints for UI
- Authentication not required for MVP
LLM Provider Support:
- Model-agnostic architecture using LiteLLM
- Configuration-driven provider selection
API Gateway vendor-neutral support:
- Different vendor support
- Native support for "Native API Gateway"
Settings/Configurations:
- Components endpoints
- API Gateway connection settings
- LLM provider and model
Data storage:
- APIs and Metrics: API Gateway -> OpenSearch
- AI Insights: AI Agents -> OpenSearch
Data retrieval flow:
- Frontend -> Backend -> AI Agents -> MCP tools -> OpenSearch
- Frontend -> Backend -> AI Agents -> OpenSearch
Demo API Gateway:
- Name as "Native API Gateway"
- Works with API Intelligence Plane seamlessly
- Support for REST APIs
- API policies: Protocol translation, Authentication, Request validation, Routing, Logging, Rate limiting, Monitoring, Throttling, Response validation, Transformation
- Tech stack: Backend - Java, Frontend - React.js, Database: OpenSearch
Testing:
- Unit tests not required.
- Integration tests (by integrating all components) required.
- End-to-end tests required.
- Mock data generation support for testing.
- Use Demo API Gateway for Integation and End-to-end tests.
Deployment:
- Docker containers for all components
Documentation:
- API documentation using Swagger/OpenAPI
- User guides and tutorials
- Architecture diagrams and system design
Code quality:
- Avoid Hardcoded Values
- DRY Principle
- Null Safety
- Modularity and Reusability
- Formatting and Indentation
- Error handling
- Strategy, Adapter patterns for vendor-neutral Gateways
Additional considerations:
- FedRAMP 140-3 compliance
    - NIST-approved algorithms 
    - Encryption in transit