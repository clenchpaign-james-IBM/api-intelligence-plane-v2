"""
Discovery Scheduler Jobs

Background jobs for API discovery from Gateways.
"""

import logging
from typing import Dict, Any

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.adapters.factory import GatewayAdapterFactory
from app.services.discovery_service import DiscoveryService

logger = logging.getLogger(__name__)


async def run_discovery_job() -> Dict[str, Any]:
    """
    Run API discovery across all connected Gateways.
    
    This job is scheduled to run every 5 minutes to discover new APIs
    and update existing API information.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled API discovery job")
    
    try:
        # Initialize dependencies
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        adapter_factory = GatewayAdapterFactory()
        
        discovery_service = DiscoveryService(
            api_repository=api_repo,
            gateway_repository=gateway_repo,
            adapter_factory=adapter_factory,
        )
        
        # Run discovery for all gateways
        result = await discovery_service.discover_all_gateways()
        
        logger.info(
            f"Discovery job completed: {result['total_apis_discovered']} APIs discovered "
            f"from {result['successful_gateways']}/{result['total_gateways']} gateways"
        )
        
        return {
            "status": "success",
            "job": "discovery",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Discovery job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "discovery",
            "error": str(e),
        }


async def run_shadow_api_detection_job() -> Dict[str, Any]:
    """
    Run shadow API detection across all Gateways.
    
    This job analyzes traffic logs stored in OpenSearch to identify
    undocumented APIs that are receiving traffic but not registered
    in the inventory.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled shadow API detection job")
    
    try:
        # Initialize dependencies
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        adapter_factory = GatewayAdapterFactory()
        
        discovery_service = DiscoveryService(
            api_repository=api_repo,
            gateway_repository=gateway_repo,
            adapter_factory=adapter_factory,
        )
        
        # Get all connected gateways
        gateways, total = gateway_repo.find_connected_gateways(size=1000)
        
        total_shadow_apis = 0
        successful_gateways = 0
        failed_gateways = 0
        errors = []
        
        # Run shadow API detection for each gateway
        for gateway in gateways:
            try:
                shadow_apis = await discovery_service.detect_shadow_apis(gateway.id)
                total_shadow_apis += len(shadow_apis)
                successful_gateways += 1
            except Exception as e:
                logger.error(f"Shadow API detection failed for gateway {gateway.id}: {e}")
                failed_gateways += 1
                errors.append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error": str(e),
                })
        
        result = {
            "total_gateways": len(gateways),
            "successful_gateways": successful_gateways,
            "failed_gateways": failed_gateways,
            "shadow_apis_found": total_shadow_apis,
            "errors": errors,
        }
        
        logger.info(
            f"Shadow API detection completed: {result['shadow_apis_found']} shadow APIs found "
            f"across {result['successful_gateways']}/{result['total_gateways']} gateways"
        )
        
        return {
            "status": "success",
            "job": "shadow_api_detection",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Shadow API detection job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "shadow_api_detection",
            "error": str(e),
        }


async def run_inactive_api_cleanup_job() -> Dict[str, Any]:
    """
    Mark inactive APIs that haven't received traffic in 24+ hours.
    
    This job updates the status of APIs that appear to be inactive
    based on their last_seen timestamp.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled inactive API cleanup job")
    
    try:
        # Initialize dependencies
        api_repo = APIRepository()
        
        # Get all active APIs
        from app.models.api import APIStatus
        from datetime import datetime, timedelta
        
        # Query for APIs that haven't been seen in 24+ hours
        query = {
            "bool": {
                "must": [
                    {"term": {"status": APIStatus.ACTIVE.value}},
                    {
                        "range": {
                            "last_seen_at": {
                                "lt": (datetime.utcnow() - timedelta(hours=24)).isoformat()
                            }
                        }
                    },
                ],
            }
        }
        
        inactive_apis, total = api_repo.search(query, size=10000)
        
        # Mark each API as inactive
        inactive_count = 0
        for api in inactive_apis:
            try:
                api_repo.update(str(api.id), {"status": APIStatus.INACTIVE.value})
                inactive_count += 1
            except Exception as e:
                logger.warning(f"Failed to mark API {api.id} as inactive: {e}")
        
        logger.info(f"Inactive API cleanup completed: {inactive_count} APIs marked as inactive")
        
        return {
            "status": "success",
            "job": "inactive_api_cleanup",
            "result": {
                "inactive_apis_marked": inactive_count,
            },
        }
        
    except Exception as e:
        logger.error(f"Inactive API cleanup job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "inactive_api_cleanup",
            "error": str(e),
        }


# Made with Bob