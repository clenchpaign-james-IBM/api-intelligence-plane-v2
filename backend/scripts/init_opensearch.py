#!/usr/bin/env python3
"""
OpenSearch Initialization Script

This script initializes the OpenSearch cluster with all required indices,
index templates, and settings for the API Intelligence Plane.

Usage:
    python scripts/init_opensearch.py [--host HOST] [--port PORT] [--user USER] [--password PASSWORD]
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from opensearchpy import OpenSearch, exceptions
from app.db.migrations import (
    create_api_inventory_index,
    create_gateway_registry_index,
    create_api_metrics_index_template,
    create_predictions_index,
    create_security_findings_index,
    create_optimization_recommendations_index,
    create_rate_limit_policies_index,
    create_query_history_index,
    create_compliance_violations_index,
    create_transactional_logs_index_template,
    create_wm_metrics_1m_index_template,
    create_wm_metrics_5m_index_template,
    create_wm_metrics_1h_index_template,
    create_wm_metrics_1d_index_template,
)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Initialize OpenSearch cluster for API Intelligence Plane"
    )
    parser.add_argument(
        "--host",
        default="localhost",
        help="OpenSearch host (default: localhost)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=9200,
        help="OpenSearch port (default: 9200)",
    )
    parser.add_argument(
        "--user",
        default="admin",
        help="OpenSearch username (default: admin)",
    )
    parser.add_argument(
        "--password",
        default="admin",
        help="OpenSearch password (default: admin)",
    )
    parser.add_argument(
        "--use-ssl",
        action="store_true",
        help="Use SSL/TLS connection",
    )
    parser.add_argument(
        "--verify-certs",
        action="store_true",
        help="Verify SSL certificates",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of existing indices (WARNING: deletes data)",
    )
    return parser.parse_args()


def create_opensearch_client(args):
    """Create OpenSearch client with provided configuration."""
    return OpenSearch(
        hosts=[{"host": args.host, "port": args.port}],
        http_auth=(args.user, args.password),
        use_ssl=args.use_ssl,
        verify_certs=args.verify_certs,
        ssl_show_warn=False,
    )


def check_cluster_health(client: OpenSearch) -> bool:
    """Check if OpenSearch cluster is healthy."""
    try:
        health = client.cluster.health()
        status = health["status"]
        print(f"✓ Cluster health: {status}")
        return status in ["green", "yellow"]
    except Exception as e:
        print(f"✗ Failed to check cluster health: {e}")
        return False


def delete_index_if_exists(client: OpenSearch, index_name: str, force: bool):
    """Delete index if it exists and force flag is set."""
    if client.indices.exists(index=index_name):
        if force:
            print(f"  Deleting existing index: {index_name}")
            client.indices.delete(index=index_name)
        else:
            print(f"  Index already exists: {index_name} (use --force to recreate)")
            return False
    return True


def initialize_indices(client: OpenSearch, force: bool = False):
    """Initialize all required indices and templates."""
    migrations = [
        ("api-inventory", "API Inventory", create_api_inventory_index),
        ("gateway-registry", "Gateway Registry", create_gateway_registry_index),
        ("api-metrics-*", "API Metrics Template", create_api_metrics_index_template),
        ("api-predictions", "Predictions", create_predictions_index),
        ("security-findings", "Security Findings", create_security_findings_index),
        (
            "optimization-recommendations",
            "Optimization Recommendations",
            create_optimization_recommendations_index,
        ),
        ("rate-limit-policies", "Rate Limit Policies", create_rate_limit_policies_index),
        ("query-history", "Query History", create_query_history_index),
        ("compliance-violations", "Compliance Violations", create_compliance_violations_index),
        (
            "transactional-logs-*",
            "Transactional Logs Template",
            create_transactional_logs_index_template,
        ),
        ("api-metrics-1m-*", "API Metrics 1m Template", create_wm_metrics_1m_index_template),
        ("api-metrics-5m-*", "API Metrics 5m Template", create_wm_metrics_5m_index_template),
        ("api-metrics-1h-*", "API Metrics 1h Template", create_wm_metrics_1h_index_template),
        ("api-metrics-1d-*", "API Metrics 1d Template", create_wm_metrics_1d_index_template),
    ]

    print("\nInitializing indices and templates...")
    success_count = 0
    skip_count = 0
    error_count = 0

    for index_name, display_name, migration_func in migrations:
        try:
            print(f"\n{display_name} ({index_name}):")
            
            # For index templates, check differently
            if "*" in index_name:
                template_name = index_name.replace("*", "template")
                if client.indices.exists_template(name=template_name):
                    if force:
                        print(f"  Deleting existing template: {template_name}")
                        client.indices.delete_template(name=template_name)
                    else:
                        print(f"  Template already exists (use --force to recreate)")
                        skip_count += 1
                        continue
            else:
                if not delete_index_if_exists(client, index_name, force):
                    skip_count += 1
                    continue

            # Execute migration
            migration_func(client)
            print(f"  ✓ Created successfully")
            success_count += 1

        except exceptions.RequestError as e:
            print(f"  ✗ Request error: {e.error}")
            error_count += 1
        except Exception as e:
            print(f"  ✗ Unexpected error: {e}")
            error_count += 1

    print(f"\n{'='*60}")
    print(f"Initialization complete:")
    print(f"  ✓ Created: {success_count}")
    print(f"  ⊘ Skipped: {skip_count}")
    print(f"  ✗ Errors: {error_count}")
    print(f"{'='*60}\n")

    return error_count == 0


def verify_indices(client: OpenSearch):
    """Verify that all indices were created successfully."""
    print("Verifying indices...")
    
    expected_indices = [
        "api-inventory",
        "gateway-registry",
        "api-predictions",
        "security-findings",
        "optimization-recommendations",
        "rate-limit-policies",
        "query-history",
        "compliance-violations",
    ]
    
    all_exist = True
    for index_name in expected_indices:
        exists = client.indices.exists(index=index_name)
        status = "✓" if exists else "✗"
        print(f"  {status} {index_name}")
        if not exists:
            all_exist = False
    
    # Check templates
    expected_templates = [
        "api-metrics-template",
        "transactional-logs-template",
        "api-metrics-1m-template",
        "api-metrics-5m-template",
        "api-metrics-1h-template",
        "api-metrics-1d-template",
    ]

    for template_name in expected_templates:
        template_exists = client.indices.exists_template(name=template_name)
        status = "✓" if template_exists else "✗"
        print(f"  {status} {template_name}")
        if not template_exists:
            all_exist = False

    return all_exist


def main():
    """Main execution function."""
    args = parse_args()
    
    print("="*60)
    print("API Intelligence Plane - OpenSearch Initialization")
    print("="*60)
    print(f"\nConnecting to OpenSearch at {args.host}:{args.port}...")
    
    try:
        # Create client
        client = create_opensearch_client(args)
        
        # Check cluster health
        if not check_cluster_health(client):
            print("\n✗ Cluster is not healthy. Aborting initialization.")
            return 1
        
        # Initialize indices
        if not initialize_indices(client, args.force):
            print("\n⚠ Some indices failed to initialize.")
            return 1
        
        # Verify indices
        if not verify_indices(client):
            print("\n✗ Some indices are missing after initialization.")
            return 1
        
        print("\n✓ OpenSearch initialization completed successfully!")
        return 0
        
    except exceptions.ConnectionError as e:
        print(f"\n✗ Failed to connect to OpenSearch: {e}")
        print("  Make sure OpenSearch is running and accessible.")
        return 1
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
