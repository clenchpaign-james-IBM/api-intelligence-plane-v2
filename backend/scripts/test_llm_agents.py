#!/usr/bin/env python3
"""
LLM Agent Validation Script

Tests that AI-enhanced prediction and optimization agents work correctly.
"""

import asyncio
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.services.llm_service import LLMService
from app.services.prediction_service import PredictionService
from app.services.optimization_service import OptimizationService
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.models.base.metric import Metric
from datetime import datetime, timedelta
from uuid import uuid4


async def test_llm_connection():
    """Test basic LLM connection."""
    print("\n=== Testing LLM Connection ===")
    
    try:
        settings = Settings()
        llm_service = LLMService(settings)
        
        result = await llm_service.test_connection()
        
        print(f"✓ Total providers configured: {result['total_providers']}")
        for provider_result in result['results']:
            status = "✓" if provider_result['status'] == 'success' else "✗"
            print(f"{status} {provider_result['model']}: {provider_result['status']}")
            if provider_result['status'] == 'failed':
                print(f"  Error: {provider_result['error']}")
        
        return any(r['status'] == 'success' for r in result['results'])
        
    except Exception as e:
        print(f"✗ LLM connection test failed: {e}")
        return False


async def test_prediction_agent():
    """Test PredictionAgent functionality."""
    print("\n=== Testing Prediction Agent ===")
    
    try:
        # Initialize services
        settings = Settings()
        llm_service = LLMService(settings)
        
        prediction_repo = PredictionRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        
        prediction_service = PredictionService(
            prediction_repository=prediction_repo,
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            llm_service=llm_service,
        )
        
        # Create mock metrics
        api_id = uuid4()
        mock_metrics = [
            Metric(
                id=uuid4(),
                api_id=api_id,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                response_time_p50=100 + i * 10,
                response_time_p95=200 + i * 20,
                response_time_p99=300 + i * 30,
                error_rate=0.01 + i * 0.001,
                throughput=100 - i,
                availability=99.9 - i * 0.1,
            )
            for i in range(20)
        ]
        
        # Test AI-enhanced prediction generation
        print("Testing AI-enhanced prediction generation...")
        
        # Import agent directly
        from app.agents.prediction_agent import PredictionAgent, LANGGRAPH_AVAILABLE
        
        if not LANGGRAPH_AVAILABLE:
            print("⚠ LangGraph not available - using direct execution mode")
        
        agent = PredictionAgent(
            llm_service=llm_service,
            prediction_service=prediction_service,
        )
        
        result = await agent.generate_enhanced_predictions(
            api_id=api_id,
            api_name="test-api",
            metrics=mock_metrics,
        )
        
        if 'error' in result:
            print(f"✗ Prediction agent failed: {result['error']}")
            return False
        
        print(f"✓ Generated analysis: {result.get('analysis', 'N/A')[:100]}...")
        print(f"✓ Predictions generated: {len(result.get('predictions', []))}")
        
        return True
        
    except Exception as e:
        print(f"✗ Prediction agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_optimization_agent():
    """Test OptimizationAgent functionality."""
    print("\n=== Testing Optimization Agent ===")
    
    try:
        # Initialize services
        settings = Settings()
        llm_service = LLMService(settings)
        
        recommendation_repo = RecommendationRepository()
        metrics_repo = MetricsRepository()
        api_repo = APIRepository()
        
        optimization_service = OptimizationService(
            recommendation_repository=recommendation_repo,
            metrics_repository=metrics_repo,
            api_repository=api_repo,
            llm_service=llm_service,
        )
        
        # Create mock metrics
        api_id = uuid4()
        mock_metrics = [
            Metric(
                id=uuid4(),
                api_id=api_id,
                timestamp=datetime.utcnow() - timedelta(hours=i),
                response_time_p50=150 + i * 5,
                response_time_p95=300 + i * 10,
                response_time_p99=500 + i * 15,
                error_rate=0.02 + i * 0.001,
                throughput=80 - i,
                availability=99.5 - i * 0.05,
            )
            for i in range(20)
        ]
        
        # Test AI-enhanced recommendation generation
        print("Testing AI-enhanced recommendation generation...")
        
        # Import agent directly
        from app.agents.optimization_agent import OptimizationAgent, LANGGRAPH_AVAILABLE
        
        if not LANGGRAPH_AVAILABLE:
            print("⚠ LangGraph not available - using direct execution mode")
        
        agent = OptimizationAgent(
            llm_service=llm_service,
            optimization_service=optimization_service,
        )
        
        result = await agent.generate_enhanced_recommendations(
            api_id=api_id,
            api_name="test-api",
            metrics=mock_metrics,
        )
        
        if 'error' in result:
            print(f"✗ Optimization agent failed: {result['error']}")
            return False
        
        print(f"✓ Generated performance analysis: {result.get('performance_analysis', 'N/A')[:100]}...")
        print(f"✓ Recommendations generated: {len(result.get('recommendations', []))}")
        print(f"✓ Prioritization guidance: {result.get('prioritization', 'N/A')[:100]}...")
        
        return True
        
    except Exception as e:
        print(f"✗ Optimization agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all agent validation tests."""
    print("=" * 60)
    print("LLM Agent Validation")
    print("=" * 60)
    
    results = {}
    
    # Test LLM connection
    results['llm_connection'] = await test_llm_connection()
    
    if not results['llm_connection']:
        print("\n⚠ LLM connection failed - agents will use fallback mode")
        print("  Set LLM_API_KEY in .env to enable AI features")
    
    # Test agents (they should work even without LLM via fallback)
    results['prediction_agent'] = await test_prediction_agent()
    results['optimization_agent'] = await test_optimization_agent()
    
    # Summary
    print("\n" + "=" * 60)
    print("Validation Summary")
    print("=" * 60)
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n✓ All agent validation tests passed!")
        return 0
    else:
        print("\n✗ Some agent validation tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)

# Made with Bob
