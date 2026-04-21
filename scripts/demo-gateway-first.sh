#!/bin/bash

# API Intelligence Plane - Gateway-First Architecture Demo Script
# Version: 2.0.0
# Last Updated: 2026-04-14
# 
# This script demonstrates the gateway-first architecture by:
# 1. Registering multiple gateways
# 2. Discovering APIs scoped to each gateway
# 3. Generating gateway-scoped metrics
# 4. Showing proper data isolation between gateways

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
API_VERSION="v1"
BASE_URL="${BACKEND_URL}/api/${API_VERSION}"

# Helper functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

check_backend() {
    print_header "Checking Backend Availability"
    
    if curl -s -f "${BACKEND_URL}/health" > /dev/null 2>&1; then
        print_success "Backend is available at ${BACKEND_URL}"
    else
        print_error "Backend is not available at ${BACKEND_URL}"
        print_info "Please ensure the backend is running: docker-compose up -d backend"
        exit 1
    fi
}

# Step 1: Register Gateways
register_gateways() {
    print_header "Step 1: Registering Multiple Gateways"
    print_info "Gateway-first architecture requires gateway registration before API discovery"
    
    # Register Production Gateway
    print_info "Registering Production webMethods Gateway..."
    PROD_GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/gateways" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Production webMethods Gateway",
            "vendor": "webmethods",
            "base_url": "http://prod-gateway:5555",
            "credentials": {
                "type": "basic",
                "username": "admin",
                "password": "manage"
            },
            "transactional_logs_url": "http://prod-opensearch:9200",
            "description": "Production environment gateway"
        }')
    
    PROD_GATEWAY_ID=$(echo $PROD_GATEWAY_RESPONSE | jq -r '.id')
    print_success "Registered Production Gateway: ${PROD_GATEWAY_ID}"
    
    # Register Staging Gateway
    print_info "Registering Staging webMethods Gateway..."
    STAGING_GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/gateways" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Staging webMethods Gateway",
            "vendor": "webmethods",
            "base_url": "http://staging-gateway:5555",
            "credentials": {
                "type": "basic",
                "username": "admin",
                "password": "manage"
            },
            "transactional_logs_url": "http://staging-opensearch:9200",
            "description": "Staging environment gateway"
        }')
    
    STAGING_GATEWAY_ID=$(echo $STAGING_GATEWAY_RESPONSE | jq -r '.id')
    print_success "Registered Staging Gateway: ${STAGING_GATEWAY_ID}"
    
    # Register Development Gateway
    print_info "Registering Development webMethods Gateway..."
    DEV_GATEWAY_RESPONSE=$(curl -s -X POST "${BASE_URL}/gateways" \
        -H "Content-Type: application/json" \
        -d '{
            "name": "Development webMethods Gateway",
            "vendor": "webmethods",
            "base_url": "http://dev-gateway:5555",
            "credentials": {
                "type": "basic",
                "username": "admin",
                "password": "manage"
            },
            "transactional_logs_url": "http://dev-opensearch:9200",
            "description": "Development environment gateway"
        }')
    
    DEV_GATEWAY_ID=$(echo $DEV_GATEWAY_RESPONSE | jq -r '.id')
    print_success "Registered Development Gateway: ${DEV_GATEWAY_ID}"
    
    echo ""
    print_info "Gateway Registration Summary:"
    echo "  Production:  ${PROD_GATEWAY_ID}"
    echo "  Staging:     ${STAGING_GATEWAY_ID}"
    echo "  Development: ${DEV_GATEWAY_ID}"
}

# Step 2: Discover APIs per Gateway
discover_apis() {
    print_header "Step 2: Discovering APIs (Gateway-Scoped)"
    print_info "Each gateway discovers its own APIs independently"
    
    # Discover APIs for Production Gateway
    print_info "Discovering APIs for Production Gateway..."
    curl -s -X POST "${BASE_URL}/discovery/discover?gateway_id=${PROD_GATEWAY_ID}" > /dev/null
    print_success "Discovery initiated for Production Gateway"
    
    # Discover APIs for Staging Gateway
    print_info "Discovering APIs for Staging Gateway..."
    curl -s -X POST "${BASE_URL}/discovery/discover?gateway_id=${STAGING_GATEWAY_ID}" > /dev/null
    print_success "Discovery initiated for Staging Gateway"
    
    # Discover APIs for Development Gateway
    print_info "Discovering APIs for Development Gateway..."
    curl -s -X POST "${BASE_URL}/discovery/discover?gateway_id=${DEV_GATEWAY_ID}" > /dev/null
    print_success "Discovery initiated for Development Gateway"
    
    print_info "Waiting for discovery to complete..."
    sleep 5
}

# Step 3: Query APIs by Gateway
query_apis_by_gateway() {
    print_header "Step 3: Querying APIs (Gateway-Scoped)"
    print_info "Demonstrating gateway-first data isolation"
    
    # Query Production APIs
    print_info "Querying APIs for Production Gateway..."
    PROD_APIS=$(curl -s "${BASE_URL}/apis?gateway_id=${PROD_GATEWAY_ID}")
    PROD_API_COUNT=$(echo $PROD_APIS | jq '. | length')
    print_success "Found ${PROD_API_COUNT} APIs in Production Gateway"
    
    # Query Staging APIs
    print_info "Querying APIs for Staging Gateway..."
    STAGING_APIS=$(curl -s "${BASE_URL}/apis?gateway_id=${STAGING_GATEWAY_ID}")
    STAGING_API_COUNT=$(echo $STAGING_APIS | jq '. | length')
    print_success "Found ${STAGING_API_COUNT} APIs in Staging Gateway"
    
    # Query Development APIs
    print_info "Querying APIs for Development Gateway..."
    DEV_APIS=$(curl -s "${BASE_URL}/apis?gateway_id=${DEV_GATEWAY_ID}")
    DEV_API_COUNT=$(echo $DEV_APIS | jq '. | length')
    print_success "Found ${DEV_API_COUNT} APIs in Development Gateway"
    
    echo ""
    print_info "API Count Summary (Gateway-Scoped):"
    echo "  Production:  ${PROD_API_COUNT} APIs"
    echo "  Staging:     ${STAGING_API_COUNT} APIs"
    echo "  Development: ${DEV_API_COUNT} APIs"
    echo "  Total:       $((PROD_API_COUNT + STAGING_API_COUNT + DEV_API_COUNT)) APIs across all gateways"
}

# Step 4: Generate Gateway-Scoped Metrics
generate_metrics() {
    print_header "Step 4: Generating Gateway-Scoped Metrics"
    print_info "Metrics are always scoped to their parent gateway"
    
    # Generate metrics for Production Gateway
    print_info "Generating metrics for Production Gateway..."
    docker-compose exec -T backend python scripts/generate_traffic.py \
        --gateway-id "${PROD_GATEWAY_ID}" \
        --duration 60 \
        --requests-per-second 100 > /dev/null 2>&1 &
    print_success "Metrics generation started for Production Gateway"
    
    # Generate metrics for Staging Gateway
    print_info "Generating metrics for Staging Gateway..."
    docker-compose exec -T backend python scripts/generate_traffic.py \
        --gateway-id "${STAGING_GATEWAY_ID}" \
        --duration 60 \
        --requests-per-second 50 > /dev/null 2>&1 &
    print_success "Metrics generation started for Staging Gateway"
    
    print_info "Waiting for metrics to be generated..."
    sleep 10
}

# Step 5: Query Metrics by Gateway
query_metrics_by_gateway() {
    print_header "Step 5: Querying Metrics (Gateway-Scoped)"
    print_info "Demonstrating proper metric isolation between gateways"
    
    # Query Production Metrics
    print_info "Querying metrics for Production Gateway..."
    PROD_METRICS=$(curl -s "${BASE_URL}/metrics?gateway_id=${PROD_GATEWAY_ID}&time_range=1h")
    PROD_METRIC_COUNT=$(echo $PROD_METRICS | jq '. | length')
    print_success "Found ${PROD_METRIC_COUNT} metric records for Production Gateway"
    
    # Query Staging Metrics
    print_info "Querying metrics for Staging Gateway..."
    STAGING_METRICS=$(curl -s "${BASE_URL}/metrics?gateway_id=${STAGING_GATEWAY_ID}&time_range=1h")
    STAGING_METRIC_COUNT=$(echo $STAGING_METRICS | jq '. | length')
    print_success "Found ${STAGING_METRIC_COUNT} metric records for Staging Gateway"
    
    echo ""
    print_info "Metrics Summary (Gateway-Scoped):"
    echo "  Production:  ${PROD_METRIC_COUNT} records"
    echo "  Staging:     ${STAGING_METRIC_COUNT} records"
}

# Step 6: Demonstrate Cross-Gateway Query
demonstrate_cross_gateway() {
    print_header "Step 6: Cross-Gateway Comparison (Explicit)"
    print_info "Cross-gateway views require explicit gateway selection"
    
    print_info "Comparing metrics across Production and Staging..."
    CROSS_GATEWAY_METRICS=$(curl -s "${BASE_URL}/metrics/cross-gateway?gateway_ids=${PROD_GATEWAY_ID}&gateway_ids=${STAGING_GATEWAY_ID}&time_range=1h")
    
    PROD_TOTAL=$(echo $CROSS_GATEWAY_METRICS | jq -r ".\"${PROD_GATEWAY_ID}\" | length")
    STAGING_TOTAL=$(echo $CROSS_GATEWAY_METRICS | jq -r ".\"${STAGING_GATEWAY_ID}\" | length")
    
    print_success "Cross-gateway comparison complete"
    echo ""
    print_info "Cross-Gateway Comparison:"
    echo "  Production:  ${PROD_TOTAL} records"
    echo "  Staging:     ${STAGING_TOTAL} records"
}

# Step 7: Demonstrate Gateway-Scoped Predictions
demonstrate_predictions() {
    print_header "Step 7: Gateway-Scoped Predictions"
    print_info "Predictions are generated per gateway"
    
    # Generate predictions for Production Gateway
    print_info "Generating predictions for Production Gateway..."
    curl -s -X POST "${BASE_URL}/predictions/generate?gateway_id=${PROD_GATEWAY_ID}" > /dev/null
    print_success "Predictions generated for Production Gateway"
    
    # Query predictions
    print_info "Querying predictions for Production Gateway..."
    PROD_PREDICTIONS=$(curl -s "${BASE_URL}/predictions?gateway_id=${PROD_GATEWAY_ID}")
    PROD_PRED_COUNT=$(echo $PROD_PREDICTIONS | jq '. | length')
    print_success "Found ${PROD_PRED_COUNT} predictions for Production Gateway"
}

# Step 8: Show Dashboard Stats
show_dashboard_stats() {
    print_header "Step 8: Dashboard Statistics (Gateway-Scoped)"
    print_info "Dashboard defaults to gateway-level aggregation"
    
    # Get Production Gateway stats
    print_info "Getting dashboard stats for Production Gateway..."
    PROD_STATS=$(curl -s "${BASE_URL}/dashboard/stats?gateway_id=${PROD_GATEWAY_ID}")
    
    PROD_API_COUNT=$(echo $PROD_STATS | jq -r '.total_apis')
    PROD_HEALTH=$(echo $PROD_STATS | jq -r '.healthy_apis')
    PROD_PREDICTIONS=$(echo $PROD_STATS | jq -r '.total_predictions')
    
    print_success "Production Gateway Dashboard:"
    echo "  Total APIs:        ${PROD_API_COUNT}"
    echo "  Healthy APIs:      ${PROD_HEALTH}"
    echo "  Total Predictions: ${PROD_PREDICTIONS}"
    
    # Get Staging Gateway stats
    print_info "Getting dashboard stats for Staging Gateway..."
    STAGING_STATS=$(curl -s "${BASE_URL}/dashboard/stats?gateway_id=${STAGING_GATEWAY_ID}")
    
    STAGING_API_COUNT=$(echo $STAGING_STATS | jq -r '.total_apis')
    STAGING_HEALTH=$(echo $STAGING_STATS | jq -r '.healthy_apis')
    STAGING_PREDICTIONS=$(echo $STAGING_STATS | jq -r '.total_predictions')
    
    print_success "Staging Gateway Dashboard:"
    echo "  Total APIs:        ${STAGING_API_COUNT}"
    echo "  Healthy APIs:      ${STAGING_HEALTH}"
    echo "  Total Predictions: ${STAGING_PREDICTIONS}"
}

# Main execution
main() {
    print_header "API Intelligence Plane - Gateway-First Architecture Demo"
    print_info "This demo showcases the gateway-first architecture"
    print_info "All operations are scoped to gateways as the primary dimension"
    
    check_backend
    register_gateways
    discover_apis
    query_apis_by_gateway
    generate_metrics
    query_metrics_by_gateway
    demonstrate_cross_gateway
    demonstrate_predictions
    show_dashboard_stats
    
    print_header "Demo Complete!"
    print_success "Gateway-first architecture demonstrated successfully"
    echo ""
    print_info "Key Takeaways:"
    echo "  1. Gateway is the primary scope dimension"
    echo "  2. APIs are always scoped to their parent gateway"
    echo "  3. Metrics, predictions, and analytics are gateway-scoped"
    echo "  4. Cross-gateway views require explicit gateway selection"
    echo "  5. Data isolation between gateways is properly maintained"
    echo ""
    print_info "Next Steps:"
    echo "  - View the dashboard at http://localhost:3000"
    echo "  - Select different gateways to see isolated data"
    echo "  - Try cross-gateway comparisons in the UI"
    echo "  - Read the Gateway-Scoped Development Guide"
}

# Run main function
main

# Made with Bob
