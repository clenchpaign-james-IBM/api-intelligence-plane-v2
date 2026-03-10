"""
Rate Limiting API Endpoints

REST API endpoints for intelligent rate limiting policy management.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status as http_status
from pydantic import BaseModel, Field

from app.db.repositories.rate_limit_repository import RateLimitPolicyRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.rate_limit_service import RateLimitService
from app.models.rate_limit import (
    RateLimitPolicy,
    PolicyType,
    PolicyStatus,
    EnforcementAction,
    LimitThresholds,
    AdaptationParameters,
    PriorityRule,
    ConsumerTier,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Rate Limiting"])


# Request Models
class LimitThresholdsRequest(BaseModel):
    """Request model for rate limit thresholds."""
    
    requests_per_second: Optional[int] = Field(None, ge=0)
    requests_per_minute: Optional[int] = Field(None, ge=0)
    requests_per_hour: Optional[int] = Field(None, ge=0)
    concurrent_requests: Optional[int] = Field(None, ge=0)


class AdaptationParametersRequest(BaseModel):
    """Request model for adaptation parameters."""
    
    learning_rate: float = Field(..., gt=0, le=1)
    adjustment_frequency: int = Field(..., gt=0)
    min_threshold: Optional[int] = Field(None, ge=0)
    max_threshold: Optional[int] = Field(None, ge=0)


class PriorityRuleRequest(BaseModel):
    """Request model for priority rules."""
    
    tier: str
    multiplier: float = Field(..., gt=0)
    guaranteed_throughput: int = Field(..., ge=0)
    burst_multiplier: float = Field(..., gt=0)


class ConsumerTierRequest(BaseModel):
    """Request model for consumer tiers."""
    
    tier_name: str
    tier_level: int = Field(..., ge=1)
    rate_multiplier: float = Field(..., gt=0)
    priority_score: int = Field(..., ge=0)


class CreateRateLimitPolicyRequest(BaseModel):
    """Request model for creating a rate limit policy."""
    
    api_id: UUID
    policy_name: str = Field(..., min_length=1, max_length=255)
    policy_type: PolicyType
    limit_thresholds: LimitThresholdsRequest
    enforcement_action: EnforcementAction = EnforcementAction.THROTTLE
    priority_rules: Optional[list[PriorityRuleRequest]] = None
    burst_allowance: Optional[int] = Field(None, ge=0)
    adaptation_parameters: Optional[AdaptationParametersRequest] = None
    consumer_tiers: Optional[list[ConsumerTierRequest]] = None


# Response Models
class LimitThresholdsResponse(BaseModel):
    """Response model for rate limit thresholds."""
    
    requests_per_second: Optional[int]
    requests_per_minute: Optional[int]
    requests_per_hour: Optional[int]
    concurrent_requests: Optional[int]


class AdaptationParametersResponse(BaseModel):
    """Response model for adaptation parameters."""
    
    learning_rate: float
    adjustment_frequency: int
    min_threshold: Optional[int]
    max_threshold: Optional[int]


class PriorityRuleResponse(BaseModel):
    """Response model for priority rules."""
    
    tier: str
    multiplier: float
    guaranteed_throughput: int
    burst_multiplier: float


class ConsumerTierResponse(BaseModel):
    """Response model for consumer tiers."""
    
    tier_name: str
    tier_level: int
    rate_multiplier: float
    priority_score: int


class RateLimitPolicyResponse(BaseModel):
    """Response model for a rate limit policy."""
    
    id: str
    api_id: str
    policy_name: str
    policy_type: str
    status: str
    limit_thresholds: LimitThresholdsResponse
    enforcement_action: str
    priority_rules: Optional[list[PriorityRuleResponse]] = None
    burst_allowance: Optional[int] = None
    adaptation_parameters: Optional[AdaptationParametersResponse] = None
    consumer_tiers: Optional[list[ConsumerTierResponse]] = None
    applied_at: Optional[str] = None
    last_adjusted_at: Optional[str] = None
    effectiveness_score: Optional[float] = None
    created_at: str
    updated_at: str


class RateLimitPolicyListResponse(BaseModel):
    """Response model for rate limit policy list."""
    
    items: list[RateLimitPolicyResponse]
    total: int
    page: int
    page_size: int


class PolicySuggestionResponse(BaseModel):
    """Response model for policy suggestions."""
    
    api_id: str
    api_name: str
    suggested_policy_type: str
    suggested_thresholds: dict
    adaptation_parameters: Optional[dict]
    burst_allowance: int
    enforcement_action: str
    analysis_summary: dict


class EffectivenessAnalysisResponse(BaseModel):
    """Response model for effectiveness analysis."""
    
    policy_id: str
    policy_name: str
    effectiveness_score: float
    status: str
    metrics: dict
    component_scores: dict
    recommendations: list[str]
    analysis_period: dict


def _convert_policy_to_response(policy: RateLimitPolicy) -> RateLimitPolicyResponse:
    """Convert RateLimitPolicy model to response model."""
    return RateLimitPolicyResponse(
        id=str(policy.id),
        api_id=str(policy.api_id),
        policy_name=policy.policy_name,
        policy_type=policy.policy_type.value,
        status=policy.status.value,
        limit_thresholds=LimitThresholdsResponse(
            requests_per_second=policy.limit_thresholds.requests_per_second,
            requests_per_minute=policy.limit_thresholds.requests_per_minute,
            requests_per_hour=policy.limit_thresholds.requests_per_hour,
            concurrent_requests=policy.limit_thresholds.concurrent_requests,
        ),
        enforcement_action=policy.enforcement_action.value,
        priority_rules=[
            PriorityRuleResponse(
                tier=rule.tier,
                multiplier=rule.multiplier,
                guaranteed_throughput=rule.guaranteed_throughput,
                burst_multiplier=rule.burst_multiplier,
            )
            for rule in policy.priority_rules
        ] if policy.priority_rules else None,
        burst_allowance=policy.burst_allowance,
        adaptation_parameters=AdaptationParametersResponse(
            learning_rate=policy.adaptation_parameters.learning_rate,
            adjustment_frequency=policy.adaptation_parameters.adjustment_frequency,
            min_threshold=policy.adaptation_parameters.min_threshold,
            max_threshold=policy.adaptation_parameters.max_threshold,
        ) if policy.adaptation_parameters else None,
        consumer_tiers=[
            ConsumerTierResponse(
                tier_name=tier.tier_name,
                tier_level=tier.tier_level,
                rate_multiplier=tier.rate_multiplier,
                priority_score=tier.priority_score,
            )
            for tier in policy.consumer_tiers
        ] if policy.consumer_tiers else None,
        applied_at=policy.applied_at.isoformat() if policy.applied_at else None,
        last_adjusted_at=policy.last_adjusted_at.isoformat() if policy.last_adjusted_at else None,
        effectiveness_score=policy.effectiveness_score,
        created_at=policy.created_at.isoformat(),
        updated_at=policy.updated_at.isoformat(),
    )


@router.get(
    "/rate-limits",
    response_model=RateLimitPolicyListResponse,
    summary="List rate limit policies",
)
async def list_rate_limit_policies(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    status: Optional[PolicyStatus] = Query(None, description="Filter by status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> RateLimitPolicyListResponse:
    """
    List rate limit policies with optional filters.
    
    Args:
        api_id: Filter by API ID
        status: Filter by policy status
        page: Page number (1-indexed)
        page_size: Items per page
        
    Returns:
        Paginated list of rate limit policies
    """
    try:
        # Initialize repositories and service
        rate_limit_repo = RateLimitPolicyRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        service = RateLimitService(rate_limit_repo, metrics_repo, api_repo)
        
        # Get policies
        policies, total = service.list_policies(
            api_id=api_id,
            status=status,
            page=page,
            page_size=page_size,
        )
        
        # Convert to response models
        policy_responses = [_convert_policy_to_response(p) for p in policies]
        
        return RateLimitPolicyListResponse(
            items=policy_responses,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"Failed to list rate limit policies: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list rate limit policies: {str(e)}",
        )


@router.post(
    "/rate-limits",
    response_model=RateLimitPolicyResponse,
    status_code=http_status.HTTP_201_CREATED,
    summary="Create rate limit policy",
)
async def create_rate_limit_policy(
    request: CreateRateLimitPolicyRequest,
) -> RateLimitPolicyResponse:
    """
    Create a new rate limit policy.
    
    Args:
        request: Policy creation request
        
    Returns:
        Created rate limit policy
    """
    try:
        # Initialize repositories and service
        rate_limit_repo = RateLimitPolicyRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        service = RateLimitService(rate_limit_repo, metrics_repo, api_repo)
        
        # Convert request models to domain models
        limit_thresholds = LimitThresholds(
            requests_per_second=request.limit_thresholds.requests_per_second,
            requests_per_minute=request.limit_thresholds.requests_per_minute,
            requests_per_hour=request.limit_thresholds.requests_per_hour,
            concurrent_requests=request.limit_thresholds.concurrent_requests,
        )
        
        priority_rules = None
        if request.priority_rules:
            priority_rules = [
                PriorityRule(
                    tier=rule.tier,
                    multiplier=rule.multiplier,
                    guaranteed_throughput=rule.guaranteed_throughput,
                    burst_multiplier=rule.burst_multiplier,
                )
                for rule in request.priority_rules
            ]
        
        adaptation_parameters = None
        if request.adaptation_parameters:
            adaptation_parameters = AdaptationParameters(
                learning_rate=request.adaptation_parameters.learning_rate,
                adjustment_frequency=request.adaptation_parameters.adjustment_frequency,
                min_threshold=request.adaptation_parameters.min_threshold,
                max_threshold=request.adaptation_parameters.max_threshold,
            )
        
        consumer_tiers = None
        if request.consumer_tiers:
            consumer_tiers = [
                ConsumerTier(
                    tier_name=tier.tier_name,
                    tier_level=tier.tier_level,
                    rate_multiplier=tier.rate_multiplier,
                    priority_score=tier.priority_score,
                )
                for tier in request.consumer_tiers
            ]
        
        # Create policy
        policy = service.create_policy(
            api_id=request.api_id,
            policy_name=request.policy_name,
            policy_type=request.policy_type,
            limit_thresholds=limit_thresholds,
            enforcement_action=request.enforcement_action,
            priority_rules=priority_rules,
            burst_allowance=request.burst_allowance,
            adaptation_parameters=adaptation_parameters,
            consumer_tiers=consumer_tiers,
        )
        
        return _convert_policy_to_response(policy)
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to create rate limit policy: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rate limit policy: {str(e)}",
        )


@router.get(
    "/rate-limits/{policy_id}",
    response_model=RateLimitPolicyResponse,
    summary="Get rate limit policy",
)
async def get_rate_limit_policy(
    policy_id: UUID,
) -> RateLimitPolicyResponse:
    """
    Get a specific rate limit policy by ID.
    
    Args:
        policy_id: Policy UUID
        
    Returns:
        Rate limit policy details
    """
    try:
        rate_limit_repo = RateLimitPolicyRepository()
        
        policy = rate_limit_repo.get_by_id(policy_id)
        if not policy:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Rate limit policy {policy_id} not found",
            )
        
        return _convert_policy_to_response(policy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get rate limit policy: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit policy: {str(e)}",
        )


@router.post(
    "/rate-limits/{policy_id}/activate",
    response_model=RateLimitPolicyResponse,
    summary="Activate rate limit policy",
)
async def activate_rate_limit_policy(
    policy_id: UUID,
) -> RateLimitPolicyResponse:
    """
    Activate a rate limit policy.
    
    Args:
        policy_id: Policy UUID to activate
        
    Returns:
        Activated rate limit policy
    """
    try:
        rate_limit_repo = RateLimitPolicyRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        service = RateLimitService(rate_limit_repo, metrics_repo, api_repo)
        
        policy = service.activate_policy(policy_id)
        if not policy:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Rate limit policy {policy_id} not found",
            )
        
        return _convert_policy_to_response(policy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate rate limit policy: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate rate limit policy: {str(e)}",
        )


@router.post(
    "/rate-limits/{policy_id}/deactivate",
    response_model=RateLimitPolicyResponse,
    summary="Deactivate rate limit policy",
)
async def deactivate_rate_limit_policy(
    policy_id: UUID,
) -> RateLimitPolicyResponse:
    """
    Deactivate a rate limit policy.
    
    Args:
        policy_id: Policy UUID to deactivate
        
    Returns:
        Deactivated rate limit policy
    """
    try:
        rate_limit_repo = RateLimitPolicyRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        service = RateLimitService(rate_limit_repo, metrics_repo, api_repo)
        
        policy = service.deactivate_policy(policy_id)
        if not policy:
            raise HTTPException(
                status_code=http_status.HTTP_404_NOT_FOUND,
                detail=f"Rate limit policy {policy_id} not found",
            )
        
        return _convert_policy_to_response(policy)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate rate limit policy: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to deactivate rate limit policy: {str(e)}",
        )


@router.get(
    "/rate-limits/suggest/{api_id}",
    response_model=PolicySuggestionResponse,
    summary="Get rate limit policy suggestion",
)
async def suggest_rate_limit_policy(
    api_id: UUID,
) -> PolicySuggestionResponse:
    """
    Get intelligent rate limit policy suggestion for an API.
    
    Args:
        api_id: API UUID
        
    Returns:
        Suggested policy parameters based on traffic analysis
    """
    try:
        rate_limit_repo = RateLimitPolicyRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        service = RateLimitService(rate_limit_repo, metrics_repo, api_repo)
        
        suggestion = service.suggest_policy_for_api(api_id)
        
        return PolicySuggestionResponse(**suggestion)
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to suggest rate limit policy: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest rate limit policy: {str(e)}",
        )


@router.get(
    "/rate-limits/{policy_id}/effectiveness",
    response_model=EffectivenessAnalysisResponse,
    summary="Analyze rate limit policy effectiveness",
)
async def analyze_rate_limit_effectiveness(
    policy_id: UUID,
    analysis_period_hours: int = Query(24, ge=1, le=720, description="Analysis period in hours"),
) -> EffectivenessAnalysisResponse:
    """
    Analyze the effectiveness of a rate limit policy.
    
    Args:
        policy_id: Policy UUID
        analysis_period_hours: Hours to analyze (default: 24)
        
    Returns:
        Effectiveness analysis with metrics and recommendations
    """
    try:
        rate_limit_repo = RateLimitPolicyRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        service = RateLimitService(rate_limit_repo, metrics_repo, api_repo)
        
        analysis = service.analyze_policy_effectiveness(
            policy_id=policy_id,
            analysis_period_hours=analysis_period_hours,
        )
        
        return EffectivenessAnalysisResponse(**analysis)
        
    except ValueError as e:
        logger.warning(f"Invalid request: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to analyze rate limit effectiveness: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to analyze rate limit effectiveness: {str(e)}",
        )


# Made with Bob