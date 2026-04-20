"""
API Discovery Scheduler Jobs

Background jobs for API discovery from Gateways. Each gateway gets its own
isolated job to prevent single point of failure and enable independent scheduling.
"""

import logging
from typing import Dict, Any
from uuid import UUID

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.adapters.factory import GatewayAdapterFactory
from app.services.discovery_service import DiscoveryService
from app.config import settings

logger = logging.getLogger(__name__)


async def run_api_discovery_job() -> None:
    """
    Run API discovery for all connected gateways.
    
    This job:
    1. Fetches all connected gateways dynamically
    2. For each gateway:
       - Fetches APIs (along with PolicyActions) from the gateway
       - Stores them in the data store
    
    Note: This does NOT perform shadow API detection or other analysis -
    those are handled by separate use cases.
    """
    logger.info("🔄 Starting API discovery job for all connected gateways")
    
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
        
        if not gateways:
            logger.info("No connected gateways found - skipping API discovery")
            return
        
        logger.info(f"Found {len(gateways)} connected gateway(s) for API discovery")
        
        # Run discovery for each gateway
        success_count = 0
        error_count = 0
        total_apis = 0
        
        for gateway in gateways:
            try:
                logger.info(f"Discovering APIs for gateway {gateway.name} ({gateway.id})")
                
                result = await discovery_service.discover_gateway_apis(gateway.id)
                
                apis_discovered = result.get('apis_discovered', 0)
                total_apis += apis_discovered
                success_count += 1
                
                logger.info(
                    f"✅ API discovery completed for gateway {gateway.name}: "
                    f"{apis_discovered} APIs discovered"
                )
                
            except Exception as e:
                error_count += 1
                logger.error(
                    f"❌ API discovery failed for gateway {gateway.name} ({gateway.id}): {e}",
                    exc_info=True
                )
        
        logger.info(
            f"✅ API discovery job completed: "
            f"{success_count} succeeded, {error_count} failed out of {len(gateways)} gateways, "
            f"{total_apis} total APIs discovered"
        )
        
    except Exception as e:
        logger.error(
            f"❌ API discovery job failed: {e}",
            exc_info=True
        )


def setup_api_discovery_jobs(scheduler, gateway_repository: GatewayRepository) -> None:
    """
    Setup a single API discovery job that processes all connected gateways.
    
    This approach dynamically discovers connected gateways on each run, eliminating
    the need to register/unregister jobs when gateways connect/disconnect.
    
    Args:
        scheduler: APScheduler instance
        gateway_repository: Repository for gateway operations (not used, kept for compatibility)
    """
    from apscheduler.triggers.interval import IntervalTrigger
    
    # Register single job that will discover gateways dynamically
    scheduler.add_job(
        run_api_discovery_job,
        trigger=IntervalTrigger(minutes=settings.API_DISCOVERY_INTERVAL_MINUTES),
        id="api_discovery",
        name="API Discovery (All Gateways)",
        replace_existing=True,
    )
    
    logger.info(
        f"✅ Scheduled API discovery job "
        f"(runs every {settings.API_DISCOVERY_INTERVAL_MINUTES} minutes, discovers gateways dynamically)"
    )


# Made with Bob