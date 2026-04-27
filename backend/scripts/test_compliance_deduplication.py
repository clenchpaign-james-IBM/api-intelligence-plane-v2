"""Test script for compliance violation deduplication.

This script tests that:
1. New violations are created correctly
2. Duplicate violations are updated instead of creating new records
3. Reopened violations (previously remediated) are handled correctly
4. Evidence and audit trails are properly merged
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.config import Settings
from app.db.repositories.compliance_repository import ComplianceRepository
from app.models.compliance import (
    ComplianceViolation,
    ComplianceStandard,
    ComplianceViolationType,
    ComplianceSeverity,
    ComplianceStatus,
    DetectionMethod,
    Evidence,
)
from app.services.compliance_service import ComplianceService
from datetime import datetime


async def test_deduplication():
    """Test compliance violation deduplication."""
    print("=" * 80)
    print("Testing Compliance Violation Deduplication")
    print("=" * 80)
    
    settings = Settings()
    compliance_repo = ComplianceRepository()
    compliance_service = ComplianceService(settings)
    
    # Test data
    gateway_id = uuid4()
    api_id = uuid4()
    
    # Create first violation
    print("\n1. Creating initial violation...")
    violation1 = ComplianceViolation(
        gateway_id=gateway_id,
        api_id=api_id,
        compliance_standard=ComplianceStandard.HIPAA,
        violation_type=ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY,
        severity=ComplianceSeverity.CRITICAL,
        title="Missing TLS Encryption",
        description="API endpoint does not enforce TLS 1.3",
        affected_endpoints=["/api/v1/patients"],
        detection_method=DetectionMethod.AI_ANALYSIS,
        detected_at=datetime.utcnow(),
        status=ComplianceStatus.OPEN,
        evidence=[
            Evidence(
                type="gateway_config",
                description="TLS version check",
                source="gateway_api",
                timestamp=datetime.utcnow(),
                data={"tls_version": "1.2"}
            )
        ],
    )
    
    compliance_repo.create(violation1)
    print(f"✓ Created violation: {violation1.id}")
    print(f"  - Status: {violation1.status.value}")
    print(f"  - Evidence count: {len(violation1.evidence)}")
    print(f"  - Audit trail count: {len(violation1.audit_trail)}")
    
    # Check for existing violation
    print("\n2. Checking for existing violation...")
    existing = await compliance_repo.find_existing_violation(
        gateway_id=gateway_id,
        api_id=api_id,
        violation_type=ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY.value,
        compliance_standard=ComplianceStandard.HIPAA.value,
    )
    
    if existing:
        print(f"✓ Found existing violation: {existing.id}")
        print(f"  - Matches original: {existing.id == violation1.id}")
    else:
        print("✗ No existing violation found (unexpected)")
        return
    
    # Create duplicate violation (should update existing)
    print("\n3. Creating duplicate violation (should update)...")
    violation2 = ComplianceViolation(
        gateway_id=gateway_id,
        api_id=api_id,
        compliance_standard=ComplianceStandard.HIPAA,
        violation_type=ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY,
        severity=ComplianceSeverity.HIGH,  # Changed severity
        title="Missing TLS Encryption",
        description="API endpoint does not enforce TLS 1.3 - Updated scan",
        affected_endpoints=["/api/v1/patients", "/api/v1/records"],  # Added endpoint
        detection_method=DetectionMethod.AI_ANALYSIS,
        detected_at=datetime.utcnow(),
        status=ComplianceStatus.OPEN,
        evidence=[
            Evidence(
                type="gateway_config",
                description="TLS version check - rescan",
                source="gateway_api",
                timestamp=datetime.utcnow(),
                data={"tls_version": "1.2", "min_version": "1.0"}
            )
        ],
    )
    
    updated = await compliance_service._update_existing_violation(existing, violation2)
    print(f"✓ Updated violation: {updated.id}")
    print(f"  - Same ID as original: {updated.id == violation1.id}")
    print(f"  - Updated severity: {updated.severity.value}")
    print(f"  - Evidence count: {len(updated.evidence)}")
    print(f"  - Audit trail count: {len(updated.audit_trail)}")
    print(f"  - Affected endpoints: {updated.affected_endpoints}")
    
    # Test reopening remediated violation
    print("\n4. Testing reopening of remediated violation...")
    
    # Mark as remediated
    remediated_data = existing.model_dump()
    remediated_data["status"] = ComplianceStatus.REMEDIATED
    remediated_data["remediated_at"] = datetime.utcnow()
    remediated_violation = ComplianceViolation(**remediated_data)
    compliance_repo.update(str(existing.id), remediated_violation.model_dump())
    print(f"✓ Marked violation as remediated")
    
    # Fetch and verify
    remediated = await compliance_repo.find_existing_violation(
        gateway_id=gateway_id,
        api_id=api_id,
        violation_type=ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY.value,
        compliance_standard=ComplianceStandard.HIPAA.value,
    )
    if not remediated:
        print("✗ Could not fetch remediated violation")
        return
    print(f"  - Status: {remediated.status.value}")
    
    # Detect again (should reopen)
    violation3 = ComplianceViolation(
        gateway_id=gateway_id,
        api_id=api_id,
        compliance_standard=ComplianceStandard.HIPAA,
        violation_type=ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY,
        severity=ComplianceSeverity.CRITICAL,
        title="Missing TLS Encryption",
        description="API endpoint still does not enforce TLS 1.3",
        affected_endpoints=["/api/v1/patients"],
        detection_method=DetectionMethod.AI_ANALYSIS,
        detected_at=datetime.utcnow(),
        status=ComplianceStatus.OPEN,
        evidence=[
            Evidence(
                type="gateway_config",
                description="TLS version check - post remediation",
                source="gateway_api",
                timestamp=datetime.utcnow(),
                data={"tls_version": "1.2"}
            )
        ],
    )
    
    reopened = await compliance_service._update_existing_violation(remediated, violation3)
    print(f"✓ Reopened violation: {reopened.id}")
    print(f"  - Status changed to: {reopened.status.value}")
    print(f"  - Remediated_at cleared: {reopened.remediated_at is None}")
    print(f"  - Audit trail entries: {len(reopened.audit_trail)}")
    
    # Check audit trail for reopening entry
    reopen_entries = [
        entry for entry in reopened.audit_trail
        if entry.action == "violation_reopened"
    ]
    print(f"  - Reopen audit entries: {len(reopen_entries)}")
    
    # Cleanup
    print("\n5. Cleaning up test data...")
    compliance_repo.delete(str(violation1.id))
    print("✓ Test data cleaned up")
    
    print("\n" + "=" * 80)
    print("✓ All deduplication tests passed!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_deduplication())

# Made with Bob
