"""Shared OpenSearch client for MCP servers.

Provides a reusable OpenSearch client for all MCP servers to access
the API Intelligence Plane data.
"""

import logging
import os
from typing import Any, Optional

from opensearchpy import AsyncOpenSearch, OpenSearch

logger = logging.getLogger(__name__)


class MCPOpenSearchClient:
    """Shared OpenSearch client for MCP servers.

    This client provides access to the API Intelligence Plane's OpenSearch
    indices for MCP servers to query and retrieve data.
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_ssl: bool = False,
        verify_certs: bool = False,
    ):
        """Initialize OpenSearch client for MCP servers.

        Args:
            host: OpenSearch host (default: from OPENSEARCH_HOST env var or localhost)
            port: OpenSearch port (default: from OPENSEARCH_PORT env var or 9200)
            username: OpenSearch username (default: from OPENSEARCH_USERNAME env var)
            password: OpenSearch password (default: from OPENSEARCH_PASSWORD env var)
            use_ssl: Whether to use SSL (default: from OPENSEARCH_USE_SSL env var or False)
            verify_certs: Whether to verify SSL certificates (default: False)
        """
        self.host = host or os.getenv("OPENSEARCH_HOST", "localhost")
        self.port = port or int(os.getenv("OPENSEARCH_PORT", "9200"))
        self.username = username or os.getenv("OPENSEARCH_USERNAME")
        self.password = password or os.getenv("OPENSEARCH_PASSWORD")
        self.use_ssl = use_ssl or os.getenv("OPENSEARCH_USE_SSL", "false").lower() == "true"
        self.verify_certs = verify_certs

        self._client: Optional[AsyncOpenSearch] = None
        self._sync_client: Optional[OpenSearch] = None

        logger.info(f"Initialized MCP OpenSearch client for {self.host}:{self.port}")

    def _get_connection_params(self) -> dict[str, Any]:
        """Get OpenSearch connection parameters.

        Returns:
            dict: Connection parameters
        """
        params = {
            "hosts": [{"host": self.host, "port": self.port}],
            "use_ssl": self.use_ssl,
            "verify_certs": self.verify_certs,
            "ssl_show_warn": False,
        }

        if self.username and self.password:
            params["http_auth"] = (self.username, self.password)

        return params

    async def connect(self) -> AsyncOpenSearch:
        """Get or create async OpenSearch client.

        Returns:
            AsyncOpenSearch: Async OpenSearch client instance
        """
        if self._client is None:
            params = self._get_connection_params()
            self._client = AsyncOpenSearch(**params)
            logger.info("Created async OpenSearch client")

        return self._client

    def connect_sync(self) -> OpenSearch:
        """Get or create sync OpenSearch client.

        Returns:
            OpenSearch: Sync OpenSearch client instance
        """
        if self._sync_client is None:
            params = self._get_connection_params()
            self._sync_client = OpenSearch(**params)
            logger.info("Created sync OpenSearch client")

        return self._sync_client

    async def close(self) -> None:
        """Close async OpenSearch client connection."""
        if self._client:
            await self._client.close()
            self._client = None
            logger.info("Closed async OpenSearch client")

    def close_sync(self) -> None:
        """Close sync OpenSearch client connection."""
        if self._sync_client:
            self._sync_client.close()
            self._sync_client = None
            logger.info("Closed sync OpenSearch client")

    async def search(
        self,
        index: str,
        query: dict[str, Any],
        size: int = 10,
        from_: int = 0,
    ) -> dict[str, Any]:
        """Search OpenSearch index.

        Args:
            index: Index name or pattern
            query: OpenSearch query DSL
            size: Number of results to return
            from_: Starting offset

        Returns:
            dict: Search results
        """
        client = await self.connect()
        try:
            response = await client.search(
                index=index,
                body={"query": query, "size": size, "from": from_}
            )
            return response
        except Exception as e:
            logger.error(f"Search failed for index {index}: {e}")
            raise

    async def get_document(self, index: str, doc_id: str) -> Optional[dict[str, Any]]:
        """Get a document by ID.

        Args:
            index: Index name
            doc_id: Document ID

        Returns:
            Optional[dict]: Document if found, None otherwise
        """
        client = await self.connect()
        try:
            response = await client.get(index=index, id=doc_id)
            return response["_source"]
        except Exception as e:
            logger.warning(f"Document not found: {index}/{doc_id}: {e}")
            return None

    async def count(self, index: str, query: Optional[dict[str, Any]] = None) -> int:
        """Count documents matching query.

        Args:
            index: Index name or pattern
            query: Optional OpenSearch query DSL

        Returns:
            int: Document count
        """
        client = await self.connect()
        try:
            body = {"query": query} if query else None
            response = await client.count(index=index, body=body)
            return response["count"]
        except Exception as e:
            logger.error(f"Count failed for index {index}: {e}")
            raise

    async def aggregate(
        self, index: str, query: dict[str, Any], aggregations: dict[str, Any]
    ) -> dict[str, Any]:
        """Perform aggregations on index.

        Args:
            index: Index name or pattern
            query: OpenSearch query DSL
            aggregations: Aggregation definitions

        Returns:
            dict: Aggregation results
        """
        client = await self.connect()
        try:
            response = await client.search(
                index=index,
                body={
                    "query": query,
                    "size": 0,
                    "aggs": aggregations,
                }
            )
            return response.get("aggregations", {})
        except Exception as e:
            logger.error(f"Aggregation failed for index {index}: {e}")
            raise

    async def health_check(self) -> dict[str, Any]:
        """Check OpenSearch cluster health.

        Returns:
            dict: Cluster health information
        """
        client = await self.connect()
        try:
            health = await client.cluster.health()
            return {
                "status": health["status"],
                "cluster_name": health["cluster_name"],
                "number_of_nodes": health["number_of_nodes"],
                "active_shards": health["active_shards"],
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "unavailable",
                "error": str(e),
            }

# Made with Bob
