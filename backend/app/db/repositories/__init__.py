"""
Repository module for data access patterns.

Provides base repository classes and specific repository implementations
for each entity type.
"""

from .base import BaseRepository
from .recommendation_repository import RecommendationRepository

__all__ = ["BaseRepository", "RecommendationRepository"]

# Made with Bob
