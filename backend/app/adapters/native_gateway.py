"""Demo Gateway adapter implementation for API Intelligence Plane.

Implements the BaseGatewayAdapter interface for the Demo Gateway (Spring Boot).
The Demo Gateway serves as both a testing gateway and reference implementation
of the vendor-neutral architecture.

Note: "Native Gateway" and "Demo Gateway" refer to the same implementation.
"""

import base64
import logging
from datetime import datetime, timedelta
from typing import Any, Optional
from uuid import uuid4

import httpx

from app.adapters.base import BaseGatewayAdapter
from app.models.base.api import (
    API,
    APIDefinition,
    APIStatus,
    APIType,
    AuthenticationType,
    DeploymentInfo,
    DiscoveryMethod,
    Endpoint,
    EndpointParameter,
    IntelligenceMetadata,
    OwnershipInfo,
    PolicyAction,
    PolicyActionType,
    VersionInfo,
)
from app.models.base.metric import EndpointMetric, Metric, TimeBucket
from app.models.base.transaction import (
    CacheStatus,
    EventStatus,
    EventType,
    TransactionalLog,
)
from app.models.gateway import Gateway

logger = logging.getLogger(__name__)


class NativeGatewayAdapter(BaseGatewayAdapter):
    """Demo Gateway adapter for vendor-neutral gateway support.

    This adapter communicates with the Demo Gateway (Spring Boot) via REST API
    to discover APIs, collect metrics, and manage policies. The Demo Gateway
    serves as both a testing gateway and reference implementation.
    
    Note: Class name retained as "NativeGatewayAdapter" for backward compatibility,
    but it implements the Demo Gateway functionality.
    """

    def __init__(self, gateway: Gateway):
        """Initialize the Native Gateway adapter.

        Args:
            gateway: Gateway configuration
        """
        super().__init__(gateway)
        self._client: Optional[httpx.AsyncClient] = None
        self._base_url = str(gateway.base_url).rstrip("/")

    async def connect(self) -> bool:
        """Establish connection to the Native Gateway.

        Returns:
            bool: True if connection successful

        Raises:
            ConnectionError: If connection fails
        """
        try:
            headers = self._get_auth_headers()
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )

            response = await self._client.get("/actuator/health")
            response.raise_for_status()

            self._connected = True
            logger.info("Connected to Native Gateway: %s", self.gateway.name)
            return True

        except Exception as e:
            logger.error("Failed to connect to Native Gateway: %s", e)
            self._connected = False
            raise ConnectionError(f"Failed to connect to Gateway: {e}")

    async def disconnect(self) -> None:
        """Close connection to the Native Gateway."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._connected = False
        logger.info("Disconnected from Native Gateway: %s", self.gateway.name)

    async def test_connection(self) -> dict[str, Any]:
        """Test the Gateway connection and return status.

        Returns:
            dict: Connection status with details
        """
        try:
            self._ensure_connected()
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            start_time = datetime.utcnow()
            response = await client.get("/actuator/health")
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
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.get("/api/v1/apis")
            response.raise_for_status()
            payload = response.json()

            apis_data = payload.get("items", payload) if isinstance(payload, dict) else payload
            apis = [self._transform_to_api(api_data) for api_data in apis_data]

            logger.info("Discovered %s APIs from Native Gateway", len(apis))
            return apis

        except Exception as e:
            logger.error("Failed to discover APIs: %s", e)
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
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.get(f"/api/v1/apis/{api_id}")
            if response.status_code == 404:
                return None

            response.raise_for_status()
            api_data = response.json()
            return self._transform_to_api(api_data)

        except Exception as e:
            logger.error("Failed to get API details for %s: %s", api_id, e)
            return None

    async def get_transactional_logs(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[TransactionalLog]:
        """Retrieve vendor-neutral transactional logs from the Native Gateway."""
        self._ensure_connected()

        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            params: dict[str, str | int] = {}

            if start_time:
                params["startTime"] = start_time.isoformat()
            if end_time:
                params["endTime"] = end_time.isoformat()

            response = await client.get("/gateway/logs", params=params)
            if response.status_code == 404:
                logger.info("Transactional logs endpoint not available on Native Gateway")
                return []

            response.raise_for_status()
            payload = response.json()
            logs_data = payload.get("items", payload) if isinstance(payload, dict) else payload

            transformed_logs: list[TransactionalLog] = []
            for index, item in enumerate(logs_data):
                if not isinstance(item, dict):
                    continue
                transformed_logs.append(
                    self._transform_to_transactional_log(
                        item,
                        api_id=None,
                        fallback_index=index,
                    )
                )

            return transformed_logs

        except Exception as e:
            logger.error("Failed to get transactional logs: %s", e)
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
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                f"/api/v1/apis/{api_id}/rate-limit", json=policy
            )
            response.raise_for_status()
            logger.info("Applied rate limit policy to API %s", api_id)
            return True

        except Exception as e:
            logger.error("Failed to apply rate limit policy: %s", e)
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
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.delete(f"/api/v1/apis/{api_id}/rate-limit")
            response.raise_for_status()
            logger.info("Removed rate limit policy from API %s", api_id)
            return True

        except Exception as e:
            logger.error("Failed to remove rate limit policy: %s", e)
            return False

    async def apply_caching_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply a caching policy to an API.

        Args:
            api_id: API identifier
            policy: Caching policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()

        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                f"/api/v1/apis/{api_id}/caching", json=policy
            )
            response.raise_for_status()
            logger.info("Applied caching policy to API %s", api_id)
            return True

        except Exception as e:
            logger.error("Failed to apply caching policy: %s", e)
            return False

    async def remove_caching_policy(self, api_id: str) -> bool:
        """Remove caching policy from an API.

        Args:
            api_id: API identifier

        Returns:
            bool: True if policy removed successfully
        """
        self._ensure_connected()

        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.delete(f"/api/v1/apis/{api_id}/caching")
            response.raise_for_status()
            logger.info("Removed caching policy from API %s", api_id)
            return True

        except Exception as e:
            logger.error("Failed to remove caching policy: %s", e)
            return False

    async def apply_compression_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply a compression policy to an API.

        Args:
            api_id: API identifier
            policy: Compression policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()

        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                f"/api/v1/apis/{api_id}/compression", json=policy
            )
            response.raise_for_status()
            logger.info("Applied compression policy to API %s", api_id)
            return True

        except Exception as e:
            logger.error("Failed to apply compression policy: %s", e)
            return False

    async def remove_compression_policy(self, api_id: str) -> bool:
        """Remove compression policy from an API.

        Args:
            api_id: API identifier

        Returns:
            bool: True if policy removed successfully
        """
        self._ensure_connected()

        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.delete(f"/api/v1/apis/{api_id}/compression")
            response.raise_for_status()
            logger.info("Removed compression policy from API %s", api_id)
            return True

        except Exception as e:
            logger.error("Failed to remove compression policy: %s", e)
            return False

    async def get_gateway_health(self) -> dict[str, Any]:
        """Get Native Gateway health status and metrics.

        Returns:
            dict: Gateway health information
        """
        self._ensure_connected()

        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.get("/actuator/health")
            response.raise_for_status()
            health_data = response.json()

            metrics_response = await client.get("/actuator/metrics")
            metrics_data = metrics_response.json() if metrics_response.status_code == 200 else {}

            return {
                "status": health_data.get("status", "unknown").lower(),
                "uptime_seconds": metrics_data.get("uptime", 0),
                "total_apis": health_data.get("components", {}).get("apiCount", 0),
                "total_requests": metrics_data.get("totalRequests", 0),
                "error_rate": metrics_data.get("errorRate", 0.0),
            }

        except Exception as e:
            logger.error("Failed to get Gateway health: %s", e)
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

        creds = self.gateway.base_url_credentials
        if not creds:
            return headers

        if creds.api_key:
            headers["X-API-Key"] = creds.api_key
        elif creds.token:
            headers["Authorization"] = f"Bearer {creds.token}"
        elif creds.username and creds.password:
            auth_str = f"{creds.username}:{creds.password}"
            auth_bytes = auth_str.encode("utf-8")
            auth_b64 = base64.b64encode(auth_bytes).decode("utf-8")
            headers["Authorization"] = f"Basic {auth_b64}"

        return headers

    def _transform_to_api(self, vendor_data: Any) -> API:
        """Transform native gateway API data to vendor-neutral API model."""
        data = vendor_data if isinstance(vendor_data, dict) else dict(vendor_data)
        now = datetime.utcnow()

        endpoints = [self._build_endpoint(ep_data) for ep_data in data.get("endpoints", [])]
        if not endpoints:
            base_path = data.get("basePath", "/")
            methods = data.get("methods", ["GET"])
            endpoints = [
                Endpoint(
                    path=base_path,
                    method=method,
                    description=data.get("description"),
                    connection_timeout=None,
                    read_timeout=None,
                )
                for method in methods
            ]

        methods = data.get("methods") or sorted({endpoint.method for endpoint in endpoints}) or ["GET"]
        base_path = data.get("basePath") or data.get("base_path") or "/"

        return API(
            id=data.get("id", uuid4()),
            gateway_id=self.gateway.id,
            name=data["name"],
            display_name=data.get("displayName", data.get("name")),
            description=data.get("description"),
            version_info=VersionInfo(
                current_version=str(data.get("version", "1.0.0")),
                previous_version=None,
                next_version=None,
                version_history=None,
            ),
            type=APIType(str(data.get("type", "REST")).upper()),
            base_path=base_path,
            api_definition=APIDefinition(
                type=str(data.get("type", "REST")).upper(),
                version=str(data.get("version", "1.0.0")),
                base_path=base_path,
                openapi_spec=data.get("openApiSpec") or data.get("openapiSpec"),
                swagger_version=None,
                paths=data.get("paths"),
                schemas=data.get("schemas"),
                security_schemes=data.get("securitySchemes"),
                vendor_extensions=None,
            ),
            endpoints=endpoints,
            methods=methods,
            authentication_type=self._map_authentication_type(
                data.get("authenticationType") or data.get("authentication", {}).get("type")
            ),
            authentication_config=data.get("authenticationConfig") or data.get("authentication"),
            policy_actions=self._extract_policy_actions(data),
            ownership=self._build_ownership(data),
            deployments=self._build_deployments(data),
            intelligence_metadata=IntelligenceMetadata(
                is_shadow=data.get("isShadow", False),
                discovery_method=DiscoveryMethod.REGISTERED,
                discovered_at=self._parse_datetime(data.get("discoveredAt"), now),
                last_seen_at=self._parse_datetime(data.get("lastSeenAt"), now),
                health_score=float(data.get("healthScore", 100.0)),
                risk_score=None,
                security_score=None,
                compliance_status=None,
                usage_trend=None,
            ),
            status=APIStatus(data.get("status", "active")),
            is_active=data.get("status", "active") == APIStatus.ACTIVE.value,
            icon=None,
            maturity_state=None,
            publishing=None,
            vendor_metadata={
                "vendor": "native",
                "gateway_name": self.gateway.name,
                "upstream_url": data.get("upstreamUrl"),
                "native_id": data.get("id"),
                "raw_status": data.get("status"),
            },
        )

    def _transform_to_metric(self, vendor_data: Any) -> Metric:
        """Transform native gateway metric data to vendor-neutral Metric model."""
        data = vendor_data if isinstance(vendor_data, dict) else dict(vendor_data)

        request_count = int(data.get("requestCount", 0))
        success_count = int(data.get("successCount", max(request_count - int(data.get("errorCount", 0)), 0)))
        failure_count = int(data.get("failureCount", data.get("errorCount", 0)))
        timeout_count = int(data.get("timeoutCount", 0))
        total_data_size = int(data.get("totalDataSize", 0))
        avg_request_size = float(data.get("avgRequestSize", 0.0))
        avg_response_size = float(data.get("avgResponseSize", 0.0))
        cache_hit_count = int(data.get("cacheHitCount", 0))
        cache_miss_count = int(data.get("cacheMissCount", 0))
        cache_bypass_count = int(data.get("cacheBypassCount", 0))
        status_codes = {str(k): int(v) for k, v in data.get("statusCodes", {}).items()}

        endpoint_metrics = self._build_endpoint_metrics(data.get("endpointMetrics", []))
        time_bucket = self._map_time_bucket(data.get("timeBucket", data.get("interval", "5m")))

        return Metric(
            id=data.get("id", uuid4()),
            gateway_id=self.gateway.id,
            api_id=str(data.get("apiId", "unknown")),
            application_id=data.get("applicationId"),
            operation=data.get("operation"),
            timestamp=self._parse_datetime(data.get("timestamp"), datetime.utcnow()),
            time_bucket=time_bucket,
            request_count=request_count,
            success_count=success_count,
            failure_count=failure_count,
            timeout_count=timeout_count,
            error_rate=self._safe_percentage(failure_count, request_count),
            availability=float(data.get("availability", 100.0 - self._safe_percentage(failure_count, request_count))),
            response_time_avg=float(data.get("responseTimeAvg", data.get("responseTimeP50", 0.0))),
            response_time_min=float(data.get("responseTimeMin", 0.0)),
            response_time_max=float(data.get("responseTimeMax", data.get("responseTimeP99", 0.0))),
            response_time_p50=float(data.get("responseTimeP50", 0.0)),
            response_time_p95=float(data.get("responseTimeP95", data.get("responseTimeP50", 0.0))),
            response_time_p99=float(data.get("responseTimeP99", data.get("responseTimeP95", 0.0))),
            gateway_time_avg=float(data.get("gatewayTimeAvg", 0.0)),
            backend_time_avg=float(data.get("backendTimeAvg", 0.0)),
            throughput=float(data.get("throughput", 0.0)),
            total_data_size=total_data_size,
            avg_request_size=avg_request_size,
            avg_response_size=avg_response_size,
            cache_hit_count=cache_hit_count,
            cache_miss_count=cache_miss_count,
            cache_bypass_count=cache_bypass_count,
            cache_hit_rate=self._safe_percentage(
                cache_hit_count, cache_hit_count + cache_miss_count
            ),
            status_2xx_count=self._status_group_count(status_codes, 200, 299),
            status_3xx_count=self._status_group_count(status_codes, 300, 399),
            status_4xx_count=self._status_group_count(status_codes, 400, 499),
            status_5xx_count=self._status_group_count(status_codes, 500, 599),
            status_codes=status_codes,
            endpoint_metrics=endpoint_metrics or None,
            vendor_metadata={
                "vendor": "native",
                "raw_metric_id": data.get("id"),
            },
        )

    def _transform_to_transactional_log(
        self, vendor_data: Any, api_id: Optional[str] = None, fallback_index: int = 0
    ) -> TransactionalLog:
        """Transform native gateway log payload to vendor-neutral transactional log."""
        data = vendor_data if isinstance(vendor_data, dict) else dict(vendor_data)
        timestamp = self._parse_datetime(
            data.get("timestamp") or data.get("createdAt"),
            datetime.utcnow(),
        )

        resolved_api_id = str(
            data.get("apiId") or api_id or data.get("api_id") or "unknown-api"
        )
        status_code = int(data.get("statusCode", data.get("status_code", 200)))
        total_time_ms = int(data.get("latencyMs", data.get("totalTimeMs", 0)))
        gateway_time_ms = int(data.get("gatewayTimeMs", max(total_time_ms // 2, 0)))
        backend_time_ms = int(
            data.get("backendTimeMs", max(total_time_ms - gateway_time_ms, 0))
        )

        return TransactionalLog(
            api_id=resolved_api_id,
            api_name=str(data.get("apiName", data.get("api_name", resolved_api_id))),
            api_version=str(data.get("apiVersion", data.get("api_version", "1.0.0"))),
            operation=str(
                data.get("operation")
                or data.get("path")
                or data.get("requestPath")
                or f"operation-{fallback_index}"
            ),
            event_type=EventType.TRANSACTIONAL,
            timestamp=int(timestamp.timestamp() * 1000),
            http_method=str(data.get("method", data.get("httpMethod", "GET"))),
            request_path=str(data.get("path", data.get("requestPath", "/"))),
            request_headers=data.get("requestHeaders", {}),
            request_payload=data.get("requestPayload"),
            request_size=int(data.get("requestSize", 0)),
            query_parameters=data.get("queryParameters", {}),
            status_code=status_code,
            response_headers=data.get("responseHeaders", {}),
            response_payload=data.get("responsePayload"),
            response_size=int(data.get("responseSize", 0)),
            client_id=str(
                data.get("applicationId")
                or data.get("clientId")
                or data.get("consumerId")
                or "unknown-client"
            ),
            client_name=data.get("applicationName", data.get("clientName")),
            client_ip=str(data.get("clientIp", data.get("client_ip", "0.0.0.0"))),
            user_agent=data.get("userAgent"),
            total_time_ms=total_time_ms,
            gateway_time_ms=gateway_time_ms,
            backend_time_ms=backend_time_ms,
            status=EventStatus.SUCCESS if status_code < 400 else EventStatus.FAILURE,
            correlation_id=str(
                data.get("correlationId")
                or data.get("requestId")
                or data.get("traceId")
                or f"{resolved_api_id}-{fallback_index}"
            ),
            session_id=data.get("sessionId"),
            trace_id=data.get("traceId"),
            cache_status=CacheStatus(
                str(data.get("cacheStatus", "disabled")).lower()
            ),
            backend_url=str(data.get("backendUrl", self._base_url)),
            backend_method=data.get("backendMethod"),
            backend_request_headers=data.get("backendRequestHeaders", {}),
            backend_response_headers=data.get("backendResponseHeaders", {}),
            error_origin=None,
            error_message=data.get("errorMessage"),
            error_code=data.get("errorCode"),
            external_calls=[],
            gateway_id=str(self.gateway.id),
            gateway_node=data.get("gatewayNode"),
            vendor_metadata={
                "vendor": "native",
                "raw_log_id": data.get("id"),
            },
        )

    def _transform_to_policy_action(self, vendor_data: Any) -> PolicyAction:
        """Transform native gateway policy data to vendor-neutral policy action."""
        data = vendor_data if isinstance(vendor_data, dict) else dict(vendor_data)
        return PolicyAction(
            action_type=self._map_policy_action_type(data.get("type")),
            enabled=data.get("enabled", True),
            stage=data.get("stage"),
            config=data.get("config") or data.get("policy"),
            vendor_config={
                "vendor": "native",
                "raw_policy": data,
            },
            name=data.get("name"),
            description=data.get("description"),
        )

    def _build_endpoint(self, ep_data: dict[str, Any]) -> Endpoint:
        """Build vendor-neutral endpoint model."""
        parameters = [
            EndpointParameter(
                name=param.get("name", "unknown"),
                type=param.get("type", "query"),
                data_type=param.get("dataType", param.get("data_type", "string")),
                required=param.get("required", False),
                description=param.get("description"),
            )
            for param in ep_data.get("parameters", [])
        ]
        return Endpoint(
            path=ep_data["path"],
            method=ep_data["method"],
            description=ep_data.get("description"),
            parameters=parameters,
            response_codes=ep_data.get("responseCodes", ep_data.get("response_codes", [])),
            connection_timeout=ep_data.get("connectionTimeout"),
            read_timeout=ep_data.get("readTimeout"),
        )

    def _extract_policy_actions(self, data: dict[str, Any]) -> Optional[list[PolicyAction]]:
        """Extract policy actions from native gateway payload."""
        policies = data.get("policies") or data.get("policyActions") or []
        if not policies:
            return None
        return [self._transform_to_policy_action(policy) for policy in policies]

    def _build_ownership(self, data: dict[str, Any]) -> Optional[OwnershipInfo]:
        """Build ownership information when available."""
        ownership = data.get("ownership") or {}
        if not ownership and not data.get("team") and not data.get("contact"):
            return None

        return OwnershipInfo(
            team=ownership.get("team", data.get("team")),
            contact=ownership.get("contact", data.get("contact")),
            repository=ownership.get("repository"),
            organization=ownership.get("organization"),
            department=ownership.get("department"),
        )

    def _build_deployments(self, data: dict[str, Any]) -> Optional[list[DeploymentInfo]]:
        """Build deployment information when available."""
        deployments = data.get("deployments", [])
        if not deployments:
            environment = data.get("environment")
            if not environment:
                return None
            deployments = [
                {
                    "environment": environment,
                    "gatewayEndpoints": {"default": data.get("upstreamUrl", self._base_url)},
                    "deploymentStatus": data.get("status", "active"),
                }
            ]

        return [
            DeploymentInfo(
                environment=deployment.get("environment", "unknown"),
                gateway_endpoints=deployment.get(
                    "gatewayEndpoints",
                    deployment.get("gateway_endpoints", {}),
                ),
                deployed_at=self._parse_optional_datetime(
                    deployment.get("deployedAt") or deployment.get("deployed_at")
                ),
                deployment_status=deployment.get(
                    "deploymentStatus", deployment.get("deployment_status")
                ),
            )
            for deployment in deployments
        ]

    def _build_endpoint_metrics(self, metrics: list[dict[str, Any]]) -> list[EndpointMetric]:
        """Build per-endpoint metric models."""
        return [
            EndpointMetric(
                endpoint=metric.get("endpoint", metric.get("path", "/")),
                method=metric.get("method", "GET"),
                request_count=int(metric.get("requestCount", 0)),
                success_count=int(metric.get("successCount", 0)),
                failure_count=int(metric.get("failureCount", 0)),
                error_rate=float(
                    metric.get(
                        "errorRate",
                        self._safe_percentage(
                            int(metric.get("failureCount", 0)),
                            int(metric.get("requestCount", 0)),
                        ),
                    )
                ),
                response_time_avg=float(metric.get("responseTimeAvg", 0.0)),
                response_time_p50=float(metric.get("responseTimeP50", 0.0)),
                response_time_p95=float(metric.get("responseTimeP95", 0.0)),
                response_time_p99=float(metric.get("responseTimeP99", 0.0)),
            )
            for metric in metrics
        ]

    def _map_authentication_type(self, auth_type: Optional[str]) -> AuthenticationType:
        """Map native auth type to vendor-neutral enum."""
        if not auth_type:
            return AuthenticationType.NONE

        normalized = str(auth_type).lower()
        mapping = {
            "none": AuthenticationType.NONE,
            "basic": AuthenticationType.BASIC,
            "bearer": AuthenticationType.BEARER,
            "oauth2": AuthenticationType.OAUTH2,
            "api_key": AuthenticationType.API_KEY,
            "apikey": AuthenticationType.API_KEY,
            "mtls": AuthenticationType.MTLS,
        }
        return mapping.get(normalized, AuthenticationType.CUSTOM)

    def _map_policy_action_type(self, policy_type: Optional[str]) -> PolicyActionType:
        """Map native policy type to vendor-neutral enum."""
        if not policy_type:
            return PolicyActionType.CUSTOM

        normalized = str(policy_type).lower().replace("-", "_")
        mapping = {
            "authentication": PolicyActionType.AUTHENTICATION,
            "authorization": PolicyActionType.AUTHORIZATION,
            "rate_limit": PolicyActionType.RATE_LIMITING,
            "rate_limiting": PolicyActionType.RATE_LIMITING,
            "caching": PolicyActionType.CACHING,
            "cache": PolicyActionType.CACHING,
            "logging": PolicyActionType.LOGGING,
            "validation": PolicyActionType.VALIDATION,
            "cors": PolicyActionType.CORS,
            "compression": PolicyActionType.COMPRESSION,
            "tls": PolicyActionType.TLS,
            "security_headers": PolicyActionType.CUSTOM,
        }
        return mapping.get(normalized, PolicyActionType.CUSTOM)

    def _map_time_bucket(self, value: str) -> TimeBucket:
        """Map raw interval value to supported time bucket."""
        normalized = str(value).lower()
        mapping = {
            "1m": TimeBucket.ONE_MINUTE,
            "5m": TimeBucket.FIVE_MINUTES,
            "15m": TimeBucket.FIVE_MINUTES,
            "1h": TimeBucket.ONE_HOUR,
            "1d": TimeBucket.ONE_DAY,
        }
        return mapping.get(normalized, TimeBucket.FIVE_MINUTES)

    def _status_group_count(self, status_codes: dict[str, int], start: int, end: int) -> int:
        """Count status codes within inclusive range."""
        total = 0
        for code, count in status_codes.items():
            try:
                numeric_code = int(code)
            except (TypeError, ValueError):
                continue
            if start <= numeric_code <= end:
                total += count
        return total

    def _safe_percentage(self, numerator: int, denominator: int) -> float:
        """Safely calculate a percentage."""
        if denominator <= 0:
            return 0.0
        return (numerator / denominator) * 100

    def _parse_datetime(self, value: Optional[str], default: datetime) -> datetime:
        """Parse datetime string with fallback."""
        parsed = self._parse_optional_datetime(value)
        return parsed or default

    def _parse_optional_datetime(self, value: Optional[str]) -> Optional[datetime]:
        """Parse optional datetime string."""
        if not value:
            return None

        normalized = str(value).replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized)
        except ValueError:
            logger.debug("Failed to parse datetime value: %s", value)
            return None

    async def apply_authentication_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply authentication policy to an API.

        Args:
            api_id: API identifier
            policy: Authentication policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()
        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                "/policies/authentication",
                json={"apiId": api_id, "policy": policy},
            )
            response.raise_for_status()
            logger.info("Applied authentication policy to API %s", api_id)
            return True
        except Exception as e:
            logger.error("Failed to apply authentication policy: %s", e)
            return False

    async def apply_authorization_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply authorization policy to an API.

        Args:
            api_id: API identifier
            policy: Authorization policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()
        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                "/policies/authorization",
                json={"apiId": api_id, "policy": policy},
            )
            response.raise_for_status()
            logger.info("Applied authorization policy to API %s", api_id)
            return True
        except Exception as e:
            logger.error("Failed to apply authorization policy: %s", e)
            return False

    async def apply_tls_policy(self, api_id: str, policy: dict[str, Any]) -> bool:
        """Apply TLS/HTTPS policy to an API.

        Args:
            api_id: API identifier
            policy: TLS policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()
        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                "/policies/tls",
                json={"apiId": api_id, "policy": policy},
            )
            response.raise_for_status()
            logger.info("Applied TLS policy to API %s", api_id)
            return True
        except Exception as e:
            logger.error("Failed to apply TLS policy: %s", e)
            return False

    async def apply_cors_policy(self, api_id: str, policy: dict[str, Any]) -> bool:
        """Apply CORS policy to an API.

        Args:
            api_id: API identifier
            policy: CORS policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()
        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                "/policies/cors",
                json={"apiId": api_id, "policy": policy},
            )
            response.raise_for_status()
            logger.info("Applied CORS policy to API %s", api_id)
            return True
        except Exception as e:
            logger.error("Failed to apply CORS policy: %s", e)
            return False

    async def apply_validation_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply input validation policy to an API.

        Args:
            api_id: API identifier
            policy: Validation policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()
        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                "/policies/validation",
                json={"apiId": api_id, "policy": policy},
            )
            response.raise_for_status()
            logger.info("Applied validation policy to API %s", api_id)
            return True
        except Exception as e:
            logger.error("Failed to apply validation policy: %s", e)
            return False

    async def apply_security_headers_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply security headers policy to an API.

        Args:
            api_id: API identifier
            policy: Security headers policy configuration

        Returns:
            bool: True if policy applied successfully
        """
        self._ensure_connected()
        try:
            client = self._client
            if client is None:
                raise RuntimeError("Gateway client is not initialized")

            response = await client.post(
                "/policies/security-headers",
                json={"apiId": api_id, "policy": policy},
            )
            response.raise_for_status()
            logger.info("Applied security headers policy to API %s", api_id)
            return True
        except Exception as e:
            logger.error("Failed to apply security headers policy: %s", e)
            return False


# Made with Bob
