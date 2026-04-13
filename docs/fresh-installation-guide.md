# Fresh Installation Guide: API Intelligence Plane

**Version**: 2.0.0  
**Last Updated**: 2026-04-11  
**Architecture**: Vendor-Neutral with Time-Bucketed Metrics

## Overview

This guide provides step-by-step instructions for installing the API Intelligence Plane with the new vendor-neutral architecture. This is a **fresh installation guide** - no data migration is required as the system starts with clean, empty indices.

### What's New in Version 2.0

- **Vendor-Neutral Data Models**: All data stored in vendor-neutral format
- **Time-Bucketed Metrics**: Metrics stored separately in time-bucketed indices (1m, 5m, 1h, 1d)
- **Adapter Pattern**: Gateway-specific adapters transform vendor data to vendor-neutral models
- **Separated Intelligence**: Intelligence fields in `intelligence_metadata` wrapper
- **WebMethods-First**: Initial implementation focuses on webMethods API Gateway

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+, RHEL 8+) or macOS 12+
- **Docker**: 24.0+ with Docker Compose 2.23+
- **Memory**: Minimum 8GB RAM (16GB recommended)
- **Storage**: Minimum 50GB free space (100GB+ recommended for production)
- **Network**: Outbound HTTPS access for LLM providers

### Software Requirements

- **Python**: 3.11 or higher
- **Node.js**: 18.0 or higher
- **Java**: 17 or higher (for demo gateway, optional)
- **Git**: 2.30 or higher

### API Gateway Requirements

For webMethods API Gateway integration:
- **webMethods API Gateway**: 10.15 or higher
- **API Access**: REST API endpoint accessible from backend
- **Credentials**: Basic auth credentials for API Gateway
- **OpenSearch Access**: Access to webMethods transactional logs in OpenSearch

## Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/api-intelligence-plane-v2.git
cd api-intelligence-plane-v2
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your configuration
nano .env
```

**Required Configuration**:

```bash
# OpenSearch Configuration
OPENSEARCH_HOST=localhost
OPENSEARCH_PORT=9200
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin
OPENSEARCH_USE_SSL=false

# LLM Provider Configuration (choose one)
LLM_PROVIDER=openai  # or anthropic, azure, etc.
OPENAI_API_KEY=your-api-key-here

# Backend Configuration
BACKEND_HOST=0.0.0.0
BACKEND_PORT=8000
BACKEND_RELOAD=true

# Frontend Configuration
FRONTEND_PORT=3000
VITE_API_BASE_URL=http://localhost:8000

# Scheduler Configuration
DISCOVERY_INTERVAL=5  # minutes
METRICS_INTERVAL=1    # minutes
SECURITY_SCAN_INTERVAL=60  # minutes
PREDICTION_INTERVAL=15     # minutes

# Feature Flags
PREDICTION_AI_ENABLED=true
PREDICTION_AI_THRESHOLD=0.8
```

### Step 3: Start Services with Docker Compose

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps

# Expected output:
# NAME                    STATUS
# opensearch              Up (healthy)
# backend                 Up (healthy)
# frontend                Up
```

### Step 4: Initialize OpenSearch Indices

The system will automatically create empty indices with the new vendor-neutral schema:

```bash
# Initialize all indices
docker-compose exec backend python scripts/init_opensearch.py

# Expected output:
# ✓ Created index: api-inventory
# ✓ Created index: gateway-registry
# ✓ Created index template: api-metrics-1m-*
# ✓ Created index template: api-metrics-5m-*
# ✓ Created index template: api-metrics-1h-*
# ✓ Created index template: api-metrics-1d-*
# ✓ Created index template: transactional-logs-*
# ✓ Created index: api-predictions
# ✓ Created index: security-findings
# ✓ Created index: compliance-violations
# ✓ Created index: optimization-recommendations
# ✓ Created index: rate-limit-policies
# ✓ Created index: query-history
```

### Step 5: Register API Gateway

Register your first API Gateway through the UI or API:

**Option A: Using the Frontend UI**

1. Navigate to http://localhost:3000
2. Go to "Gateways" page
3. Click "Add Gateway"
4. Fill in the form:
   - **Name**: Production Gateway
   - **Vendor**: webmethods
   - **Base URL**: http://your-gateway:5555
   - **Credentials**: Basic auth (username/password)
   - **Transactional Logs URL**: http://your-opensearch:9200
   - **Transactional Logs Credentials**: Basic auth for OpenSearch

**Option B: Using the API**

```bash
curl -X POST http://localhost:8000/api/v1/gateways \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Production Gateway",
    "vendor": "webmethods",
    "base_url": "http://your-gateway:5555",
    "credentials": {
      "type": "basic",
      "username": "Administrator",
      "password": "manage"
    },
    "transactional_logs_url": "http://your-opensearch:9200",
    "transactional_logs_credentials": {
      "type": "basic",
      "username": "admin",
      "password": "admin"
    }
  }'
```

### Step 6: Trigger Initial Discovery

```bash
# Trigger API discovery for the registered gateway
curl -X POST http://localhost:8000/api/v1/discovery/discover \
  -H "Content-Type: application/json" \
  -d '{
    "gateway_id": "your-gateway-uuid"
  }'

# Check discovery status
curl http://localhost:8000/api/v1/apis?gateway_id=your-gateway-uuid
```

### Step 7: Verify Installation

```bash
# Check backend health
curl http://localhost:8000/health

# Check OpenSearch indices
curl http://localhost:9200/_cat/indices?v

# Check frontend
open http://localhost:3000
```

## Post-Installation Configuration

### Configure Background Schedulers

The system includes background schedulers that run automatically:

- **Discovery Job**: Runs every 5 minutes (configurable via `DISCOVERY_INTERVAL`)
- **Metrics Collection**: Runs every 1 minute (configurable via `METRICS_INTERVAL`)
- **Security Scanning**: Runs every 1 hour (configurable via `SECURITY_SCAN_INTERVAL`)
- **Prediction Generation**: Runs every 15 minutes (configurable via `PREDICTION_INTERVAL`)
- **Compliance Monitoring**: Runs every 24 hours

To modify scheduler intervals, update `.env` and restart the backend:

```bash
docker-compose restart backend
```

### Generate Mock Data (Optional)

For testing and demonstration purposes, generate mock data:

```bash
# Generate mock APIs and metrics
docker-compose exec backend python scripts/generate_mock_data.py

# Generate security vulnerabilities
docker-compose exec backend python scripts/generate_mock_security_data.py --count 50

# Generate predictions
docker-compose exec backend python scripts/generate_mock_predictions.py

# Generate optimization recommendations
docker-compose exec backend python scripts/generate_mock_optimizations.py

# Generate compliance violations
docker-compose exec backend python scripts/generate_mock_compliance.py
```

### Configure Index Lifecycle Management

Set up automatic index cleanup based on retention policies:

```bash
# Apply ILM policies (automatically done during init_opensearch.py)
# Manual verification:
curl http://localhost:9200/_ilm/policy
```

**Default Retention Policies**:
- `api-metrics-1m-*`: 24 hours
- `api-metrics-5m-*`: 7 days
- `api-metrics-1h-*`: 30 days
- `api-metrics-1d-*`: 90 days
- `transactional-logs-*`: 7 days
- Other indices: 90 days or permanent

## Verification Checklist

- [ ] All Docker containers are running and healthy
- [ ] OpenSearch indices are created successfully
- [ ] Backend API responds to health checks
- [ ] Frontend UI is accessible
- [ ] At least one gateway is registered
- [ ] Initial API discovery completed successfully
- [ ] Metrics are being collected (check after 5 minutes)
- [ ] Background schedulers are running

## Architecture Overview

### Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (webMethods)                  │
│  • REST API: /rest/apigateway/apis                          │
│  • OpenSearch: Transactional logs                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              WebMethodsGatewayAdapter                        │
│  • Transform webMethods data to vendor-neutral models       │
│  • Store vendor-specific fields in vendor_metadata          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              Vendor-Neutral Data Models                      │
│  • API (base/api.py)                                        │
│  • Metric (base/metric.py) - Time-bucketed                  │
│  • TransactionalLog (base/transaction.py)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    OpenSearch Indices                        │
│  • api-inventory (permanent)                                │
│  • api-metrics-{1m,5m,1h,1d}-{YYYY.MM} (time-bucketed)     │
│  • transactional-logs-{YYYY.MM} (7 days)                   │
│  • api-predictions, security-findings, etc.                 │
└─────────────────────────────────────────────────────────────┘
```

### Index Structure

**API Inventory** (`api-inventory`):
- Vendor-neutral API metadata
- Policy actions with vendor_config
- Intelligence metadata (health_score, risk_score, etc.)
- Vendor metadata (vendor-specific fields)

**Time-Bucketed Metrics** (`api-metrics-{bucket}-{YYYY.MM}`):
- Separate indices for each time bucket (1m, 5m, 1h, 1d)
- Monthly index rotation
- Automatic retention cleanup
- Aggregated from raw transactional logs

**Transactional Logs** (`transactional-logs-{YYYY.MM}`):
- Raw event data from gateways
- 7-day retention
- Used for drill-down from aggregated metrics

## Troubleshooting

### Services Not Starting

```bash
# Check logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs opensearch

# Restart services
docker-compose restart
```

### OpenSearch Connection Issues

```bash
# Verify OpenSearch is accessible
curl http://localhost:9200

# Check OpenSearch health
curl http://localhost:9200/_cluster/health

# Verify credentials in .env
grep OPENSEARCH .env
```

### Gateway Connection Issues

```bash
# Test gateway connectivity
curl -u username:password http://your-gateway:5555/rest/apigateway/apis

# Check backend logs for adapter errors
docker-compose logs backend | grep -i "adapter\|gateway"
```

### No Metrics Appearing

```bash
# Verify metrics collection is running
docker-compose logs backend | grep -i "metrics\|scheduler"

# Check if transactional logs are accessible
curl -u admin:admin http://your-opensearch:9200/transactional-logs-*/_search

# Manually trigger metrics collection
curl -X POST http://localhost:8000/api/v1/metrics/collect
```

### Frontend Not Loading

```bash
# Check frontend logs
docker-compose logs frontend

# Verify API base URL in frontend/.env
grep VITE_API_BASE_URL frontend/.env

# Rebuild frontend
docker-compose build frontend
docker-compose up -d frontend
```

## Next Steps

1. **Configure Additional Gateways**: Add more API Gateways through the UI
2. **Set Up Monitoring**: Configure Prometheus and Grafana for system monitoring
3. **Enable TLS**: Follow [TLS Deployment Guide](./tls-deployment.md) for production
4. **Configure Alerts**: Set up alerting for critical predictions and security findings
5. **Customize Policies**: Configure rate limiting and optimization policies
6. **Review Documentation**: Read [Architecture Documentation](./architecture.md) for detailed system design

## Support

For issues and questions:
- **Documentation**: See [docs/](../docs/) directory
- **GitHub Issues**: https://github.com/yourusername/api-intelligence-plane-v2/issues
- **Architecture Guide**: [docs/architecture.md](./architecture.md)
- **API Reference**: [docs/api-reference.md](./api-reference.md)

## Appendix: Manual Installation (Without Docker)

### Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Set environment variables
export OPENSEARCH_HOST=localhost
export OPENSEARCH_PORT=9200
# ... other variables from .env

# Initialize OpenSearch
python scripts/init_opensearch.py

# Start backend
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup

```bash
cd frontend
npm install

# Create .env file
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# Start frontend
npm run dev
```

### OpenSearch Setup

```bash
# Download and extract OpenSearch
wget https://artifacts.opensearch.org/releases/bundle/opensearch/2.11.0/opensearch-2.11.0-linux-x64.tar.gz
tar -xzf opensearch-2.11.0-linux-x64.tar.gz
cd opensearch-2.11.0

# Configure
echo "plugins.security.disabled: true" >> config/opensearch.yml

# Start OpenSearch
./bin/opensearch