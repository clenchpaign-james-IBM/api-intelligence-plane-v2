"""
Query Repository

Provides data access layer for Query entities with specialized query operations
for natural language query history and session management.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from uuid import UUID

from app.db.repositories.base import BaseRepository
from app.models.query import Query, QueryType, UserFeedback

logger = logging.getLogger(__name__)


class QueryRepository(BaseRepository[Query]):
    """
    Repository for Query entity operations.
    
    Provides CRUD operations and specialized queries for natural language
    query history, session management, and analytics.
    """
    
    def __init__(self):
        """Initialize the Query repository."""
        super().__init__(
            index_name="query-history",
            model_class=Query
        )
    
    def get_by_session(
        self,
        session_id: UUID,
        size: int = 50,
        from_: int = 0
    ) -> tuple[List[Query], int]:
        """
        Get all queries for a specific session.
        
        Args:
            session_id: Session UUID
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of queries, total count)
        """
        query = {
            "term": {
                "session_id": str(session_id)
            }
        }
        
        sort = [{"created_at": {"order": "asc"}}]
        
        return self.search(query, size=size, from_=from_, sort=sort)
    
    def get_recent_queries(
        self,
        user_id: Optional[str] = None,
        hours: int = 24,
        size: int = 20
    ) -> List[Query]:
        """
        Get recent queries, optionally filtered by user.
        
        Args:
            user_id: Optional user identifier
            hours: Number of hours to look back
            size: Maximum number of results
            
        Returns:
            List of recent queries
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        must_clauses = [
            {
                "range": {
                    "created_at": {
                        "gte": since.isoformat()
                    }
                }
            }
        ]
        
        if user_id:
            must_clauses.append({
                "term": {
                    "user_id": {
                        "value": user_id
                    }
                }
            })
        
        query = {
            "bool": {
                "must": must_clauses
            }
        }
        
        sort = [{"created_at": {"order": "desc"}}]
        
        queries, _ = self.search(query, size=size, sort=sort)
        return queries
    
    def get_by_query_type(
        self,
        query_type: QueryType,
        size: int = 20,
        from_: int = 0
    ) -> tuple[List[Query], int]:
        """
        Get queries by type.
        
        Args:
            query_type: Type of query to filter by
            size: Number of results to return
            from_: Offset for pagination
            
        Returns:
            Tuple of (list of queries, total count)
        """
        query = {
            "term": {
                "query_type": query_type.value
            }
        }
        
        sort = [{"created_at": {"order": "desc"}}]
        
        return self.search(query, size=size, from_=from_, sort=sort)
    
    def get_queries_with_feedback(
        self,
        feedback: Optional[UserFeedback] = None,
        size: int = 50
    ) -> List[Query]:
        """
        Get queries that have user feedback.
        
        Args:
            feedback: Optional specific feedback type to filter by
            size: Maximum number of results
            
        Returns:
            List of queries with feedback
        """
        if feedback:
            query = {
                "term": {
                    "feedback": feedback.value
                }
            }
        else:
            query = {
                "exists": {
                    "field": "feedback"
                }
            }
        
        sort = [{"created_at": {"order": "desc"}}]
        
        queries, _ = self.search(query, size=size, sort=sort)
        return queries
    
    def get_low_confidence_queries(
        self,
        threshold: float = 0.7,
        size: int = 20
    ) -> List[Query]:
        """
        Get queries with low confidence scores for analysis.
        
        Args:
            threshold: Confidence score threshold (queries below this)
            size: Maximum number of results
            
        Returns:
            List of low confidence queries
        """
        query = {
            "range": {
                "confidence_score": {
                    "lt": threshold
                }
            }
        }
        
        sort = [{"confidence_score": {"order": "asc"}}]
        
        queries, _ = self.search(query, size=size, sort=sort)
        return queries
    
    def get_slow_queries(
        self,
        threshold_ms: int = 3000,
        size: int = 20
    ) -> List[Query]:
        """
        Get queries that took longer than threshold to execute.
        
        Args:
            threshold_ms: Execution time threshold in milliseconds
            size: Maximum number of results
            
        Returns:
            List of slow queries
        """
        query = {
            "range": {
                "execution_time_ms": {
                    "gte": threshold_ms
                }
            }
        }
        
        sort = [{"execution_time_ms": {"order": "desc"}}]
        
        queries, _ = self.search(query, size=size, sort=sort)
        return queries
    
    def update_feedback(
        self,
        query_id: str,
        feedback: UserFeedback,
        comment: Optional[str] = None
    ) -> Optional[Query]:
        """
        Update user feedback for a query.
        
        Args:
            query_id: Query ID
            feedback: User feedback
            comment: Optional feedback comment
            
        Returns:
            Updated query if found, None otherwise
        """
        updates = {
            "feedback": feedback.value
        }
        
        if comment:
            updates["feedback_comment"] = comment
        
        return self.update(query_id, updates)
    
    def get_query_statistics(
        self,
        session_id: Optional[UUID] = None,
        hours: int = 24
    ) -> dict:
        """
        Get query statistics for analytics.
        
        Args:
            session_id: Optional session to filter by
            hours: Number of hours to look back
            
        Returns:
            Dictionary with query statistics
        """
        since = datetime.utcnow() - timedelta(hours=hours)
        
        must_clauses = [
            {
                "range": {
                    "created_at": {
                        "gte": since.isoformat()
                    }
                }
            }
        ]
        
        if session_id:
            must_clauses.append({
                "term": {
                    "session_id": {
                        "value": str(session_id)
                    }
                }
            })
        
        query = {
            "bool": {
                "must": must_clauses
            }
        }
        
        # Get aggregations
        body = {
            "query": query,
            "size": 0,
            "aggs": {
                "by_type": {
                    "terms": {
                        "field": "query_type",
                        "size": 10
                    }
                },
                "avg_confidence": {
                    "avg": {
                        "field": "confidence_score"
                    }
                },
                "avg_execution_time": {
                    "avg": {
                        "field": "execution_time_ms"
                    }
                },
                "feedback_distribution": {
                    "terms": {
                        "field": "feedback",
                        "size": 10
                    }
                }
            }
        }
        
        try:
            response = self.client.search(
                index=self.index_name,
                body=body
            )
            
            return {
                "total_queries": response["hits"]["total"]["value"],
                "by_type": {
                    bucket["key"]: bucket["doc_count"]
                    for bucket in response["aggregations"]["by_type"]["buckets"]
                },
                "avg_confidence": response["aggregations"]["avg_confidence"]["value"],
                "avg_execution_time_ms": response["aggregations"]["avg_execution_time"]["value"],
                "feedback_distribution": {
                    bucket["key"]: bucket["doc_count"]
                    for bucket in response["aggregations"]["feedback_distribution"]["buckets"]
                }
            }
        except Exception as e:
            logger.error(f"Failed to get query statistics: {e}")
            return {
                "total_queries": 0,
                "by_type": {},
                "avg_confidence": 0.0,
                "avg_execution_time_ms": 0.0,
                "feedback_distribution": {}
            }
    
    def search_by_text(
        self,
        search_text: str,
        size: int = 20
    ) -> List[Query]:
        """
        Search queries by text content.
        
        Args:
            search_text: Text to search for
            size: Maximum number of results
            
        Returns:
            List of matching queries
        """
        query = {
            "multi_match": {
                "query": search_text,
                "fields": ["query_text", "response_text"],
                "type": "best_fields"
            }
        }
        
        sort = [{"_score": {"order": "desc"}}, {"created_at": {"order": "desc"}}]
        
        queries, _ = self.search(query, size=size, sort=sort)
        return queries


# Made with Bob