#!/usr/bin/env python3
"""
Test frontend integration with rate limit policies API.
Simulates what the browser does when loading the Rate Limiting tab.
"""

import requests
import json

def test_rate_limit_api():
    """Test the rate limit API endpoint."""
    print("Testing Rate Limit API Integration...")
    print("=" * 60)
    
    # Test the API endpoint
    url = "http://localhost:8000/api/v1/rate-limits"
    print(f"\n1. Fetching from: {url}")
    
    try:
        response = requests.get(url)
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response Keys: {list(data.keys())}")
            print(f"   Total Policies: {data.get('total', 0)}")
            print(f"   Items Count: {len(data.get('items', []))}")
            
            # Check if items exist
            items = data.get('items', [])
            if items:
                print(f"\n2. Policy Details:")
                for i, policy in enumerate(items, 1):
                    print(f"\n   Policy {i}:")
                    print(f"     - Name: {policy.get('policy_name')}")
                    print(f"     - Type: {policy.get('policy_type')}")
                    print(f"     - Status: {policy.get('status')}")
                    print(f"     - ID: {policy.get('id')}")
                    
                    # Check thresholds
                    thresholds = policy.get('limit_thresholds', {})
                    if thresholds:
                        print(f"     - Requests/sec: {thresholds.get('requests_per_second')}")
                        print(f"     - Requests/min: {thresholds.get('requests_per_minute')}")
                
                # Count active policies
                active_count = len([p for p in items if p.get('status') == 'active'])
                print(f"\n3. Statistics:")
                print(f"   - Active Policies: {active_count}")
                print(f"   - Total Policies: {len(items)}")
                
                # Calculate average effectiveness
                policies_with_score = [p for p in items if p.get('effectiveness_score') is not None]
                if policies_with_score:
                    avg_effectiveness = sum(p.get('effectiveness_score', 0) for p in policies_with_score) / len(policies_with_score)
                    print(f"   - Avg Effectiveness: {avg_effectiveness * 100:.0f}%")
                
                print(f"\n✓ SUCCESS: API is returning {len(items)} policies correctly")
                print(f"✓ Frontend should display these policies in the Rate Limiting tab")
                
            else:
                print("\n✗ ERROR: API returned 0 items")
                print("  This is why the frontend shows 'No rate limit policies found'")
                
        else:
            print(f"\n✗ ERROR: API returned status {response.status_code}")
            print(f"  Response: {response.text}")
            
    except Exception as e:
        print(f"\n✗ ERROR: Failed to connect to API")
        print(f"  Error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    test_rate_limit_api()

# Made with Bob
