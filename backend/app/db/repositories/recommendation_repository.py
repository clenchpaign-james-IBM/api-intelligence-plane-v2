"""
Recommendation Repository

Handles CRUD operations and queries for optimization recommendations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from app.db.repositories.base import BaseRepository
from app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
)


class RecommendationRepository(BaseRepository[OptimizationRecommendation]):
    """Repository for managing optimization recommendations"""

    def __init__(self):
        super().__init__(
            index_name="optimization-recommendations",
            model_class=OptimizationRecommendation,
        )

    def create_recommendation(
        self, recommendation: OptimizationRecommendation
    ) -> OptimizationRecommendation:
        """
        Create a new recommendation

        Args:
            recommendation: OptimizationRecommendation model instance

        Returns:
            Created recommendation with ID
        """
        return self.create(recommendation)

    def get_recommendation(
        self, recommendation_id: str
    ) -> Optional[OptimizationRecommendation]:
        """
        Get recommendation by ID

        Args:
            recommendation_id: Recommendation UUID

        Returns:
            Recommendation if found, None otherwise
        """
        return self.get(recommendation_id)

    def list_recommendations(
        self,
        api_id: Optional[str] = None,
        priority: Optional[RecommendationPriority] = None,
        status: Optional[RecommendationStatus] = None,
        recommendation_type: Optional[RecommendationType] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """
        List recommendations with filters

        Args:
            api_id: Filter by API ID
            priority: Filter by priority level
            status: Filter by recommendation status
            recommendation_type: Filter by recommendation type
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Dict with recommendations list and pagination info
        """
        must_clauses = []

        if api_id:
            must_clauses.append({"term": {"api_id": api_id}})
        if priority:
            must_clauses.append({"term": {"priority": priority.value}})
        if status:
            must_clauses.append({"term": {"status": status.value}})
        if recommendation_type:
            must_clauses.append(
                {"term": {"recommendation_type": recommendation_type.value}}
            )

        # Default to pending recommendations if no status filter
        if not status:
            must_clauses.append({"term": {"status": RecommendationStatus.PENDING.value}})

        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}

        # Sort by priority (critical first) and estimated impact (highest first)
        sort = [
            {
                "priority": {
                    "order": "asc",
                    "unmapped_type": "keyword",
                }
            },
            {
                "estimated_impact.improvement_percentage": {
                    "order": "desc",
                    "unmapped_type": "float",
                }
            },
        ]

        # Calculate offset from page number
        from_ = (page - 1) * page_size

        recommendations, total = self.search(
            query=query,
            sort=sort,
            size=page_size,
            from_=from_,
        )

        return {
            "recommendations": recommendations,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    def get_pending_recommendations_for_api(
        self, api_id: str
    ) -> List[OptimizationRecommendation]:
        """
        Get all pending recommendations for a specific API

        Args:
            api_id: API UUID

        Returns:
            List of pending recommendations
        """
        query = {
            "bool": {
                "must": [
                    {"term": {"api_id": api_id}},
                    {"term": {"status": RecommendationStatus.PENDING.value}},
                ]
            }
        }

        recommendations, _ = self.search(query=query, size=100)
        return recommendations

    def get_recommendations_by_type(
        self,
        recommendation_type: RecommendationType,
        api_id: Optional[str] = None,
    ) -> List[OptimizationRecommendation]:
        """
        Get recommendations by type

        Args:
            recommendation_type: Type of recommendation
            api_id: Optional API ID filter

        Returns:
            List of recommendations
        """
        must_clauses = [
            {"term": {"recommendation_type": recommendation_type.value}},
        ]

        if api_id:
            must_clauses.append({"term": {"api_id": api_id}})

        query = {"bool": {"must": must_clauses}}

        recommendations, _ = self.search(query=query, size=100)
        return recommendations

    def update_recommendation_status(
        self,
        recommendation_id: str,
        status: RecommendationStatus,
        implemented_at: Optional[datetime] = None,
    ) -> Optional[OptimizationRecommendation]:
        """
        Update recommendation status

        Args:
            recommendation_id: Recommendation UUID
            status: New status
            implemented_at: When the recommendation was implemented

        Returns:
            Updated recommendation if found
        """
        update_doc = {
            "status": status.value,
        }

        if implemented_at:
            update_doc["implemented_at"] = implemented_at.isoformat()

        return self.update(recommendation_id, update_doc)

    def add_validation_results(
        self,
        recommendation_id: str,
        validation_results: Dict[str, Any],
    ) -> Optional[OptimizationRecommendation]:
        """
        Add validation results after implementation

        Args:
            recommendation_id: Recommendation UUID
            validation_results: Validation results data

        Returns:
            Updated recommendation with validation results
        """
        update_doc = {
            "validation_results": validation_results,
        }

        return self.update(recommendation_id, update_doc)

    def get_high_impact_recommendations(
        self,
        min_improvement: float = 20.0,
        api_id: Optional[str] = None,
    ) -> List[OptimizationRecommendation]:
        """
        Get high-impact recommendations

        Args:
            min_improvement: Minimum improvement percentage
            api_id: Optional API ID filter

        Returns:
            List of high-impact recommendations
        """
        must_clauses = [
            {
                "range": {
                    "estimated_impact.improvement_percentage": {"gte": min_improvement}
                }
            },
            {"term": {"status": RecommendationStatus.PENDING.value}},
        ]

        if api_id:
            must_clauses.append({"term": {"api_id": api_id}})

        query = {"bool": {"must": must_clauses}}

        recommendations, _ = self.search(query=query, size=100)
        return recommendations

    def get_expired_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Get recommendations that have expired

        Returns:
            List of expired pending recommendations
        """
        now = datetime.utcnow()
        query = {
            "bool": {
                "must": [
                    {"term": {"status": RecommendationStatus.PENDING.value}},
                    {"range": {"expires_at": {"lt": now.isoformat()}}},
                ]
            }
        }

        recommendations, _ = self.search(query=query, size=1000)
        return recommendations

    def get_implementation_stats(
        self, api_id: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get recommendation implementation statistics

        Args:
            api_id: Optional API ID filter
            days: Number of days to look back

        Returns:
            Dict with implementation statistics
        """
        start_time = datetime.utcnow() - timedelta(days=days)

        must_clauses = [
            {"range": {"created_at": {"gte": start_time.isoformat()}}},
        ]

        if api_id:
            must_clauses.append({"term": {"api_id": api_id}})

        query = {"bool": {"must": must_clauses}}

        # Aggregation for statistics
        aggs = {
            "by_status": {
                "terms": {"field": "status"},
            },
            "by_priority": {
                "terms": {"field": "priority"},
            },
            "by_type": {
                "terms": {"field": "recommendation_type"},
            },
            "avg_improvement": {
                "avg": {"field": "estimated_impact.improvement_percentage"}
            },
            "total_cost_savings": {"sum": {"field": "cost_savings"}},
        }

        result = self.client.search(
            index=self.index_name, body={"query": query, "aggs": aggs, "size": 0}
        )

        aggregations = result.get("aggregations", {})

        return {
            "total_recommendations": result["hits"]["total"]["value"],
            "by_status": [
                {"status": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggregations.get("by_status", {}).get("buckets", [])
            ],
            "by_priority": [
                {"priority": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggregations.get("by_priority", {}).get("buckets", [])
            ],
            "by_type": [
                {"type": bucket["key"], "count": bucket["doc_count"]}
                for bucket in aggregations.get("by_type", {}).get("buckets", [])
            ],
            "avg_improvement": aggregations.get("avg_improvement", {}).get("value", 0),
            "total_cost_savings": aggregations.get("total_cost_savings", {}).get(
                "value", 0
            ),
        }

    def get_validation_success_rate(
        self, api_id: Optional[str] = None, days: int = 30
    ) -> Dict[str, Any]:
        """
        Get validation success rate for implemented recommendations

        Args:
            api_id: Optional API ID filter
            days: Number of days to look back

        Returns:
            Dict with validation statistics
        """
        start_time = datetime.utcnow() - timedelta(days=days)

        must_clauses = [
            {"term": {"status": RecommendationStatus.IMPLEMENTED.value}},
            {"exists": {"field": "validation_results"}},
            {"range": {"implemented_at": {"gte": start_time.isoformat()}}},
        ]

        if api_id:
            must_clauses.append({"term": {"api_id": api_id}})

        query = {"bool": {"must": must_clauses}}

        # Aggregation for success rate
        aggs = {
            "by_success": {
                "terms": {"field": "validation_results.success"},
            },
            "avg_actual_improvement": {
                "avg": {"field": "validation_results.actual_impact.actual_improvement"}
            },
        }

        result = self.client.search(
            index=self.index_name, body={"query": query, "aggs": aggs, "size": 0}
        )

        aggregations = result.get("aggregations", {})
        total = result["hits"]["total"]["value"]

        success_buckets = aggregations.get("by_success", {}).get("buckets", [])
        success_count = next(
            (b["doc_count"] for b in success_buckets if b["key"] == True), 0
        )

        return {
            "total_validated": total,
            "successful": success_count,
            "failed": total - success_count,
            "success_rate": (success_count / total * 100) if total > 0 else 0,
            "avg_actual_improvement": aggregations.get("avg_actual_improvement", {}).get(
                "value", 0
            ),
        }

    def delete_old_recommendations(self, days: int = 90) -> int:
        """
        Delete recommendations older than specified days

        Args:
            days: Age threshold in days

        Returns:
            Number of deleted recommendations
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        query = {"range": {"created_at": {"lt": cutoff_date.isoformat()}}}

        result = self.client.delete_by_query(
            index=self.index_name, body={"query": query}
        )

        return result.get("deleted", 0)


# Made with Bob