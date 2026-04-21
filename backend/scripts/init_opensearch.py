#!/usr/bin/env python3
"""
OpenSearch Initialization Script

CLI tool for initializing OpenSearch cluster with all required indices,
index templates, and ILM policies for the API Intelligence Plane.

This script is a thin wrapper around the unified initialization module
(app.db.init_indices) and provides CLI-specific features like:
- Custom connection parameters
- Force recreation of indices
- Verbose output and verification
- Exit codes for CI/CD integration

Usage:
    python scripts/init_opensearch.py [OPTIONS]
    
Examples:
    # Initialize with defaults
    python scripts/init_opensearch.py
    
    # Force recreation of all indices (DESTRUCTIVE!)
    python scripts/init_opensearch.py --force
    
    # Connect to remote cluster
    python scripts/init_opensearch.py --host prod.example.com --port 9200
    
    # Skip ILM policies
    python scripts/init_opensearch.py --no-ilm
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from opensearchpy import OpenSearch, exceptions
from app.db.init_indices import initialize_all_infrastructure, verify_infrastructure


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Initialize OpenSearch cluster for API Intelligence Plane",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Initialize with defaults
  %(prog)s --force                            # Force recreation (DESTRUCTIVE!)
  %(prog)s --host prod.example.com           # Connect to remote cluster
  %(prog)s --no-ilm                          # Skip ILM policies
  %(prog)s --verify-only                     # Only verify, don't create
        """
    )
    
    # Connection options
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
    
    # Initialization options
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of existing indices (WARNING: deletes data!)",
    )
    parser.add_argument(
        "--no-ilm",
        action="store_true",
        help="Skip ILM policy creation",
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify infrastructure, don't create anything",
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


def main():
    """Main execution function."""
    args = parse_args()
    
    print("=" * 80)
    print("API Intelligence Plane - OpenSearch Initialization")
    print("=" * 80)
    print(f"\nConnecting to OpenSearch at {args.host}:{args.port}...")
    
    try:
        # Create client
        client = create_opensearch_client(args)
        
        # Check cluster health
        if not check_cluster_health(client):
            print("\n✗ Cluster is not healthy. Aborting initialization.")
            return 1
        
        # Verify-only mode
        if args.verify_only:
            print("\nVerifying infrastructure (no changes will be made)...")
            results = verify_infrastructure(client)
            
            all_exist = all(results.values())
            if all_exist:
                print("\n✓ All infrastructure components exist")
                return 0
            else:
                missing = [name for name, exists in results.items() if not exists]
                print(f"\n✗ Missing components: {', '.join(missing)}")
                return 1
        
        # Initialize infrastructure
        print("\nInitializing infrastructure...")
        if args.force:
            print("⚠️  WARNING: Force mode enabled - existing indices will be deleted!")
            response = input("Continue? (yes/no): ")
            if response.lower() != "yes":
                print("Aborted.")
                return 0
        
        indices_results, ilm_results = initialize_all_infrastructure(
            client,
            force=args.force,
            include_ilm=not args.no_ilm,
            raise_on_error=False
        )
        
        # Check results
        indices_success = sum(indices_results.values())
        indices_total = len(indices_results)
        
        print(f"\n{'=' * 80}")
        print(f"Indices/Templates: {indices_success}/{indices_total} successful")
        
        if ilm_results:
            ilm_success = sum(ilm_results.values())
            ilm_total = len(ilm_results)
            print(f"ILM Policies: {ilm_success}/{ilm_total} successful")
        
        # Verify
        print(f"\nVerifying infrastructure...")
        verify_results = verify_infrastructure(client)
        all_verified = all(verify_results.values())
        
        print(f"{'=' * 80}\n")
        
        if all_verified and indices_success == indices_total:
            print("✓ OpenSearch initialization completed successfully!")
            return 0
        else:
            print("⚠️  Some components failed to initialize. Check logs above.")
            return 1
        
    except exceptions.ConnectionError as e:
        print(f"\n✗ Failed to connect to OpenSearch: {e}")
        print("  Make sure OpenSearch is running and accessible.")
        return 1
    except KeyboardInterrupt:
        print("\n\nAborted by user.")
        return 130
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
