"""
Update API violation counts in intelligence metadata.

This script counts violations for each API and updates the violation_count
field in the intelligence_metadata.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.compliance_repository import ComplianceRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def update_violation_counts():
    """Update violation counts for all APIs."""
    api_repo = APIRepository()
    comp_repo = ComplianceRepository()
    
    # Get all APIs
    apis, total = api_repo.list_all(size=10000)
    logger.info(f"Found {total} APIs to update")
    
    updated_count = 0
    for api in apis:
        try:
            # Count violations for this API
            violations = await comp_repo.find_by_api_id(api.id)
            violation_count = len(violations)
            
            # Update the API's intelligence metadata
            if api.intelligence_metadata:
                api.intelligence_metadata.violation_count = violation_count
                
                # Update in database
                api_repo.update(
                    str(api.id),
                    {"intelligence_metadata": api.intelligence_metadata.model_dump()}
                )
                
                updated_count += 1
                if updated_count % 10 == 0:
                    logger.info(f"Updated {updated_count}/{total} APIs")
                    
        except Exception as e:
            logger.error(f"Failed to update API {api.id}: {e}")
            continue
    
    logger.info(f"Successfully updated {updated_count} APIs")


if __name__ == "__main__":
    asyncio.run(update_violation_counts())

# Made with Bob
