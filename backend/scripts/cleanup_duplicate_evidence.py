"""
Cleanup script to remove duplicate evidence entries from existing compliance violations.

This script:
1. Fetches all compliance violations from OpenSearch
2. Deduplicates evidence entries based on (type, source, description)
3. Updates violations with cleaned evidence
"""

import asyncio
import logging
from datetime import datetime

from app.db.client import get_client
from app.models.compliance import ComplianceViolation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def cleanup_duplicate_evidence():
    """Remove duplicate evidence entries from all compliance violations."""
    
    client = get_client()
    index_name = "compliance-violations"
    
    # Fetch all violations
    query = {"query": {"match_all": {}}, "size": 10000}
    
    try:
        response = client.search(index=index_name, body=query)
        violations = response["hits"]["hits"]
        
        logger.info(f"Found {len(violations)} violations to process")
        
        updated_count = 0
        cleaned_evidence_count = 0
        
        for hit in violations:
            violation_id = hit["_id"]
            source = hit["_source"]
            
            # Get evidence
            evidence_list = source.get("evidence", [])
            
            if not evidence_list or len(evidence_list) <= 1:
                continue
            
            # Deduplicate evidence by (type, source, description)
            seen_keys = set()
            unique_evidence = []
            duplicates_removed = 0
            
            for evidence in evidence_list:
                evidence_key = (
                    evidence.get("type"),
                    evidence.get("source"),
                    evidence.get("description"),
                )
                
                if evidence_key not in seen_keys:
                    seen_keys.add(evidence_key)
                    unique_evidence.append(evidence)
                else:
                    duplicates_removed += 1
            
            # Update if duplicates were found
            if duplicates_removed > 0:
                source["evidence"] = unique_evidence
                source["updated_at"] = datetime.utcnow().isoformat()
                
                # Update in OpenSearch
                client.update(
                    index=index_name,
                    id=violation_id,
                    body={"doc": source}
                )
                
                updated_count += 1
                cleaned_evidence_count += duplicates_removed
                
                logger.info(
                    f"Cleaned violation {violation_id}: "
                    f"removed {duplicates_removed} duplicate evidence entries "
                    f"({len(evidence_list)} -> {len(unique_evidence)})"
                )
        
        logger.info(
            f"\nCleanup complete:\n"
            f"  - Violations updated: {updated_count}\n"
            f"  - Duplicate evidence removed: {cleaned_evidence_count}"
        )
        
    except Exception as e:
        logger.error(f"Cleanup failed: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(cleanup_duplicate_evidence())

# Made with Bob
