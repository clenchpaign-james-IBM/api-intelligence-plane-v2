"""
OpenSearch Client Wrapper

Provides a singleton OpenSearch client with connection pooling,
error handling, and retry logic.
"""

import logging
from typing import Optional
from contextlib import contextmanager

from opensearchpy import OpenSearch, exceptions
from opensearchpy.connection import RequestsHttpConnection

logger = logging.getLogger(__name__)


class OpenSearchClient:
    """
    Singleton wrapper for OpenSearch client with connection management.
    
    Features:
    - Connection pooling
    - Automatic retry logic
    - Error handling and logging
    - Health check capabilities
    """
    
    _instance: Optional["OpenSearchClient"] = None
    _client: Optional[OpenSearch] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize the OpenSearch client wrapper."""
        if self._client is None:
            self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the OpenSearch client with configuration."""
        from app.config import settings
        from app.utils.tls_config import get_opensearch_ssl_config
        
        try:
            # Get SSL configuration
            ssl_config = get_opensearch_ssl_config()
            
            self._client = OpenSearch(
                hosts=[{
                    "host": settings.OPENSEARCH_HOST,
                    "port": settings.OPENSEARCH_PORT,
                }],
                http_auth=(
                    settings.OPENSEARCH_USER,
                    settings.OPENSEARCH_PASSWORD,
                ),
                connection_class=RequestsHttpConnection,
                pool_maxsize=settings.OPENSEARCH_POOL_SIZE,
                timeout=settings.OPENSEARCH_TIMEOUT,
                max_retries=settings.OPENSEARCH_MAX_RETRIES,
                retry_on_timeout=True,
                **ssl_config,
            )
            
            # Verify connection
            if self._client.ping():
                logger.info(
                    f"Connected to OpenSearch at "
                    f"{settings.OPENSEARCH_HOST}:{settings.OPENSEARCH_PORT}"
                )
            else:
                logger.error("Failed to ping OpenSearch cluster")
                
        except Exception as e:
            logger.error(f"Failed to initialize OpenSearch client: {e}")
            raise
    
    @property
    def client(self) -> OpenSearch:
        """Get the OpenSearch client instance."""
        if self._client is None:
            self._initialize_client()
        return self._client
    
    def health_check(self) -> dict:
        """
        Check OpenSearch cluster health.
        
        Returns:
            dict: Cluster health information
        """
        try:
            health = self.client.cluster.health()
            return {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"],
                "active_shards": health["active_shards"],
                "unassigned_shards": health["unassigned_shards"],
            }
        except exceptions.ConnectionError as e:
            logger.error(f"OpenSearch connection error: {e}")
            return {"status": "error", "error": str(e)}
        except Exception as e:
            logger.error(f"OpenSearch health check failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def ping(self) -> bool:
        """
        Ping the OpenSearch cluster.
        
        Returns:
            bool: True if cluster is reachable
        """
        try:
            return self.client.ping()
        except Exception as e:
            logger.error(f"OpenSearch ping failed: {e}")
            return False
    
    @contextmanager
    def error_handler(self, operation: str):
        """
        Context manager for handling OpenSearch errors.
        
        Args:
            operation: Description of the operation being performed
        """
        try:
            yield
        except exceptions.NotFoundError as e:
            logger.warning(f"{operation} - Resource not found: {e}")
            raise
        except exceptions.ConflictError as e:
            logger.warning(f"{operation} - Conflict error: {e}")
            raise
        except exceptions.RequestError as e:
            logger.error(f"{operation} - Request error: {e.error}")
            raise
        except exceptions.ConnectionError as e:
            logger.error(f"{operation} - Connection error: {e}")
            raise
        except exceptions.TransportError as e:
            logger.error(f"{operation} - Transport error: {e}")
            raise
        except Exception as e:
            logger.error(f"{operation} - Unexpected error: {e}")
            raise
    
    def close(self):
        """Close the OpenSearch client connection."""
        if self._client:
            try:
                self._client.close()
                logger.info("OpenSearch client connection closed")
            except Exception as e:
                logger.error(f"Error closing OpenSearch client: {e}")
            finally:
                self._client = None


# Singleton instance
_opensearch_client: Optional[OpenSearchClient] = None


def get_opensearch_client() -> OpenSearchClient:
    """
    Get the singleton OpenSearch client instance.
    
    Returns:
        OpenSearchClient: The OpenSearch client wrapper
    """
    global _opensearch_client
    if _opensearch_client is None:
        _opensearch_client = OpenSearchClient()
    return _opensearch_client


def get_client() -> OpenSearch:
    """
    Get the raw OpenSearch client for direct operations.
    
    Returns:
        OpenSearch: The OpenSearch client instance
    """
    return get_opensearch_client().client

# Made with Bob
