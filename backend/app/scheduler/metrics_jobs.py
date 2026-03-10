"""
Metrics Scheduler Jobs

Background jobs for collecting metrics from Gateways.
"""

import logging
from typing import Dict, Any

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.adapters.factory import GatewayAdapterFactory
from app.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


async def run_metrics_collection_job() -> Dict[str, Any]:
    """
    Collect metrics from all connected Gateways.
    
    This job is scheduled to run every 1 minute to collect real-time
    metrics data from all APIs across all connected Gateways.
    The metrics are stored in OpenSearch for analysis and monitoring.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled metrics collection job")
    
    try:
        # Initialize dependencies
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        adapter_factory = GatewayAdapterFactory()
        
        metrics_service = MetricsService(
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            gateway_repository=gateway_repo,
            adapter_factory=adapter_factory,
        )
        
        # Collect metrics from all gateways
        result = await metrics_service.collect_all_metrics()
        
        logger.info(
            f"Metrics collection completed: {result['total_metrics_collected']} metrics collected "
            f"from {result['successful_gateways']}/{result['total_gateways']} gateways"
        )
        
        return {
            "status": "success",
            "job": "metrics_collection",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Metrics collection job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "metrics_collection",
            "error": str(e),
        }


async def run_health_score_calculation_job() -> Dict[str, Any]:
    """
    Calculate health scores for all active APIs.
    
    This job calculates health scores based on recent metrics
    and updates the API records in OpenSearch.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled health score calculation job")
    
    try:
        # Initialize dependencies
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        adapter_factory = GatewayAdapterFactory()
        
        metrics_service = MetricsService(
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            gateway_repository=gateway_repo,
            adapter_factory=adapter_factory,
        )
        
        # Get all active APIs
        from app.models.api import APIStatus
        
        query = {"term": {"status": APIStatus.ACTIVE.value}}
        active_apis, total = api_repo.search(query, size=10000)
        
        # Calculate health score for each API
        updated_count = 0
        failed_count = 0
        
        for api in active_apis:
            try:
                health_score = metrics_service.calculate_health_score(api.id)
                
                # Update API with new health score
                api_repo.update(str(api.id), {"health_score": health_score})
                updated_count += 1
                
            except Exception as e:
                logger.warning(f"Failed to calculate health score for API {api.id}: {e}")
                failed_count += 1
        
        result = {
            "total_apis": len(active_apis),
            "updated_apis": updated_count,
            "failed_apis": failed_count,
        }
        
        logger.info(
            f"Health score calculation completed: {updated_count}/{len(active_apis)} APIs updated"
        )
        
        return {
            "status": "success",
            "job": "health_score_calculation",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Health score calculation job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "health_score_calculation",
            "error": str(e),
        }


# Made with Bob