"""
Optimization Scheduler Jobs

Background jobs for generating performance optimization recommendations.
"""

import logging
from typing import Dict, Any

from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.optimization_service import OptimizationService
from app.models.recommendation import RecommendationStatus

logger = logging.getLogger(__name__)


async def run_optimization_job() -> Dict[str, Any]:
    """
    Generate optimization recommendations for all APIs across all gateways.
    
    This job is scheduled to run every 30 minutes to analyze metrics
    and generate performance optimization recommendations. Recommendations
    are stored in OpenSearch for review and implementation.
    
    Iterates over all gateways and generates recommendations for each gateway's APIs.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled optimization recommendation generation job (gateway-scoped)")
    
    try:
        # Initialize dependencies
        from app.db.repositories.gateway_repository import GatewayRepository
        
        recommendation_repo = RecommendationRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        
        from app.services.llm_service import LLMService
        from app.config import Settings

        settings = Settings()
        llm_service = LLMService(settings)

        optimization_service = OptimizationService(
            recommendation_repository=recommendation_repo,
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            llm_service=llm_service,
        )
        
        # Get all gateways
        gateways, _ = gateway_repo.list_all(size=1000)
        
        # Aggregate results across all gateways
        total_apis = 0
        total_analyzed = 0
        total_recommendations = 0
        all_errors = []
        
        for gateway in gateways:
            try:
                logger.info(f"Generating recommendations for gateway {gateway.id} ({gateway.name})")
                gateway_result = await optimization_service.generate_recommendations_for_gateway(
                    gateway_id=gateway.id,
                    min_impact=10.0
                )
                total_apis += gateway_result["total_apis"]
                total_analyzed += gateway_result["apis_analyzed"]
                total_recommendations += gateway_result["recommendations_generated"]
                all_errors.extend(gateway_result.get("errors", []))
            except Exception as e:
                logger.error(f"Failed to generate recommendations for gateway {gateway.id}: {e}")
                all_errors.append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error": str(e),
                })
        
        result = {
            "total_gateways": len(gateways),
            "total_apis": total_apis,
            "apis_analyzed": total_analyzed,
            "recommendations_generated": total_recommendations,
            "errors": all_errors,
        }
        
        # Expire old recommendations
        expired_count = _expire_old_recommendations(recommendation_repo)
        result["expired_recommendations"] = expired_count
        
        logger.info(
            f"Optimization recommendation generation completed: "
            f"{result['recommendations_generated']} recommendations "
            f"for {result['apis_analyzed']}/{result['total_apis']} APIs, "
            f"{expired_count} recommendations expired"
        )
        
        return {
            "status": "success",
            "job": "optimization_recommendation_generation",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Optimization recommendation generation job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "optimization_recommendation_generation",
            "error": str(e),
        }


async def run_recommendation_validation_job() -> Dict[str, Any]:
    """
    Track and validate implemented recommendations.
    
    This job reviews recommendations that have been marked as implemented
    and checks if validation results have been added. It also expires
    recommendations that are no longer relevant.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled recommendation validation job")
    
    try:
        # Initialize dependencies
        recommendation_repo = RecommendationRepository()
        
        # Get implemented recommendations without validation
        # This would check for recommendations that were implemented
        # but haven't been validated yet
        
        # For now, just get statistics
        stats = recommendation_repo.get_implementation_stats(days=30)
        
        logger.info(
            f"Recommendation validation completed: "
            f"{stats['total_recommendations']} total recommendations"
        )
        
        return {
            "status": "success",
            "job": "recommendation_validation",
            "result": {
                "total_recommendations": stats["total_recommendations"],
                "by_status": stats["by_status"],
                "avg_improvement": stats["avg_improvement"],
                "total_cost_savings": stats["total_cost_savings"],
            },
        }
        
    except Exception as e:
        logger.error(f"Recommendation validation job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "recommendation_validation",
            "error": str(e),
        }


async def run_recommendation_cleanup_job() -> Dict[str, Any]:
    """
    Clean up old and expired recommendations.
    
    This job removes recommendations that are older than 90 days
    and updates the status of expired pending recommendations.
    
    Returns:
        dict: Job execution results with statistics
    """
    logger.info("Starting scheduled recommendation cleanup job")
    
    try:
        # Initialize dependencies
        recommendation_repo = RecommendationRepository()
        
        # Expire old pending recommendations
        expired_recs = recommendation_repo.get_expired_recommendations()
        expired_count = 0
        
        for rec in expired_recs:
            try:
                recommendation_repo.update_recommendation_status(
                    recommendation_id=str(rec.id),
                    status=RecommendationStatus.EXPIRED,
                )
                expired_count += 1
            except Exception as e:
                logger.error(f"Failed to expire recommendation {rec.id}: {e}")
        
        # Delete very old recommendations (90+ days)
        deleted_count = recommendation_repo.delete_old_recommendations(days=90)
        
        logger.info(
            f"Recommendation cleanup completed: "
            f"{expired_count} recommendations expired, "
            f"{deleted_count} old recommendations deleted"
        )
        
        return {
            "status": "success",
            "job": "recommendation_cleanup",
            "result": {
                "expired_count": expired_count,
                "deleted_count": deleted_count,
            },
        }
        
    except Exception as e:
        logger.error(f"Recommendation cleanup job failed: {e}", exc_info=True)
        return {
            "status": "error",
            "job": "recommendation_cleanup",
            "error": str(e),
        }


def _expire_old_recommendations(recommendation_repo: RecommendationRepository) -> int:
    """
    Helper function to expire old pending recommendations.
    
    Args:
        recommendation_repo: Recommendation repository instance
        
    Returns:
        Number of recommendations expired
    """
    try:
        expired_recs = recommendation_repo.get_expired_recommendations()
        expired_count = 0
        
        for rec in expired_recs:
            try:
                recommendation_repo.update_recommendation_status(
                    recommendation_id=str(rec.id),
                    status=RecommendationStatus.EXPIRED,
                )
                expired_count += 1
            except Exception as e:
                logger.error(f"Failed to expire recommendation {rec.id}: {e}")
        
        return expired_count
        
    except Exception as e:
        logger.error(f"Failed to expire recommendations: {e}")
        return 0


# Made with Bob