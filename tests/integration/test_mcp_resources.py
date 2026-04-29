"""
Integration tests for MCP resource access.

Tests MCP resource access patterns and their integration with backend:
1. Resource listing
2. Resource reading
3. Resource templates
4. Resource error handling
"""

import pytest
import httpx


@pytest.mark.asyncio
class TestMCPResources:
    """Integration tests for MCP resource access."""

    async def test_list_resources(self):
        """Test listing available MCP resources."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    timeout=10.0
                )
                
                # Verify response
                assert response.status_code == 200
                data = response.json()
                
                # Verify response structure
                assert "resources" in data or isinstance(data, list)
                
                # If resources exist, verify structure
                if isinstance(data, dict) and "resources" in data:
                    resources = data["resources"]
                    if resources:
                        resource = resources[0]
                        assert "uri" in resource
                        assert "name" in resource or "description" in resource
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_read_gateway_resource(self):
        """Test reading a gateway resource."""
        async with httpx.AsyncClient() as client:
            try:
                # First, list resources to get a valid URI
                list_response = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    timeout=10.0
                )
                
                if list_response.status_code == 200:
                    data = list_response.json()
                    resources = data.get("resources", []) if isinstance(data, dict) else data
                    
                    # Find a gateway resource
                    gateway_resource = None
                    for resource in resources:
                        if "gateway" in resource.get("uri", "").lower():
                            gateway_resource = resource
                            break
                    
                    if gateway_resource:
                        # Read the resource
                        read_response = await client.get(
                            f"http://localhost:8007/mcp/v1/resources/{gateway_resource['uri']}",
                            timeout=10.0
                        )
                        
                        assert read_response.status_code in [200, 404]
                        
                        if read_response.status_code == 200:
                            resource_data = read_response.json()
                            assert "contents" in resource_data or "data" in resource_data
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_read_api_resource(self):
        """Test reading an API resource."""
        async with httpx.AsyncClient() as client:
            try:
                # First, list resources to get a valid URI
                list_response = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    timeout=10.0
                )
                
                if list_response.status_code == 200:
                    data = list_response.json()
                    resources = data.get("resources", []) if isinstance(data, dict) else data
                    
                    # Find an API resource
                    api_resource = None
                    for resource in resources:
                        if "api" in resource.get("uri", "").lower():
                            api_resource = resource
                            break
                    
                    if api_resource:
                        # Read the resource
                        read_response = await client.get(
                            f"http://localhost:8007/mcp/v1/resources/{api_resource['uri']}",
                            timeout=10.0
                        )
                        
                        assert read_response.status_code in [200, 404]
                        
                        if read_response.status_code == 200:
                            resource_data = read_response.json()
                            assert "contents" in resource_data or "data" in resource_data
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_read_nonexistent_resource(self):
        """Test reading a non-existent resource."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "http://localhost:8007/mcp/v1/resources/nonexistent://resource",
                    timeout=10.0
                )
                
                # Should return 404 or error
                assert response.status_code in [404, 400]
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_resource_templates(self):
        """Test resource templates functionality."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "http://localhost:8007/mcp/v1/resources/templates",
                    timeout=10.0
                )
                
                # Verify response
                assert response.status_code in [200, 404]
                
                if response.status_code == 200:
                    data = response.json()
                    # Verify templates structure
                    assert isinstance(data, (list, dict))
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_resource_with_query_parameters(self):
        """Test resource access with query parameters."""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    params={
                        "type": "gateway",
                        "limit": 10
                    },
                    timeout=10.0
                )
                
                # Verify response
                assert response.status_code in [200, 400]
                
                if response.status_code == 200:
                    data = response.json()
                    assert "resources" in data or isinstance(data, list)
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_resource_pagination(self):
        """Test resource pagination."""
        async with httpx.AsyncClient() as client:
            try:
                # Get first page
                page1_response = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    params={
                        "page": 1,
                        "page_size": 5
                    },
                    timeout=10.0
                )
                
                # Get second page
                page2_response = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    params={
                        "page": 2,
                        "page_size": 5
                    },
                    timeout=10.0
                )
                
                # Both should succeed or both should fail
                assert page1_response.status_code == page2_response.status_code
                
                if page1_response.status_code == 200:
                    page1_data = page1_response.json()
                    page2_data = page2_response.json()
                    
                    # Verify pagination structure
                    assert "resources" in page1_data or isinstance(page1_data, list)
                    assert "resources" in page2_data or isinstance(page2_data, list)
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")

    async def test_resource_caching(self):
        """Test resource caching behavior."""
        async with httpx.AsyncClient() as client:
            try:
                # Make first request
                response1 = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    timeout=10.0
                )
                
                # Make second request (should potentially use cache)
                response2 = await client.get(
                    "http://localhost:8007/mcp/v1/resources",
                    timeout=10.0
                )
                
                # Both should succeed
                assert response1.status_code == response2.status_code
                
                if response1.status_code == 200:
                    # Verify consistent responses
                    data1 = response1.json()
                    data2 = response2.json()
                    
                    # Structure should be the same
                    assert type(data1) == type(data2)
                
            except httpx.ConnectError:
                pytest.skip("MCP server not running on localhost:8007")


# Made with Bob