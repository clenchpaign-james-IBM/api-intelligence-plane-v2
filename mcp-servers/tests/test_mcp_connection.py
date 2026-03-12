"""Test MCP server connectivity using the MCP SDK."""

import asyncio
import logging
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_discovery_server():
    """Test connection to Discovery MCP server."""
    logger.info("Testing Discovery MCP server connection...")
    
    try:
        # Connect using streamable HTTP transport
        async with streamable_http_client("http://localhost:8001/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                # List available tools
                tools_result = await session.list_tools()
                logger.info(f"✓ Connected to Discovery server")
                logger.info(f"  Available tools: {len(tools_result.tools)}")
                for tool in tools_result.tools:
                    logger.info(f"    - {tool.name}: {tool.description}")
                
                # Test calling a tool
                logger.info("\nTesting server_info tool...")
                result = await session.call_tool("server_info", {})
                logger.info(f"✓ server_info result: {result.content}")
                
                return True
                
    except Exception as e:
        logger.error(f"✗ Failed to connect to Discovery server: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_metrics_server():
    """Test connection to Metrics MCP server."""
    logger.info("\nTesting Metrics MCP server connection...")
    
    try:
        async with streamable_http_client("http://localhost:8002/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools_result = await session.list_tools()
                logger.info(f"✓ Connected to Metrics server")
                logger.info(f"  Available tools: {len(tools_result.tools)}")
                for tool in tools_result.tools:
                    logger.info(f"    - {tool.name}")
                
                return True
                
    except Exception as e:
        logger.error(f"✗ Failed to connect to Metrics server: {e}")
        return False


async def test_optimization_server():
    """Test connection to Optimization MCP server."""
    logger.info("\nTesting Optimization MCP server connection...")
    
    try:
        async with streamable_http_client("http://localhost:8004/mcp") as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                tools_result = await session.list_tools()
                logger.info(f"✓ Connected to Optimization server")
                logger.info(f"  Available tools: {len(tools_result.tools)}")
                for tool in tools_result.tools:
                    logger.info(f"    - {tool.name}")
                
                return True
                
    except Exception as e:
        logger.error(f"✗ Failed to connect to Optimization server: {e}")
        return False


async def main():
    """Run all connection tests."""
    logger.info("=" * 60)
    logger.info("MCP Server Connection Tests")
    logger.info("=" * 60)
    
    results = []
    
    # Test each server
    results.append(("Discovery", await test_discovery_server()))
    results.append(("Metrics", await test_metrics_server()))
    results.append(("Optimization", await test_optimization_server()))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("Test Summary")
    logger.info("=" * 60)
    
    for name, success in results:
        status = "✓ PASS" if success else "✗ FAIL"
        logger.info(f"{name:20s}: {status}")
    
    all_passed = all(success for _, success in results)
    logger.info("=" * 60)
    
    if all_passed:
        logger.info("✓ All MCP servers are accessible and working!")
        return 0
    else:
        logger.error("✗ Some MCP servers failed connectivity tests")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)

# Made with Bob
