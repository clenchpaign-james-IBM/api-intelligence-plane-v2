"""Base MCP server class for API Intelligence Plane.

Provides a base class for MCP servers using FastMCP framework.
"""

import logging
from typing import Any, Callable, Optional

from fastmcp import FastMCP

logger = logging.getLogger(__name__)


class BaseMCPServer:
    """Base class for MCP servers in the API Intelligence Plane.

    This class provides common functionality for all MCP servers including:
    - Server initialization and lifecycle management
    - Tool registration using FastMCP decorators
    - Resource registration
    - Prompt registration
    - Error handling and logging
    """

    def __init__(self, name: str, version: str = "1.0.0"):
        """Initialize the MCP server using FastMCP.

        Args:
            name: Server name
            version: Server version
        """
        self.name = name
        self.version = version
        self.mcp = FastMCP(name)

        logger.info(f"Initializing FastMCP server: {name} v{version}")

    def tool(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a tool with the MCP server.

        Args:
            name: Tool name (defaults to function name)
            description: Tool description

        Returns:
            Decorator function

        Example:
            @server.tool(description="Search for APIs")
            async def search_apis(query: str) -> list[dict]:
                return await search(query)
        """
        return self.mcp.tool(name=name, description=description)

    def resource(self, uri: str, name: Optional[str] = None, description: Optional[str] = None, mime_type: str = "text/plain"):
        """Decorator to register a resource with the MCP server.

        Args:
            uri: Resource URI pattern
            name: Resource name
            description: Resource description
            mime_type: MIME type of resource content

        Returns:
            Decorator function

        Example:
            @server.resource("api://{api_id}")
            async def get_api(api_id: str) -> str:
                return await fetch_api(api_id)
        """
        return self.mcp.resource(uri=uri, name=name, description=description, mime_type=mime_type)

    def prompt(self, name: Optional[str] = None, description: Optional[str] = None):
        """Decorator to register a prompt with the MCP server.

        Args:
            name: Prompt name (defaults to function name)
            description: Prompt description

        Returns:
            Decorator function

        Example:
            @server.prompt(description="Generate API analysis prompt")
            async def analyze_api(api_id: str) -> list[dict]:
                return [{"role": "user", "content": f"Analyze API {api_id}"}]
        """
        return self.mcp.prompt(name=name, description=description)

    async def initialize(self) -> None:
        """Initialize server resources.

        Override this method to perform server-specific initialization
        such as database connections, cache setup, etc.
        """
        logger.info(f"Initializing {self.name} server resources")

    async def cleanup(self) -> None:
        """Cleanup server resources.

        Override this method to perform server-specific cleanup
        such as closing database connections, clearing caches, etc.
        """
        logger.info(f"Cleaning up {self.name} server resources")

    def run(self, transport: str = "stdio") -> None:
        """Run the MCP server.

        Args:
            transport: Transport type ("stdio" or "streamable-http")

        This starts the server with the specified transport.
        For stdio: Used for local MCP clients
        For streamable-http: Used for remote HTTP-based clients
        """
        try:
            logger.info(f"Starting {self.name} FastMCP server with {transport} transport")
            self.mcp.run(transport=transport)
        except Exception as e:
            logger.error(f"Server error: {e}", exc_info=True)
            raise

    def get_server_info(self) -> dict[str, Any]:
        """Get server information.

        Returns:
            dict: Server metadata including registered tools, resources, and prompts
        """
        return {
            "name": self.name,
            "version": self.version,
            "framework": "FastMCP",
            "tools": [tool.name for tool in self.mcp._tools.values()] if hasattr(self.mcp, '_tools') else [],
            "resources": [resource.uri for resource in self.mcp._resources.values()] if hasattr(self.mcp, '_resources') else [],
            "prompts": [prompt.name for prompt in self.mcp._prompts.values()] if hasattr(self.mcp, '_prompts') else [],
        }

    def __repr__(self) -> str:
        """String representation of the server.

        Returns:
            str: Server description
        """
        return f"BaseMCPServer(name={self.name}, version={self.version})"

# Made with Bob
