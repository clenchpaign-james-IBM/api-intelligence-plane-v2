"""
Test for analytics drill-down endpoint
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from uuid import uuid4

from app.api.v1.metrics import drill_down_to_logs
from app.models.base.metric import TimeBucket


@pytest.mark.asyncio
async def test_drill_down_to_logs_success():
    """Test successful drill-down to logs"""
    metric_id = str(uuid4())
    
    # Mock metric
    mock_metric = Mock()
    mock_metric.id = metric_id
    mock_metric.api_id = uuid4()
    mock_metric.gateway_id = uuid4()
    mock_metric.timestamp = datetime.utcnow()
    mock_metric.time_bucket = TimeBucket.ONE_HOUR
    mock_metric.request_count = 100
    mock_metric.error_rate = 5.0
    mock_metric.response_time_p50 = 100.0
    mock_metric.response_time_p95 = 200.0
    mock_metric.response_time_p99 = 300.0
    
    # Mock log
    mock_log = Mock()
    mock_log.id = uuid4()
    mock_log.timestamp = int(datetime.utcnow().timestamp() * 1000)
    mock_log.api_id = mock_metric.api_id
    mock_log.gateway_id = mock_metric.gateway_id
    mock_log.application_id = None
    mock_log.operation = "GET /api/test"
    mock_log.method = "GET"
    mock_log.path = "/api/test"
    mock_log.status_code = 200
    mock_log.total_time_ms = 150
    mock_log.gateway_time_ms = 50
    mock_log.backend_time_ms = 100
    mock_log.request_size = 1024
    mock_log.response_size = 2048
    mock_log.client_ip = "192.168.1.1"
    mock_log.user_agent = "TestAgent/1.0"
    mock_log.error_message = None
    
    # Mock service response
    mock_result = {
        "metric_summary": {
            "api_id": str(mock_metric.api_id),
            "gateway_id": str(mock_metric.gateway_id),
            "timestamp": mock_metric.timestamp,
            "time_bucket": mock_metric.time_bucket.value,
            "request_count": mock_metric.request_count,
            "error_rate": mock_metric.error_rate,
            "response_time_p50": mock_metric.response_time_p50,
            "response_time_p95": mock_metric.response_time_p95,
            "response_time_p99": mock_metric.response_time_p99,
        },
        "time_range": {
            "start": mock_metric.timestamp,
            "end": mock_metric.timestamp,
        },
        "logs": [mock_log],
        "total_logs": 1,
        "returned_logs": 1,
    }
    
    with patch("app.api.v1.metrics.MetricsService") as MockService:
        mock_service_instance = MockService.return_value
        mock_service_instance.drill_down_to_logs = AsyncMock(return_value=mock_result)
        
        # Call the endpoint
        result = await drill_down_to_logs(metric_id=metric_id, limit=100)
        
        # Verify response structure
        assert "items" in result
        assert "total" in result
        assert "metric_summary" in result
        assert "time_range" in result
        
        # Verify log data
        assert len(result["items"]) == 1
        assert result["total"] == 1
        
        log_data = result["items"][0]
        assert log_data["method"] == "GET"
        assert log_data["path"] == "/api/test"
        assert log_data["status_code"] == 200


@pytest.mark.asyncio
async def test_drill_down_to_logs_not_found():
    """Test drill-down when metric not found"""
    metric_id = str(uuid4())
    
    # Mock service response with error
    mock_result = {
        "error": "Metric not found"
    }
    
    with patch("app.api.v1.metrics.MetricsService") as MockService:
        mock_service_instance = MockService.return_value
        mock_service_instance.drill_down_to_logs = AsyncMock(return_value=mock_result)
        
        # Call the endpoint and expect HTTPException
        from fastapi import HTTPException
        with pytest.raises(HTTPException) as exc_info:
            await drill_down_to_logs(metric_id=metric_id, limit=100)
        
        assert exc_info.value.status_code == 404
        assert "Metric not found" in str(exc_info.value.detail)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

# Made with Bob
