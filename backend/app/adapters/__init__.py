"""Adapters package for API Intelligence Plane.

This package exposes the active gateway adapter surface for the current
implementation phase.

The architecture remains vendor-neutral at the model and service layers, but
the currently supported runtime adapter is webMethods only. Deferred adapters
are intentionally not exported from this package surface.
"""

from app.adapters.base import BaseGatewayAdapter
from app.adapters.factory import (
    GatewayAdapterFactory,
    create_gateway_adapter,
)
from app.adapters.webmethods_gateway import WebMethodsGatewayAdapter

__all__ = [
    "BaseGatewayAdapter",
    "WebMethodsGatewayAdapter",
    "GatewayAdapterFactory",
    "create_gateway_adapter",
]

# Made with Bob
