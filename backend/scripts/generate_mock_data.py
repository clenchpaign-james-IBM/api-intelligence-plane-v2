"""Generate mock data for API Intelligence Plane.

This script generates realistic mock data for:
- Gateways
- APIs  
- Metrics

Useful for integration tests and manual testing.
"""

import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_opensearch_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDataGenerator:
    """Generate mock data for testing."""

    def __init__(self):
        """Initialize mock data generator."""
        self.os_client = get_opensearch_client()
        self.gateway_ids = []
        self.api_ids = []

    def generate_all(self, num_gateways: int = 3, num_apis_per_gateway: int = 5):
        """Generate all mock data.
        
        Args:
            num_gateways: Number of gateways to create
            num_apis_per_gateway: Number of APIs per gateway
        """
        logger.info("Starting mock data generation...")
        
        # Generate gateways
        self.generate_gateways(num_gateways)
        
        # Generate APIs
        self.generate_apis(num_apis_per_gateway)
        
        # Generate metrics
        self.generate_metrics()
        
        logger.info("Mock data generation complete!")
        logger.info(f"Created {len(self.gateway_ids)} gateways")
        logger.info(f"Created {len(self.api_ids)} APIs")

    def generate_gateways(self, count: int = 3):
        """Generate mock gateways.
        
        Args:
            count: Number of gateways to create
        """
        logger.info(f"Generating {count} mock gateways...")
        
        vendors = ["kong", "apigee", "native"]
        environments = ["production", "staging", "development"]
        
        for i in range(count):
            gateway_id = str(uuid4())
            vendor = vendors[i % len(vendors)]
            env = environments[i % len(environments)]
            
            gateway = {
                "id": gateway_id,
                "name": f"{vendor.title()} Gateway - {env.title()}",
                "vendor": vendor,
                "connection_url": f"https://{vendor}-{env}.example.com",
                "connection_type": "rest_api",
                "credentials": {
                    "type": "api_key",
                    "api_key": f"mock_key_{gateway_id[:8]}"
                },
                "status": "connected",
                "version": f"{random.randint(1, 3)}.{random.randint(0, 9)}.{random.randint(0, 20)}",
                "capabilities": ["discovery", "metrics", "policies"],
                "configuration": {"timeout": 30, "retry": 3},
                "metadata": {"environment": env, "region": "us-west-2"},
                "created_at": (datetime.utcnow() - timedelta(days=random.randint(30, 365))).isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "last_connected_at": datetime.utcnow().isoformat(),
            }
            
            # Store in OpenSearch
            try:
                self.os_client.client.index(
                    index="gateway-registry",
                    id=gateway_id,
                    body=gateway,
                )
                self.gateway_ids.append(gateway_id)
                logger.info(f"Created gateway: {gateway['name']}")
            except Exception as e:
                logger.error(f"Failed to create gateway: {e}")

    def generate_apis(self, per_gateway: int = 5):
        """Generate mock APIs.
        
        Args:
            per_gateway: Number of APIs per gateway
        """
        logger.info(f"Generating {per_gateway} APIs per gateway...")
        
        api_names = [
            "User Service", "Payment Service", "Order Service",
            "Inventory Service", "Notification Service", "Analytics Service",
            "Auth Service", "Product Service", "Shipping Service", "Review Service"
        ]
        
        auth_types = ["oauth2", "api_key", "bearer"]
        statuses = ["active", "active", "active", "deprecated"]
        
        for gateway_id in self.gateway_ids:
            for i in range(per_gateway):
                api_id = str(uuid4())
                name = api_names[i % len(api_names)]
                
                # Create at least one endpoint
                base_path = f"/api/v1/{name.lower().replace(' ', '-')}"
                endpoints = [
                    {
                        "path": f"{base_path}/{{id}}",
                        "method": "GET",
                        "description": f"Get {name} by ID",
                        "parameters": [
                            {
                                "name": "id",
                                "type": "path",
                                "data_type": "string",
                                "required": True,
                                "description": "Resource ID"
                            }
                        ],
                        "response_codes": [200, 404]
                    }
                ]
                
                # Generate proper current_metrics
                p50 = round(random.uniform(50, 200), 2)
                p95 = round(p50 * random.uniform(1.5, 2.5), 2)
                p99 = round(p95 * random.uniform(1.2, 1.8), 2)
                
                # Generate realistic security policies
                is_production = "production" in gateway_id or random.random() < 0.6
                has_sensitive_data = name in ["Payment Service", "User Service", "Auth Service"]
                
                compliance_standards = []
                if has_sensitive_data:
                    compliance_standards = random.sample(
                        ["PCI-DSS", "HIPAA", "SOC2", "GDPR", "ISO27001"],
                        k=random.randint(1, 3)
                    )
                
                security_policies = {
                    "authentication_required": random.choice(auth_types) != "none",
                    "authorization_enabled": is_production or random.random() < 0.7,
                    "rate_limiting_enabled": is_production or random.random() < 0.5,
                    "rate_limit_config": {
                        "requests_per_minute": random.choice([100, 500, 1000, 5000]),
                        "burst_size": random.choice([10, 50, 100])
                    } if is_production or random.random() < 0.5 else None,
                    "tls_enforced": is_production or random.random() < 0.8,
                    "tls_version": random.choice(["TLS 1.2", "TLS 1.3"]) if is_production else "TLS 1.2",
                    "cors_enabled": random.random() < 0.6,
                    "cors_config": {
                        "allowed_origins": ["https://app.example.com", "https://admin.example.com"],
                        "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
                        "allow_credentials": True
                    } if random.random() < 0.6 else None,
                    "input_validation_enabled": is_production or random.random() < 0.7,
                    "output_sanitization_enabled": has_sensitive_data or random.random() < 0.6,
                    "logging_enabled": True,
                    "encryption_at_rest": has_sensitive_data or random.random() < 0.5,
                    "waf_enabled": is_production and (has_sensitive_data or random.random() < 0.4),
                    "ip_whitelisting_enabled": random.random() < 0.2,
                    "allowed_ips": ["10.0.0.0/8", "172.16.0.0/12"] if random.random() < 0.2 else None,
                    "api_key_rotation_enabled": has_sensitive_data or random.random() < 0.3,
                    "key_rotation_days": random.choice([30, 60, 90]) if has_sensitive_data or random.random() < 0.3 else None,
                    "compliance_standards": compliance_standards if compliance_standards else None,
                    "last_policy_update": (datetime.utcnow() - timedelta(days=random.randint(1, 30))).isoformat()
                }
                
                api = {
                    "id": api_id,
                    "gateway_id": gateway_id,
                    "name": name,
                    "base_path": base_path,
                    "version": f"v{random.randint(1, 3)}",
                    "status": random.choice(statuses),
                    "methods": ["GET", "POST", "PUT", "DELETE"],
                    "authentication_type": random.choice(auth_types),
                    "authentication_config": {"required": True},
                    "discovery_method": "registered",  # Use valid enum value
                    "is_shadow": random.random() < 0.1,  # 10% shadow APIs
                    "health_score": round(random.uniform(0.7, 1.0), 2),
                    "endpoints": endpoints,
                    "tags": [name.split()[0].lower(), "service", "api"],
                    "ownership": {"team": "platform", "contact": "platform@example.com"},
                    "current_metrics": {
                        "response_time_p50": p50,
                        "response_time_p95": p95,
                        "response_time_p99": p99,
                        "error_rate": round(random.uniform(0, 0.05), 4),  # 0-5% as 0-0.05
                        "throughput": round(random.uniform(10, 1000), 2),
                        "availability": round(random.uniform(95, 100), 2),
                        "measured_at": datetime.utcnow().isoformat()
                    },
                    "security_policies": security_policies,
                    "metadata": {"criticality": "high", "sla": "99.9%"},
                    "discovered_at": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
                    "last_seen_at": datetime.utcnow().isoformat(),
                    "created_at": (datetime.utcnow() - timedelta(days=random.randint(1, 90))).isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                }
                
                # Store in OpenSearch
                try:
                    self.os_client.client.index(
                        index="api-inventory",
                        id=api_id,
                        body=api,
                    )
                    self.api_ids.append(api_id)
                    logger.info(f"Created API: {api['name']} (Gateway: {gateway_id[:8]}...)")
                except Exception as e:
                    logger.error(f"Failed to create API: {e}")

    def generate_metrics(self):
        """Generate mock metrics for APIs."""
        logger.info("Generating mock metrics...")
        
        # Generate metrics for the last 7 days
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        current_time = start_time
        metric_count = 0
        
        while current_time <= end_time:
            for api_id in self.api_ids:
                gateway_id = self.gateway_ids[self.api_ids.index(api_id) % len(self.gateway_ids)]
                
                # Generate metrics every 5 minutes
                metric = {
                    "id": str(uuid4()),
                    "api_id": api_id,
                    "gateway_id": gateway_id,
                    "timestamp": current_time.isoformat(),
                    "request_count": random.randint(100, 10000),
                    "error_count": random.randint(0, 100),
                    "response_time_p50": round(random.uniform(50, 500), 2),
                    "response_time_p95": round(random.uniform(200, 2000), 2),
                    "response_time_p99": round(random.uniform(500, 5000), 2),
                    "error_rate": round(random.uniform(0, 5), 2),
                    "availability": round(random.uniform(95, 100), 2),
                    "throughput": round(random.uniform(10, 1000), 2),
                    "status_codes": {
                        "200": random.randint(8000, 9500),
                        "400": random.randint(0, 100),
                        "500": random.randint(0, 50),
                    },
                    "endpoint_metrics": [],
                    "metadata": {"source": "mock_generator"},
                }
                
                # Store in OpenSearch with monthly index
                index_name = f"api-metrics-{current_time.strftime('%Y.%m')}"
                try:
                    self.os_client.client.index(
                        index=index_name,
                        body=metric,
                    )
                    metric_count += 1
                except Exception as e:
                    logger.error(f"Failed to create metric: {e}")
            
            current_time += timedelta(minutes=5)
        
        logger.info(f"Created {metric_count} metric data points")

    def cleanup(self):
        """Clean up all mock data."""
        logger.info("Cleaning up mock data...")
        
        # Delete all documents from indices
        indices = ["gateway-registry", "api-inventory", "api-metrics-*"]
        
        for index in indices:
            try:
                self.os_client.client.delete_by_query(
                    index=index,
                    body={"query": {"match_all": {}}},
                )
                logger.info(f"Cleaned up index: {index}")
            except Exception as e:
                logger.warning(f"Failed to clean up {index}: {e}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate mock data for API Intelligence Plane")
    parser.add_argument("--gateways", type=int, default=3, help="Number of gateways to create")
    parser.add_argument("--apis-per-gateway", type=int, default=5, help="Number of APIs per gateway")
    parser.add_argument("--cleanup", action="store_true", help="Clean up existing mock data")
    
    args = parser.parse_args()
    
    generator = MockDataGenerator()
    
    if args.cleanup:
        generator.cleanup()
    else:
        generator.generate_all(
            num_gateways=args.gateways,
            num_apis_per_gateway=args.apis_per_gateway,
        )


if __name__ == "__main__":
    main()

# Made with Bob