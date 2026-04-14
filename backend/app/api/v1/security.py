"""Security API endpoints for API Intelligence Plane.

Provides REST API for security scanning, vulnerability management, and remediation.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_security_service
from app.models.vulnerability import Vulnerability, VulnerabilityStatus
from app.services.security_service import SecurityService

logger = logging.getLogger(__name__)

router = APIRouter(tags=["security"])


# Request/Response Models
class ScanRequest(BaseModel):
    """Request model for security scan."""

    gateway_id: UUID = Field(..., description="Gateway containing the API")
    api_id: UUID = Field(..., description="API to scan")


class ScanResponse(BaseModel):
    """Response model for security scan."""

    scan_id: str = Field(..., description="Scan identifier")
    api_id: str = Field(..., description="API identifier")
    api_name: str = Field(..., description="API name")
    scan_completed_at: str = Field(..., description="Scan completion timestamp")
    vulnerabilities_found: int = Field(..., description="Number of vulnerabilities")
    severity_breakdown: dict = Field(..., description="Vulnerabilities by severity")
    vulnerabilities: List[dict] = Field(..., description="List of vulnerabilities")
    remediation_plan: dict = Field(..., description="Remediation plan")


class RemediationRequest(BaseModel):
    """Request model for vulnerability remediation."""

    vulnerability_id: UUID = Field(..., description="Vulnerability to remediate")
    remediation_strategy: Optional[str] = Field(
        None, description="Optional specific strategy"
    )


class RemediationResponse(BaseModel):
    """Response model for remediation."""

    vulnerability_id: str = Field(..., description="Vulnerability identifier")
    status: str = Field(..., description="Remediation status")
    remediation_result: Optional[dict] = Field(None, description="Remediation details")
    verification_result: Optional[dict] = Field(None, description="Verification details")
    message: Optional[str] = Field(None, description="Status message")


class SecurityPostureResponse(BaseModel):
    """Response model for security posture."""

    total_vulnerabilities: int = Field(..., description="Total vulnerabilities")
    by_severity: dict = Field(..., description="Breakdown by severity")
    by_status: dict = Field(..., description="Breakdown by status")
    by_type: dict = Field(..., description="Breakdown by type")
    remediation_rate: float = Field(..., description="Remediation rate percentage")
    risk_score: int = Field(..., description="Overall risk score (0-100)")
    risk_level: str = Field(..., description="Risk level (low/medium/high/critical)")
    avg_remediation_time_ms: Optional[float] = Field(
        None, description="Average remediation time"
    )


# API Endpoints
@router.post(
    "/gateways/{gateway_id}/security/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan API for security vulnerabilities",
    description="Perform security scan on a specific API within a gateway using hybrid analysis (rule-based + AI-enhanced)",
)
async def scan_gateway_api(
    gateway_id: UUID,
    request: ScanRequest,
    security_service: SecurityService = Depends(get_security_service),
) -> ScanResponse:
    """Scan API for security policy coverage issues using hybrid analysis.
    
    Always uses hybrid approach combining:
    - Rule-based checks for deterministic security factors
    - AI-enhanced analysis for context-aware severity assessment

    Args:
        gateway_id: Gateway UUID (required, must match request.gateway_id)
        request: Scan request with gateway_id and API ID
        security_service: Security service dependency

    Returns:
        Scan results with vulnerabilities and remediation plan

    Raises:
        HTTPException: If gateway or API not found or scan fails
    """
    try:
        # Verify gateway_id matches path parameter
        if str(request.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Gateway ID in request body must match path parameter",
            )
        
        # Verify gateway exists
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Verify API belongs to gateway
        from app.db.repositories.api_repository import APIRepository
        api_repo = APIRepository()
        api = api_repo.get(str(request.api_id))
        
        if not api:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {request.api_id} not found",
            )
        
        if str(api.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API {request.api_id} not found in gateway {gateway_id}",
            )
        
        logger.info(f"Scanning API {request.api_id} in gateway {gateway_id} for security vulnerabilities (hybrid analysis)")

        result = await security_service.scan_api_security(
            api_id=request.api_id,
            gateway_id=gateway_id,
        )

        return ScanResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Security scan failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Security scan failed: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/security/vulnerabilities",
    response_model=List[Vulnerability],
    status_code=status.HTTP_200_OK,
    summary="Get vulnerabilities for a gateway",
    description="Retrieve vulnerabilities for APIs within a gateway with optional filters",
)
async def get_gateway_vulnerabilities(
    gateway_id: UUID,
    api_id: Optional[UUID] = Query(None, description="Filter by API ID within gateway"),
    status_filter: Optional[VulnerabilityStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    security_service: SecurityService = Depends(get_security_service),
) -> List[Vulnerability]:
    """Get vulnerabilities for APIs within a gateway with optional filters.

    Args:
        gateway_id: Gateway UUID (required)
        api_id: Optional API filter within gateway
        status_filter: Optional status filter
        severity: Optional severity filter
        limit: Maximum results
        security_service: Security service dependency

    Returns:
        List of vulnerabilities

    Raises:
        HTTPException: If gateway not found or query fails
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
        
        # If api_id is provided, verify it belongs to the gateway
        if api_id:
            from app.db.repositories.api_repository import APIRepository
            api_repo = APIRepository()
            api = api_repo.get(str(api_id))
            if not api or str(api.gateway_id) != str(gateway_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"API {api_id} not found in gateway {gateway_id}",
                )
        
        logger.info(
            f"Fetching vulnerabilities for gateway {gateway_id} (api_id={api_id}, status={status_filter}, "
            f"severity={severity}, limit={limit})"
        )

        vulnerabilities = await security_service.get_vulnerabilities(
            api_id=api_id,
            status=status_filter,
            severity=severity,
            limit=limit,
        )
        
        # Filter vulnerabilities to only include those from APIs in this gateway
        if not api_id:
            from app.db.repositories.api_repository import APIRepository
            api_repo = APIRepository()
            gateway_apis, _ = api_repo.find_by_gateway(gateway_id=gateway_id, size=10000)
            gateway_api_ids = {str(api.id) for api in gateway_apis}
            
            vulnerabilities = [
                v for v in vulnerabilities
                if str(v.api_id) in gateway_api_ids
            ]

        return vulnerabilities

    except Exception as e:
        logger.error(f"Failed to fetch vulnerabilities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vulnerabilities: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/security/vulnerabilities/{vulnerability_id}",
    response_model=Vulnerability,
    status_code=status.HTTP_200_OK,
    summary="Get vulnerability by ID",
    description="Retrieve a specific vulnerability within a gateway",
)
async def get_gateway_vulnerability(
    gateway_id: UUID,
    vulnerability_id: UUID,
    security_service: SecurityService = Depends(get_security_service),
) -> Vulnerability:
    """Get vulnerability by ID within a gateway.

    Args:
        gateway_id: Gateway UUID (required)
        vulnerability_id: Vulnerability identifier
        security_service: Security service dependency

    Returns:
        Vulnerability details

    Raises:
        HTTPException: If gateway or vulnerability not found
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
        
        vulnerability = security_service.vulnerability_repository.get(
            str(vulnerability_id)
        )

        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vulnerability not found: {vulnerability_id}",
            )
        
        # Verify vulnerability's API belongs to the gateway
        from app.db.repositories.api_repository import APIRepository
        api_repo = APIRepository()
        api = api_repo.get(str(vulnerability.api_id))
        if not api or str(api.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vulnerability {vulnerability_id} not found in gateway {gateway_id}",
            )

        return vulnerability

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to fetch vulnerability: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vulnerability: {str(e)}",
        )


@router.post(
    "/gateways/{gateway_id}/security/vulnerabilities/{vulnerability_id}/remediate",
    response_model=RemediationResponse,
    status_code=status.HTTP_200_OK,
    summary="Remediate vulnerability",
    description="Trigger automated remediation for a vulnerability within a gateway",
)
async def remediate_gateway_vulnerability(
    gateway_id: UUID,
    vulnerability_id: UUID,
    request: Optional[RemediationRequest] = None,
    security_service: SecurityService = Depends(get_security_service),
) -> RemediationResponse:
    """Trigger automated remediation for a vulnerability within a gateway.

    Args:
        gateway_id: Gateway UUID (required)
        vulnerability_id: Vulnerability to remediate
        request: Optional remediation request with strategy
        security_service: Security service dependency

    Returns:
        Remediation result

    Raises:
        HTTPException: If gateway or vulnerability not found or remediation fails
    """
    try:
        # Verify gateway exists and vulnerability belongs to it
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Verify vulnerability exists and belongs to gateway
        vulnerability = security_service.vulnerability_repository.get(str(vulnerability_id))
        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vulnerability {vulnerability_id} not found",
            )
        
        from app.db.repositories.api_repository import APIRepository
        api_repo = APIRepository()
        api = api_repo.get(str(vulnerability.api_id))
        if not api or str(api.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vulnerability {vulnerability_id} not found in gateway {gateway_id}",
            )
        
        logger.info(f"Remediating vulnerability {vulnerability_id} in gateway {gateway_id}")

        remediation_strategy = None
        if request:
            remediation_strategy = request.remediation_strategy

        result = await security_service.remediate_vulnerability(
            vulnerability_id=vulnerability_id,
            remediation_strategy=remediation_strategy,
        )

        return RemediationResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Remediation failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Remediation failed: {str(e)}",
        )


@router.post(
    "/gateways/{gateway_id}/security/vulnerabilities/{vulnerability_id}/verify",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Verify remediation",
    description="Verify that a vulnerability remediation is effective within a gateway",
)
async def verify_gateway_remediation(
    gateway_id: UUID,
    vulnerability_id: UUID,
    security_service: SecurityService = Depends(get_security_service),
) -> dict:
    """Verify that remediation was successful within a gateway.

    Args:
        gateway_id: Gateway UUID (required)
        vulnerability_id: Vulnerability to verify
        security_service: Security service dependency

    Returns:
        Verification result

    Raises:
        HTTPException: If gateway or vulnerability not found or verification fails
    """
    try:
        # Verify gateway exists and vulnerability belongs to it
        from app.db.repositories.gateway_repository import GatewayRepository
        gateway_repo = GatewayRepository()
        gateway = gateway_repo.get(str(gateway_id))
        
        if not gateway:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Gateway {gateway_id} not found",
            )
        
        # Verify vulnerability exists and belongs to gateway
        vulnerability = security_service.vulnerability_repository.get(str(vulnerability_id))
        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vulnerability {vulnerability_id} not found",
            )
        
        from app.db.repositories.api_repository import APIRepository
        api_repo = APIRepository()
        api = api_repo.get(str(vulnerability.api_id))
        if not api or str(api.gateway_id) != str(gateway_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vulnerability {vulnerability_id} not found in gateway {gateway_id}",
            )
        
        logger.info(f"Verifying remediation for vulnerability {vulnerability_id} in gateway {gateway_id}")

        result = await security_service.verify_remediation(vulnerability_id)

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Verification failed: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/security/summary",
    summary="Get security summary for a gateway",
    description="Get aggregated security metrics for a gateway's APIs",
)
async def get_gateway_security_summary(
    gateway_id: UUID,
    security_service: SecurityService = Depends(get_security_service),
) -> dict:
    """Get security summary metrics for a gateway's APIs.
    
    Args:
        gateway_id: Gateway UUID (required)
    
    Returns:
        Dictionary with vulnerability counts by severity
        
    Raises:
        HTTPException: If gateway not found or query fails
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
        
        logger.info(f"Fetching security summary for gateway {gateway_id}")
        
        # Get all vulnerabilities
        all_vulnerabilities = await security_service.get_vulnerabilities(limit=10000)
        
        # Filter to only include vulnerabilities from APIs in this gateway
        from app.db.repositories.api_repository import APIRepository
        api_repo = APIRepository()
        gateway_apis, _ = api_repo.find_by_gateway(gateway_id=gateway_id, size=10000)
        gateway_api_ids = {str(api.id) for api in gateway_apis}
        
        vulnerabilities = [
            v for v in all_vulnerabilities
            if str(v.api_id) in gateway_api_ids
        ]
        
        # Count by severity
        critical = sum(1 for v in vulnerabilities if v.severity == "critical")
        high = sum(1 for v in vulnerabilities if v.severity == "high")
        medium = sum(1 for v in vulnerabilities if v.severity == "medium")
        low = sum(1 for v in vulnerabilities if v.severity == "low")
        
        return {
            "gateway_id": str(gateway_id),
            "total_vulnerabilities": len(vulnerabilities),
            "critical_vulnerabilities": critical,
            "high_vulnerabilities": high,
            "medium_vulnerabilities": medium,
            "low_vulnerabilities": low,
        }
        
    except Exception as e:
        logger.error(f"Failed to fetch security summary: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch security summary: {str(e)}",
        )


@router.get(
    "/gateways/{gateway_id}/security/posture",
    response_model=SecurityPostureResponse,
    status_code=status.HTTP_200_OK,
    summary="Get security posture for a gateway",
    description="Get security posture metrics and risk score for a gateway's APIs",
)
async def get_gateway_security_posture(
    gateway_id: UUID,
    api_id: Optional[UUID] = Query(None, description="Filter by API ID within gateway"),
    security_service: SecurityService = Depends(get_security_service),
) -> SecurityPostureResponse:
    """Get security posture metrics for a gateway's APIs.

    Args:
        gateway_id: Gateway UUID (required)
        api_id: Optional API filter within gateway
        security_service: Security service dependency

    Returns:
        Security posture metrics

    Raises:
        HTTPException: If gateway not found or query fails
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
        
        # If api_id is provided, verify it belongs to the gateway
        if api_id:
            from app.db.repositories.api_repository import APIRepository
            api_repo = APIRepository()
            api = api_repo.get(str(api_id))
            if not api or str(api.gateway_id) != str(gateway_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"API {api_id} not found in gateway {gateway_id}",
                )
        
        logger.info(f"Fetching security posture for gateway {gateway_id} (api_id={api_id})")

        posture = await security_service.get_security_posture(api_id)

        return SecurityPostureResponse(**posture)

    except Exception as e:
        logger.error(f"Failed to fetch security posture: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch security posture: {str(e)}",
        )


# Made with Bob