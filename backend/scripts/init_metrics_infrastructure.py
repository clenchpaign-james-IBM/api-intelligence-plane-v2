"""
Initialize Metrics Infrastructure

Sets up ILM policies and index templates for time-bucketed metrics storage.
Run this script once during deployment or when updating infrastructure.

Usage:
    python -m backend.scripts.init_metrics_infrastructure
"""

import sys
import logging
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.db.client import get_opensearch_client
from app.db.ilm_policies import create_all_ilm_policies, get_ilm_policy_status
from app.db.index_templates import (
    create_all_index_templates,
    create_transactional_logs_template,
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
    
    try:
        # Get OpenSearch client
        logger.info("\n1. Connecting to OpenSearch...")
        client = get_opensearch_client()
        logger.info("✓ Connected to OpenSearch")
        
        # Create ILM policies
        logger.info("\n2. Creating ILM policies for time-bucketed metrics...")
        ilm_results = create_all_ilm_policies(client)
        
        for bucket, success in ilm_results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} ILM policy for {bucket.value} bucket")
        
        # Create index templates
        logger.info("\n3. Creating index templates for time-bucketed metrics...")
        template_results = create_all_index_templates(client)
        
        for bucket, success in template_results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} Index template for {bucket.value} bucket")
        
        # Create transactional logs template
        logger.info("\n4. Creating transactional logs index template...")
        logs_success = create_transactional_logs_template(client)
        status = "✓" if logs_success else "✗"
        logger.info(f"  {status} Transactional logs template")
        
        # Verify setup
        logger.info("\n5. Verifying infrastructure setup...")
        all_success = True
        
        for bucket in TimeBucket:
            # Check ILM policy
            ilm_status = get_ilm_policy_status(client, bucket)
            if not ilm_status["exists"]:
                logger.error(f"  ✗ ILM policy missing for {bucket.value}")
                all_success = False
            
            # Check index template
            template_status = get_index_template_status(client, bucket)
            if not template_status["exists"]:
                logger.error(f"  ✗ Index template missing for {bucket.value}")
                all_success = False
        
        if all_success:
            logger.info("  ✓ All infrastructure components verified")
        
        # Summary
        logger.info("\n" + "=" * 80)
        if all_success:
            logger.info("✓ Metrics infrastructure initialized successfully!")
            logger.info("\nNext steps:")
            logger.info("  1. Start the backend service")
            logger.info("  2. Metrics will be automatically aggregated to all time buckets")
            logger.info("  3. ILM policies will manage data retention automatically")
        else:
            logger.error("✗ Some infrastructure components failed to initialize")
            logger.error("Please check the logs above for details")
            sys.exit(1)
        
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"\n✗ Failed to initialize metrics infrastructure: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

# Made with Bob
