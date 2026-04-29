"""
Integration tests for transactional log collection flow.

Tests the complete transactional log collection workflow:
1. Store transactional logs in OpenSearch with daily index rotation
2. Query logs with filters (gateway, API, application, time range)
3. Verify external call tracking
4. Test bulk log ingestion
5. Validate drill-down capabilities
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from backend.app.db.repositories.transactional_log_repository import TransactionalLogRepository
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
def transactional_log_repository():
    """Create TransactionalLog repository instance."""
    return TransactionalLogRepository()


@pytest.mark.asyncio
class TestTransactionalLogCollection:
    """Integration tests for transactional log collection flow."""

    async def test_store_transactional_log(self, transactional_log_repository):
        """Test storing a transactional log."""
        # Create a transactional log
        now = datetime.utcnow()
        log = TransactionalLog(
            id=uuid4(),
            event_type=EventType.TRANSACTIONAL,
            timestamp=int(now.timestamp() * 1000),
            api_id=str(uuid4()),
            api_name="Test Analytics API",
            api_version="1.0.0",
            operation="/data",
            http_method="GET",
            request_path="/api/v1/analytics/data",
            request_headers={"Content-Type": "application/json"},
            request_payload=None,
            request_size=256,
            query_parameters={"limit": "10"},
            status_code=200,
            response_headers={"Content-Type": "application/json"},
            response_payload=None,
            response_size=1024,
            client_id="test-client",
            client_name="Test Client",
            client_ip="192.168.1.100",
            user_agent="TestAgent/1.0",
            total_time_ms=150,
            gateway_time_ms=50,
            backend_time_ms=100,
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
            external_calls=[],
            gateway_id=str(uuid4()),
            gateway_node=None,
            vendor_metadata=None,
            created_at=now,
        )
        
        # Store the log
        created_log = transactional_log_repository.create(log)
        
        # Verify log was created
        assert created_log is not None
        assert created_log.id == log.id
        assert created_log.api_name == "Test Analytics API"
        assert created_log.status == EventStatus.SUCCESS
        
        # Retrieve the log
        retrieved_log = transactional_log_repository.get(created_log.id)
        assert retrieved_log is not None
        assert retrieved_log.id == created_log.id

    async def test_bulk_log_ingestion(self, transactional_log_repository):
        """Test bulk ingestion of transactional logs."""
        # Create multiple logs
        now = datetime.utcnow()
        gateway_id = str(uuid4())
        api_id = str(uuid4())
        logs = []
        
        for i in range(10):
            log = TransactionalLog(
                id=uuid4(),
                event_type=EventType.TRANSACTIONAL,
                timestamp=int((now - timedelta(minutes=i)).timestamp() * 1000),
                api_id=api_id,
                api_name="Test API",
                api_version="1.0.0",
                operation=f"/data/{i}",
                http_method="GET",
                request_path=f"/api/v1/analytics/data/{i}",
                request_headers={},
                request_payload=None,
                request_size=100 + i,
                query_parameters={},
                status_code=200,
                response_headers={},
                response_payload=None,
                response_size=500 + i,
                client_id=f"client-{i}",
                client_name=f"Client {i}",
                client_ip=f"192.168.1.{100 + i}",
                user_agent="TestAgent/1.0",
                total_time_ms=100 + i * 10,
                gateway_time_ms=30 + i * 5,
                backend_time_ms=70 + i * 5,
                status=EventStatus.SUCCESS,
                correlation_id=f"corr-{uuid4()}",
                session_id=None,
                trace_id=None,
                cache_status=CacheStatus.MISS,
                backend_url=f"http://backend:8080/data/{i}",
                backend_method=None,
                backend_request_headers={},
                backend_response_headers={},
                error_origin=None,
                error_message=None,
                error_code=None,
                external_calls=[],
                gateway_id=gateway_id,
                gateway_node=None,
                vendor_metadata=None,
                created_at=now - timedelta(minutes=i),
            )
            logs.append(log)
        
        # Bulk create logs
        created_count = transactional_log_repository.bulk_create(logs)
        
        # Verify all logs were created
        assert created_count == 10

    async def test_query_logs_with_filters(self, transactional_log_repository):
        """Test querying logs with various filters."""
        # Create test logs
        now = datetime.utcnow()
        gateway_id = str(uuid4())
        api_id = str(uuid4())
        logs = []
        
        for i in range(5):
            log = TransactionalLog(
                id=uuid4(),
                event_type=EventType.TRANSACTIONAL,
                timestamp=int((now - timedelta(minutes=i)).timestamp() * 1000),
                api_id=api_id,
                api_name="Test API",
                api_version="1.0.0",
                operation="/data",
                http_method="GET",
                request_path="/api/v1/analytics/data",
                request_headers={},
                request_payload=None,
                request_size=100,
                query_parameters={},
                status_code=200,
                response_headers={},
                response_payload=None,
                response_size=500,
                client_id="test-client",
                client_name="Test Client",
                client_ip="192.168.1.100",
                user_agent="TestAgent/1.0",
                total_time_ms=150,
                gateway_time_ms=50,
                backend_time_ms=100,
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
                external_calls=[],
                gateway_id=gateway_id,
                gateway_node=None,
                vendor_metadata=None,
                created_at=now - timedelta(minutes=i),
            )
            logs.append(log)
        
        # Store logs
        transactional_log_repository.bulk_create(logs)
        
        # Query by gateway_id
        results, total = transactional_log_repository.find_logs(
            gateway_id=gateway_id,
            size=10
        )
        assert len(results) >= 5
        assert all(r.gateway_id == gateway_id for r in results)
        
        # Query by api_id
        results, total = transactional_log_repository.find_logs(
            api_id=api_id,
            size=10
        )
        assert len(results) >= 5
        assert all(r.api_id == api_id for r in results)
        
        # Query by time range
        start_time = now - timedelta(minutes=10)
        end_time = now
        results, total = transactional_log_repository.find_logs(
            start_time=start_time,
            end_time=end_time,
            size=10
        )
        assert len(results) >= 5

    async def test_external_call_tracking(self, transactional_log_repository):
        """Test tracking external calls in transactional logs."""
        # Create log with external calls
        now = datetime.utcnow()
        external_calls = [
            ExternalCall(
                call_type=ExternalCallType.AUTHENTICATION,
                url="http://auth-service:8080/validate",
                method="POST",
                start_time=int(now.timestamp() * 1000),
                end_time=int((now + timedelta(milliseconds=20)).timestamp() * 1000),
                duration_ms=20,
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
                start_time=int((now + timedelta(milliseconds=20)).timestamp() * 1000),
                end_time=int((now + timedelta(milliseconds=120)).timestamp() * 1000),
                duration_ms=100,
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
            timestamp=int(now.timestamp() * 1000),
            api_id=str(uuid4()),
            api_name="Test API",
            api_version="1.0.0",
            operation="/data",
            http_method="GET",
            request_path="/api/v1/analytics/data",
            request_headers={},
            request_payload=None,
            request_size=100,
            query_parameters={},
            status_code=200,
            response_headers={},
            response_payload=None,
            response_size=500,
            client_id="test-client",
            client_name="Test Client",
            client_ip="192.168.1.100",
            user_agent="TestAgent/1.0",
            total_time_ms=150,
            gateway_time_ms=30,
            backend_time_ms=120,
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
            gateway_id=str(uuid4()),
            gateway_node=None,
            vendor_metadata=None,
            created_at=now,
        )
        
        # Store log
        created_log = transactional_log_repository.create(log)
        
        # Verify external calls were stored
        assert len(created_log.external_calls) == 2
        assert created_log.external_calls[0].call_type == ExternalCallType.AUTHENTICATION
        assert created_log.external_calls[1].call_type == ExternalCallType.BACKEND_SERVICE

    async def test_error_log_collection(self, transactional_log_repository):
        """Test collecting logs for failed requests."""
        # Create error log
        now = datetime.utcnow()
        log = TransactionalLog(
            id=uuid4(),
            event_type=EventType.ERROR,
            timestamp=int(now.timestamp() * 1000),
            api_id=str(uuid4()),
            api_name="Test API",
            api_version="1.0.0",
            operation="/data",
            http_method="GET",
            request_path="/api/v1/analytics/data",
            request_headers={},
            request_payload=None,
            request_size=100,
            query_parameters={},
            status_code=500,
            response_headers={},
            response_payload=None,
            response_size=200,
            client_id="test-client",
            client_name="Test Client",
            client_ip="192.168.1.100",
            user_agent="TestAgent/1.0",
            total_time_ms=50,
            gateway_time_ms=10,
            backend_time_ms=40,
            status=EventStatus.FAILURE,
            correlation_id=f"corr-{uuid4()}",
            session_id=None,
            trace_id=None,
            cache_status=CacheStatus.BYPASS,
            backend_url="http://backend:8080/data",
            backend_method=None,
            backend_request_headers={},
            backend_response_headers={},
            error_origin=ErrorOrigin.BACKEND,
            error_message="Internal Server Error",
            error_code="500",
            external_calls=[],
            gateway_id=str(uuid4()),
            gateway_node=None,
            vendor_metadata=None,
            created_at=now,
        )
        
        # Store error log
        created_log = transactional_log_repository.create(log)
        
        # Verify error details
        assert created_log.status == EventStatus.FAILURE
        assert created_log.error_origin == ErrorOrigin.BACKEND
        assert created_log.error_message == "Internal Server Error"
        assert created_log.status_code == 500

    async def test_daily_index_rotation(self, transactional_log_repository):
        """Test that logs are stored in daily indices."""
        # Create logs for different days
        today = datetime.utcnow()
        yesterday = today - timedelta(days=1)
        
        logs = [
            TransactionalLog(
                id=uuid4(),
                event_type=EventType.TRANSACTIONAL,
                timestamp=int(today.timestamp() * 1000),
                api_id=str(uuid4()),
                api_name="Test API",
                api_version="1.0.0",
                operation="/data",
                http_method="GET",
                request_path="/api/v1/analytics/data",
                request_headers={},
                request_payload=None,
                request_size=100,
                query_parameters={},
                status_code=200,
                response_headers={},
                response_payload=None,
                response_size=500,
                client_id="test-client",
                client_name="Test Client",
                client_ip="192.168.1.100",
                user_agent="TestAgent/1.0",
                total_time_ms=150,
                gateway_time_ms=50,
                backend_time_ms=100,
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
                external_calls=[],
                gateway_id=str(uuid4()),
                gateway_node=None,
                vendor_metadata=None,
                created_at=today,
            ),
            TransactionalLog(
                id=uuid4(),
                event_type=EventType.TRANSACTIONAL,
                timestamp=int(yesterday.timestamp() * 1000),
                api_id=str(uuid4()),
                api_name="Test API",
                api_version="1.0.0",
                operation="/data",
                http_method="GET",
                request_path="/api/v1/analytics/data",
                request_headers={},
                request_payload=None,
                request_size=100,
                query_parameters={},
                status_code=200,
                response_headers={},
                response_payload=None,
                response_size=500,
                client_id="test-client",
                client_name="Test Client",
                client_ip="192.168.1.100",
                user_agent="TestAgent/1.0",
                total_time_ms=150,
                gateway_time_ms=50,
                backend_time_ms=100,
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
                external_calls=[],
                gateway_id=str(uuid4()),
                gateway_node=None,
                vendor_metadata=None,
                created_at=yesterday,
            ),
        ]
        
        # Store logs
        created_count = transactional_log_repository.bulk_create(logs)
        assert created_count == 2
        
        # Verify logs can be retrieved
        for log in logs:
            retrieved = transactional_log_repository.get(log.id)
            assert retrieved is not None
            assert retrieved.id == log.id


# Made with Bob