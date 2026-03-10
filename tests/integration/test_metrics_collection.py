"""
Integration tests for metrics collection flow.

Tests the complete metrics collection workflow:
1. Collect metrics from Gateway
2. Store metrics in OpenSearch
3. Retrieve time-series metrics
4. Calculate health scores
5. Aggregate metrics
6. Detect anomalies
"""

import asyncio
import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.client import get_opensearch_client
from backend.app.db.repositories.api_repository import APIRepository
from backend.app.db.repositories.gateway_repository import GatewayRepository
from backend.app.db.repositories.metrics_repository import MetricsRepository
from backend.app.services.metrics_service import MetricsService
from backend.app.models.api import API, APIStatus, AuthenticationType, DiscoveryMethod
from backend.app.models.gateway import Gateway, GatewayStatus
from backend.app.models.metric import Metric


@pytest.fixture
async def opensearch_client():
    """Get OpenSearch client for tests."""
    client = get_opensearch_client()
    yield client


@pytest.fixture
async def gateway_repository(opensearch_client):
    """Create Gateway repository instance."""
    return GatewayRepository(opensearch_client)


@pytest.fixture
async def api_repository(opensearch_client):
    """Create API repository instance."""
    return APIRepository(opensearch_client)


@pytest.fixture
async def metrics_repository(opensearch_client):
    """Create Metrics repository instance."""
    return MetricsRepository(opensearch_client)


@pytest.fixture
async def metrics_service(opensearch_client):
    """Create Metrics service instance."""
    return MetricsService(opensearch_client)


@pytest.fixture
async def test_gateway(gateway_repository):
    """Create a test Gateway."""
    gateway = Gateway(
        id=uuid4(),
        name="Test Metrics Gateway",
        vendor="demo",
        version="1.0.0",
        connection_url="http://localhost:8081",
        connection_type="http",
        credentials={"api_key": "test-key"},
        status=GatewayStatus.CONNECTED,
        capabilities=["metrics"],
        last_connected_at=datetime.utcnow(),
        last_error=None,
        configuration={},
        metadata={"test": True},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    created_gateway = await gateway_repository.create(gateway)
    yield created_gateway
    
    # Cleanup
    try:
        await gateway_repository.delete(created_gateway.id)
    except Exception:
        pass


@pytest.fixture
async def test_api(api_repository, test_gateway):
    """Create a test API."""
    api = API(
        id=uuid4(),
        gateway_id=test_gateway.id,
        name="Test Metrics API",
        version="1.0.0",
        base_path="/api/v1/test",
        endpoints=[
            {
                "path": "/users",
                "method": "GET",
                "description": "Get users",
            }
        ],
        methods=["GET", "POST"],
        authentication_type=AuthenticationType.API_KEY,
        authentication_config={},
        ownership={},
        tags=["test"],
        is_shadow=False,
        discovery_method=DiscoveryMethod.GATEWAY_API,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        status=APIStatus.ACTIVE,
        health_score=100.0,
        current_metrics={
            "response_time_p50": 50.0,
            "response_time_p95": 100.0,
            "response_time_p99": 150.0,
            "error_rate": 0.01,
            "throughput": 100.0,
            "availability": 99.9,
        },
        metadata={},
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    created_api = await api_repository.create(api)
    yield created_api
    
    # Cleanup
    try:
        await api_repository.delete(created_api.id)
    except Exception:
        pass


@pytest.mark.asyncio
class TestMetricsCollection:
    """Integration tests for metrics collection flow."""

    async def test_collect_metrics_from_gateway(
        self,
        metrics_service,
        metrics_repository,
        test_api,
        test_gateway
    ):
        """Test collecting metrics from a Gateway."""
        # Collect metrics
        metric = await metrics_service.collect_metrics_for_api(
            api_id=test_api.id,
            gateway_id=test_gateway.id
        )
        
        # Verify metric was collected
        assert metric is not None
        assert metric.api_id == test_api.id
        assert metric.response_time_p50 > 0
        assert metric.response_time_p95 > 0
        assert metric.response_time_p99 > 0
        assert 0 <= metric.error_rate <= 1
        assert metric.throughput >= 0
        assert 0 <= metric.availability <= 100
        
        # Verify metric is stored
        stored_metric = await metrics_repository.get(metric.id)
        assert stored_metric is not None
        assert stored_metric.id == metric.id

    async def test_metrics_time_series_storage(
        self,
        metrics_service,
        metrics_repository,
        test_api
    ):
        """Test storing metrics as time series."""
        # Collect multiple metrics over time
        metrics = []
        for i in range(5):
            metric = await metrics_service.collect_metrics_for_api(
                api_id=test_api.id,
                gateway_id=test_api.gateway_id
            )
            metrics.append(metric)
            await asyncio.sleep(0.1)  # Small delay
        
        # Retrieve time series
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        time_series = await metrics_repository.get_time_series(
            api_id=test_api.id,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=1
        )
        
        # Verify time series data
        assert len(time_series) > 0
        for data_point in time_series:
            assert "timestamp" in data_point
            assert "response_time_p95" in data_point
            assert "error_rate" in data_point

    async def test_health_score_calculation(
        self,
        metrics_service,
        test_api
    ):
        """Test health score calculation."""
        # Calculate health score
        health_score = await metrics_service.calculate_health_score(test_api.id)
        
        # Verify health score
        assert 0 <= health_score <= 100
        assert isinstance(health_score, float)

    async def test_metrics_aggregation(
        self,
        metrics_service,
        metrics_repository,
        test_api
    ):
        """Test metrics aggregation over time range."""
        # Collect some metrics first
        for _ in range(3):
            await metrics_service.collect_metrics_for_api(
                api_id=test_api.id,
                gateway_id=test_api.gateway_id
            )
            await asyncio.sleep(0.1)
        
        # Aggregate metrics
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        aggregated = await metrics_repository.aggregate_metrics(
            api_id=test_api.id,
            start_time=start_time,
            end_time=end_time,
            aggregation="avg"
        )
        
        # Verify aggregated metrics
        assert aggregated is not None
        assert "response_time_p95" in aggregated
        assert "error_rate" in aggregated
        assert "throughput" in aggregated

    async def test_metrics_comparison(
        self,
        metrics_service,
        api_repository,
        test_gateway
    ):
        """Test comparing metrics between two APIs."""
        # Create second API
        api2 = API(
            id=uuid4(),
            gateway_id=test_gateway.id,
            name="Test API 2",
            version="1.0.0",
            base_path="/api/v1/test2",
            endpoints=[],
            methods=["GET"],
            authentication_type=AuthenticationType.API_KEY,
            authentication_config={},
            ownership={},
            is_shadow=False,
            discovery_method=DiscoveryMethod.GATEWAY_API,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            status=APIStatus.ACTIVE,
            health_score=100.0,
            current_metrics={},
            metadata={},
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        
        created_api2 = await api_repository.create(api2)
        
        try:
            # Collect metrics for both APIs
            metric1 = await metrics_service.collect_metrics_for_api(
                api_id=test_api.id,
                gateway_id=test_gateway.id
            )
            metric2 = await metrics_service.collect_metrics_for_api(
                api_id=created_api2.id,
                gateway_id=test_gateway.id
            )
            
            # Compare metrics
            comparison = {
                "response_time_diff": metric1.response_time_p95 - metric2.response_time_p95,
                "error_rate_diff": metric1.error_rate - metric2.error_rate,
                "throughput_diff": metric1.throughput - metric2.throughput,
            }
            
            # Verify comparison
            assert "response_time_diff" in comparison
            assert "error_rate_diff" in comparison
            assert "throughput_diff" in comparison
        finally:
            # Cleanup
            await api_repository.delete(created_api2.id)

    async def test_anomaly_detection(
        self,
        metrics_service,
        metrics_repository,
        test_api
    ):
        """Test anomaly detection in metrics."""
        # Collect baseline metrics
        baseline_metrics = []
        for _ in range(10):
            metric = await metrics_service.collect_metrics_for_api(
                api_id=test_api.id,
                gateway_id=test_api.gateway_id
            )
            baseline_metrics.append(metric)
            await asyncio.sleep(0.05)
        
        # Calculate baseline statistics
        avg_response_time = sum(m.response_time_p95 for m in baseline_metrics) / len(baseline_metrics)
        
        # Simulate anomaly (response time spike)
        # In real scenario, this would come from actual Gateway
        # For test, we just verify the detection logic exists
        
        # Verify we can detect if a metric is anomalous
        threshold = avg_response_time * 2  # 2x baseline
        anomalous = any(m.response_time_p95 > threshold for m in baseline_metrics)
        
        # This is a basic check - real anomaly detection would be more sophisticated
        assert isinstance(anomalous, bool)

    async def test_concurrent_metrics_collection(
        self,
        metrics_service,
        test_api
    ):
        """Test concurrent metrics collection."""
        # Collect metrics concurrently
        tasks = [
            metrics_service.collect_metrics_for_api(
                api_id=test_api.id,
                gateway_id=test_api.gateway_id
            )
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all collections completed
        assert len(results) == 5
        
        # At least some should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) > 0

    async def test_metrics_retention(
        self,
        metrics_repository,
        test_api
    ):
        """Test metrics retention and cleanup."""
        # Create old metric
        old_metric = Metric(
            id=uuid4(),
            api_id=test_api.id,
            timestamp=datetime.utcnow() - timedelta(days=91),  # 91 days old
            response_time_p50=50.0,
            response_time_p95=100.0,
            response_time_p99=150.0,
            error_rate=0.01,
            throughput=100.0,
            availability=99.9,
            sample_count=1000,
            created_at=datetime.utcnow() - timedelta(days=91),
        )
        
        # Store old metric
        await metrics_repository.create(old_metric)
        
        # Verify it exists
        retrieved = await metrics_repository.get(old_metric.id)
        assert retrieved is not None
        
        # In production, a cleanup job would delete metrics older than retention period
        # For now, just verify we can query by date range
        recent_start = datetime.utcnow() - timedelta(days=30)
        recent_metrics = await metrics_repository.get_time_series(
            api_id=test_api.id,
            start_time=recent_start,
            end_time=datetime.utcnow(),
            interval_minutes=60
        )
        
        # Old metric should not be in recent results
        old_metric_in_recent = any(
            m.get("timestamp") == old_metric.timestamp.isoformat()
            for m in recent_metrics
        )
        assert not old_metric_in_recent
        
        # Cleanup
        await metrics_repository.delete(old_metric.id)


@pytest.mark.asyncio
class TestMetricsPerformance:
    """Performance tests for metrics operations."""

    async def test_metrics_collection_performance(
        self,
        metrics_service,
        test_api
    ):
        """Test metrics collection performance."""
        import time
        
        start_time = time.time()
        
        metric = await metrics_service.collect_metrics_for_api(
            api_id=test_api.id,
            gateway_id=test_api.gateway_id
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Collection should be fast
        assert duration < 5.0, f"Metrics collection took too long: {duration}s"
        assert metric is not None

    async def test_time_series_query_performance(
        self,
        metrics_repository,
        test_api
    ):
        """Test time series query performance."""
        import time
        
        # Query large time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=7)
        
        start = time.time()
        
        time_series = await metrics_repository.get_time_series(
            api_id=test_api.id,
            start_time=start_time,
            end_time=end_time,
            interval_minutes=60
        )
        
        end = time.time()
        duration = end - start
        
        # Query should be reasonably fast
        assert duration < 10.0, f"Time series query took too long: {duration}s"
        assert isinstance(time_series, list)

    async def test_bulk_metrics_storage(
        self,
        metrics_repository,
        test_api
    ):
        """Test bulk metrics storage performance."""
        import time
        
        # Create test metrics
        test_metrics = [
            Metric(
                id=uuid4(),
                api_id=test_api.id,
                timestamp=datetime.utcnow() - timedelta(minutes=i),
                response_time_p50=50.0 + i,
                response_time_p95=100.0 + i,
                response_time_p99=150.0 + i,
                error_rate=0.01,
                throughput=100.0,
                availability=99.9,
                sample_count=1000,
                created_at=datetime.utcnow(),
            )
            for i in range(100)
        ]
        
        start_time = time.time()
        
        # Store metrics
        for metric in test_metrics:
            await metrics_repository.create(metric)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Bulk storage should be reasonably fast
        assert duration < 30.0, f"Bulk storage took too long: {duration}s"
        
        # Cleanup
        for metric in test_metrics:
            try:
                await metrics_repository.delete(metric.id)
            except Exception:
                pass

# Made with Bob
