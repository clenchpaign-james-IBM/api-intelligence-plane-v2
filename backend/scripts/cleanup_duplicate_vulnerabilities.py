"""Cleanup script to remove duplicate vulnerabilities.

This script identifies and removes duplicate vulnerabilities, keeping only
the most recent instance of each unique (api_id, vulnerability_type, title) combination.
"""

import asyncio
import logging
import sys
from pathlib import Path
from collections import defaultdict

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.repositories.vulnerability_repository import VulnerabilityRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_duplicates():
    """Remove duplicate vulnerabilities, keeping only the most recent."""
    
    repo = VulnerabilityRepository()
    
    # Get all vulnerabilities
    logger.info("Fetching all vulnerabilities...")
    body = {
        "query": {"match_all": {}},
        "size": 10000,
        "sort": [{"detected_at": {"order": "desc"}}]
    }
    response = repo.client.search(index=repo.index_name, body=body)
    all_vulns = [repo.model_class(**hit["_source"]) for hit in response["hits"]["hits"]]
    
    logger.info(f"Found {len(all_vulns)} total vulnerabilities")
    
    # Group by unique key (api_id, vulnerability_type, title)
    groups = defaultdict(list)
    for vuln in all_vulns:
        key = (str(vuln.api_id), vuln.vulnerability_type.value, vuln.title)
        groups[key].append(vuln)
    
    # Find duplicates
    duplicates_to_delete = []
    for key, vulns in groups.items():
        if len(vulns) > 1:
            # Sort by detected_at descending (most recent first)
            vulns_sorted = sorted(vulns, key=lambda v: v.detected_at, reverse=True)
            # Keep the first (most recent), delete the rest
            to_delete = vulns_sorted[1:]
            duplicates_to_delete.extend(to_delete)
            logger.info(f"Found {len(vulns)} instances of {key[2]}, will delete {len(to_delete)}")
    
    if not duplicates_to_delete:
        logger.info("No duplicates found!")
        return
    
    logger.info(f"\nDeleting {len(duplicates_to_delete)} duplicate vulnerabilities...")
    
    deleted_count = 0
    for vuln in duplicates_to_delete:
        try:
            repo.delete(str(vuln.id))
            deleted_count += 1
            if deleted_count % 10 == 0:
                logger.info(f"Deleted {deleted_count}/{len(duplicates_to_delete)}...")
        except Exception as e:
            logger.error(f"Failed to delete {vuln.id}: {e}")
    
    logger.info(f"\n✅ Cleanup complete! Deleted {deleted_count} duplicate vulnerabilities")
    
    # Verify
    response = repo.client.search(index=repo.index_name, body={"query": {"match_all": {}}, "size": 0})
    final_count = response["hits"]["total"]["value"]
    logger.info(f"Final vulnerability count: {final_count}")


if __name__ == "__main__":
    asyncio.run(cleanup_duplicates())

# Made with Bob
