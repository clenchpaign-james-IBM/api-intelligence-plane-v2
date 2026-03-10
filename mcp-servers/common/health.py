"""Health check utilities for MCP servers.

Provides health check functionality for MCP servers to report their status.
"""

import logging
from datetime import datetime
from typing import Any, Optional

from common.opensearch import MCPOpenSearchClient

logger = logging.getLogger(__name__)


class HealthChecker:
    """Health checker for MCP servers.

    Provides health check functionality including:
    - Server status
    - OpenSearch connectivity
    - Resource availability
    - Performance metrics
    """

    def __init__(self, server_name: str, version: str):
        """Initialize health checker.

        Args:
            server_name: Name of the MCP server
            version: Server version
        """
        self.server_name = server_name
        self.version = version
        self.start_time = datetime.utcnow()
        self.opensearch_client: Optional[MCPOpenSearchClient] = None

    def set_opensearch_client(self, client: MCPOpenSearchClient) -> None:
        """Set OpenSearch client for health checks.

        Args:
            client: OpenSearch client instance
        """
        self.opensearch_client = client

    async def check_health(self) -> dict[str, Any]:
        """Perform comprehensive health check.

        Returns:
            dict: Health check results with status and details
        """
        health_status = {
            "server": self.server_name,
            "version": self.version,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "checks": {},
        }

        # Check OpenSearch connectivity
        if self.opensearch_client:
            opensearch_health = await self._check_opensearch()
            health_status["checks"]["opensearch"] = opensearch_health

            if opensearch_health["status"] != "healthy":
                health_status["status"] = "degraded"
        else:
            health_status["checks"]["opensearch"] = {
                "status": "not_configured",
                "message": "OpenSearch client not configured",
            }

        return health_status

    async def _check_opensearch(self) -> dict[str, Any]:
        """Check OpenSearch connectivity and health.

        Returns:
            dict: OpenSearch health status
        """
        try:
            cluster_health = await self.opensearch_client.health_check()

            if cluster_health.get("status") == "unavailable":
                return {
                    "status": "unhealthy",
                    "message": "OpenSearch cluster unavailable",
                    "error": cluster_health.get("error"),
                }

            # Map OpenSearch cluster status to health status
            cluster_status = cluster_health.get("status", "unknown")
            if cluster_status == "green":
                status = "healthy"
            elif cluster_status == "yellow":
                status = "degraded"
            else:
                status = "unhealthy"

            return {
                "status": status,
                "cluster_status": cluster_status,
                "cluster_name": cluster_health.get("cluster_name"),
                "nodes": cluster_health.get("number_of_nodes"),
                "active_shards": cluster_health.get("active_shards"),
            }

        except Exception as e:
            logger.error(f"OpenSearch health check failed: {e}")
            return {
                "status": "unhealthy",
                "message": "Failed to check OpenSearch health",
                "error": str(e),
            }

    def get_basic_info(self) -> dict[str, Any]:
        """Get basic server information.

        Returns:
            dict: Basic server info
        """
        return {
            "server": self.server_name,
            "version": self.version,
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds(),
            "start_time": self.start_time.isoformat(),
        }

    def is_healthy(self, health_status: dict[str, Any]) -> bool:
        """Check if server is healthy based on health status.

        Args:
            health_status: Health status dict from check_health()

        Returns:
            bool: True if healthy, False otherwise
        """
        return health_status.get("status") in ["healthy", "degraded"]


def create_health_tool(health_checker: HealthChecker):
    """Create a health check tool for MCP server.

    Args:
        health_checker: HealthChecker instance

    Returns:
        Async function that can be registered as an MCP tool

    Example:
        health_checker = HealthChecker("my-server", "1.0.0")
        health_tool = create_health_tool(health_checker)

        @server.tool(description="Check server health")
        async def health() -> dict:
            return await health_tool()
    """

    async def health_tool() -> dict[str, Any]:
        """Check MCP server health.

        Returns:
            dict: Health status
        """
        return await health_checker.check_health()

    return health_tool


def create_info_tool(health_checker: HealthChecker):
    """Create a server info tool for MCP server.

    Args:
        health_checker: HealthChecker instance

    Returns:
        Function that can be registered as an MCP tool

    Example:
        health_checker = HealthChecker("my-server", "1.0.0")
        info_tool = create_info_tool(health_checker)

        @server.tool(description="Get server info")
        def info() -> dict:
            return info_tool()
    """

    def info_tool() -> dict[str, Any]:
        """Get MCP server information.

        Returns:
            dict: Server info
        """
        return health_checker.get_basic_info()

    return info_tool

# Made with Bob
