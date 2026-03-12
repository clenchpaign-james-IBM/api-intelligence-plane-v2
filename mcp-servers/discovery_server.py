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
                # Test backend connectivity by making a simple request
                await self.backend_client.list_apis(page=1, page_size=1)
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
            gateway_id: Optional[str] = None,
            status: Optional[str] = None,
            is_shadow: Optional[bool] = None,
            health_score_min: Optional[float] = None,
            limit: int = 100
        ) -> dict[str, Any]:
            """Get API inventory with optional filters.
            
            Args:
                gateway_id: Filter by gateway UUID
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
        async def search_apis(query: str, filters: Optional[dict] = None) -> dict[str, Any]:
            """Search APIs by name, path, or tags.
            
            Note: This is a simplified search that uses the backend's list API.
            For more advanced search, the backend would need a dedicated search endpoint.
            
            Args:
                query: Search query (name, path, tags)
                filters: Additional filters to apply
                
            Returns:
                dict: Search results with relevance scores
            """
            return await self._search_apis_impl(query, filters)

    async def initialize(self) -> None:
        """Initialize server resources."""
        await super().initialize()
        logger.info("Discovery server initialized and ready")
    
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
            except ValueError:
                return {
                    "discovered_count": 0,
                    "shadow_apis_count": 0,
                    "apis": [],
                    "discovery_time_ms": 0,
                    "error": f"Invalid gateway_id format: {gateway_id}"
                }
            
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
            return {
                "discovered_count": 0,
                "shadow_apis_count": 0,
                "apis": [],
                "discovery_time_ms": 0,
                "error": str(e)
            }
    
    async def _get_api_inventory_impl(
        self,
        gateway_id: Optional[str] = None,
        status: Optional[str] = None,
        is_shadow: Optional[bool] = None,
        health_score_min: Optional[float] = None,
        limit: int = 100
    ) -> dict[str, Any]:
        """Implementation of get_api_inventory tool.
        
        Args:
            gateway_id: Filter by gateway UUID
            status: Filter by status (active, inactive, deprecated, failed)
            is_shadow: Filter shadow APIs
            health_score_min: Minimum health score filter
            limit: Maximum number of results
            
        Returns:
            dict: API inventory with filtering applied
        """
        try:
            # Get APIs from backend with filters
            response = await self.backend_client.list_apis(
                gateway_id=gateway_id,
                status=status,
                is_shadow=is_shadow,
                page_size=min(limit, 1000)
            )
            
            apis = response.get("items", [])
            
            # Apply health score filter if specified (client-side filtering)
            if health_score_min is not None:
                apis = [
                    api for api in apis
                    if api.get("health_score", 0) >= health_score_min
                ]
            
            return {
                "total_count": response.get("total", 0),
                "filtered_count": len(apis),
                "apis": apis
            }
            
        except Exception as e:
            logger.error(f"Error getting API inventory: {e}")
            return {
                "total_count": 0,
                "filtered_count": 0,
                "apis": [],
                "error": str(e)
            }
    
    async def _search_apis_impl(self, query: str, filters: Optional[dict] = None) -> dict[str, Any]:
        """Implementation of search_apis tool.
        
        Note: This is a simplified implementation that filters results client-side.
        For production, the backend should provide a dedicated search endpoint.
        
        Args:
            query: Search query (name, path, tags)
            filters: Additional filters to apply
            
        Returns:
            dict: Search results with relevance scores
        """
        try:
            # Get all APIs (or filtered by gateway if specified)
            gateway_id = filters.get("gateway_id") if filters else None
            status = filters.get("status") if filters else None
            is_shadow = filters.get("is_shadow") if filters else None
            
            response = await self.backend_client.list_apis(
                gateway_id=gateway_id,
                status=status,
                is_shadow=is_shadow,
                page_size=1000
            )
            
            apis = response.get("items", [])
            
            # Simple client-side search (case-insensitive substring match)
            query_lower = query.lower()
            results = []
            
            for api in apis:
                score = 0.0
                
                # Check name match (highest weight)
                if query_lower in api.get("name", "").lower():
                    score += 3.0
                
                # Check base_path match (medium weight)
                if query_lower in api.get("base_path", "").lower():
                    score += 2.0
                
                # Check description match (low weight)
                if query_lower in api.get("description", "").lower():
                    score += 1.0
                
                # Check tags match (medium weight)
                tags = api.get("tags", [])
                if any(query_lower in tag.lower() for tag in tags):
                    score += 2.0
                
                if score > 0:
                    results.append({
                        "api": api,
                        "relevance_score": score
                    })
            
            # Sort by relevance score (descending)
            results.sort(key=lambda x: x["relevance_score"], reverse=True)
            
            # Limit to top 100 results
            results = results[:100]
            
            return {
                "results": results,
                "total_results": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error searching APIs: {e}")
            return {
                "results": [],
                "total_results": 0,
                "error": str(e)
            }

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