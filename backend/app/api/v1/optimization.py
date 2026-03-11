"""
Optimization API Endpoints

REST API endpoints for performance optimization recommendations.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status as http_status
from pydantic import BaseModel, Field

from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.optimization_service import OptimizationService
from app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
    ImplementationEffort,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Optimization"])


# Response Models
class EstimatedImpactResponse(BaseModel):
    """Response model for estimated impact."""
    
    metric: str
    current_value: float
    expected_value: float
    improvement_percentage: float
    confidence: float


class RecommendationResponse(BaseModel):
    """Response model for a single recommendation."""
    
    id: str
    api_id: str
    recommendation_type: str
    title: str
    description: str
    priority: str
    estimated_impact: EstimatedImpactResponse
    implementation_effort: str
    implementation_steps: list[str]
    status: str
    implemented_at: Optional[str] = None
    cost_savings: Optional[float] = None
    created_at: str
    updated_at: str
    expires_at: Optional[str] = None


class RecommendationListResponse(BaseModel):
    """Response model for recommendation list."""
    
    recommendations: list[RecommendationResponse]
    total: int
    page: int
    page_size: int


class RecommendationStatsResponse(BaseModel):
    """Response model for recommendation statistics."""
    
    total_recommendations: int
    by_status: list[dict]
    by_priority: list[dict]
    by_type: list[dict]
    avg_improvement: float
    total_cost_savings: float


@router.get(
    "/recommendations",
    response_model=RecommendationListResponse,
    summary="List optimization recommendations",
)
async def list_recommendations(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    priority: Optional[RecommendationPriority] = Query(None, description="Filter by priority"),
    status: Optional[RecommendationStatus] = Query(None, description="Filter by status"),
    recommendation_type: Optional[RecommendationType] = Query(None, description="Filter by type"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> RecommendationListResponse:
    """
    List optimization recommendations with optional filters.
    
    Args:
        api_id: Filter by API ID
        priority: Filter by priority level
        status: Filter by recommendation status
        recommendation_type: Filter by recommendation type
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        List of recommendations with pagination info
        
    Raises:
        HTTPException: If recommendation retrieval fails
    """
    try:
        # Initialize repository
        recommendation_repo = RecommendationRepository()
        
        # Get recommendations with filters
        result = recommendation_repo.list_recommendations(
            api_id=str(api_id) if api_id else None,
            priority=priority,
            status=status,
            recommendation_type=recommendation_type,
            page=page,
            page_size=page_size,
        )
        
        # Convert to response models
        recommendations = [
            RecommendationResponse(
                id=str(rec.id),
                api_id=str(rec.api_id),
                recommendation_type=rec.recommendation_type.value,
                title=rec.title,
                description=rec.description,
                priority=rec.priority.value,
                estimated_impact=EstimatedImpactResponse(
                    metric=rec.estimated_impact.metric,
                    current_value=rec.estimated_impact.current_value,
                    expected_value=rec.estimated_impact.expected_value,
                    improvement_percentage=rec.estimated_impact.improvement_percentage,
                    confidence=rec.estimated_impact.confidence,
                ),
                implementation_effort=rec.implementation_effort.value,
                implementation_steps=rec.implementation_steps,
                status=rec.status.value,
                implemented_at=rec.implemented_at.isoformat() if rec.implemented_at else None,
                cost_savings=rec.cost_savings,
                created_at=rec.created_at.isoformat(),
                updated_at=rec.updated_at.isoformat(),
                expires_at=rec.expires_at.isoformat() if rec.expires_at else None,
            )
            for rec in result["recommendations"]
        ]
        
        return RecommendationListResponse(
            recommendations=recommendations,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
        )
        
    except Exception as e:
        logger.error(f"Failed to list recommendations: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recommendations: {str(e)}",
        )


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=RecommendationResponse,
    summary="Get recommendation details",
)
async def get_recommendation(
    recommendation_id: UUID,
) -> RecommendationResponse:
    """
    Get detailed information about a specific recommendation.
    
    Args:
        recommendation_id: Recommendation UUID
        
    Returns:
        Recommendation details
        
    Raises:
        HTTPException: If recommendation not found or retrieval fails
    """
    try:
        # Initialize repository
        recommendation_repo = RecommendationRepository()
        
        # Get recommendation
        recommendation = recommendation_repo.get_recommendation(str(recommendation_id))
        
        if not recommendation:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation {recommendation_id} not found",
            )
        
        # Convert to response model
        return RecommendationResponse(
            id=str(recommendation.id),
            api_id=str(recommendation.api_id),
            recommendation_type=recommendation.recommendation_type.value,
            title=recommendation.title,
            description=recommendation.description,
            priority=recommendation.priority.value,
            estimated_impact=EstimatedImpactResponse(
                metric=recommendation.estimated_impact.metric,
                current_value=recommendation.estimated_impact.current_value,
                expected_value=recommendation.estimated_impact.expected_value,
                improvement_percentage=recommendation.estimated_impact.improvement_percentage,
                confidence=recommendation.estimated_impact.confidence,
            ),
            implementation_effort=recommendation.implementation_effort.value,
            implementation_steps=recommendation.implementation_steps,
            status=recommendation.status.value,
            implemented_at=recommendation.implemented_at.isoformat() if recommendation.implemented_at else None,
            cost_savings=recommendation.cost_savings,
            created_at=recommendation.created_at.isoformat(),
            updated_at=recommendation.updated_at.isoformat(),
            expires_at=recommendation.expires_at.isoformat() if recommendation.expires_at else None,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendation {recommendation_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve recommendation: {str(e)}",
        )


@router.post(
    "/recommendations/generate",
    response_model=dict,
    summary="Generate recommendations for an API",
)
async def generate_recommendations(
    api_id: UUID = Query(..., description="API ID to generate recommendations for"),
    min_impact: float = Query(10.0, ge=0, le=100, description="Minimum expected improvement %"),
    use_ai: bool = Query(False, description="Use AI-enhanced recommendation generation"),
) -> dict:
    """
    Generate optimization recommendations for a specific API.
    
    Args:
        api_id: API UUID
        min_impact: Minimum expected improvement percentage
        
    Returns:
        Generation results with recommendation count
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        # Initialize dependencies
        recommendation_repo = RecommendationRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        
        optimization_service = OptimizationService(
            recommendation_repository=recommendation_repo,
            metrics_repository=metrics_repo,
            api_repository=api_repo,
        )
        
        # Generate recommendations
        if use_ai:
            # Try to get LLM service for AI-enhanced generation
            try:
                from app.services.llm_service import LLMService
                from app.config import Settings
                settings = Settings()
                llm_service = LLMService(settings)
                optimization_service.llm_service = llm_service
            except Exception as e:
                logger.warning(f"LLM service unavailable, using rule-based: {e}")
            
            result = await optimization_service.generate_ai_enhanced_recommendations(
                api_id=api_id,
                min_impact=min_impact,
            )
            
            return {
                "status": "accepted",
                "message": f"Generated AI-enhanced recommendations for API {api_id}",
                "result": result,
            }
        else:
            recommendations = optimization_service.generate_recommendations_for_api(
                api_id=api_id,
                min_impact=min_impact,
            )
            
            return {
                "api_id": str(api_id),
                "recommendations_generated": len(recommendations),
                "recommendations": [
                    {
                        "id": str(rec.id),
                        "type": rec.recommendation_type.value,
                        "title": rec.title,
                        "priority": rec.priority.value,
                        "expected_improvement": rec.estimated_impact.improvement_percentage,
                    }
                    for rec in recommendations
                ],
            }
        
    except Exception as e:
        logger.error(f"Failed to generate recommendations for API {api_id}: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate recommendations: {str(e)}",
        )


@router.get(
    "/recommendations/stats",
    response_model=RecommendationStatsResponse,
    summary="Get recommendation statistics",
)
async def get_recommendation_stats(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
) -> RecommendationStatsResponse:
    """
    Get statistics about optimization recommendations.
    
    Args:
        api_id: Optional API ID filter
        days: Number of days to look back
        
    Returns:
        Recommendation statistics
        
    Raises:
        HTTPException: If stats retrieval fails
    """
    try:
        # Initialize repository
        recommendation_repo = RecommendationRepository()
        
        # Get statistics
        stats = recommendation_repo.get_implementation_stats(
            api_id=str(api_id) if api_id else None,
            days=days,
        )
        
        return RecommendationStatsResponse(
            total_recommendations=stats["total_recommendations"],
            by_status=stats["by_status"],
            by_priority=stats["by_priority"],
            by_type=stats["by_type"],
            avg_improvement=stats["avg_improvement"],
            total_cost_savings=stats["total_cost_savings"],
        )
        
    except Exception as e:
        logger.error(f"Failed to get recommendation stats: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve statistics: {str(e)}",
        )


@router.post(
    "/recommendations/ai-enhanced",
    summary="Generate AI-enhanced recommendations",
)
async def generate_ai_enhanced_recommendations(
    api_id: UUID = Query(..., description="API ID to generate recommendations for"),
    min_impact: float = Query(10.0, ge=0, le=100, description="Minimum expected improvement %"),
) -> dict:
    """
    Generate AI-enhanced optimization recommendations with LLM analysis.
    
    Args:
        api_id: API ID to generate recommendations for
        min_impact: Minimum expected improvement percentage
        
    Returns:
        AI-enhanced recommendations with analysis
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        # Initialize services
        recommendation_repo = RecommendationRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        
        # Try to get LLM service
        try:
            from app.services.llm_service import LLMService
            from app.config import Settings
            settings = Settings()
            llm_service = LLMService(settings)
        except Exception as e:
            logger.warning(f"LLM service unavailable: {e}")
            llm_service = None
        
        optimization_service = OptimizationService(
            recommendation_repository=recommendation_repo,
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            llm_service=llm_service,
        )
        
        # Generate AI-enhanced recommendations
        result = await optimization_service.generate_ai_enhanced_recommendations(
            api_id=api_id,
            min_impact=min_impact,
        )
        
        return {
            "status": "success",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Failed to generate AI-enhanced recommendations: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI-enhanced recommendations: {str(e)}",
        )


@router.get(
    "/recommendations/{recommendation_id}/insights",
    summary="Get AI insights for recommendation",
)
async def get_recommendation_insights(
    recommendation_id: UUID,
) -> dict:
    """
    Get AI-generated insights for a specific recommendation.
    
    Args:
        recommendation_id: Recommendation UUID
        
    Returns:
        AI-generated insights
        
    Raises:
        HTTPException: If recommendation not found or insights fail
    """
    try:
        # Initialize repositories
        recommendation_repo = RecommendationRepository()
        
        # Get recommendation
        recommendation = recommendation_repo.get_recommendation(str(recommendation_id))
        
        if not recommendation:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Recommendation {recommendation_id} not found",
            )
        
        # Try to get LLM service
        try:
            from app.services.llm_service import LLMService
            from app.config import Settings
            settings = Settings()
            llm_service = LLMService(settings)
            
            # Generate insights
            insights = await llm_service.generate_optimization_recommendation({
                "response_time_p95": recommendation.estimated_impact.current_value,
                "response_time_p99": recommendation.estimated_impact.current_value * 1.5,
                "error_rate": 0.01,
                "throughput": 100,
                "availability": 99.5,
            })
            
            return {
                "status": "success",
                "recommendation_id": str(recommendation_id),
                "insights": insights,
            }
            
        except Exception as e:
            logger.warning(f"LLM insights unavailable: {e}")
            return {
                "status": "fallback",
                "recommendation_id": str(recommendation_id),
                "insights": {
                    "title": recommendation.title,
                    "description": recommendation.description,
                    "priority": recommendation.priority.value,
                    "estimated_impact": f"{recommendation.estimated_impact.improvement_percentage:.1f}%",
                },
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get recommendation insights: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recommendation insights: {str(e)}",
        )

# Made with Bob