"""
Vendor-neutral policy configuration models for API Intelligence Plane.

This module provides structured, type-safe configuration models for all policy types,
enabling better validation, documentation, and vendor-neutral policy management.

Design Principles:
1. Vendor-Neutral Core: Define common fields across all vendors
2. Type Safety: Use Pydantic models for validation
3. Extensibility: Support vendor-specific extensions via vendor_config
4. Backward Compatibility: Coexist with dict-based configs during migration
5. Progressive Enhancement: Allow gradual adoption

Usage:
    from backend.app.models.base.policy_configs import RateLimitConfig, AuthenticationConfig
    
    # Create type-safe rate limit config
    config = RateLimitConfig(
        requests_per_minute=1000,
        burst_allowance=100,
        rate_limit_key="api_key"
    )
"""

from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Rate Limiting Configuration
# ============================================================================

class RateLimitConfig(BaseModel):
    """Vendor-neutral rate limiting configuration."""
    
    # Time-based limits
    requests_per_second: Optional[int] = Field(
        None, ge=1, description="Maximum requests per second"
    )
    requests_per_minute: Optional[int] = Field(
        None, ge=1, description="Maximum requests per minute"
    )
    requests_per_hour: Optional[int] = Field(
        None, ge=1, description="Maximum requests per hour"
    )
    requests_per_day: Optional[int] = Field(
        None, ge=1, description="Maximum requests per day"
    )
    
    # Concurrent limits
    concurrent_requests: Optional[int] = Field(
        None, ge=1, description="Maximum concurrent requests"
    )
    
    # Burst handling
    burst_allowance: Optional[int] = Field(
        None, ge=0, description="Additional requests allowed in burst"
    )
    
    # Rate limit key
    rate_limit_key: Literal["ip", "user", "api_key", "custom"] = Field(
        "ip", description="Key to use for rate limiting"
    )
    custom_key_header: Optional[str] = Field(
        None, description="Custom header name if rate_limit_key is 'custom'"
    )
    
    # Enforcement
    enforcement_action: Literal["reject", "throttle", "queue"] = Field(
        "reject", description="Action when limit exceeded"
    )
    
    # Response headers
    include_rate_limit_headers: bool = Field(
        True, description="Include X-RateLimit-* headers in response"
    )
    
    # Consumer tiers (optional)
    consumer_tiers: Optional[dict[str, int]] = Field(
        None, description="Rate limits per consumer tier"
    )


# ============================================================================
# Authentication Configuration
# ============================================================================

class AuthenticationConfig(BaseModel):
    """Vendor-neutral authentication configuration."""
    
    # Authentication type
    auth_type: Literal["basic", "bearer", "oauth2", "api_key", "jwt", "mtls"] = Field(
        ..., description="Authentication mechanism"
    )
    
    # OAuth2 specific
    oauth_provider: Optional[str] = Field(
        None, description="OAuth2 provider (e.g., 'auth0', 'okta')"
    )
    oauth_scopes: Optional[list[str]] = Field(
        None, description="Required OAuth2 scopes"
    )
    oauth_token_endpoint: Optional[str] = Field(
        None, description="OAuth2 token validation endpoint"
    )
    
    # JWT specific
    jwt_issuer: Optional[str] = Field(
        None, description="Expected JWT issuer"
    )
    jwt_audience: Optional[str] = Field(
        None, description="Expected JWT audience"
    )
    jwt_public_key_url: Optional[str] = Field(
        None, description="URL to fetch JWT public key (JWKS)"
    )
    
    # API Key specific
    api_key_header: Optional[str] = Field(
        None, description="Header name for API key (default: 'X-API-Key')"
    )
    api_key_query_param: Optional[str] = Field(
        None, description="Query parameter name for API key"
    )
    
    # General settings
    allow_anonymous: bool = Field(
        False, description="Allow unauthenticated requests"
    )
    cache_credentials: bool = Field(
        True, description="Cache validated credentials"
    )
    cache_ttl_seconds: Optional[int] = Field(
        300, ge=0, description="Credential cache TTL"
    )


# ============================================================================
# Authorization Configuration
# ============================================================================

class AuthorizationConfig(BaseModel):
    """Vendor-neutral authorization configuration."""
    
    # User-based authorization
    allowed_users: Optional[list[str]] = Field(
        None, description="List of authorized usernames"
    )
    denied_users: Optional[list[str]] = Field(
        None, description="List of explicitly denied usernames"
    )
    
    # Group-based authorization
    allowed_groups: Optional[list[str]] = Field(
        None, description="List of authorized user groups"
    )
    denied_groups: Optional[list[str]] = Field(
        None, description="List of explicitly denied user groups"
    )
    
    # Role-based authorization
    allowed_roles: Optional[list[str]] = Field(
        None, description="List of authorized roles"
    )
    denied_roles: Optional[list[str]] = Field(
        None, description="List of explicitly denied roles"
    )
    
    # Access profiles (vendor-specific concept, but useful)
    allowed_access_profiles: Optional[list[str]] = Field(
        None, description="List of authorized access profiles"
    )
    
    # Permission-based authorization
    required_permissions: Optional[list[str]] = Field(
        None, description="List of required permissions (all must be present)"
    )
    any_permissions: Optional[list[str]] = Field(
        None, description="List of permissions (at least one must be present)"
    )
    
    # Scope-based authorization (OAuth2/JWT)
    required_scopes: Optional[list[str]] = Field(
        None, description="List of required OAuth2/JWT scopes (all must be present)"
    )
    any_scopes: Optional[list[str]] = Field(
        None, description="List of scopes (at least one must be present)"
    )
    
    # Claim-based authorization (JWT)
    required_claims: Optional[dict[str, Any]] = Field(
        None, description="Required JWT claims (key-value pairs that must match)"
    )
    
    # IP-based authorization
    allowed_ip_ranges: Optional[list[str]] = Field(
        None, description="List of allowed IP ranges (CIDR notation)"
    )
    denied_ip_ranges: Optional[list[str]] = Field(
        None, description="List of denied IP ranges (CIDR notation)"
    )
    
    # Time-based authorization
    allowed_time_windows: Optional[list[dict[str, str]]] = Field(
        None, description="List of allowed time windows (e.g., [{'start': '09:00', 'end': '17:00'}])"
    )
    timezone: Optional[str] = Field(
        None, description="Timezone for time-based authorization (e.g., 'America/New_York')"
    )
    
    # Authorization logic
    authorization_mode: Literal["all", "any", "custom"] = Field(
        "all", description="How to combine authorization rules (all=AND, any=OR)"
    )
    custom_authorization_expression: Optional[str] = Field(
        None, description="Custom authorization expression for complex logic"
    )
    
    # Error handling
    unauthorized_status_code: int = Field(
        403, ge=400, le=499, description="HTTP status code for unauthorized requests"
    )
    unauthorized_message: Optional[str] = Field(
        None, description="Custom error message for unauthorized requests"
    )


# ============================================================================
# Caching Configuration
# ============================================================================

class CachingConfig(BaseModel):
    """Vendor-neutral caching configuration."""
    
    # TTL settings
    ttl_seconds: int = Field(
        300, ge=0, description="Cache time-to-live in seconds"
    )
    max_ttl_seconds: Optional[int] = Field(
        None, ge=0, description="Maximum TTL regardless of headers"
    )
    
    # Cache key strategy
    cache_key_strategy: Literal["url", "url_query", "url_headers", "custom"] = Field(
        "url", description="Strategy for generating cache keys"
    )
    vary_headers: Optional[list[str]] = Field(
        None, description="Headers to include in cache key"
    )
    vary_query_params: Optional[list[str]] = Field(
        None, description="Query parameters to include in cache key"
    )
    
    # Cache control
    respect_cache_control_headers: bool = Field(
        True, description="Honor Cache-Control headers from backend"
    )
    cache_methods: list[str] = Field(
        ["GET", "HEAD"], description="HTTP methods to cache"
    )
    cache_status_codes: list[int] = Field(
        [200, 203, 204, 206, 300, 301], description="Status codes to cache"
    )
    
    # Size limits
    max_payload_size_bytes: Optional[int] = Field(
        None, ge=0, description="Maximum response size to cache"
    )
    
    # Invalidation
    invalidate_on_methods: Optional[list[str]] = Field(
        ["POST", "PUT", "PATCH", "DELETE"], 
        description="Methods that invalidate cache"
    )


# ============================================================================
# CORS Configuration
# ============================================================================

class CorsConfig(BaseModel):
    """Vendor-neutral CORS configuration."""
    
    allowed_origins: list[str] = Field(
        ..., description="Allowed origins (use '*' for all)"
    )
    allowed_methods: list[str] = Field(
        ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    allowed_headers: list[str] = Field(
        ["*"], description="Allowed request headers"
    )
    exposed_headers: Optional[list[str]] = Field(
        None, description="Headers exposed to browser"
    )
    allow_credentials: bool = Field(
        False, description="Allow credentials (cookies, auth headers)"
    )
    max_age_seconds: Optional[int] = Field(
        3600, ge=0, description="Preflight cache duration"
    )


# ============================================================================
# Validation Configuration
# ============================================================================

class ValidationConfig(BaseModel):
    """Vendor-neutral request/response validation configuration."""
    
    # Schema validation
    validate_request_schema: bool = Field(
        True, description="Validate request against OpenAPI schema"
    )
    validate_response_schema: bool = Field(
        False, description="Validate response against OpenAPI schema"
    )
    
    # Parameter validation
    validate_query_params: bool = Field(
        True, description="Validate query parameters"
    )
    validate_path_params: bool = Field(
        True, description="Validate path parameters"
    )
    validate_headers: bool = Field(
        True, description="Validate request headers"
    )
    
    # Content validation
    validate_content_type: bool = Field(
        True, description="Validate Content-Type header"
    )
    allowed_content_types: Optional[list[str]] = Field(
        None, description="Allowed Content-Type values"
    )
    
    # Error handling
    strict_mode: bool = Field(
        False, description="Reject requests with unknown fields"
    )
    return_validation_errors: bool = Field(
        True, description="Include validation errors in response"
    )


# ============================================================================
# Data Masking Configuration
# ============================================================================

class MaskingRule(BaseModel):
    """Individual masking rule."""
    
    field_path: str = Field(
        ..., description="JSONPath or XPath to field"
    )
    mask_type: Literal["full", "partial", "hash", "remove"] = Field(
        "full", description="Type of masking to apply"
    )
    mask_character: str = Field(
        "*", description="Character to use for masking"
    )
    preserve_length: bool = Field(
        True, description="Preserve original field length"
    )
    partial_mask_start: Optional[int] = Field(
        None, description="Characters to show at start (partial mask)"
    )
    partial_mask_end: Optional[int] = Field(
        None, description="Characters to show at end (partial mask)"
    )


class DataMaskingConfig(BaseModel):
    """Vendor-neutral data masking configuration."""
    
    mask_request: bool = Field(
        False, description="Mask request data"
    )
    mask_response: bool = Field(
        True, description="Mask response data"
    )
    mask_logs: bool = Field(
        True, description="Apply masking to logs"
    )
    
    masking_rules: list[MaskingRule] = Field(
        ..., description="List of masking rules"
    )


# ============================================================================
# Transformation Configuration
# ============================================================================

class TransformationConfig(BaseModel):
    """Vendor-neutral request/response transformation configuration."""
    
    transform_request: bool = Field(
        False, description="Transform request"
    )
    transform_response: bool = Field(
        False, description="Transform response"
    )
    
    # Header transformations
    add_headers: Optional[dict[str, str]] = Field(
        None, description="Headers to add"
    )
    remove_headers: Optional[list[str]] = Field(
        None, description="Headers to remove"
    )
    rename_headers: Optional[dict[str, str]] = Field(
        None, description="Headers to rename (old: new)"
    )
    
    # Body transformations
    transformation_template: Optional[str] = Field(
        None, description="Template for body transformation (e.g., Jinja2)"
    )
    transformation_language: Optional[Literal["jinja2", "jsonata", "xslt"]] = Field(
        None, description="Transformation language"
    )


# ============================================================================
# Logging Configuration
# ============================================================================

class LoggingConfig(BaseModel):
    """Vendor-neutral logging configuration."""
    
    log_level: Literal["none", "error", "info", "debug"] = Field(
        "info", description="Logging level"
    )
    
    # What to log
    log_request_headers: bool = Field(True)
    log_request_body: bool = Field(False)
    log_response_headers: bool = Field(True)
    log_response_body: bool = Field(False)
    
    # Sampling
    sampling_rate: float = Field(
        1.0, ge=0.0, le=1.0, description="Fraction of requests to log (0.0-1.0)"
    )
    
    # Destinations
    log_to_gateway: bool = Field(True, description="Log to gateway logs")
    log_to_external: bool = Field(False, description="Log to external system")
    external_log_endpoint: Optional[str] = Field(
        None, description="External logging endpoint URL"
    )
    
    # Compression
    compress_logs: bool = Field(
        False, description="Compress log payloads"
    )


# ============================================================================
# TLS Configuration
# ============================================================================

class TlsConfig(BaseModel):
    """Vendor-neutral TLS configuration."""
    
    enforce_tls: bool = Field(
        True, description="Require TLS for all connections"
    )
    min_tls_version: Literal["1.0", "1.1", "1.2", "1.3"] = Field(
        "1.2", description="Minimum TLS version"
    )
    allowed_cipher_suites: Optional[list[str]] = Field(
        None, description="Allowed TLS cipher suites"
    )
    
    # Client certificates
    require_client_certificate: bool = Field(
        False, description="Require client certificate (mTLS)"
    )
    trusted_ca_certificates: Optional[list[str]] = Field(
        None, description="Trusted CA certificate paths"
    )
    
    # Backend TLS
    verify_backend_certificate: bool = Field(
        True, description="Verify backend server certificate"
    )


# ============================================================================
# Compression Configuration
# ============================================================================

class CompressionConfig(BaseModel):
    """Vendor-neutral compression configuration."""
    
    enabled: bool = Field(True, description="Enable compression")
    algorithms: list[Literal["gzip", "deflate", "br", "zstd"]] = Field(
        ["gzip", "br"], description="Supported compression algorithms"
    )
    min_size_bytes: int = Field(
        1024, ge=0, description="Minimum response size to compress"
    )
    compression_level: int = Field(
        6, ge=1, le=9, description="Compression level (1-9)"
    )
    content_types: list[str] = Field(
        ["text/*", "application/json", "application/xml"],
        description="Content types to compress"
    )


# ============================================================================
# Union Type for All Configurations
# ============================================================================

# Type alias for all policy configurations
PolicyConfigType = (
    RateLimitConfig |
    AuthenticationConfig |
    AuthorizationConfig |
    CachingConfig |
    CorsConfig |
    ValidationConfig |
    DataMaskingConfig |
    TransformationConfig |
    LoggingConfig |
    TlsConfig |
    CompressionConfig
)


# Export all config types
__all__ = [
    "RateLimitConfig",
    "AuthenticationConfig",
    "AuthorizationConfig",
    "CachingConfig",
    "CorsConfig",
    "ValidationConfig",
    "DataMaskingConfig",
    "MaskingRule",
    "TransformationConfig",
    "LoggingConfig",
    "TlsConfig",
    "CompressionConfig",
    "PolicyConfigType",
]

# Made with Bob
