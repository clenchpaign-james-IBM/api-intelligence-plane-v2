"""Backward compatibility shim for API model imports.

This module provides backward compatibility for code that imports from
backend.app.models.api instead of backend.app.models.base.api.
"""

# Re-export everything from base.api for backward compatibility
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
    MaturityState,
    OwnershipInfo,
    PolicyAction,
    PolicyActionType,
    PublishingInfo,
    VersionInfo,
)

__all__ = [
    "API",
    "APIDefinition",
    "APIStatus",
    "APIType",
    "AuthenticationType",
    "DeploymentInfo",
    "DiscoveryMethod",
    "Endpoint",
    "EndpointParameter",
    "IntelligenceMetadata",
    "MaturityState",
    "OwnershipInfo",
    "PolicyAction",
    "PolicyActionType",
    "PublishingInfo",
    "VersionInfo",
]

# Made with Bob
