"""HTTP health endpoint wrapper for MCP servers.

Provides a simple HTTP server that exposes /health endpoint for Docker healthchecks
while the MCP server runs on the main transport.
"""

import asyncio
import logging
import threading
from typing import Optional

from aiohttp import web

from common.health import HealthChecker

logger = logging.getLogger(__name__)


class HTTPHealthServer:
    """HTTP server for health checks.
    
    Runs in a separate thread to provide /health endpoint for Docker healthchecks.
    """

    def __init__(self, health_checker: HealthChecker, port: int = 8000):
        """Initialize HTTP health server.
        
        Args:
            health_checker: HealthChecker instance
            port: Port to listen on
        """
        self.health_checker = health_checker
        self.port = port
        self.app = web.Application()
        self.runner: Optional[web.AppRunner] = None
        self.thread: Optional[threading.Thread] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._setup_routes()

    def _setup_routes(self) -> None:
        """Setup HTTP routes."""
        self.app.router.add_get('/health', self._health_handler)
        self.app.router.add_get('/healthz', self._health_handler)  # k8s style
        self.app.router.add_get('/ready', self._ready_handler)

    async def _health_handler(self, request: web.Request) -> web.Response:
        """Handle health check requests.
        
        Args:
            request: HTTP request
            
        Returns:
            JSON response with health status
        """
        try:
            health_status = await self.health_checker.check_health()
            
            # Return 200 for healthy/degraded, 503 for unhealthy
            status_code = 200 if health_status.get("status") in ["healthy", "degraded"] else 503
            
            return web.json_response(health_status, status=status_code)
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return web.json_response(
                {
                    "status": "unhealthy",
                    "error": str(e)
                },
                status=503
            )

    async def _ready_handler(self, request: web.Request) -> web.Response:
        """Handle readiness check requests.
        
        Args:
            request: HTTP request
            
        Returns:
            JSON response with readiness status
        """
        try:
            health_status = await self.health_checker.check_health()
            
            # Only return 200 if fully healthy
            status_code = 200 if health_status.get("status") == "healthy" else 503
            
            return web.json_response(
                {
                    "ready": status_code == 200,
                    "status": health_status.get("status")
                },
                status=status_code
            )
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return web.json_response(
                {
                    "ready": False,
                    "error": str(e)
                },
                status=503
            )

    def _run_server(self) -> None:
        """Run the server in a separate thread."""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        async def start_server():
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await site.start()
            logger.info(f"HTTP health server started on port {self.port}")
            
            # Keep the server running
            while True:
                await asyncio.sleep(1)
        
        try:
            self.loop.run_until_complete(start_server())
        except Exception as e:
            logger.error(f"Health server error: {e}")

    def start(self) -> None:
        """Start the HTTP health server in a background thread."""
        self.thread = threading.Thread(target=self._run_server, daemon=True)
        self.thread.start()
        logger.info("HTTP health server thread started")

    def stop(self) -> None:
        """Stop the HTTP health server."""
        if self.loop and self.runner is not None:
            async def cleanup():
                if self.runner:
                    await self.runner.cleanup()
                    logger.info("HTTP health server stopped")
            
            asyncio.run_coroutine_threadsafe(cleanup(), self.loop)


# Made with Bob