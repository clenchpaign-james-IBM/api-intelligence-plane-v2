"""Adapters package for API Intelligence Plane.

This package contains Gateway adapters implementing the Strategy pattern
for multi-vendor Gateway support.
"""

from backend.app.adapters.apigee_gateway import ApigeeGatewayAdapter
from backend.app.adapters.base import BaseGatewayAdapter
from backend.app.adapters.factory import (
    GatewayAdapterFactory,
    create_gateway_adapter,
)
from backend.app.adapters.kong_gateway import KongGatewayAdapter
from backend.app.adapters.native_gateway import NativeGatewayAdapter

__all__ = [
    "BaseGatewayAdapter",
    "NativeGatewayAdapter",
    "KongGatewayAdapter",
    "ApigeeGatewayAdapter",
    "GatewayAdapterFactory",
    "create_gateway_adapter",
]

# Made with Bob
