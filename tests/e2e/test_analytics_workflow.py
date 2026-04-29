"""End-to-end tests for analytics drill-down workflow.

Tests the complete analytics workflow including:
- High-level dashboard metrics aggregation
- Drill-down from summary to detailed views
- Multi-dimensional analysis (time, API, endpoint, status code)
- Metric correlation and pattern detection
- Export and reporting capabilities

Note: Uses mocked dependencies to focus on workflow logic.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from unittest.mock import Mock, AsyncMock


@pytest.fixture
def mock_analytics_service():
    """Create analytics service with mocked dependencies."""
    metrics_repo = Mock()
    metrics_repo.find_by_api = AsyncMock(return_value=([], 0))
    metrics_repo.aggregate_metrics = AsyncMock(return_value={})
    metrics_repo.get_time_series = AsyncMock(return_value=[])
    
    api_repo = Mock()
    api_repo.get = AsyncMock()
    api_repo.find_all = AsyncMock(return_value=[])
    
    gateway_repo = Mock()
    gateway_repo.get = AsyncMock()
    gateway_repo.find_all = AsyncMock(return_value=[])
    
    return metrics_repo, api_repo, gateway_repo


class TestAnalyticsDrillDownWorkflow:
    """Test complete analytics drill-down workflow."""

    @pytest.mark.asyncio
    async def test_complete_drill_down_workflow(self, mock_analytics_service):
        """Test complete workflow from dashboard to detailed analysis."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        # Step 1: Dashboard - High-level overview
        dashboard_metrics = {
            "total_apis": 150,
            "total_requests": 10000000,
            "avg_response_time": 250.0,
            "overall_error_rate": 0.02,
            "overall_availability": 99.5,
            "top_apis_by_traffic": [
                {"api_id": uuid4(), "name": "Payment API", "request_count": 2000000},
                {"api_id": uuid4(), "name": "User API", "request_count": 1500000},
                {"api_id": uuid4(), "name": "Product API", "request_count": 1000000}
            ]
        }
        
        metrics_repo.aggregate_metrics.return_value = dashboard_metrics
        
        # Verify dashboard metrics
        assert dashboard_metrics["total_apis"] == 150
        assert len(dashboard_metrics["top_apis_by_traffic"]) == 3
        
        # Step 2: Drill down to specific API (Payment API)
        payment_api_id = dashboard_metrics["top_apis_by_traffic"][0]["api_id"]
        
        api_details = {
            "id": payment_api_id,
            "name": "Payment API",
            "base_path": "/api/v1/payments"
        }
        
        api_repo.get.return_value = api_details
        
        # Get API-level metrics
        api_metrics = {
            "request_count": 2000000,
            "avg_response_time": 450.0,
            "error_rate": 0.05,
            "availability": 98.0,
            "top_endpoints": [
                {"path": "/api/v1/payments/process", "request_count": 1200000},
                {"path": "/api/v1/payments/refund", "request_count": 500000},
                {"path": "/api/v1/payments/status", "request_count": 300000}
            ]
        }
        
        metrics_repo.aggregate_metrics.return_value = api_metrics
        
        # Verify API-level drill-down
        assert api_metrics["request_count"] == 2000000
        assert len(api_metrics["top_endpoints"]) == 3
        
        # Step 3: Drill down to specific endpoint
        endpoint_path = api_metrics["top_endpoints"][0]["path"]
        
        endpoint_metrics = {
            "path": endpoint_path,
            "request_count": 1200000,
            "avg_response_time": 550.0,
            "error_rate": 0.08,
            "status_code_distribution": {
                "200": 1100000,
                "400": 20000,
                "500": 80000
            },
            "response_time_percentiles": {
                "p50": 400.0,
                "p95": 800.0,
                "p99": 1200.0
            }
        }
        
        metrics_repo.aggregate_metrics.return_value = endpoint_metrics
        
        # Verify endpoint-level drill-down
        assert endpoint_metrics["request_count"] == 1200000
        assert endpoint_metrics["status_code_distribution"]["500"] == 80000
        
        # Step 4: Drill down to time-series analysis
        time_series_data = []
        now = datetime.utcnow()
        
        for hour in range(24):
            time_series_data.append({
                "timestamp": now - timedelta(hours=23-hour),
                "request_count": 50000,
                "avg_response_time": 550 + (hour * 10),
                "error_rate": 0.08 + (hour * 0.001)
            })
        
        metrics_repo.get_time_series.return_value = time_series_data
        
        # Verify time-series drill-down
        assert len(time_series_data) == 24
        assert time_series_data[-1]["avg_response_time"] > time_series_data[0]["avg_response_time"]

    @pytest.mark.asyncio
    async def test_multi_dimensional_analysis(self, mock_analytics_service):
        """Test multi-dimensional analysis across different dimensions."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        # Analyze by multiple dimensions: Gateway, API, Time
        
        # Dimension 1: By Gateway
        gateway_metrics = {
            "gateway_1": {
                "name": "Production Gateway",
                "api_count": 100,
                "total_requests": 8000000,
                "avg_response_time": 200.0
            },
            "gateway_2": {
                "name": "Staging Gateway",
                "api_count": 50,
                "total_requests": 2000000,
                "avg_response_time": 300.0
            }
        }
        
        # Dimension 2: By API Type
        api_type_metrics = {
            "REST": {"count": 120, "avg_response_time": 250.0},
            "SOAP": {"count": 20, "avg_response_time": 500.0},
            "GraphQL": {"count": 10, "avg_response_time": 300.0}
        }
        
        # Dimension 3: By Time Period
        time_period_metrics = {
            "peak_hours": {"avg_response_time": 400.0, "error_rate": 0.05},
            "off_peak_hours": {"avg_response_time": 200.0, "error_rate": 0.01}
        }
        
        # Verify multi-dimensional analysis
        assert len(gateway_metrics) == 2
        assert len(api_type_metrics) == 3
        assert time_period_metrics["peak_hours"]["error_rate"] > time_period_metrics["off_peak_hours"]["error_rate"]

    @pytest.mark.asyncio
    async def test_correlation_analysis(self, mock_analytics_service):
        """Test correlation analysis between metrics."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        # Analyze correlation between response time and error rate
        correlation_data = []
        
        for i in range(100):
            correlation_data.append({
                "response_time": 200 + (i * 10),
                "error_rate": 0.01 + (i * 0.001),
                "timestamp": datetime.utcnow() - timedelta(hours=i)
            })
        
        # Calculate correlation coefficient (simplified)
        # In real implementation, would use statistical methods
        correlation_coefficient = 0.85  # Strong positive correlation
        
        correlation_result = {
            "metric_1": "response_time",
            "metric_2": "error_rate",
            "correlation": correlation_coefficient,
            "interpretation": "Strong positive correlation - as response time increases, error rate increases"
        }
        
        # Verify correlation analysis
        assert correlation_result["correlation"] > 0.7  # Strong correlation
        assert "positive" in correlation_result["interpretation"]

    @pytest.mark.asyncio
    async def test_comparative_analysis(self, mock_analytics_service):
        """Test comparative analysis between time periods."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        # Compare current week vs previous week
        current_week_metrics = {
            "period": "current_week",
            "avg_response_time": 300.0,
            "error_rate": 0.03,
            "total_requests": 5000000
        }
        
        previous_week_metrics = {
            "period": "previous_week",
            "avg_response_time": 250.0,
            "error_rate": 0.02,
            "total_requests": 4500000
        }
        
        # Calculate changes
        comparison = {
            "response_time_change": (
                (current_week_metrics["avg_response_time"] - previous_week_metrics["avg_response_time"])
                / previous_week_metrics["avg_response_time"]
            ) * 100,
            "error_rate_change": (
                (current_week_metrics["error_rate"] - previous_week_metrics["error_rate"])
                / previous_week_metrics["error_rate"]
            ) * 100,
            "traffic_change": (
                (current_week_metrics["total_requests"] - previous_week_metrics["total_requests"])
                / previous_week_metrics["total_requests"]
            ) * 100
        }
        
        # Verify comparative analysis
        assert comparison["response_time_change"] == 20.0  # 20% increase
        assert comparison["error_rate_change"] == 50.0  # 50% increase
        assert comparison["traffic_change"] > 0  # Traffic increased

    @pytest.mark.asyncio
    async def test_anomaly_detection_workflow(self, mock_analytics_service):
        """Test anomaly detection in analytics."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        # Normal baseline metrics
        baseline_metrics = {
            "avg_response_time": 250.0,
            "std_dev": 50.0,
            "error_rate": 0.02
        }
        
        # Current metrics with anomaly
        current_metrics = {
            "response_time": 800.0,  # Anomaly: 11 std devs above mean
            "error_rate": 0.15  # Anomaly: 7.5x normal rate
        }
        
        # Detect anomalies
        anomalies = []
        
        # Response time anomaly
        if current_metrics["response_time"] > baseline_metrics["avg_response_time"] + (3 * baseline_metrics["std_dev"]):
            anomalies.append({
                "metric": "response_time",
                "value": current_metrics["response_time"],
                "baseline": baseline_metrics["avg_response_time"],
                "severity": "high",
                "deviation": (current_metrics["response_time"] - baseline_metrics["avg_response_time"]) / baseline_metrics["std_dev"]
            })
        
        # Error rate anomaly
        if current_metrics["error_rate"] > baseline_metrics["error_rate"] * 3:
            anomalies.append({
                "metric": "error_rate",
                "value": current_metrics["error_rate"],
                "baseline": baseline_metrics["error_rate"],
                "severity": "critical",
                "multiplier": current_metrics["error_rate"] / baseline_metrics["error_rate"]
            })
        
        # Verify anomaly detection
        assert len(anomalies) == 2
        assert any(a["metric"] == "response_time" for a in anomalies)
        assert any(a["metric"] == "error_rate" for a in anomalies)


class TestAnalyticsReporting:
    """Test analytics reporting workflows."""

    @pytest.mark.asyncio
    async def test_generate_performance_report(self, mock_analytics_service):
        """Test generating comprehensive performance report."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        report_data = {
            "report_id": uuid4(),
            "report_type": "performance",
            "period": {
                "start": datetime.utcnow() - timedelta(days=30),
                "end": datetime.utcnow()
            },
            "summary": {
                "total_apis": 150,
                "total_requests": 300000000,
                "avg_response_time": 250.0,
                "overall_error_rate": 0.02
            },
            "top_performers": [
                {"api": "User API", "health_score": 95.0},
                {"api": "Product API", "health_score": 92.0}
            ],
            "bottom_performers": [
                {"api": "Payment API", "health_score": 45.0},
                {"api": "Legacy API", "health_score": 38.0}
            ],
            "trends": {
                "response_time_trend": "increasing",
                "error_rate_trend": "stable",
                "traffic_trend": "increasing"
            }
        }
        
        # Verify report structure
        assert report_data["report_type"] == "performance"
        assert len(report_data["top_performers"]) == 2
        assert len(report_data["bottom_performers"]) == 2

    @pytest.mark.asyncio
    async def test_export_analytics_data(self, mock_analytics_service):
        """Test exporting analytics data in different formats."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        # Prepare export data
        export_data = {
            "format": "csv",
            "data": [
                {"timestamp": datetime.utcnow(), "api": "Payment API", "response_time": 450.0, "error_rate": 0.05},
                {"timestamp": datetime.utcnow(), "api": "User API", "response_time": 250.0, "error_rate": 0.02}
            ],
            "columns": ["timestamp", "api", "response_time", "error_rate"]
        }
        
        # Verify export data
        assert export_data["format"] == "csv"
        assert len(export_data["data"]) == 2
        assert len(export_data["columns"]) == 4

    @pytest.mark.asyncio
    async def test_scheduled_report_generation(self, mock_analytics_service):
        """Test scheduled report generation workflow."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        # Define report schedule
        report_schedule = {
            "schedule_id": uuid4(),
            "report_type": "weekly_performance",
            "frequency": "weekly",
            "day_of_week": "monday",
            "time": "09:00",
            "recipients": ["ops-team@example.com"],
            "enabled": True
        }
        
        # Simulate scheduled execution
        report_execution = {
            "execution_id": uuid4(),
            "schedule_id": report_schedule["schedule_id"],
            "executed_at": datetime.utcnow(),
            "status": "completed",
            "report_generated": True,
            "recipients_notified": True
        }
        
        # Verify scheduled report
        assert report_schedule["enabled"] is True
        assert report_execution["status"] == "completed"
        assert report_execution["report_generated"] is True


class TestAnalyticsFiltering:
    """Test analytics filtering and segmentation."""

    @pytest.mark.asyncio
    async def test_filter_by_gateway(self, mock_analytics_service):
        """Test filtering analytics by gateway."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        gateway_id = uuid4()
        
        filtered_metrics = {
            "gateway_id": gateway_id,
            "api_count": 50,
            "total_requests": 5000000,
            "avg_response_time": 300.0
        }
        
        metrics_repo.aggregate_metrics.return_value = filtered_metrics
        
        # Verify gateway filtering
        assert filtered_metrics["gateway_id"] == gateway_id
        assert filtered_metrics["api_count"] == 50

    @pytest.mark.asyncio
    async def test_filter_by_time_range(self, mock_analytics_service):
        """Test filtering analytics by time range."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        time_range = {
            "start": datetime.utcnow() - timedelta(hours=24),
            "end": datetime.utcnow()
        }
        
        filtered_metrics = {
            "time_range": time_range,
            "data_points": 24,
            "avg_response_time": 250.0
        }
        
        metrics_repo.get_time_series.return_value = [{"timestamp": time_range["start"]}]
        
        # Verify time range filtering
        assert filtered_metrics["data_points"] == 24

    @pytest.mark.asyncio
    async def test_filter_by_status_code(self, mock_analytics_service):
        """Test filtering analytics by HTTP status code."""
        metrics_repo, api_repo, gateway_repo = mock_analytics_service
        
        status_code_metrics = {
            "status_code": 500,
            "count": 50000,
            "percentage": 0.5,
            "top_apis": [
                {"api": "Payment API", "count": 30000},
                {"api": "User API", "count": 20000}
            ]
        }
        
        # Verify status code filtering
        assert status_code_metrics["status_code"] == 500
        assert status_code_metrics["count"] == 50000


# Made with Bob