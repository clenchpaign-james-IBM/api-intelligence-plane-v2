"""
Transactional Logs Collection Scheduler Jobs

Background jobs for collecting transactional logs from Gateways and
aggregating them into time-bucketed metrics. Each gateway gets its own
isolated job to prevent single point of failure.
"""

import logging
from typing import Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.adapters.factory import GatewayAdapterFactory
from app.services.metrics_service import MetricsService
from app.config import settings

logger = logging.getLogger(__name__)


async def run_transactional_logs_collection_job(gateway_id: UUID) -> None:
    """
    Collect transactional logs and aggregate metrics for a specific gateway.
    
    This job:
    1. Fetches transactional logs from the gateway for the configured time interval
    2. Stores logs in TransactionalLogRepository (daily indices)
    3. Aggregates logs into time-bucketed metrics
    4. Stores metrics in MetricsRepository (time-bucketed indices)
    
    Args:
        gateway_id: UUID of the gateway to collect logs from
    """
    try:
        # Initialize metrics service with all dependencies
        metrics_service = MetricsService(
            metrics_repository=MetricsRepository(),
            api_repository=APIRepository(),
            gateway_repository=GatewayRepository(),
            adapter_factory=GatewayAdapterFactory(),
        )
        
        # Calculate time range based on configured interval
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=settings.TRANSACTIONAL_LOGS_INTERVAL_MINUTES)
        
        # Collect logs, store them, aggregate to metrics, and store metrics
        # Method handles all storage via repositories internally
        await metrics_service.collect_transactional_logs(
            gateway_id=gateway_id,
            start_time=start_time,
            end_time=end_time,
            time_bucket=settings.METRICS_AGGREGATION_BUCKET,
        )
        
        logger.info(
            f"Transactional logs collection completed for gateway {gateway_id} "
            f"(interval: {start_time.isoformat()} to {end_time.isoformat()})"
        )
        
    except Exception as e:
        logger.error(
            f"Transactional logs collection failed for gateway {gateway_id}: {e}",
            exc_info=True
        )


def setup_logs_metrics_collection_jobs(scheduler, gateway_repository: GatewayRepository) -> None:
    """
    Dynamically create transactional logs collection jobs for each connected gateway.
    
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
        logger.warning("No connected gateways found - no transactional logs jobs scheduled")
        return
    
    # Create a job for each gateway
    for gateway in gateways:
        job_id = f"transactional_logs_{gateway.id}"
        
        scheduler.add_job(
            run_transactional_logs_collection_job,
            args=[gateway.id],
            trigger=IntervalTrigger(minutes=settings.TRANSACTIONAL_LOGS_INTERVAL_MINUTES),
            id=job_id,
            name=f"Transactional Logs Collection - {gateway.name}",
            replace_existing=True,
        )
        
        logger.info(
            f"Scheduled transactional logs job for gateway {gateway.name} ({gateway.id}) "
            f"- interval: {settings.TRANSACTIONAL_LOGS_INTERVAL_MINUTES} minutes"
        )
    
    logger.info(f"Scheduled {len(gateways)} transactional logs collection jobs")


# Made with Bob