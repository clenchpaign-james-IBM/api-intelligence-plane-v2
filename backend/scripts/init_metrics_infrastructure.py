#!/usr/bin/env python3
"""
Initialize Metrics Infrastructure

CLI tool for setting up ILM policies and index templates for time-bucketed
metrics storage. This is now a convenience wrapper around init_opensearch.py
that focuses specifically on metrics infrastructure.

This script is useful when you only want to update metrics-related infrastructure
without touching other indices.

Usage:
    python scripts/init_metrics_infrastructure.py
    
Note:
    For complete infrastructure initialization, use init_opensearch.py instead.
    This script is maintained for backward compatibility and focused metrics setup.
"""

import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.client import get_client
from app.db.init_indices import initialize_ilm_policies
from app.db.index_templates import (
    create_all_index_templates,
    get_index_template_status
)
from app.models.base.metric import TimeBucket

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Initialize metrics infrastructure."""
    logger.info("=" * 80)
    logger.info("Initializing Metrics Infrastructure")
    logger.info("=" * 80)
    logger.info("\nNote: For complete infrastructure setup, use init_opensearch.py")
    logger.info("This script focuses on metrics-specific components only.\n")
    
    try:
        # Get OpenSearch client
        logger.info("1. Connecting to OpenSearch...")
        client = get_client()
        logger.info("✓ Connected to OpenSearch")
        
        # Create ILM policies using unified initialization
        logger.info("\n2. Creating ILM policies for time-bucketed metrics...")
        ilm_results = initialize_ilm_policies(client, raise_on_error=False)
        
        ilm_success = sum(ilm_results.values())
        ilm_total = len(ilm_results)
        logger.info(f"ILM policies: {ilm_success}/{ilm_total} successful")
        
        # Create index templates
        logger.info("\n3. Creating index templates for time-bucketed metrics...")
        template_results = create_all_index_templates(client)
        
        template_success = sum(template_results.values())
        template_total = len(template_results)
        logger.info(f"Index templates: {template_success}/{template_total} successful")
        
        # Verify setup
        logger.info("\n4. Verifying infrastructure setup...")
        all_success = True
        
        for bucket in TimeBucket:
            # Check index template
            template_status = get_index_template_status(client, bucket)
            if not template_status["exists"]:
                logger.error(f"  ✗ Index template missing for {bucket.value}")
                all_success = False
            else:
                logger.info(f"  ✓ Index template exists for {bucket.value}")
        
        # Summary
        logger.info("\n" + "=" * 80)
        if all_success:
            logger.info("✓ Metrics infrastructure initialized successfully!")
            logger.info("\nNext steps:")
            logger.info("  1. Start the backend service")
            logger.info("  2. Metrics will be automatically aggregated to all time buckets")
            logger.info("  3. ILM policies will manage data retention automatically")
            logger.info("\nFor complete infrastructure setup, run:")
            logger.info("  python scripts/init_opensearch.py")
        else:
            logger.error("✗ Some infrastructure components failed to initialize")
            logger.error("Please check the logs above for details")
            logger.error("\nTry running the complete initialization:")
            logger.error("  python scripts/init_opensearch.py --force")
            sys.exit(1)
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n✗ Failed to initialize metrics infrastructure: {e}", exc_info=True)
        logger.error("\nTry running the complete initialization:")
        logger.error("  python scripts/init_opensearch.py")
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
