"""Gateway adapter factory for API Intelligence Plane.

Factory pattern implementation for creating appropriate Gateway adapters
based on vendor type.
"""

import logging
from typing import Type

from app.adapters.base import BaseGatewayAdapter
from app.adapters.native_gateway import NativeGatewayAdapter
from app.models.gateway import Gateway, GatewayVendor

logger = logging.getLogger(__name__)


class GatewayAdapterFactory:
    """Factory for creating Gateway adapters based on vendor type.

    This factory implements the Factory pattern to instantiate the appropriate
    Gateway adapter based on the Gateway vendor configuration.
    """

    # Registry of adapter classes by vendor
    _adapters: dict[GatewayVendor, Type[BaseGatewayAdapter]] = {
        GatewayVendor.NATIVE: NativeGatewayAdapter,
        # Additional adapters will be registered here as they are implemented
        # GatewayVendor.KONG: KongGatewayAdapter,
        # GatewayVendor.APIGEE: ApigeeGatewayAdapter,
        # GatewayVendor.AWS: AWSGatewayAdapter,
        # GatewayVendor.AZURE: AzureGatewayAdapter,
        # GatewayVendor.CUSTOM: CustomGatewayAdapter,
    }

    @classmethod
    def create_adapter(cls, gateway: Gateway) -> BaseGatewayAdapter:
        """Create a Gateway adapter for the specified Gateway configuration.

        Args:
            gateway: Gateway configuration containing vendor and connection details

        Returns:
            BaseGatewayAdapter: Instantiated adapter for the Gateway vendor

        Raises:
            ValueError: If vendor is not supported
        """
        adapter_class = cls._adapters.get(gateway.vendor)

        if adapter_class is None:
            supported_vendors = ", ".join([v.value for v in cls._adapters.keys()])
            raise ValueError(
                f"Unsupported Gateway vendor: {gateway.vendor.value}. "
                f"Supported vendors: {supported_vendors}"
            )

        logger.info(
            f"Creating {adapter_class.__name__} for Gateway: {gateway.name} ({gateway.vendor.value})"
        )
        return adapter_class(gateway)

    @classmethod
    def register_adapter(
        cls, vendor: GatewayVendor, adapter_class: Type[BaseGatewayAdapter]
    ) -> None:
        """Register a new Gateway adapter for a vendor.

        This allows dynamic registration of adapters at runtime, useful for
        plugins or custom Gateway implementations.

        Args:
            vendor: Gateway vendor type
            adapter_class: Adapter class to register

        Raises:
            TypeError: If adapter_class is not a subclass of BaseGatewayAdapter
        """
        if not issubclass(adapter_class, BaseGatewayAdapter):
            raise TypeError(
                f"Adapter class must be a subclass of BaseGatewayAdapter, got {adapter_class}"
            )

        cls._adapters[vendor] = adapter_class
        logger.info(
            f"Registered {adapter_class.__name__} for vendor: {vendor.value}"
        )

    @classmethod
    def get_supported_vendors(cls) -> list[str]:
        """Get list of supported Gateway vendors.

        Returns:
            list[str]: List of supported vendor names
        """
        return [vendor.value for vendor in cls._adapters.keys()]

    @classmethod
    def is_vendor_supported(cls, vendor: GatewayVendor) -> bool:
        """Check if a Gateway vendor is supported.

        Args:
            vendor: Gateway vendor to check

        Returns:
            bool: True if vendor is supported, False otherwise
        """
        return vendor in cls._adapters


# Convenience function for creating adapters
def create_gateway_adapter(gateway: Gateway) -> BaseGatewayAdapter:
    """Create a Gateway adapter for the specified Gateway configuration.

    This is a convenience function that delegates to GatewayAdapterFactory.

    Args:
        gateway: Gateway configuration

    Returns:
        BaseGatewayAdapter: Instantiated adapter

    Raises:
        ValueError: If vendor is not supported
    """
    return GatewayAdapterFactory.create_adapter(gateway)

# Made with Bob
