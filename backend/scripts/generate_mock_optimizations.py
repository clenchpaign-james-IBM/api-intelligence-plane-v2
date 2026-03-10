#!/usr/bin/env python3
"""
Mock Optimization Recommendation Data Generator

Generates realistic optimization recommendation data for testing and development.
Creates recommendations with various types, priorities, and implementation statuses.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
from typing import List
import random
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_client
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.api_repository import APIRepository
from app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    RecommendationStatus,
    EstimatedImpact,
    ImplementationEffort,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockOptimizationGenerator:
    """Generates mock optimization recommendation data for testing."""
    
    def __init__(self):
        self.recommendation_repo = RecommendationRepository()
        self.api_repo = APIRepository()
    
    async def generate_recommendations(
        self,
        api_id: str,
        count: int = 5,
        status_distribution: dict | None = None
    ) -> List[OptimizationRecommendation]:
        """
        Generate mock optimization recommendations for an API.
        
        Args:
            api_id: Target API ID
            count: Number of recommendations to generate
            status_distribution: Distribution of statuses (default: mixed)
            
        Returns:
            List of created recommendations
        """
        if status_distribution is None:
            status_distribution = {
                RecommendationStatus.PENDING: 0.4,
                RecommendationStatus.IN_PROGRESS: 0.2,
                RecommendationStatus.IMPLEMENTED: 0.3,
                RecommendationStatus.REJECTED: 0.1,
            }
        
        recommendations = []
        recommendation_types = list(RecommendationType)
        
        for i in range(count):
            # Select recommendation type
            rec_type = random.choice(recommendation_types)
            
            # Select status based on distribution
            status = random.choices(
                list(status_distribution.keys()),
                weights=list(status_distribution.values())
            )[0]
            
            # Generate recommendation
            recommendation = self._create_recommendation(
                api_id=api_id,
                recommendation_type=rec_type,
                status=status,
                index=i
            )
            
            # Save to database
            created = self.recommendation_repo.create_recommendation(recommendation)
            recommendations.append(created)
            logger.info(
                f"Created {rec_type.value} recommendation "
                f"(status: {status.value}, priority: {recommendation.priority.value})"
            )
        
        return recommendations
    
    def _create_recommendation(
        self,
        api_id: str,
        recommendation_type: RecommendationType,
        status: RecommendationStatus,
        index: int
    ) -> OptimizationRecommendation:
        """Create a single recommendation with realistic data."""
        
        # Priority based on type
        priority_map = {
            RecommendationType.QUERY_OPTIMIZATION: RecommendationPriority.CRITICAL,
            RecommendationType.CACHING: RecommendationPriority.HIGH,
            RecommendationType.CONNECTION_POOLING: RecommendationPriority.HIGH,
            RecommendationType.RESOURCE_ALLOCATION: RecommendationPriority.MEDIUM,
            RecommendationType.COMPRESSION: RecommendationPriority.LOW,
            RecommendationType.RATE_LIMITING: RecommendationPriority.MEDIUM,
        }
        
        priority = priority_map.get(recommendation_type, RecommendationPriority.MEDIUM)
        
        # Generate type-specific data
        type_data = self._get_type_specific_data(recommendation_type)
        
        # Base recommendation
        # Build recommendation dict
        rec_dict = {
            "id": str(uuid4()),
            "api_id": api_id,
            "recommendation_type": recommendation_type,
            "priority": priority,
            "title": type_data["title"],
            "description": type_data["description"],
            "estimated_impact": type_data["estimated_impact"],
            "implementation_steps": type_data["implementation_steps"],
            "implementation_effort": type_data["effort"],
            "status": status,
            "cost_savings": type_data.get("cost_savings", random.uniform(500, 5000)),
            "created_at": datetime.utcnow() - timedelta(days=random.randint(1, 30)),
            "updated_at": datetime.utcnow(),
            "metadata": {"current_metrics": type_data["current_metrics"]},
        }
        
        # Add status-specific fields
        if status in [RecommendationStatus.IN_PROGRESS, RecommendationStatus.IMPLEMENTED]:
            rec_dict["implemented_at"] = datetime.utcnow() - timedelta(
                days=random.randint(1, 14)
            )
        
        recommendation = OptimizationRecommendation(**rec_dict)
        
        return recommendation
    
    def _get_type_specific_data(self, rec_type: RecommendationType) -> dict:
        """Get type-specific recommendation data."""
        
        data_map = {
            RecommendationType.CACHING: {
                "title": "Implement Redis caching for frequently accessed data",
                "description": "Add caching layer to reduce database load and improve response times for read-heavy endpoints. Current cache hit rate is 0%, indicating no caching is in place.",
                "current_metrics": {
                    "avg_response_time_ms": random.uniform(400, 600),
                    "p95_response_time_ms": random.uniform(800, 1200),
                    "requests_per_minute": random.uniform(150, 250),
                    "cache_hit_rate": 0.0,
                },
                "estimated_impact": EstimatedImpact(
                    metric="response_time_p95",
                    current_value=random.uniform(800, 1200),
                    expected_value=random.uniform(300, 500),
                    improvement_percentage=random.uniform(50, 70),
                    confidence=random.uniform(0.85, 0.95),
                ),
                "implementation_steps": [
                    "Set up Redis cluster",
                    "Identify cacheable GET endpoints",
                    "Implement cache-aside pattern",
                    "Configure TTL based on data volatility",
                    "Add cache invalidation logic",
                    "Monitor cache hit rates and memory usage",
                ],
                "effort": ImplementationEffort.HIGH,
                "cost_savings": random.uniform(2000, 5000),
            },
            RecommendationType.QUERY_OPTIMIZATION: {
                "title": "Optimize database queries with missing indexes",
                "description": "Add database indexes and optimize N+1 query patterns causing performance bottlenecks. Slow query analysis shows multiple queries taking over 1 second.",
                "current_metrics": {
                    "avg_response_time_ms": random.uniform(1000, 1500),
                    "p95_response_time_ms": random.uniform(2000, 3000),
                    "requests_per_minute": random.uniform(60, 100),
                    "slow_query_count": random.randint(30, 60),
                },
                "estimated_impact": EstimatedImpact(
                    metric="response_time_p95",
                    current_value=random.uniform(2000, 3000),
                    expected_value=random.uniform(500, 800),
                    improvement_percentage=random.uniform(65, 80),
                    confidence=random.uniform(0.90, 0.98),
                ),
                "implementation_steps": [
                    "Analyze slow query logs",
                    "Identify missing indexes",
                    "Create composite indexes for common queries",
                    "Refactor N+1 queries to use joins",
                    "Add query result pagination",
                    "Monitor query execution times",
                ],
                "effort": ImplementationEffort.HIGH,
                "cost_savings": random.uniform(3000, 7000),
            },
            RecommendationType.RESOURCE_ALLOCATION: {
                "title": "Adjust resource allocation based on usage patterns",
                "description": "Right-size container resources and implement auto-scaling for cost optimization. Current resource utilization shows over-provisioning.",
                "current_metrics": {
                    "avg_cpu_usage": random.uniform(20, 35),
                    "avg_memory_usage": random.uniform(35, 50),
                    "peak_cpu_usage": random.uniform(60, 75),
                    "peak_memory_usage": random.uniform(70, 85),
                },
                "estimated_impact": EstimatedImpact(
                    metric="cost_per_request",
                    current_value=random.uniform(0.04, 0.06),
                    expected_value=random.uniform(0.025, 0.035),
                    improvement_percentage=random.uniform(30, 40),
                    confidence=random.uniform(0.85, 0.92),
                ),
                "implementation_steps": [
                    "Analyze resource utilization patterns",
                    "Right-size container CPU and memory",
                    "Configure horizontal pod autoscaling",
                    "Set up resource requests and limits",
                    "Implement cost monitoring",
                ],
                "effort": ImplementationEffort.MEDIUM,
                "cost_savings": random.uniform(1500, 4000),
            },
            RecommendationType.COMPRESSION: {
                "title": "Enable response compression for large payloads",
                "description": "Implement gzip/brotli compression to reduce bandwidth and improve transfer speeds. Current responses are uncompressed.",
                "current_metrics": {
                    "avg_response_size_kb": random.uniform(400, 500),
                    "bandwidth_usage_gb": random.uniform(100, 150),
                    "compression_enabled": False,
                },
                "estimated_impact": EstimatedImpact(
                    metric="bandwidth_usage",
                    current_value=random.uniform(100, 150),
                    expected_value=random.uniform(60, 90),
                    improvement_percentage=random.uniform(35, 45),
                    confidence=random.uniform(0.88, 0.94),
                ),
                "implementation_steps": [
                    "Enable gzip compression middleware",
                    "Configure compression thresholds",
                    "Test with various content types",
                    "Monitor compression ratios",
                    "Measure bandwidth savings",
                ],
                "effort": ImplementationEffort.LOW,
                "cost_savings": random.uniform(800, 2000),
            },
            RecommendationType.CONNECTION_POOLING: {
                "title": "Optimize database connection pooling",
                "description": "Configure connection pool settings to reduce connection overhead and improve concurrency. Current pool is undersized.",
                "current_metrics": {
                    "avg_connection_time_ms": random.uniform(70, 100),
                    "active_connections": random.randint(12, 18),
                    "max_connections": 20,
                    "connection_errors": random.randint(8, 15),
                },
                "estimated_impact": EstimatedImpact(
                    metric="connection_time_ms",
                    current_value=random.uniform(70, 100),
                    expected_value=random.uniform(40, 60),
                    improvement_percentage=random.uniform(25, 35),
                    confidence=random.uniform(0.82, 0.90),
                ),
                "implementation_steps": [
                    "Analyze connection pool metrics",
                    "Increase pool size based on load",
                    "Configure connection timeout settings",
                    "Implement connection retry logic",
                    "Monitor pool utilization",
                ],
                "effort": ImplementationEffort.MEDIUM,
                "cost_savings": random.uniform(1000, 2500),
            },
            RecommendationType.RATE_LIMITING: {
                "title": "Implement adaptive rate limiting",
                "description": "Add rate limiting to protect against traffic spikes and abuse. Current API has no rate limiting.",
                "current_metrics": {
                    "peak_requests_per_minute": random.uniform(300, 500),
                    "avg_requests_per_minute": random.uniform(150, 250),
                    "rate_limit_enabled": False,
                },
                "estimated_impact": EstimatedImpact(
                    metric="availability",
                    current_value=99.5,
                    expected_value=99.9,
                    improvement_percentage=random.uniform(15, 25),
                    confidence=random.uniform(0.80, 0.88),
                ),
                "implementation_steps": [
                    "Define rate limit policies",
                    "Implement rate limiting middleware",
                    "Configure limits per endpoint",
                    "Add rate limit headers",
                    "Monitor rate limit violations",
                ],
                "effort": ImplementationEffort.MEDIUM,
                "cost_savings": random.uniform(500, 1500),
            },
        }
        
        return data_map.get(rec_type, data_map[RecommendationType.CACHING])
    
    async def generate_for_all_apis(
        self,
        recommendations_per_api: int = 3
    ) -> dict:
        """
        Generate recommendations for all APIs in the system.
        
        Args:
            recommendations_per_api: Number of recommendations per API
            
        Returns:
            Dictionary mapping API IDs to their recommendations
        """
        # Get all APIs
        apis, total = self.api_repo.search(query={"match_all": {}}, size=100)
        
        if not apis:
            logger.warning("No APIs found. Please create APIs first.")
            return {}
        
        results = {}
        for api in apis:
            logger.info(f"Generating recommendations for API: {api.name}")
            recommendations = await self.generate_recommendations(
                api_id=str(api.id),
                count=recommendations_per_api
            )
            results[str(api.id)] = recommendations
        
        return results


async def main():
    """Main entry point for mock data generation."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate mock optimization recommendation data"
    )
    parser.add_argument(
        "--api-id",
        help="Generate recommendations for specific API ID"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of recommendations to generate per API (default: 5)"
    )
    parser.add_argument(
        "--all-apis",
        action="store_true",
        help="Generate recommendations for all APIs"
    )
    
    args = parser.parse_args()
    
    generator = MockOptimizationGenerator()
    
    try:
        if args.api_id:
            # Generate for specific API
            logger.info(f"Generating {args.count} recommendations for API {args.api_id}")
            recommendations = await generator.generate_recommendations(
                api_id=args.api_id,
                count=args.count
            )
            logger.info(f"Successfully created {len(recommendations)} recommendations")
            
        elif args.all_apis:
            # Generate for all APIs
            logger.info("Generating recommendations for all APIs")
            results = await generator.generate_for_all_apis(
                recommendations_per_api=args.count
            )
            total = sum(len(recs) for recs in results.values())
            logger.info(
                f"Successfully created {total} recommendations "
                f"across {len(results)} APIs"
            )
            
        else:
            logger.error("Please specify --api-id or --all-apis")
            parser.print_help()
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error generating mock data: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
