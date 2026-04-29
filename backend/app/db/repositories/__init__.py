"""
Repository module for data access patterns.

Provides base repository classes and specific repository implementations
for each entity type.
"""

from .base import BaseRepository
from .query_repository import QueryRepository
from .recommendation_repository import RecommendationRepository

__all__ = ["BaseRepository", "QueryRepository", "RecommendationRepository"]

# Made with Bob
