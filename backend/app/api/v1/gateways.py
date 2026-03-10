"""
Gateway API Endpoints

REST API endpoints for managing API Gateways.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db.repositories.gateway_repository import GatewayRepository
from app.models.gateway import Gateway, GatewayStatus, GatewayVendor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gateways", tags=["Gateways"])


# Request/Response Models
class CreateGatewayRequest(BaseModel):
    """Request model for creating a new Gateway."""
    
    name: str = Field(..., description="Gateway name")
    vendor: GatewayVendor = Field(..., description="Gateway vendor")
    version: Optional[str] = Field(None, description="Gateway version")
    connection_url: str = Field(..., description="Gateway API endpoint URL")
    connection_type: str = Field(default="rest_api", description="Connection method")
    credential_type: str = Field(default="api_key", description="Credential type")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    token: Optional[str] = Field(None, description="Bearer token for authentication")
    capabilities: list[str] = Field(default_factory=list, description="Gateway capabilities")
    configuration: Optional[dict] = Field(None, description="Vendor-specific configuration")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class UpdateGatewayRequest(BaseModel):
    """Request model for updating a Gateway."""
    
    name: Optional[str] = Field(None, description="Gateway name")
    version: Optional[str] = Field(None, description="Gateway version")
    connection_url: Optional[str] = Field(None, description="Gateway API endpoint URL")
    connection_type: Optional[str] = Field(None, description="Connection method")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    username: Optional[str] = Field(None, description="Username for authentication")
    password: Optional[str] = Field(None, description="Password for authentication")
    token: Optional[str] = Field(None, description="Bearer token for authentication")
    capabilities: Optional[list[str]] = Field(None, description="Gateway capabilities")
    status: Optional[GatewayStatus] = Field(None, description="Gateway status")
    configuration: Optional[dict] = Field(None, description="Vendor-specific configuration")
    metadata: Optional[dict] = Field(None, description="Additional metadata")


class GatewayListResponse(BaseModel):
    """Response model for listing Gateways."""
    
    items: list[Gateway]
    total: int
    page: int
    page_size: int


@router.post(
    "",
    response_model=Gateway,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new API Gateway",
)
async def create_gateway(request: CreateGatewayRequest) -> Gateway:
    """
    Register a new API Gateway.
    
    Args:
        request: Gateway creation request
        
    Returns:
        Created Gateway
        
    Raises:
        HTTPException: If gateway creation fails
    """
    try:
        repo = GatewayRepository()
        
        # Import required types
        from app.models.gateway import GatewayCredentials, ConnectionType
        from pydantic import HttpUrl
        
        # Build credentials
        credentials = GatewayCredentials(
            type=request.credential_type,
            username=request.username,
            password=request.password,
            api_key=request.api_key,
            token=request.token,
        )
        
        # Create Gateway model
        gateway = Gateway(
            name=request.name,
            vendor=request.vendor,
            version=request.version,
            connection_url=HttpUrl(request.connection_url),
            connection_type=ConnectionType(request.connection_type),
            credentials=credentials,
            capabilities=request.capabilities if request.capabilities else ["discovery"],
            status=GatewayStatus.DISCONNECTED,  # Initial status
            last_connected_at=None,
            last_error=None,
            api_count=0,
            configuration=request.configuration,
            metadata=request.metadata,
        )
        
        # Save to database
        created_gateway = repo.create(gateway)
        
        logger.info(f"Created gateway: {created_gateway.id} ({created_gateway.name})")
        return created_gateway
        
    except Exception as e:
        logger.error(f"Failed to create gateway: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create gateway: {str(e)}",
        )


@router.get(
    "",
    response_model=GatewayListResponse,
    summary="List all connected API Gateways",
)
async def list_gateways(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Page size"),
    status_filter: Optional[GatewayStatus] = Query(None, alias="status", description="Filter by status"),
) -> GatewayListResponse:
    """
    List all registered API Gateways with optional filtering.
    
    Args:
        page: Page number (1-based)
        page_size: Number of items per page
        status_filter: Optional status filter
        
    Returns:
        Paginated list of Gateways
    """
    try:
        repo = GatewayRepository()
        
        # Calculate offset
        offset = (page - 1) * page_size
        
        if status_filter:
            # Filter by status
            gateways, total = repo.find_by_status(
                status=status_filter,
                size=page_size,
                from_=offset,
            )
        else:
            # Get all gateways
            gateways, total = repo.list_all(size=page_size, from_=offset)
        
        return GatewayListResponse(
            items=gateways,
            total=total,
            page=page,
            page_size=page_size,
        )
        
    except Exception as e:
        logger.error(f"Failed to list gateways: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list gateways: {str(e)}",
        )


@router.get(
    "/{gateway_id}",
    response_model=Gateway,
    summary="Get gateway details",
)
async def get_gateway(gateway_id: UUID) -> Gateway:
    """
    Get details of a specific Gateway.
    
    Args:
        gateway_id: Gateway UUID
        
    Returns:
        Gateway details
        
    Raises:
        HTTPException: If gateway not found
    """
    try:
        repo = GatewayRepository()
        gateway = repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        return gateway
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get gateway {gateway_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get gateway: {str(e)}",
        )


@router.put(
    "/{gateway_id}",
    response_model=Gateway,
    summary="Update gateway configuration",
)
async def update_gateway(
    gateway_id: UUID,
    request: UpdateGatewayRequest,
) -> Gateway:
    """
    Update Gateway configuration.
    
    Args:
        gateway_id: Gateway UUID
        request: Gateway update request
        
    Returns:
        Updated Gateway
        
    Raises:
        HTTPException: If gateway not found or update fails
    """
    try:
        repo = GatewayRepository()
        
        # Check if gateway exists
        existing_gateway = repo.get(str(gateway_id))
        if not existing_gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Build updates dictionary (only include provided fields)
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.version is not None:
            updates["version"] = request.version
        if request.connection_url is not None:
            updates["connection_url"] = request.connection_url
        if request.connection_type is not None:
            updates["connection_type"] = request.connection_type
        
        # Update credentials if any credential field is provided
        if any([request.api_key, request.username, request.password, request.token]):
            from app.models.gateway import GatewayCredentials
            
            # Get existing credentials or create new
            existing_creds = existing_gateway.credentials
            credentials = GatewayCredentials(
                type=existing_creds.type if existing_creds else "api_key",
                username=request.username if request.username is not None else (existing_creds.username if existing_creds else None),
                password=request.password if request.password is not None else (existing_creds.password if existing_creds else None),
                api_key=request.api_key if request.api_key is not None else (existing_creds.api_key if existing_creds else None),
                token=request.token if request.token is not None else (existing_creds.token if existing_creds else None),
            )
            updates["credentials"] = credentials.model_dump()
        
        if request.capabilities is not None:
            updates["capabilities"] = request.capabilities
        if request.status is not None:
            updates["status"] = request.status.value
        if request.configuration is not None:
            updates["configuration"] = request.configuration
        if request.metadata is not None:
            updates["metadata"] = request.metadata
        
        # Update gateway
        updated_gateway = repo.update(str(gateway_id), updates)
        
        if not updated_gateway:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update gateway",
            )
        
        logger.info(f"Updated gateway: {gateway_id}")
        return updated_gateway
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update gateway {gateway_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update gateway: {str(e)}",
        )


@router.delete(
    "/{gateway_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove gateway",
)
async def delete_gateway(gateway_id: UUID) -> None:
    """
    Remove a Gateway from the system.
    
    Args:
        gateway_id: Gateway UUID
        
    Raises:
        HTTPException: If gateway not found or deletion fails
    """
    try:
        repo = GatewayRepository()
        
        # Check if gateway exists
        existing_gateway = repo.get(str(gateway_id))
        if not existing_gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Delete gateway
        success = repo.delete(str(gateway_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete gateway",
            )
        
        logger.info(f"Deleted gateway: {gateway_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete gateway {gateway_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete gateway: {str(e)}",
        )


@router.post(
    "/{gateway_id}/sync",
    summary="Sync APIs from gateway",
)
async def sync_gateway(
    gateway_id: UUID,
    force_refresh: bool = Query(False, description="Force refresh even if recently synced"),
) -> dict:
    """
    Trigger API discovery/sync from a Gateway.
    
    Args:
        gateway_id: Gateway UUID
        force_refresh: Force refresh even if recently synced
        
    Returns:
        Sync result with number of APIs discovered
        
    Raises:
        HTTPException: If gateway not found or sync fails
    """
    try:
        from app.services.discovery_service import DiscoveryService
        from app.db.repositories.api_repository import APIRepository
        from app.adapters.factory import GatewayAdapterFactory
        
        # Initialize services
        api_repo = APIRepository()
        gateway_repo = GatewayRepository()
        adapter_factory = GatewayAdapterFactory()
        discovery_service = DiscoveryService(api_repo, gateway_repo, adapter_factory)
        
        # Check if gateway exists
        gateway = gateway_repo.get(str(gateway_id))
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Perform discovery
        logger.info(f"Starting sync for gateway {gateway_id} (force_refresh={force_refresh})")
        result = await discovery_service.discover_gateway_apis(
            gateway_id=gateway_id,
            force_refresh=force_refresh,
        )
        
        return {
            "message": "Gateway sync completed successfully",
            "apis_discovered": result["apis_discovered"],
            "new_apis": result["new_apis"],
            "updated_apis": result["updated_apis"],
            "shadow_apis_found": result["shadow_apis_found"],
            "gateway_id": str(gateway_id),
            "gateway_name": result["gateway_name"],
            "timestamp": result["timestamp"],
        }
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Failed to sync gateway {gateway_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync gateway: {str(e)}",
        )


# Made with Bob