# Quickstart Guide: API Intelligence Plane

**Date**: 2026-03-09  
**Version**: 1.0.0  
**Estimated Setup Time**: 30 minutes

## Overview

This guide will help you set up and run the API Intelligence Plane locally for development and testing. By the end, you'll have all components running and be able to discover APIs, view predictions, and interact with the natural language query interface.

---

## Prerequisites

### Required Software

- **Docker** 24.0+ and **Docker Compose** 2.20+
- **Python** 3.11+
- **Node.js** 18+ and **npm** 9+
- **Java** 17+ (for Demo Gateway)
- **Git**

### System Requirements

- **RAM**: 8GB minimum, 16GB recommended
- **Disk**: 10GB free space
- **OS**: macOS, Linux, or Windows with WSL2

### API Keys (Optional for MVP)

- OpenAI API key (for LLM features)
- Or use local LLM via Ollama

---

## Quick Start (Docker Compose)

### 1. Clone Repository

```bash
git clone https://github.com/your-org/api-intelligence-plane.git
cd api-intelligence-plane
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
nano .env
```

**Minimum `.env` configuration**:
```env
# OpenSearch
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin

# LLM Provider (choose one)
LLM_PROVIDER=openai
OPENAI_API_KEY=your-key-here

# Or use local Ollama
# LLM_PROVIDER=ollama
# OLLAMA_BASE_URL=http://localhost:11434

# Backend
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000

# Frontend
FRONTEND_PORT=3000

# MCP Servers
MCP_DISCOVERY_PORT=8001
MCP_METRICS_PORT=8002
MCP_SECURITY_PORT=8003
MCP_OPTIMIZATION_PORT=8004

# Demo Gateway
DEMO_GATEWAY_PORT=9000
```

### 3. Start All Services

```bash
# Start all containers
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

### 4. Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend
curl http://localhost:3000

# Check Demo Gateway
curl http://localhost:9000/health

# Check MCP servers
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
```

### 5. Access Applications

- **Frontend UI**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Demo Gateway**: http://localhost:9000
- **OpenSearch Dashboards**: http://localhost:5601

---

## Manual Setup (Development)

### 1. Set Up OpenSearch

```bash
# Start OpenSearch with Docker
docker run -d \
  --name opensearch \
  -p 9200:9200 -p 9600:9600 \
  -e "discovery.type=single-node" \
  -e "OPENSEARCH_INITIAL_ADMIN_PASSWORD=Admin@123" \
  opensearchproject/opensearch:2.11.0

# Verify OpenSearch is running
curl -XGET https://localhost:9200 -u admin:Admin@123 -k
```

### 2. Set Up Backend

```bash
cd backend

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations (create indices)
python scripts/init_opensearch.py

# Start backend server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Set Up MCP Servers

```bash
cd mcp-servers

# Install dependencies
pip install -r requirements.txt

# Start discovery server
python discovery_server.py &

# Start metrics server
python metrics_server.py &

# Start security server
python security_server.py &

# Start optimization server
python optimization_server.py &
```

### 4. Set Up Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Set Up Demo Gateway

```bash
cd demo-gateway

# Build with Maven
./mvnw clean package

# Run the gateway
java -jar target/native-gateway-1.0.0.jar
```

---

## Initial Configuration

### 1. Register Demo Gateway

```bash
curl -X POST http://localhost:8000/gateways \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Native API Gateway",
    "vendor": "native",
    "connection_url": "http://localhost:9000",
    "credentials": {
      "type": "api_key",
      "api_key": "demo-key-12345"
    }
  }'
```

### 2. Register Sample APIs in Demo Gateway

```bash
# Register a sample API
curl -X POST http://localhost:9000/apis \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Users API",
    "version": "1.0.0",
    "base_path": "/api/users",
    "upstream_url": "http://backend:8000/users",
    "endpoints": [
      {
        "path": "/api/users",
        "method": "GET"
      },
      {
        "path": "/api/users/{id}",
        "method": "GET"
      }
    ],
    "authentication": {
      "type": "bearer"
    }
  }'
```

### 3. Trigger API Discovery

```bash
# Discover APIs from the gateway
curl -X POST http://localhost:8000/gateways/{gateway_id}/discover
```

### 4. Generate Sample Traffic

```bash
# Run traffic generator script
python scripts/generate_traffic.py --gateway-url http://localhost:9000 --duration 300
```

---

## Verification Steps

### 1. Check API Discovery

```bash
# List discovered APIs
curl http://localhost:8000/apis

# Expected: At least 1 API discovered
```

### 2. Check Metrics Collection

```bash
# Get API metrics
curl "http://localhost:8000/apis/{api_id}/metrics?start_time=2026-03-09T00:00:00Z&end_time=2026-03-09T23:59:59Z"

# Expected: Metrics data points
```

### 3. Check Predictions

```bash
# List predictions
curl http://localhost:8000/predictions

# Expected: Predictions generated (may take 15 minutes)
```

### 4. Check Security Scanning

```bash
# List vulnerabilities
curl http://localhost:8000/vulnerabilities

# Expected: Security findings (may take 1 hour)
```

### 5. Test Natural Language Query

```bash
# Execute a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query_text": "Which APIs are currently active?"
  }'

# Expected: Natural language response with API list
```

---

## Common Tasks

### View Logs

```bash
# Backend logs
docker-compose logs -f backend

# MCP server logs
docker-compose logs -f mcp-discovery

# Demo Gateway logs
docker-compose logs -f demo-gateway

# All logs
docker-compose logs -f
```

### Restart Services

```bash
# Restart specific service
docker-compose restart backend

# Restart all services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

### Access OpenSearch

```bash
# List all indices
curl -XGET "http://localhost:9200/_cat/indices?v" -u admin:Admin@123

# Query API inventory
curl -XGET "http://localhost:9200/api-inventory/_search?pretty" -u admin:Admin@123

# Query metrics
curl -XGET "http://localhost:9200/api-metrics-*/_search?pretty" -u admin:Admin@123
```

### Run Tests

```bash
# Backend integration tests
cd backend
pytest tests/integration/

# Frontend tests
cd frontend
npm test

# End-to-end tests
cd tests/e2e
pytest test_complete_workflow.py
```

---

## Troubleshooting

### OpenSearch Connection Issues

**Problem**: Backend can't connect to OpenSearch

**Solution**:
```bash
# Check OpenSearch is running
docker ps | grep opensearch

# Check OpenSearch logs
docker logs opensearch

# Verify connection
curl -XGET http://localhost:9200/_cluster/health -u admin:Admin@123
```

### MCP Server Not Responding

**Problem**: MCP tools return errors

**Solution**:
```bash
# Check MCP server health
curl http://localhost:8001/health

# Restart MCP servers
docker-compose restart mcp-discovery mcp-metrics mcp-security mcp-optimization

# Check logs
docker-compose logs mcp-discovery
```

### Demo Gateway Not Starting

**Problem**: Demo Gateway fails to start

**Solution**:
```bash
# Check Java version
java -version  # Should be 17+

# Check port availability
lsof -i :9000

# Check Gateway logs
docker-compose logs demo-gateway

# Rebuild Gateway
cd demo-gateway
./mvnw clean package
```

### No APIs Discovered

**Problem**: Discovery returns empty results

**Solution**:
```bash
# Verify Gateway is registered
curl http://localhost:8000/gateways

# Check Gateway connection
curl http://localhost:9000/health

# Manually trigger discovery
curl -X POST http://localhost:8000/gateways/{gateway_id}/discover

# Check discovery logs
docker-compose logs mcp-discovery
```

### LLM Queries Failing

**Problem**: Natural language queries return errors

**Solution**:
```bash
# Check LLM provider configuration
echo $LLM_PROVIDER
echo $OPENAI_API_KEY

# Test LLM connection
python scripts/test_llm.py

# Use local Ollama instead
docker run -d -p 11434:11434 ollama/ollama
docker exec -it ollama ollama pull llama2
```

---

## Development Workflow

### 1. Make Code Changes

```bash
# Backend changes
cd backend
# Edit files
# Backend auto-reloads with uvicorn --reload

# Frontend changes
cd frontend
# Edit files
# Frontend auto-reloads with Vite
```

### 2. Run Tests

```bash
# Backend tests
cd backend
pytest tests/

# Frontend tests
cd frontend
npm test

# Integration tests
pytest tests/integration/
```

### 3. Format Code

```bash
# Backend formatting
cd backend
black .
isort .
flake8 .

# Frontend formatting
cd frontend
npm run lint
npm run format
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature"
git push origin feature-branch
```

---

## Production Deployment

### Docker Compose (Simple)

```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# With environment overrides
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Kubernetes (Advanced)

```bash
# Apply Kubernetes manifests
kubectl apply -f k8s/namespace.yaml
kubectl apply -f k8s/opensearch/
kubectl apply -f k8s/backend/
kubectl apply -f k8s/frontend/
kubectl apply -f k8s/mcp-servers/
kubectl apply -f k8s/demo-gateway/

# Check deployment status
kubectl get pods -n api-intelligence-plane
```

---

## Next Steps

1. **Explore the UI**: Navigate to http://localhost:3000 and explore the dashboard
2. **Register More Gateways**: Add your actual API Gateways
3. **Configure Policies**: Set up rate limiting and security policies
4. **Review Documentation**: Read the full documentation in `/docs`
5. **Run Integration Tests**: Execute end-to-end test scenarios
6. **Monitor Performance**: Check metrics and predictions
7. **Customize Configuration**: Adjust settings for your environment

---

## Useful Commands Reference

```bash
# Start everything
docker-compose up -d

# Stop everything
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# View all logs
docker-compose logs -f

# Rebuild specific service
docker-compose up -d --build backend

# Execute command in container
docker-compose exec backend bash

# Check resource usage
docker stats

# Export data
python scripts/export_data.py --output backup.json

# Import data
python scripts/import_data.py --input backup.json
```

---

## Support

- **Documentation**: `/docs` directory
- **API Reference**: http://localhost:8000/docs
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

---

**Quickstart Complete!** 🎉

You now have a fully functional API Intelligence Plane installation. Start discovering APIs, monitoring health, and leveraging AI-driven insights!

---

**Last Updated**: 2026-03-09  
**Version**: 1.0.0  
**Maintainer**: API Intelligence Plane Team