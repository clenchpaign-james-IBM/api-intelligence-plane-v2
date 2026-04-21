"""
Metrics Generator Utility

Provides utilities for generating realistic metric patterns for testing,
including stable, degrading, spiking, and volatile patterns.
"""

from datetime import datetime, timedelta
from uuid import UUID, uuid4
from typing import List, Literal
import random
import math

from app.models.base.metric import Metric


MetricPattern = Literal["stable", "degrading", "spiking", "volatile", "recovering"]


class MetricsGenerator:
    """Generates realistic metric patterns for testing."""
    
    @staticmethod
    def generate_stable_metrics(
        api_id: UUID,
        gateway_id: UUID,
        hours: int = 24,
        base_error_rate: float = 0.01,
        base_response_time: float = 150.0,
        base_availability: float = 99.9
    ) -> List[Metric]:
        """
        Generate stable metrics with minimal variation.
        
        Args:
            api_id: API ID
            gateway_id: Gateway ID
            hours: Number of hours of metrics
            base_error_rate: Base error rate (0-1)
            base_response_time: Base response time in ms
            base_availability: Base availability percentage
        
        Returns:
            List of stable metrics
        """
        now = datetime.utcnow()
        metrics = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-1-i)
            
            # Add small random variation (±5%)
            error_rate = base_error_rate * random.uniform(0.95, 1.05)
            response_time_p95 = base_response_time * random.uniform(0.95, 1.05)
            availability = base_availability * random.uniform(0.999, 1.001)
            
            # Clamp values
            error_rate = max(0.0, min(1.0, error_rate))
            availability = max(0.0, min(100.0, availability))
            
            metric = MetricsGenerator._create_metric(
                api_id=api_id,
                gateway_id=gateway_id,
                timestamp=timestamp,
                error_rate=error_rate,
                response_time_p95=response_time_p95,
                availability=availability,
            )
            metrics.append(metric)
        
        return metrics
    
    @staticmethod
    def generate_degrading_metrics(
        api_id: UUID,
        gateway_id: UUID,
        hours: int = 24,
        start_error_rate: float = 0.02,
        end_error_rate: float = 0.15,
        start_response_time: float = 100.0,
        end_response_time: float = 400.0,
        start_availability: float = 99.9,
        end_availability: float = 94.0,
        degradation_curve: Literal["linear", "exponential", "logarithmic"] = "linear"
    ) -> List[Metric]:
        """
        Generate degrading metrics showing performance decline.
        
        Args:
            api_id: API ID
            gateway_id: Gateway ID
            hours: Number of hours of metrics
            start_error_rate: Starting error rate
            end_error_rate: Ending error rate
            start_response_time: Starting response time
            end_response_time: Ending response time
            start_availability: Starting availability
            end_availability: Ending availability
            degradation_curve: Type of degradation curve
        
        Returns:
            List of degrading metrics
        """
        now = datetime.utcnow()
        metrics = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-1-i)
            
            # Calculate progress (0 to 1)
            progress = i / (hours - 1) if hours > 1 else 0
            
            # Apply degradation curve
            if degradation_curve == "exponential":
                # Slow start, rapid decline
                curve_progress = progress ** 2
            elif degradation_curve == "logarithmic":
                # Rapid start, slow decline
                curve_progress = math.log(1 + progress * (math.e - 1)) / math.log(math.e)
            else:  # linear
                curve_progress = progress
            
            # Calculate values
            error_rate = start_error_rate + (end_error_rate - start_error_rate) * curve_progress
            response_time_p95 = start_response_time + (end_response_time - start_response_time) * curve_progress
            availability = start_availability - (start_availability - end_availability) * curve_progress
            
            # Add small random noise
            error_rate *= random.uniform(0.95, 1.05)
            response_time_p95 *= random.uniform(0.95, 1.05)
            availability *= random.uniform(0.995, 1.005)
            
            # Clamp values
            error_rate = max(0.0, min(1.0, error_rate))
            availability = max(0.0, min(100.0, availability))
            
            metric = MetricsGenerator._create_metric(
                api_id=api_id,
                gateway_id=gateway_id,
                timestamp=timestamp,
                error_rate=error_rate,
                response_time_p95=response_time_p95,
                availability=availability,
            )
            metrics.append(metric)
        
        return metrics
    
    @staticmethod
    def generate_spiking_metrics(
        api_id: UUID,
        gateway_id: UUID,
        hours: int = 24,
        spike_start_hour: int = 18,
        spike_duration: int = 6,
        base_error_rate: float = 0.01,
        spike_error_rate: float = 0.20,
        base_response_time: float = 150.0,
        spike_response_time: float = 600.0
    ) -> List[Metric]:
        """
        Generate metrics with a sudden spike in errors/latency.
        
        Args:
            api_id: API ID
            gateway_id: Gateway ID
            hours: Number of hours of metrics
            spike_start_hour: Hour when spike starts (0-based)
            spike_duration: Duration of spike in hours
            base_error_rate: Normal error rate
            spike_error_rate: Error rate during spike
            base_response_time: Normal response time
            spike_response_time: Response time during spike
        
        Returns:
            List of metrics with spike
        """
        now = datetime.utcnow()
        metrics = []
        
        spike_end_hour = spike_start_hour + spike_duration
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-1-i)
            
            # Determine if in spike window
            if spike_start_hour <= i < spike_end_hour:
                # During spike
                spike_progress = (i - spike_start_hour) / spike_duration
                
                # Ramp up at start, ramp down at end
                if spike_progress < 0.2:
                    # Ramp up
                    intensity = spike_progress / 0.2
                elif spike_progress > 0.8:
                    # Ramp down
                    intensity = (1.0 - spike_progress) / 0.2
                else:
                    # Full spike
                    intensity = 1.0
                
                error_rate = base_error_rate + (spike_error_rate - base_error_rate) * intensity
                response_time_p95 = base_response_time + (spike_response_time - base_response_time) * intensity
                availability = 99.9 - (5.0 * intensity)
            else:
                # Normal operation
                error_rate = base_error_rate
                response_time_p95 = base_response_time
                availability = 99.9
            
            # Add noise
            error_rate *= random.uniform(0.9, 1.1)
            response_time_p95 *= random.uniform(0.9, 1.1)
            
            # Clamp values
            error_rate = max(0.0, min(1.0, error_rate))
            availability = max(0.0, min(100.0, availability))
            
            metric = MetricsGenerator._create_metric(
                api_id=api_id,
                gateway_id=gateway_id,
                timestamp=timestamp,
                error_rate=error_rate,
                response_time_p95=response_time_p95,
                availability=availability,
            )
            metrics.append(metric)
        
        return metrics
    
    @staticmethod
    def generate_volatile_metrics(
        api_id: UUID,
        gateway_id: UUID,
        hours: int = 24,
        base_error_rate: float = 0.05,
        base_response_time: float = 200.0,
        volatility: float = 0.5
    ) -> List[Metric]:
        """
        Generate volatile metrics with high variation.
        
        Args:
            api_id: API ID
            gateway_id: Gateway ID
            hours: Number of hours of metrics
            base_error_rate: Base error rate
            base_response_time: Base response time
            volatility: Volatility factor (0-1, higher = more volatile)
        
        Returns:
            List of volatile metrics
        """
        now = datetime.utcnow()
        metrics = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-1-i)
            
            # High random variation
            variation = 1.0 + (random.random() - 0.5) * 2 * volatility
            
            error_rate = base_error_rate * variation
            response_time_p95 = base_response_time * variation
            availability = 99.0 + random.random() * (1.0 - volatility)
            
            # Clamp values
            error_rate = max(0.0, min(1.0, error_rate))
            availability = max(0.0, min(100.0, availability))
            
            metric = MetricsGenerator._create_metric(
                api_id=api_id,
                gateway_id=gateway_id,
                timestamp=timestamp,
                error_rate=error_rate,
                response_time_p95=response_time_p95,
                availability=availability,
            )
            metrics.append(metric)
        
        return metrics
    
    @staticmethod
    def generate_recovering_metrics(
        api_id: UUID,
        gateway_id: UUID,
        hours: int = 24,
        recovery_start_hour: int = 12,
        start_error_rate: float = 0.20,
        end_error_rate: float = 0.02,
        start_response_time: float = 500.0,
        end_response_time: float = 150.0
    ) -> List[Metric]:
        """
        Generate metrics showing recovery from degraded state.
        
        Args:
            api_id: API ID
            gateway_id: Gateway ID
            hours: Number of hours of metrics
            recovery_start_hour: Hour when recovery starts
            start_error_rate: Error rate before recovery
            end_error_rate: Error rate after recovery
            start_response_time: Response time before recovery
            end_response_time: Response time after recovery
        
        Returns:
            List of recovering metrics
        """
        now = datetime.utcnow()
        metrics = []
        
        for i in range(hours):
            timestamp = now - timedelta(hours=hours-1-i)
            
            if i < recovery_start_hour:
                # Degraded state
                error_rate = start_error_rate
                response_time_p95 = start_response_time
                availability = 94.0
            else:
                # Recovery phase
                recovery_progress = (i - recovery_start_hour) / (hours - recovery_start_hour)
                
                error_rate = start_error_rate - (start_error_rate - end_error_rate) * recovery_progress
                response_time_p95 = start_response_time - (start_response_time - end_response_time) * recovery_progress
                availability = 94.0 + (99.9 - 94.0) * recovery_progress
            
            # Add noise
            error_rate *= random.uniform(0.95, 1.05)
            response_time_p95 *= random.uniform(0.95, 1.05)
            
            # Clamp values
            error_rate = max(0.0, min(1.0, error_rate))
            availability = max(0.0, min(100.0, availability))
            
            metric = MetricsGenerator._create_metric(
                api_id=api_id,
                gateway_id=gateway_id,
                timestamp=timestamp,
                error_rate=error_rate,
                response_time_p95=response_time_p95,
                availability=availability,
            )
            metrics.append(metric)
        
        return metrics
    
    @staticmethod
    def _create_metric(
        api_id: UUID,
        gateway_id: UUID,
        timestamp: datetime,
        error_rate: float,
        response_time_p95: float,
        availability: float
    ) -> Metric:
        """Create a metric with calculated derived values."""
        response_time_p50 = response_time_p95 * 0.6
        response_time_p99 = response_time_p95 * 1.2
        
        request_count = 1000
        error_count = int(error_rate * request_count)
        success_count = request_count - error_count
        
        return Metric(
            id=uuid4(),
            api_id=api_id,
            gateway_id=gateway_id,
            timestamp=timestamp,
            response_time_p50=response_time_p50,
            response_time_p95=response_time_p95,
            response_time_p99=response_time_p99,
            error_rate=error_rate,
            error_count=error_count,
            request_count=request_count,
            throughput=request_count / 60,  # requests per second
            availability=availability,
            status_codes={
                "200": success_count,
                "500": error_count
            },
            endpoint_metrics=None,
            metadata={"generated": True},
        )


# Convenience functions
def create_stable_metrics(api_id: UUID, gateway_id: UUID, hours: int = 24) -> List[Metric]:
    """Create stable metrics."""
    return MetricsGenerator.generate_stable_metrics(api_id, gateway_id, hours)


def create_degrading_metrics(api_id: UUID, gateway_id: UUID, hours: int = 24) -> List[Metric]:
    """Create degrading metrics."""
    return MetricsGenerator.generate_degrading_metrics(api_id, gateway_id, hours)


def create_spiking_metrics(api_id: UUID, gateway_id: UUID, hours: int = 24) -> List[Metric]:
    """Create spiking metrics."""
    return MetricsGenerator.generate_spiking_metrics(api_id, gateway_id, hours)


def create_volatile_metrics(api_id: UUID, gateway_id: UUID, hours: int = 24) -> List[Metric]:
    """Create volatile metrics."""
    return MetricsGenerator.generate_volatile_metrics(api_id, gateway_id, hours)


def create_recovering_metrics(api_id: UUID, gateway_id: UUID, hours: int = 24) -> List[Metric]:
    """Create recovering metrics."""
    return MetricsGenerator.generate_recovering_metrics(api_id, gateway_id, hours)


# Made with Bob