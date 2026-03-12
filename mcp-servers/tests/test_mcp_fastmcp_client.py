#!/usr/bin/env python3
"""
MCP FastMCP Client Tests

Tests the running MCP servers (in Docker) using FastMCP's built-in client
for streamable-http transport.
"""

import asyncio
import json
from typing import Any, Dict
from datetime import datetime

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client


# ANSI color codes
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
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


class MCPServerTester:
    """Test MCP servers using FastMCP client"""
    
    def __init__(self):
        self.discovery_url = "http://localhost:8001/mcp"
        self.metrics_url = "http://localhost:8002/mcp"
        self.optimization_url = "http://localhost:8004/mcp"
        self.backend_url = "http://localhost:8000"
        self.results = {
            "discovery": {"passed": 0, "failed": 0},
            "metrics": {"passed": 0, "failed": 0},
            "optimization": {"passed": 0, "failed": 0}
        }
    
    async def test_server_health(self) -> bool:
        """Test basic health of all servers"""
        print_section("Testing: Server Health")
        
        servers = {
            "Backend": f"{self.backend_url}/",
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
                        if name == "Backend":
                            print_success(f"{name} API: Available")
                        else:
                            data = response.json()
                            print_success(f"{name} Server: {data.get('status', 'unknown')}")
                    else:
                        print_error(f"{name}: HTTP {response.status_code}")
                        all_healthy = False
                except Exception as e:
                    print_error(f"{name}: {str(e)}")
                    all_healthy = False
        
        return all_healthy
    
    async def test_discovery_server(self):
        """Test Discovery MCP Server"""
        print_section("Testing: Discovery MCP Server (Port 8001)")
        
        try:
            async with streamable_http_client(self.discovery_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize
                    print_info("Initializing MCP session...")
                    await session.initialize()
                    print_success("Session initialized")
                    self.results["discovery"]["passed"] += 1
                    
                    # List tools
                    print_info("\nTest 1: Listing available tools...")
                    tools_response = await session.list_tools()
                    tools = tools_response.tools
                    print_success(f"Found {len(tools)} tools")
                    for tool in tools:
                        print_info(f"  - {tool.name}: {tool.description[:60] if tool.description else 'No description'}...")
                    self.results["discovery"]["passed"] += 1
                    
                    # Call list_apis tool
                    print_info("\nTest 2: Calling list_apis tool...")
                    result = await session.call_tool("list_apis", arguments={})
                    if result.content and len(result.content) > 0:
                        apis = json.loads(result.content[0].text)
                        print_success(f"Retrieved {len(apis)} APIs")
                        if apis:
                            sample = apis[0]
                            print_info(f"  Sample: {sample.get('name')} ({sample.get('id')})")
                            print_info(f"  Status: {sample.get('status')}")
                        self.results["discovery"]["passed"] += 1
                        
                        # Call get_api_details
                        if apis:
                            api_id = apis[0]["id"]
                            print_info(f"\nTest 3: Calling get_api_details for {api_id}...")
                            result = await session.call_tool("get_api_details", arguments={"api_id": api_id})
                            if result.content and len(result.content) > 0:
                                api_details = json.loads(result.content[0].text)
                                print_success(f"Retrieved: {api_details.get('name')}")
                                print_info(f"  Base Path: {api_details.get('base_path')}")
                                print_info(f"  Health Score: {api_details.get('health_score')}")
                                self.results["discovery"]["passed"] += 1
                    
                    # Call filter_shadow_apis
                    print_info("\nTest 4: Calling filter_shadow_apis tool...")
                    result = await session.call_tool("filter_shadow_apis", arguments={})
                    if result.content and len(result.content) > 0:
                        shadow_apis = json.loads(result.content[0].text)
                        print_success(f"Found {len(shadow_apis)} shadow APIs")
                        self.results["discovery"]["passed"] += 1
            
        except Exception as e:
            print_error(f"Discovery test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results["discovery"]["failed"] += 1
    
    async def test_metrics_server(self):
        """Test Metrics MCP Server"""
        print_section("Testing: Metrics MCP Server (Port 8002)")
        
        try:
            async with streamable_http_client(self.metrics_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize
                    print_info("Initializing MCP session...")
                    await session.initialize()
                    print_success("Session initialized")
                    self.results["metrics"]["passed"] += 1
                    
                    # List tools
                    print_info("\nTest 1: Listing available tools...")
                    tools_response = await session.list_tools()
                    tools = tools_response.tools
                    print_success(f"Found {len(tools)} tools")
                    for tool in tools:
                        print_info(f"  - {tool.name}")
                    self.results["metrics"]["passed"] += 1
                    
                    # Get an API ID from backend
                    async with httpx.AsyncClient() as http_client:
                        response = await http_client.get(f"{self.backend_url}/api/v1/apis")
                        apis = response.json()
                    
                    if apis:
                        api_id = apis[0]["id"]
                        
                        # Call get_api_metrics
                        print_info(f"\nTest 2: Calling get_api_metrics for {api_id}...")
                        result = await session.call_tool("get_api_metrics", arguments={
                            "api_id": api_id,
                            "hours": 24
                        })
                        if result.content and len(result.content) > 0:
                            metrics = json.loads(result.content[0].text)
                            print_success(f"Retrieved {len(metrics.get('time_series', []))} data points")
                            if metrics.get("summary"):
                                summary = metrics["summary"]
                                print_info(f"  Avg Response Time: {summary.get('avg_response_time', 'N/A')}ms")
                            self.results["metrics"]["passed"] += 1
                        
                        # Call get_api_health
                        print_info(f"\nTest 3: Calling get_api_health for {api_id}...")
                        result = await session.call_tool("get_api_health", arguments={"api_id": api_id})
                        if result.content and len(result.content) > 0:
                            health = json.loads(result.content[0].text)
                            print_success(f"Health Score: {health.get('health_score', 'N/A')}")
                            print_info(f"  Status: {health.get('status', 'N/A')}")
                            self.results["metrics"]["passed"] += 1
            
        except Exception as e:
            print_error(f"Metrics test failed: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results["metrics"]["failed"] += 1
    
    async def test_optimization_server(self):
        """Test Optimization MCP Server"""
        print_section("Testing: Optimization MCP Server (Port 8004)")
        
        try:
            async with streamable_http_client(self.optimization_url) as (read, write, _):
                async with ClientSession(read, write) as session:
                    # Initialize
                    print_info("Initializing MCP session...")
                    await session.initialize()
                    print_success("Session initialized")
                    self.results["optimization"]["passed"] += 1
                    
                    # List tools
                    print_info("\nTest 1: Listing available tools...")
                    tools_response = await session.list_tools()
                    tools = tools_response.tools
                    print_success(f"Found {len(tools)} tools")
                    for tool in tools:
                        print_info(f"  - {tool.name}")
                    self.results["optimization"]["passed"] += 1
                    
                    # Get an API ID from backend
                    async with httpx.AsyncClient() as http_client:
                        response = await http_client.get(f"{self.backend_url}/api/v1/apis")
                        apis = response.json()
                    
                    if apis:
                        api_id = apis[0]["id"]
                        
                        # Call list_predictions
                        print_info("\nTest 2: Calling list_predictions...")
                        result = await session.call_tool("list_predictions", arguments={})
                        if result.content and len(result.content) > 0:
                            predictions = json.loads(result.content[0].text)
                            print_success(f"Found {len(predictions)} predictions")
                            if predictions:
                                sample = predictions[0]
                                print_info(f"  Sample: {sample.get('prediction_type')} - Confidence: {sample.get('confidence')}")
                            self.results["optimization"]["passed"] += 1
                        
                        # Call list_recommendations
                        print_info("\nTest 3: Calling list_recommendations...")
                        result = await session.call_tool("list_recommendations", arguments={})
                        if result.content and len(result.content) > 0:
                            recommendations = json.loads(result.content[0].text)
                            print_success(f"Found {len(recommendations)} recommendations")
                            if recommendations:
                                sample = recommendations[0]
                                print_info(f"  Sample: {sample.get('title')}")
                            self.results["optimization"]["passed"] += 1
                        
                        # Call list_rate_limit_policies
                        print_info("\nTest 4: Calling list_rate_limit_policies...")
                        result = await session.call_tool("list_rate_limit_policies", arguments={})
                        if result.content and len(result.content) > 0:
                            policies = json.loads(result.content[0].text)
                            print_success(f"Found {len(policies)} rate limit policies")
                            if policies:
                                sample = policies[0]
                                print_info(f"  Sample: {sample.get('policy_name')}")
                            self.results["optimization"]["passed"] += 1
                        
                        # Call create_rate_limit_policy
                        print_info(f"\nTest 5: Calling create_rate_limit_policy for {api_id}...")
                        policy_name = f"FastMCP Test {datetime.utcnow().timestamp()}"
                        result = await session.call_tool("create_rate_limit_policy", arguments={
                            "api_id": api_id,
                            "policy_name": policy_name,
                            "policy_type": "fixed",
                            "max_requests": 100,
                            "window_seconds": 60
                        })
                        if result.content and len(result.content) > 0:
                            policy = json.loads(result.content[0].text)
                            print_success(f"Created policy: {policy.get('id')}")
                            print_info(f"  Name: {policy.get('policy_name')}")
                            self.results["optimization"]["passed"] += 1
            
        except Exception as e:
            print_error(f"Optimization test failed: {str(e)}")
            import traceback
            traceback.print_exc()
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
            print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 All MCP FastMCP client tests passed!{Colors.END}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ Some tests failed. Check output above.{Colors.END}")


async def main():
    """Run all tests"""
    print_header("MCP FastMCP Client Integration Tests\nTesting Running MCP Servers via FastMCP Streamable HTTP Client")
    
    print_info(f"Test Time: {datetime.utcnow().isoformat()}Z")
    
    tester = MCPServerTester()
    
    # Test health first
    if not await tester.test_server_health():
        print_error("\nSome servers are not healthy. Aborting tests.")
        return
    
    # Run all tests
    await tester.test_discovery_server()
    await tester.test_metrics_server()
    await tester.test_optimization_server()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
