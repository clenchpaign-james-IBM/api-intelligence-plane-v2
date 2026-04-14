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

router = APIRouter(tags=["APIs"])


# Response Models
class APIListResponse(BaseModel):
    """Response model for listing APIs."""
    
    items: list[API]
    total: int
    page: int
    page_size: int


@router.get(
    "/gateways/{gateway_id}/apis",
    response_model=APIListResponse,
    summary="List APIs for a specific gateway",
)
async def list_gateway_apis(
    gateway_id: UUID,
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status_filter: Optional[APIStatus] = Query(None, alias="status", description="Filter by status"),
    is_shadow: Optional[bool] = Query(None, description="Filter shadow APIs"),
    health_score_min: Optional[float] = Query(None, ge=0.0, le=1.0, description="Minimum health score"),
) -> APIListResponse:
    """
    List APIs for a specific gateway with optional filtering.
    
    Args:
        gateway_id: Gateway UUID (required)
        page: Page number (1-based)
        page_size: Number of items per page
        status_filter: Optional status filter
        is_shadow: Optional shadow API filter
        health_score_min: Optional minimum health score filter (0.0-1.0)
        
    Returns:
        Paginated list of APIs for the gateway
    """
    try:
        # Verify gateway exists
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        repo = APIRepository()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        # Build query based on filters - gateway_id is always required
        if health_score_min is not None:
            # Use OpenSearch query for health score filtering
            query = {
                "bool": {
                    "must": [
                        {
                            "range": {
                                "intelligence_metadata.health_score": {
                                    "gte": health_score_min
                                }
                            }
                        }
                    ],
                    "filter": [
                        {"term": {"gateway_id": str(gateway_id)}}
                    ]
                }
            }
            
            # Add additional filters
            if status_filter:
                query["bool"]["filter"].append({"term": {"status": status_filter.value}})
            if is_shadow is not None:
                query["bool"]["filter"].append({"term": {"intelligence_metadata.is_shadow": is_shadow}})
            
            apis, total = repo.search(query, size=page_size, from_=offset)
        elif is_shadow is not None:
            # Filter by shadow status within gateway
            query = {
                "bool": {
                    "filter": [
                        {"term": {"gateway_id": str(gateway_id)}},
                        {"term": {"intelligence_metadata.is_shadow": is_shadow}}
                    ]
                }
            }
            apis, total = repo.search(query, size=page_size, from_=offset)
        elif status_filter:
            # Filter by status within gateway
            query = {
                "bool": {
                    "filter": [
                        {"term": {"gateway_id": str(gateway_id)}},
                        {"term": {"status": status_filter.value}}
                    ]
                }
            }
            apis, total = repo.search(query, size=page_size, from_=offset)
        else:
            # Get all APIs for this gateway
            apis, total = repo.find_by_gateway(
                gateway_id=gateway_id,
                size=page_size,
                from_=offset,
            )
        
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
            detail=f"Failed to list APIs: {str(e)}"
        )


@router.get(
    "/gateways/{gateway_id}/apis/search",
    response_model=dict,
    summary="Search APIs within a gateway using full-text search",
)
async def search_gateway_apis(
    gateway_id: UUID,
    q: str = Query(..., description="Search query"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    status_filter: Optional[APIStatus] = Query(None, alias="status", description="Filter by status"),
    is_shadow: Optional[bool] = Query(None, description="Filter shadow APIs"),
) -> dict:
    """
    Search APIs within a specific gateway using OpenSearch full-text search.
    
    Uses multi_match query with fuzzy matching for better results.
    Searches across name, base_path, description, and tags fields.
    
    Args:
        gateway_id: Gateway UUID (required)
        q: Search query string
        limit: Maximum number of results (1-1000)
        status_filter: Optional status filter
        is_shadow: Optional shadow API filter
        
    Returns:
        dict: Search results with total count
    """
    try:
        # Verify gateway exists
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        repo = APIRepository()
        
        # Build OpenSearch multi_match query with gateway filter
        query = {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": q,
                            "fields": [
                                "name^3",           # Highest weight
                                "base_path^2",      # Medium weight
                                "description",      # Normal weight
                                "tags"              # Normal weight
                            ],
                            "type": "best_fields",
                            "fuzziness": "AUTO",    # Fuzzy matching for typos
                            "operator": "or"
                        }
                    }
                ],
                "filter": [
                    {"term": {"gateway_id": str(gateway_id)}}
                ]
            }
        }
        
        # Add additional filters
        if status_filter:
            query["bool"]["filter"].append({"term": {"status": status_filter.value}})
        if is_shadow is not None:
            query["bool"]["filter"].append({"term": {"intelligence_metadata.is_shadow": is_shadow}})
        
        # Execute search
        results, total = repo.search(query, size=limit)
        
        return {
            "results": results,
            "total": total,
            "query": q
        }
        
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list APIs: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/apis/{api_id}",
    response_model=API,
    summary="Get API details",
)
async def get_gateway_api(gateway_id: UUID, api_id: UUID) -> API:
    """
    Get details of a specific API within a gateway.
    
    Args:
        gateway_id: Gateway UUID (required)
        api_id: API UUID
        
    Returns:
        API details
        
    Raises:
        HTTPException: If gateway or API not found
    """
    try:
        # Verify gateway exists
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        repo = APIRepository()
        api = repo.get(str(api_id))
        
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found",
            )
        
        # Verify API belongs to the gateway
        if str(api.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found in gateway {gateway_id}",
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
    "/gateways/{gateway_id}/apis/{api_id}/security-policies",
    response_model=list[PolicyAction],
    summary="Get API security policies",
)
async def get_gateway_api_security_policies(gateway_id: UUID, api_id: UUID) -> list[PolicyAction]:
    """
    Get security-related policy actions for a specific API within a gateway.
    
    This endpoint derives security policies from the API's policy_actions field,
    filtering for security-related action types like authentication, authorization,
    rate limiting, TLS, validation, etc.
    
    Args:
        gateway_id: Gateway UUID (required)
        api_id: API UUID
        
    Returns:
        List of security-related PolicyAction objects
        
    Raises:
        HTTPException: If gateway or API not found
    """
    try:
        # Verify gateway exists
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        repo = APIRepository()
        
        # Get the API
        api = repo.get(str(api_id))
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found",
            )
        
        # Verify API belongs to the gateway
        if str(api.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {api_id} not found in gateway {gateway_id}",
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