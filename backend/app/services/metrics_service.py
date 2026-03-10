"""
Metrics Service

Handles metrics collection from Gateways, aggregation, and analysis.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.adapters.factory import GatewayAdapterFactory
from app.models.metric import Metric
from app.models.gateway import GatewayStatus

logger = logging.getLogger(__name__)


class MetricsService:
    """Service for collecting and managing API metrics."""
    
    def __init__(
        self,
        metrics_repository: MetricsRepository,
        api_repository: APIRepository,
        gateway_repository: GatewayRepository,
        adapter_factory: GatewayAdapterFactory,
    ):
        """
        Initialize the Metrics Service.
        
        Args:
            metrics_repository: Repository for metrics operations
            api_repository: Repository for API operations
            gateway_repository: Repository for Gateway operations
            adapter_factory: Factory for creating Gateway adapters
        """
        self.metrics_repo = metrics_repository
        self.api_repo = api_repository
        self.gateway_repo = gateway_repository
        self.adapter_factory = adapter_factory
    
    async def collect_all_metrics(self) -> Dict[str, Any]:
        """
        Collect metrics from all connected Gateways.
        
        Returns:
            dict: Collection results with statistics
        """
        logger.info("Starting metrics collection across all gateways")
        
        # Get all connected gateways
        gateways, total = self.gateway_repo.find_connected_gateways(size=1000)
        
        if not gateways:
            logger.warning("No connected gateways found")
            return {
                "total_gateways": 0,
                "successful_gateways": 0,
                "failed_gateways": 0,
                "total_metrics_collected": 0,
                "errors": [],
            }
        
        results = {
            "total_gateways": len(gateways),
            "successful_gateways": 0,
            "failed_gateways": 0,
            "total_metrics_collected": 0,
            "errors": [],
        }
        
        # Collect metrics from each gateway
        for gateway in gateways:
            try:
                gateway_result = await self.collect_gateway_metrics(gateway.id)
                results["successful_gateways"] += 1
                results["total_metrics_collected"] += gateway_result["metrics_collected"]
            except Exception as e:
                logger.error(f"Failed to collect metrics from gateway {gateway.id}: {e}")
                results["failed_gateways"] += 1
                results["errors"].append({
                    "gateway_id": str(gateway.id),
                    "gateway_name": gateway.name,
                    "error": str(e),
                })
        
        logger.info(
            f"Metrics collection complete: {results['total_metrics_collected']} metrics "
            f"from {results['successful_gateways']}/{results['total_gateways']} gateways"
        )
        
        return results
    
    async def collect_gateway_metrics(
        self,
        gateway_id: UUID,
        time_range_minutes: int = 5,
    ) -> Dict[str, Any]:
        """
        Collect metrics from a specific Gateway.
        
        Args:
            gateway_id: Gateway UUID
            time_range_minutes: Time range for metrics collection
            
        Returns:
            dict: Collection results for this gateway
            
        Raises:
            ValueError: If gateway not found
            RuntimeError: If collection fails
        """
        logger.info(f"Collecting metrics from gateway {gateway_id}")
        
        # Get gateway configuration
        gateway = self.gateway_repo.get(str(gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {gateway_id} not found")
        
        if gateway.status != GatewayStatus.CONNECTED:
            raise RuntimeError(f"Gateway {gateway_id} is not connected")
        
        try:
            # Create adapter for this gateway
            adapter = self.adapter_factory.create_adapter(gateway)
            
            # Connect to gateway
            await adapter.connect()
            
            # Collect metrics for all APIs
            metrics = await adapter.collect_metrics(
                api_id=None,  # Collect for all APIs
                time_range_minutes=time_range_minutes,
            )
            
            # Store metrics in bulk
            if metrics:
                stored_count = self.metrics_repo.bulk_create_metrics(metrics)
                
                # Update current metrics for each API
                for metric in metrics:
                    self._update_api_current_metrics(metric)
            else:
                stored_count = 0
            
            # Disconnect from gateway
            await adapter.disconnect()
            
            result = {
                "gateway_id": str(gateway_id),
                "gateway_name": gateway.name,
                "metrics_collected": stored_count,
                "timestamp": datetime.utcnow().isoformat(),
            }
            
            logger.info(
                f"Metrics collection complete for gateway {gateway_id}: "
                f"{stored_count} metrics stored"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Metrics collection failed for gateway {gateway_id}: {e}")
            raise RuntimeError(f"Failed to collect metrics from gateway {gateway_id}: {e}")
    
    async def collect_api_metrics(
        self,
        api_id: UUID,
        time_range_minutes: int = 5,
    ) -> List[Metric]:
        """
        Collect metrics for a specific API.
        
        Args:
            api_id: API UUID
            time_range_minutes: Time range for metrics collection
            
        Returns:
            list[Metric]: Collected metrics
            
        Raises:
            ValueError: If API not found
            RuntimeError: If collection fails
        """
        logger.info(f"Collecting metrics for API {api_id}")
        
        # Get API
        api = self.api_repo.get(str(api_id))
        if not api:
            raise ValueError(f"API {api_id} not found")
        
        # Get gateway
        gateway = self.gateway_repo.get(str(api.gateway_id))
        if not gateway:
            raise ValueError(f"Gateway {api.gateway_id} not found")
        
        try:
            # Create adapter
            adapter = self.adapter_factory.create_adapter(gateway)
            await adapter.connect()
            
            # Collect metrics for this API
            metrics = await adapter.collect_metrics(
                api_id=str(api_id),
                time_range_minutes=time_range_minutes,
            )
            
            # Store metrics
            if metrics:
                self.metrics_repo.bulk_create_metrics(metrics)
                
                # Update current metrics
                for metric in metrics:
                    self._update_api_current_metrics(metric)
            
            await adapter.disconnect()
            
            logger.info(f"Collected {len(metrics)} metrics for API {api_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics collection failed for API {api_id}: {e}")
            raise RuntimeError(f"Failed to collect metrics for API {api_id}: {e}")
    
    def _update_api_current_metrics(self, metric: Metric) -> None:
        """
        Update the current metrics snapshot for an API.
        
        Args:
            metric: Metric to update from
        """
        try:
            from app.models.api import CurrentMetrics
            
            current_metrics = CurrentMetrics(
                response_time_p50=metric.response_time_p50,
                response_time_p95=metric.response_time_p95,
                response_time_p99=metric.response_time_p99,
                error_rate=metric.error_rate,
                throughput=metric.throughput,
                availability=metric.availability,
                last_error=None,
                measured_at=metric.timestamp,
            )
            
            updates = {
                "current_metrics": current_metrics.model_dump(),
            }
            
            self.api_repo.update(str(metric.api_id), updates)
            
        except Exception as e:
            logger.warning(f"Failed to update current metrics for API {metric.api_id}: {e}")
    
    def get_api_metrics(
        self,
        api_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> tuple[List[Metric], int]:
        """
        Get metrics for an API within a time range.
        
        Args:
            api_id: API UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of metrics to return
            
        Returns:
            tuple[List[Metric], int]: List of metrics and total count
        """
        return self.metrics_repo.find_by_api(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            size=limit,
        )
    
    def get_gateway_metrics(
        self,
        gateway_id: UUID,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> tuple[List[Metric], int]:
        """
        Get metrics for all APIs in a Gateway within a time range.
        
        Args:
            gateway_id: Gateway UUID
            start_time: Start of time range (default: 24 hours ago)
            end_time: End of time range (default: now)
            limit: Maximum number of metrics to return
            
        Returns:
            tuple[List[Metric], int]: List of metrics and total count
        """
        return self.metrics_repo.find_by_gateway(
            gateway_id=gateway_id,
            start_time=start_time,
            end_time=end_time,
            size=limit,
        )
    
    def get_latest_metric(self, api_id: UUID) -> Optional[Metric]:
        """
        Get the most recent metric for an API.
        
        Args:
            api_id: API UUID
            
        Returns:
            Latest metric if found, None otherwise
        """
        return self.metrics_repo.get_latest_metric(api_id)
    
    def get_time_series(
        self,
        api_id: UUID,
        start_time: datetime,
        end_time: datetime,
        interval: str = "1h",
    ) -> List[Dict[str, Any]]:
        """
        Get aggregated time-series metrics for an API.
        
        Args:
            api_id: API UUID
            start_time: Start of time range
            end_time: End of time range
            interval: Aggregation interval (e.g., "1m", "5m", "1h", "1d")
            
        Returns:
            List of aggregated metric buckets
        """
        return self.metrics_repo.get_time_series(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            interval=interval,
        )
    
    def get_aggregated_metrics(
        self,
        api_id: UUID,
        start_time: datetime,
        end_time: datetime,
    ) -> Dict[str, Any]:
        """
        Get aggregated metrics for an API over a time range.
        
        Args:
            api_id: API UUID
            start_time: Start of time range
            end_time: End of time range
            
        Returns:
            Dictionary with aggregated metrics
        """
        return self.metrics_repo.get_aggregated_metrics(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )
    
    def analyze_trends(
        self,
        api_id: UUID,
        metric_name: str,
        time_range_hours: int = 24,
    ) -> Dict[str, Any]:
        """
        Analyze trends for a specific metric.
        
        Args:
            api_id: API UUID
            metric_name: Name of metric to analyze (e.g., "response_time_p95", "error_rate")
            time_range_hours: Hours of historical data to analyze
            
        Returns:
            dict: Trend analysis results
        """
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=time_range_hours)
        
        # Get time series data
        time_series = self.get_time_series(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            interval="1h",
        )
        
        if not time_series:
            return {
                "metric_name": metric_name,
                "trend": "insufficient_data",
                "direction": None,
                "change_percentage": 0.0,
                "current_value": None,
                "average_value": None,
            }
        
        # Extract metric values
        metric_key = f"avg_{metric_name}"
        values: List[float] = []
        for bucket in time_series:
            value = bucket.get(metric_key)
            if value is not None and isinstance(value, (int, float)):
                values.append(float(value))
        
        if not values:
            return {
                "metric_name": metric_name,
                "trend": "no_data",
                "direction": None,
                "change_percentage": 0.0,
                "current_value": None,
                "average_value": None,
            }
        
        # Calculate trend
        current_value: float = values[-1]
        average_value: float = sum(values) / len(values)
        
        # Simple linear regression for trend direction
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = average_value
        
        numerator = sum((i - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((i - x_mean) ** 2 for i in range(n))
        
        slope = numerator / denominator if denominator != 0 else 0
        
        # Determine trend direction
        if abs(slope) < 0.01 * average_value:
            trend = "stable"
            direction = "flat"
        elif slope > 0:
            trend = "increasing"
            direction = "up"
        else:
            trend = "decreasing"
            direction = "down"
        
        # Calculate change percentage
        if len(values) > 1:
            first_value = values[0]
            change_percentage = ((current_value - first_value) / first_value * 100) if first_value != 0 else 0
        else:
            change_percentage = 0.0
        
        return {
            "metric_name": metric_name,
            "trend": trend,
            "direction": direction,
            "change_percentage": round(change_percentage, 2),
            "current_value": round(current_value, 2),
            "average_value": round(average_value, 2),
            "slope": round(slope, 4),
            "data_points": len(values),
        }
    
    def calculate_health_score(self, api_id: UUID) -> float:
        """
        Calculate health score for an API based on recent metrics.
        
        Args:
            api_id: API UUID
            
        Returns:
            Health score (0-100)
        """
        # Get metrics from last hour
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        aggregated = self.get_aggregated_metrics(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
        )
        
        if not aggregated:
            return 50.0  # Default score if no data
        
        # Calculate health score based on multiple factors
        # Availability (40% weight)
        availability_score = aggregated.get("avg_availability", 100.0) * 0.4
        
        # Error rate (30% weight) - inverse score
        error_rate = aggregated.get("avg_error_rate", 0.0)
        error_score = (1 - min(error_rate, 1.0)) * 30.0
        
        # Response time (30% weight) - inverse score
        # Assume good response time is < 200ms, bad is > 1000ms
        p95_response = aggregated.get("avg_response_time_p95", 200.0)
        if p95_response < 200:
            response_score = 30.0
        elif p95_response > 1000:
            response_score = 0.0
        else:
            response_score = 30.0 * (1 - (p95_response - 200) / 800)
        
        health_score = availability_score + error_score + response_score
        
        return round(min(max(health_score, 0.0), 100.0), 2)


# Made with Bob