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
        
        # Priority based on type (only gateway-observable recommendations)
        priority_map = {
            RecommendationType.CACHING: RecommendationPriority.HIGH,
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
        
        # Multiple variations for each recommendation type
        caching_variations = [
            {
                "title": "Enable Response Caching Policy",
                "description": "Configure gateway-level caching policy to reduce response times for read-heavy endpoints. Current P95 response time is high and no caching policy is enabled.",
                "steps": [
                    "Configure gateway caching policy for this API",
                    "Set cache TTL based on data freshness requirements (e.g., 5-60 minutes)",
                    "Define cache key strategy (URL, headers, query parameters)",
                    "Configure cache invalidation rules",
                    "Monitor cache hit rates and adjust policy as needed",
                ],
            },
            {
                "title": "Configure Cache-Control Headers",
                "description": "Implement proper Cache-Control headers at the gateway level to enable browser and CDN caching. Current responses lack caching directives.",
                "steps": [
                    "Add Cache-Control headers to gateway responses",
                    "Set appropriate max-age values for different endpoints",
                    "Configure ETag generation for conditional requests",
                    "Implement Vary headers for content negotiation",
                    "Test caching behavior across different clients",
                ],
            },
            {
                "title": "Optimize Cache TTL Strategy",
                "description": "Fine-tune cache TTL values at the gateway to balance freshness and performance. Current cache policy uses suboptimal TTL values.",
                "steps": [
                    "Analyze data volatility patterns per endpoint",
                    "Adjust cache TTL values in gateway policy",
                    "Implement stale-while-revalidate strategy",
                    "Configure cache warming for critical endpoints",
                    "Monitor cache effectiveness metrics",
                ],
            },
        ]
        
        compression_variations = [
            {
                "title": "Enable Response Compression Policy",
                "description": "Configure gateway compression to reduce bandwidth usage and improve transfer speeds. Current responses are uncompressed.",
                "steps": [
                    "Enable gzip/brotli compression in gateway policy",
                    "Set minimum response size threshold (e.g., 1KB)",
                    "Configure compression level (balance speed vs ratio)",
                    "Test compression with various content types",
                    "Monitor bandwidth savings and CPU impact",
                ],
            },
            {
                "title": "Optimize Compression Settings",
                "description": "Fine-tune gateway compression settings for optimal performance. Current compression policy uses default settings.",
                "steps": [
                    "Adjust compression level based on content type",
                    "Configure selective compression for specific endpoints",
                    "Enable Brotli for modern clients",
                    "Set appropriate compression thresholds",
                    "Measure compression ratio improvements",
                ],
            },
            {
                "title": "Enable Selective Content Compression",
                "description": "Configure gateway to compress only appropriate content types. Current policy compresses all responses indiscriminately.",
                "steps": [
                    "Define compressible content types (JSON, XML, HTML, CSS, JS)",
                    "Exclude already-compressed formats (images, video)",
                    "Configure compression based on Accept-Encoding headers",
                    "Implement compression bypass for small responses",
                    "Monitor compression effectiveness per content type",
                ],
            },
        ]
        
        rate_limiting_variations = [
            {
                "title": "Implement Rate Limiting Policy",
                "description": "Configure gateway rate limiting to protect against traffic spikes and abuse. Current API has no rate limiting.",
                "steps": [
                    "Define rate limit thresholds per endpoint",
                    "Configure rate limiting policy in gateway",
                    "Set up rate limit response headers (X-RateLimit-*)",
                    "Implement different limits for authenticated vs anonymous users",
                    "Monitor rate limit violations and adjust as needed",
                ],
            },
            {
                "title": "Configure Adaptive Rate Limiting",
                "description": "Implement dynamic rate limiting that adjusts based on system load. Current static limits don't account for capacity changes.",
                "steps": [
                    "Configure adaptive rate limiting in gateway",
                    "Set baseline and maximum rate limits",
                    "Define load-based adjustment triggers",
                    "Implement gradual limit reduction under high load",
                    "Monitor system capacity and rate limit effectiveness",
                ],
            },
            {
                "title": "Optimize Rate Limit Granularity",
                "description": "Fine-tune rate limiting rules at the gateway for better protection. Current limits are too coarse-grained.",
                "steps": [
                    "Implement per-endpoint rate limits",
                    "Configure different limits for read vs write operations",
                    "Set up tiered limits based on user roles",
                    "Add burst allowance for legitimate traffic spikes",
                    "Review and adjust limits based on usage patterns",
                ],
            },
        ]
        
        # Select random variation based on type
        if rec_type == RecommendationType.CACHING:
            variation = random.choice(caching_variations)
        elif rec_type == RecommendationType.COMPRESSION:
            variation = random.choice(compression_variations)
        elif rec_type == RecommendationType.RATE_LIMITING:
            variation = random.choice(rate_limiting_variations)
        else:
            variation = caching_variations[0]
        
        # Build common data structure
        return {
            "title": variation["title"],
            "description": variation["description"],
            "current_metrics": {
                "avg_response_time_ms": random.uniform(400, 600),
                "p95_response_time_ms": random.uniform(800, 1200),
                "requests_per_minute": random.uniform(150, 250),
            },
            "estimated_impact": EstimatedImpact(
                metric="response_time_p95" if rec_type == RecommendationType.CACHING else "bandwidth_usage" if rec_type == RecommendationType.COMPRESSION else "availability",
                current_value=random.uniform(800, 1200) if rec_type == RecommendationType.CACHING else random.uniform(100, 150) if rec_type == RecommendationType.COMPRESSION else 99.5,
                expected_value=random.uniform(300, 500) if rec_type == RecommendationType.CACHING else random.uniform(60, 90) if rec_type == RecommendationType.COMPRESSION else 99.9,
                improvement_percentage=random.uniform(50, 70) if rec_type == RecommendationType.CACHING else random.uniform(35, 45) if rec_type == RecommendationType.COMPRESSION else random.uniform(15, 25),
                confidence=random.uniform(0.85, 0.95),
            ),
            "implementation_steps": variation["steps"],
            "effort": ImplementationEffort.LOW if rec_type in [RecommendationType.CACHING, RecommendationType.COMPRESSION] else ImplementationEffort.MEDIUM,
            "cost_savings": random.uniform(2000, 5000) if rec_type == RecommendationType.CACHING else random.uniform(800, 2000) if rec_type == RecommendationType.COMPRESSION else random.uniform(500, 1500),
        }
    
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
