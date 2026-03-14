"""
Predictions API Endpoints

REST API endpoints for API failure predictions.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status as http_status
from pydantic import BaseModel, Field

from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.prediction_service import PredictionService
from app.models.prediction import (
    Prediction,
    PredictionSeverity,
    PredictionStatus,
    ContributingFactor,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Predictions"])


# Response Models
class ContributingFactorResponse(BaseModel):
    """Response model for contributing factor."""
    
    factor: str
    current_value: float
    threshold: float
    trend: str
    weight: float


class PredictionResponse(BaseModel):
    """Response model for a single prediction."""
    
    id: str
    api_id: str
    api_name: Optional[str] = None
    prediction_type: str
    predicted_at: str
    predicted_time: str
    confidence_score: float
    severity: str
    status: str
    contributing_factors: list[ContributingFactorResponse]
    recommended_actions: list[str]
    actual_outcome: Optional[str] = None
    actual_time: Optional[str] = None
    accuracy_score: Optional[float] = None
    model_version: str
    metadata: Optional[dict] = None
    created_at: str
    updated_at: str


class PredictionListResponse(BaseModel):
    """Response model for prediction list."""
    
    predictions: list[PredictionResponse]
    total: int
    page: int
    page_size: int


@router.get(
    "/predictions",
    response_model=PredictionListResponse,
    summary="List failure predictions",
)
async def list_predictions(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    severity: Optional[PredictionSeverity] = Query(None, description="Filter by severity"),
    status: Optional[PredictionStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> PredictionListResponse:
    """
    List failure predictions with optional filters.
    
    Args:
        api_id: Filter by API ID
        severity: Filter by severity level
        status: Filter by prediction status
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        List of predictions with pagination info
        
    Raises:
        HTTPException: If prediction retrieval fails
    """
    try:
        # Initialize repository
        prediction_repo = PredictionRepository()
        
        # Get predictions with filters
        result = prediction_repo.list_predictions(
            api_id=str(api_id) if api_id else None,
            severity=severity,
            status=status,
            page=page,
            page_size=page_size,
        )
        
        # Convert to response models
        predictions_response = [
            PredictionResponse(
                id=str(p.id),
                api_id=str(p.api_id),
                api_name=p.api_name,
                prediction_type=p.prediction_type.value,
                predicted_at=p.predicted_at.isoformat(),
                predicted_time=p.predicted_time.isoformat(),
                confidence_score=p.confidence_score,
                severity=p.severity.value,
                status=p.status.value,
                contributing_factors=[
                    ContributingFactorResponse(
                        factor=f.factor,
                        current_value=f.current_value,
                        threshold=f.threshold,
                        trend=f.trend,
                        weight=f.weight,
                    )
                    for f in p.contributing_factors
                ],
                recommended_actions=p.recommended_actions,
                actual_outcome=p.actual_outcome.value if p.actual_outcome else None,
                actual_time=p.actual_time.isoformat() if p.actual_time else None,
                accuracy_score=p.accuracy_score,
                model_version=p.model_version,
                metadata=p.metadata,
                created_at=p.created_at.isoformat(),
                updated_at=p.updated_at.isoformat(),
            )
            for p in result["predictions"]
        ]
        
        return PredictionListResponse(
            predictions=predictions_response,
            total=result["total"],
            page=result["page"],
            page_size=result["page_size"],
        )
        
    except Exception as e:
        logger.error(f"Failed to list predictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve predictions: {str(e)}",
        )


@router.get(
    "/predictions/{prediction_id}",
    response_model=PredictionResponse,
    summary="Get prediction details",
)
async def get_prediction(
    prediction_id: UUID,
) -> PredictionResponse:
    """
    Get details for a specific prediction.
    
    Args:
        prediction_id: Prediction UUID
        
    Returns:
        Prediction details
        
    Raises:
        HTTPException: If prediction not found
    """
    try:
        # Initialize repository
        prediction_repo = PredictionRepository()
        
        # Get prediction
        prediction = prediction_repo.get_prediction(str(prediction_id))
        
        if not prediction:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Prediction {prediction_id} not found",
            )
        
        # Enrich with API name
        api_repo = APIRepository()
        try:
            api = api_repo.get(str(prediction.api_id))
            api_name = api.name if api else None
        except Exception:
            api_name = None
        
        # Convert to response model
        return PredictionResponse(
            id=str(prediction.id),
            api_id=str(prediction.api_id),
            api_name=api_name or f"API {str(prediction.api_id)[:8]}",
            prediction_type=prediction.prediction_type.value,
            predicted_at=prediction.predicted_at.isoformat(),
            predicted_time=prediction.predicted_time.isoformat(),
            confidence_score=prediction.confidence_score,
            severity=prediction.severity.value,
            status=prediction.status.value,
            contributing_factors=[
                ContributingFactorResponse(
                    factor=f.factor,
                    current_value=f.current_value,
                    threshold=f.threshold,
                    trend=f.trend,
                    weight=f.weight,
                )
                for f in prediction.contributing_factors
            ],
            recommended_actions=prediction.recommended_actions,
            actual_outcome=prediction.actual_outcome.value if prediction.actual_outcome else None,
            actual_time=prediction.actual_time.isoformat() if prediction.actual_time else None,
            accuracy_score=prediction.accuracy_score,
            model_version=prediction.model_version,
            created_at=prediction.created_at.isoformat(),
            updated_at=prediction.updated_at.isoformat(),
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction {prediction_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve prediction: {str(e)}",
        )


@router.post(
    "/predictions/generate",
    status_code=http_status.HTTP_202_ACCEPTED,
    summary="Trigger prediction generation",
)
async def generate_predictions(
    api_id: Optional[UUID] = Query(None, description="Generate for specific API (or all if not provided)"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"),
    use_ai: bool = Query(False, description="Use AI-enhanced prediction generation"),
) -> dict:
    """
    Trigger prediction generation for APIs.
    
    Args:
        api_id: Optional API ID to generate predictions for (generates for all if not provided)
        min_confidence: Minimum confidence threshold (0-1)
        
    Returns:
        Generation status
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        # Initialize services
        prediction_repo = PredictionRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        
        prediction_service = PredictionService(
            prediction_repository=prediction_repo,
            metrics_repository=metrics_repo,
            api_repository=api_repo,
        )
        
        if api_id:
            # Generate for specific API
            if use_ai:
                # Try to get LLM service for AI-enhanced generation
                try:
                    from app.services.llm_service import LLMService
                    from app.config import Settings
                    settings = Settings()
                    llm_service = LLMService(settings)
                    prediction_service.llm_service = llm_service
                except Exception as e:
                    logger.warning(f"LLM service unavailable, using rule-based: {e}")
                
                result = await prediction_service.generate_ai_enhanced_predictions(
                    api_id=api_id,
                    min_confidence=min_confidence,
                )
                
                return {
                    "status": "accepted",
                    "message": f"Generated AI-enhanced predictions for API {api_id}",
                    "result": result,
                }
            else:
                predictions = prediction_service.generate_predictions_for_api(
                    api_id=api_id,
                    min_confidence=min_confidence,
                )
                
                return {
                    "status": "accepted",
                    "message": f"Generated {len(predictions)} predictions for API {api_id}",
                    "predictions_generated": len(predictions),
                }
        else:
            # Generate for all APIs
            result = prediction_service.generate_predictions_for_all_apis(
                min_confidence=min_confidence,
            )
            
            return {
                "status": "accepted",
                "message": f"Generated {result['predictions_generated']} predictions for {result['apis_analyzed']} APIs",
                "result": result,
            }
        
    except Exception as e:
        logger.error(f"Failed to generate predictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate predictions: {str(e)}",
        )


@router.get(
    "/predictions/stats/accuracy",
    summary="Get prediction accuracy statistics",
)
async def get_prediction_accuracy_stats(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    days: int = Query(30, ge=1, le=90, description="Number of days to look back"),
) -> dict:
    """
    Get prediction accuracy statistics.
    
    Args:
        api_id: Optional API ID filter
        days: Number of days to look back (1-90)
        
    Returns:
        Accuracy statistics
        
    Raises:
        HTTPException: If retrieval fails
    """
    try:
        # Initialize repository
        prediction_repo = PredictionRepository()
        
        # Get accuracy stats
        stats = prediction_repo.get_prediction_accuracy_stats(
            api_id=str(api_id) if api_id else None,
            days=days,
        )
        
        return {
            "status": "success",
            "stats": stats,
            "period_days": days,
        }
        
    except Exception as e:
        logger.error(f"Failed to get accuracy stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve accuracy statistics: {str(e)}",
        )

@router.post(
    "/predictions/ai-enhanced",
    summary="Generate AI-enhanced predictions",
)
async def generate_ai_enhanced_predictions(
    api_id: UUID = Query(..., description="API ID to generate predictions for"),
    min_confidence: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold"),
) -> dict:
    """
    Generate AI-enhanced predictions with LLM analysis.
    
    Args:
        api_id: API ID to generate predictions for
        min_confidence: Minimum confidence threshold (0-1)
        
    Returns:
        AI-enhanced predictions with analysis
        
    Raises:
        HTTPException: If generation fails
    """
    try:
        # Initialize services
        prediction_repo = PredictionRepository()
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
        
        prediction_service = PredictionService(
            prediction_repository=prediction_repo,
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            llm_service=llm_service,
        )
        
        # Generate AI-enhanced predictions
        result = await prediction_service.generate_ai_enhanced_predictions(
            api_id=api_id,
            min_confidence=min_confidence,
        )
        
        return {
            "status": "success",
            "result": result,
        }
        
    except Exception as e:
        logger.error(f"Failed to generate AI-enhanced predictions: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate AI-enhanced predictions: {str(e)}",
        )


@router.get(
    "/predictions/{prediction_id}/explanation",
    summary="Get AI explanation for prediction",
)
async def get_prediction_explanation(
    prediction_id: UUID,
) -> dict:
    """
    Get AI-generated explanation for a specific prediction.
    
    Args:
        prediction_id: Prediction UUID
        
    Returns:
        AI-generated explanation
        
    Raises:
        HTTPException: If prediction not found or explanation fails
    """
    try:
        # Initialize repositories
        prediction_repo = PredictionRepository()
        
        # Get prediction
        prediction = prediction_repo.get_prediction(str(prediction_id))
        
        if not prediction:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Prediction {prediction_id} not found",
            )
        
        # Try to get LLM service
        try:
            from app.services.llm_service import LLMService
            from app.config import Settings
            settings = Settings()
            llm_service = LLMService(settings)
            
            # Generate explanation
            explanation = await llm_service.generate_prediction_explanation({
                "prediction_type": prediction.prediction_type.value,
                "confidence_score": prediction.confidence_score,
                "severity": prediction.severity.value,
                "contributing_factors": [
                    {
                        "factor": f.factor,
                        "current_value": f.current_value,
                        "threshold": f.threshold,
                        "trend": f.trend,
                    }
                    for f in prediction.contributing_factors
                ],
                "recommended_actions": prediction.recommended_actions,
            })
            
            return {
                "status": "success",
                "prediction_id": str(prediction_id),
                "explanation": explanation,
            }
            
        except Exception as e:
            logger.warning(f"LLM explanation unavailable: {e}")
            return {
                "status": "fallback",
                "prediction_id": str(prediction_id),
                "explanation": f"This is a {prediction.severity.value} severity {prediction.prediction_type.value} prediction with {prediction.confidence_score:.1%} confidence.",
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get prediction explanation: {e}", exc_info=True)
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get prediction explanation: {str(e)}",
        )

# Made with Bob
