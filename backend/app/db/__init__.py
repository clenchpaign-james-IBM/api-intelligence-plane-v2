"""
Database module for OpenSearch operations.

This module provides:
- OpenSearch client management
- Base repository patterns
- Index migrations
- Connection pooling and error handling
"""

from .client import get_opensearch_client, OpenSearchClient

__all__ = ["get_opensearch_client", "OpenSearchClient"]

# Made with Bob
