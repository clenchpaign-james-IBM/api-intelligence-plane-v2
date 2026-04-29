# Kubernetes Deployment for API Intelligence Plane

This directory contains Kubernetes manifests for deploying the API Intelligence Plane in production.

## Prerequisites

- Kubernetes cluster (v1.28+)
- kubectl CLI configured
- NGINX Ingress Controller installed
- cert-manager installed (for TLS certificates)
- Persistent Volume provisioner (for OpenSearch storage)

## Directory Structure

```
k8s/
├── namespace.yaml              # Namespace definition
├── secrets.yaml                # Secrets (update before deployment)
├── configmap.yaml              # Configuration maps
├── ingress.yaml                # Ingress rules
├── opensearch/
│   ├── statefulset.yaml       # OpenSearch StatefulSet
│   └── service.yaml           # OpenSearch Services
├── backend/
│   ├── deployment.yaml        # Backend API Deployment
│   └── service.yaml           # Backend Service
├── frontend/
│   ├── deployment.yaml        # Frontend Deployment
│   └── service.yaml           # Frontend Service
├── mcp-servers/
│   ├── deployment.yaml        # MCP Unified Server Deployment
│   └── service.yaml           # MCP Service
└── monitoring/                 # Monitoring stack (optional)
```

## Quick Start

### 1. Update Secrets

**IMPORTANT**: Before deploying, update the secrets in `secrets.yaml`:

```bash
# Edit secrets.yaml and replace placeholder values
vim k8s/secrets.yaml

# Required secrets:
# - opensearch-credentials: admin-password
# - llm-credentials: openai-api-key (and other LLM providers)
```

### 2. Update Ingress Host

Edit `ingress.yaml` and replace `api-intelligence-plane.example.com` with your actual domain:

```bash
vim k8s/ingress.yaml
```

### 3. Deploy to Kubernetes

```bash
# Create namespace
kubectl apply -f k8s/namespace.yaml

# Create secrets (ensure you've updated them first!)
kubectl apply -f k8s/secrets.yaml

# Create config maps
kubectl apply -f k8s/configmap.yaml

# Deploy OpenSearch
kubectl apply -f k8s/opensearch/

# Wait for OpenSearch to be ready
kubectl wait --for=condition=ready pod -l app=opensearch -n api-intelligence-plane --timeout=300s

# Deploy Backend
kubectl apply -f k8s/backend/

# Deploy Frontend
kubectl apply -f k8s/frontend/

# Deploy MCP Servers (optional)
kubectl apply -f k8s/mcp-servers/

# Deploy Ingress
kubectl apply -f k8s/ingress.yaml
```

### 4. Verify Deployment

```bash
# Check all pods are running
kubectl get pods -n api-intelligence-plane

# Check services
kubectl get svc -n api-intelligence-plane

# Check ingress
kubectl get ingress -n api-intelligence-plane

# View logs
kubectl logs -f deployment/backend -n api-intelligence-plane
kubectl logs -f deployment/frontend -n api-intelligence-plane
```

## Configuration

### Environment Variables

Environment variables are configured via:
- **Secrets**: Sensitive data (passwords, API keys)
- **ConfigMaps**: Non-sensitive configuration

### Resource Limits

Default resource allocations:

| Component | Requests | Limits |
|-----------|----------|--------|
| OpenSearch | 4Gi RAM, 1 CPU | 4Gi RAM, 2 CPU |
| Backend | 512Mi RAM, 500m CPU | 1Gi RAM, 1 CPU |
| Frontend | 128Mi RAM, 100m CPU | 256Mi RAM, 200m CPU |
| MCP Servers | 256Mi RAM, 250m CPU | 512Mi RAM, 500m CPU |

Adjust these in the respective deployment files based on your workload.

### Storage

OpenSearch uses PersistentVolumeClaims with:
- **Storage Class**: `standard` (change if needed)
- **Size**: 50Gi per node (adjust based on data retention needs)

## Scaling

### Horizontal Scaling

Scale deployments:

```bash
# Scale backend
kubectl scale deployment backend --replicas=5 -n api-intelligence-plane

# Scale frontend
kubectl scale deployment frontend --replicas=3 -n api-intelligence-plane

# Scale MCP servers
kubectl scale deployment mcp-unified --replicas=3 -n api-intelligence-plane
```

### OpenSearch Scaling

To scale OpenSearch cluster:

```bash
# Edit the StatefulSet
kubectl edit statefulset opensearch -n api-intelligence-plane

# Change spec.replicas to desired number (must be odd for quorum)
# Example: 3, 5, 7
```

## Monitoring

### Health Checks

All services expose `/health` endpoints:

```bash
# Check backend health
kubectl exec -it deployment/backend -n api-intelligence-plane -- curl http://localhost:8000/health

# Check MCP health
kubectl exec -it deployment/mcp-unified -n api-intelligence-plane -- curl http://localhost:8001/health
```

### Logs

View logs:

```bash
# Backend logs
kubectl logs -f deployment/backend -n api-intelligence-plane

# Frontend logs
kubectl logs -f deployment/frontend -n api-intelligence-plane

# OpenSearch logs
kubectl logs -f statefulset/opensearch -n api-intelligence-plane

# MCP logs
kubectl logs -f deployment/mcp-unified -n api-intelligence-plane
```

### Metrics

If Prometheus is installed:

```bash
# Port-forward to access metrics
kubectl port-forward svc/backend 8000:8000 -n api-intelligence-plane

# Access metrics at http://localhost:8000/metrics
```

## Backup & Recovery

### OpenSearch Backup

```bash
# Create snapshot repository (configure in OpenSearch)
# Use S3, GCS, or Azure Blob Storage

# Create snapshot
curl -X PUT "opensearch-client:9200/_snapshot/my_backup/snapshot_1?wait_for_completion=true"

# Restore snapshot
curl -X POST "opensearch-client:9200/_snapshot/my_backup/snapshot_1/_restore"
```

### Configuration Backup

```bash
# Export all manifests
kubectl get all -n api-intelligence-plane -o yaml > backup.yaml

# Export secrets (encrypted)
kubectl get secrets -n api-intelligence-plane -o yaml > secrets-backup.yaml
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n api-intelligence-plane

# Check events
kubectl get events -n api-intelligence-plane --sort-by='.lastTimestamp'

# Check logs
kubectl logs <pod-name> -n api-intelligence-plane
```

### OpenSearch Issues

```bash
# Check OpenSearch cluster health
kubectl exec -it opensearch-0 -n api-intelligence-plane -- curl -k https://localhost:9200/_cluster/health

# Check OpenSearch logs
kubectl logs opensearch-0 -n api-intelligence-plane

# Restart OpenSearch pod
kubectl delete pod opensearch-0 -n api-intelligence-plane
```

### Backend Connection Issues

```bash
# Test backend connectivity
kubectl exec -it deployment/backend -n api-intelligence-plane -- curl http://opensearch-client:9200

# Check environment variables
kubectl exec -it deployment/backend -n api-intelligence-plane -- env | grep OPENSEARCH
```

### Ingress Issues

```bash
# Check ingress status
kubectl describe ingress api-intelligence-plane -n api-intelligence-plane

# Check NGINX ingress logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller

# Test internal service
kubectl run -it --rm debug --image=curlimages/curl --restart=Never -- curl http://backend.api-intelligence-plane:8000/health
```

## Security

### TLS/SSL

TLS is managed by cert-manager with Let's Encrypt:

```bash
# Check certificate status
kubectl get certificate -n api-intelligence-plane

# Describe certificate
kubectl describe certificate api-intelligence-plane-tls -n api-intelligence-plane
```

### Network Policies

Apply network policies for additional security:

```bash
# Example: Restrict backend to only accept traffic from frontend
kubectl apply -f k8s/network-policies/
```

### RBAC

Create service accounts with minimal permissions:

```bash
# Create service account
kubectl create serviceaccount api-intelligence-plane -n api-intelligence-plane

# Bind role
kubectl create rolebinding api-intelligence-plane --clusterrole=view --serviceaccount=api-intelligence-plane:api-intelligence-plane -n api-intelligence-plane
```

## Updating

### Rolling Updates

```bash
# Update backend image
kubectl set image deployment/backend backend=api-intelligence-plane/backend:v2.0.0 -n api-intelligence-plane

# Check rollout status
kubectl rollout status deployment/backend -n api-intelligence-plane

# Rollback if needed
kubectl rollout undo deployment/backend -n api-intelligence-plane
```

### Configuration Updates

```bash
# Update ConfigMap
kubectl apply -f k8s/configmap.yaml

# Restart deployments to pick up changes
kubectl rollout restart deployment/backend -n api-intelligence-plane
kubectl rollout restart deployment/frontend -n api-intelligence-plane
```

## Cleanup

### Remove Deployment

```bash
# Delete all resources
kubectl delete namespace api-intelligence-plane

# Or delete individually
kubectl delete -f k8s/ingress.yaml
kubectl delete -f k8s/mcp-servers/
kubectl delete -f k8s/frontend/
kubectl delete -f k8s/backend/
kubectl delete -f k8s/opensearch/
kubectl delete -f k8s/configmap.yaml
kubectl delete -f k8s/secrets.yaml
kubectl delete -f k8s/namespace.yaml
```

## Production Checklist

Before deploying to production:

- [ ] Update all secrets in `secrets.yaml`
- [ ] Configure proper domain in `ingress.yaml`
- [ ] Set up TLS certificates (cert-manager)
- [ ] Configure persistent storage for OpenSearch
- [ ] Set appropriate resource limits
- [ ] Enable monitoring and alerting
- [ ] Configure backup strategy
- [ ] Set up log aggregation
- [ ] Review security policies
- [ ] Test disaster recovery procedures
- [ ] Document runbooks for common issues
- [ ] Set up CI/CD pipeline for updates

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [OpenSearch Kubernetes Guide](https://opensearch.org/docs/latest/install-and-configure/install-opensearch/kubernetes/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)

## Support

For issues or questions:
- GitHub Issues: https://github.com/your-org/api-intelligence-plane/issues
- Documentation: See `docs/deployment.md`
- Email: support@intelligence-plane.example.com