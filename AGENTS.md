# api-intelligence-plane-v2 Development Guidelines

Auto-generated from all feature plans. Last updated: 2026-03-11

## Active Technologies

### Backend (Python 3.11+)
- **Framework**: FastAPI 0.109+
- **AI/ML**: LangChain 0.1+, LangGraph 0.0.20+, LiteLLM 1.17+
- **MCP**: FastMCP 0.1+
- **Database**: OpenSearch Python Client 2.4+
- **Scheduling**: APScheduler 3.10+
- **Testing**: pytest 7.4+, pytest-asyncio 0.21+
- **Code Quality**: Black, isort, flake8, mypy

### Frontend (TypeScript/React)
- **Framework**: React 18.2+, Vite 5.0+
- **Routing**: React Router 6.20+
- **State Management**: TanStack Query 5.14+
- **UI Components**: Tailwind CSS 3.4+
- **Charts**: Recharts 2.10+
- **HTTP Client**: Axios 1.6+
- **Code Quality**: ESLint 8.56+, Prettier 3.1+, TypeScript 5.3+

### Demo Gateway (Java 17+)
- **Framework**: Spring Boot 3.2+
- **Database**: OpenSearch Java Client 2.8+
- **Metrics**: Micrometer 1.12+
- **Build Tool**: Maven 3.9+
- **Testing**: JUnit 5.10+

### MCP Servers (Python 3.11+)
- **Framework**: FastMCP 0.1+
- **Transport**: Streamable HTTP
- **Database**: OpenSearch Python Client 2.4+

### Infrastructure
- **Container**: Docker 24+, Docker Compose 2.23+
- **Orchestration**: Kubernetes 1.28+
- **Storage**: OpenSearch 2.11+
- **Monitoring**: Prometheus, Grafana

## Project Structure

```text
api-intelligence-plane-v2/
├── backend/              # FastAPI backend service
│   ├── app/
│   │   ├── api/         # REST API endpoints (v1)
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic
│   │   ├── agents/      # LangChain/LangGraph agents
│   │   ├── adapters/    # Gateway adapters (Strategy pattern)
│   │   ├── db/          # OpenSearch client and repositories
│   │   ├── scheduler/   # APScheduler jobs
│   │   ├── middleware/  # FastAPI middleware
│   │   └── utils/       # Utility functions
│   ├── tests/           # Integration and E2E tests
│   └── scripts/         # Utility scripts
├── frontend/            # React.js frontend
│   └── src/
│       ├── components/  # Reusable components
│       ├── pages/       # Page components
│       ├── services/    # API client services
│       ├── hooks/       # Custom React hooks
│       └── types/       # TypeScript types
├── mcp-servers/         # MCP servers (FastMCP)
│   ├── discovery_server.py
│   ├── metrics_server.py
│   ├── optimization_server.py
│   └── common/          # Shared utilities
├── demo-gateway/        # Native API Gateway (Spring Boot)
│   └── src/main/java/com/example/gateway/
├── tests/               # Cross-component tests
├── config/              # Configuration files
├── k8s/                 # Kubernetes manifests
├── docs/                # Documentation
└── specs/               # Feature specifications
```

## Commands

### Backend
```bash
# Development
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Testing
pytest tests/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Code Quality
black app/ tests/
isort app/ tests/
flake8 app/ tests/
mypy app/
```

### Frontend
```bash
# Development
cd frontend
npm install
npm run dev

# Build
npm run build
npm run preview

# Testing
npm test
npm run test:coverage

# Code Quality
npm run lint
npm run format
npm run type-check
```

### Demo Gateway
```bash
# Development
cd demo-gateway
mvn spring-boot:run

# Build
mvn clean package
java -jar target/demo-gateway-1.0.0.jar

# Testing
mvn test
mvn verify
```

### MCP Servers
```bash
# Development
cd mcp-servers
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python discovery_server.py
python metrics_server.py
python optimization_server.py
```

### Docker
```bash
# Local Development
docker-compose up -d
docker-compose logs -f

# Production
docker-compose -f docker-compose.prod.yml up -d

# Rebuild
docker-compose build --no-cache
```

## Code Style

### Python (Backend & MCP Servers)
- **Formatter**: Black (line length: 100)
- **Import Sorting**: isort (profile: black)
- **Linter**: flake8 (max-line-length: 100)
- **Type Checking**: mypy (strict mode)
- **Docstrings**: Google style
- **Naming**: snake_case for functions/variables, PascalCase for classes

### TypeScript/JavaScript (Frontend)
- **Formatter**: Prettier (semi: false, singleQuote: true)
- **Linter**: ESLint (extends: recommended, typescript-eslint)
- **Style Guide**: Airbnb TypeScript
- **Naming**: camelCase for functions/variables, PascalCase for components/classes

### Java (Demo Gateway)
- **Style Guide**: Google Java Style Guide
- **Formatter**: Spring Java Format
- **Naming**: camelCase for methods/variables, PascalCase for classes

## Architecture Patterns

### Backend
- **Repository Pattern**: Data access abstraction
- **Service Layer**: Business logic separation
- **Strategy Pattern**: Gateway adapters for multi-vendor support
- **Dependency Injection**: FastAPI dependencies
- **Agent Pattern**: LangChain/LangGraph for AI workflows

### Frontend
- **Component-Based**: Reusable React components
- **Custom Hooks**: Shared logic extraction
- **Service Layer**: API client abstraction
- **State Management**: TanStack Query for server state

### Security
- **Encryption**: TLS 1.3 for all communications
- **Cryptography**: FIPS 140-3 compliant algorithms
- **Secrets**: Environment variables, never hardcoded
- **Audit Logging**: All operations logged

## Performance Targets

- Query latency: <5 seconds for natural language queries
- Discovery cycles: Complete within 5 minutes
- Security scans: Complete within 1 hour
- API support: 1000+ APIs
- Data retention: 90 days
- Concurrent requests: Support millions per minute

## Testing Strategy

- **Integration Tests**: Cross-component testing (required)
- **E2E Tests**: Complete workflow validation (required)
- **Unit Tests**: Not required per project specification
- **Mock Data**: Fixtures for testing scenarios
- **Coverage**: Focus on integration and E2E coverage

## Recent Changes

- 2026-03-11: Updated with comprehensive technology stack and architecture patterns
- 2026-03-09: Added Python 3.11+ (Backend), JavaScript/TypeScript (Frontend), Java (Demo API Gateway)

<!-- MANUAL ADDITIONS START -->
## Chat Instructions

- Don't create summary reports at the end of conversations
<!-- MANUAL ADDITIONS END -->
