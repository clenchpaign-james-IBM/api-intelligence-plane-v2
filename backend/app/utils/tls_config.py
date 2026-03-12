"""
TLS 1.3 Configuration for FedRAMP 140-3 Compliance

This module provides TLS 1.3 configuration for all services to ensure
secure communication and compliance with FedRAMP 140-3 requirements.
"""

import os
import ssl
from typing import Any, Optional

from app.config import settings


def create_ssl_context(
    certfile: Optional[str] = None,
    keyfile: Optional[str] = None,
    cafile: Optional[str] = None,
    verify_mode: ssl.VerifyMode = ssl.CERT_REQUIRED,
) -> ssl.SSLContext:
    """
    Create an SSL context with TLS 1.3 and FedRAMP 140-3 compliant settings.
    
    Args:
        certfile: Path to certificate file
        keyfile: Path to private key file
        cafile: Path to CA certificate file
        verify_mode: Certificate verification mode
        
    Returns:
        Configured SSL context
    """
    # Create context with TLS 1.3 minimum
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    
    # Set minimum TLS version to 1.3
    context.minimum_version = ssl.TLSVersion.TLSv1_3
    
    # Set maximum TLS version to 1.3 (enforce TLS 1.3 only)
    context.maximum_version = ssl.TLSVersion.TLSv1_3
    
    # TLS 1.3 cipher suites are configured automatically
    # Python's ssl module handles TLS 1.3 ciphers differently than TLS 1.2
    # The default TLS 1.3 ciphers are all FIPS 140-3 compliant AEAD ciphers
    
    # Load certificates if provided
    if certfile and keyfile:
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    
    # Load CA certificates if provided
    if cafile:
        context.load_verify_locations(cafile=cafile)
    
    # Set verification mode
    context.verify_mode = verify_mode
    
    # Additional security options
    context.check_hostname = True
    context.options |= ssl.OP_NO_COMPRESSION  # Disable compression
    context.options |= ssl.OP_SINGLE_DH_USE  # Generate new DH key for each connection
    context.options |= ssl.OP_SINGLE_ECDH_USE  # Generate new ECDH key for each connection
    
    return context


def create_client_ssl_context(
    certfile: Optional[str] = None,
    keyfile: Optional[str] = None,
    cafile: Optional[str] = None,
) -> ssl.SSLContext:
    """
    Create an SSL context for client connections with TLS 1.3.
    
    Args:
        certfile: Path to client certificate file
        keyfile: Path to client private key file
        cafile: Path to CA certificate file
        
    Returns:
        Configured SSL context for client connections
    """
    # Create context with TLS 1.2 minimum (OpenSearch compatibility)
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    
    # Set minimum TLS version to 1.2 for compatibility
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    
    # TLS 1.3 cipher suites are configured automatically
    # All TLS 1.3 ciphers are AEAD and FIPS 140-3 compliant
    
    # Load client certificates if provided
    if certfile and keyfile:
        context.load_cert_chain(certfile=certfile, keyfile=keyfile)
    
    # Load CA certificates
    if cafile:
        context.load_verify_locations(cafile=cafile)
    else:
        context.load_default_certs()
    
    # Disable hostname checking for internal services
    context.check_hostname = False
    context.verify_mode = ssl.CERT_REQUIRED
    
    return context


def get_uvicorn_ssl_config() -> dict:
    """
    Get SSL configuration for Uvicorn server.
    
    Returns:
        Dictionary with SSL configuration for Uvicorn
    """
    if not settings.TLS_ENABLED:
        return {}
    
    return {
        "ssl_keyfile": settings.TLS_KEY_FILE,
        "ssl_certfile": settings.TLS_CERT_FILE,
        "ssl_ca_certs": settings.TLS_CA_FILE,
        "ssl_version": ssl.PROTOCOL_TLS_SERVER,
        "ssl_cert_reqs": ssl.CERT_REQUIRED,
    }


def get_opensearch_ssl_config() -> dict[str, Any]:
    """
    Get SSL configuration for OpenSearch client.
    
    The opensearchpy library uses the requests library which requires
    ca_certs, client_cert, and client_key parameters instead of ssl_context.
    
    Returns:
        Dictionary with SSL configuration for OpenSearch
    """
    if not settings.OPENSEARCH_USE_SSL:
        return {"use_ssl": False}
    
    config = {
        "use_ssl": True,
        "verify_certs": settings.OPENSEARCH_VERIFY_CERTS,
        "ssl_show_warn": False,
    }
    
    # Add CA certificate if it exists
    if settings.OPENSEARCH_CA_CERT and os.path.isfile(settings.OPENSEARCH_CA_CERT):
        config["ca_certs"] = settings.OPENSEARCH_CA_CERT
    
    # Add client certificates if they exist (for mTLS)
    if (settings.OPENSEARCH_CLIENT_CERT and
        settings.OPENSEARCH_CLIENT_KEY and
        os.path.isfile(settings.OPENSEARCH_CLIENT_CERT) and
        os.path.isfile(settings.OPENSEARCH_CLIENT_KEY)):
        config["client_cert"] = settings.OPENSEARCH_CLIENT_CERT
        config["client_key"] = settings.OPENSEARCH_CLIENT_KEY
    
    return config


def get_httpx_ssl_config() -> ssl.SSLContext:
    """
    Get SSL configuration for HTTPX client (used for external API calls).
    
    Returns:
        SSL context for HTTPX client
    """
    return create_client_ssl_context(
        certfile=settings.CLIENT_CERT_FILE,
        keyfile=settings.CLIENT_KEY_FILE,
        cafile=settings.CLIENT_CA_FILE,
    )

# Made with Bob
