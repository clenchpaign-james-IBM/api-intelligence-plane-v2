#!/usr/bin/env python3
"""
Test script to verify the complete query flow end-to-end.
This helps debug issues with query processing and LLM integration.
"""

import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from uuid import uuid4
from app.config import Settings
from app.services.llm_service import LLMService
from app.services.query_service import QueryService
from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository


async def test_llm_service():
    """Test LLM service directly."""
    print("\n" + "="*80)
    print("STEP 1: Testing LLM Service")
    print("="*80)
    
    settings = Settings()
    llm_service = LLMService(settings)
    
    print(f"\nLLM Provider: {settings.LLM_PROVIDER}")
    print(f"LLM Model: {settings.LLM_MODEL}")
    print(f"Ollama URL: {settings.OLLAMA_BASE_URL}")
    print(f"Number of providers configured: {len(llm_service.providers)}")
    
    if llm_service.providers:
        print("\nConfigured providers:")
        for i, provider in enumerate(llm_service.providers, 1):
            print(f"  {i}. Model: {provider['model']}")
            print(f"     API Base: {provider.get('api_base', 'default')}")
    
    # Test simple completion
    print("\nTesting simple LLM completion...")
    try:
        response = await llm_service.generate_completion(
            messages=[{"role": "user", "content": "Say 'Hello, World!' and nothing else."}],
            system_prompt="You are a helpful assistant.",
            temperature=0.1,
            max_tokens=50,
        )
        print(f"✅ LLM Response: {response['content']}")
        print(f"   Model used: {response['model']}")
        print(f"   Tokens: {response['usage']['total_tokens']}")
        return True
    except Exception as e:
        print(f"❌ LLM Error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_query_service():
    """Test query service with a sample query."""
    print("\n" + "="*80)
    print("STEP 2: Testing Query Service")
    print("="*80)
    
    settings = Settings()
    
    # Initialize repositories
    query_repo = QueryRepository()
    api_repo = APIRepository()
    metrics_repo = MetricsRepository()
    prediction_repo = PredictionRepository()
    recommendation_repo = RecommendationRepository()
    llm_service = LLMService(settings)
    
    # Initialize query service
    query_service = QueryService(
        query_repository=query_repo,
        api_repository=api_repo,
        metrics_repository=metrics_repo,
        prediction_repository=prediction_repo,
        recommendation_repository=recommendation_repo,
        llm_service=llm_service,
    )
    
    # Test query
    test_query = "which apis are down?"
    print(f"\nProcessing query: '{test_query}'")
    
    try:
        result = await query_service.process_query(
            query_text=test_query,
            session_id=uuid4(),
            user_id="test-user",
        )
        
        print(f"\n✅ Query processed successfully!")
        print(f"   Query ID: {result.id}")
        print(f"   Query Type: {result.query_type}")
        print(f"   Confidence: {result.confidence_score:.2f}")
        print(f"   Execution Time: {result.execution_time_ms}ms")
        print(f"   Results Count: {result.results.count}")
        print(f"\n   Response Text:")
        print(f"   {'-'*76}")
        print(f"   {result.response_text}")
        print(f"   {'-'*76}")
        
        if result.follow_up_queries:
            print(f"\n   Follow-up suggestions:")
            for i, suggestion in enumerate(result.follow_up_queries, 1):
                print(f"   {i}. {suggestion}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Query processing error: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("QUERY FLOW TEST SUITE")
    print("="*80)
    
    # Test LLM service
    llm_ok = await test_llm_service()
    
    if not llm_ok:
        print("\n⚠️  LLM service test failed. Query service will use fallback responses.")
    
    # Test query service
    query_ok = await test_query_service()
    
    # Summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"LLM Service: {'✅ PASS' if llm_ok else '❌ FAIL'}")
    print(f"Query Service: {'✅ PASS' if query_ok else '❌ FAIL'}")
    print("="*80 + "\n")
    
    return 0 if (llm_ok and query_ok) else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

# Made with Bob
