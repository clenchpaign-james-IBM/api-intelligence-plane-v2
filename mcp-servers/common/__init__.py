"""Common utilities for MCP servers.

This package provides shared functionality for all MCP servers including:
- Base MCP server class using FastMCP
- Shared OpenSearch client
- Health check utilities
"""

from common.health import HealthChecker, create_health_tool, create_info_tool
from common.mcp_base import BaseMCPServer
from common.opensearch import MCPOpenSearchClient

__all__ = [
    "BaseMCPServer",
    "MCPOpenSearchClient",
    "HealthChecker",
    "create_health_tool",
    "create_info_tool",
]

# Made with Bob
