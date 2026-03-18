# API Intelligence Plane v2 - Demo Script

This guide will walk you through setting up the API Intelligence Plane application using Docker Compose, generating mock data, and exploring key workflows.

## Prerequisites

- Docker 24+ and Docker Compose 2.23+
- Git
- At least 8GB RAM available for Docker
- Ports 8000, 3000, 9200, 8001-8004 available
- (Optional) AI IDE like Bob or Claude Desktop for MCP integration

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd api-intelligence-plane-v2

# Copy environment configuration
cp .env.example .env

# Review and adjust settings if needed
cat .env
```

### 2. Start the Application

```bash
# Start all services with Docker Compose
docker-compose up -d

# Verify all services are running
docker-compose ps

# Expected services:
# - opensearch (port 9200)
# - backend (port 8000)
# - frontend (port 3000)
# - demo-gateway (port 8080)
# - mcp-discovery (port 8001)
# - mcp-metrics (port 8002)
# - mcp-optimization (port 8004)
```

### 3. Wait for Services to Initialize

```bash
# Monitor logs to ensure services are ready
docker-compose logs -f

# Wait for these messages:
# - "OpenSearch is ready"
# - "Application startup complete" (backend)
# - "Local: http://localhost:3000/" (frontend)
# - "Started GatewayApplication" (demo-gateway)

# Press Ctrl+C to stop following logs
```

### 4. Verify Service Health

```bash
# Check backend health
curl http://localhost:8000/health

# Check OpenSearch
curl http://localhost:9200/_cluster/health

# Check demo gateway
curl http://localhost:8080/actuator/health

# Check MCP servers
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8004/health
```

## Generate Mock Data

### 5. Initialize OpenSearch Indices

```bash
# Create required indices and mappings
docker-compose exec backend python scripts/init_opensearch.py --host opensearch

# Expected output: "All indices created successfully"
```

### 6. Generate Mock API Data

```bash
# Generate mock APIs, gateways, and metrics
docker-compose exec backend python scripts/generate_mock_data.py

# This creates:
# - 3 API Gateways (Native, Kong, Apigee)
# - 50+ APIs across different categories
# - Historical metrics data
# - API health scores and status
```

### 7. Generate Predictions and Optimizations

```bash
# Generate failure predictions
docker-compose exec backend python scripts/generate_mock_predictions.py

# Generate optimization recommendations
docker-compose exec backend python scripts/generate_mock_optimizations.py --all-apis

# Generate rate limiting policies
docker-compose exec backend python scripts/generate_mock_rate_limits.py
```

### 8. Generate Traffic (Optional)

```bash
# Simulate API traffic for realistic metrics
docker-compose exec backend python scripts/generate_traffic.py

# This will continuously generate traffic
# Press Ctrl+C to stop
```

## Explore Key Workflows

### Workflow 1: API Discovery and Inventory

**Objective**: Discover and view all APIs managed by gateways

1. **Open the Frontend**
   ```
   Navigate to: http://localhost:3000
   ```

2. **View API Inventory**
   - Click on "API Inventory" in the navigation
   - You should see 50+ APIs listed with:
     - API names and versions
     - Gateway assignments
     - Health scores
     - Status indicators

3. **Filter and Search**
   - Use the search bar to find specific APIs
   - Filter by gateway (Native, Kong, Apigee)
   - Filter by status (Active, Deprecated, Shadow)
   - Filter by health score

4. **View API Details**
   - Click on any API to see detailed information:
     - Endpoints and methods
     - Authentication requirements
     - Rate limits
     - Recent metrics
     - Associated gateway

5. **Test via API**
   ```bash
   # List all APIs
   curl http://localhost:8000/api/v1/apis

   # Get specific API
   curl http://localhost:8000/api/v1/apis/{api_id}

   # Search APIs
   curl "http://localhost:8000/api/v1/apis?gateway_id=native-gateway-1"
   ```

### Workflow 2: Gateway Management

**Objective**: Manage API gateways and trigger discovery

1. **View Gateways**
   - Navigate to "Gateways" page
   - See all connected gateways with status

2. **Trigger API Discovery**
   ```bash
   # Discover APIs from a gateway
   curl -X POST http://localhost:8000/api/v1/gateways/native-gateway-1/discover

   # Check discovery status
   curl http://localhost:8000/api/v1/gateways/native-gateway-1
   ```

3. **Add New Gateway** (via API)
   ```bash
   curl -X POST http://localhost:8000/api/v1/gateways \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test Gateway",
       "type": "kong",
       "base_url": "http://test-gateway:8000",
       "admin_url": "http://test-gateway:8001",
       "credentials": {
         "api_key": "test-key"
       }
     }'
   ```

### Workflow 3: Natural Language Queries

**Objective**: Query API inventory using natural language

1. **Via Frontend**
   - Navigate to "Query" page
   - Enter natural language queries like:
     - "Show me all payment APIs"
     - "Which APIs have health score below 70?"
     - "List deprecated APIs"
     - "Show APIs with high error rates"

2. **Via API**
   ```bash
   # Natural language query
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{
       "query": "Show me all payment APIs with health score below 80"
     }'

   # The response includes:
   # - Interpreted query
   # - Matching APIs
   # - Confidence score
   # - Explanation
   ```

3. **Example Queries to Try**
   ```bash
   # Find high-risk APIs
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Which APIs are at risk of failure?"}'

   # Find slow APIs
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "Show APIs with response time over 500ms"}'

   # Find shadow APIs
   curl -X POST http://localhost:8000/api/v1/query \
     -H "Content-Type: application/json" \
     -d '{"query": "List all shadow APIs"}'
   ```

### Workflow 4: Failure Predictions

**Objective**: View and analyze API failure predictions

1. **View Predictions Dashboard**
   - Navigate to "Predictions" page
   - See all predicted failures with:
     - Confidence scores
     - Time windows
     - Risk factors
     - Recommended actions

2. **View Prediction Details**
   - Click on any prediction to see:
     - Detailed risk analysis
     - Contributing factors
     - Historical patterns
     - Mitigation recommendations

3. **Via API**
   ```bash
   # Get all predictions
   curl http://localhost:8000/api/v1/predictions

   # Get predictions for specific API
   curl "http://localhost:8000/api/v1/predictions?api_id={api_id}"

   # Get high-confidence predictions only
   curl "http://localhost:8000/api/v1/predictions?min_confidence=0.8"

   # Generate new predictions
   curl -X POST http://localhost:8000/api/v1/predictions/generate
   ```

### Workflow 5: Performance Optimization

**Objective**: Get and apply optimization recommendations

1. **View Recommendations**
   - Navigate to "Optimization" page
   - See recommendations for:
     - Caching strategies
     - Rate limiting adjustments
     - Resource allocation
     - Query optimization

2. **View Recommendation Details**
   - Click on any recommendation to see:
     - Expected impact
     - Implementation steps
     - Risk assessment
     - Estimated effort

3. **Via API**
   ```bash
   # Get all recommendations
   curl http://localhost:8000/api/v1/optimization/recommendations

   # Get recommendations for specific API
   curl "http://localhost:8000/api/v1/optimization/recommendations?api_id={api_id}"

   # Generate new recommendations
   curl -X POST "http://localhost:8000/api/v1/optimization/recommendations?api_id={api_id}"
   ```

### Workflow 6: Rate Limiting

**Objective**: Manage and apply rate limiting policies

1. **View Rate Limits**
   ```bash
   # List all rate limit policies
   curl http://localhost:8000/api/v1/rate-limits

   # Get rate limits for specific API
   curl "http://localhost:8000/api/v1/rate-limits?api_id={api_id}"
   ```

2. **Create Rate Limit Policy**
   ```bash
   curl -X POST http://localhost:8000/api/v1/rate-limits \
     -H "Content-Type: application/json" \
     -d '{
       "api_id": "api-001",
       "policy_type": "fixed_window",
       "limit_thresholds": {
         "requests_per_minute": 100,
         "requests_per_hour": 5000
       },
       "enforcement_action": "throttle"
     }'
   ```

3. **Apply Rate Limit to Gateway**
   ```bash
   # Apply policy
   curl -X POST http://localhost:8000/api/v1/rate-limits/{policy_id}/apply

   # Check application status
   curl http://localhost:8000/api/v1/rate-limits/{policy_id}
   ```

### Workflow 7: MCP Server Integration with AI IDEs

**Objective**: Use MCP servers through AI IDEs for intelligent API management

The MCP (Model Context Protocol) servers are designed to be used with AI IDEs like **Bob** or **Claude Desktop** for natural language interactions with the API Intelligence Plane.

1. **Configure MCP Servers in Your AI IDE**

   For **Bob IDE** or **Claude Desktop**, add the following MCP server configurations:

   ```json
   {
     "mcpServers": {
       "api-discovery": {
         "command": "uvx",
         "args": ["mcp-proxy", "--transport", "streamablehttp", "http://localhost:8001/mcp"]
       },
       "api-metrics": {
         "command": "uvx",
         "args": ["mcp-proxy", "--transport", "streamablehttp", "http://localhost:8002/mcp"]
       },
       "api-optimization": {
         "command": "uvx",
         "args": ["mcp-proxy", "--transport", "streamablehttp", "http://localhost:8004/mcp"]
       }
     }
   }
   ```

2. **Example AI IDE Interactions**

   Once configured, you can interact with the MCP servers using natural language in your AI IDE:

   **Discovery Server Examples:**
   - "Discover all APIs from the native gateway"
   - "Search for payment-related APIs"
   - "Show me the API inventory with health scores below 70"
   - "Get details about the user authentication API"

   **Metrics Server Examples:**
   - "Collect current metrics for all APIs"
   - "Show me the response time trends for the payment API over the last 24 hours"
   - "Analyze error rate patterns for high-traffic APIs"
   - "What APIs have the highest latency?"

   **Optimization Server Examples:**
   - "Generate failure predictions for the next 48 hours"
   - "What optimization recommendations do you have for the checkout API?"
   - "Create a rate limiting policy for the authentication API"
   - "Analyze the effectiveness of current rate limits"

3. **Verify MCP Server Health**
   ```bash
   # Check if MCP servers are running
   curl http://localhost:8001/health
   curl http://localhost:8002/health
   curl http://localhost:8004/health
   ```

4. **MCP Server Capabilities**

   - **Discovery Server** (`localhost:8001`):
     - Discover APIs from connected gateways
     - Search API inventory with natural language
     - Get API details and specifications
     - Retrieve complete API inventory with filtering

   - **Metrics Server** (`localhost:8002`):
     - Collect real-time metrics from gateways
     - Retrieve time-series metrics for analysis
     - Analyze trends and patterns
     - Generate metric-based insights

   - **Optimization Server** (`localhost:8004`):
     - Generate failure predictions
     - Create optimization recommendations
     - Manage rate limiting policies
     - Analyze policy effectiveness

## Advanced Scenarios

### Scenario 1: End-to-End API Lifecycle

```bash
# 1. Discover new APIs
curl -X POST http://localhost:8000/api/v1/gateways/native-gateway-1/discover

# 2. Query for specific APIs
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show newly discovered APIs"}'

# 3. Generate predictions for new APIs
curl -X POST http://localhost:8000/api/v1/predictions/generate

# 4. Get optimization recommendations
curl -X POST "http://localhost:8000/api/v1/optimization/recommendations?api_id={api_id}"

# 5. Apply rate limiting
curl -X POST http://localhost:8000/api/v1/rate-limits \
  -H "Content-Type: application/json" \
  -d '{
    "api_id": "{api_id}",
    "policy_type": "fixed_window",
    "limit_thresholds": {"requests_per_minute": 100}
  }'
```

### Scenario 2: Shadow API Detection

```bash
# 1. Query for shadow APIs
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Find all shadow APIs"}'

# 2. Get details of shadow APIs
curl "http://localhost:8000/api/v1/apis?is_shadow=true"

# 3. Analyze security risks
curl http://localhost:8000/api/v1/apis/{shadow_api_id}

# 4. Generate security recommendations
curl -X POST "http://localhost:8000/api/v1/optimization/recommendations?api_id={shadow_api_id}"
```

### Scenario 3: Performance Troubleshooting

```bash
# 1. Find slow APIs
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Which APIs have response time over 500ms?"}'

# 2. Get detailed metrics via backend API
curl http://localhost:8000/api/v1/apis/{api_id}

# 3. Use MCP Metrics Server (via AI IDE)
# Ask: "Show me the response time trends for API {api_id} over the last 24 hours"

# 4. Get optimization recommendations
curl -X POST "http://localhost:8000/api/v1/optimization/recommendations?api_id={api_id}"
```

## Monitoring and Logs

### View Service Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f demo-gateway
docker-compose logs -f mcp-discovery

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Check Service Status

```bash
# List all containers
docker-compose ps

# Check resource usage
docker stats

# Inspect specific service
docker-compose exec backend ps aux
```

## Troubleshooting

### Services Not Starting

```bash
# Check logs for errors
docker-compose logs

# Restart specific service
docker-compose restart backend

# Rebuild and restart
docker-compose up -d --build backend
```

### Port Conflicts

```bash
# Check if ports are in use
lsof -i :8000  # Backend
lsof -i :3000  # Frontend
lsof -i :9200  # OpenSearch

# Stop conflicting services or change ports in docker-compose.yml
```

### OpenSearch Issues

```bash
# Check OpenSearch health
curl http://localhost:9200/_cluster/health

# View indices
curl http://localhost:9200/_cat/indices?v

# Delete and recreate indices
docker-compose exec backend python scripts/init_opensearch.py
```

### Reset Everything

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes all data)
docker-compose down -v

# Rebuild and restart
docker-compose up -d --build

# Regenerate mock data
docker-compose exec backend python scripts/init_opensearch.py
docker-compose exec backend python scripts/generate_mock_data.py
```

## Cleanup

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Stop and remove images
docker-compose down --rmi all
```

### Remove Generated Data

```bash
# Clear OpenSearch data
curl -X DELETE http://localhost:9200/apis
curl -X DELETE http://localhost:9200/gateways
curl -X DELETE http://localhost:9200/metrics
curl -X DELETE http://localhost:9200/predictions
curl -X DELETE http://localhost:9200/recommendations
```

## Next Steps

1. **Explore the Frontend**: Navigate through all pages to see visualizations
2. **Try Custom Queries**: Experiment with different natural language queries
3. **Configure AI IDE**: Set up Bob or Claude Desktop with MCP servers for enhanced interactions
4. **Review Documentation**: Check `docs/` folder for detailed guides
5. **Integrate with Your Gateway**: Configure connection to your actual API gateway
6. **Customize Workflows**: Modify scripts to match your use cases

## Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Review documentation in `docs/` folder
3. Open an issue on GitHub
4. Contact the development team

---

**Demo Complete!** You've successfully set up and explored the API Intelligence Plane application.