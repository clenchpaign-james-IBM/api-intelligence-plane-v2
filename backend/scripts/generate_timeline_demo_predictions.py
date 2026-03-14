#!/usr/bin/env python3
"""
Generate predictions distributed over 72 hours for timeline demonstration.
Includes overdue, current, and future predictions.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4
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
)


async def main():
    """Generate predictions distributed over 72 hours."""
    print("Generating Timeline Demo Predictions")
    print("=" * 70)
    
    # Initialize
    prediction_repo = PredictionRepository()
    api_repo = APIRepository()
    client = get_client()
    
    # Clear old predictions
    print("\n1. Clearing old predictions...")
    try:
        result = client.delete_by_query(
            index='api-predictions',
            body={'query': {'match_all': {}}},
            conflicts='proceed'
        )
        print(f"   Deleted {result.get('deleted', 0)} old predictions")
        client.indices.refresh(index='api-predictions')
    except Exception as e:
        print(f"   Note: {e}")
    
    # Get APIs
    print("\n2. Fetching APIs...")
    apis, total = api_repo.search(query={"match_all": {}}, size=100)
    print(f"   Found {total} APIs")
    
    if not apis:
        print("   No APIs found. Please run generate_mock_data.py first.")
        return
    
    # Generate predictions distributed over 72 hours
    print("\n3. Generating predictions distributed over 72 hours...")
    print("   (Including overdue, current, and future predictions)")
    
    now = datetime.utcnow()
    total_generated = 0
    
    # Time ranges for distribution
    time_ranges = [
        ("Overdue (-24h to -12h)", -24, -12, 8),
        ("Overdue (-12h to -2h)", -12, -2, 6),
        ("Near Future (2h to 12h)", 2, 12, 10),
        ("Mid Future (12h to 24h)", 12, 24, 8),
        ("Far Future (24h to 48h)", 24, 48, 10),
        ("Extended Future (48h to 72h)", 48, 72, 8),
    ]
    
    api_index = 0
    for range_name, start_hours, end_hours, count in time_ranges:
        print(f"\n   {range_name}:")
        
        for i in range(count):
            # Select API (cycle through available APIs)
            api = apis[api_index % len(apis)]
            api_index += 1
            
            # Random severity
            severity = random.choices(
                [PredictionSeverity.CRITICAL, PredictionSeverity.HIGH, 
                 PredictionSeverity.MEDIUM, PredictionSeverity.LOW],
                weights=[0.15, 0.30, 0.35, 0.20]
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
            
            # Confidence
            if severity == PredictionSeverity.CRITICAL:
                confidence = random.uniform(0.9, 1.0)
            elif severity == PredictionSeverity.HIGH:
                confidence = random.uniform(0.8, 0.9)
            elif severity == PredictionSeverity.MEDIUM:
                confidence = random.uniform(0.7, 0.8)
            else:
                confidence = random.uniform(0.5, 0.7)
            
            # Calculate times
            # predicted_time is when the event is expected to occur
            hours_offset = random.uniform(start_hours, end_hours)
            predicted_time = now + timedelta(hours=hours_offset)
            
            # predicted_at must be 24-48 hours before predicted_time (model validation)
            hours_before = random.uniform(24, 48)
            predicted_at = predicted_time - timedelta(hours=hours_before)
            
            # Status based on whether it's overdue
            if hours_offset < 0:
                # Overdue - mix of statuses
                status = random.choice([
                    PredictionStatus.ACTIVE,
                    PredictionStatus.RESOLVED,
                    PredictionStatus.FALSE_POSITIVE
                ])
            else:
                status = PredictionStatus.ACTIVE
            
            # Contributing factors
            factors = [
                ContributingFactor(
                    factor="increasing_error_rate",
                    current_value=random.uniform(0.05, 0.25),
                    threshold=0.10,
                    trend="increasing",
                    weight=round(confidence * 0.4, 3)
                ),
                ContributingFactor(
                    factor="degrading_response_time",
                    current_value=random.uniform(200, 800),
                    threshold=500.0,
                    trend="increasing",
                    weight=round(confidence * 0.35, 3)
                ),
                ContributingFactor(
                    factor="memory_usage_spike",
                    current_value=random.uniform(70, 95),
                    threshold=80.0,
                    trend="volatile",
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
                predicted_at=predicted_at,
                predicted_time=predicted_time,
                confidence_score=confidence,
                severity=severity,
                status=status,
                contributing_factors=factors,
                recommended_actions=random.sample(actions, 3),
                actual_outcome=None,
                actual_time=None,
                accuracy_score=None,
                model_version="1.0.0",
                metadata={"generated": True, "demo": True}
            )
            
            # Save
            prediction_repo.create(prediction)
            total_generated += 1
            
            print(f"      [{i+1}/{count}] {severity.value:8} | {hours_offset:6.1f}h | {api.name}")
    
    print(f"\n{'=' * 70}")
    print(f"✓ Successfully generated {total_generated} predictions")
    print(f"  Distributed over 72 hours (-24h to +72h from now)")
    print(f"  Includes overdue, current, and future predictions")
    print(f"{'=' * 70}\n")


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
