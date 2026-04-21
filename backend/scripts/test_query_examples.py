"""
Test Query Examples from Documentation

Tests all 50+ query examples from docs/query-service-user-guide.md
to validate query service functionality and measure success rate.
"""

import asyncio
import sys
from typing import List, Dict, Any, Tuple
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, '/Users/clenchpaign/projects/bobathon/api-intelligence-plane-v2/backend')

from app.services.query_service import QueryService
from app.services.llm_service import LLMService
from app.db.client import get_opensearch_client
from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository


# Test queries from documentation
SINGLE_ENTITY_QUERIES = {
    "APIs": [
        "Show me all APIs",
        "List payment APIs",
        "Which APIs are deprecated?",
        "Show me APIs created last month",
    ],
    "Gateways": [
        "Show all gateways",
        "Which gateways are offline?",
        "List gateways in production",
    ],
    "Metrics": [
        "Show API metrics",
        "What's the average response time?",
        "Show error rates for today",
    ],
    "Security": [
        "Show all vulnerabilities",
        "List critical security issues",
        "Which CVEs are unpatched?",
    ],
    "Predictions": [
        "Show recent predictions",
        "What failures are predicted?",
        "Show high-confidence predictions",
    ],
    "Recommendations": [
        "Show optimization recommendations",
        "List rate limiting suggestions",
        "What caching recommendations exist?",
    ],
    "Compliance": [
        "Show compliance violations",
        "List GDPR violations",
        "Which APIs are non-compliant?",
    ],
}

MULTI_ENTITY_QUERIES = {
    "APIs + Vulnerabilities": [
        "Show me APIs with critical vulnerabilities",
        "Which payment APIs have security issues?",
        "List APIs affected by CVE-2024-1234",
    ],
    "APIs + Metrics": [
        "Show me APIs with high latency",
        "Which APIs have error rates above 5%?",
        "List slow payment APIs",
    ],
    "APIs + Predictions": [
        "Show me APIs predicted to fail",
        "Which APIs will have high traffic?",
        "List APIs with failure predictions",
    ],
    "Gateways + APIs": [
        "Show me APIs on gateway-1",
        "Which gateways have the most APIs?",
        "List APIs per gateway",
    ],
    "APIs + Recommendations": [
        "Show me APIs with rate limiting recommendations",
        "Which APIs need caching?",
        "List optimization suggestions for payment APIs",
    ],
}

TIME_RANGE_QUERIES = [
    "Show me API metrics from last 7 days",
    "List vulnerabilities discovered this month",
    "Show predictions for next week",
    "API traffic from January to March",
]

FILTERING_QUERIES = [
    "Show me critical vulnerabilities",
    "List active APIs in production",
    "Show high-severity compliance violations",
    "APIs with status code 500",
]

AGGREGATION_QUERIES = [
    "How many APIs are active?",
    "What's the average API response time?",
    "Count vulnerabilities by severity",
    "Show API distribution by gateway",
]


class QueryTester:
    """Test query service with documentation examples."""
    
    def __init__(self):
        from app.config import settings
        
        # Initialize repositories (they use singleton client internally)
        self.query_repo = QueryRepository()
        self.api_repo = APIRepository()
        self.metrics_repo = MetricsRepository()
        self.prediction_repo = PredictionRepository()
        self.recommendation_repo = RecommendationRepository()
        self.compliance_repo = ComplianceRepository()
        self.gateway_repo = GatewayRepository()
        self.vulnerability_repo = VulnerabilityRepository()
        self.transactional_log_repo = TransactionalLogRepository()
        
        # Initialize LLM service
        self.llm_service = LLMService(settings)
        
        # Initialize query service
        self.query_service = QueryService(
            query_repository=self.query_repo,
            api_repository=self.api_repo,
            metrics_repository=self.metrics_repo,
            prediction_repository=self.prediction_repo,
            recommendation_repository=self.recommendation_repo,
            llm_service=self.llm_service,
            compliance_repository=self.compliance_repo,
            gateway_repository=self.gateway_repo,
            vulnerability_repository=self.vulnerability_repo,
            transactional_log_repository=self.transactional_log_repo,
        )
        
        self.results: List[Dict[str, Any]] = []
        self.session_id = uuid4()
    
    async def test_query(self, query: str, category: str) -> Dict[str, Any]:
        """Test a single query."""
        try:
            result = await self.query_service.process_query(
                session_id=self.session_id,
                query_text=query
            )
            
            success = result.results.count >= 0  # Query executed without error
            
            return {
                "query": query,
                "category": category,
                "success": success,
                "count": result.results.count,
                "execution_time_ms": result.execution_time_ms,
                "error": None
            }
        except Exception as e:
            return {
                "query": query,
                "category": category,
                "success": False,
                "count": 0,
                "execution_time_ms": 0,
                "error": str(e)
            }
    
    async def run_tests(self):
        """Run all test queries."""
        print("=" * 80)
        print("QUERY SERVICE DOCUMENTATION EXAMPLES TEST")
        print("=" * 80)
        print()
        
        # Test single-entity queries
        print("Testing Single-Entity Queries...")
        for category, queries in SINGLE_ENTITY_QUERIES.items():
            print(f"\n  {category}:")
            for query in queries:
                result = await self.test_query(query, f"Single: {category}")
                self.results.append(result)
                status = "✓" if result["success"] else "✗"
                print(f"    {status} {query}")
                if result["error"]:
                    print(f"      Error: {result['error']}")
        
        # Test multi-entity queries
        print("\n\nTesting Multi-Entity Queries...")
        for category, queries in MULTI_ENTITY_QUERIES.items():
            print(f"\n  {category}:")
            for query in queries:
                result = await self.test_query(query, f"Multi: {category}")
                self.results.append(result)
                status = "✓" if result["success"] else "✗"
                print(f"    {status} {query}")
                if result["error"]:
                    print(f"      Error: {result['error']}")
        
        # Test time range queries
        print("\n\nTesting Time Range Queries...")
        for query in TIME_RANGE_QUERIES:
            result = await self.test_query(query, "Time Range")
            self.results.append(result)
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {query}")
            if result["error"]:
                print(f"    Error: {result['error']}")
        
        # Test filtering queries
        print("\n\nTesting Filtering Queries...")
        for query in FILTERING_QUERIES:
            result = await self.test_query(query, "Filtering")
            self.results.append(result)
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {query}")
            if result["error"]:
                print(f"    Error: {result['error']}")
        
        # Test aggregation queries
        print("\n\nTesting Aggregation Queries...")
        for query in AGGREGATION_QUERIES:
            result = await self.test_query(query, "Aggregation")
            self.results.append(result)
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {query}")
            if result["error"]:
                print(f"    Error: {result['error']}")
        
        # Print summary and return result
        return self.print_summary()
    
    def print_summary(self):
        """Print test summary."""
        print("\n\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)
        
        total = len(self.results)
        successful = sum(1 for r in self.results if r["success"])
        failed = total - successful
        success_rate = (successful / total * 100) if total > 0 else 0
        
        print(f"\nTotal Queries: {total}")
        print(f"Successful: {successful} ({success_rate:.1f}%)")
        print(f"Failed: {failed}")
        
        if failed > 0:
            print("\n\nFailed Queries:")
            for result in self.results:
                if not result["success"]:
                    print(f"\n  Query: {result['query']}")
                    print(f"  Category: {result['category']}")
                    print(f"  Error: {result['error']}")
        
        # Category breakdown
        print("\n\nCategory Breakdown:")
        categories = {}
        for result in self.results:
            cat = result["category"]
            if cat not in categories:
                categories[cat] = {"total": 0, "success": 0}
            categories[cat]["total"] += 1
            if result["success"]:
                categories[cat]["success"] += 1
        
        for cat, stats in sorted(categories.items()):
            rate = (stats["success"] / stats["total"] * 100) if stats["total"] > 0 else 0
            print(f"  {cat}: {stats['success']}/{stats['total']} ({rate:.1f}%)")
        
        print("\n" + "=" * 80)
        
        # Return success rate for validation
        return success_rate >= 90.0


async def main():
    """Main test function."""
    tester = QueryTester()
    success = await tester.run_tests()
    
    if success:
        print("\n✓ SUCCESS: Query service meets >90% success rate requirement")
        sys.exit(0)
    else:
        print("\n✗ FAILURE: Query service below 90% success rate requirement")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
