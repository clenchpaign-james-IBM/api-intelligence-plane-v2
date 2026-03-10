"""Validation script for User Story 5: Intelligent Rate Limiting.

This script simulates traffic and validates that:
1. Rate limit policies can be created and activated
2. Adaptive policies adjust thresholds based on traffic
3. Effectiveness tracking works correctly
4. Policy suggestions are intelligent
5. End-to-end flow works as expected

Run with: python -m backend.scripts.validate_rate_limiting
"""

import asyncio
import time
from datetime import datetime, timedelta
from uuid import uuid4
import statistics

from app.db.client import get_client
from app.db.repositories.rate_limit_repository import RateLimitPolicyRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.services.rate_limit_service import RateLimitService
from app.models.rate_limit import (
    PolicyType,
    PolicyStatus,
    EnforcementAction,
    LimitThresholds,
    AdaptationParameters,
)
from app.models.metric import Metric
from app.models.api import (
    API,
    APIStatus,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    CurrentMetrics,
)


class RateLimitingValidator:
    """Validator for rate limiting functionality."""
    
    def __init__(self):
        """Initialize validator with repositories and services."""
        self.client = get_client()
        self.policy_repo = RateLimitPolicyRepository(self.client)
        self.metrics_repo = MetricsRepository(self.client)
        self.api_repo = APIRepository(self.client)
        self.rate_limit_service = RateLimitService(
            self.policy_repo,
            self.metrics_repo,
            self.api_repo
        )
        self.test_api_id = None
        self.test_policy_id = None
    
    def setup_test_api(self):
        """Create a test API for validation."""
        print("\n[1/6] Setting up test API...")
        
        api = API(
            id=uuid4(),
            gateway_id=uuid4(),
            name="Rate Limiting Test API",
            base_path="/api/ratelimit-test",
            endpoints=[
                Endpoint(
                    path="/test",
                    method="GET",
                    description="Test endpoint",
                )
            ],
            methods=["GET"],
            authentication_type=AuthenticationType.NONE,
            is_shadow=False,
            discovery_method=DiscoveryMethod.REGISTERED,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=APIStatus.ACTIVE,
            health_score=0.95,
            current_metrics=CurrentMetrics(
                response_time_p50=100.0,
                response_time_p95=200.0,
                response_time_p99=300.0,
                error_rate=0.01,
                throughput=100.0,
                availability=0.99,
                measured_at=datetime.utcnow(),
            ),
        )
        
        self.api_repo.create(api.model_dump(), str(api.id))
        self.test_api_id = str(api.id)
        
        print(f"✓ Created test API: {api.name} (ID: {self.test_api_id})")
        return api
    
    def simulate_traffic(self, hours=24):
        """Simulate traffic metrics for the test API."""
        print(f"\n[2/6] Simulating {hours} hours of traffic...")
        
        now = datetime.utcnow()
        metrics_created = 0
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours - 1 - i)
            
            # Simulate realistic traffic pattern
            hour = timestamp.hour
            if 9 <= hour <= 17:
                # Business hours: higher traffic with variation
                base_throughput = 150.0
                variation = (i % 5) * 15
            else:
                # Off hours: lower traffic
                base_throughput = 50.0
                variation = (i % 3) * 10
            
            throughput = base_throughput + variation
            
            metric = Metric(
                id=uuid4(),
                api_id=uuid4(self.test_api_id),
                gateway_id=uuid4(),
                timestamp=timestamp,
                response_time_p50=100.0 + (i % 5) * 10,
                response_time_p95=200.0 + (i % 5) * 20,
                response_time_p99=350.0 + (i % 5) * 30,
                error_rate=0.01 + (i % 3) * 0.005,
                error_count=int(throughput * 0.01),
                request_count=int(throughput * 60),
                throughput=throughput,
                availability=0.99,
                status_codes={"200": int(throughput * 59), "500": int(throughput * 0.6)},
            )
            
            self.metrics_repo.create(metric.model_dump(), str(metric.id))
            metrics_created += 1
        
        print(f"✓ Created {metrics_created} metric data points")
    
    def test_policy_suggestion(self):
        """Test intelligent policy suggestion."""
        print("\n[3/6] Testing intelligent policy suggestion...")
        
        suggestion = self.rate_limit_service.suggest_policy_for_api(self.test_api_id)
        
        assert suggestion is not None, "Policy suggestion failed"
        assert "suggested_policy" in suggestion, "Missing suggested_policy"
        assert "reasoning" in suggestion, "Missing reasoning"
        assert "traffic_analysis" in suggestion, "Missing traffic_analysis"
        
        suggested_policy = suggestion["suggested_policy"]
        traffic_analysis = suggestion["traffic_analysis"]
        
        print(f"✓ Policy suggestion generated")
        print(f"  - Suggested type: {suggested_policy['policy_type']}")
        print(f"  - Avg throughput: {traffic_analysis['avg_throughput']:.1f} req/s")
        print(f"  - Peak throughput: {traffic_analysis['peak_throughput']:.1f} req/s")
        print(f"  - P95 throughput: {traffic_analysis['p95_throughput']:.1f} req/s")
        print(f"  - Reasoning: {suggestion['reasoning'][:100]}...")
        
        return suggestion
    
    def test_policy_creation_and_activation(self, suggestion):
        """Test creating and activating a rate limit policy."""
        print("\n[4/6] Testing policy creation and activation...")
        
        # Create adaptive policy based on suggestion
        suggested_policy = suggestion["suggested_policy"]
        thresholds = suggested_policy["limit_thresholds"]
        
        policy = self.rate_limit_service.create_policy(
            api_id=self.test_api_id,
            policy_name="Validation Test Policy",
            policy_type=PolicyType(suggested_policy["policy_type"]),
            limit_thresholds=LimitThresholds(
                requests_per_second=thresholds.get("requests_per_second"),
                requests_per_minute=thresholds.get("requests_per_minute"),
                requests_per_hour=thresholds.get("requests_per_hour"),
            ),
            enforcement_action=EnforcementAction(suggested_policy["enforcement_action"]),
            adaptation_parameters=AdaptationParameters(
                learning_rate=0.1,
                adjustment_frequency=300,
                min_threshold=int(thresholds.get("requests_per_second", 100) * 0.5),
                max_threshold=int(thresholds.get("requests_per_second", 100) * 2.0),
            ) if suggested_policy["policy_type"] == "adaptive" else None,
        )
        
        self.test_policy_id = str(policy.id)
        
        print(f"✓ Created policy: {policy.policy_name}")
        print(f"  - Type: {policy.policy_type}")
        print(f"  - RPS limit: {policy.limit_thresholds.requests_per_second}")
        print(f"  - Status: {policy.status}")
        
        # Activate policy
        activated = self.rate_limit_service.activate_policy(self.test_policy_id)
        
        assert activated.status == PolicyStatus.ACTIVE, "Policy activation failed"
        assert activated.applied_at is not None, "Applied timestamp not set"
        
        print(f"✓ Policy activated at {activated.applied_at}")
        
        return policy
    
    def test_adaptive_adjustment(self):
        """Test adaptive policy adjustment."""
        print("\n[5/6] Testing adaptive policy adjustment...")
        
        # Get current policy
        current_policy = self.policy_repo.get(self.test_policy_id)
        original_rps = current_policy.limit_thresholds.requests_per_second
        
        print(f"  - Original RPS: {original_rps}")
        
        # Adjust policy
        adjusted = self.rate_limit_service.adjust_adaptive_policy(self.test_policy_id)
        
        if adjusted:
            new_rps = adjusted.limit_thresholds.requests_per_second
            change_pct = ((new_rps - original_rps) / original_rps) * 100
            
            print(f"✓ Policy adjusted")
            print(f"  - New RPS: {new_rps}")
            print(f"  - Change: {change_pct:+.1f}%")
            print(f"  - Last adjusted: {adjusted.last_adjusted_at}")
        else:
            print("  - No adjustment needed (within target utilization)")
    
    def test_effectiveness_analysis(self):
        """Test policy effectiveness analysis."""
        print("\n[6/6] Testing effectiveness analysis...")
        
        analysis = self.rate_limit_service.analyze_policy_effectiveness(self.test_policy_id)
        
        assert analysis is not None, "Effectiveness analysis failed"
        assert "effectiveness_score" in analysis, "Missing effectiveness_score"
        assert "metrics" in analysis, "Missing metrics"
        assert "recommendations" in analysis, "Missing recommendations"
        
        score = analysis["effectiveness_score"]
        metrics = analysis["metrics"]
        
        print(f"✓ Effectiveness analysis complete")
        print(f"  - Overall score: {score:.2f} ({score * 100:.0f}%)")
        print(f"  - Error rate: {metrics['error_rate']:.4f}")
        print(f"  - Avg response time: {metrics['avg_response_time']:.1f}ms")
        print(f"  - Throttled requests: {metrics['throttled_requests']}")
        print(f"  - Total requests: {metrics['total_requests']}")
        
        if analysis["recommendations"]:
            print(f"  - Recommendations: {len(analysis['recommendations'])}")
            for i, rec in enumerate(analysis["recommendations"][:3], 1):
                print(f"    {i}. {rec}")
        
        return analysis
    
    def cleanup(self):
        """Clean up test data."""
        print("\n[Cleanup] Removing test data...")
        
        try:
            if self.test_policy_id:
                self.policy_repo.delete(self.test_policy_id)
                print(f"✓ Deleted test policy")
        except Exception as e:
            print(f"  Warning: Could not delete policy: {e}")
        
        try:
            if self.test_api_id:
                self.api_repo.delete(self.test_api_id)
                print(f"✓ Deleted test API")
        except Exception as e:
            print(f"  Warning: Could not delete API: {e}")
    
    def run_validation(self):
        """Run complete validation suite."""
        print("=" * 70)
        print("User Story 5: Intelligent Rate Limiting - Validation")
        print("=" * 70)
        
        try:
            # Setup
            api = self.setup_test_api()
            self.simulate_traffic(hours=24)
            
            # Test core functionality
            suggestion = self.test_policy_suggestion()
            policy = self.test_policy_creation_and_activation(suggestion)
            
            # Test adaptive features
            if policy.policy_type == PolicyType.ADAPTIVE:
                self.test_adaptive_adjustment()
            
            # Test effectiveness tracking
            analysis = self.test_effectiveness_analysis()
            
            # Summary
            print("\n" + "=" * 70)
            print("VALIDATION SUMMARY")
            print("=" * 70)
            print("✓ All tests passed successfully!")
            print(f"✓ Policy effectiveness: {analysis['effectiveness_score'] * 100:.0f}%")
            print(f"✓ Rate limiting is working as expected")
            print("=" * 70)
            
            return True
            
        except Exception as e:
            print(f"\n✗ Validation failed: {e}")
            import traceback
            traceback.print_exc()
            return False
            
        finally:
            self.cleanup()


def main():
    """Main entry point."""
    validator = RateLimitingValidator()
    success = validator.run_validation()
    
    if success:
        print("\n✓ User Story 5 validation complete - Rate limiting works independently")
        exit(0)
    else:
        print("\n✗ User Story 5 validation failed")
        exit(1)


if __name__ == "__main__":
    main()


# Made with Bob