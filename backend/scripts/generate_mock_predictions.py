#!/usr/bin/env python3
"""
Mock Prediction Data Generator

Generates realistic prediction data for testing and development purposes.
Creates predictions with various severities, confidence scores, and contributing factors.
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta
from uuid import uuid4, UUID
from typing import List
import random

# Add parent directory to path for imports
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


class MockPredictionGenerator:
    """Generates mock prediction data for testing."""
    
    def __init__(self):
        self.prediction_repo = PredictionRepository()
        self.api_repo = APIRepository()
    
    async def generate_predictions(
        self,
        api_id: str,
        count: int = 10,
        severity_distribution: dict | None = None
    ) -> List[Prediction]:
        """
        Generate mock predictions for an API.
        
        Args:
            api_id: Target API ID
            count: Number of predictions to generate
            severity_distribution: Distribution of severities (default: balanced)
        
        Returns:
            List of generated predictions
        """
        if severity_distribution is None:
            severity_distribution = {
                PredictionSeverity.CRITICAL: 0.1,
                PredictionSeverity.HIGH: 0.3,
                PredictionSeverity.MEDIUM: 0.4,
                PredictionSeverity.LOW: 0.2,
            }
        
        predictions = []
        now = datetime.utcnow()
        
        for i in range(count):
            # Determine severity based on distribution
            severity = self._choose_severity(severity_distribution)
            
            # Generate prediction
            prediction = self._create_prediction(
                api_id=api_id,
                severity=severity,
                predicted_at=now - timedelta(hours=random.randint(0, 48)),
            )
            
            # Store in OpenSearch
            created = self.prediction_repo.create(prediction)
            predictions.append(created)
            
            print(f"Generated prediction {i+1}/{count}: {severity.value} severity")
        
        return predictions
    
    def _choose_severity(self, distribution: dict) -> PredictionSeverity:
        """Choose severity based on distribution."""
        rand = random.random()
        cumulative = 0.0
        
        for severity, probability in distribution.items():
            cumulative += probability
            if rand <= cumulative:
                return severity
        
        return PredictionSeverity.LOW
    
    def _create_prediction(
        self,
        api_id: str,
        severity: PredictionSeverity,
        predicted_at: datetime
    ) -> Prediction:
        """Create a single mock prediction."""
        # Determine prediction type based on severity
        if severity == PredictionSeverity.CRITICAL:
            prediction_type = PredictionType.FAILURE
        elif severity == PredictionSeverity.HIGH:
            prediction_type = random.choice([PredictionType.FAILURE, PredictionType.DEGRADATION])
        else:
            prediction_type = random.choice([
                PredictionType.DEGRADATION,
                PredictionType.CAPACITY,
                PredictionType.SECURITY
            ])
        
        # Calculate confidence based on severity
        if severity == PredictionSeverity.CRITICAL:
            confidence = random.uniform(0.9, 1.0)
        elif severity == PredictionSeverity.HIGH:
            confidence = random.uniform(0.8, 0.9)
        elif severity == PredictionSeverity.MEDIUM:
            confidence = random.uniform(0.7, 0.8)
        else:
            confidence = random.uniform(0.5, 0.7)
        
        # Generate contributing factors
        factors = self._generate_contributing_factors(severity, confidence)
        
        # Generate recommended actions
        actions = self._generate_recommended_actions(prediction_type, factors)
        
        # Predicted time: 24-48 hours from predicted_at
        predicted_time = predicted_at + timedelta(
            hours=random.uniform(24, 48)
        )
        
        # Determine status
        status = random.choice([
            PredictionStatus.ACTIVE,
            PredictionStatus.ACTIVE,
            PredictionStatus.ACTIVE,
            PredictionStatus.RESOLVED,
        ])
        
        return Prediction(
            id=uuid4(),
            api_id=uuid4() if api_id == "random" else UUID(api_id) if isinstance(api_id, str) else api_id,
            prediction_type=prediction_type,
            predicted_at=predicted_at,
            predicted_time=predicted_time,
            confidence_score=confidence,
            severity=severity,
            status=status,
            contributing_factors=factors,
            recommended_actions=actions,
            actual_outcome=None,
            actual_time=None,
            accuracy_score=None,
            model_version="1.0.0",
            metadata={
                "generated": True,
                "generator": "mock_prediction_generator",
            },
        )
    
    def _generate_contributing_factors(
        self,
        severity: PredictionSeverity,
        confidence: float
    ) -> List[ContributingFactor]:
        """Generate realistic contributing factors."""
        factor_templates = [
            {
                "factor": "increasing_error_rate",
                "current_value": lambda: random.uniform(0.05, 0.25),
                "threshold": 0.10,
                "trend": "increasing",
            },
            {
                "factor": "degrading_response_time",
                "current_value": lambda: random.uniform(200, 800),
                "threshold": 500.0,
                "trend": "increasing",
            },
            {
                "factor": "decreasing_availability",
                "current_value": lambda: random.uniform(90, 98),
                "threshold": 95.0,
                "trend": "decreasing",
            },
            {
                "factor": "memory_usage_spike",
                "current_value": lambda: random.uniform(70, 95),
                "threshold": 80.0,
                "trend": "increasing",
            },
            {
                "factor": "cpu_utilization_high",
                "current_value": lambda: random.uniform(60, 90),
                "threshold": 75.0,
                "trend": "volatile",
            },
        ]
        
        # Number of factors based on severity
        if severity == PredictionSeverity.CRITICAL:
            num_factors = random.randint(3, 5)
        elif severity == PredictionSeverity.HIGH:
            num_factors = random.randint(2, 4)
        else:
            num_factors = random.randint(1, 3)
        
        selected_templates = random.sample(factor_templates, min(num_factors, len(factor_templates)))
        
        factors = []
        remaining_confidence = confidence
        
        for i, template in enumerate(selected_templates):
            # Distribute confidence across factors
            if i == len(selected_templates) - 1:
                weight = remaining_confidence
            else:
                weight = random.uniform(0.1, remaining_confidence * 0.5)
                remaining_confidence -= weight
            
            factor = ContributingFactor(
                factor=template["factor"],
                current_value=template["current_value"](),
                threshold=template["threshold"],
                trend=template["trend"],
                weight=round(weight, 3),
            )
            factors.append(factor)
        
        # Sort by weight descending
        factors.sort(key=lambda f: f.weight, reverse=True)
        
        return factors
    
    def _generate_recommended_actions(
        self,
        prediction_type: PredictionType,
        factors: List[ContributingFactor]
    ) -> List[str]:
        """Generate recommended actions based on prediction type and factors."""
        actions = []
        
        # Type-specific actions
        if prediction_type == PredictionType.FAILURE:
            actions.extend([
                "Immediately review error logs and identify root cause",
                "Scale up infrastructure resources to handle increased load",
                "Enable circuit breaker to prevent cascade failures",
            ])
        elif prediction_type == PredictionType.DEGRADATION:
            actions.extend([
                "Monitor performance metrics closely for next 24 hours",
                "Review recent code deployments for performance regressions",
                "Consider implementing caching layer to reduce load",
            ])
        elif prediction_type == PredictionType.CAPACITY:
            actions.extend([
                "Plan capacity increase within next 48 hours",
                "Review auto-scaling policies and thresholds",
                "Analyze traffic patterns to optimize resource allocation",
            ])
        else:  # SECURITY
            actions.extend([
                "Review security logs for suspicious activity",
                "Update security policies and access controls",
                "Run security scan to identify vulnerabilities",
            ])
        
        # Factor-specific actions
        for factor in factors[:2]:  # Top 2 factors
            if "error_rate" in factor.factor:
                actions.append("Investigate error patterns and implement retry logic")
            elif "response_time" in factor.factor:
                actions.append("Optimize database queries and API calls")
            elif "availability" in factor.factor:
                actions.append("Check health of dependent services")
            elif "memory" in factor.factor:
                actions.append("Investigate memory leaks and optimize memory usage")
            elif "cpu" in factor.factor:
                actions.append("Profile CPU usage and optimize hot code paths")
        
        # Return unique actions
        return list(set(actions))[:5]  # Max 5 actions


async def main():
    """Main entry point for mock data generation."""
    generator = MockPredictionGenerator()
    
    print("Mock Prediction Data Generator")
    print("=" * 50)
    
    # Get all APIs using search with match_all query
    try:
        apis, total = generator.api_repo.search(query={"match_all": {}}, size=100)
    except Exception as e:
        print(f"Error fetching APIs: {e}")
        print("Using sample API IDs for demonstration")
        apis = []
        total = 0
    
    if not apis:
        print("No APIs found. Please run generate_mock_data.py first.")
        return
    
    print(f"Found {total} APIs")
    print()
    
    # Generate predictions for each API
    for api in apis[:5]:  # Limit to first 5 APIs
        print(f"Generating predictions for API: {api.name}")
        
        # Generate 5-10 predictions per API
        count = random.randint(5, 10)
        predictions = await generator.generate_predictions(
            api_id=str(api.id),
            count=count
        )
        
        print(f"Generated {len(predictions)} predictions")
        print()
    
    print("Mock prediction data generation complete!")


if __name__ == "__main__":
    asyncio.run(main())


# Made with Bob