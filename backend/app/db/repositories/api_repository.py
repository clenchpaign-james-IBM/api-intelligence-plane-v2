"""
API Repository

Provides CRUD operations and specialized queries for API entities.
"""

import logging
from typing import Dict, List, Optional, Any
from uuid import UUID

from app.db.repositories.base import BaseRepository
from app.models.api import API, APIStatus, DiscoveryMethod

logger = logging.getLogger(__name__)


class APIRepository(BaseRepository[API]):
    """Repository for API entity operations."""
    
    def __init__(self):
        """Initialize the API repository."""
        super().__init__(index_name="api-inventory", model_class=API)
    
    def find_by_gateway(
        self,
        gateway_id: UUID,
        size: int = 100,
        from_: int = 0,
    ) -> tuple[List[API], int]:
        """
        Find all APIs belonging to a specific gateway.
        
        Args:
            gateway_id: Gateway UUID
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of APIs, total count)
        """
        query = {
            "term": {
                "gateway_id": str(gateway_id)
            }
        }
        return self.search(query, size=size, from_=from_)
    
    def find_by_status(
        self,
        status: APIStatus,
        size: int = 100,
        from_: int = 0,
    ) -> tuple[List[API], int]:
        """
        Find all APIs with a specific status.
        
        Args:
            status: API status to filter by
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of APIs, total count)
        """
        query = {
            "term": {
                "status": status.value
            }
        }
        return self.search(query, size=size, from_=from_)
    
    def find_shadow_apis(
        self,
        size: int = 100,
        from_: int = 0,
    ) -> tuple[List[API], int]:
        """
        Find all shadow APIs.
        
        Args:
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of shadow APIs, total count)
        """
        query = {
            "term": {
                "is_shadow": True
            }
        }
        return self.search(query, size=size, from_=from_)
    
    def find_by_discovery_method(
        self,
        method: DiscoveryMethod,
        size: int = 100,
        from_: int = 0,
    ) -> tuple[List[API], int]:
        """
        Find APIs by discovery method.
        
        Args:
            method: Discovery method to filter by
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of APIs, total count)
        """
        query = {
            "term": {
                "discovery_method": method.value
            }
        }
        return self.search(query, size=size, from_=from_)
    
    def search_by_name(
        self,
        name: str,
        size: int = 100,
        from_: int = 0,
    ) -> tuple[List[API], int]:
        """
        Search APIs by name (fuzzy match).
        
        Args:
            name: Name to search for
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of APIs, total count)
        """
        query = {
            "match": {
                "name": {
                    "query": name,
                    "fuzziness": "AUTO"
                }
            }
        }
        return self.search(query, size=size, from_=from_)
    
    def search_by_tags(
        self,
        tags: List[str],
        size: int = 100,
        from_: int = 0,
    ) -> tuple[List[API], int]:
        """
        Search APIs by tags.
        
        Args:
            tags: List of tags to search for
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of APIs, total count)
        """
        query = {
            "terms": {
                "tags": tags
            }
        }
        return self.search(query, size=size, from_=from_)
    
    def find_unhealthy_apis(
        self,
        health_threshold: float = 50.0,
        size: int = 100,
        from_: int = 0,
    ) -> tuple[List[API], int]:
        """
        Find APIs with health score below threshold.
        
        Args:
            health_threshold: Health score threshold (0-100)
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of unhealthy APIs, total count)
        """
        query = {
            "range": {
                "health_score": {
                    "lt": health_threshold
                }
            }
        }
        sort = [{"health_score": {"order": "asc"}}]
        return self.search(query, size=size, from_=from_, sort=sort)
    
    def find_by_base_path(
        self,
        base_path: str,
        gateway_id: Optional[UUID] = None,
    ) -> Optional[API]:
        """
        Find API by base path (and optionally gateway).
        
        Args:
            base_path: Base path to search for
            gateway_id: Optional gateway ID to narrow search
            
        Returns:
            API if found, None otherwise
        """
        query: Dict[str, Any] = {
            "bool": {
                "must": [
                    {"term": {"base_path": base_path}}
                ]
            }
        }
        
        if gateway_id:
            query["bool"]["must"].append(
                {"term": {"gateway_id": str(gateway_id)}}
            )
        
        results, _ = self.search(query, size=1)
        return results[0] if results else None
    
    def advanced_search(
        self,
        filters: Dict[str, Any],
        size: int = 100,
        from_: int = 0,
        sort_by: Optional[str] = None,
        sort_order: str = "asc",
    ) -> tuple[List[API], int]:
        """
        Advanced search with multiple filters.
        
        Args:
            filters: Dictionary of filter criteria
                - gateway_id: UUID
                - status: APIStatus
                - is_shadow: bool
                - min_health_score: float
                - max_health_score: float
                - tags: List[str]
                - name: str (fuzzy match)
            size: Number of results to return
            from_: Offset for pagination
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            
        Returns:
            Tuple of (list of APIs, total count)
        """
        must_clauses = []
        
        # Gateway filter
        if "gateway_id" in filters:
            must_clauses.append({
                "term": {"gateway_id": str(filters["gateway_id"])}
            })
        
        # Status filter
        if "status" in filters:
            status_value = filters["status"].value if isinstance(filters["status"], APIStatus) else filters["status"]
            must_clauses.append({
                "term": {"status": status_value}
            })
        
        # Shadow API filter
        if "is_shadow" in filters:
            must_clauses.append({
                "term": {"is_shadow": filters["is_shadow"]}
            })
        
        # Health score range
        if "min_health_score" in filters or "max_health_score" in filters:
            range_query: Dict[str, Any] = {}
            if "min_health_score" in filters:
                range_query["gte"] = filters["min_health_score"]
            if "max_health_score" in filters:
                range_query["lte"] = filters["max_health_score"]
            must_clauses.append({
                "range": {"health_score": range_query}
            })
        
        # Tags filter
        if "tags" in filters and filters["tags"]:
            must_clauses.append({
                "terms": {"tags": filters["tags"]}
            })
        
        # Name search (fuzzy)
        if "name" in filters:
            must_clauses.append({
                "match": {
                    "name": {
                        "query": filters["name"],
                        "fuzziness": "AUTO"
                    }
                }
            })
        
        # Build query
        query = {
            "bool": {
                "must": must_clauses if must_clauses else [{"match_all": {}}]
            }
        }
        
        # Build sort
        sort = None
        if sort_by:
            sort = [{sort_by: {"order": sort_order}}]
        
        return self.search(query, size=size, from_=from_, sort=sort)
    
    def get_statistics(self, gateway_id: Optional[UUID] = None) -> Dict[str, Any]:
        """
        Get API statistics.
        
        Args:
            gateway_id: Optional gateway ID to filter by
            
        Returns:
            Dictionary with statistics
        """
        try:
            # Build aggregation query
            aggs = {
                "total_apis": {"value_count": {"field": "id"}},
                "shadow_apis": {
                    "filter": {"term": {"is_shadow": True}}
                },
                "by_status": {
                    "terms": {"field": "status"}
                },
                "by_discovery_method": {
                    "terms": {"field": "discovery_method"}
                },
                "avg_health_score": {
                    "avg": {"field": "health_score"}
                },
                "health_distribution": {
                    "histogram": {
                        "field": "health_score",
                        "interval": 10
                    }
                }
            }
            
            # Add gateway filter if specified
            query = {"match_all": {}}
            if gateway_id:
                query = {"term": {"gateway_id": str(gateway_id)}}
            
            response = self.client.search(
                index=self.index_name,
                body={
                    "size": 0,
                    "query": query,
                    "aggs": aggs
                }
            )
            
            return {
                "total_apis": response["aggregations"]["total_apis"]["value"],
                "shadow_apis": response["aggregations"]["shadow_apis"]["doc_count"],
                "by_status": {
                    bucket["key"]: bucket["doc_count"]
                    for bucket in response["aggregations"]["by_status"]["buckets"]
                },
                "by_discovery_method": {
                    bucket["key"]: bucket["doc_count"]
                    for bucket in response["aggregations"]["by_discovery_method"]["buckets"]
                },
                "avg_health_score": response["aggregations"]["avg_health_score"]["value"],
                "health_distribution": [
                    {"range": f"{bucket['key']}-{bucket['key']+10}", "count": bucket["doc_count"]}
                    for bucket in response["aggregations"]["health_distribution"]["buckets"]
                ]
            }
            
        except Exception as e:
            logger.error(f"Failed to get API statistics: {e}")
            raise


# Made with Bob