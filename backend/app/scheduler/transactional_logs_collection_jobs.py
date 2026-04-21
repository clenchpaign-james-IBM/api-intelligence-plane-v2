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


async def run_transactional_logs_collection_job() -> None:
    """
    Collect transactional logs and aggregate metrics for all connected gateways.
    
    This job:
    1. Fetches all connected gateways dynamically
    2. For each gateway:
       - Fetches transactional logs for the configured time interval
       - Stores logs in TransactionalLogRepository (daily indices)
       - Aggregates logs into time-bucketed metrics
       - Stores metrics in MetricsRepository (time-bucketed indices)
    """
    logger.info("🔄 Starting transactional logs collection job for all connected gateways")
    
    try:
        # Initialize repositories
        gateway_repo = GatewayRepository()
        metrics_service = MetricsService(
            metrics_repository=MetricsRepository(),
            api_repository=APIRepository(),
            gateway_repository=gateway_repo,
            adapter_factory=GatewayAdapterFactory(),
        )
        
        # Get all connected gateways
        gateways, total = gateway_repo.find_connected_gateways(size=1000)
        
        if not gateways:
            logger.info("No connected gateways found - skipping transactional logs collection")
            return
        
        logger.info(f"Found {len(gateways)} connected gateway(s) for transactional logs collection")
        
        # Calculate time range based on configured interval
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=settings.TRANSACTIONAL_LOGS_INTERVAL_MINUTES)
        
        # Collect logs for each gateway
        success_count = 0
        error_count = 0
        
        for gateway in gateways:
            try:
                logger.info(
                    f"Collecting logs for gateway {gateway.name} ({gateway.id}) "
                    f"from {start_time.isoformat()} to {end_time.isoformat()}"
                )
                
                # Collect logs, store them, aggregate to metrics, and store metrics
                await metrics_service.collect_transactional_logs(
                    gateway_id=gateway.id,
                    start_time=start_time,
                    end_time=end_time,
                    time_bucket=settings.METRICS_AGGREGATION_BUCKET,
                )
                
                success_count += 1
                logger.info(f"✅ Completed transactional logs collection for gateway {gateway.name}")
                
            except Exception as e:
                error_count += 1
                logger.error(
                    f"❌ Transactional logs collection failed for gateway {gateway.name} ({gateway.id}): {e}",
                    exc_info=True
                )
        
        logger.info(
            f"✅ Transactional logs collection job completed: "
            f"{success_count} succeeded, {error_count} failed out of {len(gateways)} gateways"
        )
        
    except Exception as e:
        logger.error(
            f"❌ Transactional logs collection job failed: {e}",
            exc_info=True
        )


def setup_logs_metrics_collection_jobs(scheduler, gateway_repository: GatewayRepository) -> None:
    """
    Setup a single transactional logs collection job that processes all connected gateways.
    
    This approach dynamically discovers connected gateways on each run, eliminating
    the need to register/unregister jobs when gateways connect/disconnect.
    
    Args:
        scheduler: APScheduler instance
        gateway_repository: Repository for gateway operations (not used, kept for compatibility)
    """
    from apscheduler.triggers.interval import IntervalTrigger
    
    # Register single job that will discover gateways dynamically
    scheduler.add_job(
        run_transactional_logs_collection_job,
        trigger=IntervalTrigger(minutes=settings.TRANSACTIONAL_LOGS_INTERVAL_MINUTES),
        id="transactional_logs_collection",
        name="Transactional Logs Collection (All Gateways)",
        replace_existing=True,
    )
    
    logger.info(
        f"✅ Scheduled transactional logs collection job "
        f"(runs every {settings.TRANSACTIONAL_LOGS_INTERVAL_MINUTES} minutes, discovers gateways dynamically)"
    )


# Made with Bob