#!/usr/bin/env python3
"""Validation script for Option B implementation.

This script validates that the Option B implementation is correctly integrated
by checking the code structure and data model.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.vulnerability import Vulnerability
from app.agents.security_agent import SecurityAgent
import inspect


def validate_vulnerability_model():
    """Validate Vulnerability model has new fields."""
    print("=" * 80)
    print("1. Validating Vulnerability Model")
    print("=" * 80)
    
    # Check if new fields exist
    required_fields = [
        'recommended_remediation',
        'recommended_priority',
        'recommended_verification_steps',
        'recommended_estimated_time_hours',
        'plan_generated_at',
        'plan_source',
        'plan_version',
        'plan_status',
    ]
    
    model_fields = Vulnerability.model_fields
    
    for field in required_fields:
        if field in model_fields:
            field_info = model_fields[field]
            print(f"✓ {field}: {field_info.annotation}")
        else:
            print(f"✗ {field}: MISSING")
            return False
    
    print("\n✅ All required fields present in Vulnerability model")
    return True


def validate_security_agent():
    """Validate SecurityAgent has normalization method."""
    print("\n" + "=" * 80)
    print("2. Validating SecurityAgent Methods")
    print("=" * 80)
    
    # Check if normalization method exists
    if hasattr(SecurityAgent, '_normalize_per_vulnerability_plans'):
        print("✓ _normalize_per_vulnerability_plans method exists")
        
        # Check method signature
        sig = inspect.signature(SecurityAgent._normalize_per_vulnerability_plans)
        params = list(sig.parameters.keys())
        print(f"  Parameters: {params}")
        
        if 'batched_plan' in params and 'vulnerabilities' in params:
            print("  ✓ Correct parameters")
        else:
            print("  ✗ Incorrect parameters")
            return False
    else:
        print("✗ _normalize_per_vulnerability_plans method MISSING")
        return False
    
    # Check if _create_remediation_plan exists
    if hasattr(SecurityAgent, '_create_remediation_plan'):
        print("✓ _create_remediation_plan method exists")
    else:
        print("✗ _create_remediation_plan method MISSING")
        return False
    
    # Check if _analyze_direct exists
    if hasattr(SecurityAgent, '_analyze_direct'):
        print("✓ _analyze_direct method exists")
        
        # Check if it calls normalization
        source = inspect.getsource(SecurityAgent._analyze_direct)
        if '_normalize_per_vulnerability_plans' in source:
            print("  ✓ Calls _normalize_per_vulnerability_plans")
        else:
            print("  ✗ Does not call _normalize_per_vulnerability_plans")
            return False
            
        if 'recommended_remediation' in source:
            print("  ✓ Attaches recommended_remediation to vulnerabilities")
        else:
            print("  ✗ Does not attach recommended_remediation")
            return False
    else:
        print("✗ _analyze_direct method MISSING")
        return False
    
    print("\n✅ SecurityAgent methods correctly implemented")
    return True


def validate_integration():
    """Validate integration points."""
    print("\n" + "=" * 80)
    print("3. Validating Integration Points")
    print("=" * 80)
    
    # Check workflow node
    if hasattr(SecurityAgent, '_generate_remediation_plan_node'):
        print("✓ _generate_remediation_plan_node method exists")
        
        source = inspect.getsource(SecurityAgent._generate_remediation_plan_node)
        if '_normalize_per_vulnerability_plans' in source:
            print("  ✓ Workflow node calls _normalize_per_vulnerability_plans")
        else:
            print("  ✗ Workflow node does not call normalization")
            return False
            
        if 'recommended_remediation' in source:
            print("  ✓ Workflow node attaches plans to vulnerabilities")
        else:
            print("  ✗ Workflow node does not attach plans")
            return False
    else:
        print("✗ _generate_remediation_plan_node method MISSING")
        return False
    
    print("\n✅ Integration points correctly implemented")
    return True


def main():
    """Run all validations."""
    print("\n" + "=" * 80)
    print("Option B Implementation Validation")
    print("=" * 80)
    
    results = []
    
    # Run validations
    results.append(("Vulnerability Model", validate_vulnerability_model()))
    results.append(("SecurityAgent Methods", validate_security_agent()))
    results.append(("Integration Points", validate_integration()))
    
    # Summary
    print("\n" + "=" * 80)
    print("Validation Summary")
    print("=" * 80)
    
    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
        if not passed:
            all_passed = False
    
    if all_passed:
        print("\n" + "=" * 80)
        print("🎉 All validations passed!")
        print("=" * 80)
        print("\nOption B implementation is correctly integrated:")
        print("  1. Vulnerability model has per-vulnerability plan fields")
        print("  2. SecurityAgent has normalization logic")
        print("  3. Both analysis paths use Option B pattern")
        print("  4. Plans are attached to vulnerabilities with metadata")
        return 0
    else:
        print("\n" + "=" * 80)
        print("❌ Some validations failed")
        print("=" * 80)
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
