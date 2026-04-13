"""Test fixtures for vendor-neutral API models.

Provides reusable test data for API-related tests with the new vendor-neutral structure.
"""

from datetime import datetime
from typing import Optional
from uuid import UUID, uuid4

from app.models.base.api import (
    API,
    APIDefinition,
    APIStatus,
    APIType,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    EndpointParameter,
    IntelligenceMetadata,
    MaturityState,
    PolicyAction,
    PolicyActionType,
    VersionInfo,
)


def create_sample_api(
    api_id: Optional[UUID] = None,
    gateway_id: Optional[UUID] = None,
    name: str = "Test API",
    version: str = "1.0.0",
    status: APIStatus = APIStatus.ACTIVE,
    is_shadow: bool = False,
    **kwargs
) -> API:
    """Create a sample vendor-neutral API fixture.
    
    Args:
        api_id: API ID (generates random if None)
        gateway_id: Gateway ID (generates random if None)
        name: API name
        version: API version
        status: API status
        is_shadow: Whether this is a shadow API
        **kwargs: Additional fields to override
        
    Returns:
        Sample API instance with vendor-neutral structure
    """
    now = datetime.utcnow()
    
    defaults = {
        "id": api_id or uuid4(),
        "gateway_id": gateway_id or uuid4(),
        "name": name,
        "display_name": f"{name} Display",
        "description": f"Test API for {name}",
        "base_path": f"/api/{version}",
        "version_info": VersionInfo(
            current_version=version,
            previous_version=None,
            next_version=None,
            system_version=1,
            version_history=None,
        ),
        "type": APIType.REST,
        "maturity_state": MaturityState.PRODUCTIVE,
        "endpoints": [
            Endpoint(
                path="/test",
                method="GET",
                description="Test endpoint",
                parameters=[
                    EndpointParameter(
                        name="id",
                        type="query",
                        data_type="string",
                        required=False,
                        description="Optional ID parameter",
                    )
                ],
                response_codes=[200, 400, 500],
                connection_timeout=None,
                read_timeout=None,
            ),
            Endpoint(
                path="/test/{id}",
                method="GET",
                description="Get test by ID",
                parameters=[
                    EndpointParameter(
                        name="id",
                        type="path",
                        data_type="string",
                        required=True,
                        description="Test ID",
                    )
                ],
                response_codes=[200, 404, 500],
                connection_timeout=None,
                read_timeout=None,
            ),
        ],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "authentication_type": AuthenticationType.BEARER,
        "authentication_config": {"scheme": "bearer", "format": "JWT"},
        "policy_actions": [
            PolicyAction(
                action_type=PolicyActionType.AUTHENTICATION,
                enabled=True,
                stage="request",
                name="Authentication Policy",
                description="Bearer token authentication",
                config={"scheme": "bearer"},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.RATE_LIMITING,
                enabled=True,
                stage="request",
                name="Rate Limiting Policy",
                description="Request rate limiting",
                config={"requests_per_minute": 1000},
                vendor_config={},
            ),
        ],
        "tags": ["test", "api"],
        "intelligence_metadata": IntelligenceMetadata(
            is_shadow=is_shadow,
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=now,
            last_seen_at=now,
            health_score=95.0,
            risk_score=5.0,
            security_score=90.0,
            compliance_status=None,
            usage_trend=None,
            has_active_predictions=False,
        ),
        "status": status,
        "is_active": status == APIStatus.ACTIVE,
        "vendor_metadata": {"vendor": "test", "environment": "test"},
        "created_at": now,
        "updated_at": now,
    }
    
    defaults.update(kwargs)
    return API(**defaults)


def create_shadow_api(
    api_id: Optional[UUID] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> API:
    """Create a shadow API fixture (discovered via traffic analysis)."""
    return create_sample_api(
        api_id=api_id,
        gateway_id=gateway_id,
        name="Shadow API",
        is_shadow=True,
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=True,
            discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            health_score=70.0,
            risk_score=60.0,
            security_score=40.0,
            compliance_status={"PCI-DSS": False, "GDPR": False},
            usage_trend="increasing",
            has_active_predictions=True,
        ),
        **kwargs
    )


def create_api_with_security_policies(
    api_id: Optional[UUID] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> API:
    """Create an API with comprehensive security policies."""
    return create_sample_api(
        api_id=api_id,
        gateway_id=gateway_id,
        name="Secure API",
        policy_actions=[
            PolicyAction(
                action_type=PolicyActionType.AUTHENTICATION,
                enabled=True,
                stage="request",
                name="Authentication",
                description="Bearer authentication",
                config={"scheme": "bearer"},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.AUTHORIZATION,
                enabled=True,
                stage="request",
                name="Authorization",
                description="Role-based authorization",
                config={"roles": ["admin", "user"]},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.TLS,
                enabled=True,
                stage="transport",
                name="TLS Enforcement",
                description="TLS 1.2+ enforcement",
                config={"min_version": "1.2"},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.CORS,
                enabled=True,
                stage="response",
                name="CORS Policy",
                description="Cross-origin resource sharing",
                config={"allowed_origins": ["https://example.com"]},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.VALIDATION,
                enabled=True,
                stage="request",
                name="Request Validation",
                description="OpenAPI schema validation",
                config={"schema": "openapi"},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.DATA_MASKING,
                enabled=True,
                stage="response",
                name="Data Masking",
                description="Sensitive data masking",
                config={"fields": ["ssn", "credit_card"]},
                vendor_config={},
            ),
        ],
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=False,
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            health_score=98.0,
            risk_score=2.0,
            security_score=98.0,
            compliance_status={"PCI-DSS": True, "GDPR": True, "HIPAA": True},
            usage_trend="stable",
            has_active_predictions=False,
        ),
        **kwargs
    )


def create_api_with_performance_policies(
    api_id: Optional[UUID] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> API:
    """Create an API with performance optimization policies."""
    return create_sample_api(
        api_id=api_id,
        gateway_id=gateway_id,
        name="Optimized API",
        policy_actions=[
            PolicyAction(
                action_type=PolicyActionType.CACHING,
                enabled=True,
                stage="response",
                name="Response Caching",
                description="Cache responses for 5 minutes",
                config={"ttl": 300, "cache_key": "url"},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.COMPRESSION,
                enabled=True,
                stage="response",
                name="Response Compression",
                description="GZIP compression for responses",
                config={"algorithm": "gzip", "min_size": 1024},
                vendor_config={},
            ),
            PolicyAction(
                action_type=PolicyActionType.RATE_LIMITING,
                enabled=True,
                stage="request",
                name="Rate Limiting",
                description="Limit requests per minute",
                config={"requests_per_minute": 5000, "burst": 100},
                vendor_config={},
            ),
        ],
        **kwargs
    )


def create_deprecated_api(
    api_id: Optional[UUID] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> API:
    """Create a deprecated API fixture."""
    return create_sample_api(
        api_id=api_id,
        gateway_id=gateway_id,
        name="Deprecated API",
        status=APIStatus.DEPRECATED,
        maturity_state=MaturityState.DEPRECATED,
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=False,
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            health_score=60.0,
            risk_score=40.0,
            security_score=70.0,
            compliance_status=None,
            usage_trend="decreasing",
            has_active_predictions=True,
        ),
        **kwargs
    )


def create_api_with_definition(
    api_id: Optional[UUID] = None,
    gateway_id: Optional[UUID] = None,
    **kwargs
) -> API:
    """Create an API with OpenAPI definition."""
    api_definition = APIDefinition(
        type="REST",
        version="3.0.0",
        openapi_spec={
            "openapi": "3.0.0",
            "info": {
                "title": "Test API",
                "description": "Test API with OpenAPI definition",
                "version": "1.0.0",
            },
            "paths": {
                "/test": {
                    "get": {
                        "summary": "Get test data",
                        "responses": {
                            "200": {"description": "Success"},
                            "500": {"description": "Error"},
                        }
                    }
                }
            },
        },
        swagger_version=None,
        base_path="/api/v1",
        paths={
            "/test": {
                "get": {
                    "summary": "Get test data",
                    "responses": {
                        "200": {"description": "Success"},
                        "500": {"description": "Error"},
                    }
                }
            }
        },
        schemas={},
        security_schemes={
            "bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
            }
        },
        vendor_extensions={},
    )
    
    return create_sample_api(
        api_id=api_id,
        gateway_id=gateway_id,
        name="API with Definition",
        api_definition=api_definition,
        **kwargs
    )


# Made with Bob