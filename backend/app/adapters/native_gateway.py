"""Native Gateway adapter implementation for API Intelligence Plane.

Implements the BaseGatewayAdapter interface for the native/built-in Gateway.
This adapter communicates with our Demo Gateway (Spring Boot application).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import httpx

from backend.app.adapters.base import BaseGatewayAdapter
from backend.app.models.api import (
    API,
    APIStatus,
    AuthenticationType,
    CurrentMetrics,
    DiscoveryMethod,
    Endpoint,
)
from backend.app.models.metric import Metric

logger = logging.getLogger(__name__)


class NativeGatewayAdapter(BaseGatewayAdapter):
    """Native Gateway adapter for built-in Gateway support.

    This adapter communicates with the Demo Gateway (Spring Boot) via REST API
    to discover APIs, collect metrics, and manage policies.
    """

    def __init__(self, gateway):
        """Initialize the Native Gateway adapter.

        Args:
            gateway: Gateway configuration
        """
        super().__init__(gateway)
        self._client: Optional[httpx.AsyncClient] = None
        self._base_url = str(gateway.connection_url).rstrip("/")

    async def connect(self) -> bool:
        """Establish connection to the Native Gateway.

        Returns:
            bool: True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            # Create HTTP client with authentication
            headers = self._get_auth_headers()
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )

            # Test connection
            response = await self._client.get("/actuator/health")
            response.raise_for_status()

            self._connected = True
            logger.info(f"Connected to Native Gateway: {self.gateway.name}")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to Native Gateway: {e}")
            self._connected = False
            raise ConnectionError(f"Failed to connect to Gateway: {e}")

    async def disconnect(self) -> None:
        """Close connection to the Native Gateway."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info(f"Disconnected from Native Gateway: {self.gateway.name}")

    async def test_connection(self) -> dict[str, Any]:
        """Test the Gateway connection and return status.

        Returns:
            dict: Connection status with details
        """
        try:
            start_time = datetime.utcnow()
            response = await self._client.get("/actuator/health")
            latency = (datetime.utcnow() - start_time).total_seconds() * 1000

            data = response.json()
            return {
                "connected": True,
                "latency_ms": latency,
                "version": data.get("version", "unknown"),
                "error": None,
            }
        except Exception as e:
            return {
                "connected": False,
                "latency_ms": 0,
                "version": "unknown",
                "error": str(e),
            }

    async def discover_apis(self) -> list[API]:
        """Discover all APIs registered in the Native Gateway.

        Returns:
            list[API]: List of discovered API entities
        """
        self._ensure_connected()

        try:
            response = await self._client.get("/api/v1/apis")
            response.raise_for_status()
            apis_data = response.json()

            apis = []
            for api_data in apis_data:
                api = self._parse_api_response(api_data)
                apis.append(api)

            logger.info(f"Discovered {len(apis)} APIs from Native Gateway")
            return apis

        except Exception as e:
            logger.error(f"Failed to discover APIs: {e}")
            raise RuntimeError(f"Failed to discover APIs: {e}")

    async def get_api_details(self, api_id: str) -> Optional[API]:
        """Get detailed information about a specific API.

        Args:
            api_id: API identifier in the Gateway

        Returns:
            Optional[API]: API entity if found
        """
        self._ensure_connected()

        try:
            response = await self._client.get(f"/api/v1/apis/{api_id}")
            if response.status_code == 404:
                return None

            response.raise_for_status()
            api_data = response.json()
            return self._parse_api_response(api_data)

        except Exception as e:
            logger.error(f"Failed to get API details for {api_id}: {e}")
            return None

    async def collect_metrics(
        self, api_id: Optional[str] = None, time_range_minutes: int = 5
    ) -> list[Metric]:
        """Collect performance metrics from the Native Gateway.

        Args:
            api_id: Optional API identifier to filter metrics
            time_range_minutes: Time range for metrics collection

        Returns:
            list[Metric]: List of collected metrics
        """
        self._ensure_connected()

        try:
            params = {"timeRange": time_range_minutes}
            if api_id:
                params["apiId"] = api_id

            response = await self._client.get("/api/v1/metrics", params=params)
            response.raise_for_status()
            metrics_data = response.json()

            metrics = []
            for metric_data in metrics_data:
                metric = self._parse_metric_response(metric_data)
                metrics.append(metric)

            logger.info(f"Collected {len(metrics)} metrics from Native Gateway")
            return metrics

        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            raise RuntimeError(f"Failed to collect metrics: {e}")

    async def get_api_logs(
        self, api_id: str, limit: int = 100, time_range_minutes: int = 60
    ) -> list[dict[str, Any]]:
        """Retrieve API access logs from the Native Gateway.

        Args:
            api_id: API identifier
            limit: Maximum number of log entries
            time_range_minutes: Time range for log retrieval

        Returns:
            list[dict]: List of log entries
        """
        self._ensure_connected()

        try:
            params = {
                "apiId": api_id,
                "limit": limit,
                "timeRange": time_range_minutes,
            }
            response = await self._client.get("/api/v1/logs", params=params)
            response.raise_for_status()
            return response.json()

        except Exception as e:
            logger.error(f"Failed to get API logs: {e}")
            return []

    async def apply_rate_limit_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply a rate limiting policy to an API.

        Args:
            api_id: API identifier
            policy: Rate limit policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()

        try:
            response = await self._client.post(
                f"/api/v1/apis/{api_id}/rate-limit", json=policy
            )
            response.raise_for_status()
            logger.info(f"Applied rate limit policy to API {api_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to apply rate limit policy: {e}")
            return False

    async def remove_rate_limit_policy(self, api_id: str) -> bool:
        """Remove rate limiting policy from an API.

        Args:
            api_id: API identifier

        Returns:
            bool: True if policy removed successfully
        """
        self._ensure_connected()

        try:
            response = await self._client.delete(f"/api/v1/apis/{api_id}/rate-limit")
            response.raise_for_status()
            logger.info(f"Removed rate limit policy from API {api_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to remove rate limit policy: {e}")
            return False

    async def get_gateway_health(self) -> dict[str, Any]:
        """Get Native Gateway health status and metrics.

        Returns:
            dict: Gateway health information
        """
        self._ensure_connected()

        try:
            response = await self._client.get("/actuator/health")
            response.raise_for_status()
            health_data = response.json()

            # Get additional metrics
            metrics_response = await self._client.get("/actuator/metrics")
            metrics_data = metrics_response.json() if metrics_response.status_code == 200 else {}

            return {
                "status": health_data.get("status", "unknown").lower(),
                "uptime_seconds": metrics_data.get("uptime", 0),
                "total_apis": health_data.get("components", {}).get("apiCount", 0),
                "total_requests": metrics_data.get("totalRequests", 0),
                "error_rate": metrics_data.get("errorRate", 0.0),
            }

        except Exception as e:
            logger.error(f"Failed to get Gateway health: {e}")
            return {
                "status": "unhealthy",
                "uptime_seconds": 0,
                "total_apis": 0,
                "total_requests": 0,
                "error_rate": 1.0,
            }

    async def get_capabilities(self) -> list[str]:
        """Get list of capabilities supported by Native Gateway.

        Returns:
            list[str]: List of capability names
        """
        return [
            "api_discovery",
            "metrics_collection",
            "log_streaming",
            "policy_management",
            "rate_limiting",
            "authentication_management",
            "monitoring",
        ]

    def _ensure_connected(self) -> None:
        """Ensure adapter is connected to Gateway.

        Raises:
            RuntimeError: If not connected
        """
        if not self._connected or not self._client:
            raise RuntimeError("Not connected to Gateway. Call connect() first.")

    def _get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for Gateway API.

        Returns:
            dict: HTTP headers with authentication
        """
        headers = {"Content-Type": "application/json"}

        # Add authentication based on credentials type
        creds = self.gateway.credentials
        if creds.api_key:
            headers["X-API-Key"] = creds.api_key
        elif creds.token:
            headers["Authorization"] = f"Bearer {creds.token}"
        elif creds.username and creds.password:
            import base64

            auth_str = f"{creds.username}:{creds.password}"
            auth_bytes = auth_str.encode("utf-8")
            auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
            headers["Authorization"] = f"Basic {auth_b64}"

        return headers

    def _parse_api_response(self, data: dict[str, Any]) -> API:
        """Parse API response from Gateway into API model.

        Args:
            data: Raw API data from Gateway

        Returns:
            API: Parsed API entity
        """
        # Parse endpoints
        endpoints = []
        for ep_data in data.get("endpoints", []):
            endpoint = Endpoint(
                path=ep_data["path"],
                method=ep_data["method"],
                description=ep_data.get("description"),
                parameters=ep_data.get("parameters", []),
                response_codes=ep_data.get("responseCodes", []),
            )
            endpoints.append(endpoint)

        # Parse current metrics
        metrics_data = data.get("currentMetrics", {})
        current_metrics = CurrentMetrics(
            response_time_p50=metrics_data.get("responseTimeP50", 0.0),
            response_time_p95=metrics_data.get("responseTimeP95", 0.0),
            response_time_p99=metrics_data.get("responseTimeP99", 0.0),
            error_rate=metrics_data.get("errorRate", 0.0),
            throughput=metrics_data.get("throughput", 0.0),
            availability=metrics_data.get("availability", 100.0),
            last_error=datetime.fromisoformat(metrics_data["lastError"])
            if metrics_data.get("lastError")
            else None,
            measured_at=datetime.fromisoformat(metrics_data.get("measuredAt", datetime.utcnow().isoformat())),
        )

        return API(
            id=uuid4(),
            gateway_id=self.gateway.id,
            name=data["name"],
            version=data.get("version"),
            base_path=data["basePath"],
            endpoints=endpoints,
            methods=data.get("methods", []),
            authentication_type=AuthenticationType(
                data.get("authenticationType", "none")
            ),
            authentication_config=data.get("authenticationConfig"),
            tags=data.get("tags", []),
            is_shadow=data.get("isShadow", False),
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=APIStatus(data.get("status", "active")),
            health_score=data.get("healthScore", 100.0),
            current_metrics=current_metrics,
        )

    def _parse_metric_response(self, data: dict[str, Any]) -> Metric:
        """Parse metric response from Gateway into Metric model.

        Args:
            data: Raw metric data from Gateway

        Returns:
            Metric: Parsed Metric entity
        """
        return Metric(
            id=uuid4(),
            api_id=uuid4(),  # Will be resolved later
            gateway_id=self.gateway.id,
            timestamp=datetime.fromisoformat(data["timestamp"]),
            response_time_p50=data["responseTimeP50"],
            response_time_p95=data["responseTimeP95"],
            response_time_p99=data["responseTimeP99"],
            error_rate=data["errorRate"],
            error_count=data["errorCount"],
            request_count=data["requestCount"],
            throughput=data["throughput"],
            availability=data["availability"],
            status_codes=data.get("statusCodes", {}),
            endpoint_metrics=data.get("endpointMetrics"),
        )

# Made with Bob
