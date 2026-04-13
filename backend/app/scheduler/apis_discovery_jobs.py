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


async def run_api_discovery_job(gateway_id: UUID) -> None:
    """
    Run API discovery for a specific gateway.
    
    This job fetches APIs (along with PolicyActions) from the gateway
    and stores them in the data store. It does NOT perform shadow API
    detection or other analysis - those are handled by separate use cases.
    
    Args:
        gateway_id: UUID of the gateway to discover APIs from
    """
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
        
        # Run discovery for this specific gateway
        result = await discovery_service.discover_gateway_apis(gateway_id)
        
        logger.info(
            f"API discovery completed for gateway {gateway_id}: "
            f"{result.get('apis_discovered', 0)} APIs discovered"
        )
        
    except Exception as e:
        logger.error(
            f"API discovery failed for gateway {gateway_id}: {e}",
            exc_info=True
        )


def setup_api_discovery_jobs(scheduler, gateway_repository: GatewayRepository) -> None:
    """
    Dynamically create API discovery jobs for each connected gateway.
    
    This creates isolated jobs per gateway to prevent single point of failure.
    Each gateway's job runs independently on the configured interval.
    
    Args:
        scheduler: APScheduler instance
        gateway_repository: Repository for gateway operations
    """
    from apscheduler.triggers.interval import IntervalTrigger
    
    # Get all connected gateways
    gateways, total = gateway_repository.find_connected_gateways(size=1000)
    
    if not gateways:
        logger.warning("No connected gateways found - no API discovery jobs scheduled")
        return
    
    # Create a job for each gateway
    for gateway in gateways:
        job_id = f"api_discovery_{gateway.id}"
        
        scheduler.add_job(
            run_api_discovery_job,
            args=[gateway.id],
            trigger=IntervalTrigger(minutes=settings.API_DISCOVERY_INTERVAL_MINUTES),
            id=job_id,
            name=f"API Discovery - {gateway.name}",
            replace_existing=True,
        )
        
        logger.info(
            f"Scheduled API discovery job for gateway {gateway.name} ({gateway.id}) "
            f"- interval: {settings.API_DISCOVERY_INTERVAL_MINUTES} minutes"
        )
    
    logger.info(f"Scheduled {len(gateways)} API discovery jobs")


# Made with Bob