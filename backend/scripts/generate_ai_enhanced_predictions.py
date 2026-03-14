#!/usr/bin/env python3
"""
Generate AI-Enhanced Predictions

This script generates predictions using the AI-enhanced mode (with LLM analysis)
and saves them to the database.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.db.client import OpenSearchClient
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.services.llm_service import LLMService
from app.services.prediction_service import PredictionService
from app.models.prediction import Prediction, PredictionStatus
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Generate AI-enhanced predictions for all APIs."""
    logger.info("Starting AI-enhanced prediction generation...")
    
    # Initialize services
    settings = Settings()
    
    api_repo = APIRepository()
    metrics_repo = MetricsRepository()
    pred_repo = PredictionRepository()
    llm_service = LLMService(settings)
    
    pred_service = PredictionService(
        prediction_repository=pred_repo,
        metrics_repository=metrics_repo,
        api_repository=api_repo,
        llm_service=llm_service
    )
    
    # Get all APIs
    apis, total = api_repo.list_all(size=100)
    logger.info(f"Found {len(apis)} APIs to analyze")
    
    total_predictions = 0
    successful_apis = 0
    failed_apis = 0
    
    for api in apis:
        try:
            logger.info(f"\nProcessing API: {api.name} ({api.id})")
            
            # Generate AI-enhanced predictions
            result = await pred_service.generate_ai_enhanced_predictions(
                api_id=api.id,
                min_confidence=0.5
            )
            
            if result.get('error'):
                logger.warning(f"  Error: {result['error']}")
                failed_apis += 1
                continue
            
            predictions_data = result.get('predictions', [])
            logger.info(f"  Generated {len(predictions_data)} predictions")
            
            # Save predictions to database
            for pred_data in predictions_data:
                try:
                    # Create Prediction object from dict
                    # Store LLM explanation in metadata
                    metadata = pred_data.get('metadata', {})
                    if pred_data.get('llm_explanation'):
                        metadata['ai_explanation'] = pred_data['llm_explanation']
                    
                    prediction = Prediction(
                        id=pred_data['id'],
                        api_id=pred_data['api_id'],
                        api_name=api.name,
                        prediction_type=pred_data['prediction_type'],
                        predicted_at=datetime.fromisoformat(pred_data['predicted_at']),
                        predicted_time=datetime.fromisoformat(pred_data['predicted_time']),
                        confidence_score=pred_data['confidence_score'],
                        severity=pred_data['severity'],
                        status=pred_data.get('status', PredictionStatus.ACTIVE.value),
                        contributing_factors=pred_data.get('contributing_factors', []),
                        recommended_actions=pred_data.get('recommended_actions', []),
                        actual_outcome=None,
                        actual_time=None,
                        accuracy_score=None,
                        model_version=pred_data.get('model_version', '1.0.0'),
                        metadata=metadata
                    )
                    
                    # Save to database
                    pred_repo.create(prediction)
                    total_predictions += 1
                    logger.info(f"    Saved prediction: {prediction.prediction_type} "
                              f"(confidence: {prediction.confidence_score:.2%}, "
                              f"severity: {prediction.severity})")
                    
                except Exception as e:
                    logger.error(f"    Failed to save prediction: {e}")
            
            successful_apis += 1
            
        except Exception as e:
            logger.error(f"  Failed to process API {api.name}: {e}")
            failed_apis += 1
    
    logger.info(f"\n{'='*60}")
    logger.info(f"AI-Enhanced Prediction Generation Complete!")
    logger.info(f"{'='*60}")
    logger.info(f"Total APIs: {len(apis)}")
    logger.info(f"Successful: {successful_apis}")
    logger.info(f"Failed: {failed_apis}")
    logger.info(f"Total Predictions Generated: {total_predictions}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
