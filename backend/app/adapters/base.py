"""Base Gateway adapter interface for API Intelligence Plane.

Defines the abstract interface that all Gateway adapters must implement,
following the Strategy pattern for multi-vendor Gateway support.
"""

from abc import ABC, abstractmethod
from typing import Any, List, Optional

from app.models.base.api import API, PolicyAction
from app.models.gateway import Gateway
from app.models.base.metric import Metric
from app.models.base.transaction import TransactionalLog


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
    async def get_transactional_logs(
        self,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
    ) -> list[TransactionalLog]:
        """Retrieve raw transactional log events from the Gateway (low-level method).

        This is the low-level method with full control over time ranges.
        For convenience, use [`collect_transactional_logs()`](backend/app/adapters/base.py:356)
        which wraps this method with simplified parameters.

        Args:
            start_time: Optional lower timestamp bound
            end_time: Optional upper timestamp bound

        Returns:
            list[TransactionalLog]: Raw transactional events for analytics and drill-down
        """
        pass

    @abstractmethod
    async def apply_rate_limit_policy(
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral rate limiting policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.
                Adapter implementations must translate [`PolicyAction`](backend/app/models/base/api.py:157)
                to the target vendor format via [`_transform_from_policy_action()`](backend/app/adapters/base.py:499).

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
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral caching policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.
                Common cache settings should live in `config`; vendor-specific settings
                must remain in `vendor_config` and be translated by the adapter.

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
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral compression policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.

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
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral authentication policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_authorization_policy(
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral authorization policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_tls_policy(
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral TLS policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_cors_policy(
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral CORS policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_validation_policy(
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral validation policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.

        Returns:
            bool: True if policy applied successfully, False otherwise
        """
        pass

    @abstractmethod
    async def apply_security_headers_policy(
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral security headers policy to an API.

        Args:
            api_id: API identifier
            policy: Vendor-neutral [`PolicyAction`](backend/app/models/base/api.py:157) model.

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

    # ========================================================================
    # Transformation Methods (Added in Phase 0.5)
    # ========================================================================

    @abstractmethod
    def _transform_to_api(self, vendor_data: Any) -> API:
        """Transform vendor-specific API data to vendor-neutral API model.

        This method must:
        1. Map vendor-specific fields to standard API fields
        2. Transform vendor policies to PolicyAction array
        3. Populate vendor_metadata with vendor-specific fields
        4. Populate intelligence_metadata with discovery information

        Args:
            vendor_data: Vendor-specific API data structure

        Returns:
            API: Vendor-neutral API model

        Note:
            - Store vendor-specific fields in vendor_metadata dict
            - Use PolicyActionType enum for policy_actions
            - Populate intelligence_metadata.discovery_method
        """
        pass

    @abstractmethod
    def _transform_to_metric(self, vendor_data: Any) -> Metric:
        """Transform vendor-specific metric data to vendor-neutral Metric model.

        This method must:
        1. Map vendor-specific metric fields to standard Metric fields
        2. Calculate percentiles if not provided
        3. Populate vendor_metadata with vendor-specific metrics

        Args:
            vendor_data: Vendor-specific metric data structure

        Returns:
            Metric: Vendor-neutral Metric model

        Note:
            - Store vendor-specific metrics in vendor_metadata dict
            - Ensure time_bucket is set appropriately
        """
        pass

    @abstractmethod
    def _transform_to_transactional_log(self, vendor_data: Any) -> TransactionalLog:
        """Transform vendor-specific log data to vendor-neutral TransactionalLog model.

        This method must:
        1. Map vendor-specific log fields to standard TransactionalLog fields
        2. Extract timing breakdown (gateway, backend, total)
        3. Extract error information
        4. Populate vendor_metadata with vendor-specific log data

        Args:
            vendor_data: Vendor-specific log data structure

        Returns:
            TransactionalLog: Vendor-neutral TransactionalLog model

        Note:
            - Store vendor-specific log fields in vendor_metadata dict
            - Ensure all timing fields are in milliseconds
        """
        pass

    @abstractmethod
    def _transform_to_policy_action(self, vendor_data: Any) -> PolicyAction:
        """Transform vendor-specific policy to vendor-neutral PolicyAction model.

        This method must:
        1. Map vendor policy type to PolicyActionType enum
        2. Extract policy configuration to vendor_config dict
        3. Set enabled status

        Args:
            vendor_data: Vendor-specific policy data structure

        Returns:
            PolicyAction: Vendor-neutral PolicyAction model

        Note:
            - Use PolicyActionType enum for action_type
            - Store vendor-specific config in vendor_config dict
        """
        pass

    @abstractmethod
    def _transform_from_policy_action(self, policy_action: PolicyAction) -> Any:
        """Transform vendor-neutral PolicyAction to vendor-specific policy format.

        This method must:
        1. Map PolicyActionType enum to vendor policy type
        2. Extract vendor_config dict to vendor policy structure
        3. Format for vendor API requests

        Args:
            policy_action: Vendor-neutral PolicyAction model

        Returns:
            Any: Vendor-specific policy data structure ready for API submission

        Note:
            - Extract vendor_config dict for vendor-specific parameters
            - Format according to vendor API requirements
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
