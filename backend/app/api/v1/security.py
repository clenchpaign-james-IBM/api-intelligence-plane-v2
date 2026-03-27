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

router = APIRouter(prefix="/security", tags=["security"])


# Request/Response Models
class ScanRequest(BaseModel):
    """Request model for security scan."""

    api_id: UUID = Field(..., description="API to scan")
    use_ai_enhancement: bool = Field(
        default=True, description="Use AI-enhanced analysis"
    )


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
    ai_enhanced: bool = Field(..., description="Whether AI enhancement was used")


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
    "/scan",
    response_model=ScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan API for security vulnerabilities",
    description="Perform security scan on a specific API using AI-enhanced analysis",
)
async def scan_api(
    request: ScanRequest,
    security_service: SecurityService = Depends(get_security_service),
) -> ScanResponse:
    """Scan API for security policy coverage issues.

    Args:
        request: Scan request with API ID and options
        security_service: Security service dependency

    Returns:
        Scan results with vulnerabilities and remediation plan

    Raises:
        HTTPException: If API not found or scan fails
    """
    try:
        logger.info(f"Scanning API {request.api_id} for security vulnerabilities")

        result = await security_service.scan_api_security(
            api_id=request.api_id,
            use_ai_enhancement=request.use_ai_enhancement,
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
    "/vulnerabilities",
    response_model=List[Vulnerability],
    status_code=status.HTTP_200_OK,
    summary="Get vulnerabilities",
    description="Retrieve vulnerabilities with optional filters",
)
async def get_vulnerabilities(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    status_filter: Optional[VulnerabilityStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    security_service: SecurityService = Depends(get_security_service),
) -> List[Vulnerability]:
    """Get vulnerabilities with optional filters.

    Args:
        api_id: Optional API filter
        status_filter: Optional status filter
        severity: Optional severity filter
        limit: Maximum results
        security_service: Security service dependency

    Returns:
        List of vulnerabilities

    Raises:
        HTTPException: If query fails
    """
    try:
        logger.info(
            f"Fetching vulnerabilities (api_id={api_id}, status={status_filter}, "
            f"severity={severity}, limit={limit})"
        )

        vulnerabilities = await security_service.get_vulnerabilities(
            api_id=api_id,
            status=status_filter,
            severity=severity,
            limit=limit,
        )

        return vulnerabilities

    except Exception as e:
        logger.error(f"Failed to fetch vulnerabilities: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch vulnerabilities: {str(e)}",
        )


@router.get(
    "/vulnerabilities/{vulnerability_id}",
    response_model=Vulnerability,
    status_code=status.HTTP_200_OK,
    summary="Get vulnerability by ID",
    description="Retrieve a specific vulnerability",
)
async def get_vulnerability(
    vulnerability_id: UUID,
    security_service: SecurityService = Depends(get_security_service),
) -> Vulnerability:
    """Get vulnerability by ID.

    Args:
        vulnerability_id: Vulnerability identifier
        security_service: Security service dependency

    Returns:
        Vulnerability details

    Raises:
        HTTPException: If vulnerability not found
    """
    try:
        vulnerability = security_service.vulnerability_repository.get(
            str(vulnerability_id)
        )

        if not vulnerability:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Vulnerability not found: {vulnerability_id}",
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
    "/vulnerabilities/{vulnerability_id}/remediate",
    response_model=RemediationResponse,
    status_code=status.HTTP_200_OK,
    summary="Remediate vulnerability",
    description="Trigger automated remediation for a vulnerability",
)
async def remediate_vulnerability(
    vulnerability_id: UUID,
    request: Optional[RemediationRequest] = None,
    security_service: SecurityService = Depends(get_security_service),
) -> RemediationResponse:
    """Trigger automated remediation for a vulnerability.

    Args:
        vulnerability_id: Vulnerability to remediate
        request: Optional remediation request with strategy
        security_service: Security service dependency

    Returns:
        Remediation result

    Raises:
        HTTPException: If vulnerability not found or remediation fails
    """
    try:
        logger.info(f"Remediating vulnerability {vulnerability_id}")

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
    "/vulnerabilities/{vulnerability_id}/verify",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Verify remediation",
    description="Verify that a vulnerability remediation is effective",
)
async def verify_remediation(
    vulnerability_id: UUID,
    security_service: SecurityService = Depends(get_security_service),
) -> dict:
    """Verify that remediation was successful.

    Args:
        vulnerability_id: Vulnerability to verify
        security_service: Security service dependency

    Returns:
        Verification result

    Raises:
        HTTPException: If vulnerability not found or verification fails
    """
    try:
        logger.info(f"Verifying remediation for vulnerability {vulnerability_id}")

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
    "/posture",
    response_model=SecurityPostureResponse,
    status_code=status.HTTP_200_OK,
    summary="Get security posture",
    description="Get overall security posture metrics and risk score",
)
async def get_security_posture(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    security_service: SecurityService = Depends(get_security_service),
) -> SecurityPostureResponse:
    """Get security posture metrics.

    Args:
        api_id: Optional API filter
        security_service: Security service dependency

    Returns:
        Security posture metrics

    Raises:
        HTTPException: If query fails
    """
    try:
        logger.info(f"Fetching security posture (api_id={api_id})")

        posture = await security_service.get_security_posture(api_id)

        return SecurityPostureResponse(**posture)

    except Exception as e:
        logger.error(f"Failed to fetch security posture: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch security posture: {str(e)}",
        )


# Made with Bob