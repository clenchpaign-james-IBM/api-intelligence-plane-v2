"""Compliance API endpoints for API Intelligence Plane.

Provides REST API for compliance monitoring, violation management, and audit reporting.
Focuses on scheduled audit preparation and regulatory reporting (distinct from immediate security threat response).
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_compliance_service
from app.models.compliance import (
    ComplianceViolation,
    ComplianceStandard,
    ComplianceStatus,
    ComplianceSeverity,
)
from app.services.compliance_service import ComplianceService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/compliance", tags=["compliance"])


# Request/Response Models
class ComplianceScanRequest(BaseModel):
    """Request model for compliance scan."""

    api_id: UUID = Field(..., description="API to scan")
    standards: Optional[List[ComplianceStandard]] = Field(
        None, description="Specific standards to check (default: all 5)"
    )


class ComplianceScanResponse(BaseModel):
    """Response model for compliance scan."""

    scan_id: str = Field(..., description="Scan identifier")
    api_id: str = Field(..., description="API identifier")
    api_name: str = Field(..., description="API name")
    scan_completed_at: str = Field(..., description="Scan completion timestamp")
    violations_found: int = Field(..., description="Number of violations")
    severity_breakdown: dict = Field(..., description="Violations by severity")
    standard_breakdown: dict = Field(..., description="Violations by standard")
    violations: List[dict] = Field(..., description="List of violations")
    audit_evidence: List[dict] = Field(..., description="Audit evidence collected")


class AuditReportRequest(BaseModel):
    """Request model for audit report generation."""

    api_id: Optional[UUID] = Field(None, description="Optional API filter")
    standard: Optional[ComplianceStandard] = Field(
        None, description="Optional standard filter"
    )
    start_date: Optional[datetime] = Field(
        None, description="Report start date (default: 90 days ago)"
    )
    end_date: Optional[datetime] = Field(
        None, description="Report end date (default: now)"
    )


class AuditReportResponse(BaseModel):
    """Response model for audit report."""

    report_id: str = Field(..., description="Report identifier")
    generated_at: str = Field(..., description="Report generation timestamp")
    report_period: dict = Field(..., description="Report time period")
    executive_summary: str = Field(..., description="AI-generated executive summary")
    compliance_posture: dict = Field(..., description="Overall compliance posture")
    violations_by_standard: dict = Field(..., description="Violations by standard")
    violations_by_severity: dict = Field(..., description="Violations by severity")
    remediation_status: dict = Field(..., description="Remediation status breakdown")
    violations_needing_audit: List[dict] = Field(
        ..., description="Violations needing audit attention"
    )
    audit_evidence: List[dict] = Field(..., description="Collected audit evidence")
    recommendations: List[str] = Field(..., description="Audit recommendations")


class CompliancePostureResponse(BaseModel):
    """Response model for compliance posture."""

    total_violations: int = Field(..., description="Total violations")
    by_severity: dict = Field(..., description="Breakdown by severity")
    by_status: dict = Field(..., description="Breakdown by status")
    by_standard: dict = Field(..., description="Breakdown by standard")
    remediation_rate: float = Field(..., description="Remediation rate percentage")
    compliance_score: float = Field(
        ..., description="Overall compliance score (0-100, higher is better)"
    )
    last_scan: Optional[str] = Field(None, description="Last scan timestamp")
    next_audit_date: str = Field(..., description="Next recommended audit date")


# API Endpoints
@router.post(
    "/scan",
    response_model=ComplianceScanResponse,
    status_code=status.HTTP_200_OK,
    summary="Scan API for compliance violations",
    description="Perform compliance scan on a specific API using AI-driven analysis for 5 regulatory standards",
)
async def scan_api_compliance(
    request: ComplianceScanRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service),
) -> ComplianceScanResponse:
    """Scan API for compliance violations across regulatory standards.

    Checks compliance with:
    - GDPR (General Data Protection Regulation)
    - HIPAA (Health Insurance Portability and Accountability Act)
    - SOC2 (Service Organization Control 2)
    - PCI-DSS (Payment Card Industry Data Security Standard)
    - ISO 27001 (Information Security Management)

    Args:
        request: Scan request with API ID and optional standards filter
        compliance_service: Compliance service dependency

    Returns:
        Scan results with violations and audit evidence

    Raises:
        HTTPException: If API not found or scan fails
    """
    try:
        logger.info(f"Scanning API {request.api_id} for compliance violations")

        result = await compliance_service.scan_api_compliance(
            api_id=request.api_id,
            standards=request.standards,
        )

        return ComplianceScanResponse(**result)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Compliance scan failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Compliance scan failed: {str(e)}",
        )


@router.get(
    "/violations",
    response_model=List[ComplianceViolation],
    status_code=status.HTTP_200_OK,
    summary="Get compliance violations",
    description="Retrieve compliance violations with optional filters",
)
async def get_violations(
    api_id: Optional[UUID] = Query(None, description="Filter by API ID"),
    standard: Optional[ComplianceStandard] = Query(
        None, description="Filter by compliance standard"
    ),
    severity: Optional[ComplianceSeverity] = Query(
        None, description="Filter by severity"
    ),
    status_filter: Optional[ComplianceStatus] = Query(
        None, alias="status", description="Filter by status"
    ),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    compliance_service: ComplianceService = Depends(get_compliance_service),
) -> List[ComplianceViolation]:
    """Get compliance violations with optional filters.

    Args:
        api_id: Optional API filter
        standard: Optional compliance standard filter
        severity: Optional severity filter
        status_filter: Optional status filter
        limit: Maximum results
        compliance_service: Compliance service dependency

    Returns:
        List of compliance violations

    Raises:
        HTTPException: If query fails
    """
    try:
        from app.db.repositories.compliance_repository import ComplianceRepository

        compliance_repo = ComplianceRepository()

        # Build filters - all methods return List[ComplianceViolation]
        violations: List[ComplianceViolation] = []
        
        if api_id:
            violations = await compliance_repo.find_by_api_id(api_id)
        elif standard:
            violations = await compliance_repo.find_by_standard(standard)
        elif severity:
            violations = await compliance_repo.find_by_severity(severity)
        elif status_filter:
            # Get open violations and filter by status
            open_violations = await compliance_repo.find_open_violations(limit=limit)
            violations = [v for v in open_violations if v.status == status_filter]
        else:
            # Get all open violations by default
            violations = await compliance_repo.find_open_violations(limit=limit)

        # Apply limit if needed
        if len(violations) > limit:
            violations = violations[:limit]

        return violations

    except Exception as e:
        logger.error(f"Failed to get violations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get violations: {str(e)}",
        )


@router.get(
    "/posture",
    response_model=CompliancePostureResponse,
    status_code=status.HTTP_200_OK,
    summary="Get compliance posture",
    description="Get overall compliance posture metrics and scores",
)
async def get_compliance_posture(
    api_id: Optional[UUID] = Query(None, description="Optional API filter"),
    standard: Optional[ComplianceStandard] = Query(
        None, description="Optional standard filter"
    ),
    compliance_service: ComplianceService = Depends(get_compliance_service),
) -> CompliancePostureResponse:
    """Get compliance posture metrics.

    Args:
        api_id: Optional API filter
        standard: Optional compliance standard filter
        compliance_service: Compliance service dependency

    Returns:
        Compliance posture metrics and scores

    Raises:
        HTTPException: If query fails
    """
    try:
        logger.info("Getting compliance posture")

        posture = await compliance_service.get_compliance_posture(
            api_id=api_id,
            standard=standard,
        )

        return CompliancePostureResponse(**posture)

    except Exception as e:
        logger.error(f"Failed to get compliance posture: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get compliance posture: {str(e)}",
        )


@router.post(
    "/reports/audit",
    response_model=AuditReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate audit report",
    description="Generate comprehensive audit report with evidence and recommendations",
)
async def generate_audit_report(
    request: AuditReportRequest,
    compliance_service: ComplianceService = Depends(get_compliance_service),
) -> AuditReportResponse:
    """Generate comprehensive audit report.

    Includes:
    - AI-generated executive summary
    - Compliance posture analysis
    - Violations breakdown by standard and severity
    - Remediation status tracking
    - Violations needing audit attention
    - Collected audit evidence
    - Actionable recommendations

    Args:
        request: Audit report request with optional filters
        compliance_service: Compliance service dependency

    Returns:
        Comprehensive audit report

    Raises:
        HTTPException: If report generation fails
    """
    try:
        logger.info("Generating audit report")

        report = await compliance_service.generate_audit_report(
            api_id=request.api_id,
            standard=request.standard,
            start_date=request.start_date,
            end_date=request.end_date,
        )

        return AuditReportResponse(**report)

    except Exception as e:
        logger.error(f"Failed to generate audit report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate audit report: {str(e)}",
        )


@router.get(
    "/violations/{violation_id}",
    response_model=ComplianceViolation,
    status_code=status.HTTP_200_OK,
    summary="Get violation by ID",
    description="Retrieve a specific compliance violation by ID",
)
async def get_violation(
    violation_id: UUID,
    compliance_service: ComplianceService = Depends(get_compliance_service),
) -> ComplianceViolation:
    """Get a specific compliance violation by ID.

    Args:
        violation_id: Violation identifier
        compliance_service: Compliance service dependency

    Returns:
        Compliance violation details

    Raises:
        HTTPException: If violation not found
    """
    try:
        from app.db.repositories.compliance_repository import ComplianceRepository

        compliance_repo = ComplianceRepository()
        violation = compliance_repo.get(str(violation_id))

        if not violation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Violation not found: {violation_id}",
            )

        return violation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get violation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get violation: {str(e)}",
        )

# Made with Bob
