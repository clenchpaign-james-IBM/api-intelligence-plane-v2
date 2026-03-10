"""
RateLimitPolicy Repository

Provides data access operations for rate limit policies in OpenSearch.
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from opensearchpy import exceptions

from app.db.repositories.base import BaseRepository
from app.models.rate_limit import RateLimitPolicy, PolicyStatus, PolicyType

logger = logging.getLogger(__name__)


class RateLimitPolicyRepository(BaseRepository[RateLimitPolicy]):
    """Repository for RateLimitPolicy operations."""

    def __init__(self):
        """Initialize the RateLimitPolicy repository."""
        super().__init__(
            index_name="rate-limit-policies",
            model_class=RateLimitPolicy
        )

    def create_policy(self, policy: RateLimitPolicy) -> RateLimitPolicy:
        """
        Create a new rate limit policy.

        Args:
            policy: RateLimitPolicy to create

        Returns:
            Created RateLimitPolicy

        Raises:
            Exception: If creation fails
        """
        return self.create(policy, doc_id=str(policy.id))

    def get_by_id(self, policy_id: UUID) -> Optional[RateLimitPolicy]:
        """
        Get a rate limit policy by ID.

        Args:
            policy_id: Policy UUID

        Returns:
            RateLimitPolicy if found, None otherwise
        """
        return self.get(str(policy_id))

    def get_by_api_id(
        self,
        api_id: UUID,
        status: Optional[PolicyStatus] = None
    ) -> List[RateLimitPolicy]:
        """
        Get all rate limit policies for an API.

        Args:
            api_id: API UUID
            status: Optional status filter

        Returns:
            List of RateLimitPolicy objects
        """
        try:
            query = {
                "bool": {
                    "must": [
                        {"term": {"api_id": str(api_id)}}
                    ]
                }
            }

            if status:
                query["bool"]["must"].append({"term": {"status": status.value}})

            result = self.client.search(
                index=self.index_name,
                body={
                    "query": query,
                    "sort": [{"created_at": {"order": "desc"}}],
                    "size": 100
                }
            )

            return [
                self.model_class(**hit["_source"])
                for hit in result["hits"]["hits"]
            ]

        except Exception as e:
            logger.error(f"Failed to get policies for API {api_id}: {e}")
            raise

    async def get_active_policy(self, api_id: UUID) -> Optional[RateLimitPolicy]:
        """
        Get the active rate limit policy for an API.

        Args:
            api_id: API UUID

        Returns:
            Active RateLimitPolicy if found, None otherwise
        """
        try:
            result = self.client.search(
                index=self.index_name,
                body={
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"api_id": str(api_id)}},
                                {"term": {"status": PolicyStatus.ACTIVE.value}}
                            ]
                        }
                    },
                    "sort": [{"applied_at": {"order": "desc"}}],
                    "size": 1
                }
            )

            hits = result["hits"]["hits"]
            if hits:
                return self.model_class(**hits[0]["_source"])
            return None

        except Exception as e:
            logger.error(f"Failed to get active policy for API {api_id}: {e}")
            raise

    def update_policy(self, policy: RateLimitPolicy) -> Optional[RateLimitPolicy]:
        """
        Update an existing rate limit policy.

        Args:
            policy: RateLimitPolicy with updated data

        Returns:
            Updated RateLimitPolicy

        Raises:
            Exception: If update fails
        """
        policy.updated_at = datetime.utcnow()
        updates = policy.model_dump(mode="json", exclude={"id", "created_at"})
        return self.update(str(policy.id), updates)

    def delete_policy(self, policy_id: UUID) -> bool:
        """
        Delete a rate limit policy.

        Args:
            policy_id: Policy UUID

        Returns:
            True if deleted, False if not found

        Raises:
            Exception: If deletion fails
        """
        return self.delete(str(policy_id))

    def list_policies(
        self,
        api_id: Optional[UUID] = None,
        status: Optional[PolicyStatus] = None,
        policy_type: Optional[PolicyType] = None,
        page: int = 1,
        page_size: int = 20
    ) -> tuple[List[RateLimitPolicy], int]:
        """
        List rate limit policies with optional filters.

        Args:
            api_id: Optional API filter
            status: Optional status filter
            policy_type: Optional policy type filter
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (policies list, total count)
        """
        try:
            must_clauses = []

            if api_id:
                must_clauses.append({"term": {"api_id": str(api_id)}})
            if status:
                must_clauses.append({"term": {"status": status.value}})
            if policy_type:
                must_clauses.append({"term": {"policy_type": policy_type.value}})

            query = {"match_all": {}} if not must_clauses else {
                "bool": {"must": must_clauses}
            }

            from_index = (page - 1) * page_size

            result = self.client.search(
                index=self.index_name,
                body={
                    "query": query,
                    "sort": [{"created_at": {"order": "desc"}}],
                    "from": from_index,
                    "size": page_size
                }
            )

            policies = [
                self.model_class(**hit["_source"])
                for hit in result["hits"]["hits"]
            ]
            total = result["hits"]["total"]["value"]

            return policies, total

        except Exception as e:
            logger.error(f"Failed to list rate limit policies: {e}")
            raise

    def update_effectiveness_score(
        self,
        policy_id: UUID,
        effectiveness_score: float
    ) -> Optional[RateLimitPolicy]:
        """
        Update the effectiveness score of a policy.

        Args:
            policy_id: Policy UUID
            effectiveness_score: New effectiveness score (0-1)

        Returns:
            Updated RateLimitPolicy if found, None otherwise
        """
        try:
            policy = self.get_by_id(policy_id)
            if not policy:
                return None

            policy.effectiveness_score = effectiveness_score
            policy.updated_at = datetime.utcnow()

            return self.update_policy(policy)

        except Exception as e:
            logger.error(f"Failed to update effectiveness score: {e}")
            raise

    def activate_policy(self, policy_id: UUID) -> Optional[RateLimitPolicy]:
        """
        Activate a rate limit policy and deactivate others for the same API.

        Args:
            policy_id: Policy UUID to activate

        Returns:
            Activated RateLimitPolicy if found, None otherwise
        """
        try:
            policy = self.get_by_id(policy_id)
            if not policy:
                return None

            # Deactivate other policies for the same API
            existing_policies = self.get_by_api_id(
                policy.api_id,
                status=PolicyStatus.ACTIVE
            )
            for existing in existing_policies:
                if existing.id != policy_id:
                    existing.status = PolicyStatus.INACTIVE
                    self.update_policy(existing)

            # Activate the new policy
            policy.status = PolicyStatus.ACTIVE
            policy.applied_at = datetime.utcnow()
            policy.updated_at = datetime.utcnow()

            return self.update_policy(policy)

        except Exception as e:
            logger.error(f"Failed to activate policy: {e}")
            raise

    def adjust_thresholds(
        self,
        policy_id: UUID,
        new_thresholds: dict
    ) -> Optional[RateLimitPolicy]:
        """
        Adjust rate limit thresholds for adaptive policies.

        Args:
            policy_id: Policy UUID
            new_thresholds: New threshold values

        Returns:
            Updated RateLimitPolicy if found, None otherwise
        """
        try:
            policy = self.get_by_id(policy_id)
            if not policy:
                return None

            # Update thresholds
            if "requests_per_second" in new_thresholds:
                policy.limit_thresholds.requests_per_second = new_thresholds["requests_per_second"]
            if "requests_per_minute" in new_thresholds:
                policy.limit_thresholds.requests_per_minute = new_thresholds["requests_per_minute"]
            if "requests_per_hour" in new_thresholds:
                policy.limit_thresholds.requests_per_hour = new_thresholds["requests_per_hour"]
            if "concurrent_requests" in new_thresholds:
                policy.limit_thresholds.concurrent_requests = new_thresholds["concurrent_requests"]

            policy.last_adjusted_at = datetime.utcnow()
            policy.updated_at = datetime.utcnow()

            return self.update_policy(policy)

        except Exception as e:
            logger.error(f"Failed to adjust thresholds: {e}")
            raise


# Made with Bob