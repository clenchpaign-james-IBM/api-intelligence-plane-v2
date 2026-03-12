#!/usr/bin/env python3
"""
MCP Client Integration Tests

Tests the running MCP servers (in Docker) by connecting as MCP clients
and invoking their tools through the Streamable HTTP transport.

This validates:
1. MCP server connectivity and protocol compliance
2. Tool discovery and invocation
3. Real-world usage scenarios
4. Integration with backend services
"""

import asyncio
import json
from typing import Any, Dict, List
from datetime import datetime

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    from mcp.client.sse import sse_client
    HAS_MCP_CLIENT = True
except ImportError:
    HAS_MCP_CLIENT = False
    print("⚠️  MCP client library not installed. Install with: pip install mcp")

import httpx


# ANSI color codes for output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{'=' * 70}")
    print(text)
    print(f"{'=' * 70}{Colors.END}\n")


def print_section(text: str):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{text}{Colors.END}")


def print_success(text: str):
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.YELLOW}ℹ {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}✗ {text}{Colors.END}")


class MCPClientTester:
    """Test MCP servers using MCP client protocol"""
    
    def __init__(self):
        self.discovery_url = "http://localhost:8001/sse"
        self.metrics_url = "http://localhost:8002/sse"
        self.optimization_url = "http://localhost:8004/sse"
        self.results = {
            "discovery": {"passed": 0, "failed": 0},
            "metrics": {"passed": 0, "failed": 0},
            "optimization": {"passed": 0, "failed": 0}
        }
    
    async def test_server_connectivity(self) -> bool:
        """Test basic HTTP connectivity to all MCP servers"""
        print_section("Testing: MCP Server Connectivity")
        
        servers = {
            "Discovery": "http://localhost:8001/health",
            "Metrics": "http://localhost:8002/health",
            "Optimization": "http://localhost:8004/health"
        }
        
        all_healthy = True
        async with httpx.AsyncClient() as client:
            for name, url in servers.items():
                try:
                    response = await client.get(url, timeout=5.0)
                    if response.status_code == 200:
                        data = response.json()
                        print_success(f"{name} Server: {data.get('status', 'unknown')}")
                    else:
                        print_error(f"{name} Server: HTTP {response.status_code}")
                        all_healthy = False
                except Exception as e:
                    print_error(f"{name} Server: {str(e)}")
                    all_healthy = False
        
        return all_healthy
    
    async def test_discovery_server(self):
        """Test Discovery MCP Server tools"""
        print_section("Testing: Discovery MCP Server")
        
        if not HAS_MCP_CLIENT:
            print_error("MCP client library not available")
            return
        
        try:
            async with sse_client(self.discovery_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List available tools
                    print_info("Test 1: Listing available tools...")
                    tools = await session.list_tools()
                    print_success(f"Found {len(tools.tools)} tools")
                    for tool in tools.tools:
                        print_info(f"  - {tool.name}: {tool.description}")
                    self.results["discovery"]["passed"] += 1
                    
                    # Test list_apis tool
                    print_info("\nTest 2: Invoking list_apis tool...")
                    result = await session.call_tool("list_apis", arguments={})
                    apis = json.loads(result.content[0].text)
                    print_success(f"Retrieved {len(apis)} APIs")
                    if apis:
                        sample = apis[0]
                        print_info(f"  Sample: {sample.get('name')} ({sample.get('id')})")
                    self.results["discovery"]["passed"] += 1
                    
                    # Test get_api_details tool
                    if apis:
                        print_info("\nTest 3: Invoking get_api_details tool...")
                        api_id = apis[0]["id"]
                        result = await session.call_tool("get_api_details", arguments={"api_id": api_id})
                        api_details = json.loads(result.content[0].text)
                        print_success(f"Retrieved details for: {api_details.get('name')}")
                        print_info(f"  Base Path: {api_details.get('base_path')}")
                        print_info(f"  Status: {api_details.get('status')}")
                        self.results["discovery"]["passed"] += 1
                    
                    # Test filter_shadow_apis tool
                    print_info("\nTest 4: Invoking filter_shadow_apis tool...")
                    result = await session.call_tool("filter_shadow_apis", arguments={})
                    shadow_apis = json.loads(result.content[0].text)
                    print_success(f"Found {len(shadow_apis)} shadow APIs")
                    self.results["discovery"]["passed"] += 1
                    
        except Exception as e:
            print_error(f"Discovery server test failed: {str(e)}")
            self.results["discovery"]["failed"] += 1
    
    async def test_metrics_server(self):
        """Test Metrics MCP Server tools"""
        print_section("Testing: Metrics MCP Server")
        
        if not HAS_MCP_CLIENT:
            print_error("MCP client library not available")
            return
        
        try:
            async with sse_client(self.metrics_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List available tools
                    print_info("Test 1: Listing available tools...")
                    tools = await session.list_tools()
                    print_success(f"Found {len(tools.tools)} tools")
                    for tool in tools.tools:
                        print_info(f"  - {tool.name}: {tool.description}")
                    self.results["metrics"]["passed"] += 1
                    
                    # Get an API ID first
                    async with httpx.AsyncClient() as client:
                        response = await client.get("http://localhost:8000/api/v1/apis")
                        apis = response.json()
                    
                    if apis:
                        api_id = apis[0]["id"]
                        
                        # Test get_api_metrics tool
                        print_info(f"\nTest 2: Invoking get_api_metrics for API {api_id}...")
                        result = await session.call_tool("get_api_metrics", arguments={
                            "api_id": api_id,
                            "hours": 24
                        })
                        metrics = json.loads(result.content[0].text)
                        print_success(f"Retrieved {len(metrics.get('time_series', []))} metric data points")
                        if metrics.get("summary"):
                            summary = metrics["summary"]
                            print_info(f"  Avg Response Time: {summary.get('avg_response_time', 'N/A')}ms")
                            print_info(f"  Avg Error Rate: {summary.get('avg_error_rate', 'N/A')}%")
                        self.results["metrics"]["passed"] += 1
                        
                        # Test get_api_health tool
                        print_info(f"\nTest 3: Invoking get_api_health for API {api_id}...")
                        result = await session.call_tool("get_api_health", arguments={
                            "api_id": api_id
                        })
                        health = json.loads(result.content[0].text)
                        print_success(f"Health Score: {health.get('health_score', 'N/A')}")
                        print_info(f"  Status: {health.get('status', 'N/A')}")
                        self.results["metrics"]["passed"] += 1
                    
        except Exception as e:
            print_error(f"Metrics server test failed: {str(e)}")
            self.results["metrics"]["failed"] += 1
    
    async def test_optimization_server(self):
        """Test Optimization MCP Server tools"""
        print_section("Testing: Optimization MCP Server")
        
        if not HAS_MCP_CLIENT:
            print_error("MCP client library not available")
            return
        
        try:
            async with sse_client(self.optimization_url) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # List available tools
                    print_info("Test 1: Listing available tools...")
                    tools = await session.list_tools()
                    print_success(f"Found {len(tools.tools)} tools")
                    for tool in tools.tools:
                        print_info(f"  - {tool.name}: {tool.description}")
                    self.results["optimization"]["passed"] += 1
                    
                    # Get an API ID first
                    async with httpx.AsyncClient() as client:
                        response = await client.get("http://localhost:8000/api/v1/apis")
                        apis = response.json()
                    
                    if apis:
                        api_id = apis[0]["id"]
                        
                        # Test list_predictions tool
                        print_info("\nTest 2: Invoking list_predictions tool...")
                        result = await session.call_tool("list_predictions", arguments={})
                        predictions = json.loads(result.content[0].text)
                        print_success(f"Found {len(predictions)} predictions")
                        if predictions:
                            sample = predictions[0]
                            print_info(f"  Sample: {sample.get('prediction_type')} - Confidence: {sample.get('confidence')}")
                        self.results["optimization"]["passed"] += 1
                        
                        # Test generate_predictions tool
                        print_info(f"\nTest 3: Invoking generate_predictions for API {api_id}...")
                        result = await session.call_tool("generate_predictions", arguments={
                            "api_id": api_id
                        })
                        response_data = json.loads(result.content[0].text)
                        print_success(f"Prediction generation: {response_data.get('status', 'unknown')}")
                        self.results["optimization"]["passed"] += 1
                        
                        # Test list_recommendations tool
                        print_info("\nTest 4: Invoking list_recommendations tool...")
                        result = await session.call_tool("list_recommendations", arguments={})
                        recommendations = json.loads(result.content[0].text)
                        print_success(f"Found {len(recommendations)} recommendations")
                        if recommendations:
                            sample = recommendations[0]
                            print_info(f"  Sample: {sample.get('title')}")
                            print_info(f"  Expected Improvement: {sample.get('expected_improvement', 'N/A')}%")
                        self.results["optimization"]["passed"] += 1
                        
                        # Test list_rate_limit_policies tool
                        print_info("\nTest 5: Invoking list_rate_limit_policies tool...")
                        result = await session.call_tool("list_rate_limit_policies", arguments={})
                        policies = json.loads(result.content[0].text)
                        print_success(f"Found {len(policies)} rate limit policies")
                        if policies:
                            sample = policies[0]
                            print_info(f"  Sample: {sample.get('policy_name')}")
                            print_info(f"  Type: {sample.get('policy_type')}")
                        self.results["optimization"]["passed"] += 1
                        
                        # Test create_rate_limit_policy tool
                        print_info(f"\nTest 6: Invoking create_rate_limit_policy for API {api_id}...")
                        policy_name = f"MCP Test Policy {datetime.utcnow().timestamp()}"
                        result = await session.call_tool("create_rate_limit_policy", arguments={
                            "api_id": api_id,
                            "policy_name": policy_name,
                            "policy_type": "fixed",
                            "max_requests": 100,
                            "window_seconds": 60
                        })
                        policy = json.loads(result.content[0].text)
                        print_success(f"Created policy: {policy.get('id')}")
                        print_info(f"  Name: {policy.get('policy_name')}")
                        self.results["optimization"]["passed"] += 1
                    
        except Exception as e:
            print_error(f"Optimization server test failed: {str(e)}")
            self.results["optimization"]["failed"] += 1
    
    def print_summary(self):
        """Print test summary"""
        print_header("Test Summary")
        
        total_passed = sum(r["passed"] for r in self.results.values())
        total_failed = sum(r["failed"] for r in self.results.values())
        total_tests = total_passed + total_failed
        
        for server, results in self.results.items():
            status = f"{Colors.GREEN}✓ PASSED{Colors.END}" if results["failed"] == 0 else f"{Colors.RED}✗ FAILED{Colors.END}"
            print(f"{server.capitalize():20} {status}")
            print(f"  Passed: {results['passed']}, Failed: {results['failed']}")
        
        print(f"\n{Colors.BOLD}Total: {total_passed}/{total_tests} tests passed{Colors.END}")
        
        if total_failed == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All MCP client tests passed!{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Check output above.{Colors.END}")


async def main():
    """Run all MCP client tests"""
    print_header("MCP Client Integration Tests\nTesting Running MCP Servers via MCP Protocol")
    
    if not HAS_MCP_CLIENT:
        print_error("MCP client library not installed!")
        print_info("Install with: pip install mcp")
        return
    
    print_info(f"Test Time: {datetime.utcnow().isoformat()}Z")
    
    tester = MCPClientTester()
    
    # Test connectivity first
    if not await tester.test_server_connectivity():
        print_error("\nSome servers are not healthy. Aborting tests.")
        return
    
    # Run all server tests
    await tester.test_discovery_server()
    await tester.test_metrics_server()
    await tester.test_optimization_server()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
