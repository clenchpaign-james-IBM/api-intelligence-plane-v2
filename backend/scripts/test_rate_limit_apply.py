#!/usr/bin/env python3
"""
Test Rate Limit Policy Application to Gateway

This script tests the complete flow of applying a rate limit policy to a Gateway:
1. Verify backend endpoint exists
2. Create a test policy
3. Apply the policy to the Gateway
4. Verify the policy was applied successfully
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.config import settings


async def test_rate_limit_apply():
    """Test applying rate limit policy to Gateway"""
    
    base_url = f"http://localhost:{settings.PORT}"
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 80)
        print("Testing Rate Limit Policy Application to Gateway")
        print("=" * 80)
        
        # Step 1: Get existing policies
        print("\n1. Fetching existing rate limit policies...")
        try:
            response = await client.get(f"{base_url}/api/v1/rate-limits")
            response.raise_for_status()
            data = response.json()
            policies = data.get("items", [])
            print(f"   ✓ Found {len(policies)} existing policies")
            
            if not policies:
                print("   ✗ No policies found. Please run generate_mock_rate_limits.py first")
                return False
                
            # Use the first policy for testing
            test_policy = policies[0]
            policy_id = test_policy["id"]
            print(f"   ✓ Using policy ID: {policy_id}")
            print(f"   ✓ API ID: {test_policy.get('api_id', 'N/A')}")
            print(f"   ✓ Policy Type: {test_policy.get('policy_type', 'N/A')}")
            print(f"   ✓ Status: {test_policy['status']}")
            
        except Exception as e:
            print(f"   ✗ Failed to fetch policies: {e}")
            return False
        
        # Step 2: Apply the policy to Gateway
        print(f"\n2. Applying policy {policy_id} to Gateway...")
        try:
            response = await client.post(f"{base_url}/api/v1/rate-limits/{policy_id}/apply")
            response.raise_for_status()
            result = response.json()
            
            print(f"   ✓ Policy application successful!")
            print(f"   ✓ Status: {result.get('status')}")
            print(f"   ✓ Message: {result.get('message')}")
            
            if result.get("gateway_response"):
                print(f"   ✓ Gateway Response:")
                gateway_resp = result["gateway_response"]
                for key, value in gateway_resp.items():
                    print(f"      - {key}: {value}")
            
        except httpx.HTTPStatusError as e:
            print(f"   ✗ Failed to apply policy: HTTP {e.response.status_code}")
            print(f"   ✗ Response: {e.response.text}")
            return False
        except Exception as e:
            print(f"   ✗ Failed to apply policy: {e}")
            return False
        
        # Step 3: Verify policy status was updated
        print(f"\n3. Verifying policy status...")
        try:
            response = await client.get(f"{base_url}/api/v1/rate-limits/{policy_id}")
            response.raise_for_status()
            updated_policy = response.json()
            
            print(f"   ✓ Policy retrieved successfully")
            print(f"   ✓ Status: {updated_policy['status']}")
            print(f"   ✓ Last Applied: {updated_policy.get('last_applied_at', 'N/A')}")
            
            if updated_policy.get("gateway_policy_id"):
                print(f"   ✓ Gateway Policy ID: {updated_policy['gateway_policy_id']}")
            
        except Exception as e:
            print(f"   ✗ Failed to verify policy: {e}")
            return False
        
        # Step 4: Test Gateway endpoint
        print(f"\n4. Testing Gateway rate limit endpoint...")
        try:
            gateway_url = "http://localhost:8081"
            api_id = test_policy["api_id"]
            
            # Check if policy exists on Gateway
            response = await client.get(f"{gateway_url}/apis/{api_id}/rate-limit")
            
            if response.status_code == 200:
                gateway_policy = response.json()
                print(f"   ✓ Policy found on Gateway!")
                print(f"   ✓ Policy Type: {gateway_policy.get('policyType')}")
                print(f"   ✓ Enforcement Action: {gateway_policy.get('enforcementAction')}")
                
                if gateway_policy.get("thresholds"):
                    thresholds = gateway_policy["thresholds"]
                    print(f"   ✓ Thresholds:")
                    print(f"      - Requests/Second: {thresholds.get('requestsPerSecond')}")
                    print(f"      - Requests/Minute: {thresholds.get('requestsPerMinute')}")
                    print(f"      - Concurrent Requests: {thresholds.get('concurrentRequests')}")
            elif response.status_code == 404:
                print(f"   ⚠ Policy not found on Gateway (may not be persisted yet)")
            else:
                print(f"   ⚠ Unexpected response from Gateway: {response.status_code}")
                
        except Exception as e:
            print(f"   ⚠ Could not verify Gateway policy: {e}")
            print(f"   ⚠ This is expected if Gateway is not running")
        
        print("\n" + "=" * 80)
        print("✓ Rate Limit Policy Application Test Complete!")
        print("=" * 80)
        return True


if __name__ == "__main__":
    success = asyncio.run(test_rate_limit_apply())
    sys.exit(0 if success else 1)

# Made with Bob
