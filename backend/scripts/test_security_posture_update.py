"""Test script to verify security posture updates after vulnerability remediation.

This script:
1. Gets initial security posture for a gateway
2. Remediates a vulnerability
3. Verifies the security posture is updated correctly
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.services.security_service import SecurityService
from app.models.vulnerability import VulnerabilityStatus


async def test_security_posture_update():
    """Test that security posture updates after remediation."""
    print("=" * 80)
    print("Testing Security Posture Update After Remediation")
    print("=" * 80)
    
    # Initialize repositories and services
    settings = Settings()
    gateway_repo = GatewayRepository()
    api_repo = APIRepository()
    vuln_repo = VulnerabilityRepository()
    security_service = SecurityService(settings)
    
    # Get first gateway
    gateways, total = gateway_repo.search({"match_all": {}}, size=1)
    if not gateways:
        print("❌ No gateways found. Please run init_opensearch.py first.")
        return False
    
    gateway = gateways[0]
    gateway_id = gateway.id
    print(f"\n✓ Using gateway: {gateway.name} ({gateway_id})")
    
    # Get APIs for this gateway
    apis, _ = api_repo.find_by_gateway(gateway_id, size=10)
    if not apis:
        print(f"❌ No APIs found for gateway {gateway_id}")
        return False
    
    print(f"✓ Found {len(apis)} APIs in gateway")
    
    # Get initial security posture for the gateway
    print("\n" + "-" * 80)
    print("Step 1: Get Initial Security Posture")
    print("-" * 80)
    
    initial_posture = await security_service.get_security_posture(gateway_id=gateway_id)
    print(f"\nInitial Security Posture:")
    print(f"  Total Vulnerabilities: {initial_posture['total_vulnerabilities']}")
    print(f"  By Severity: {initial_posture['by_severity']}")
    print(f"  By Status: {initial_posture['by_status']}")
    print(f"  Risk Score: {initial_posture['risk_score']}")
    print(f"  Remediation Rate: {initial_posture['remediation_rate']}%")
    
    # Find an open vulnerability to remediate
    print("\n" + "-" * 80)
    print("Step 2: Find Open Vulnerability")
    print("-" * 80)
    
    open_vulns = await vuln_repo.find_open_vulnerabilities(limit=100)
    
    # Filter to only vulnerabilities in this gateway
    gateway_api_ids = {str(api.id) for api in apis}
    gateway_vulns = [v for v in open_vulns if str(v.api_id) in gateway_api_ids]
    
    if not gateway_vulns:
        print(f"❌ No open vulnerabilities found for gateway {gateway_id}")
        print("   Run a security scan first to generate vulnerabilities.")
        return False
    
    test_vuln = gateway_vulns[0]
    print(f"\n✓ Found vulnerability to test:")
    print(f"  ID: {test_vuln.id}")
    print(f"  Title: {test_vuln.title}")
    print(f"  Severity: {test_vuln.severity}")
    print(f"  Status: {test_vuln.status}")
    print(f"  API ID: {test_vuln.api_id}")
    
    # Manually update vulnerability status to remediated (simulating remediation)
    print("\n" + "-" * 80)
    print("Step 3: Simulate Vulnerability Remediation")
    print("-" * 80)
    
    vuln_repo.update(
        str(test_vuln.id),
        {
            "status": VulnerabilityStatus.REMEDIATED.value,
            "verification_status": "verified"
        }
    )
    print(f"✓ Updated vulnerability {test_vuln.id} to REMEDIATED status")
    
    # Get updated security posture
    print("\n" + "-" * 80)
    print("Step 4: Get Updated Security Posture")
    print("-" * 80)
    
    updated_posture = await security_service.get_security_posture(gateway_id=gateway_id)
    print(f"\nUpdated Security Posture:")
    print(f"  Total Vulnerabilities: {updated_posture['total_vulnerabilities']}")
    print(f"  By Severity: {updated_posture['by_severity']}")
    print(f"  By Status: {updated_posture['by_status']}")
    print(f"  Risk Score: {updated_posture['risk_score']}")
    print(f"  Remediation Rate: {updated_posture['remediation_rate']}%")
    
    # Verify the changes
    print("\n" + "-" * 80)
    print("Step 5: Verify Changes")
    print("-" * 80)
    
    success = True
    
    # Check if remediated count increased
    initial_remediated = initial_posture['by_status'].get('remediated', 0)
    updated_remediated = updated_posture['by_status'].get('remediated', 0)
    
    if updated_remediated > initial_remediated:
        print(f"✓ Remediated count increased: {initial_remediated} → {updated_remediated}")
    else:
        print(f"❌ Remediated count did not increase: {initial_remediated} → {updated_remediated}")
        success = False
    
    # Check if open count decreased
    initial_open = initial_posture['by_status'].get('open', 0)
    updated_open = updated_posture['by_status'].get('open', 0)
    
    if updated_open < initial_open:
        print(f"✓ Open count decreased: {initial_open} → {updated_open}")
    else:
        print(f"❌ Open count did not decrease: {initial_open} → {updated_open}")
        success = False
    
    # Check if remediation rate increased
    if updated_posture['remediation_rate'] > initial_posture['remediation_rate']:
        print(f"✓ Remediation rate increased: {initial_posture['remediation_rate']:.1f}% → {updated_posture['remediation_rate']:.1f}%")
    else:
        print(f"❌ Remediation rate did not increase: {initial_posture['remediation_rate']:.1f}% → {updated_posture['remediation_rate']:.1f}%")
        success = False
    
    # Restore original status for cleanup
    print("\n" + "-" * 80)
    print("Step 6: Cleanup - Restore Original Status")
    print("-" * 80)
    
    vuln_repo.update(
        str(test_vuln.id),
        {
            "status": VulnerabilityStatus.OPEN.value,
            "verification_status": None
        }
    )
    print(f"✓ Restored vulnerability {test_vuln.id} to original OPEN status")
    
    # Final result
    print("\n" + "=" * 80)
    if success:
        print("✅ TEST PASSED: Security posture correctly updates after remediation")
    else:
        print("❌ TEST FAILED: Security posture did not update correctly")
    print("=" * 80)
    
    return success


if __name__ == "__main__":
    result = asyncio.run(test_security_posture_update())
    sys.exit(0 if result else 1)

# Made with Bob
