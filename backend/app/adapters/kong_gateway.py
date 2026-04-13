"""Kong Gateway adapter stub for API Intelligence Plane.

Placeholder implementation for Kong Gateway support.
This will be fully implemented in a future phase.
"""

import logging
from typing import Any, Optional

from app.adapters.base import BaseGatewayAdapter
from app.models.base.api import API, PolicyAction
from app.models.base.metric import Metric

logger = logging.getLogger(__name__)


class KongGatewayAdapter(BaseGatewayAdapter):
    """Kong Gateway adapter (placeholder for future implementation).

    This adapter will communicate with Kong Gateway via its Admin API
    to discover APIs, collect metrics, and manage policies.

    Kong Gateway Documentation: https://docs.konghq.com/gateway/latest/admin-api/
    """

    async def connect(self) -> bool:
        """Establish connection to Kong Gateway.

        Returns:
            bool: True if connection successful

        Raises:
            NotImplementedError: Kong adapter not yet implemented
        """
        logger.warning("Kong Gateway adapter not yet implemented")
        raise NotImplementedError(
            "Kong Gateway adapter is not yet implemented. "
            "Please use Native Gateway or implement Kong support."
        )

    async def disconnect(self) -> None:
        """Close connection to Kong Gateway."""
        pass

    async def test_connection(self) -> dict[str, Any]:
        """Test Kong Gateway connection.

        Returns:
            dict: Connection status
        """
        return {
            "connected": False,
            "latency_ms": 0,
            "version": "unknown",
            "error": "Kong Gateway adapter not yet implemented",
        }

    async def discover_apis(self) -> list[API]:
        """Discover APIs from Kong Gateway.

        Returns:
            list[API]: Empty list (not implemented)
        """
        logger.warning("Kong Gateway API discovery not yet implemented")
        return []

    async def get_api_details(self, api_id: str) -> Optional[API]:
        """Get API details from Kong Gateway.

        Args:
            api_id: API identifier

        Returns:
            None: Not implemented
        """
        return None

    async def apply_rate_limit_policy(
        self, api_id: str, policy: PolicyAction
    ) -> bool:
        """Apply a vendor-neutral rate limit policy in Kong Gateway.

        Args:
            api_id: API identifier
            policy: Vendor-neutral policy action model

        Returns:
            bool: False (not implemented)
        """
        logger.warning("Kong Gateway rate limiting not yet implemented")
        return False

    async def remove_rate_limit_policy(self, api_id: str) -> bool:
        """Remove rate limit policy from Kong Gateway.

        Args:
            api_id: API identifier

        Returns:
            bool: False (not implemented)
        """
        return False

    async def get_gateway_health(self) -> dict[str, Any]:
        """Get Kong Gateway health status.

        Returns:
            dict: Health information (placeholder)
        """
        return {
            "status": "unknown",
            "uptime_seconds": 0,
            "total_apis": 0,
            "total_requests": 0,
            "error_rate": 0.0,
        }

    async def get_capabilities(self) -> list[str]:
        """Get Kong Gateway capabilities.

        Returns:
            list[str]: Empty list (not implemented)
        """
        return []

# Made with Bob
