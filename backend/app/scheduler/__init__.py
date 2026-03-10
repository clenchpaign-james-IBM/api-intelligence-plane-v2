"""
Background Scheduler

APScheduler setup for periodic background jobs including:
- API discovery
- Metrics collection
- Security scanning
- Prediction generation
- Optimization analysis
"""

import logging
from typing import Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

from app.config import settings

logger = logging.getLogger(__name__)

# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """
    Get the global scheduler instance.
    
    Returns:
        AsyncIOScheduler instance
    """
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


def setup_scheduler() -> AsyncIOScheduler:
    """
    Setup and configure the background scheduler.
    
    Registers all periodic jobs based on configuration settings.
    Jobs are only added if scheduler is enabled in settings.
    
    Returns:
        Configured scheduler instance
    """
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled in settings")
        return None
    
    scheduler = get_scheduler()
    
    # Import job functions (will be implemented in respective modules)
    # These imports are done here to avoid circular dependencies
    try:
        from app.scheduler.discovery_jobs import run_discovery_job
        from app.scheduler.metrics_jobs import run_metrics_collection_job
        from app.scheduler.security_jobs import run_security_scan_job
        from app.scheduler.prediction_jobs import run_prediction_job
        from app.scheduler.optimization_jobs import run_optimization_job
        
        # Add discovery job
        scheduler.add_job(
            run_discovery_job,
            trigger=IntervalTrigger(minutes=settings.DISCOVERY_INTERVAL_MINUTES),
            id="discovery_job",
            name="API Discovery",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled discovery job: every {settings.DISCOVERY_INTERVAL_MINUTES} minutes"
        )
        
        # Add metrics collection job
        scheduler.add_job(
            run_metrics_collection_job,
            trigger=IntervalTrigger(minutes=settings.METRICS_INTERVAL_MINUTES),
            id="metrics_job",
            name="Metrics Collection",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled metrics job: every {settings.METRICS_INTERVAL_MINUTES} minutes"
        )
        
        # Add security scan job
        scheduler.add_job(
            run_security_scan_job,
            trigger=IntervalTrigger(minutes=settings.SECURITY_SCAN_INTERVAL_MINUTES),
            id="security_job",
            name="Security Scanning",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled security job: every {settings.SECURITY_SCAN_INTERVAL_MINUTES} minutes"
        )
        
        # Add prediction job
        scheduler.add_job(
            run_prediction_job,
            trigger=IntervalTrigger(minutes=settings.PREDICTION_INTERVAL_MINUTES),
            id="prediction_job",
            name="Prediction Generation",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled prediction job: every {settings.PREDICTION_INTERVAL_MINUTES} minutes"
        )
        
        # Add optimization job
        scheduler.add_job(
            run_optimization_job,
            trigger=IntervalTrigger(minutes=settings.OPTIMIZATION_INTERVAL_MINUTES),
            id="optimization_job",
            name="Optimization Analysis",
            replace_existing=True,
        )
        logger.info(
            f"Scheduled optimization job: every {settings.OPTIMIZATION_INTERVAL_MINUTES} minutes"
        )
        
    except ImportError as e:
        logger.warning(f"Some scheduler jobs not available yet: {e}")
    
    return scheduler


def start_scheduler() -> None:
    """Start the background scheduler."""
    if not settings.SCHEDULER_ENABLED:
        logger.info("Scheduler is disabled, not starting")
        return
    
    scheduler = get_scheduler()
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started")


def shutdown_scheduler() -> None:
    """Shutdown the background scheduler."""
    scheduler = get_scheduler()
    if scheduler and scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler shutdown")

# Made with Bob
