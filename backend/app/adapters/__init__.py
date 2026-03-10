"""Adapters package for API Intelligence Plane.

This package contains Gateway adapters implementing the Strategy pattern
for multi-vendor Gateway support.
"""

from app.adapters.apigee_gateway import ApigeeGatewayAdapter
from app.adapters.base import BaseGatewayAdapter
from app.adapters.factory import (
    GatewayAdapterFactory,
    create_gateway_adapter,
)
from app.adapters.kong_gateway import KongGatewayAdapter
from app.adapters.native_gateway import NativeGatewayAdapter

__all__ = [
    "BaseGatewayAdapter",
    "NativeGatewayAdapter",
    "KongGatewayAdapter",
    "ApigeeGatewayAdapter",
    "GatewayAdapterFactory",
    "create_gateway_adapter",
]

# Made with Bob
