"""Discovery MCP Server for API Intelligence Plane.

This MCP server provides tools for discovering and managing APIs from connected
API Gateways. It acts as a thin wrapper around the backend REST API, exposing
tools that AI agents can use to interact with the discovery functionality.

Port: 8001
Transport: Streamable HTTP
"""

import asyncio
import logging
import os
import sys
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.backend_client import BackendClient
from common.health import HealthChecker, create_health_tool
from common.mcp_base import BaseMCPServer

logger = logging.getLogger(__name__)


class DiscoveryMCPServer(BaseMCPServer):
    """MCP Server for API Discovery operations.
    
    Provides tools for:
    - Discovering APIs from Gateways
    - Retrieving API inventory
    - Searching APIs
    
    This server acts as a thin wrapper around the backend REST API,
    delegating all business logic to the backend services.
    """

    def __init__(self):
        """Initialize Discovery MCP server."""
        super().__init__(name="discovery-server", version="1.0.0")
        
        # Initialize backend client instead of OpenSearch
        self.backend_client = BackendClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        
        # Register tools
        self._register_tools()
        
        logger.info("Discovery MCP server initialized (using backend API)")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        @self.tool(description="Check Discovery server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.
            
            Returns:
                dict: Health status including backend connectivity
            """
            try:
                # Test backend connectivity by making a simple request to gateways endpoint
                response = await self.backend_client.client.get("/gateways", params={"page": 1, "page_size": 1})
                response.raise_for_status()
                backend_status = "connected"
            except Exception as e:
                logger.error(f"Backend health check failed: {e}")
                backend_status = "disconnected"
            
            return {
                "status": "healthy" if backend_status == "connected" else "degraded",
                "server": self.name,
                "version": self.version,
                "backend_status": backend_status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Server info tool
        @self.tool(description="Get Discovery server information")
        def server_info() -> dict[str, Any]:
            """Get server information.
            
            Returns:
                dict: Server metadata and capabilities
            """
            info = self.get_server_info()
            info.update({
                "port": 8001,
                "transport": "streamable-http",
                "architecture": "thin_wrapper",
                "backend_url": self.backend_client.base_url,
                "capabilities": [
                    "api_discovery",
                    "inventory_management",
                    "api_search",
                    "shadow_api_detection"
                ]
            })
            return info
        
        # Discovery tools
        @self.tool(description="Discover APIs from a connected Gateway")
        async def discover_apis(gateway_id: str, force_refresh: bool = False) -> dict[str, Any]:
            """Discover APIs from a Gateway.
            
            This tool retrieves the current API inventory for a specific gateway
            from the backend. The backend handles the actual discovery process.
            
            Args:
                gateway_id: Gateway UUID to discover APIs from
                force_refresh: Force immediate discovery instead of using cache
                
            Returns:
                dict: Discovery results with API count and details
            """
            return await self._discover_apis_impl(gateway_id, force_refresh)
        
        @self.tool(description="Retrieve complete API inventory with filtering")
        async def get_api_inventory(
            gateway_id: str,
            status: Optional[str] = None,
            is_shadow: Optional[bool] = None,
            health_score_min: Optional[float] = None,
            limit: int = 100
        ) -> dict[str, Any]:
            """Get API inventory with optional filters for a specific gateway.
            
            Args:
                gateway_id: Gateway UUID (required)
                status: Filter by status (active, inactive, deprecated, failed)
                is_shadow: Filter shadow APIs
                health_score_min: Minimum health score filter
                limit: Maximum number of results
                
            Returns:
                dict: API inventory with filtering applied
            """
            return await self._get_api_inventory_impl(
                gateway_id, status, is_shadow, health_score_min, limit
            )
        
        @self.tool(description="Search APIs using natural language or structured queries")
        async def search_apis(gateway_id: str, query: str, filters: Optional[dict] = None) -> dict[str, Any]:
            """Search APIs by name, path, or tags within a specific gateway.
            
            Note: This is a simplified search that uses the backend's list API.
            For more advanced search, the backend would need a dedicated search endpoint.
            
            Args:
                gateway_id: Gateway UUID (required)
                query: Search query (name, path, tags)
                filters: Additional filters to apply
                
            Returns:
                dict: Search results with relevance scores
            """
            return await self._search_apis_impl(gateway_id, query, filters)

    async def initialize(self) -> None:
        """Initialize server resources."""
        await super().initialize()
        logger.info("Discovery server initialized and ready")
    
    def _create_error_response(
        self,
        error: Exception,
        error_code: str,
        default_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Create standardized error response.
        
        Args:
            error: The exception that occurred
            error_code: Error code for categorization
            default_data: Default data fields for this response type
            
        Returns:
            dict: Standardized error response
        """
        return {
            "success": False,
            "error": {
                "code": error_code,
                "message": str(error),
                "type": type(error).__name__
            },
            **default_data
        }
    
    async def _discover_apis_impl(self, gateway_id: str, force_refresh: bool = False) -> dict[str, Any]:
        """Implementation of discover_apis tool.
        
        Args:
            gateway_id: Gateway UUID to discover APIs from
            force_refresh: Force immediate discovery instead of using cache
            
        Returns:
            dict: Discovery results with API count and details
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate UUID format
            try:
                UUID(gateway_id)
            except ValueError as e:
                return self._create_error_response(
                    error=e,
                    error_code="INVALID_GATEWAY_ID",
                    default_data={
                        "discovered_count": 0,
                        "shadow_apis_count": 0,
                        "apis": [],
                        "discovery_time_ms": 0
                    }
                )
            
            # Get APIs from backend for this gateway
            response = await self.backend_client.list_apis(
                gateway_id=gateway_id,
                page_size=1000
            )
            
            apis = response.get("items", [])
            shadow_count = sum(1 for api in apis if api.get("is_shadow", False))
            
            # Format API data
            formatted_apis = [
                {
                    "id": api.get("id"),
                    "name": api.get("name"),
                    "base_path": api.get("base_path"),
                    "is_shadow": api.get("is_shadow", False)
                }
                for api in apis
            ]
            
            discovery_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "discovered_count": len(formatted_apis),
                "shadow_apis_count": shadow_count,
                "apis": formatted_apis,
                "discovery_time_ms": discovery_time_ms
            }
            
        except Exception as e:
            logger.error(f"Error discovering APIs: {e}")
            return self._create_error_response(
                error=e,
                error_code="DISCOVERY_FAILED",
                default_data={
                    "discovered_count": 0,
                    "shadow_apis_count": 0,
                    "apis": [],
                    "discovery_time_ms": 0
                }
            )
    
    async def _get_api_inventory_impl(
        self,
        gateway_id: str,
        status: Optional[str] = None,
        is_shadow: Optional[bool] = None,
        health_score_min: Optional[float] = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """Implementation of get_api_inventory tool.
        
        Args:
            gateway_id: Gateway UUID (required)
            status: Filter by status (active, inactive, deprecated, failed)
            is_shadow: Filter shadow APIs
            health_score_min: Minimum health score filter
            limit: Maximum number of results
            
        Returns:
            dict: API inventory with filtering applied
        """
        try:
            # Get APIs from backend with filters (including health_score_min)
            response = await self.backend_client.list_apis(
                gateway_id=gateway_id,
                status=status,
                is_shadow=is_shadow,
                health_score_min=health_score_min,  # Backend handles filtering
                page_size=min(limit, 1000)
            )
            
            apis = response.get("items", [])
            
            return {
                "total_count": response.get("total", 0),
                "filtered_count": len(apis),
                "apis": apis
            }
            
        except Exception as e:
            logger.error(f"Error getting API inventory: {e}")
            return self._create_error_response(
                error=e,
                error_code="INVENTORY_FETCH_FAILED",
                default_data={
                    "total_count": 0,
                    "filtered_count": 0,
                    "apis": []
                }
            )
    
    async def _search_apis_impl(self, gateway_id: str, query: str, filters: Optional[dict] = None) -> dict[str, Any]:
        """Implementation of search_apis tool.
        
        Uses backend's OpenSearch full-text search for efficient and scalable searching.
        
        Args:
            gateway_id: Gateway UUID (required)
            query: Search query (name, path, tags, description)
            filters: Additional filters to apply (status, is_shadow)
            
        Returns:
            dict: Search results with relevance scores from OpenSearch
        """
        try:
            # Extract filters
            status = filters.get("status") if filters else None
            is_shadow = filters.get("is_shadow") if filters else None
            limit = filters.get("limit", 100) if filters else 100
            
            # Use backend search endpoint
            response = await self.backend_client.search_apis(
                gateway_id=gateway_id,
                query=query,
                limit=limit,
                status=status,
                is_shadow=is_shadow
            )
            
            return {
                "results": response.get("results", []),
                "total_results": response.get("total", 0),
                "query": query
            }
            
        except Exception as e:
            logger.error(f"Error searching APIs: {e}")
            return self._create_error_response(
                error=e,
                error_code="SEARCH_FAILED",
                default_data={
                    "results": [],
                    "total_results": 0,
                    "query": query
                }
            )

    async def cleanup(self) -> None:
        """Cleanup server resources."""
        await super().cleanup()
        
        # Close backend client connection
        await self.backend_client.close()
        logger.info("Discovery server disconnected from backend")


def main():
    """Main entry point for Discovery MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create server
    server = DiscoveryMCPServer()
    
    # Run MCP server on port 8000 (matches Docker port mapping)
    # FastMCP's built-in server will handle both MCP and health endpoints
    server.run(transport="streamable-http", port=8000)


if __name__ == "__main__":
    main()

# Made with Bob