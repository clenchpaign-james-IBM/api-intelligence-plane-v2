"""
Prediction Service

Handles ML-based prediction generation for API failures, including
trend analysis, anomaly detection, and contributing factor identification.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import statistics

from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.api_repository import APIRepository
from app.models.prediction import (
    Prediction,
    PredictionType,
    PredictionSeverity,
    PredictionStatus,
    ContributingFactor,
    ContributingFactorType,
)
from app.models.base.metric import Metric, TimeBucket
from app.config import settings

logger = logging.getLogger(__name__)


class PredictionService:
    """Service for generating and managing API failure predictions."""

    # Thresholds for prediction triggers
    ERROR_RATE_THRESHOLD = 0.10  # 10% error rate
    RESPONSE_TIME_P95_THRESHOLD = 2000  # 2000ms
    RESPONSE_TIME_P99_THRESHOLD = 5000  # 5000ms
    AVAILABILITY_THRESHOLD = 95.0  # 95% availability
    
    # Trend analysis window
    TREND_WINDOW_HOURS = 24
    PREDICTION_WINDOW_HOURS = 48
    
    # Model version
    MODEL_VERSION = "1.0.0"

    def __init__(
        self,
        prediction_repository: PredictionRepository,
        metrics_repository: MetricsRepository,
        api_repository: APIRepository,
        llm_service: Any = None,
    ):
        """
        Initialize the Prediction Service.

        Args:
            prediction_repository: Repository for prediction operations
            metrics_repository: Repository for metrics operations
            api_repository: Repository for API operations
            llm_service: Optional LLM service for AI enhancement
        """
        self.prediction_repo = prediction_repository
        self.metrics_repo = metrics_repository
        self.api_repo = api_repository
        self.llm_service = llm_service
        self._prediction_agent = None

    def generate_predictions_for_api(
        self, gateway_id: UUID, api_id: UUID, min_confidence: float = 0.7
    ) -> List[Prediction]:
        """
        Generate and persist predictions for a specific API within a gateway context.

        The prediction flow is single-path:
        1. Generate rule-based predictions
        2. Apply AI enhancement metadata when available
        3. Persist predictions with graceful fallback to rule-based metadata

        Args:
            gateway_id: Gateway UUID (primary scope dimension)
            api_id: API UUID (secondary scope dimension)
            min_confidence: Minimum confidence threshold (0-1)

        Returns:
            List of generated predictions
        """
        logger.info(f"Generating predictions for API {api_id} in gateway {gateway_id}")

        api, metrics = self._get_api_and_metrics(gateway_id, api_id)
        if not api or metrics is None:
            return []

        predictions = self._build_rule_based_predictions(
            gateway_id=gateway_id,
            api_id=api_id,
            metrics=metrics,
            min_confidence=min_confidence,
        )
        if not predictions:
            return []

        self._apply_ai_enhancement(
            api_id=api_id,
            api_name=api.name,
            metrics=metrics,
            predictions=predictions,
        )
        self._store_predictions(api_id=api_id, predictions=predictions)

        return predictions

    def generate_predictions_for_gateway(
        self, gateway_id: UUID, min_confidence: float = 0.7
    ) -> Dict[str, Any]:
        """
        Generate predictions for all APIs within a specific gateway.

        Args:
            gateway_id: Gateway UUID (primary scope dimension)
            min_confidence: Minimum confidence threshold (0-1)

        Returns:
            Dict with generation results
        """
        logger.info(f"Generating predictions for all APIs in gateway {gateway_id}")

        apis, _ = self.api_repo.find_by_gateway(gateway_id, size=1000)

        results = {
            "gateway_id": str(gateway_id),
            "total_apis": len(apis),
            "apis_analyzed": 0,
            "predictions_generated": 0,
            "errors": [],
        }

        for api in apis:
            try:
                predictions = self.generate_predictions_for_api(gateway_id, api.id, min_confidence)
                results["apis_analyzed"] += 1
                results["predictions_generated"] += len(predictions)
            except Exception as e:
                logger.error(f"Failed to generate predictions for API {api.id}: {e}")
                results["errors"].append({
                    "api_id": str(api.id),
                    "api_name": api.name,
                    "error": str(e),
                })

        logger.info(
            f"Prediction generation complete: {results['predictions_generated']} predictions "
            f"for {results['apis_analyzed']}/{results['total_apis']} APIs"
        )

        return results

    def _get_api_and_metrics(
        self,
        gateway_id: UUID,
        api_id: UUID,
    ) -> tuple[Optional[Any], Optional[List[Metric]]]:
        """Fetch API details and historical metrics for prediction analysis."""
        api = self.api_repo.get(str(api_id))
        if not api:
            logger.warning(f"API {api_id} not found")
            return None, None
        
        # Verify API belongs to gateway
        if api.gateway_id != gateway_id:
            logger.warning(f"API {api_id} does not belong to gateway {gateway_id}")
            return None, None

        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=self.TREND_WINDOW_HOURS)

        metrics, _ = self.metrics_repo.find_by_api_with_bucket(
            api_id=api_id,
            start_time=start_time,
            end_time=end_time,
            time_bucket=TimeBucket.ONE_HOUR,
        )

        if len(metrics) < 10:
            logger.info(f"Insufficient metrics data for API {api_id} (only {len(metrics)} points)")
            return api, None

        return api, metrics

    def _build_rule_based_predictions(
        self,
        gateway_id: UUID,
        api_id: UUID,
        metrics: List[Metric],
        min_confidence: float,
    ) -> List[Prediction]:
        """Build rule-based predictions before AI enhancement."""
        predictions: List[Prediction] = []

        failure_prediction = self._analyze_failure_risk(gateway_id, api_id, metrics)
        if failure_prediction and failure_prediction.confidence_score >= min_confidence:
            predictions.append(failure_prediction)

        degradation_prediction = self._analyze_degradation_risk(gateway_id, api_id, metrics)
        if degradation_prediction and degradation_prediction.confidence_score >= min_confidence:
            predictions.append(degradation_prediction)

        capacity_prediction = self._analyze_capacity_risk(gateway_id, api_id, metrics)
        if capacity_prediction and capacity_prediction.confidence_score >= min_confidence:
            predictions.append(capacity_prediction)

        return predictions

    def _apply_ai_enhancement(
        self,
        api_id: UUID,
        api_name: Optional[str],
        metrics: List[Metric],
        predictions: List[Prediction],
    ) -> None:
        """Attach AI enhancement metadata to every prediction with graceful fallback."""
        if not predictions:
            return

        for prediction in predictions:
            prediction.metadata = dict(prediction.metadata or {})

        if not self.llm_service:
            logger.info(f"LLM service unavailable for API {api_id}; storing rule-based predictions only")
            for prediction in predictions:
                metadata = dict(prediction.metadata or {})
                metadata["ai_enhanced"] = False
                metadata["ai_enhancement_error"] = "LLM service unavailable"
                prediction.metadata = metadata
            return

        try:
            if self._prediction_agent is None:
                from app.agents.prediction_agent import PredictionAgent

                self._prediction_agent = PredictionAgent(
                    llm_service=self.llm_service,
                    prediction_service=self,
                )

            analysis = "AI analysis unavailable"
            try:
                metrics_summary = self._prediction_agent._prepare_metrics_summary(metrics)
                analysis_response = self.llm_service.generate_sync(
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                "You are an expert API reliability engineer. Analyze API metrics "
                                "and summarize the most important operational risks, likely failure "
                                "patterns, and practical preventive actions."
                            ),
                        },
                        {
                            "role": "user",
                            "content": (
                                f"Analyze metrics for API '{api_name or f'API {str(api_id)[:8]}'}':\n\n"
                                f"{metrics_summary}"
                            ),
                        },
                    ],
                    temperature=0.3,
                    max_tokens=400,
                )
                analysis = analysis_response.get("content", analysis)
            except Exception as analysis_error:
                logger.warning(f"AI metrics analysis failed for API {api_id}: {analysis_error}")

            enhanced_predictions = []
            for prediction in predictions:
                explanation = "AI explanation unavailable"
                try:
                    explanation = self.llm_service.generate_sync(
                        messages=[
                            {
                                "role": "system",
                                "content": (
                                    "You are an expert API reliability engineer. Explain the prediction "
                                    "clearly, concisely, and provide practical next steps."
                                ),
                            },
                            {
                                "role": "user",
                                "content": (
                                    f"API: {api_name or f'API {str(api_id)[:8]}'}\n"
                                    f"Prediction Type: {prediction.prediction_type.value}\n"
                                    f"Severity: {prediction.severity.value}\n"
                                    f"Confidence: {prediction.confidence_score:.2%}\n"
                                    f"Predicted Time: {prediction.predicted_time.isoformat()}\n"
                                    f"Contributing Factors: "
                                    f"{', '.join(str(f.factor.value) for f in prediction.contributing_factors)}\n"
                                    f"Recommended Actions: {'; '.join(prediction.recommended_actions)}\n"
                                    f"Metrics Analysis: {analysis}"
                                ),
                            },
                        ],
                        temperature=0.4,
                        max_tokens=300,
                    ).get("content", explanation)
                except Exception as explanation_error:
                    logger.warning(
                        f"AI explanation failed for prediction {prediction.id}: {explanation_error}"
                    )

                enhanced_predictions.append(
                    {
                        "prediction_type": prediction.prediction_type.value,
                        "analysis": analysis,
                        "explanation": explanation,
                        "recommended_actions": prediction.recommended_actions,
                    }
                )
            predictions_by_type = {
                prediction.prediction_type.value: prediction for prediction in predictions
            }

            for enhanced_prediction in enhanced_predictions:
                prediction_type = enhanced_prediction.get("prediction_type")
                prediction = predictions_by_type.get(prediction_type)
                if not prediction:
                    continue

                metadata = dict(prediction.metadata or {})
                metadata["ai_enhanced"] = True
                metadata["ai_analysis"] = enhanced_prediction.get("analysis")
                metadata["ai_explanation"] = enhanced_prediction.get("explanation")
                metadata["ai_recommended_actions"] = enhanced_prediction.get(
                    "recommended_actions"
                )
                prediction.metadata = metadata

        except Exception as e:
            logger.error(f"AI enhancement failed for API {api_id}: {e}")
            for prediction in predictions:
                metadata = dict(prediction.metadata or {})
                metadata["ai_enhanced"] = False
                metadata["ai_enhancement_error"] = str(e)
                prediction.metadata = metadata

    def _store_predictions(self, api_id: UUID, predictions: List[Prediction]) -> None:
        """Persist predictions after enhancement."""
        for prediction in predictions:
            try:
                self.prediction_repo.create_prediction(prediction)
                logger.info(
                    f"Created {prediction.prediction_type.value} prediction for API {api_id} "
                    f"with confidence {prediction.confidence_score:.2f}"
                )
            except Exception as e:
                logger.error(f"Failed to store prediction: {e}")

    def _analyze_failure_risk(
        self, gateway_id: UUID, api_id: UUID, metrics: List[Metric]
    ) -> Optional[Prediction]:
        """
        Analyze metrics for failure risk.

        Args:
            api_id: API UUID
            metrics: Historical metrics

        Returns:
            Prediction if failure risk detected, None otherwise
        """
        contributing_factors = []
        confidence_weights = []

        # Analyze error rate trend
        error_rates = [m.error_rate for m in metrics]
        error_rate_trend = self._calculate_trend(error_rates)
        current_error_rate = error_rates[-1] if error_rates else 0

        if current_error_rate > self.ERROR_RATE_THRESHOLD and error_rate_trend > 0:
            weight = min(0.4, current_error_rate / self.ERROR_RATE_THRESHOLD * 0.4)
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.INCREASING_ERROR_RATE,
                    current_value=current_error_rate,
                    threshold=self.ERROR_RATE_THRESHOLD,
                    trend="increasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        # Analyze response time degradation
        response_times_p95 = [m.response_time_p95 for m in metrics]
        response_time_trend = self._calculate_trend(response_times_p95)
        current_response_time = response_times_p95[-1] if response_times_p95 else 0

        if current_response_time > self.RESPONSE_TIME_P95_THRESHOLD and response_time_trend > 0:
            weight = min(0.3, current_response_time / self.RESPONSE_TIME_P95_THRESHOLD * 0.3)
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.DEGRADING_RESPONSE_TIME,
                    current_value=current_response_time,
                    threshold=self.RESPONSE_TIME_P95_THRESHOLD,
                    trend="increasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        # Analyze availability drops
        availabilities = [m.availability for m in metrics]
        availability_trend = self._calculate_trend(availabilities)
        current_availability = availabilities[-1] if availabilities else 100

        if current_availability < self.AVAILABILITY_THRESHOLD and availability_trend < 0:
            weight = min(0.3, (100 - current_availability) / (100 - self.AVAILABILITY_THRESHOLD) * 0.3)
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.DECLINING_AVAILABILITY,
                    current_value=current_availability,
                    threshold=self.AVAILABILITY_THRESHOLD,
                    trend="decreasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        # If no significant factors, no prediction
        if not contributing_factors:
            return None

        # Calculate overall confidence
        confidence = sum(confidence_weights)
        confidence = min(1.0, confidence)  # Cap at 1.0

        # Determine severity based on confidence and factors
        severity = self._determine_severity(confidence, contributing_factors)

        # Generate recommended actions
        recommended_actions = self._generate_recommended_actions(contributing_factors)

        # Create prediction
        predicted_at = datetime.utcnow()
        predicted_time = predicted_at + timedelta(hours=self.PREDICTION_WINDOW_HOURS)

        # Get API name for enrichment
        api = self.api_repo.get(str(api_id))
        api_name = api.name if api else None
        
        return Prediction(
            gateway_id=gateway_id,
            api_id=api_id,
            api_name=api_name,
            prediction_type=PredictionType.FAILURE,
            predicted_at=predicted_at,
            predicted_time=predicted_time,
            confidence_score=confidence,
            severity=severity,
            status=PredictionStatus.ACTIVE,
            contributing_factors=contributing_factors,
            recommended_actions=recommended_actions,
            actual_outcome=None,
            actual_time=None,
            accuracy_score=None,
            model_version=self.MODEL_VERSION,
            metadata=None,
        )

    def _analyze_degradation_risk(
        self, gateway_id: UUID, api_id: UUID, metrics: List[Metric]
    ) -> Optional[Prediction]:
        """
        Analyze metrics for performance degradation risk.

        Args:
            api_id: API UUID
            metrics: Historical metrics

        Returns:
            Prediction if degradation risk detected, None otherwise
        """
        contributing_factors = []
        confidence_weights = []

        # Analyze gradual response time increase
        response_times_p50 = [m.response_time_p50 for m in metrics]
        response_time_trend = self._calculate_trend(response_times_p50)
        current_response_time = response_times_p50[-1] if response_times_p50 else 0
        avg_response_time = statistics.mean(response_times_p50) if response_times_p50 else 0

        if response_time_trend > 0 and current_response_time > avg_response_time * 1.5:
            weight = 0.35
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.GRADUAL_RESPONSE_TIME_INCREASE,
                    current_value=current_response_time,
                    threshold=avg_response_time,
                    trend="increasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        # Analyze throughput decline
        throughputs = [m.throughput for m in metrics]
        throughput_trend = self._calculate_trend(throughputs)
        current_throughput = throughputs[-1] if throughputs else 0
        avg_throughput = statistics.mean(throughputs) if throughputs else 0

        if throughput_trend < 0 and current_throughput < avg_throughput * 0.7:
            weight = 0.25
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.DECLINING_THROUGHPUT,
                    current_value=current_throughput,
                    threshold=avg_throughput,
                    trend="decreasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        # Analyze error rate increase (but not critical)
        error_rates = [m.error_rate for m in metrics]
        error_rate_trend = self._calculate_trend(error_rates)
        current_error_rate = error_rates[-1] if error_rates else 0

        if error_rate_trend > 0 and 0.05 < current_error_rate < self.ERROR_RATE_THRESHOLD:
            weight = 0.20
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.INCREASING_ERROR_RATE,
                    current_value=current_error_rate,
                    threshold=0.05,
                    trend="increasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        if not contributing_factors:
            return None

        confidence = sum(confidence_weights)
        confidence = min(1.0, confidence)

        severity = self._determine_severity(confidence, contributing_factors)
        recommended_actions = self._generate_recommended_actions(contributing_factors)

        # Get API name for enrichment
        api = self.api_repo.get(str(api_id))
        api_name = api.name if api else None
        
        predicted_at = datetime.utcnow()
        predicted_time = predicted_at + timedelta(hours=self.PREDICTION_WINDOW_HOURS)

        return Prediction(
            gateway_id=gateway_id,
            api_id=api_id,
            api_name=api_name,
            prediction_type=PredictionType.DEGRADATION,
            predicted_at=predicted_at,
            predicted_time=predicted_time,
            confidence_score=confidence,
            severity=severity,
            status=PredictionStatus.ACTIVE,
            contributing_factors=contributing_factors,
            recommended_actions=recommended_actions,
            actual_outcome=None,
            actual_time=None,
            accuracy_score=None,
            model_version=self.MODEL_VERSION,
            metadata=None,
        )

    def _analyze_capacity_risk(
        self, gateway_id: UUID, api_id: UUID, metrics: List[Metric]
    ) -> Optional[Prediction]:
        """
        Analyze metrics for capacity/scaling risk.

        Args:
            api_id: API UUID
            metrics: Historical metrics

        Returns:
            Prediction if capacity risk detected, None otherwise
        """
        contributing_factors = []
        confidence_weights = []

        # Analyze request count growth
        request_counts = [float(m.request_count) for m in metrics]
        request_trend = self._calculate_trend(request_counts)
        current_requests = request_counts[-1] if request_counts else 0
        avg_requests = statistics.mean(request_counts) if request_counts else 0

        if request_trend > 0 and current_requests > avg_requests * 2:
            weight = 0.40
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.RAPID_REQUEST_GROWTH,
                    current_value=current_requests,
                    threshold=avg_requests,
                    trend="increasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        # Analyze response time under load
        response_times_p99 = [m.response_time_p99 for m in metrics]
        response_time_trend = self._calculate_trend(response_times_p99)
        current_p99 = response_times_p99[-1] if response_times_p99 else 0

        if response_time_trend > 0 and current_p99 > self.RESPONSE_TIME_P99_THRESHOLD:
            weight = 0.30
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.HIGH_LATENCY_UNDER_LOAD,
                    current_value=current_p99,
                    threshold=self.RESPONSE_TIME_P99_THRESHOLD,
                    trend="increasing",
                    weight=weight,
                )
            )
            confidence_weights.append(weight)

        if not contributing_factors:
            return None

        confidence = sum(confidence_weights)
        confidence = min(1.0, confidence)

        severity = self._determine_severity(confidence, contributing_factors)
        recommended_actions = self._generate_recommended_actions(contributing_factors)

        # Get API name for enrichment
        api = self.api_repo.get(str(api_id))
        api_name = api.name if api else None
        
        predicted_at = datetime.utcnow()
        predicted_time = predicted_at + timedelta(hours=self.PREDICTION_WINDOW_HOURS)

        return Prediction(
            gateway_id=gateway_id,
            api_id=api_id,
            api_name=api_name,
            prediction_type=PredictionType.CAPACITY,
            predicted_at=predicted_at,
            predicted_time=predicted_time,
            confidence_score=confidence,
            severity=severity,
            status=PredictionStatus.ACTIVE,
            contributing_factors=contributing_factors,
            recommended_actions=recommended_actions,
            actual_outcome=None,
            actual_time=None,
            accuracy_score=None,
            model_version=self.MODEL_VERSION,
            metadata=None,
        )

    def _calculate_trend(self, values: List[float]) -> float:
        """
        Calculate trend direction using simple linear regression.

        Args:
            values: List of metric values

        Returns:
            Trend coefficient (positive = increasing, negative = decreasing)
        """
        if len(values) < 2:
            return 0.0

        n = len(values)
        x = list(range(n))
        
        # Calculate means
        x_mean = sum(x) / n
        y_mean = sum(values) / n
        
        # Calculate slope
        numerator = sum((x[i] - x_mean) * (values[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return 0.0
        
        slope = numerator / denominator
        return slope

    def _determine_severity(
        self, confidence: float, factors: List[ContributingFactor]
    ) -> PredictionSeverity:
        """
        Determine prediction severity based on confidence and factors.

        Args:
            confidence: Confidence score
            factors: Contributing factors

        Returns:
            Severity level
        """
        # Calculate weighted severity
        max_weight = max(f.weight for f in factors) if factors else 0

        if confidence >= 0.9 or max_weight >= 0.4:
            return PredictionSeverity.CRITICAL
        elif confidence >= 0.8 or max_weight >= 0.3:
            return PredictionSeverity.HIGH
        elif confidence >= 0.7 or max_weight >= 0.2:
            return PredictionSeverity.MEDIUM
        else:
            return PredictionSeverity.LOW

    def _generate_recommended_actions(
        self, factors: List[ContributingFactor]
    ) -> List[str]:
        """
        Generate recommended actions based on contributing factors.

        Args:
            factors: Contributing factors

        Returns:
            List of recommended actions
        """
        actions = []
        factor_types = [f.factor for f in factors]

        if ContributingFactorType.INCREASING_ERROR_RATE in factor_types:
            actions.append("Review recent code changes and deployments")
            actions.append("Check application logs for error patterns")
            actions.append("Verify external service dependencies")

        if (ContributingFactorType.DEGRADING_RESPONSE_TIME in factor_types or
            ContributingFactorType.GRADUAL_RESPONSE_TIME_INCREASE in factor_types):
            actions.append("Analyze slow query logs and database performance")
            actions.append("Review caching strategy and hit rates")
            actions.append("Check for resource contention (CPU, memory, I/O)")

        if ContributingFactorType.DECLINING_AVAILABILITY in factor_types:
            actions.append("Verify health check endpoints")
            actions.append("Check load balancer configuration")
            actions.append("Review instance health and auto-scaling policies")

        if ContributingFactorType.DECLINING_THROUGHPUT in factor_types:
            actions.append("Check for rate limiting or throttling")
            actions.append("Review connection pool settings")
            actions.append("Analyze network latency and bandwidth")

        if (ContributingFactorType.RAPID_REQUEST_GROWTH in factor_types or
            ContributingFactorType.HIGH_LATENCY_UNDER_LOAD in factor_types):
            actions.append("Scale up API instances horizontally")
            actions.append("Implement or adjust rate limiting")
            actions.append("Consider caching frequently accessed data")
            actions.append("Review and optimize resource allocation")

        # Add generic actions if no specific ones
        if not actions:
            actions.append("Monitor API metrics closely")
            actions.append("Review system logs for anomalies")
            actions.append("Verify infrastructure health")

        return actions

    def update_prediction_outcome(
        self,
        prediction_id: str,
        actual_outcome: str,
        actual_time: Optional[datetime] = None,
    ) -> Optional[Prediction]:
        """
        Update prediction with actual outcome and calculate accuracy.

        Args:
            prediction_id: Prediction UUID
            actual_outcome: What actually happened
            actual_time: When the event occurred

        Returns:
            Updated prediction
        """
        # Update status and outcome
        if actual_outcome == "occurred":
            status = PredictionStatus.RESOLVED
        elif actual_outcome == "prevented":
            status = PredictionStatus.RESOLVED
        else:
            status = PredictionStatus.FALSE_POSITIVE

        prediction = self.prediction_repo.update_prediction_status(
            prediction_id=prediction_id,
            status=status,
            actual_outcome=actual_outcome,
            actual_time=actual_time or datetime.utcnow(),
        )

        # Calculate accuracy if event occurred
        if prediction and actual_time:
            prediction = self.prediction_repo.calculate_and_update_accuracy(prediction_id)

        return prediction

    def expire_old_predictions(self) -> int:
        """
        Mark expired predictions as expired.

        Returns:
            Number of predictions expired
        """
        expired_predictions = self.prediction_repo.get_expired_predictions()
        
        count = 0
        for prediction in expired_predictions:
            self.prediction_repo.update_prediction_status(
                prediction_id=str(prediction.id),
                status=PredictionStatus.EXPIRED,
            )
            count += 1

        if count > 0:
            logger.info(f"Expired {count} old predictions")

        return count

# Made with Bob
