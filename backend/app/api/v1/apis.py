"""
API Endpoints

REST API endpoints for managing discovered APIs.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel

from app.db.repositories.api_repository import APIRepository
from app.models.base.api import API, APIStatus, PolicyAction

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/apis", tags=["APIs"])


# Response Models
class APIListResponse(BaseModel):
    """Response model for listing APIs."""
    
    items: list[API]
    total: int
    page: int
    page_size: int


@router.get(
    "",
    response_model=APIListResponse,
    summary="List all discovered APIs",
)
async def list_apis(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    gateway_id: Optional[UUID] = Query(None, description="Filter by gateway ID"),
    status_filter: Optional[APIStatus] = Query(None, alias="status", description="Filter by status"),
    is_shadow: Optional[bool] = Query(None, description="Filter shadow APIs"),
) -> APIListResponse:
    """
    List all discovered APIs with optional filtering.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        gateway_id: Optional gateway ID filter
        status_filter: Optional status filter
        is_shadow: Optional shadow API filter
        
    Returns:
        Paginated list of APIs
    """
    try:
        repo = APIRepository()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query based on filters
        if gateway_id:
            # Filter by gateway
            apis, total = repo.find_by_gateway(
                gateway_id=gateway_id,
                size=page_size,
                from_=offset,
            )
        elif is_shadow is not None:
            if is_shadow:
                # Get shadow APIs
                apis, total = repo.find_shadow_apis(size=page_size, from_=offset)
            else:
                # Get non-shadow APIs - use nested path for intelligence_metadata
                query = {"term": {"intelligence_metadata.is_shadow": False}}
                apis, total = repo.search(query, size=page_size, from_=offset)
        elif status_filter:
            # Filter by status
            apis, total = repo.find_by_status(
                status=status_filter,
                size=page_size,
                from_=offset,
            )
        else:
            # Get all APIs
            apis, total = repo.list_all(size=page_size, from_=offset)
        
        return APIListResponse(
            items=apis,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"Failed to list APIs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list APIs: {str(e)}",
        )


@router.get(
    "/{api_id}",
    response_model=API,
    summary="Get API details",
)
async def get_api(api_id: UUID) -> API:
    """
    Get details of a specific API.
    
    Args:
        api_id: API UUID
        
    Returns:
        API details
        
    Raises:
        HTTPException: If API not found
    """
    try:
        repo = APIRepository()
        api = repo.get(str(api_id))
        
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found",
            )
        
        return api
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get API {api_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get API: {str(e)}",
        )


@router.get(
    "/{api_id}/security-policies",
    response_model=list[PolicyAction],
    summary="Get API security policies",
)
async def get_api_security_policies(api_id: UUID) -> list[PolicyAction]:
    """
    Get security-related policy actions for a specific API.
    
    This endpoint derives security policies from the API's policy_actions field,
    filtering for security-related action types like authentication, authorization,
    rate limiting, TLS, validation, etc.
    
    Args:
        api_id: API UUID
        
    Returns:
        List of security-related PolicyAction objects
        
    Raises:
        HTTPException: If API not found
    """
    try:
        repo = APIRepository()
        
        # Get the API
        api = repo.get(str(api_id))
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found",
            )
        
        # Use the repository method to derive security policies
        security_policies = repo.derive_security_policies(api)
        
        return security_policies
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get security policies for API {api_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security policies: {str(e)}",
        )


# Made with Bob