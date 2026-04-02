#!/usr/bin/env python3
"""
Mock Compliance Violation Data Generator

Generates realistic compliance violation data for testing and development purposes.
Creates violations across 5 compliance standards (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
with various severities, statuses, and evidence.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List
import random
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_client
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.api_repository import APIRepository
from app.models.compliance import (
    ComplianceViolation,
    ComplianceStandard,
    ComplianceViolationType,
    ComplianceSeverity,
    ComplianceStatus,
    DetectionMethod,
    Evidence,
    AuditTrailEntry,
    RemediationDocumentation,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockComplianceGenerator:
    """Generates mock compliance violation data for testing."""
    
    # Violation type mappings for each standard
    STANDARD_VIOLATIONS = {
        ComplianceStandard.GDPR: [
            ComplianceViolationType.GDPR_DATA_PROTECTION_BY_DESIGN,
            ComplianceViolationType.GDPR_SECURITY_OF_PROCESSING,
            ComplianceViolationType.GDPR_RECORDS_OF_PROCESSING,
            ComplianceViolationType.GDPR_DATA_BREACH_NOTIFICATION,
        ],
        ComplianceStandard.HIPAA: [
            ComplianceViolationType.HIPAA_ACCESS_CONTROL,
            ComplianceViolationType.HIPAA_AUDIT_CONTROLS,
            ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY,
            ComplianceViolationType.HIPAA_INTEGRITY_CONTROLS,
        ],
        ComplianceStandard.SOC2: [
            ComplianceViolationType.SOC2_SECURITY_AVAILABILITY,
            ComplianceViolationType.SOC2_SYSTEM_MONITORING,
            ComplianceViolationType.SOC2_LOGICAL_ACCESS,
            ComplianceViolationType.SOC2_CONFIDENTIALITY,
        ],
        ComplianceStandard.PCI_DSS: [
            ComplianceViolationType.PCI_DSS_NETWORK_SECURITY,
            ComplianceViolationType.PCI_DSS_ENCRYPTION_IN_TRANSIT,
            ComplianceViolationType.PCI_DSS_ACCESS_CONTROL,
            ComplianceViolationType.PCI_DSS_MONITORING_TESTING,
        ],
        ComplianceStandard.ISO_27001: [
            ComplianceViolationType.ISO_27001_ACCESS_CONTROL,
            ComplianceViolationType.ISO_27001_CRYPTOGRAPHY,
            ComplianceViolationType.ISO_27001_OPERATIONS_SECURITY,
            ComplianceViolationType.ISO_27001_COMMUNICATIONS_SECURITY,
        ],
    }
    
    # Cross-standard violations
    CROSS_STANDARD_VIOLATIONS = [
        ComplianceViolationType.INSUFFICIENT_LOGGING_MONITORING,
        ComplianceViolationType.INADEQUATE_ACCESS_CONTROLS,
        ComplianceViolationType.MISSING_ENCRYPTION_CONTROLS,
        ComplianceViolationType.INADEQUATE_AVAILABILITY_CONTROLS,
    ]
    
    # Regulatory references
    REGULATORY_REFERENCES = {
        ComplianceStandard.GDPR: {
            ComplianceViolationType.GDPR_DATA_PROTECTION_BY_DESIGN: "GDPR Article 25",
            ComplianceViolationType.GDPR_SECURITY_OF_PROCESSING: "GDPR Article 32",
            ComplianceViolationType.GDPR_RECORDS_OF_PROCESSING: "GDPR Article 30",
            ComplianceViolationType.GDPR_DATA_BREACH_NOTIFICATION: "GDPR Article 33",
        },
        ComplianceStandard.HIPAA: {
            ComplianceViolationType.HIPAA_ACCESS_CONTROL: "45 CFR § 164.312(a)(1)",
            ComplianceViolationType.HIPAA_AUDIT_CONTROLS: "45 CFR § 164.312(b)",
            ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY: "45 CFR § 164.312(e)(1)",
            ComplianceViolationType.HIPAA_INTEGRITY_CONTROLS: "45 CFR § 164.312(c)(1)",
        },
        ComplianceStandard.SOC2: {
            ComplianceViolationType.SOC2_SECURITY_AVAILABILITY: "CC6.1",
            ComplianceViolationType.SOC2_SYSTEM_MONITORING: "CC7.2",
            ComplianceViolationType.SOC2_LOGICAL_ACCESS: "CC6.2",
            ComplianceViolationType.SOC2_CONFIDENTIALITY: "C1.1",
        },
        ComplianceStandard.PCI_DSS: {
            ComplianceViolationType.PCI_DSS_NETWORK_SECURITY: "PCI-DSS Requirement 1",
            ComplianceViolationType.PCI_DSS_ENCRYPTION_IN_TRANSIT: "PCI-DSS Requirement 4",
            ComplianceViolationType.PCI_DSS_ACCESS_CONTROL: "PCI-DSS Requirement 7",
            ComplianceViolationType.PCI_DSS_MONITORING_TESTING: "PCI-DSS Requirements 10, 11",
        },
        ComplianceStandard.ISO_27001: {
            ComplianceViolationType.ISO_27001_ACCESS_CONTROL: "ISO 27001 A.9",
            ComplianceViolationType.ISO_27001_CRYPTOGRAPHY: "ISO 27001 A.10",
            ComplianceViolationType.ISO_27001_OPERATIONS_SECURITY: "ISO 27001 A.12",
            ComplianceViolationType.ISO_27001_COMMUNICATIONS_SECURITY: "ISO 27001 A.13",
        },
    }
    
    def __init__(self):
        self.compliance_repo = ComplianceRepository()
        self.api_repo = APIRepository()
    
    def generate_violations(
        self,
        api_id: str,
        count: int = 10,
        standards: List[ComplianceStandard] | None = None,
        severity_distribution: dict | None = None,
        status_distribution: dict | None = None,
    ) -> List[ComplianceViolation]:
        """
        Generate mock compliance violations for an API.
        
        Args:
            api_id: Target API ID
            count: Number of violations to generate
            standards: Specific standards to generate violations for (default: all)
            severity_distribution: Distribution of severities (default: balanced)
            status_distribution: Distribution of statuses (default: mostly open)
            
        Returns:
            List of generated violations
        """
        if standards is None:
            standards = list(ComplianceStandard)
        
        if severity_distribution is None:
            severity_distribution = {
                ComplianceSeverity.CRITICAL: 0.15,
                ComplianceSeverity.HIGH: 0.30,
                ComplianceSeverity.MEDIUM: 0.35,
                ComplianceSeverity.LOW: 0.20,
            }
        
        if status_distribution is None:
            status_distribution = {
                ComplianceStatus.OPEN: 0.50,
                ComplianceStatus.IN_PROGRESS: 0.25,
                ComplianceStatus.REMEDIATED: 0.15,
                ComplianceStatus.ACCEPTED_RISK: 0.08,
                ComplianceStatus.FALSE_POSITIVE: 0.02,
            }
        
        violations = []
        now = datetime.utcnow()
        
        for i in range(count):
            # Choose standard
            standard = random.choice(standards)
            
            # Choose violation type for standard
            violation_type = self._choose_violation_type(standard)
            
            # Choose severity and status
            severity = self._choose_from_distribution(severity_distribution)
            status = self._choose_from_distribution(status_distribution)
            
            # Generate violation
            violation = self._create_violation(
                api_id=api_id,
                standard=standard,
                violation_type=violation_type,
                severity=severity,
                status=status,
                detected_at=now - timedelta(days=random.randint(1, 30)),
            )
            
            # Store in OpenSearch
            created = self.compliance_repo.create(violation)
            violations.append(created)
            
            logger.info(
                f"Generated violation {i+1}/{count}: {standard.value} - "
                f"{violation_type.value} ({severity.value})"
            )
        
        return violations
    
    def generate_violations_for_all_apis(
        self,
        violations_per_api: int = 5,
        standards: List[ComplianceStandard] | None = None,
    ) -> dict:
        """
        Generate violations for all APIs in the system.
        
        Args:
            violations_per_api: Number of violations per API
            standards: Specific standards to generate violations for
            
        Returns:
            Dictionary mapping API IDs to generated violations
        """
        # Get all APIs
        apis, total = self.api_repo.search(query={}, size=100)
        
        if not apis:
            logger.warning("No APIs found in system")
            return {}
        
        results = {}
        for api in apis:
            violations = self.generate_violations(
                api_id=str(api.id),
                count=violations_per_api,
                standards=standards,
            )
            results[str(api.id)] = violations
            logger.info(f"Generated {len(violations)} violations for API: {api.name}")
        
        return results
    
    def _choose_violation_type(self, standard: ComplianceStandard) -> ComplianceViolationType:
        """Choose violation type for a standard."""
        # 80% chance of standard-specific, 20% chance of cross-standard
        if random.random() < 0.8:
            return random.choice(self.STANDARD_VIOLATIONS[standard])
        else:
            return random.choice(self.CROSS_STANDARD_VIOLATIONS)
    
    def _choose_from_distribution(self, distribution: dict):
        """Choose item based on probability distribution."""
        rand = random.random()
        cumulative = 0.0
        
        for item, probability in distribution.items():
            cumulative += probability
            if rand <= cumulative:
                return item
        
        return list(distribution.keys())[-1]
    
    def _create_violation(
        self,
        api_id: str,
        standard: ComplianceStandard,
        violation_type: ComplianceViolationType,
        severity: ComplianceSeverity,
        status: ComplianceStatus,
        detected_at: datetime,
    ) -> ComplianceViolation:
        """Create a compliance violation with realistic data."""
        now = datetime.utcnow()
        
        # Get regulatory reference
        regulatory_ref = None
        if standard in self.REGULATORY_REFERENCES:
            if violation_type in self.REGULATORY_REFERENCES[standard]:
                regulatory_ref = self.REGULATORY_REFERENCES[standard][violation_type]
        
        # Generate title and description
        title, description = self._generate_violation_content(
            standard, violation_type, severity
        )
        
        # Generate evidence
        evidence = self._generate_evidence(violation_type, detected_at)
        
        # Generate audit trail
        audit_trail = self._generate_audit_trail(status, detected_at)
        
        # Generate remediation documentation if remediated
        remediation_docs = None
        remediated_at = None
        if status == ComplianceStatus.REMEDIATED:
            remediation_docs = self._generate_remediation_docs(violation_type)
            remediated_at = detected_at + timedelta(days=random.randint(1, 14))
        
        # Calculate remediation deadline
        deadline_days = {
            ComplianceSeverity.CRITICAL: 7,
            ComplianceSeverity.HIGH: 30,
            ComplianceSeverity.MEDIUM: 90,
            ComplianceSeverity.LOW: 180,
        }
        remediation_deadline = detected_at + timedelta(
            days=deadline_days.get(severity, 90)
        )
        
        # Determine risk level
        risk_levels = ["financial", "reputational", "operational", "legal"]
        risk_level = random.choice(risk_levels)
        
        return ComplianceViolation(
            id=uuid4(),
            api_id=uuid4() if isinstance(api_id, str) else api_id,
            compliance_standard=standard,
            violation_type=violation_type,
            severity=severity,
            title=title,
            description=description,
            affected_endpoints=[f"/api/v1/endpoint{random.randint(1, 5)}"],
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            detected_at=detected_at,
            status=status,
            evidence=evidence,
            audit_trail=audit_trail,
            remediation_documentation=remediation_docs,
            regulatory_reference=regulatory_ref,
            risk_level=risk_level,
            remediation_deadline=remediation_deadline,
            remediated_at=remediated_at,
            last_audit_date=detected_at - timedelta(days=90),
            next_audit_date=now + timedelta(days=90),
            metadata={
                "generated": True,
                "generator_version": "1.0",
                "detection_confidence": random.uniform(0.7, 1.0),
            },
        )
    
    def _generate_violation_content(
        self,
        standard: ComplianceStandard,
        violation_type: ComplianceViolationType,
        severity: ComplianceSeverity,
    ) -> tuple[str, str]:
        """Generate title and description for violation."""
        templates = {
            ComplianceViolationType.GDPR_DATA_PROTECTION_BY_DESIGN: (
                "Missing Data Protection by Design Controls",
                "API lacks privacy-by-design controls required by GDPR Article 25. "
                "Personal data processing occurs without adequate technical and "
                "organizational measures to implement data protection principles."
            ),
            ComplianceViolationType.GDPR_SECURITY_OF_PROCESSING: (
                "Inadequate Security of Processing",
                "API does not implement appropriate technical and organizational measures "
                "to ensure security of personal data processing as required by GDPR Article 32."
            ),
            ComplianceViolationType.HIPAA_ACCESS_CONTROL: (
                "Missing HIPAA Access Controls",
                "API lacks required access control mechanisms for Protected Health Information (PHI). "
                "Violates 45 CFR § 164.312(a)(1) - Technical Safeguards."
            ),
            ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY: (
                "Inadequate PHI Transmission Security",
                "API transmits PHI without adequate encryption and integrity controls. "
                "Violates 45 CFR § 164.312(e)(1) - Transmission Security."
            ),
            ComplianceViolationType.PCI_DSS_NETWORK_SECURITY: (
                "PCI-DSS Network Security Violation",
                "API handling cardholder data lacks required network security controls. "
                "Violates PCI-DSS Requirement 1 - Install and maintain firewall configuration."
            ),
            ComplianceViolationType.PCI_DSS_ENCRYPTION_IN_TRANSIT: (
                "Missing Encryption for Cardholder Data",
                "API transmits cardholder data without strong cryptography. "
                "Violates PCI-DSS Requirement 4 - Encrypt transmission of cardholder data."
            ),
            ComplianceViolationType.SOC2_SECURITY_AVAILABILITY: (
                "SOC2 Security and Availability Violation",
                "API lacks controls to ensure system security and availability. "
                "Violates SOC2 Trust Service Criteria CC6.1."
            ),
            ComplianceViolationType.SOC2_SYSTEM_MONITORING: (
                "Inadequate System Monitoring",
                "API lacks continuous monitoring and logging controls. "
                "Violates SOC2 Trust Service Criteria CC7.2."
            ),
            ComplianceViolationType.ISO_27001_ACCESS_CONTROL: (
                "ISO 27001 Access Control Deficiency",
                "API lacks adequate access control measures. "
                "Violates ISO 27001 Annex A.9 - Access Control."
            ),
            ComplianceViolationType.ISO_27001_CRYPTOGRAPHY: (
                "Missing Cryptographic Controls",
                "API does not implement required cryptographic controls. "
                "Violates ISO 27001 Annex A.10 - Cryptography."
            ),
            ComplianceViolationType.INSUFFICIENT_LOGGING_MONITORING: (
                "Insufficient Logging and Monitoring",
                "API lacks adequate logging and monitoring capabilities required "
                "by multiple compliance standards for audit trail and incident detection."
            ),
            ComplianceViolationType.INADEQUATE_ACCESS_CONTROLS: (
                "Inadequate Access Controls",
                "API implements weak or missing access control mechanisms, "
                "violating multiple compliance standards' access control requirements."
            ),
        }
        
        # Get template or use generic
        if violation_type in templates:
            title, description = templates[violation_type]
        else:
            title = f"{violation_type.value.replace('_', ' ').title()} Violation"
            description = f"API violates {standard.value.upper()} compliance requirements for {violation_type.value}."
        
        # Add severity context
        if severity == ComplianceSeverity.CRITICAL:
            description += " CRITICAL: Immediate remediation required to avoid regulatory penalties."
        elif severity == ComplianceSeverity.HIGH:
            description += " HIGH: Significant compliance risk requiring prompt attention."
        
        return title, description
    
    def _generate_evidence(
        self,
        violation_type: ComplianceViolationType,
        detected_at: datetime,
    ) -> List[Evidence]:
        """Generate evidence for violation."""
        evidence_list = []
        
        # Gateway configuration evidence
        evidence_list.append(Evidence(
            type="gateway_config",
            description="Gateway configuration analysis",
            source="gateway_api",
            timestamp=detected_at,
            data={
                "authentication_enabled": False,
                "tls_enforced": False,
                "logging_enabled": True,
            }
        ))
        
        # Traffic analysis evidence
        evidence_list.append(Evidence(
            type="traffic_log",
            description="Traffic pattern analysis",
            source="metrics",
            timestamp=detected_at,
            data={
                "unencrypted_requests": random.randint(100, 1000),
                "unauthorized_attempts": random.randint(10, 50),
                "analysis_period_hours": 24,
            }
        ))
        
        # Policy evidence
        evidence_list.append(Evidence(
            type="policy",
            description="Security policy evaluation",
            source="compliance_scanner",
            timestamp=detected_at,
            data={
                "policies_evaluated": random.randint(5, 15),
                "policies_failed": random.randint(1, 5),
                "compliance_score": random.uniform(0.4, 0.7),
            }
        ))
        
        return evidence_list
    
    def _generate_audit_trail(
        self,
        status: ComplianceStatus,
        detected_at: datetime,
    ) -> List[AuditTrailEntry]:
        """Generate audit trail for violation."""
        trail = []
        
        # Detection entry
        trail.append(AuditTrailEntry(
            timestamp=detected_at,
            action="violation_detected",
            performed_by="compliance_scanner",
            details="Automated compliance scan detected violation",
            status_before=None,
            status_after=ComplianceStatus.OPEN.value,
        ))
        
        # Additional entries based on status
        if status in [ComplianceStatus.IN_PROGRESS, ComplianceStatus.REMEDIATED]:
            trail.append(AuditTrailEntry(
                timestamp=detected_at + timedelta(hours=random.randint(1, 48)),
                action="remediation_started",
                performed_by="security_team",
                details="Remediation work initiated",
                status_before=ComplianceStatus.OPEN.value,
                status_after=ComplianceStatus.IN_PROGRESS.value,
            ))
        
        if status == ComplianceStatus.REMEDIATED:
            trail.append(AuditTrailEntry(
                timestamp=detected_at + timedelta(days=random.randint(1, 14)),
                action="remediation_completed",
                performed_by="security_team",
                details="Remediation verified and completed",
                status_before=ComplianceStatus.IN_PROGRESS.value,
                status_after=ComplianceStatus.REMEDIATED.value,
            ))
        
        return trail
    
    def _generate_remediation_docs(
        self,
        violation_type: ComplianceViolationType,
    ) -> List[RemediationDocumentation]:
        """Generate remediation documentation."""
        docs = []
        
        # Gateway policy application
        docs.append(RemediationDocumentation(
            action="Applied authentication policy to Gateway",
            type="gateway_policy",
            status="completed",
            performed_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
            performed_by="security_team",
            gateway_policy_id=f"policy-{uuid4().hex[:8]}",
            verification_method="automated_rescan",
            verification_status="passed",
            notes="OAuth2 authentication policy applied and verified",
        ))
        
        # Configuration update
        docs.append(RemediationDocumentation(
            action="Updated API Gateway configuration",
            type="configuration",
            status="completed",
            performed_at=datetime.utcnow() - timedelta(days=random.randint(1, 7)),
            performed_by="devops_team",
            gateway_policy_id=None,
            verification_method="manual_review",
            verification_status="passed",
            notes="TLS 1.3 enforcement enabled, HTTP disabled",
        ))
        
        return docs


async def main():
    """Main entry point for mock data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate mock compliance violation data"
    )
    parser.add_argument(
        "--api-id",
        type=str,
        help="Specific API ID to generate violations for"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=10,
        help="Number of violations to generate per API (default: 10)"
    )
    parser.add_argument(
        "--all-apis",
        action="store_true",
        help="Generate violations for all APIs in the system"
    )
    parser.add_argument(
        "--standards",
        nargs="+",
        choices=["gdpr", "hipaa", "soc2", "pci_dss", "iso_27001"],
        help="Specific compliance standards to generate violations for"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = MockComplianceGenerator()
    
    # Convert standard names to enum
    standards = None
    if args.standards:
        standards = [ComplianceStandard(s) for s in args.standards]
    
    try:
        if args.all_apis:
            # Generate for all APIs
            logger.info("Generating violations for all APIs...")
            results = generator.generate_violations_for_all_apis(
                violations_per_api=args.count,
                standards=standards,
            )
            logger.info(f"Generated violations for {len(results)} APIs")
        
        elif args.api_id:
            # Generate for specific API
            logger.info(f"Generating {args.count} violations for API {args.api_id}...")
            violations = generator.generate_violations(
                api_id=args.api_id,
                count=args.count,
                standards=standards,
            )
            logger.info(f"Generated {len(violations)} violations")
        
        else:
            logger.error("Must specify either --api-id or --all-apis")
            return 1
        
        logger.info("Mock compliance data generation complete!")
        return 0
    
    except Exception as e:
        logger.error(f"Error generating mock data: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import asyncio
    exit_code = asyncio.run(main())
    sys.exit(exit_code)


# Made with Bob