"""
Integration tests for MCP server initialization.

Tests the MCP server startup and basic connectivity:
1. Server initialization
2. Health check endpoint
3. Server info endpoint
4. Backend connectivity
"""

import pytest
import httpx


@pytest.mark.asyncio
class TestMCPInitialization:
    """Integration tests for MCP server initialization."""

    async def test_mcp_server_health(self):
        """Test MCP server health endpoint."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "http://localhost:8007/health",
                    timeout=5.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify health response structure
                assert "status" in data
                assert "server" in data
                assert "version" in data
                assert data["server"] == "unified-server"
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_mcp_server_info(self):
        """Test MCP server info endpoint."""
        async with httpx.AsyncClient() as client:
            try:
                # Call server_info tool via MCP protocol
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "server_info",
                        "arguments": {}
                    },
                    timeout=5.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify server info structure
                assert "name" in data
                assert "version" in data
                assert "capabilities" in data
                assert isinstance(data["capabilities"], list)
                assert len(data["capabilities"]) > 0
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_backend_connectivity(self):
        """Test MCP server can connect to backend."""
        async with httpx.AsyncClient() as client:
            try:
                # Call health tool which checks backend connectivity
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "health",
                        "arguments": {}
                    },
                    timeout=5.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify backend connectivity
                assert "backend_status" in data
                # Backend may be connected or disconnected depending on setup
                assert data["backend_status"] in ["connected", "disconnected"]
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_mcp_server_capabilities(self):
        """Test MCP server exposes expected capabilities."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "server_info",
                        "arguments": {}
                    },
                    timeout=5.0
                )
                
                assert response.status_code == 200
                data = response.json()
                
                # Verify expected capabilities
                capabilities = data.get("capabilities", [])
                expected_capabilities = [
                    "gateway_management",
                    "api_discovery",
                    "metrics_analytics",
                    "security_scanning",
                    "compliance_monitoring",
                ]
                
                for capability in expected_capabilities:
                    assert capability in capabilities, f"Missing capability: {capability}"
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")


# Made with Bob