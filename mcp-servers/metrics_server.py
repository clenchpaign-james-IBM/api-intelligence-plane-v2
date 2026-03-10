"""Metrics MCP Server for API Intelligence Plane.

This MCP server provides tools for collecting and analyzing API metrics from
connected API Gateways. It exposes tools that AI agents can use to interact
with metrics functionality.

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

from common.health import HealthChecker, create_health_tool
from common.http_health import HTTPHealthServer
from common.mcp_base import BaseMCPServer
from common.opensearch import MCPOpenSearchClient

logger = logging.getLogger(__name__)


class MetricsMCPServer(BaseMCPServer):
    """MCP Server for API Metrics operations.
    
    Provides tools for:
    - Collecting metrics from Gateways
    - Retrieving time-series metrics data
    - Analyzing metric trends and patterns
    """

    def __init__(self):
        """Initialize Metrics MCP server."""
        super().__init__(name="metrics-server", version="1.0.0")
        
        # Initialize OpenSearch client
        self.opensearch = MCPOpenSearchClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        self.health_checker.set_opensearch_client(self.opensearch)
        
        # Register tools
        self._register_tools()
        
        logger.info("Metrics MCP server initialized")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        health_tool = create_health_tool(self.health_checker)
        
        @self.tool(description="Check Metrics server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.
            
            Returns:
                dict: Health status including OpenSearch connectivity
            """
            return await health_tool()
        
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
        
        # Connect to OpenSearch
        await self.opensearch.connect()
        logger.info("Metrics server connected to OpenSearch")
    
    async def cleanup(self) -> None:
        """Cleanup server resources."""
        await super().cleanup()
        
        # Close OpenSearch connection
        await self.opensearch.close()
        logger.info("Metrics server disconnected from OpenSearch")
    
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
            # Build query to get recent metrics
            query = {
                "bool": {
                    "must": [
                        {"term": {"gateway_id": gateway_id}},
                        {
                            "range": {
                                "timestamp": {
                                    "gte": "now-5m",
                                    "lte": "now"
                                }
                            }
                        }
                    ]
                }
            }
            
            # Add API filter if specified
            if api_ids:
                query["bool"]["must"].append({
                    "terms": {"api_id": api_ids}
                })
            
            # Get current month's index
            index_name = f"api-metrics-{datetime.utcnow().strftime('%Y.%m')}"
            
            # Query metrics
            result = await self.opensearch.search(
                index=index_name,
                query=query,
                size=1000
            )
            
            # Calculate summary statistics
            metrics_data = []
            total_requests = 0
            total_response_time = 0
            total_errors = 0
            
            for hit in result.get("hits", {}).get("hits", []):
                source = hit["_source"]
                metrics_data.append(source)
                
                total_requests += source.get("request_count", 0)
                total_response_time += source.get("response_time_p50", 0)
                if source.get("error_rate", 0) > 0:
                    total_errors += 1
            
            count = len(metrics_data)
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
            # Parse timestamps
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            
            # Build query
            query = {
                "bool": {
                    "must": [
                        {"term": {"api_id": api_id}},
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_dt.isoformat(),
                                    "lte": end_dt.isoformat()
                                }
                            }
                        }
                    ]
                }
            }
            
            # Determine which indices to query (may span multiple months)
            indices = []
            current = start_dt
            while current <= end_dt:
                indices.append(f"api-metrics-{current.strftime('%Y.%m')}")
                current = current.replace(day=1) + timedelta(days=32)
                current = current.replace(day=1)
            
            index_pattern = ",".join(indices)
            
            # Query with aggregations for time-series
            aggregations = {
                "timeseries": {
                    "date_histogram": {
                        "field": "timestamp",
                        "fixed_interval": interval,
                        "min_doc_count": 0
                    },
                    "aggs": {
                        "avg_p50": {"avg": {"field": "response_time_p50"}},
                        "avg_p95": {"avg": {"field": "response_time_p95"}},
                        "avg_p99": {"avg": {"field": "response_time_p99"}},
                        "avg_error_rate": {"avg": {"field": "error_rate"}},
                        "sum_throughput": {"sum": {"field": "request_count"}},
                        "avg_availability": {"avg": {"field": "availability"}}
                    }
                }
            }
            
            result = await self.opensearch.aggregate(
                index=index_pattern,
                query=query,
                aggregations=aggregations
            )
            
            # Format data points
            data_points = []
            for bucket in result.get("timeseries", {}).get("buckets", []):
                data_points.append({
                    "timestamp": bucket["key_as_string"],
                    "response_time_p50": round(bucket.get("avg_p50", {}).get("value", 0), 2),
                    "response_time_p95": round(bucket.get("avg_p95", {}).get("value", 0), 2),
                    "response_time_p99": round(bucket.get("avg_p99", {}).get("value", 0), 2),
                    "error_rate": round(bucket.get("avg_error_rate", {}).get("value", 0), 2),
                    "throughput": int(bucket.get("sum_throughput", {}).get("value", 0)),
                    "availability": round(bucket.get("avg_availability", {}).get("value", 0), 2)
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
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=lookback_hours)
            
            # Map metric name to field
            metric_field_map = {
                "response_time": "response_time_p50",
                "error_rate": "error_rate",
                "throughput": "request_count",
                "availability": "availability"
            }
            
            field_name = metric_field_map.get(metric, "response_time_p50")
            
            # Build query
            query = {
                "bool": {
                    "must": [
                        {"term": {"api_id": api_id}},
                        {
                            "range": {
                                "timestamp": {
                                    "gte": start_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }
                            }
                        }
                    ]
                }
            }
            
            # Get index pattern
            indices = []
            current = start_time
            while current <= end_time:
                indices.append(f"api-metrics-{current.strftime('%Y.%m')}")
                current = current.replace(day=1) + timedelta(days=32)
                current = current.replace(day=1)
            
            index_pattern = ",".join(set(indices))
            
            # Query metrics
            result = await self.opensearch.search(
                index=index_pattern,
                query=query,
                size=1000
            )
            
            # Extract values for analysis
            values = []
            timestamps = []
            for hit in result.get("hits", {}).get("hits", []):
                source = hit["_source"]
                values.append(source.get(field_name, 0))
                timestamps.append(source.get("timestamp"))
            
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
    
    # Start HTTP health server in background thread on port 8000
    health_server = HTTPHealthServer(server.health_checker, port=8000)
    health_server.start()
    
    try:
        # Run MCP server on port 8001 (this will block)
        server.run(transport="streamable-http", port=8001)
    finally:
        # Cleanup
        health_server.stop()


if __name__ == "__main__":
    main()

# Made with Bob