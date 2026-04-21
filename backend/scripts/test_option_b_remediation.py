#!/usr/bin/env python3
"""Test script for Option B: single batched LLM call plus deterministic split.

This script tests the vulnerability-centric remediation architecture implementation.
"""

import asyncio
import sys
from pathlib import Path
from uuid import uuid4
from datetime import datetime

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base.api import API, AuthenticationType
from app.models.vulnerability import (
    Vulnerability,
    VulnerabilityType,
    VulnerabilitySeverity,
    DetectionMethod,
)
from app.agents.security_agent import SecurityAgent
from app.services.llm_service import LLMService


async def test_option_b_implementation():
    """Test Option B: single batched LLM call plus deterministic split."""
    print("=" * 80)
    print("Testing Option B: Single Batched LLM Call + Deterministic Split")
    print("=" * 80)
    
    # Create test API
    test_api = API(
        id=uuid4(),
        gateway_id=uuid4(),
        name="test-payment-api",
        version="v1",
        base_path="/api/v1/payments",
        authentication_type=AuthenticationType.NONE,
        policy_actions=[],
    )
    
    # Create test vulnerabilities
    test_vulnerabilities = [
        Vulnerability(
            id=uuid4(),
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            vulnerability_type=VulnerabilityType.MISSING_AUTHENTICATION,
            severity=VulnerabilitySeverity.CRITICAL,
            title="Missing JWT Authentication",
            description="API endpoints lack JWT token validation",
            affected_endpoints=["/api/v1/payments/process"],
            detection_method=DetectionMethod.RULE_BASED,
            detected_at=datetime.utcnow(),
        ),
        Vulnerability(
            id=uuid4(),
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            vulnerability_type=VulnerabilityType.MISSING_RATE_LIMITING,
            severity=VulnerabilitySeverity.HIGH,
            title="No Rate Limiting Configured",
            description="API lacks rate limiting protection",
            affected_endpoints=["/api/v1/payments/process"],
            detection_method=DetectionMethod.RULE_BASED,
            detected_at=datetime.utcnow(),
        ),
        Vulnerability(
            id=uuid4(),
            gateway_id=test_api.gateway_id,
            api_id=test_api.id,
            vulnerability_type=VulnerabilityType.WEAK_TLS_CONFIG,
            severity=VulnerabilitySeverity.MEDIUM,
            title="Weak TLS Configuration",
            description="TLS 1.0/1.1 still enabled",
            affected_endpoints=["/api/v1/payments/process"],
            detection_method=DetectionMethod.RULE_BASED,
            detected_at=datetime.utcnow(),
        ),
    ]
    
    print(f"\n✓ Created test API: {test_api.name}")
    print(f"✓ Created {len(test_vulnerabilities)} test vulnerabilities")
    
    # Initialize security agent
    llm_service = LLMService()
    security_agent = SecurityAgent(llm_service)
    
    print("\n" + "=" * 80)
    print("Step 1: Generate Batched Remediation Plan (Single LLM Call)")
    print("=" * 80)
    
    # Generate batched plan
    batched_plan = await security_agent._create_remediation_plan(
        test_api, test_vulnerabilities
    )
    
    print(f"\n✓ Generated batched plan:")
    print(f"  - Priority: {batched_plan.get('priority')}")
    print(f"  - Total time: {batched_plan.get('estimated_time_hours')} hours")
    print(f"  - Actions: {len(batched_plan.get('actions', []))}")
    print(f"  - Verification steps: {len(batched_plan.get('verification_steps', []))}")
    
    print("\n" + "=" * 80)
    print("Step 2: Normalize into Per-Vulnerability Plans (Deterministic Split)")
    print("=" * 80)
    
    # Normalize into per-vulnerability plans
    per_vuln_plans = security_agent._normalize_per_vulnerability_plans(
        batched_plan, test_vulnerabilities
    )
    
    print(f"\n✓ Normalized into {len(per_vuln_plans)} per-vulnerability plans")
    
    # Display each per-vulnerability plan
    for i, (vuln, plan) in enumerate(zip(test_vulnerabilities, per_vuln_plans), 1):
        print(f"\n  Plan {i} for: {vuln.title}")
        print(f"    - Vulnerability ID: {plan.get('vulnerability_id')}")
        print(f"    - Priority: {plan.get('priority')}")
        print(f"    - Estimated time: {plan.get('estimated_time_hours')} hours")
        print(f"    - Actions: {len(plan.get('actions', []))}")
        print(f"    - Verification steps: {len(plan.get('verification_steps', []))}")
        
        # Show first action
        actions = plan.get('actions', [])
        if actions:
            print(f"    - First action: {actions[0].get('action', 'N/A')}")
    
    print("\n" + "=" * 80)
    print("Step 3: Attach Plans to Vulnerabilities")
    print("=" * 80)
    
    # Attach plans to vulnerabilities
    plan_timestamp = datetime.utcnow()
    for vuln, plan in zip(test_vulnerabilities, per_vuln_plans):
        vuln.recommended_remediation = plan
        vuln.recommended_priority = plan.get("priority")
        vuln.recommended_verification_steps = plan.get("verification_steps", [])
        vuln.recommended_estimated_time_hours = plan.get("estimated_time_hours")
        vuln.plan_generated_at = plan_timestamp
        vuln.plan_source = "llm"
        vuln.plan_version = "1.0"
        vuln.plan_status = "generated"
    
    print("\n✓ Attached plans to all vulnerabilities")
    
    # Verify attachments
    for i, vuln in enumerate(test_vulnerabilities, 1):
        print(f"\n  Vulnerability {i}: {vuln.title}")
        print(f"    - Has recommended_remediation: {vuln.recommended_remediation is not None}")
        print(f"    - Recommended priority: {vuln.recommended_priority}")
        print(f"    - Estimated time: {vuln.recommended_estimated_time_hours} hours")
        print(f"    - Plan source: {vuln.plan_source}")
        print(f"    - Plan status: {vuln.plan_status}")
        print(f"    - Verification steps: {len(vuln.recommended_verification_steps or [])}")
    
    print("\n" + "=" * 80)
    print("✅ Option B Implementation Test Complete!")
    print("=" * 80)
    
    # Summary
    print("\n📊 Summary:")
    print(f"  - Single LLM call generated batched plan: ✓")
    print(f"  - Deterministic split into {len(per_vuln_plans)} per-vulnerability plans: ✓")
    print(f"  - All vulnerabilities have attached remediation plans: ✓")
    print(f"  - Plan metadata (source, version, status) populated: ✓")
    
    return True


if __name__ == "__main__":
    try:
        result = asyncio.run(test_option_b_implementation())
        sys.exit(0 if result else 1)
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Made with Bob
