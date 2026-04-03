"""
Test script for compliance query integration.

Tests that compliance queries work with the natural language query interface.
"""

import asyncio
import logging
from uuid import uuid4

from app.config import Settings
from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.services.query_service import QueryService
from app.services.llm_service import LLMService
from app.agents.compliance_agent import ComplianceAgent

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_compliance_query():
    """Test compliance query processing."""
    
    # Initialize services
    settings = Settings()
    query_repo = QueryRepository()
    api_repo = APIRepository()
    metrics_repo = MetricsRepository()
    prediction_repo = PredictionRepository()
    recommendation_repo = RecommendationRepository()
    compliance_repo = ComplianceRepository()
    llm_service = LLMService(settings)
    
    # Initialize compliance agent
    compliance_agent = None
    try:
        compliance_agent = ComplianceAgent(
            llm_service=llm_service,
            metrics_repository=metrics_repo,
        )
        logger.info("ComplianceAgent initialized successfully")
    except Exception as e:
        logger.warning(f"Failed to initialize ComplianceAgent: {e}")
    
    # Initialize query service
    query_service = QueryService(
        query_repository=query_repo,
        api_repository=api_repo,
        metrics_repository=metrics_repo,
        prediction_repository=prediction_repo,
        recommendation_repository=recommendation_repo,
        llm_service=llm_service,
        compliance_agent=compliance_agent,
        compliance_repository=compliance_repo,
    )
    
    # Test queries
    test_queries = [
        "Show me all compliance violations",
        "What are the GDPR compliance issues?",
        "Show me critical compliance violations",
        "Which APIs have HIPAA violations?",
        "Show me compliance violations from the last week",
    ]
    
    session_id = uuid4()
    
    for query_text in test_queries:
        logger.info(f"\n{'='*80}")
        logger.info(f"Testing query: {query_text}")
        logger.info(f"{'='*80}")
        
        try:
            # Process query
            result = await query_service.process_query(
                query_text=query_text,
                session_id=session_id,
            )
            
            logger.info(f"Query Type: {result.query_type}")
            logger.info(f"Confidence: {result.confidence_score}")
            logger.info(f"Results Count: {result.results.count}")
            logger.info(f"Execution Time: {result.execution_time_ms}ms")
            logger.info(f"Response: {result.response_text[:200]}...")
            
            if result.follow_up_queries:
                logger.info(f"Follow-up suggestions:")
                for i, follow_up in enumerate(result.follow_up_queries, 1):
                    logger.info(f"  {i}. {follow_up}")
            
            # Check if compliance agent insights are present
            if result.results.data:
                for item in result.results.data[:1]:
                    if isinstance(item, dict) and "agent_insights" in item:
                        insights = item["agent_insights"]
                        logger.info(f"Agent Insights Type: {insights.get('type')}")
                        if insights.get('type') == 'compliance':
                            logger.info(f"  Compliance Score: {insights.get('compliance_score')}")
                            logger.info(f"  Total Violations: {insights.get('total_violations')}")
                            logger.info(f"  Critical Count: {insights.get('critical_count')}")
            
            logger.info("✓ Query processed successfully")
            
        except Exception as e:
            logger.error(f"✗ Query failed: {e}", exc_info=True)
    
    logger.info(f"\n{'='*80}")
    logger.info("Compliance query testing complete!")
    logger.info(f"{'='*80}")


if __name__ == "__main__":
    asyncio.run(test_compliance_query())

# Made with Bob
