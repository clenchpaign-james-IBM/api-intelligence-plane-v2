"""
Repository module for data access patterns.

Provides base repository classes and specific repository implementations
for each entity type.
"""

from .base import BaseRepository
from .rate_limit_repository import RateLimitPolicyRepository
from .recommendation_repository import RecommendationRepository

__all__ = ["BaseRepository", "RateLimitPolicyRepository", "RecommendationRepository"]

# Made with Bob
