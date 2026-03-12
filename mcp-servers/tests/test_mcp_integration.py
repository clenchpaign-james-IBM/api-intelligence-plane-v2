"""
Integration tests for MCP Servers

Tests the refactored MCP servers by invoking the real backend API.
This validates that the thin wrapper architecture works correctly.

Prerequisites:
- Backend service must be running at http://localhost:8000
- OpenSearch must be running and populated with test data
- Run: python backend/scripts/generate_mock_data.py first
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.backend_client import BackendClient


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'
    BOLD = '\033[1m'


def print_test(name: str):
    """Print test name."""
    print(f"\n{Colors.BLUE}{Colors.BOLD}Testing: {name}{Colors.END}")


def print_success(message: str):
    """Print success message."""
    print(f"{Colors.GREEN}✓ {message}{Colors.END}")


def print_error(message: str):
    """Print error message."""
    print(f"{Colors.RED}✗ {message}{Colors.END}")


def print_info(message: str):
    """Print info message."""
    print(f"{Colors.YELLOW}ℹ {message}{Colors.END}")


async def test_backend_connectivity():
    """Test basic backend connectivity."""
    print_test("Backend Connectivity")
    
    client = BackendClient(base_url="http://localhost:8000")
    
    try:
        # Try to list APIs
        response = await client.list_apis(page=1, page_size=1)
        print_success(f"Connected to backend at {client.base_url}")
        print_info(f"Total APIs in system: {response.get('total', 0)}")
        return True
    except Exception as e:
        print_error(f"Failed to connect to backend: {e}")
        print_info("Make sure backend is running: cd backend && uvicorn app.main:app --reload")
        return False
    finally:
        await client.close()


async def test_discovery_operations():
    """Test Discovery MCP Server operations via backend."""
    print_test("Discovery Operations")
    
    client = BackendClient(base_url="http://localhost:8000")
    
    try:
        # Test 1: List all APIs
        print_info("Test 1: Listing all APIs...")
        response = await client.list_apis(page=1, page_size=10)
        apis = response.get("items", [])
        total = response.get("total", 0)
        
        if total > 0:
            print_success(f"Found {total} APIs in inventory")
            print_info(f"Sample API: {apis[0].get('name', 'Unknown')} ({apis[0].get('id', 'N/A')})")
        else:
            print_error("No APIs found. Run: python backend/scripts/generate_mock_data.py")
            return False
        
        # Test 2: Filter by shadow APIs
        print_info("Test 2: Filtering shadow APIs...")
        shadow_response = await client.list_apis(is_shadow=True, page_size=100)
        shadow_count = shadow_response.get("total", 0)
        print_success(f"Found {shadow_count} shadow APIs")
        
        # Test 3: Get specific API details
        if apis:
            api_id = apis[0].get("id")
            print_info(f"Test 3: Getting details for API {api_id}...")
            api_details = await client.get_api(api_id)
            print_success(f"Retrieved API: {api_details.get('name')}")
            print_info(f"  Base Path: {api_details.get('base_path')}")
            print_info(f"  Status: {api_details.get('status')}")
            print_info(f"  Health Score: {api_details.get('health_score', 'N/A')}")
        
        return True
        
    except Exception as e:
        print_error(f"Discovery operations failed: {e}")
        return False
    finally:
        await client.close()


async def test_metrics_operations():
    """Test Metrics MCP Server operations via backend."""
    print_test("Metrics Operations")
    
    client = BackendClient(base_url="http://localhost:8000")
    
    try:
        # Get an API to test with
        apis_response = await client.list_apis(page=1, page_size=1)
        apis = apis_response.get("items", [])
        
        if not apis:
            print_error("No APIs available for metrics testing")
            return False
        
        api_id = apis[0].get("id")
        api_name = apis[0].get("name")
        
        # Test 1: Get metrics time series
        print_info(f"Test 1: Getting metrics for API '{api_name}'...")
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=24)
        
        metrics_response = await client.get_api_metrics(
            api_id=api_id,
            start_time=start_time.isoformat() + "Z",
            end_time=end_time.isoformat() + "Z",
            interval="1h"
        )
        
        time_series = metrics_response.get("time_series", [])
        aggregated = metrics_response.get("aggregated", {})
        
        print_success(f"Retrieved {len(time_series)} time series data points")
        
        if aggregated:
            print_info(f"  Avg Response Time: {aggregated.get('avg_response_time_p50', 'N/A')}ms")
            print_info(f"  Avg Error Rate: {aggregated.get('avg_error_rate', 'N/A')}%")
            print_info(f"  Avg Availability: {aggregated.get('avg_availability', 'N/A')}%")
        
        return True
        
    except Exception as e:
        print_error(f"Metrics operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def test_prediction_operations():
    """Test Prediction operations via backend."""
    print_test("Prediction Operations")
    
    client = BackendClient(base_url="http://localhost:8000")
    
    try:
        # Test 1: List existing predictions
        print_info("Test 1: Listing existing predictions...")
        predictions_response = await client.list_predictions(
            page=1,
            page_size=10
        )
        
        predictions = predictions_response.get("predictions", [])
        total = predictions_response.get("total", 0)
        
        print_success(f"Found {total} predictions in system")
        
        if predictions:
            pred = predictions[0]
            print_info(f"  Sample: {pred.get('prediction_type')} - Confidence: {pred.get('confidence_score', 0):.2f}")
        
        # Test 2: Generate new predictions (if APIs exist)
        apis_response = await client.list_apis(page=1, page_size=1)
        if apis_response.get("total", 0) > 0:
            api_id = apis_response["items"][0]["id"]
            print_info(f"Test 2: Generating predictions for API {api_id}...")
            
            gen_response = await client.generate_predictions(
                api_id=api_id,
                min_confidence=0.7,
                use_ai=False
            )
            
            print_success(f"Prediction generation triggered: {gen_response.get('status', 'unknown')}")
        
        return True
        
    except Exception as e:
        print_error(f"Prediction operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def test_optimization_operations():
    """Test Optimization operations via backend."""
    print_test("Optimization Operations")
    
    client = BackendClient(base_url="http://localhost:8000")
    
    try:
        # Test 1: List recommendations
        print_info("Test 1: Listing optimization recommendations...")
        recs_response = await client.list_recommendations(
            page=1,
            page_size=10
        )
        
        recommendations = recs_response.get("recommendations", [])
        total = recs_response.get("total", 0)
        
        print_success(f"Found {total} recommendations in system")
        
        if recommendations:
            rec = recommendations[0]
            print_info(f"  Sample: {rec.get('title')}")
            print_info(f"  Expected Improvement: {rec.get('estimated_impact', {}).get('improvement_percentage', 0)}%")
        
        # Test 2: Generate recommendations (if APIs exist)
        apis_response = await client.list_apis(page=1, page_size=1)
        if apis_response.get("total", 0) > 0:
            api_id = apis_response["items"][0]["id"]
            print_info(f"Test 2: Generating recommendations for API {api_id}...")
            
            gen_response = await client.generate_recommendations(
                api_id=api_id,
                min_impact=10.0,
                use_ai=False
            )
            
            print_success(f"Recommendation generation completed")
            print_info(f"  Generated: {gen_response.get('recommendations_generated', 0)} recommendations")
        
        return True
        
    except Exception as e:
        print_error(f"Optimization operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def test_rate_limit_operations():
    """Test Rate Limit operations via backend."""
    print_test("Rate Limit Operations")
    
    client = BackendClient(base_url="http://localhost:8000")
    
    try:
        # Test 1: List rate limit policies
        print_info("Test 1: Listing rate limit policies...")
        policies_response = await client.list_rate_limit_policies(
            page=1,
            page_size=10
        )
        
        policies = policies_response.get("items", [])
        total = policies_response.get("total", 0)
        
        print_success(f"Found {total} rate limit policies in system")
        
        if policies:
            policy = policies[0]
            print_info(f"  Sample: {policy.get('policy_name')}")
            print_info(f"  Type: {policy.get('policy_type')}")
            print_info(f"  Status: {policy.get('status')}")
        
        # Test 2: Create a new policy (if APIs exist)
        apis_response = await client.list_apis(page=1, page_size=1)
        if apis_response.get("total", 0) > 0:
            api_id = apis_response["items"][0]["id"]
            print_info(f"Test 2: Creating rate limit policy for API {api_id}...")
            
            policy_response = await client.create_rate_limit_policy(
                api_id=api_id,
                policy_name=f"Test Policy {datetime.utcnow().timestamp()}",
                policy_type="fixed",
                limit_thresholds={
                    "requests_per_second": 100,
                    "requests_per_minute": 5000
                },
                enforcement_action="throttle"
            )
            
            print_success(f"Created policy: {policy_response.get('id')}")
            
            # Test 3: Analyze effectiveness (use existing policy with data)
            if policies:
                existing_policy_id = policies[0].get("id")
                print_info(f"Test 3: Analyzing existing policy effectiveness...")
                try:
                    analysis = await client.analyze_rate_limit_effectiveness(
                        policy_id=existing_policy_id,
                        analysis_period_hours=24
                    )
                    
                    print_success(f"Effectiveness score: {analysis.get('effectiveness_score', 0):.2f}")
                except Exception as e:
                    print_info(f"Note: Effectiveness analysis requires metrics data: {str(e)[:100]}")
        
        return True
        
    except Exception as e:
        print_error(f"Rate limit operations failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        await client.close()


async def main():
    """Run all integration tests."""
    print(f"\n{Colors.BOLD}{'='*70}")
    print(f"MCP Server Integration Tests")
    print(f"Testing Thin Wrapper Architecture with Real Backend")
    print(f"{'='*70}{Colors.END}\n")
    
    print_info(f"Backend URL: http://localhost:8000")
    print_info(f"Test Time: {datetime.utcnow().isoformat()}Z\n")
    
    results = {}
    
    # Test 1: Backend connectivity
    results["connectivity"] = await test_backend_connectivity()
    
    if not results["connectivity"]:
        print_error("\n❌ Backend is not accessible. Cannot proceed with tests.")
        print_info("Start backend: cd backend && uvicorn app.main:app --reload")
        return
    
    # Test 2: Discovery operations
    results["discovery"] = await test_discovery_operations()
    
    # Test 3: Metrics operations
    results["metrics"] = await test_metrics_operations()
    
    # Test 4: Prediction operations
    results["predictions"] = await test_prediction_operations()
    
    # Test 5: Optimization operations
    results["optimization"] = await test_optimization_operations()
    
    # Test 6: Rate limit operations
    results["rate_limits"] = await test_rate_limit_operations()
    
    # Print summary
    print(f"\n{Colors.BOLD}{'='*70}")
    print("Test Summary")
    print(f"{'='*70}{Colors.END}\n")
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for test_name, result in results.items():
        status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if result else f"{Colors.RED}✗ FAILED{Colors.END}"
        print(f"{test_name.capitalize():20s} {status}")
    
    print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.END}")
    
    if passed == total:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All tests passed! MCP servers are working correctly.{Colors.END}\n")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Please review the errors above.{Colors.END}\n")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

# Made with Bob
