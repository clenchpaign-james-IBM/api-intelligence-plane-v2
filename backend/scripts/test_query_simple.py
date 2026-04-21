"""
Simple Query Service Test

Tests a few basic queries to validate functionality.
"""

import asyncio
import sys
from uuid import uuid4

sys.path.insert(0, '/Users/clenchpaign/projects/bobathon/api-intelligence-plane-v2/backend')

from app.services.query_service import QueryService
from app.services.llm_service import LLMService
from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.config import settings


# Simple test queries
TEST_QUERIES = [
    "Show me all APIs",
    "List active APIs",
    "Show all gateways",
    "Show API metrics",
    "Show all vulnerabilities",
    "Show recent predictions",
    "Show optimization recommendations",
    "Show compliance violations",
]


async def test_queries():
    """Test basic queries."""
    print("\n" + "=" * 80)
    print("SIMPLE QUERY SERVICE TEST")
    print("=" * 80)
    print(f"\nInitializing services...")
    
    # Initialize repositories
    query_repo = QueryRepository()
    api_repo = APIRepository()
    metrics_repo = MetricsRepository()
    prediction_repo = PredictionRepository()
    recommendation_repo = RecommendationRepository()
    compliance_repo = ComplianceRepository()
    gateway_repo = GatewayRepository()
    vulnerability_repo = VulnerabilityRepository()
    transactional_log_repo = TransactionalLogRepository()
    
    print("✓ Repositories initialized")
    
    # Initialize LLM service
    llm_service = LLMService(settings)
    print("✓ LLM service initialized")
    
    # Initialize query service
    query_service = QueryService(
        query_repository=query_repo,
        api_repository=api_repo,
        metrics_repository=metrics_repo,
        prediction_repository=prediction_repo,
        recommendation_repository=recommendation_repo,
        llm_service=llm_service,
        compliance_repository=compliance_repo,
        gateway_repository=gateway_repo,
        vulnerability_repository=vulnerability_repo,
        transactional_log_repository=transactional_log_repo,
    )
    print("✓ Query service initialized")
    
    session_id = uuid4()
    print(f"✓ Session ID: {session_id}")
    
    print(f"\n{'=' * 80}")
    print(f"Testing {len(TEST_QUERIES)} queries...")
    print("=" * 80 + "\n")
    
    results = []
    for i, query in enumerate(TEST_QUERIES, 1):
        print(f"{i}. Testing: '{query}'")
        try:
            result = await query_service.process_query(
                session_id=session_id,
                query_text=query
            )
            
            success = result.results.count >= 0
            print(f"   ✓ Success - Found {result.results.count} results in {result.execution_time_ms}ms")
            print(f"   Query type: {result.query_type}")
            print(f"   Entities: {result.interpreted_intent.entities}")
            
            results.append({
                "query": query,
                "success": True,
                "count": result.results.count,
                "time_ms": result.execution_time_ms,
            })
        except Exception as e:
            print(f"   ✗ Failed: {str(e)[:100]}")
            results.append({
                "query": query,
                "success": False,
                "error": str(e),
            })
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    total = len(results)
    successful = sum(1 for r in results if r["success"])
    failed = total - successful
    success_rate = (successful / total * 100) if total > 0 else 0
    
    print(f"\nTotal: {total}")
    print(f"Successful: {successful} ({success_rate:.1f}%)")
    print(f"Failed: {failed}")
    
    if failed > 0:
        print("\nFailed queries:")
        for r in results:
            if not r["success"]:
                print(f"  - {r['query']}")
                print(f"    Error: {r.get('error', 'Unknown')[:100]}")
    
    print("\n" + "=" * 80)
    
    return success_rate >= 90.0


async def main():
    """Main function."""
    try:
        success = await test_queries()
        if success:
            print("\n✓ TEST PASSED: Query service working correctly")
            sys.exit(0)
        else:
            print("\n✗ TEST FAILED: Query service below 90% success rate")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ TEST ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
