#!/usr/bin/env python3
"""
Clear old predictions and generate fresh ones with current timestamps.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4, UUID
import random

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_client
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.api_repository import APIRepository
from app.models.prediction import (
    Prediction,
    PredictionType,
    PredictionSeverity,
    PredictionStatus,
    ContributingFactor,
    ContributingFactorType,
)


async def main():
    """Clear old predictions and generate fresh ones."""
    print("Clearing old predictions and generating fresh data...")
    print("=" * 60)
    
    # Initialize repositories
    prediction_repo = PredictionRepository()
    api_repo = APIRepository()
    client = get_client()
    
    # Step 1: Delete all existing predictions
    print("\n1. Deleting old predictions...")
    try:
        result = client.delete_by_query(
            index='api-predictions',
            body={'query': {'match_all': {}}},
            refresh=True
        )
        deleted = result.get('deleted', 0)
        print(f"   Deleted {deleted} old predictions")
    except Exception as e:
        print(f"   Note: {e}")
    
    # Step 2: Get APIs
    print("\n2. Fetching APIs...")
    try:
        apis, total = api_repo.search(query={"match_all": {}}, size=100)
        print(f"   Found {total} APIs")
    except Exception as e:
        print(f"   Error: {e}")
        return
    
    if not apis:
        print("   No APIs found. Please run generate_mock_data.py first.")
        return
    
    # Step 3: Generate fresh predictions
    print("\n3. Generating fresh predictions...")
    now = datetime.utcnow()
    total_generated = 0
    
    for api in apis[:10]:  # Limit to first 10 APIs
        count = random.randint(3, 8)
        print(f"\n   API: {api.name}")
        
        for i in range(count):
            # Random severity distribution
            severity = random.choices(
                [PredictionSeverity.CRITICAL, PredictionSeverity.HIGH, 
                 PredictionSeverity.MEDIUM, PredictionSeverity.LOW],
                weights=[0.1, 0.3, 0.4, 0.2]
            )[0]
            
            # Prediction type based on severity
            if severity == PredictionSeverity.CRITICAL:
                pred_type = PredictionType.FAILURE
            elif severity == PredictionSeverity.HIGH:
                pred_type = random.choice([PredictionType.FAILURE, PredictionType.DEGRADATION])
            else:
                pred_type = random.choice([
                    PredictionType.DEGRADATION,
                    PredictionType.CAPACITY,
                    PredictionType.SECURITY
                ])
            
            # Confidence based on severity
            if severity == PredictionSeverity.CRITICAL:
                confidence = random.uniform(0.9, 1.0)
            elif severity == PredictionSeverity.HIGH:
                confidence = random.uniform(0.8, 0.9)
            elif severity == PredictionSeverity.MEDIUM:
                confidence = random.uniform(0.7, 0.8)
            else:
                confidence = random.uniform(0.5, 0.7)
            
            # Predicted time: 24-48 hours from now (as per model validation)
            hours_ahead = random.uniform(24, 48)
            predicted_time = now + timedelta(hours=hours_ahead)
            
            # Contributing factors
            factors = [
                ContributingFactor(
                    factor=ContributingFactorType.INCREASING_ERROR_RATE,
                    current_value=random.uniform(0.05, 0.25),
                    threshold=0.10,
                    trend="increasing",
                    weight=round(confidence * 0.4, 3)
                ),
                ContributingFactor(
                    factor=ContributingFactorType.DEGRADING_RESPONSE_TIME,
                    current_value=random.uniform(200, 800),
                    threshold=500.0,
                    trend="increasing",
                    weight=round(confidence * 0.35, 3)
                ),
                ContributingFactor(
                    factor=ContributingFactorType.HIGH_LATENCY_UNDER_LOAD,
                    current_value=random.uniform(70, 95),
                    threshold=80.0,
                    trend="increasing",
                    weight=round(confidence * 0.25, 3)
                )
            ]
            
            # Recommended actions
            actions = [
                "Monitor performance metrics closely",
                "Review recent code deployments",
                "Scale up infrastructure if needed",
                "Enable circuit breaker patterns"
            ]
            
            # Create prediction
            prediction = Prediction(
                id=uuid4(),
                api_id=api.id,
                api_name=api.name,
                prediction_type=pred_type,
                predicted_at=now,
                predicted_time=predicted_time,
                confidence_score=confidence,
                severity=severity,
                status=PredictionStatus.ACTIVE,
                contributing_factors=factors,
                recommended_actions=random.sample(actions, 3),
                actual_outcome=None,
                actual_time=None,
                accuracy_score=None,
                model_version="1.0.0",
                metadata={"generated": True, "fresh": True}
            )
            
            # Save to database
            prediction_repo.create(prediction)
            total_generated += 1
            
            print(f"      [{i+1}/{count}] {severity.value} - {hours_ahead:.1f}h ahead")
    
    print(f"\n{'=' * 60}")
    print(f"✓ Successfully generated {total_generated} fresh predictions")
    print(f"  All predictions are scheduled 2-48 hours in the future")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
