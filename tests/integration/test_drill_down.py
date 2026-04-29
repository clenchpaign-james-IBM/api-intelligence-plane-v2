"""
Integration tests for drill-down queries from metrics to transactional logs.

Tests the complete drill-down workflow:
1. Create metrics and transactional logs
2. Drill down from metric to logs
3. Verify log filtering by time range
4. Test drill-down with gateway context
5. Validate external call tracking in drill-down
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.repositories.metrics_repository import MetricsRepository
from backend.app.db.repositories.transactional_log_repository import TransactionalLogRepository
from backend.app.models.base.metric import Metric, TimeBucket
from backend.app.models.base.transaction import (
    TransactionalLog,
    EventType,
    EventStatus,
    CacheStatus,
    ErrorOrigin,
    ExternalCall,
    ExternalCallType,
)


@pytest.fixture
def metrics_repository():
    """Create Metrics repository instance."""
    return MetricsRepository()


@pytest.fixture
def transactional_log_repository():
    """Create TransactionalLog repository instance."""
    return TransactionalLogRepository()




@pytest.mark.asyncio
class TestDrillDownQueries:
    """Integration tests for drill-down from metrics to logs."""

    async def test_drill_down_from_metric_to_logs(
        self,
        metrics_repository,
        transactional_log_repository
    ):
        """Test drilling down from a metric to its source logs."""
        # Create test data
        now = datetime.utcnow()
        gateway_id = uuid4()
        api_id = str(uuid4())
        
        # Create a metric
        metric = Metric(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api_id,
            application_id=None,
            operation=None,
            timestamp=now,
            time_bucket=TimeBucket.ONE_MINUTE,
            request_count=100,
            success_count=95,
            failure_count=5,
            error_rate=0.05,
            availability=95.0,
            response_time_avg=150.0,
            response_time_min=50.0,
            response_time_max=500.0,
            response_time_p50=120.0,
            response_time_p95=250.0,
            response_time_p99=350.0,
            gateway_time_avg=50.0,
            backend_time_avg=100.0,
            throughput=100.0,
            total_data_size=102400,
            avg_request_size=256,
            avg_response_size=768,
            cache_hit_rate=0.3,
            endpoint_metrics=None,
            vendor_metadata=None,
            created_at=now,
        )
        created_metric = metrics_repository.create(metric)
        
        # Create transactional logs for the same time period
        logs = []
        for i in range(10):
            log = TransactionalLog(
                id=uuid4(),
                event_type=EventType.TRANSACTIONAL,
                timestamp=int((now + timedelta(seconds=i)).timestamp() * 1000),
                api_id=api_id,
                api_name="Test API",
                api_version="1.0.0",
                operation="/data",
                http_method="GET",
                request_path="/api/v1/data",
                request_headers={},
                request_payload=None,
                request_size=100,
                query_parameters={},
                status_code=200 if i < 9 else 500,  # One error
                response_headers={},
                response_payload=None,
                response_size=500,
                client_id=f"client-{i}",
                client_name=f"Client {i}",
                client_ip=f"192.168.1.{100 + i}",
                user_agent="TestAgent/1.0",
                total_time_ms=150 + i * 10,
                gateway_time_ms=50,
                backend_time_ms=100 + i * 10,
                status=EventStatus.SUCCESS if i < 9 else EventStatus.FAILURE,
                correlation_id=f"corr-{uuid4()}",
                session_id=None,
                trace_id=None,
                cache_status=CacheStatus.MISS if i % 3 == 0 else CacheStatus.HIT,
                backend_url="http://backend:8080/data",
                backend_method=None,
                backend_request_headers={},
                backend_response_headers={},
                error_origin=None,
                error_message=None if i < 9 else "Internal Server Error",
                error_code=None if i < 9 else "500",
                external_calls=[],
                gateway_id=str(gateway_id),
                gateway_node=None,
                vendor_metadata=None,
                created_at=now + timedelta(seconds=i),
            )
            logs.append(log)
        
        # Store logs
        transactional_log_repository.bulk_create(logs)
        
        # Query logs for the metric's time range
        start_time = now - timedelta(minutes=1)
        end_time = now + timedelta(minutes=2)
        
        results, total = transactional_log_repository.find_logs(
            api_id=api_id,
            gateway_id=str(gateway_id),
            start_time=start_time,
            end_time=end_time,
            size=20
        )
        
        # Verify drill-down results
        assert len(results) >= 10
        assert all(r.api_id == api_id for r in results)
        assert all(r.gateway_id == str(gateway_id) for r in results)

    async def test_drill_down_with_time_range_filter(
        self,
        metrics_repository,
        transactional_log_repository
    ):
        """Test drill-down with specific time range filtering."""
        # Create test data
        now = datetime.utcnow()
        gateway_id = uuid4()
        api_id = str(uuid4())
        
        # Create metric
        metric = Metric(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api_id,
            application_id=None,
            operation=None,
            timestamp=now,
            time_bucket=TimeBucket.FIVE_MINUTES,
            request_count=500,
            success_count=480,
            failure_count=20,
            error_rate=0.04,
            availability=96.0,
            response_time_avg=200.0,
            response_time_min=80.0,
            response_time_max=600.0,
            response_time_p50=180.0,
            response_time_p95=350.0,
            response_time_p99=450.0,
            gateway_time_avg=50.0,
            backend_time_avg=150.0,
            throughput=100.0,
            total_data_size=512000,
            avg_request_size=256,
            avg_response_size=768,
            cache_hit_rate=0.4,
            endpoint_metrics=None,
            vendor_metadata=None,
            created_at=now,
        )
        created_metric = metrics_repository.create(metric)
        
        # Create logs spanning 5 minutes
        logs = []
        for i in range(20):
            log = TransactionalLog(
                id=uuid4(),
                event_type=EventType.TRANSACTIONAL,
                timestamp=int((now + timedelta(seconds=i * 15)).timestamp() * 1000),
                api_id=api_id,
                api_name="Test API",
                api_version="1.0.0",
                operation="/data",
                http_method="GET",
                request_path="/api/v1/data",
                request_headers={},
                request_payload=None,
                request_size=100,
                query_parameters={},
                status_code=200,
                response_headers={},
                response_payload=None,
                response_size=500,
                client_id=f"client-{i}",
                client_name=f"Client {i}",
                client_ip=f"192.168.1.{100 + (i % 50)}",
                user_agent="TestAgent/1.0",
                total_time_ms=200 + i * 5,
                gateway_time_ms=50,
                backend_time_ms=150 + i * 5,
                status=EventStatus.SUCCESS,
                correlation_id=f"corr-{uuid4()}",
                session_id=None,
                trace_id=None,
                cache_status=CacheStatus.HIT if i % 2 == 0 else CacheStatus.MISS,
                backend_url="http://backend:8080/data",
                backend_method=None,
                backend_request_headers={},
                backend_response_headers={},
                error_origin=None,
                error_message=None,
                error_code=None,
                external_calls=[],
                gateway_id=str(gateway_id),
                gateway_node=None,
                vendor_metadata=None,
                created_at=now + timedelta(seconds=i * 15),
            )
            logs.append(log)
        
        # Store logs
        transactional_log_repository.bulk_create(logs)
        
        # Query logs for the metric's time range
        start_time = now - timedelta(minutes=1)
        end_time = now + timedelta(minutes=6)
        
        results, total = transactional_log_repository.find_logs(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            size=50
        )
        
        # Verify results
        assert len(results) >= 20
        assert all(r.api_id == api_id for r in results)

    async def test_drill_down_with_external_calls(
        self,
        metrics_repository,
        transactional_log_repository
    ):
        """Test drill-down showing external call details."""
        # Create test data
        now = datetime.utcnow()
        gateway_id = uuid4()
        api_id = str(uuid4())
        
        # Create metric
        metric = Metric(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api_id,
            application_id=None,
            operation=None,
            timestamp=now,
            time_bucket=TimeBucket.ONE_MINUTE,
            request_count=50,
            success_count=48,
            failure_count=2,
            error_rate=0.04,
            availability=96.0,
            response_time_avg=300.0,
            response_time_min=150.0,
            response_time_max=700.0,
            response_time_p50=280.0,
            response_time_p95=450.0,
            response_time_p99=550.0,
            gateway_time_avg=20.0,
            backend_time_avg=280.0,
            throughput=50.0,
            total_data_size=51200,
            avg_request_size=256,
            avg_response_size=768,
            cache_hit_rate=0.2,
            endpoint_metrics=None,
            vendor_metadata=None,
            created_at=now,
        )
        created_metric = metrics_repository.create(metric)
        
        # Create logs with external calls
        logs = []
        for i in range(5):
            external_calls = [
                ExternalCall(
                    call_type=ExternalCallType.AUTHENTICATION,
                    url="http://auth:8080/validate",
                    method="POST",
                    start_time=int(now.timestamp() * 1000),
                    end_time=int((now + timedelta(milliseconds=30)).timestamp() * 1000),
                    duration_ms=30,
                    status_code=200,
                    success=True,
                    request_size=None,
                    response_size=None,
                    error_message=None,
                ),
                ExternalCall(
                    call_type=ExternalCallType.BACKEND_SERVICE,
                    url="http://backend:8080/data",
                    method="GET",
                    start_time=int((now + timedelta(milliseconds=30)).timestamp() * 1000),
                    end_time=int((now + timedelta(milliseconds=280)).timestamp() * 1000),
                    duration_ms=250,
                    status_code=200,
                    success=True,
                    request_size=None,
                    response_size=None,
                    error_message=None,
                ),
            ]
            
            log = TransactionalLog(
                id=uuid4(),
                event_type=EventType.TRANSACTIONAL,
                timestamp=int((now + timedelta(seconds=i)).timestamp() * 1000),
                api_id=api_id,
                api_name="Test API",
                api_version="1.0.0",
                operation="/data",
                http_method="GET",
                request_path="/api/v1/data",
                request_headers={},
                request_payload=None,
                request_size=100,
                query_parameters={},
                status_code=200,
                response_headers={},
                response_payload=None,
                response_size=500,
                client_id=f"client-{i}",
                client_name=f"Client {i}",
                client_ip=f"192.168.1.{100 + i}",
                user_agent="TestAgent/1.0",
                total_time_ms=300,
                gateway_time_ms=20,
                backend_time_ms=280,
                status=EventStatus.SUCCESS,
                correlation_id=f"corr-{uuid4()}",
                session_id=None,
                trace_id=None,
                cache_status=CacheStatus.MISS,
                backend_url="http://backend:8080/data",
                backend_method=None,
                backend_request_headers={},
                backend_response_headers={},
                error_origin=None,
                error_message=None,
                error_code=None,
                external_calls=external_calls,
                gateway_id=str(gateway_id),
                gateway_node=None,
                vendor_metadata=None,
                created_at=now + timedelta(seconds=i),
            )
            logs.append(log)
        
        # Store logs
        transactional_log_repository.bulk_create(logs)
        
        # Query logs
        results, total = transactional_log_repository.find_logs(
            api_id=api_id,
            gateway_id=str(gateway_id),
            size=10
        )
        
        # Verify external calls are present
        assert len(results) >= 5
        for log in results:
            if log.external_calls:
                assert len(log.external_calls) == 2
                assert log.external_calls[0].call_type == ExternalCallType.AUTHENTICATION
                assert log.external_calls[1].call_type == ExternalCallType.BACKEND_SERVICE

    async def test_drill_down_with_errors(
        self,
        metrics_repository,
        transactional_log_repository
    ):
        """Test drill-down focusing on error logs."""
        # Create test data
        now = datetime.utcnow()
        gateway_id = uuid4()
        api_id = str(uuid4())
        
        # Create metric with high error rate
        metric = Metric(
            id=uuid4(),
            gateway_id=gateway_id,
            api_id=api_id,
            application_id=None,
            operation=None,
            timestamp=now,
            time_bucket=TimeBucket.ONE_MINUTE,
            request_count=100,
            success_count=70,
            failure_count=30,
            error_rate=0.30,
            availability=70.0,
            response_time_avg=200.0,
            response_time_min=50.0,
            response_time_max=600.0,
            response_time_p50=180.0,
            response_time_p95=400.0,
            response_time_p99=500.0,
            gateway_time_avg=20.0,
            backend_time_avg=180.0,
            throughput=100.0,
            total_data_size=102400,
            avg_request_size=256,
            avg_response_size=512,
            cache_hit_rate=0.1,
            endpoint_metrics=None,
            vendor_metadata=None,
            created_at=now,
        )
        created_metric = metrics_repository.create(metric)
        
        # Create logs with mix of success and errors
        logs = []
        for i in range(10):
            is_error = i % 3 == 0  # 30% error rate
            
            log = TransactionalLog(
                id=uuid4(),
                event_type=EventType.ERROR if is_error else EventType.TRANSACTIONAL,
                timestamp=int((now + timedelta(seconds=i)).timestamp() * 1000),
                api_id=api_id,
                api_name="Test API",
                api_version="1.0.0",
                operation="/data",
                http_method="GET",
                request_path="/api/v1/data",
                request_headers={},
                request_payload=None,
                request_size=100,
                query_parameters={},
                status_code=500 if is_error else 200,
                response_headers={},
                response_payload=None,
                response_size=200 if is_error else 500,
                client_id=f"client-{i}",
                client_name=f"Client {i}",
                client_ip=f"192.168.1.{100 + i}",
                user_agent="TestAgent/1.0",
                total_time_ms=100 if is_error else 200,
                gateway_time_ms=20,
                backend_time_ms=80 if is_error else 180,
                status=EventStatus.FAILURE if is_error else EventStatus.SUCCESS,
                correlation_id=f"corr-{uuid4()}",
                session_id=None,
                trace_id=None,
                cache_status=CacheStatus.BYPASS if is_error else CacheStatus.MISS,
                backend_url="http://backend:8080/data",
                backend_method=None,
                backend_request_headers={},
                backend_response_headers={},
                error_origin=ErrorOrigin.BACKEND if is_error else None,
                error_message="Service Unavailable" if is_error else None,
                error_code="503" if is_error else None,
                external_calls=[],
                gateway_id=str(gateway_id),
                gateway_node=None,
                vendor_metadata=None,
                created_at=now + timedelta(seconds=i),
            )
            logs.append(log)
        
        # Store logs
        transactional_log_repository.bulk_create(logs)
        
        # Query all logs
        all_results, _ = transactional_log_repository.find_logs(
            api_id=api_id,
            size=20
        )
        
        # Verify error logs are present
        error_logs = [log for log in all_results if log.status == EventStatus.FAILURE]
        success_logs = [log for log in all_results if log.status == EventStatus.SUCCESS]
        
        assert len(error_logs) >= 3  # At least 30% errors
        assert len(success_logs) >= 7  # At least 70% success
        
        # Verify error details
        for log in error_logs:
            assert log.error_message is not None
            assert log.error_code is not None
            assert log.status_code >= 400


# Made with Bob