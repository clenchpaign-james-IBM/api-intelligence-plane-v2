"""Compliance Violation model for API Intelligence Plane.

Represents a compliance violation with affected API, compliance standard,
violation type, evidence, audit trail, and remediation documentation.

SCOPE: Gateway-level compliance monitoring for proxy APIs. Focuses on compliance
requirements that can be observed and verified at the API Gateway layer.

IMPORTANT: Compliance violations are distinct from security vulnerabilities.
Security focuses on threats and exploits; Compliance focuses on regulatory requirements.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class ComplianceStandard(str, Enum):
    """Compliance standards."""

    GDPR = "gdpr"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    ISO_27001 = "iso_27001"


class ComplianceViolationType(str, Enum):
    """Type of compliance violation mapped to regulatory requirements.
    
    These are compliance-requirement-based, not security-control-based.
    Each violation type maps to specific clauses in compliance standards.
    """
    
    # GDPR-specific (Gateway-observable)
    GDPR_DATA_PROTECTION_BY_DESIGN = "gdpr_data_protection_by_design"  # Art. 25
    GDPR_SECURITY_OF_PROCESSING = "gdpr_security_of_processing"  # Art. 32
    GDPR_RECORDS_OF_PROCESSING = "gdpr_records_of_processing"  # Art. 30
    GDPR_DATA_BREACH_NOTIFICATION = "gdpr_data_breach_notification"  # Art. 33
    
    # HIPAA-specific (Gateway-observable)
    HIPAA_ACCESS_CONTROL = "hipaa_access_control"  # § 164.312(a)(1)
    HIPAA_AUDIT_CONTROLS = "hipaa_audit_controls"  # § 164.312(b)
    HIPAA_TRANSMISSION_SECURITY = "hipaa_transmission_security"  # § 164.312(e)(1)
    HIPAA_INTEGRITY_CONTROLS = "hipaa_integrity_controls"  # § 164.312(c)(1)
    
    # SOC2-specific (Gateway-observable)
    SOC2_SECURITY_AVAILABILITY = "soc2_security_availability"  # CC6.1
    SOC2_SYSTEM_MONITORING = "soc2_system_monitoring"  # CC7.2
    SOC2_LOGICAL_ACCESS = "soc2_logical_access"  # CC6.2
    SOC2_CONFIDENTIALITY = "soc2_confidentiality"  # C1.1
    
    # PCI-DSS-specific (Gateway-observable)
    PCI_DSS_NETWORK_SECURITY = "pci_dss_network_security"  # Req 1
    PCI_DSS_ENCRYPTION_IN_TRANSIT = "pci_dss_encryption_in_transit"  # Req 4
    PCI_DSS_ACCESS_CONTROL = "pci_dss_access_control"  # Req 7
    PCI_DSS_MONITORING_TESTING = "pci_dss_monitoring_testing"  # Req 10, 11
    
    # ISO 27001-specific (Gateway-observable)
    ISO_27001_ACCESS_CONTROL = "iso_27001_access_control"  # A.9
    ISO_27001_CRYPTOGRAPHY = "iso_27001_cryptography"  # A.10
    ISO_27001_OPERATIONS_SECURITY = "iso_27001_operations_security"  # A.12
    ISO_27001_COMMUNICATIONS_SECURITY = "iso_27001_communications_security"  # A.13
    
    # Cross-standard (applicable to multiple standards)
    INSUFFICIENT_LOGGING_MONITORING = "insufficient_logging_monitoring"
    INADEQUATE_ACCESS_CONTROLS = "inadequate_access_controls"
    MISSING_ENCRYPTION_CONTROLS = "missing_encryption_controls"
    INADEQUATE_AVAILABILITY_CONTROLS = "inadequate_availability_controls"


class ComplianceSeverity(str, Enum):
    """Severity level of compliance violation."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ComplianceStatus(str, Enum):
    """Remediation status of compliance violation."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    REMEDIATED = "remediated"
    ACCEPTED_RISK = "accepted_risk"
    FALSE_POSITIVE = "false_positive"


class DetectionMethod(str, Enum):
    """How compliance violation was detected."""

    AUTOMATED_SCAN = "automated_scan"
    MANUAL_AUDIT = "manual_audit"
    EXTERNAL_AUDIT = "external_audit"
    AI_ANALYSIS = "ai_analysis"


class Evidence(BaseModel):
    """Evidence supporting the compliance violation."""

    type: str = Field(..., description="Type of evidence (e.g., 'gateway_config', 'traffic_log', 'policy')")
    description: str = Field(..., description="Description of the evidence")
    source: str = Field(..., description="Source of the evidence (e.g., 'gateway_api', 'metrics')")
    timestamp: datetime = Field(..., description="When evidence was collected")
    data: Optional[dict[str, Any]] = Field(None, description="Evidence data")


class AuditTrailEntry(BaseModel):
    """Audit trail entry for compliance violation."""

    timestamp: datetime = Field(..., description="When action occurred")
    action: str = Field(..., description="Action taken")
    performed_by: str = Field(..., description="Who performed the action")
    details: Optional[str] = Field(None, description="Additional details")
    status_before: Optional[str] = Field(None, description="Status before action")
    status_after: Optional[str] = Field(None, description="Status after action")


class RemediationDocumentation(BaseModel):
    """Documentation of remediation actions (Gateway-level)."""

    action: str = Field(..., description="Remediation action taken")
    type: str = Field(..., description="Type of remediation (e.g., 'gateway_policy', 'configuration')")
    status: str = Field(..., description="Status of remediation")
    performed_at: Optional[datetime] = Field(None, description="When performed")
    performed_by: Optional[str] = Field(None, description="Who performed")
    gateway_policy_id: Optional[str] = Field(None, description="Gateway policy ID if applied")
    verification_method: Optional[str] = Field(None, description="How verified")
    verification_status: Optional[str] = Field(None, description="Verification result")
    notes: Optional[str] = Field(None, description="Additional notes")


class ComplianceViolation(BaseModel):
    """Compliance Violation entity representing a Gateway-level regulatory compliance violation.

    SCOPE: Gateway-level compliance only. Monitors compliance requirements that can be
    observed and verified at the API Gateway layer.

    DISTINCTION: Compliance violations are regulatory requirement failures, distinct from
    security vulnerabilities which are threat-based.

    Attributes:
        id: Unique identifier (UUID v4)
        api_id: Affected API (Gateway proxy endpoint)
        compliance_standard: Compliance standard violated (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
        violation_type: Type of compliance violation (mapped to regulatory requirements)
        severity: Severity level
        title: Violation title (1-255 characters)
        description: Detailed description (1-5000 characters)
        affected_endpoints: Specific Gateway endpoints affected
        detection_method: How detected
        detected_at: Detection timestamp
        status: Remediation status
        evidence: Supporting evidence from Gateway
        audit_trail: Complete audit trail
        remediation_documentation: Gateway-level remediation actions and verification
        regulatory_reference: Reference to specific regulation clause
        risk_level: Business risk level
        remediation_deadline: Deadline for remediation
        remediated_at: Remediation timestamp
        last_audit_date: Last audit date
        next_audit_date: Next scheduled audit date
        metadata: Additional data
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    gateway_id: UUID = Field(..., description="Gateway where API is deployed")
    api_id: UUID = Field(..., description="Affected API (Gateway proxy endpoint)")
    compliance_standard: ComplianceStandard = Field(
        ..., description="Compliance standard violated"
    )
    violation_type: ComplianceViolationType = Field(
        ..., description="Type of compliance violation (mapped to regulatory requirements)"
    )
    severity: ComplianceSeverity = Field(..., description="Severity level")
    title: str = Field(..., min_length=1, max_length=255, description="Violation title")
    description: str = Field(
        ..., min_length=1, max_length=5000, description="Detailed description"
    )
    affected_endpoints: Optional[list[str]] = Field(
        None, description="Specific Gateway endpoints affected"
    )
    detection_method: DetectionMethod = Field(..., description="How detected")
    detected_at: datetime = Field(..., description="Detection timestamp")
    status: ComplianceStatus = Field(
        default=ComplianceStatus.OPEN, description="Remediation status"
    )
    evidence: list[Evidence] = Field(
        default_factory=list, description="Supporting evidence from Gateway"
    )
    audit_trail: list[AuditTrailEntry] = Field(
        default_factory=list, description="Complete audit trail"
    )
    remediation_documentation: Optional[list[RemediationDocumentation]] = Field(
        None, description="Gateway-level remediation actions and verification"
    )
    regulatory_reference: Optional[str] = Field(
        None, description="Reference to specific regulation clause"
    )
    risk_level: Optional[str] = Field(
        None, description="Business risk level (e.g., 'financial', 'reputational', 'operational')"
    )
    remediation_deadline: Optional[datetime] = Field(
        None, description="Deadline for remediation"
    )
    remediated_at: Optional[datetime] = Field(None, description="Remediation timestamp")
    last_audit_date: Optional[datetime] = Field(None, description="Last audit date")
    next_audit_date: Optional[datetime] = Field(
        None, description="Next scheduled audit date"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional data")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow, description="Last update timestamp"
    )

    @field_validator("remediated_at")
    @classmethod
    def validate_remediated_at(cls, v: Optional[datetime], info) -> Optional[datetime]:
        """Validate if status is remediated, remediated_at must be set."""
        if "status" in info.data:
            status = info.data["status"]
            if status == ComplianceStatus.REMEDIATED and v is None:
                raise ValueError("remediated_at must be set when status is remediated")
        return v

    @field_validator("remediation_deadline")
    @classmethod
    def validate_remediation_deadline(
        cls, v: Optional[datetime], info
    ) -> Optional[datetime]:
        """Validate remediation deadline is in the future."""
        if v is not None and "created_at" in info.data:
            created_at = info.data["created_at"]
            if v < created_at:
                raise ValueError("remediation_deadline must be after created_at")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440005",
                "gateway_id": "550e8400-e29b-41d4-a716-446655440000",
                "api_id": "550e8400-e29b-41d4-a716-446655440001",
                "compliance_standard": "hipaa",
                "violation_type": "hipaa_transmission_security",
                "severity": "critical",
                "title": "HIPAA Transmission Security Violation",
                "description": "Gateway API endpoint handling PHI does not enforce TLS 1.3 encryption as required by HIPAA § 164.312(e)(1) for transmission security.",
                "affected_endpoints": ["/api/v1/patients", "/api/v1/medical-records"],
                "detection_method": "ai_analysis",
                "detected_at": "2026-03-09T10:00:00Z",
                "status": "open",
                "evidence": [
                    {
                        "type": "gateway_config",
                        "description": "Gateway TLS policy analysis shows TLS 1.2 allowed",
                        "source": "gateway_api",
                        "timestamp": "2026-03-09T10:00:00Z",
                        "data": {"tls_version": "1.2", "min_tls_version": "1.0"}
                    }
                ],
                "audit_trail": [
                    {
                        "timestamp": "2026-03-09T10:00:00Z",
                        "action": "violation_detected",
                        "performed_by": "compliance_agent",
                        "details": "AI-driven compliance scan detected HIPAA transmission security violation",
                    }
                ],
                "regulatory_reference": "HIPAA Security Rule § 164.312(e)(1) - Transmission Security",
                "risk_level": "financial",
                "remediation_deadline": "2026-03-16T00:00:00Z",
            }
        }


# Made with Bob