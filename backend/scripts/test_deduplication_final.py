"""Final test to verify vulnerability deduplication works correctly."""

import asyncio
import logging
import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.security_service import SecurityService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_no_new_duplicates():
    """Test that running scans doesn't create new duplicates."""
    
    settings = Settings()
    api_repo = APIRepository()
    vuln_repo = VulnerabilityRepository()
    security_service = SecurityService(settings)
    
    # Get first API
    body = {"query": {"match_all": {}}, "size": 1}
    response = api_repo.client.search(index=api_repo.index_name, body=body)
    if not response["hits"]["hits"]:
        logger.error("No APIs found")
        return False
    
    api = api_repo.model_class(**response["hits"]["hits"][0]["_source"])
    logger.info(f"Testing with API: {api.name}")
    
    # Get initial state
    initial_vulns = await vuln_repo.find_by_api_id(api.id, limit=1000)
    initial_groups = defaultdict(list)
    for v in initial_vulns:
        key = (v.vulnerability_type.value, v.title)
        initial_groups[key].append(v.id)
    
    logger.info(f"Initial state: {len(initial_vulns)} total vulnerabilities")
    logger.info(f"Initial unique types: {len(initial_groups)}")
    
    # Run scan
    logger.info("\n=== Running security scan ===")
    await security_service.scan_api_security(api.gateway_id, api.id)
    
    # Get final state
    final_vulns = await vuln_repo.find_by_api_id(api.id, limit=1000)
    final_groups = defaultdict(list)
    for v in final_vulns:
        key = (v.vulnerability_type.value, v.title)
        final_groups[key].append(v.id)
    
    logger.info(f"\nFinal state: {len(final_vulns)} total vulnerabilities")
    logger.info(f"Final unique types: {len(final_groups)}")
    
    # Check for new duplicates
    new_duplicates = False
    for key, ids in final_groups.items():
        initial_count = len(initial_groups.get(key, []))
        final_count = len(ids)
        if final_count > initial_count:
            logger.error(f"❌ NEW duplicate created for {key}: {initial_count} → {final_count}")
            new_duplicates = True
        elif final_count == initial_count:
            logger.info(f"✅ No new duplicates for {key}: {final_count} instances")
    
    if not new_duplicates:
        logger.info("\n" + "="*60)
        logger.info("✅ SUCCESS: No new duplicates created!")
        logger.info("="*60)
        return True
    else:
        logger.error("\n" + "="*60)
        logger.error("❌ FAILURE: New duplicates were created!")
        logger.error("="*60)
        return False


if __name__ == "__main__":
    success = asyncio.run(test_no_new_duplicates())
    sys.exit(0 if success else 1)

# Made with Bob
