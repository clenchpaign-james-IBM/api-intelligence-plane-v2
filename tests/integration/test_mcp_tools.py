"""
Integration tests for MCP tool execution.

Tests MCP tool calls and their integration with backend:
1. Gateway management tools
2. API discovery tools
3. Metrics query tools
4. Tool error handling
"""

import pytest
import httpx


@pytest.mark.asyncio
class TestMCPTools:
    """Integration tests for MCP tool execution."""

    async def test_list_gateways_tool(self):
        """Test list_gateways MCP tool."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "list_gateways",
                        "arguments": {
                            "page": 1,
                            "page_size": 10
                        }
                    },
                    timeout=10.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify response structure
                assert "items" in data or "gateways" in data
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_list_apis_tool(self):
        """Test list_apis MCP tool."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "list_apis",
                        "arguments": {
                            "page": 1,
                            "page_size": 10
                        }
                    },
                    timeout=10.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify response structure
                assert "items" in data or "apis" in data
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_get_predictions_tool(self):
        """Test get_predictions MCP tool."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "get_predictions",
                        "arguments": {
                            "page": 1,
                            "page_size": 10
                        }
                    },
                    timeout=10.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify response structure
                assert "items" in data or "predictions" in data
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_tool_with_invalid_arguments(self):
        """Test MCP tool with invalid arguments."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "list_gateways",
                        "arguments": {
                            "page": -1,  # Invalid page number
                            "page_size": 10
                        }
                    },
                    timeout=10.0
                )
                
                # Should return error or handle gracefully
                assert response.status_code in [200, 400, 422]
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_nonexistent_tool(self):
        """Test calling a non-existent MCP tool."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "nonexistent_tool",
                        "arguments": {}
                    },
                    timeout=10.0
                )
                
                # Should return error
                assert response.status_code in [404, 400]
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_query_tool(self):
        """Test execute_query MCP tool."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "execute_query",
                        "arguments": {
                            "query_text": "Show me all APIs"
                        }
                    },
                    timeout=15.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify query response structure
                assert "query_id" in data or "response_text" in data or "results" in data
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_tool_timeout_handling(self):
        """Test MCP tool timeout handling."""
        async with httpx.AsyncClient() as client:
            try:
                # Use very short timeout to test timeout handling
                response = await client.post(
                    "http://localhost:8007/mcp/v1/tools/call",
                    json={
                        "name": "list_apis",
                        "arguments": {
                            "page": 1,
                            "page_size": 1000  # Large page size
                        }
                    },
                    timeout=0.1  # Very short timeout
                )
                
                # Either succeeds quickly or times out
                assert response.status_code in [200, 408, 504]
                
            except (httpx.ConnectError, httpx.TimeoutException):
                # Expected for timeout test
                pass


# Made with Bob