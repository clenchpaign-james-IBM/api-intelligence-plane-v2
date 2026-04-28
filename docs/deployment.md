# Deployment Guide: API Intelligence Plane

**Version**: 1.0.0  
**Last Updated**: 2026-03-12  
**Status**: Production Ready

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Environment Configuration](#environment-configuration)
4. [Local Development](#local-development)
5. [Docker Deployment](#docker-deployment)
6. [Kubernetes Deployment](#kubernetes-deployment)
7. [MCP Servers for External Agents](#mcp-servers-for-external-agents)
8. [Production Considerations](#production-considerations)
9. [Monitoring & Observability](#monitoring--observability)
10. [Backup & Recovery](#backup--recovery)
11. [Troubleshooting](#troubleshooting)

---

## Overview

This guide covers deploying the API Intelligence Plane in various environments:

- **Local Development**: Docker Compose for development
- **Staging/Production**: Kubernetes for scalable production deployment
- **MCP Servers**: Optional deployment for external AI agent integration (Bob IDE, Claude Desktop, etc.)

### Deployment Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer / Ingress                   │
└─────────────────────────────────────────────────────────────┘
                               │
                ┌──────────────┼──────────────┐
                ▼              ▼              ▼
         ┌──────────┐   ┌──────────┐   ┌──────────┐
         │ Frontend │   │ Backend  │   │  Demo    │
         │ (React)  │   │ (FastAPI)│   │ Gateway  │
         └──────────┘   └──────────┘   └──────────┘
                               │
                               ▼
                        ┌──────────┐
                        │OpenSearch│
                        │ Cluster  │
                        └──────────┘

Optional: External AI Agent Integration
┌─────────────────────────────────────────────────────────────┐
│              MCP Servers (for AI Agents)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Discovery   │  │   Metrics    │  │Optimization  │      │
│  │   (8001)     │  │   (8002)     │  │   (8004)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            ▼                                 │
│                     Backend API (8000)                       │
└─────────────────────────────────────────────────────────────┘
         ▲
         │ MCP Protocol
         │
┌────────┴────────┐
│   AI Agents     │
│  (Bob IDE,      │
│   Claude        │
│   Desktop)      │
└─────────────────┘
```

---

## Prerequisites

### Required Software

| Component | Version | Purpose |
|-----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.23+ | Local orchestration |
| Kubernetes | 1.28+ | Production orchestration |
| kubectl | 1.28+ | Kubernetes CLI |
| Helm | 3.12+ | Kubernetes package manager (optional) |

### System Requirements

#### Development Environment

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 4 cores | 8 cores |
| RAM | 8 GB | 16 GB |
| Disk | 20 GB | 50 GB |
| OS | Linux, macOS, Windows | Linux, macOS |

#### Production Environment

| Component | CPU | Memory | Disk | Replicas | Required |
|-----------|-----|--------|------|----------|----------|
| Frontend | 0.5 | 512 MB | 1 GB | 2-3 | Yes |
| Backend | 2 | 4 GB | 10 GB | 3-5 | Yes |
| Gateway | 1 | 2 GB | 5 GB | 2-3 | Yes |
| OpenSearch | 4 | 8 GB | 100 GB | 3 | Yes |
| MCP Servers | 0.5 | 1 GB | 2 GB | 1 each | No (for AI agents) |

### External Dependencies

- **LLM Provider** (Optional): OpenAI, Anthropic, Azure OpenAI, or Ollama
- **DNS**: Domain name for production deployment
- **TLS Certificates**: SSL/TLS certificates for HTTPS

---

## Environment Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example configuration
cp .env.example .env
```

### Core Configuration

```bash
# OpenSearch Configuration
OPENSEARCH_HOST=opensearch
OPENSEARCH_PORT=9200
OPENSEARCH_SCHEME=http
OPENSEARCH_USERNAME=admin
OPENSEARCH_PASSWORD=admin

# Backend Configuration
LOG_LEVEL=INFO
PYTHONUNBUFFERED=1

# LLM Configuration (Optional - for AI features)
LLM_PROVIDER=openai              # openai, anthropic, azure, ollama
LLM_API_KEY=your-api-key-here    # Required for cloud providers
LLM_MODEL=gpt-4                  # Model to use
LLM_TEMPERATURE=0.7              # Temperature for generation
LLM_MAX_TOKENS=2000              # Max tokens per request

# For Ollama (local LLM)
OLLAMA_BASE_URL=http://host.docker.internal:11434
LLM_PROVIDER=ollama
LLM_MODEL=llama3.1:8b

# Scheduler Configuration
DISCOVERY_INTERVAL=5             # Minutes between discovery runs
METRICS_INTERVAL=1               # Minutes between metrics collection
SECURITY_SCAN_INTERVAL=60        # Minutes between security scans
PREDICTION_INTERVAL=15           # Minutes between prediction generation
OPTIMIZATION_INTERVAL=30         # Minutes between optimization analysis

# Frontend Configuration
VITE_API_BASE_URL=http://localhost:8000
VITE_ENABLE_AI_FEATURES=true
```

### Production Configuration

Additional variables for production:

```bash
# Security
ENABLE_CORS=true
CORS_ORIGINS=https://yourdomain.com
SECRET_KEY=your-secret-key-here

# TLS/SSL
ENABLE_TLS=true
TLS_CERT_PATH=/certs/tls.crt
TLS_KEY_PATH=/certs/tls.key

# Monitoring
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# Backup
BACKUP_ENABLED=true
BACKUP_SCHEDULE="0 2 * * *"      # Daily at 2 AM
BACKUP_RETENTION_DAYS=30
```

---

## Local Development

### Quick Start with Docker Compose

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/api-intelligence-plane-v2.git
   cd api-intelligence-plane-v2
   ```

2. **Configure environment**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start all services**:
   ```bash
   docker-compose up -d
   ```

4. **Initialize OpenSearch indices**:
   ```bash
   docker-compose exec backend python scripts/init_opensearch.py
   ```

5. **Verify services**:
   ```bash
   # Check service status
   docker-compose ps
   
   # View logs
   docker-compose logs -f
   ```

6. **Access applications**:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - OpenSearch: http://localhost:9200
   - OpenSearch Dashboards: http://localhost:5601
   - Gateway: http://localhost:8080
   - MCP Discovery Server: http://localhost:8001 (optional, for AI agents)
   - MCP Metrics Server: http://localhost:8002 (optional, for AI agents)
   - MCP Optimization Server: http://localhost:8004 (optional, for AI agents)

### Service-Specific Commands

#### Backend

```bash
# Start backend only
docker-compose up -d backend

# View backend logs
docker-compose logs -f backend

# Execute commands in backend
docker-compose exec backend python scripts/generate_mock_data.py

# Run tests
docker-compose exec backend pytest

# Access backend shell
docker-compose exec backend bash
```

#### Frontend

```bash
# Start frontend only
docker-compose up -d frontend

# View frontend logs
docker-compose logs -f frontend

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend

# Access frontend shell
docker-compose exec frontend sh
```

#### OpenSearch

```bash
# Check OpenSearch health
curl http://localhost:9200/_cluster/health?pretty

# List indices
curl http://localhost:9200/_cat/indices?v

# View index mapping
curl http://localhost:9200/api-inventory/_mapping?pretty
```

### Development Workflow

1. **Make code changes** in your local directory
2. **Changes auto-reload** (backend and frontend have hot reload enabled)
3. **Test changes** using the running services
4. **View logs** to debug issues
5. **Commit changes** when ready

### Stopping Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v

# Stop specific service
docker-compose stop backend
```

---

## Docker Deployment

### Production Docker Compose

For production-like deployment with Docker Compose:

1. **Use production compose file**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

2. **Production compose differences**:
   - No volume mounts (uses built images)
   - Production-optimized builds
   - Health checks enabled
   - Resource limits configured
   - TLS enabled

### Building Production Images

```bash
# Build all images
docker-compose -f docker-compose.prod.yml build

# Build specific service
docker-compose -f docker-compose.prod.yml build backend

# Build with no cache
docker-compose -f docker-compose.prod.yml build --no-cache
```

### Image Registry

Push images to container registry:

```bash
# Tag images
docker tag aip-backend:latest registry.example.com/aip-backend:1.0.0
docker tag aip-frontend:latest registry.example.com/aip-frontend:1.0.0

# Push to registry
docker push registry.example.com/aip-backend:1.0.0
docker push registry.example.com/aip-frontend:1.0.0
```

---

## Kubernetes Deployment

### Prerequisites

1. **Kubernetes cluster** (EKS, GKE, AKS, or self-hosted)
2. **kubectl** configured to access cluster
3. **Container images** pushed to registry
4. **Persistent storage** provisioner configured

### Namespace Setup

```bash
# Create namespace
kubectl create namespace api-intelligence-plane

# Set as default namespace
kubectl config set-context --current --namespace=api-intelligence-plane
```

### Configuration

1. **Create ConfigMap**:
   ```bash
   kubectl create configmap aip-config \
     --from-env-file=.env \
     -n api-intelligence-plane
   ```

2. **Create Secrets**:
   ```bash
   # OpenSearch credentials
   kubectl create secret generic opensearch-credentials \
     --from-literal=username=admin \
     --from-literal=password=your-secure-password \
     -n api-intelligence-plane
   
   # LLM API keys
   kubectl create secret generic llm-credentials \
     --from-literal=api-key=your-llm-api-key \
     -n api-intelligence-plane
   
   # TLS certificates
   kubectl create secret tls aip-tls \
     --cert=path/to/tls.crt \
     --key=path/to/tls.key \
     -n api-intelligence-plane
   ```

### Deploy OpenSearch

```bash
# Apply OpenSearch manifests
kubectl apply -f k8s/opensearch/ -n api-intelligence-plane

# Wait for OpenSearch to be ready
kubectl wait --for=condition=ready pod -l app=opensearch \
  --timeout=300s -n api-intelligence-plane

# Verify OpenSearch
kubectl exec -it opensearch-0 -n api-intelligence-plane -- \
  curl http://localhost:9200/_cluster/health?pretty
```

### Deploy Backend

```bash
# Apply backend manifests
kubectl apply -f k8s/backend/ -n api-intelligence-plane

# Wait for backend to be ready
kubectl wait --for=condition=ready pod -l app=backend \
  --timeout=180s -n api-intelligence-plane

# Initialize OpenSearch indices
kubectl exec -it deployment/backend -n api-intelligence-plane -- \
  python scripts/init_opensearch.py
```

### Deploy Frontend

```bash
# Apply frontend manifests
kubectl apply -f k8s/frontend/ -n api-intelligence-plane

# Wait for frontend to be ready
kubectl wait --for=condition=ready pod -l app=frontend \
  --timeout=180s -n api-intelligence-plane
```

### Deploy Gateway

```bash
# Apply demo gateway manifests
kubectl apply -f k8s/gateway/ -n api-intelligence-plane

# Wait for gateway to be ready
kubectl wait --for=condition=ready pod -l app=gateway \
  --timeout=180s -n api-intelligence-plane
```

### Configure Ingress

```bash
# Apply ingress configuration
kubectl apply -f k8s/ingress.yaml -n api-intelligence-plane

# Get ingress IP/hostname
kubectl get ingress -n api-intelligence-plane
```

### Verify Deployment

```bash
# Check all pods
kubectl get pods -n api-intelligence-plane

# Check services
kubectl get svc -n api-intelligence-plane

# Check ingress
kubectl get ingress -n api-intelligence-plane

# View logs
kubectl logs -f deployment/backend -n api-intelligence-plane
kubectl logs -f deployment/frontend -n api-intelligence-plane
```

### Scaling

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n api-intelligence-plane

# Scale frontend
kubectl scale deployment frontend --replicas=3 -n api-intelligence-plane

# Auto-scaling (HPA)
kubectl autoscale deployment backend \
  --cpu-percent=70 \
  --min=3 \
  --max=10 \
  -n api-intelligence-plane
```

---

## MCP Servers for External Agents

MCP (Model Context Protocol) servers are **optional** components that enable external AI agents (like Bob IDE, Claude Desktop, or custom AI tools) to interact with the API Intelligence Plane. They are **NOT** required for the core application functionality.

### When to Deploy MCP Servers

Deploy MCP servers if you want to:
- Use Bob IDE to interact with API Intelligence Plane
- Integrate with Claude Desktop for AI-assisted operations
- Build custom AI agents that need programmatic access
- Enable AI-driven automation workflows

### MCP Server Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Agent (Bob IDE, Claude)                │
└─────────────────────────────────────────────────────────────┘
                               │
                               │ MCP Protocol (Streamable HTTP)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│                      MCP Servers (Thin Wrappers)             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  Discovery   │  │   Metrics    │  │Optimization  │      │
│  │   Server     │  │   Server     │  │   Server     │      │
│  │   (8001)     │  │   (8002)     │  │   (8004)     │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│         │                  │                  │              │
│         └──────────────────┼──────────────────┘              │
│                            │ HTTP REST API                   │
│                            ▼                                 │
│                     Backend API (8000)                       │
│                  (Single Source of Truth)                    │
└─────────────────────────────────────────────────────────────┘
```

### Available MCP Servers

| Server | Port | Purpose | Tools Exposed |
|--------|------|---------|---------------|
| **Discovery** | 8001 | API discovery operations | `discover_apis`, `list_shadow_apis`, `get_api_details` |
| **Metrics** | 8002 | Metrics collection and analysis | `collect_metrics`, `get_health_status`, `get_time_series` |
| **Optimization** | 8004 | Performance optimization | `generate_recommendations`, `analyze_performance`, `get_insights` |

### Deploy MCP Servers with Docker Compose

MCP servers are included in the default `docker-compose.yml`:

```bash
# Start all services including MCP servers
docker-compose up -d

# Start only MCP server (requires backend and opensearch)
docker-compose up -d mcp-unified

# Verify MCP servers are running
curl http://localhost:8001/mcp
curl http://localhost:8002/mcp
curl http://localhost:8004/mcp
```

### Deploy MCP Servers on Kubernetes

```bash
# Apply MCP server manifests
kubectl apply -f k8s/mcp-servers/ -n api-intelligence-plane

# Wait for MCP servers to be ready
kubectl wait --for=condition=ready pod -l app=mcp-servers \
  --timeout=180s -n api-intelligence-plane

# Verify deployment
kubectl get pods -l app=mcp-servers -n api-intelligence-plane

# Check MCP server logs
kubectl logs -f deployment/mcp-unified -n api-intelligence-plane
```

### Configure AI Agents to Use MCP Servers

#### Bob IDE Configuration

Add to your Bob IDE MCP settings (`.bob/mcp.json`):

```json
{
  "mcpServers": {
    "api-intelligence-discovery": {
      "command": "node",
      "args": [],
      "url": "http://localhost:8001/mcp",
      "transport": "streamablehttp"
    },
    "api-intelligence-metrics": {
      "command": "node",
      "args": [],
      "url": "http://localhost:8002/mcp",
      "transport": "streamablehttp"
    },
    "api-intelligence-optimization": {
      "command": "node",
      "args": [],
      "url": "http://localhost:8004/mcp",
      "transport": "streamablehttp"
    }
  }
}
```

#### Claude Desktop Configuration

Add to Claude Desktop MCP settings:

```json
{
  "mcpServers": {
    "api-intelligence": {
      "url": "http://localhost:8001/mcp",
      "transport": "streamablehttp"
    }
  }
}
```

### MCP Server Health Checks

```bash
# Check MCP server health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8004/health

# Test MCP protocol endpoint
curl http://localhost:8001/mcp

# List available tools
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

### MCP Server Scaling

MCP servers are stateless and can be scaled horizontally:

```bash
# Scale MCP server in Kubernetes
kubectl scale deployment mcp-unified --replicas=2 -n api-intelligence-plane
```

### Security Considerations for MCP Servers

1. **Network Access**:
   - MCP servers should only be accessible from trusted AI agent networks
   - Use network policies to restrict access
   - Consider VPN or private network for production

2. **Authentication** (Future):
   - Implement API key authentication for MCP endpoints
   - Use OAuth 2.0 for user-based access
   - Rate limiting per client

3. **Monitoring**:
   - Track MCP server usage and performance
   - Monitor for unusual access patterns
   - Log all MCP tool invocations

### Troubleshooting MCP Servers

#### MCP Server Not Responding

```bash
# Check if MCP server is running
docker-compose ps mcp-unified

# View MCP server logs
docker-compose logs -f mcp-unified

# Test backend connectivity from MCP server
docker-compose exec mcp-unified curl http://backend:8000/health
```

#### AI Agent Cannot Connect

```bash
# Verify MCP endpoint is accessible
curl http://localhost:8001/mcp

# Check firewall rules
# Ensure ports 8001, 8002, 8004 are open

# Verify MCP protocol response
curl -X POST http://localhost:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","id":1}'
```

#### Tool Execution Failures

```bash
# Check backend API is accessible
curl http://localhost:8000/health

# Verify OpenSearch connectivity
docker-compose exec mcp-unified curl http://opensearch:9200/_cluster/health

# Check MCP server environment variables
docker-compose exec mcp-unified env | grep -E "(OPENSEARCH|BACKEND)"
```

### MCP Server Documentation

For detailed MCP server documentation, see:
- [MCP Architecture](./mcp-architecture.md)
- [MCP Usage Guide](./mcp-usage-guide.md)
- [MCP Server Development](./contributing.md#mcp-server-development)

---

## Production Considerations

### High Availability

1. **Multiple Replicas**:
   - Backend: 3-5 replicas
   - Frontend: 2-3 replicas
   - OpenSearch: 3-node cluster
   - Gateway: 2-3 replicas

2. **Pod Disruption Budgets**:
   ```yaml
   apiVersion: policy/v1
   kind: PodDisruptionBudget
   metadata:
     name: backend-pdb
   spec:
     minAvailable: 2
     selector:
       matchLabels:
         app: backend
   ```

3. **Anti-Affinity Rules**:
   ```yaml
   affinity:
     podAntiAffinity:
       requiredDuringSchedulingIgnoredDuringExecution:
       - labelSelector:
           matchExpressions:
           - key: app
             operator: In
             values:
             - backend
         topologyKey: kubernetes.io/hostname
   ```

### Resource Management

1. **Resource Requests and Limits**:
   ```yaml
   resources:
     requests:
       cpu: "1"
       memory: "2Gi"
     limits:
       cpu: "2"
       memory: "4Gi"
   ```

2. **Quality of Service**:
   - Critical services: Guaranteed QoS
   - Non-critical: Burstable QoS

### Security

1. **Network Policies**:
   - Restrict pod-to-pod communication
   - Allow only necessary ingress/egress

2. **Pod Security**:
   - Run as non-root user
   - Read-only root filesystem
   - Drop unnecessary capabilities

3. **Secrets Management**:
   - Use external secrets manager (AWS Secrets Manager, HashiCorp Vault)
   - Rotate credentials regularly
   - Encrypt secrets at rest

4. **TLS/SSL**:
   - Enable TLS for all external communications
   - Use cert-manager for certificate management
   - Enforce HTTPS redirects

### Performance Optimization

1. **Caching**:
   - Redis for session data
   - CDN for static assets
   - OpenSearch query caching

2. **Database Optimization**:
   - Index optimization
   - Query performance tuning
   - Connection pooling

3. **Load Balancing**:
   - Use cloud load balancer
   - Configure health checks
   - Enable session affinity if needed

---

## Monitoring & Observability

### Prometheus & Grafana

1. **Deploy monitoring stack**:
   ```bash
   kubectl apply -f k8s/monitoring/
   ```

2. **Access Grafana**:
   ```bash
   kubectl port-forward svc/grafana 3001:80 -n api-intelligence-plane
   # Open http://localhost:3001
   ```

3. **Import dashboards**:
   - API Intelligence Plane Overview
   - Backend Performance
   - OpenSearch Metrics
   - Prediction Accuracy

### Logging

1. **Centralized logging**:
   - Use OpenSearch for log aggregation
   - Configure log retention policies
   - Set up log rotation

2. **Log levels**:
   - Production: INFO or WARNING
   - Debug: DEBUG (temporary)

### Alerting

Configure alerts for:
- High error rates
- Service downtime
- Resource exhaustion
- Prediction accuracy degradation
- OpenSearch cluster health

---

## Backup & Recovery

### OpenSearch Backup

1. **Configure snapshot repository**:
   ```bash
   curl -X PUT "http://opensearch:9200/_snapshot/backup_repo" \
     -H 'Content-Type: application/json' \
     -d '{
       "type": "fs",
       "settings": {
         "location": "/backup",
         "compress": true
       }
     }'
   ```

2. **Create snapshot**:
   ```bash
   curl -X PUT "http://opensearch:9200/_snapshot/backup_repo/snapshot_1"
   ```

3. **Restore snapshot**:
   ```bash
   curl -X POST "http://opensearch:9200/_snapshot/backup_repo/snapshot_1/_restore"
   ```

### Automated Backups

Use CronJob for automated backups:

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: opensearch-backup
spec:
  schedule: "0 2 * * *"  # Daily at 2 AM
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: backup
            image: curlimages/curl
            command:
            - /bin/sh
            - -c
            - |
              curl -X PUT "http://opensearch:9200/_snapshot/backup_repo/snapshot_$(date +%Y%m%d)"
          restartPolicy: OnFailure
```

### Disaster Recovery

1. **Backup checklist**:
   - OpenSearch snapshots
   - Configuration files
   - Secrets and credentials
   - Custom scripts

2. **Recovery procedure**:
   - Deploy infrastructure
   - Restore OpenSearch snapshots
   - Apply configurations
   - Verify data integrity

---

## Troubleshooting

### Common Issues

#### Services Not Starting

```bash
# Check pod status
kubectl get pods -n api-intelligence-plane

# View pod events
kubectl describe pod <pod-name> -n api-intelligence-plane

# Check logs
kubectl logs <pod-name> -n api-intelligence-plane

# Check resource constraints
kubectl top pods -n api-intelligence-plane
```

#### OpenSearch Connection Issues

```bash
# Test OpenSearch connectivity
kubectl exec -it deployment/backend -n api-intelligence-plane -- \
  curl http://opensearch:9200/_cluster/health

# Check OpenSearch logs
kubectl logs -f statefulset/opensearch -n api-intelligence-plane

# Verify service
kubectl get svc opensearch -n api-intelligence-plane
```

#### High Memory Usage

```bash
# Check memory usage
kubectl top pods -n api-intelligence-plane

# Increase memory limits
kubectl set resources deployment backend \
  --limits=memory=8Gi \
  -n api-intelligence-plane

# Check for memory leaks
kubectl exec -it deployment/backend -n api-intelligence-plane -- \
  python -m memory_profiler app/main.py
```

#### Slow Performance

```bash
# Check resource utilization
kubectl top nodes
kubectl top pods -n api-intelligence-plane

# Review OpenSearch performance
curl http://opensearch:9200/_nodes/stats?pretty

# Check network latency
kubectl exec -it deployment/backend -n api-intelligence-plane -- \
  ping opensearch
```

### Debug Mode

Enable debug logging:

```bash
# Update ConfigMap
kubectl edit configmap aip-config -n api-intelligence-plane
# Set LOG_LEVEL=DEBUG

# Restart pods
kubectl rollout restart deployment/backend -n api-intelligence-plane
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/health

# Frontend health
curl http://localhost:3000

# OpenSearch health
curl http://localhost:9200/_cluster/health?pretty

# Gateway health
curl http://localhost:8080/actuator/health
```

---

## Maintenance

### Updates and Upgrades

1. **Rolling updates**:
   ```bash
   # Update image
   kubectl set image deployment/backend \
     backend=registry.example.com/aip-backend:1.1.0 \
     -n api-intelligence-plane
   
   # Monitor rollout
   kubectl rollout status deployment/backend -n api-intelligence-plane
   ```

2. **Rollback**:
   ```bash
   # Rollback to previous version
   kubectl rollout undo deployment/backend -n api-intelligence-plane
   
   # Rollback to specific revision
   kubectl rollout undo deployment/backend --to-revision=2 \
     -n api-intelligence-plane
   ```

### Database Maintenance

```bash
# Reindex OpenSearch
curl -X POST "http://opensearch:9200/_reindex" \
  -H 'Content-Type: application/json' \
  -d '{
    "source": {"index": "old-index"},
    "dest": {"index": "new-index"}
  }'

# Force merge indices
curl -X POST "http://opensearch:9200/api-metrics-*/_forcemerge?max_num_segments=1"

# Clear cache
curl -X POST "http://opensearch:9200/_cache/clear"
```

---

## Additional Resources

- [Architecture Documentation](./architecture.md)
- [API Reference](./api-reference.md)
- [Contributing Guidelines](./contributing.md)
- [AI Setup Guide](./ai-setup.md)
- [MCP Architecture](./mcp-architecture.md)

---

## Support

For deployment assistance:

- 📧 Email: support@api-intelligence-plane.com
- 💬 Discord: [Join our community](https://discord.gg/api-intelligence-plane)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/api-intelligence-plane-v2/issues)