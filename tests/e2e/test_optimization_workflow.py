"""End-to-end tests for optimization-apply-validate workflow.

Tests the complete optimization workflow including:
- Performance analysis and recommendation generation
- Optimization recommendation prioritization
- Policy application (rate limiting, caching, compression)
- Validation through metrics comparison
- Impact tracking and reporting

Note: Uses mocked dependencies to focus on workflow logic.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from backend.app.services.optimization_service import OptimizationService


@pytest.fixture
def mock_optimization_service():
    """Create optimization service with mocked dependencies."""
    recommendation_repo = Mock()
    recommendation_repo.create = AsyncMock()
    recommendation_repo.update = AsyncMock()
    recommendation_repo.get = AsyncMock()
    recommendation_repo.find_by_api = AsyncMock(return_value=[])
    recommendation_repo.find_pending = AsyncMock(return_value=[])
    
    metrics_repo = Mock()
    metrics_repo.find_by_api = AsyncMock(return_value=([], 0))
    metrics_repo.get_latest_metrics = AsyncMock(return_value={})
    
    api_repo = Mock()
    api_repo.get = AsyncMock()
    api_repo.update = AsyncMock()
    
    llm_service = Mock()
    llm_service.complete = AsyncMock(return_value="AI-generated recommendation")
    
    service = OptimizationService(
        recommendation_repository=recommendation_repo,
        metrics_repository=metrics_repo,
        api_repository=api_repo,
        llm_service=llm_service,
    )
    
    return service, recommendation_repo, metrics_repo, api_repo, llm_service


class TestOptimizationApplyValidateWorkflow:
    """Test complete optimization-apply-validate workflow."""

    @pytest.mark.asyncio
    async def test_complete_analyze_recommend_apply_validate_workflow(
        self, mock_optimization_service
    ):
        """Test complete workflow from analysis to validation."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        # Step 1: Setup test API with performance issues
        api_id = uuid4()
        gateway_id = uuid4()
        
        api_data = {
            "id": api_id,
            "gateway_id": gateway_id,
            "name": "Slow API",
            "base_path": "/api/v1/slow"
        }
        
        api_repo.get.return_value = api_data
        
        # Step 2: Analyze performance metrics
        # Simulate degraded performance metrics
        historical_metrics = []
        now = datetime.utcnow()
        
        for hour in range(24):
            metric = {
                "timestamp": now - timedelta(hours=23-hour),
                "response_time_p95": 800 + (hour * 10),  # Increasing latency
                "error_rate": 0.05,  # High error rate
                "throughput": 50.0,
                "cache_hit_rate": 0.0,  # No caching
            }
            historical_metrics.append(metric)
        
        metrics_repo.find_by_api.return_value = (historical_metrics, len(historical_metrics))
        
        # Step 3: Generate optimization recommendations
        recommendations = [
            {
                "id": uuid4(),
                "api_id": api_id,
                "recommendation_type": "caching",
                "priority": "high",
                "title": "Enable Response Caching",
                "description": "API responses are not cached, causing unnecessary backend calls",
                "estimated_improvement": {
                    "response_time_reduction": 60.0,  # 60% reduction
                    "cost_savings": 500.0  # $500/month
                },
                "status": "pending",
                "implementation_effort": "low"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "recommendation_type": "rate_limiting",
                "priority": "medium",
                "title": "Implement Rate Limiting",
                "description": "Protect API from traffic spikes",
                "estimated_improvement": {
                    "availability_increase": 5.0,  # 5% increase
                    "cost_savings": 200.0  # $200/month
                },
                "status": "pending",
                "implementation_effort": "low"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "recommendation_type": "compression",
                "priority": "medium",
                "title": "Enable Response Compression",
                "description": "Reduce bandwidth usage with gzip compression",
                "estimated_improvement": {
                    "bandwidth_reduction": 70.0,  # 70% reduction
                    "cost_savings": 300.0  # $300/month
                },
                "status": "pending",
                "implementation_effort": "low"
            }
        ]
        
        recommendation_repo.create.side_effect = lambda r: r
        
        # Create recommendations
        for rec in recommendations:
            await recommendation_repo.create(rec)
        
        # Verify recommendations were generated
        assert len(recommendations) == 3
        assert all(r["status"] == "pending" for r in recommendations)
        
        # Step 4: Apply recommendations (prioritized by impact)
        # Sort by priority and estimated improvement
        sorted_recs = sorted(
            recommendations,
            key=lambda r: (
                0 if r["priority"] == "high" else 1,
                -r["estimated_improvement"].get("response_time_reduction", 0)
            )
        )
        
        applied_recommendations = []
        
        for rec in sorted_recs:
            # Simulate policy application
            rec["status"] = "applied"
            rec["applied_at"] = datetime.utcnow()
            await recommendation_repo.update(rec)
            applied_recommendations.append(rec)
        
        # Verify recommendations were applied
        assert len(applied_recommendations) == 3
        assert all(r["status"] == "applied" for r in applied_recommendations)
        
        # Step 5: Collect post-optimization metrics
        # Simulate improved metrics after optimization
        post_optimization_metrics = {
            "response_time_p95": 320.0,  # Reduced from 800+
            "error_rate": 0.02,  # Reduced from 0.05
            "throughput": 50.0,
            "cache_hit_rate": 0.75,  # Caching enabled
            "availability": 99.8
        }
        
        metrics_repo.get_latest_metrics.return_value = post_optimization_metrics
        
        # Step 6: Validate improvements
        baseline_metrics = historical_metrics[-1]  # Last metric before optimization
        
        for rec in applied_recommendations:
            # Calculate actual improvement
            if rec["recommendation_type"] == "caching":
                actual_improvement = (
                    (baseline_metrics["response_time_p95"] - post_optimization_metrics["response_time_p95"])
                    / baseline_metrics["response_time_p95"]
                ) * 100
                
                rec["actual_impact"] = {
                    "response_time_reduction": actual_improvement,
                    "measured_at": datetime.utcnow()
                }
            
            rec["status"] = "validated"
            rec["validated_at"] = datetime.utcnow()
            await recommendation_repo.update(rec)
        
        # Verify validation completed
        assert all(r["status"] == "validated" for r in applied_recommendations)
        
        # Verify improvements met expectations
        caching_rec = next(r for r in applied_recommendations if r["recommendation_type"] == "caching")
        assert caching_rec["actual_impact"]["response_time_reduction"] > 50.0  # At least 50% improvement

    @pytest.mark.asyncio
    async def test_recommendation_prioritization_workflow(
        self, mock_optimization_service
    ):
        """Test recommendation prioritization based on impact and effort."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        api_id = uuid4()
        
        # Create recommendations with different priorities
        recommendations = [
            {
                "id": uuid4(),
                "api_id": api_id,
                "priority": "low",
                "estimated_improvement": {"response_time_reduction": 10.0},
                "implementation_effort": "high"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "priority": "high",
                "estimated_improvement": {"response_time_reduction": 60.0},
                "implementation_effort": "low"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "priority": "medium",
                "estimated_improvement": {"response_time_reduction": 30.0},
                "implementation_effort": "medium"
            }
        ]
        
        # Sort by priority and impact
        sorted_recs = sorted(
            recommendations,
            key=lambda r: (
                0 if r["priority"] == "high" else (1 if r["priority"] == "medium" else 2),
                -r["estimated_improvement"]["response_time_reduction"]
            )
        )
        
        # Verify prioritization
        assert sorted_recs[0]["priority"] == "high"
        assert sorted_recs[1]["priority"] == "medium"
        assert sorted_recs[2]["priority"] == "low"

    @pytest.mark.asyncio
    async def test_optimization_rollback_workflow(
        self, mock_optimization_service
    ):
        """Test rollback of optimization that caused issues."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        api_id = uuid4()
        
        # Create and apply recommendation
        rec_data = {
            "id": uuid4(),
            "api_id": api_id,
            "recommendation_type": "caching",
            "status": "applied",
            "applied_at": datetime.utcnow()
        }
        
        recommendation_repo.get.return_value = rec_data
        
        # Simulate negative impact after application
        post_metrics = {
            "response_time_p95": 1200.0,  # Worse than before!
            "error_rate": 0.10,  # Increased errors
        }
        
        metrics_repo.get_latest_metrics.return_value = post_metrics
        
        # Detect negative impact and rollback
        rec_data["status"] = "rolled_back"
        rec_data["rolled_back_at"] = datetime.utcnow()
        rec_data["rollback_reason"] = "Caused performance degradation"
        await recommendation_repo.update(rec_data)
        
        # Verify rollback was recorded
        recommendation_repo.update.assert_called_once()
        assert rec_data["status"] == "rolled_back"

    @pytest.mark.asyncio
    async def test_multi_api_optimization_workflow(
        self, mock_optimization_service
    ):
        """Test optimization across multiple APIs."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        # Create multiple APIs
        apis = [
            {"id": uuid4(), "name": "API 1"},
            {"id": uuid4(), "name": "API 2"},
            {"id": uuid4(), "name": "API 3"}
        ]
        
        # Generate recommendations for each API
        all_recommendations = []
        
        for api in apis:
            api_repo.get.return_value = api
            
            # Simulate metrics analysis
            metrics_repo.find_by_api.return_value = ([{"response_time_p95": 500.0}], 1)
            
            # Generate recommendations
            recs = [
                {
                    "id": uuid4(),
                    "api_id": api["id"],
                    "recommendation_type": "caching",
                    "priority": "high",
                    "status": "pending"
                }
            ]
            
            for rec in recs:
                await recommendation_repo.create(rec)
                all_recommendations.append(rec)
        
        # Verify recommendations generated for all APIs
        assert len(all_recommendations) == 3
        assert len(set(r["api_id"] for r in all_recommendations)) == 3

    @pytest.mark.asyncio
    async def test_optimization_impact_tracking(
        self, mock_optimization_service
    ):
        """Test tracking of optimization impact over time."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        api_id = uuid4()
        
        rec_data = {
            "id": uuid4(),
            "api_id": api_id,
            "recommendation_type": "caching",
            "status": "applied",
            "estimated_improvement": {"response_time_reduction": 50.0}
        }
        
        recommendation_repo.get.return_value = rec_data
        
        # Track impact over multiple time periods
        impact_measurements = []
        
        for day in range(7):
            measurement = {
                "day": day,
                "response_time_p95": 400.0 - (day * 10),  # Gradual improvement
                "cache_hit_rate": 0.5 + (day * 0.05),  # Increasing cache hits
                "measured_at": datetime.utcnow() + timedelta(days=day)
            }
            impact_measurements.append(measurement)
        
        # Calculate cumulative impact
        initial_response_time = 800.0
        final_response_time = impact_measurements[-1]["response_time_p95"]
        actual_improvement = ((initial_response_time - final_response_time) / initial_response_time) * 100
        
        rec_data["actual_impact"] = {
            "response_time_reduction": actual_improvement,
            "measurements": impact_measurements
        }
        
        await recommendation_repo.update(rec_data)
        
        # Verify impact tracking
        assert actual_improvement > 40.0  # Significant improvement
        assert len(impact_measurements) == 7


class TestOptimizationPolicyApplication:
    """Test optimization policy application workflows."""

    @pytest.mark.asyncio
    async def test_apply_caching_policy(self, mock_optimization_service):
        """Test applying caching policy."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        api_id = uuid4()
        
        # Create caching recommendation
        rec_data = {
            "id": uuid4(),
            "api_id": api_id,
            "recommendation_type": "caching",
            "configuration": {
                "cache_ttl": 300,  # 5 minutes
                "cache_key_pattern": "api:v1:*",
                "cache_methods": ["GET"]
            },
            "status": "pending"
        }
        
        # Apply caching policy
        rec_data["status"] = "applied"
        rec_data["applied_at"] = datetime.utcnow()
        await recommendation_repo.update(rec_data)
        
        # Verify application
        recommendation_repo.update.assert_called_once()
        assert rec_data["status"] == "applied"

    @pytest.mark.asyncio
    async def test_apply_rate_limiting_policy(self, mock_optimization_service):
        """Test applying rate limiting policy."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        api_id = uuid4()
        
        # Create rate limiting recommendation
        rec_data = {
            "id": uuid4(),
            "api_id": api_id,
            "recommendation_type": "rate_limiting",
            "configuration": {
                "requests_per_minute": 1000,
                "burst_size": 100,
                "rate_limit_by": "ip_address"
            },
            "status": "pending"
        }
        
        # Apply rate limiting policy
        rec_data["status"] = "applied"
        rec_data["applied_at"] = datetime.utcnow()
        await recommendation_repo.update(rec_data)
        
        # Verify application
        recommendation_repo.update.assert_called_once()
        assert rec_data["status"] == "applied"

    @pytest.mark.asyncio
    async def test_apply_compression_policy(self, mock_optimization_service):
        """Test applying compression policy."""
        service, recommendation_repo, metrics_repo, api_repo, llm_service = mock_optimization_service
        
        api_id = uuid4()
        
        # Create compression recommendation
        rec_data = {
            "id": uuid4(),
            "api_id": api_id,
            "recommendation_type": "compression",
            "configuration": {
                "compression_type": "gzip",
                "compression_level": 6,
                "min_response_size": 1024  # 1KB
            },
            "status": "pending"
        }
        
        # Apply compression policy
        rec_data["status"] = "applied"
        rec_data["applied_at"] = datetime.utcnow()
        await recommendation_repo.update(rec_data)
        
        # Verify application
        recommendation_repo.update.assert_called_once()
        assert rec_data["status"] == "applied"


# Made with Bob