"""Discovery MCP Server for API Intelligence Plane.

This MCP server provides tools for discovering and managing APIs from connected
API Gateways. It exposes tools that AI agents can use to interact with the
discovery functionality.

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

from common.health import HealthChecker, create_health_tool
from common.http_health import HTTPHealthServer
from common.mcp_base import BaseMCPServer
from common.opensearch import MCPOpenSearchClient

logger = logging.getLogger(__name__)


class DiscoveryMCPServer(BaseMCPServer):
    """MCP Server for API Discovery operations.
    
    Provides tools for:
    - Discovering APIs from Gateways
    - Retrieving API inventory
    - Searching APIs
    """

    def __init__(self):
        """Initialize Discovery MCP server."""
        super().__init__(name="discovery-server", version="1.0.0")
        
        # Initialize OpenSearch client
        self.opensearch = MCPOpenSearchClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        self.health_checker.set_opensearch_client(self.opensearch)
        
        # Register tools
        self._register_tools()
        
        logger.info("Discovery MCP server initialized")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        health_tool = create_health_tool(self.health_checker)
        
        @self.tool(description="Check Discovery server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.
            
            Returns:
                dict: Health status including OpenSearch connectivity
            """
            return await health_tool()
        
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
        
        # Connect to OpenSearch
        await self.opensearch.connect()
        logger.info("Discovery server connected to OpenSearch")
    
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
            # Query OpenSearch for APIs from this gateway
            query = {
                "bool": {
                    "must": [
                        {"term": {"gateway_id": gateway_id}}
                    ]
                }
            }
            
            # If force_refresh, we would trigger discovery service
            # For now, we query existing data from OpenSearch
            result = await self.opensearch.search(
                index="api-inventory",
                query=query,
                size=1000
            )
            
            apis = []
            shadow_count = 0
            
            for hit in result.get("hits", {}).get("hits", []):
                source = hit["_source"]
                api_data = {
                    "id": source.get("id"),
                    "name": source.get("name"),
                    "base_path": source.get("base_path"),
                    "is_shadow": source.get("is_shadow", False)
                }
                apis.append(api_data)
                
                if api_data["is_shadow"]:
                    shadow_count += 1
            
            discovery_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "discovered_count": len(apis),
                "shadow_apis_count": shadow_count,
                "apis": apis,
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
            # Build query filters
            must_filters = []
            
            if gateway_id:
                must_filters.append({"term": {"gateway_id": gateway_id}})
            
            if status:
                must_filters.append({"term": {"status": status}})
            
            if is_shadow is not None:
                must_filters.append({"term": {"is_shadow": is_shadow}})
            
            if health_score_min is not None:
                must_filters.append({"range": {"health_score": {"gte": health_score_min}}})
            
            query = {
                "bool": {
                    "must": must_filters if must_filters else [{"match_all": {}}]
                }
            }
            
            # Get total count without filters
            total_count = await self.opensearch.count(index="api-inventory")
            
            # Get filtered results
            result = await self.opensearch.search(
                index="api-inventory",
                query=query,
                size=min(limit, 1000)
            )
            
            apis = []
            for hit in result.get("hits", {}).get("hits", []):
                apis.append(hit["_source"])
            
            return {
                "total_count": total_count,
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
        
        Args:
            query: Search query (name, path, tags)
            filters: Additional filters to apply
            
        Returns:
            dict: Search results with relevance scores
        """
        try:
            # Build search query using multi_match for fuzzy search
            search_query = {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["name^3", "base_path^2", "description", "tags"],
                                "type": "best_fields",
                                "fuzziness": "AUTO"
                            }
                        }
                    ]
                }
            }
            
            # Add additional filters if provided
            if filters:
                filter_clauses = []
                
                if "gateway_id" in filters:
                    filter_clauses.append({"term": {"gateway_id": filters["gateway_id"]}})
                
                if "status" in filters:
                    filter_clauses.append({"term": {"status": filters["status"]}})
                
                if "is_shadow" in filters:
                    filter_clauses.append({"term": {"is_shadow": filters["is_shadow"]}})
                
                if filter_clauses:
                    search_query["bool"]["filter"] = filter_clauses
            
            # Execute search
            result = await self.opensearch.search(
                index="api-inventory",
                query=search_query,
                size=100
            )
            
            results = []
            for hit in result.get("hits", {}).get("hits", []):
                results.append({
                    "api": hit["_source"],
                    "relevance_score": hit["_score"]
                })
            
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
        
        # Close OpenSearch connection
        await self.opensearch.close()
        logger.info("Discovery server disconnected from OpenSearch")


def main():
    """Main entry point for Discovery MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create server
    server = DiscoveryMCPServer()
    
    # Start HTTP health server in background thread on port 8000
    health_server = HTTPHealthServer(server.health_checker, port=8000)
    health_server.start()
    
    try:
        # Run MCP server on port 8001 (this will block)
        server.run(transport="streamable-http", port=8001)
    finally:
        # Cleanup
        health_server.stop()


if __name__ == "__main__":
    main()

# Made with Bob