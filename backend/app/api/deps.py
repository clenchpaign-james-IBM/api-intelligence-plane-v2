"""
Dependency Injection

FastAPI dependencies for request handling including:
- OpenSearch client injection
- Service layer injection
- Authentication (future)
- Rate limiting (future)
"""

import logging
from typing import Generator
from fastapi import Depends
from opensearchpy import OpenSearch

from app.db.client import get_client, get_opensearch_client, OpenSearchClient
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.services.security_service import SecurityService
from app.services.compliance_service import ComplianceService
from app.services.llm_service import LLMService
from app.config import settings

logger = logging.getLogger(__name__)


def get_db() -> Generator[OpenSearch, None, None]:
    """
    Dependency to get OpenSearch client for database operations.
    
    Yields:
        OpenSearch client instance
        
    Example:
        @app.get("/items")
        async def get_items(db: OpenSearch = Depends(get_db)):
            # Use db client
            pass
    """
    try:
        client = get_client()
        yield client
    except Exception as e:
        logger.error(f"Failed to get database client: {e}")
        raise
    finally:
        # Cleanup if needed (client is singleton, so no cleanup required)
        pass


def get_opensearch() -> OpenSearchClient:
    """
    Dependency to get OpenSearch client wrapper.
    
    Returns:
        OpenSearchClient wrapper instance
        
    Example:
        @app.get("/health")
        async def health_check(os_client: OpenSearchClient = Depends(get_opensearch)):
            return os_client.health_check()
    """
    return get_opensearch_client()


def get_security_service() -> SecurityService:
    """
    Dependency to get SecurityService instance.
    
    Returns:
        SecurityService instance configured with application settings
        
    Example:
        @app.post("/security/scan")
        async def scan_api(
            security_service: SecurityService = Depends(get_security_service)
        ):
            return await security_service.scan_api_security(api_id)
    """
    return SecurityService(settings)


def get_compliance_service() -> ComplianceService:
    """
    Dependency to get ComplianceService instance.
    
    Returns:
        ComplianceService instance configured with application settings
        
    Example:
        @app.post("/compliance/scan")
        async def scan_api_compliance(
            compliance_service: ComplianceService = Depends(get_compliance_service)
        ):
            return await compliance_service.scan_api_compliance(api_id)
    """
    return ComplianceService(settings)


# Service dependencies will be added as services are implemented
# Example pattern:
#
# def get_discovery_service(
#     db: OpenSearch = Depends(get_db)
# ) -> DiscoveryService:
#     """Get discovery service instance."""
#     return DiscoveryService(db)
#
# def get_metrics_service(
#     db: OpenSearch = Depends(get_db)
# ) -> MetricsService:
#     """Get metrics service instance."""
#     return MetricsService(db)

# Made with Bob
