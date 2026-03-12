"""Metrics MCP Server for API Intelligence Plane.

This MCP server provides tools for collecting and analyzing API metrics from
connected API Gateways. It acts as a thin wrapper around the backend REST API,
exposing tools that AI agents can use to interact with metrics functionality.

Port: 8002
Transport: Streamable HTTP
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import Any, List, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.backend_client import BackendClient
from common.health import HealthChecker, create_health_tool
from common.mcp_base import BaseMCPServer

logger = logging.getLogger(__name__)


class MetricsMCPServer(BaseMCPServer):
    """MCP Server for API Metrics operations.
    
    Provides tools for:
    - Collecting metrics from Gateways
    - Retrieving time-series metrics data
    - Analyzing metric trends and patterns
    
    This server acts as a thin wrapper around the backend REST API,
    delegating all business logic to the backend services.
    """

    def __init__(self):
        """Initialize Metrics MCP server."""
        super().__init__(name="metrics-server", version="1.0.0")
        
        # Initialize backend client instead of OpenSearch
        self.backend_client = BackendClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        
        # Register tools
        self._register_tools()
        
        logger.info("Metrics MCP server initialized (using backend API)")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        @self.tool(description="Check Metrics server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.
            
            Returns:
                dict: Health status including backend connectivity
            """
            try:
                # Test backend connectivity
                await self.backend_client.list_apis(page=1, page_size=1)
                backend_status = "connected"
            except Exception as e:
                logger.error(f"Backend health check failed: {e}")
                backend_status = "disconnected"
            
            return {
                "status": "healthy" if backend_status == "connected" else "degraded",
                "server": self.name,
                "version": self.version,
                "backend_status": backend_status,
                "timestamp": datetime.utcnow().isoformat(),
            }
        
        # Server info tool
        @self.tool(description="Get Metrics server information")
        def server_info() -> dict[str, Any]:
            """Get server information.
            
            Returns:
                dict: Server metadata and capabilities
            """
            info = self.get_server_info()
            info.update({
                "port": 8002,
                "transport": "streamable-http",
                "architecture": "thin_wrapper",
                "backend_url": self.backend_client.base_url,
                "capabilities": [
                    "metrics_collection",
                    "timeseries_analysis",
                    "trend_detection",
                    "anomaly_detection"
                ]
            })
            return info
        
        # Metrics tools
        @self.tool(description="Collect current metrics from Gateway")
        async def collect_metrics(gateway_id: str, api_ids: Optional[List[str]] = None) -> dict[str, Any]:
            """Collect metrics from a Gateway.
            
            Note: This tool retrieves already-collected metrics from the backend.
            The backend handles the actual metrics collection process via scheduled jobs.
            
            Args:
                gateway_id: Gateway UUID to collect metrics from
                api_ids: Specific API UUIDs to collect (empty = all)
                
            Returns:
                dict: Collection results with metrics summary
            """
            return await self._collect_metrics_impl(gateway_id, api_ids)
        
        @self.tool(description="Retrieve time-series metrics for analysis")
        async def get_metrics_timeseries(
            api_id: str,
            start_time: str,
            end_time: str,
            interval: str = "5m",
            metrics: Optional[List[str]] = None
        ) -> dict[str, Any]:
            """Get time-series metrics data.
            
            Args:
                api_id: Target API UUID
                start_time: Start of time range (ISO 8601)
                end_time: End of time range (ISO 8601)
                interval: Aggregation interval (1m, 5m, 15m, 1h, 1d)
                metrics: Specific metrics to retrieve
                
            Returns:
                dict: Time-series data points
            """
            return await self._get_metrics_timeseries_impl(
                api_id, start_time, end_time, interval, metrics
            )
        
        @self.tool(description="Analyze metric trends and patterns")
        async def analyze_trends(
            api_id: str,
            metric: str,
            lookback_hours: int = 24
        ) -> dict[str, Any]:
            """Analyze trends for a specific metric.
            
            Args:
                api_id: Target API UUID
                metric: Metric to analyze (response_time, error_rate, throughput, availability)
                lookback_hours: Hours to look back (1-720)
                
            Returns:
                dict: Trend analysis with anomalies and forecast
            """
            return await self._analyze_trends_impl(api_id, metric, lookback_hours)

    async def initialize(self) -> None:
        """Initialize server resources."""
        await super().initialize()
        logger.info("Metrics server initialized and ready")
    
    async def cleanup(self) -> None:
        """Cleanup server resources."""
        await super().cleanup()
        
        # Close backend client connection
        await self.backend_client.close()
        logger.info("Metrics server disconnected from backend")
    
    async def _collect_metrics_impl(
        self, gateway_id: str, api_ids: Optional[List[str]] = None
    ) -> dict[str, Any]:
        """Implementation of collect_metrics tool.
        
        Args:
            gateway_id: Gateway UUID to collect from
            api_ids: Specific API UUIDs (None = all)
            
        Returns:
            dict: Collection results with summary
        """
        start_time = datetime.utcnow()
        
        try:
            # Validate UUID format
            try:
                UUID(gateway_id)
            except ValueError:
                return {
                    "collected_count": 0,
                    "collection_time_ms": 0,
                    "metrics_summary": {
                        "avg_response_time": 0,
                        "total_requests": 0,
                        "avg_error_rate": 0
                    },
                    "error": f"Invalid gateway_id format: {gateway_id}"
                }
            
            # Get APIs for this gateway
            apis_response = await self.backend_client.list_apis(
                gateway_id=gateway_id,
                page_size=1000
            )
            
            apis = apis_response.get("items", [])
            
            # Filter by specific API IDs if provided
            if api_ids:
                apis = [api for api in apis if api.get("id") in api_ids]
            
            # Collect metrics summary from current_metrics field
            total_requests = 0
            total_response_time = 0
            total_errors = 0
            count = 0
            
            for api in apis:
                current_metrics = api.get("current_metrics", {})
                if current_metrics:
                    count += 1
                    total_response_time += current_metrics.get("response_time_p50", 0)
                    error_rate = current_metrics.get("error_rate", 0)
                    if error_rate > 0:
                        total_errors += 1
                    # Estimate requests from throughput
                    throughput = current_metrics.get("throughput", 0)
                    total_requests += int(throughput * 300)  # 5 minutes worth
            
            avg_response_time = total_response_time / count if count > 0 else 0
            avg_error_rate = (total_errors / count * 100) if count > 0 else 0
            
            collection_time_ms = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            
            return {
                "collected_count": count,
                "collection_time_ms": collection_time_ms,
                "metrics_summary": {
                    "avg_response_time": round(avg_response_time, 2),
                    "total_requests": total_requests,
                    "avg_error_rate": round(avg_error_rate, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {
                "collected_count": 0,
                "collection_time_ms": 0,
                "metrics_summary": {
                    "avg_response_time": 0,
                    "total_requests": 0,
                    "avg_error_rate": 0
                },
                "error": str(e)
            }
    
    async def _get_metrics_timeseries_impl(
        self,
        api_id: str,
        start_time: str,
        end_time: str,
        interval: str = "5m",
        metrics: Optional[List[str]] = None
    ) -> dict[str, Any]:
        """Implementation of get_metrics_timeseries tool.
        
        Args:
            api_id: Target API UUID
            start_time: Start time (ISO 8601)
            end_time: End time (ISO 8601)
            interval: Aggregation interval
            metrics: Specific metrics to retrieve
            
        Returns:
            dict: Time-series data
        """
        try:
            # Validate UUID format
            try:
                UUID(api_id)
            except ValueError:
                return {
                    "api_id": api_id,
                    "time_range": {
                        "start": start_time,
                        "end": end_time
                    },
                    "data_points": [],
                    "error": f"Invalid api_id format: {api_id}"
                }
            
            # Get metrics from backend
            response = await self.backend_client.get_api_metrics(
                api_id=api_id,
                start_time=start_time,
                end_time=end_time,
                interval=interval
            )
            
            # Extract time series data
            time_series = response.get("time_series", [])
            
            # Format data points
            data_points = []
            for point in time_series:
                data_points.append({
                    "timestamp": point.get("timestamp"),
                    "response_time_p50": round(point.get("avg_response_time_p50", 0), 2),
                    "response_time_p95": round(point.get("avg_response_time_p95", 0), 2),
                    "response_time_p99": round(point.get("avg_response_time_p99", 0), 2),
                    "error_rate": round(point.get("avg_error_rate", 0), 2),
                    "throughput": int(point.get("sum_throughput", 0)),
                    "availability": round(point.get("avg_availability", 0), 2)
                })
            
            return {
                "api_id": api_id,
                "time_range": {
                    "start": start_time,
                    "end": end_time
                },
                "data_points": data_points
            }
            
        except Exception as e:
            logger.error(f"Error getting metrics timeseries: {e}")
            return {
                "api_id": api_id,
                "time_range": {
                    "start": start_time,
                    "end": end_time
                },
                "data_points": [],
                "error": str(e)
            }
    
    async def _analyze_trends_impl(
        self, api_id: str, metric: str, lookback_hours: int = 24
    ) -> dict[str, Any]:
        """Implementation of analyze_trends tool.
        
        Args:
            api_id: Target API UUID
            metric: Metric to analyze
            lookback_hours: Hours to look back
            
        Returns:
            dict: Trend analysis results
        """
        try:
            # Validate UUID format
            try:
                UUID(api_id)
            except ValueError:
                return {
                    "trend": "unknown",
                    "trend_strength": 0.0,
                    "anomalies_detected": [],
                    "forecast": {
                        "next_24h_trend": "unknown",
                        "confidence": 0.0
                    },
                    "error": f"Invalid api_id format: {api_id}"
                }
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Get metrics from backend
            response = await self.backend_client.get_api_metrics(
                api_id=api_id,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                interval="1h"
            )
            
            time_series = response.get("time_series", [])
            
            # Map metric name to field
            metric_field_map = {
                "response_time": "avg_response_time_p50",
                "error_rate": "avg_error_rate",
                "throughput": "sum_throughput",
                "availability": "avg_availability"
            }
            
            field_name = metric_field_map.get(metric, "avg_response_time_p50")
            
            # Extract values for analysis
            values = []
            timestamps = []
            for point in time_series:
                value = point.get(field_name, 0)
                if value is not None:
                    values.append(float(value))
                    timestamps.append(point.get("timestamp"))
            
            # Simple trend analysis
            if len(values) < 2:
                trend = "stable"
                trend_strength = 0.0
            else:
                # Calculate linear trend
                first_half_avg = sum(values[:len(values)//2]) / (len(values)//2)
                second_half_avg = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
                
                change_pct = ((second_half_avg - first_half_avg) / first_half_avg * 100) if first_half_avg > 0 else 0
                
                if abs(change_pct) < 5:
                    trend = "stable"
                    trend_strength = 0.2
                elif change_pct > 20:
                    trend = "increasing"
                    trend_strength = min(abs(change_pct) / 100, 1.0)
                elif change_pct < -20:
                    trend = "decreasing"
                    trend_strength = min(abs(change_pct) / 100, 1.0)
                else:
                    trend = "volatile"
                    trend_strength = 0.5
            
            # Simple anomaly detection (values > 2 std deviations)
            anomalies = []
            if len(values) > 10:
                mean = sum(values) / len(values)
                variance = sum((x - mean) ** 2 for x in values) / len(values)
                std_dev = variance ** 0.5
                
                for i, value in enumerate(values):
                    if abs(value - mean) > 2 * std_dev:
                        severity = "high" if abs(value - mean) > 3 * std_dev else "medium"
                        anomalies.append({
                            "timestamp": timestamps[i],
                            "value": round(value, 2),
                            "severity": severity
                        })
            
            # Simple forecast
            forecast_trend = "stable"
            confidence = 0.6
            
            if trend == "increasing":
                forecast_trend = "likely_to_increase"
                confidence = trend_strength * 0.8
            elif trend == "decreasing":
                forecast_trend = "likely_to_decrease"
                confidence = trend_strength * 0.8
            
            return {
                "trend": trend,
                "trend_strength": round(trend_strength, 2),
                "anomalies_detected": anomalies[:10],  # Limit to 10 most recent
                "forecast": {
                    "next_24h_trend": forecast_trend,
                    "confidence": round(confidence, 2)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {
                "trend": "unknown",
                "trend_strength": 0.0,
                "anomalies_detected": [],
                "forecast": {
                    "next_24h_trend": "unknown",
                    "confidence": 0.0
                },
                "error": str(e)
            }


def main():
    """Main entry point for Metrics MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create server
    server = MetricsMCPServer()
    
    # Run MCP server on port 8000 (matches Docker port mapping)
    # FastMCP's built-in server will handle both MCP and health endpoints
    server.run(transport="streamable-http", port=8000)


if __name__ == "__main__":
    main()

# Made with Bob