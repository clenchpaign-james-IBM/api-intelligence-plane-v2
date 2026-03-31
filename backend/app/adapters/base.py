"""Base Gateway adapter interface for API Intelligence Plane.

Defines the abstract interface that all Gateway adapters must implement,
following the Strategy pattern for multi-vendor Gateway support.
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from app.models.api import API
from app.models.gateway import Gateway
from app.models.metric import Metric


class BaseGatewayAdapter(ABC):
    """Abstract base class for Gateway adapters.

    This class defines the interface that all Gateway adapters must implement
    to support different Gateway vendors (Native, Kong, Apigee, AWS, Azure, etc.).

    Each adapter is responsible for:
    - Connecting to the Gateway
    - Discovering APIs
    - Collecting metrics
    - Managing policies
    - Retrieving logs
    """

    def __init__(self, gateway: Gateway):
        """Initialize the adapter with a Gateway configuration.

        Args:
            gateway: Gateway configuration containing connection details
        """
        self.gateway = gateway
        self._connected = False

    @abstractmethod
    async def connect(self) -> bool:
        """Establish connection to the Gateway.

        Returns:
            bool: True if connection successful, False otherwise

        Raises:
            ConnectionError: If connection fails
        """
        pass

    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the Gateway.

        Performs cleanup and releases resources.
        """
        pass

    @abstractmethod
    async def test_connection(self) -> dict[str, Any]:
        """Test the Gateway connection and return status.

        Returns:
            dict: Connection status with details:
                - connected: bool
                - latency_ms: float
                - version: str
                - error: Optional[str]
        """
        pass

    @abstractmethod
    async def discover_apis(self) -> list[API]:
        """Discover all APIs registered in the Gateway.

        Returns:
            list[API]: List of discovered API entities

        Raises:
            RuntimeError: If not connected to Gateway
        """
        pass

    @abstractmethod
    async def get_api_details(self, api_id: str) -> Optional[API]:
        """Get detailed information about a specific API.

        Args:
            api_id: API identifier in the Gateway

        Returns:
            Optional[API]: API entity if found, None otherwise
        """
        pass

    @abstractmethod
    async def collect_metrics(
        self, api_id: Optional[str] = None, time_range_minutes: int = 5
    ) -> list[Metric]:
        """Collect performance metrics from the Gateway.

        Args:
            api_id: Optional API identifier to filter metrics
            time_range_minutes: Time range for metrics collection (default: 5 minutes)

        Returns:
            list[Metric]: List of collected metrics

        Raises:
            RuntimeError: If not connected to Gateway
        """
        pass

    @abstractmethod
    async def get_api_logs(
        self, api_id: str, limit: int = 100, time_range_minutes: int = 60
    ) -> list[dict[str, Any]]:
        """Retrieve API access logs from the Gateway.

        Args:
            api_id: API identifier
            limit: Maximum number of log entries to retrieve
            time_range_minutes: Time range for log retrieval

        Returns:
            list[dict]: List of log entries with timestamp, method, path, status, etc.
        """
        pass

    @abstractmethod
    async def apply_rate_limit_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply a rate limiting policy to an API.

        Args:
            api_id: API identifier
            policy: Rate limit policy configuration

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def remove_rate_limit_policy(self, api_id: str) -> bool:
        """Remove rate limiting policy from an API.

        Args:
            api_id: API identifier

        Returns:
            bool: True if policy removed successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_caching_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply a caching policy to an API.

        Args:
            api_id: API identifier
            policy: Caching policy configuration containing:
                - ttl_seconds: Cache time-to-live in seconds
                - cache_key_strategy: Strategy for generating cache keys
                - invalidation_rules: Rules for cache invalidation
                - vary_headers: Headers to include in cache key

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def remove_caching_policy(self, api_id: str) -> bool:
        """Remove caching policy from an API.

        Args:
            api_id: API identifier

        Returns:
            bool: True if policy removed successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_compression_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply a compression policy to an API.

        Args:
            api_id: API identifier
            policy: Compression policy configuration containing:
                - compression_type: Type of compression (gzip, brotli, deflate)
                - compression_level: Compression level (1-9)
                - min_size_bytes: Minimum response size to compress
                - content_types: List of content types to compress

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def remove_compression_policy(self, api_id: str) -> bool:
        """Remove compression policy from an API.

        Args:
            api_id: API identifier

        Returns:
            bool: True if policy removed successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_authentication_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply authentication policy to an API.

        Args:
            api_id: API identifier
            policy: Authentication policy configuration containing:
                - auth_type: Type of authentication (oauth2, jwt, api_key, basic)
                - provider: Authentication provider details
                - scopes: Required scopes (for OAuth2)
                - validation_rules: Token validation rules

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_authorization_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply authorization policy to an API.

        Args:
            api_id: API identifier
            policy: Authorization policy configuration containing:
                - policy_type: Type of authorization (rbac, abac, acl)
                - roles: Role definitions
                - permissions: Permission mappings
                - rules: Authorization rules

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_tls_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply TLS/SSL policy to an API.

        Args:
            api_id: API identifier
            policy: TLS policy configuration containing:
                - enforce_https: Force HTTPS only
                - min_tls_version: Minimum TLS version (1.2, 1.3)
                - cipher_suites: Allowed cipher suites
                - hsts_enabled: Enable HSTS header

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_cors_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply CORS policy to an API.

        Args:
            api_id: API identifier
            policy: CORS policy configuration containing:
                - allowed_origins: List of allowed origins
                - allowed_methods: List of allowed HTTP methods
                - allowed_headers: List of allowed headers
                - expose_headers: Headers to expose
                - max_age: Preflight cache duration
                - allow_credentials: Allow credentials

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_validation_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply input validation policy to an API.

        Args:
            api_id: API identifier
            policy: Validation policy configuration containing:
                - schema_validation: Enable schema validation
                - content_type_validation: Validate content types
                - size_limits: Request/response size limits
                - sanitization_rules: Input sanitization rules

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_security_headers_policy(
        self, api_id: str, policy: dict[str, Any]
    ) -> bool:
        """Apply security headers policy to an API.

        Args:
            api_id: API identifier
            policy: Security headers configuration containing:
                - hsts: Strict-Transport-Security header
                - x_frame_options: X-Frame-Options header
                - x_content_type_options: X-Content-Type-Options header
                - csp: Content-Security-Policy header
                - x_xss_protection: X-XSS-Protection header

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def get_gateway_health(self) -> dict[str, Any]:
        """Get Gateway health status and metrics.

        Returns:
            dict: Gateway health information:
                - status: str (healthy, degraded, unhealthy)
                - uptime_seconds: int
                - total_apis: int
                - total_requests: int
                - error_rate: float
        """
        pass

    @abstractmethod
    async def get_capabilities(self) -> list[str]:
        """Get list of capabilities supported by this Gateway.

        Returns:
            list[str]: List of capability names (e.g., 'api_discovery', 'metrics_collection')
        """
        pass

    @property
    def is_connected(self) -> bool:
        """Check if adapter is connected to Gateway.

        Returns:
            bool: True if connected, False otherwise
        """
        return self._connected

    @property
    def vendor(self) -> str:
        """Get Gateway vendor name.

        Returns:
            str: Vendor name (e.g., 'native', 'kong', 'apigee')
        """
        return self.gateway.vendor.value

    def __repr__(self) -> str:
        """String representation of the adapter.

        Returns:
            str: Adapter description
        """
        return f"{self.__class__.__name__}(gateway={self.gateway.name}, vendor={self.vendor}, connected={self._connected})"

# Made with Bob
