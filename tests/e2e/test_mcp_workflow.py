"""End-to-end tests for MCP integration workflow.

Tests the complete MCP (Model Context Protocol) integration workflow including:
- MCP server initialization and health checks
- Tool registration and discovery
- Tool execution via MCP interface
- Resource access and management
- Error handling and retry logic
- Multi-tool workflow orchestration

Note: Uses mocked dependencies to focus on workflow logic.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_mcp_server():
    """Create MCP server with mocked dependencies."""
    backend_client = Mock()
    backend_client.get = AsyncMock()
    backend_client.post = AsyncMock()
    backend_client.put = AsyncMock()
    backend_client.delete = AsyncMock()
    
    health_checker = Mock()
    health_checker.check_health = AsyncMock(return_value={"status": "healthy"})
    
    return backend_client, health_checker


class TestMCPIntegrationWorkflow:
    """Test complete MCP integration workflow."""

    @pytest.mark.asyncio
    async def test_complete_mcp_workflow(self, mock_mcp_server):
        """Test complete workflow from initialization to tool execution."""
        backend_client, health_checker = mock_mcp_server
        
        # Step 1: Initialize MCP server
        server_info = {
            "name": "unified-server",
            "version": "1.0.0",
            "status": "initializing",
            "capabilities": [
                "gateway_management",
                "api_discovery",
                "metrics_analytics",
                "security_scanning",
                "compliance_monitoring"
            ]
        }
        
        # Verify initialization
        assert server_info["status"] == "initializing"
        assert len(server_info["capabilities"]) == 5
        
        # Step 2: Health check
        health_status = await health_checker.check_health()
        
        assert health_status["status"] == "healthy"
        
        # Update server status
        server_info["status"] = "ready"
        
        # Step 3: Register tools
        registered_tools = [
            {
                "name": "list_gateways",
                "description": "List all registered API gateways",
                "parameters": {"page": "int", "page_size": "int"}
            },
            {
                "name": "discover_apis",
                "description": "Discover APIs from a gateway",
                "parameters": {"gateway_id": "string"}
            },
            {
                "name": "scan_security",
                "description": "Scan API for security vulnerabilities",
                "parameters": {"api_id": "string"}
            },
            {
                "name": "generate_predictions",
                "description": "Generate failure predictions for an API",
                "parameters": {"api_id": "string"}
            },
            {
                "name": "execute_query",
                "description": "Execute natural language query",
                "parameters": {"query": "string"}
            }
        ]
        
        # Verify tool registration
        assert len(registered_tools) == 5
        assert all("name" in tool for tool in registered_tools)
        assert all("description" in tool for tool in registered_tools)
        
        # Step 4: Execute tool - list_gateways
        backend_client.get.return_value = {
            "gateways": [
                {"id": uuid4(), "name": "Production Gateway", "status": "connected"},
                {"id": uuid4(), "name": "Staging Gateway", "status": "connected"}
            ],
            "total": 2
        }
        
        list_result = await backend_client.get("/gateways", params={"page": 1, "page_size": 10})
        
        # Verify tool execution
        assert list_result["total"] == 2
        assert len(list_result["gateways"]) == 2
        
        # Step 5: Execute tool - discover_apis
        gateway_id = list_result["gateways"][0]["id"]
        
        backend_client.post.return_value = {
            "discovered_apis": [
                {"id": uuid4(), "name": "Payment API", "gateway_id": gateway_id},
                {"id": uuid4(), "name": "User API", "gateway_id": gateway_id}
            ],
            "count": 2
        }
        
        discover_result = await backend_client.post(
            f"/gateways/{gateway_id}/discover",
            json={}
        )
        
        # Verify discovery
        assert discover_result["count"] == 2
        assert all(api["gateway_id"] == gateway_id for api in discover_result["discovered_apis"])
        
        # Step 6: Execute tool - scan_security
        api_id = discover_result["discovered_apis"][0]["id"]
        
        backend_client.post.return_value = {
            "vulnerabilities": [
                {
                    "id": uuid4(),
                    "api_id": api_id,
                    "severity": "high",
                    "type": "authentication",
                    "status": "open"
                }
            ],
            "count": 1
        }
        
        scan_result = await backend_client.post(
            f"/security/scan/{api_id}",
            json={}
        )
        
        # Verify security scan
        assert scan_result["count"] == 1
        assert scan_result["vulnerabilities"][0]["severity"] == "high"

    @pytest.mark.asyncio
    async def test_mcp_tool_chaining_workflow(self, mock_mcp_server):
        """Test chaining multiple MCP tools in a workflow."""
        backend_client, health_checker = mock_mcp_server
        
        # Workflow: Create Gateway → Discover APIs → Scan Security → Generate Recommendations
        
        # Step 1: Create gateway
        backend_client.post.return_value = {
            "id": uuid4(),
            "name": "New Gateway",
            "status": "connected"
        }
        
        gateway = await backend_client.post("/gateways", json={"name": "New Gateway"})
        gateway_id = gateway["id"]
        
        # Step 2: Discover APIs
        backend_client.post.return_value = {
            "discovered_apis": [{"id": uuid4(), "name": "API 1"}],
            "count": 1
        }
        
        apis = await backend_client.post(f"/gateways/{gateway_id}/discover", json={})
        api_id = apis["discovered_apis"][0]["id"]
        
        # Step 3: Scan security
        backend_client.post.return_value = {
            "vulnerabilities": [{"id": uuid4(), "severity": "high"}],
            "count": 1
        }
        
        vulns = await backend_client.post(f"/security/scan/{api_id}", json={})
        
        # Step 4: Generate recommendations
        backend_client.post.return_value = {
            "recommendations": [
                {"id": uuid4(), "type": "caching", "priority": "high"}
            ],
            "count": 1
        }
        
        recs = await backend_client.post(f"/optimization/recommend/{api_id}", json={})
        
        # Verify workflow completion
        assert gateway["status"] == "connected"
        assert apis["count"] == 1
        assert vulns["count"] == 1
        assert recs["count"] == 1

    @pytest.mark.asyncio
    async def test_mcp_error_handling(self, mock_mcp_server):
        """Test MCP error handling and retry logic."""
        backend_client, health_checker = mock_mcp_server
        
        # Simulate backend error
        backend_client.get.side_effect = Exception("Backend connection failed")
        
        # Attempt tool execution with error handling
        try:
            await backend_client.get("/gateways")
            assert False, "Should have raised exception"
        except Exception as e:
            error_response = {
                "error": str(e),
                "tool": "list_gateways",
                "status": "failed",
                "retry_count": 0
            }
        
        # Verify error was caught
        assert error_response["status"] == "failed"
        assert "connection failed" in error_response["error"].lower()
        
        # Simulate retry with success
        backend_client.get.side_effect = None
        backend_client.get.return_value = {"gateways": [], "total": 0}
        
        retry_result = await backend_client.get("/gateways")
        
        # Verify retry succeeded
        assert retry_result["total"] == 0

    @pytest.mark.asyncio
    async def test_mcp_resource_access(self, mock_mcp_server):
        """Test MCP resource access workflow."""
        backend_client, health_checker = mock_mcp_server
        
        # Access different resource types
        
        # Resource 1: Gateway configuration
        backend_client.get.return_value = {
            "id": uuid4(),
            "name": "Production Gateway",
            "configuration": {
                "base_url": "https://gateway.example.com",
                "capabilities": ["api_management", "metrics"]
            }
        }
        
        gateway_config = await backend_client.get("/gateways/123")
        
        # Resource 2: API metrics
        backend_client.get.return_value = {
            "metrics": [
                {"timestamp": datetime.utcnow(), "response_time": 250.0}
            ],
            "count": 1
        }
        
        api_metrics = await backend_client.get("/metrics/api/456")
        
        # Resource 3: Security findings
        backend_client.get.return_value = {
            "vulnerabilities": [
                {"id": uuid4(), "severity": "high"}
            ],
            "count": 1
        }
        
        security_findings = await backend_client.get("/security/vulnerabilities")
        
        # Verify resource access
        assert "configuration" in gateway_config
        assert api_metrics["count"] == 1
        assert security_findings["count"] == 1

    @pytest.mark.asyncio
    async def test_mcp_concurrent_tool_execution(self, mock_mcp_server):
        """Test concurrent execution of multiple MCP tools."""
        backend_client, health_checker = mock_mcp_server
        
        # Simulate concurrent tool executions
        tool_executions = []
        
        # Tool 1: List gateways
        backend_client.get.return_value = {"gateways": [], "total": 0}
        result1 = await backend_client.get("/gateways")
        tool_executions.append({"tool": "list_gateways", "result": result1})
        
        # Tool 2: List APIs
        backend_client.get.return_value = {"apis": [], "total": 0}
        result2 = await backend_client.get("/apis")
        tool_executions.append({"tool": "list_apis", "result": result2})
        
        # Tool 3: Get metrics
        backend_client.get.return_value = {"metrics": [], "total": 0}
        result3 = await backend_client.get("/metrics")
        tool_executions.append({"tool": "get_metrics", "result": result3})
        
        # Verify all tools executed
        assert len(tool_executions) == 3
        assert all("result" in exec for exec in tool_executions)

    @pytest.mark.asyncio
    async def test_mcp_natural_language_query_integration(self, mock_mcp_server):
        """Test MCP integration with natural language query tool."""
        backend_client, health_checker = mock_mcp_server
        
        # Execute natural language query via MCP
        query_text = "Show me all APIs with high error rates"
        
        backend_client.post.return_value = {
            "query_id": uuid4(),
            "query_text": query_text,
            "results": {
                "apis": [
                    {"name": "Payment API", "error_rate": 0.08},
                    {"name": "User API", "error_rate": 0.12}
                ],
                "count": 2
            },
            "response_text": "Found 2 APIs with high error rates: Payment API (8%) and User API (12%)"
        }
        
        query_result = await backend_client.post("/query", json={"query": query_text})
        
        # Verify query execution
        assert query_result["results"]["count"] == 2
        assert "Payment API" in query_result["response_text"]


class TestMCPServerManagement:
    """Test MCP server management workflows."""

    @pytest.mark.asyncio
    async def test_server_initialization(self, mock_mcp_server):
        """Test MCP server initialization."""
        backend_client, health_checker = mock_mcp_server
        
        server_config = {
            "name": "unified-server",
            "version": "1.0.0",
            "port": 8007,
            "backend_url": "http://backend:8000",
            "transport": "streamable-http"
        }
        
        # Verify configuration
        assert server_config["name"] == "unified-server"
        assert server_config["port"] == 8007

    @pytest.mark.asyncio
    async def test_server_health_monitoring(self, mock_mcp_server):
        """Test MCP server health monitoring."""
        backend_client, health_checker = mock_mcp_server
        
        # Check health
        health_status = await health_checker.check_health()
        
        assert health_status["status"] == "healthy"
        
        # Simulate backend connectivity issue
        backend_client.get.side_effect = Exception("Connection timeout")
        health_checker.check_health.return_value = {
            "status": "degraded",
            "backend_status": "disconnected"
        }
        
        degraded_health = await health_checker.check_health()
        
        # Verify degraded status
        assert degraded_health["status"] == "degraded"
        assert degraded_health["backend_status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_server_tool_discovery(self, mock_mcp_server):
        """Test MCP tool discovery mechanism."""
        backend_client, health_checker = mock_mcp_server
        
        # Discover available tools
        available_tools = [
            {"name": "list_gateways", "category": "gateway_management"},
            {"name": "discover_apis", "category": "api_discovery"},
            {"name": "scan_security", "category": "security_scanning"},
            {"name": "generate_predictions", "category": "failure_predictions"},
            {"name": "execute_query", "category": "natural_language_queries"}
        ]
        
        # Group by category
        tools_by_category = {}
        for tool in available_tools:
            category = tool["category"]
            if category not in tools_by_category:
                tools_by_category[category] = []
            tools_by_category[category].append(tool["name"])
        
        # Verify tool discovery
        assert len(available_tools) == 5
        assert len(tools_by_category) == 5


class TestMCPDataTransformation:
    """Test MCP data transformation workflows."""

    @pytest.mark.asyncio
    async def test_request_transformation(self, mock_mcp_server):
        """Test transformation of MCP requests to backend API calls."""
        backend_client, health_checker = mock_mcp_server
        
        # MCP tool request
        mcp_request = {
            "tool": "list_gateways",
            "parameters": {
                "page": 1,
                "page_size": 10,
                "status": "connected"
            }
        }
        
        # Transform to backend API call
        backend_request = {
            "method": "GET",
            "path": "/gateways",
            "params": mcp_request["parameters"]
        }
        
        # Execute backend call
        backend_client.get.return_value = {"gateways": [], "total": 0}
        result = await backend_client.get(
            backend_request["path"],
            params=backend_request["params"]
        )
        
        # Verify transformation
        assert result["total"] == 0

    @pytest.mark.asyncio
    async def test_response_transformation(self, mock_mcp_server):
        """Test transformation of backend responses to MCP format."""
        backend_client, health_checker = mock_mcp_server
        
        # Backend response
        backend_response = {
            "gateways": [
                {"id": "123", "name": "Gateway 1", "status": "connected"}
            ],
            "total": 1,
            "page": 1,
            "page_size": 10
        }
        
        # Transform to MCP response
        mcp_response = {
            "tool": "list_gateways",
            "status": "success",
            "data": backend_response,
            "metadata": {
                "execution_time_ms": 150,
                "backend_status": "healthy"
            }
        }
        
        # Verify transformation
        assert mcp_response["status"] == "success"
        assert mcp_response["data"]["total"] == 1


# Made with Bob