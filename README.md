# API Intelligence Plane

> AI-driven API management platform that transforms API operations from reactive firefighting to proactive, autonomous management.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![React 18](https://img.shields.io/badge/react-18-blue.svg)](https://reactjs.org/)
[![Java 17](https://img.shields.io/badge/java-17-orange.svg)](https://openjdk.org/)

## Overview

API Intelligence Plane is an intelligent companion to existing API Gateways, providing:

- 🔍 **Autonomous API Discovery** - Automatically discover all APIs including shadow APIs
- 🔮 **Predictive Health Management** - 24-48 hour advance failure predictions
- 🔒 **Continuous Security Scanning** - Automated vulnerability detection and remediation
- ⚡ **Real-time Performance Optimization** - AI-driven performance recommendations
- 🎯 **Intelligent Rate Limiting** - Adaptive rate limiting based on usage patterns
- 💬 **Natural Language Interface** - Query API intelligence using natural language

## Architecture

The API Intelligence Plane uses a **thin wrapper architecture** where MCP servers act as protocol adapters that delegate to backend services, ensuring a single source of truth for business logic.

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend (React)                         │
│              Dashboard, APIs, Security, Query UI             │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend API (FastAPI)                       │
│         Discovery, Metrics, Predictions, Security            │
│              (Single Source of Truth)                        │
└─────────────────────────────────────────────────────────────┘
                    │                   │
          ┌─────────┴─────────┐         │
          ▼                   ▼         ▼
┌──────────────────────┐  ┌──────────────────────┐
│ MCP Servers (Thin    │  │  Demo Gateway        │
│ Wrappers - FastMCP)  │  │  (Spring Boot)       │
│ - Discovery (8001)   │  │  Native API Gateway  │
│ - Metrics (8002)     │  │  Implementation      │
│ - Optimization (8004)│  │                      │
└──────────────────────┘  └──────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              OpenSearch (Data Store)                         │
│    API Inventory, Metrics, Predictions, Security Findings   │
└─────────────────────────────────────────────────────────────┘
```

📖 **See [MCP Architecture Documentation](docs/mcp-architecture.md) for detailed information about the thin wrapper pattern and implementation.**

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Python 3.11+
- Node.js 18+
- Java 17+
- OpenAI API key (or other LLM provider)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/api-intelligence-plane-v2.git
   cd api-intelligence-plane-v2
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your LLM API keys
   ```

3. **Start services with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Initialize OpenSearch indices**
   ```bash
   docker-compose exec backend python scripts/init_opensearch.py
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - OpenSearch Dashboards: http://localhost:5601
   - Demo Gateway: http://localhost:8080

### Manual Setup (Development)

#### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

#### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

#### Demo Gateway Setup

```bash
cd demo-gateway
mvn clean install
mvn spring-boot:run
```

## Project Structure

```
api-intelligence-plane-v2/
├── backend/              # FastAPI backend service
│   ├── app/
│   │   ├── api/         # REST API endpoints
│   │   ├── models/      # Pydantic models
│   │   ├── services/    # Business logic
│   │   ├── agents/      # LangChain/LangGraph agents
│   │   ├── adapters/    # Gateway adapters
│   │   ├── db/          # OpenSearch client
│   │   └── scheduler/   # Background jobs
│   └── tests/           # Integration & E2E tests
├── frontend/            # React.js frontend
│   └── src/
│       ├── components/  # React components
│       ├── pages/       # Page components
│       └── services/    # API clients
├── mcp-servers/         # MCP servers (FastMCP)
│   ├── discovery_server.py
│   ├── metrics_server.py
│   ├── security_server.py
│   └── optimization_server.py
├── demo-gateway/        # Demo API Gateway (Spring Boot)
│   └── src/main/java/
├── tests/               # Cross-component tests
├── config/              # Configuration files
├── k8s/                 # Kubernetes manifests
└── docs/                # Documentation
```

## Features

### 1. API Discovery & Monitoring (P1)
- Automatic discovery of all APIs including shadow APIs
- Real-time health monitoring
- Traffic analysis and metrics collection

### 2. Predictive Health Management (P1)
- 24-48 hour advance failure predictions
- Contributing factors analysis
- Recommended preventive actions
- **🤖 AI-Enhanced**: LLM-powered trend analysis and detailed explanations

### 3. Security Scanning & Remediation (P2)
- Continuous vulnerability scanning
- Automated remediation for common issues
- Security posture tracking

### 4. Performance Optimization (P2)
- Real-time optimization recommendations
- Estimated impact analysis
- Implementation tracking
- **🤖 AI-Enhanced**: LLM-generated insights and prioritization guidance

### 5. Intelligent Rate Limiting (P3)
- Adaptive rate limiting
- Priority-based policies
- Consumer tier management

### 6. Natural Language Interface (P3)
- Query API intelligence using natural language
- Contextual responses
- Conversation history

### 🆕 AI-Enhanced Analysis

The platform includes optional AI-powered features that enhance predictions and recommendations:

- **Smart Predictions**: LLM analyzes metrics trends to provide detailed explanations of why failures are predicted
- **Intelligent Recommendations**: AI-generated optimization insights with implementation guidance and prioritization
- **Natural Language Explanations**: Human-readable interpretations of technical predictions
- **Graceful Fallback**: Automatically falls back to rule-based analysis if LLM is unavailable

**Setup**: See [AI Setup Guide](docs/ai-setup.md) for configuration instructions.

**API Endpoints**:
- `POST /api/v1/predictions/ai-enhanced` - Generate AI-enhanced predictions
- `GET /api/v1/predictions/{id}/explanation` - Get AI explanation for prediction
- `POST /api/v1/optimization/ai-enhanced` - Generate AI-enhanced recommendations
- `GET /api/v1/optimization/{id}/insights` - Get AI insights for recommendation
- Add `?use_ai=true` to existing endpoints for AI-enhanced generation

## Technology Stack

- **Backend**: Python 3.11+, FastAPI, LangChain, LangGraph, LiteLLM
- **Frontend**: React 18, TypeScript, Vite, TanStack Query, Recharts, Tailwind CSS
- **MCP**: FastMCP with Streamable HTTP transport
- **Demo Gateway**: Java 17, Spring Boot 3.2
- **Database**: OpenSearch 2.18
- **AI/ML**: LangChain for agent orchestration, LiteLLM for multi-provider support
- **Testing**: pytest, Jest, JUnit

## Development

### Running Tests

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# Integration tests
cd tests
pytest integration/

# E2E tests
pytest e2e/
```

### Code Quality

```bash
# Backend linting
cd backend
black .
isort .
flake8 .
mypy .

# Frontend linting
cd frontend
npm run lint
npm run format
```

## Configuration

Key configuration options in `.env`:

- `OPENSEARCH_HOST` - OpenSearch connection
- `LLM_PROVIDER` - Primary LLM provider (openai, anthropic, azure, etc.)
- `LLM_API_KEY` - LLM API key
- `DISCOVERY_INTERVAL` - API discovery frequency (minutes)
- `METRICS_INTERVAL` - Metrics collection frequency (minutes)
- `SECURITY_SCAN_INTERVAL` - Security scan frequency (minutes)

See [`.env.example`](.env.example) for all configuration options.

## Documentation

- [AI Setup Guide](docs/ai-setup.md) - Configure AI-enhanced features
- [Architecture Documentation](docs/architecture.md)
- [API Reference](docs/api-reference.md)
- [Deployment Guide](docs/deployment.md)
- [Contributing Guidelines](docs/contributing.md)

## Roadmap

- [x] Phase 1: Setup & Infrastructure
- [ ] Phase 2: Foundational Components
- [ ] Phase 3: User Story 1 - Discovery & Monitoring
- [ ] Phase 4: User Story 2 - Predictive Health
- [ ] Phase 5: User Story 3 - Security Scanning
- [ ] Phase 6: User Story 4 - Performance Optimization
- [ ] Phase 7: User Story 5 - Rate Limiting
- [ ] Phase 8: User Story 6 - Natural Language Interface
- [ ] Phase 9: Polish & Production Readiness

## Contributing

Contributions are welcome! Please read our [Contributing Guidelines](docs/contributing.md) first.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For questions and support:
- 📧 Email: support@api-intelligence-plane.com
- 💬 Discord: [Join our community](https://discord.gg/api-intelligence-plane)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/api-intelligence-plane-v2/issues)

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- Powered by [LangChain](https://www.langchain.com/)
- UI components from [Tailwind CSS](https://tailwindcss.com/)
- Data storage with [OpenSearch](https://opensearch.org/)

---

**Status**: 🚧 In Development | **Version**: 1.0.0 | **Last Updated**: 2026-03-09