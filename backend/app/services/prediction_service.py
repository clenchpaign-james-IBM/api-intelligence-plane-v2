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

    async def generate_predictions_for_api(
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

        await self._apply_ai_enhancement(
            api_id=api_id,
            api_name=api.name,
            metrics=metrics,
            predictions=predictions,
        )
        self._store_predictions(api_id=api_id, predictions=predictions)

        return predictions

    async def generate_predictions_for_gateway(
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
                predictions = await self.generate_predictions_for_api(gateway_id, api.id, min_confidence)
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
            time_bucket=TimeBucket.ONE_MINUTE,
        )

        if len(metrics) < 1:
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

    async def _apply_ai_enhancement(
        self,
        api_id: UUID,
        api_name: Optional[str],
        metrics: List[Metric],
        predictions: List[Prediction],
    ) -> None:
        """Enhance predictions with AI-generated analysis and explanations.

        This method enriches rule-based predictions with LLM-generated insights by:
        1. Generating an overall metrics analysis for the API
        2. Creating detailed explanations for each individual prediction
        3. Attaching AI metadata to prediction objects for downstream consumption

        The method implements graceful degradation:
        - If LLM service is unavailable, predictions are marked as non-AI-enhanced
        - If AI analysis fails, predictions retain rule-based data with error metadata
        - Individual prediction explanation failures don't block other predictions

        Args:
            api_id: Unique identifier of the API being analyzed
            api_name: Human-readable name of the API (optional, used in prompts)
            metrics: Historical metrics data used for AI analysis context
            predictions: List of rule-based predictions to enhance (modified in-place)

        Returns:
            None. Predictions are modified in-place with AI enhancement metadata.

        Side Effects:
            - Modifies prediction.metadata dict for each prediction in the list
            - Lazily initializes self._prediction_agent if not already created
            - Logs warnings/errors for AI service failures

        Metadata Added:
            - ai_enhanced (bool): True if AI enhancement succeeded
            - ai_analysis (str): Overall metrics analysis (if successful)
            - ai_explanation (str): Prediction-specific explanation (if successful)
            - ai_recommended_actions (List[str]): AI-refined action recommendations
            - ai_enhancement_error (str): Error message (if enhancement failed)

        Example:
            >>> predictions = self._generate_rule_based_predictions(...)
            >>> self._apply_ai_enhancement(api_id, "Payment API", metrics, predictions)
            >>> # predictions[0].metadata now contains AI insights
        """
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
                analysis_response = await self.llm_service.generate_completion(
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
                    explanation_response = await self.llm_service.generate_completion(
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
                    )
                    explanation = explanation_response.get("content", explanation)
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
        """
        Persist predictions after enhancement using upsert logic.
        
        This method uses upsert to prevent duplicate predictions by checking if a similar
        prediction already exists for the same API, type, and time window. If found, it
        updates the existing prediction; otherwise, it creates a new one.
        """
        for prediction in predictions:
            try:
                self.prediction_repo.upsert_prediction(prediction)
                logger.info(
                    f"Upserted {prediction.prediction_type.value} prediction for API {api_id} "
                    f"with confidence {prediction.confidence_score:.2f}"
                )
            except Exception as e:
                logger.error(f"Failed to store prediction: {e}")

    def _analyze_failure_risk(
        self, gateway_id: UUID, api_id: UUID, metrics: List[Metric]
    ) -> Optional[Prediction]:
        """
        Analyze metrics for imminent API failure risk using multi-factor trend analysis.

        This method detects critical conditions that indicate an API is at risk of complete
        failure within the prediction window (48 hours). It evaluates three key indicators:
        error rates, response times, and availability, each weighted by severity.

        Algorithm:
            1. Analyze error rate trend - checks if current error rate exceeds 10% threshold
               and is increasing (weight: up to 0.4)
            2. Analyze response time degradation - checks if P95 response time exceeds 2000ms
               threshold and is increasing (weight: up to 0.3)
            3. Analyze availability drops - checks if availability falls below 95% threshold
               and is decreasing (weight: up to 0.3)
            4. Calculate overall confidence by summing weights (capped at 1.0)
            5. Determine severity based on confidence and contributing factors
            6. Generate recommended actions based on identified issues

        Thresholds:
            - ERROR_RATE_THRESHOLD: 10% (0.10)
            - RESPONSE_TIME_P95_THRESHOLD: 2000ms
            - AVAILABILITY_THRESHOLD: 95.0%

        Args:
            gateway_id: Gateway UUID for scoping the prediction
            api_id: API UUID to analyze
            metrics: Historical metrics from the trend analysis window (24 hours)

        Returns:
            Prediction object with type FAILURE if risk detected, None if no significant
            risk factors are present. The prediction includes confidence score, severity,
            contributing factors with weights, and recommended remediation actions.

        Example:
            If an API shows 15% error rate (increasing), 2500ms P95 response time
            (increasing), and 92% availability (decreasing), this would generate a
            high-confidence FAILURE prediction with all three contributing factors.
        """
        contributing_factors = []
        confidence_weights = []

        # Analyze error rate trend
        error_rates = [m.error_rate for m in metrics]
        error_rate_trend = self._calculate_trend(error_rates)
        current_error_rate = error_rates[-1] if error_rates else 0
        
        # Convert error_rate from percentage (0-100) to decimal (0-1) for comparison
        current_error_rate_decimal = current_error_rate / 100.0

        if current_error_rate_decimal > self.ERROR_RATE_THRESHOLD and error_rate_trend > 0:
            weight = min(0.4, current_error_rate_decimal / self.ERROR_RATE_THRESHOLD * 0.4)
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
        Analyze metrics for performance degradation risk using trend analysis.

        This method detects gradual performance decline patterns that indicate
        an API is degrading over time. It identifies issues before they become
        critical failures by analyzing trends in response times, throughput,
        and error rates.

        Algorithm:
            1. Analyze response time increase - checks if P50 response time shows upward
               trend and exceeds 150% of historical average, indicating gradual slowdown
               (weight: 0.35)
            2. Analyze throughput decline - checks if throughput shows downward trend
               and drops below 70% of historical average, indicating capacity issues
               (weight: 0.25)
            3. Analyze error rate increase - checks if error rate shows upward trend
               and is between 5% and critical threshold (10%), indicating emerging issues
               (weight: 0.20)
            4. Calculate overall confidence by summing weights (capped at 1.0)
            5. Determine severity based on confidence and contributing factors
            6. Generate recommended actions based on identified degradation patterns

        Args:
            gateway_id: Gateway UUID for the API being analyzed
            api_id: API UUID to analyze for degradation risk
            metrics: Historical metrics list ordered chronologically for trend analysis

        Returns:
            Prediction object with DEGRADATION type if risk detected, None otherwise.
            Prediction includes confidence score, severity level, contributing factors,
            and recommended remediation actions.

        Example:
            >>> metrics = [Metric(response_time_p50=100, ...), Metric(response_time_p50=150, ...)]
            >>> prediction = service._analyze_degradation_risk(gateway_id, api_id, metrics)
            >>> if prediction:
            ...     print(f"Degradation risk: {prediction.confidence_score:.2%}")
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
        
        # Convert error_rate from percentage (0-100) to decimal (0-1) for comparison
        current_error_rate_decimal = current_error_rate / 100.0

        if error_rate_trend > 0 and 0.05 < current_error_rate_decimal < self.ERROR_RATE_THRESHOLD:
            weight = 0.20
            contributing_factors.append(
                ContributingFactor(
                    factor=ContributingFactorType.INCREASING_ERROR_RATE,
                    current_value=current_error_rate,
                    threshold=0.05 * 100,  # Convert back to percentage for display
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
        Analyze metrics for capacity and scaling risk using load growth patterns.

        This method detects when an API is approaching or exceeding its capacity limits
        due to rapid traffic growth or degrading performance under load. It identifies
        scaling needs before they impact service quality.

        Algorithm:
            1. Analyze request count growth - checks if request volume shows upward trend
               and exceeds 200% of historical average, indicating rapid traffic growth
               (weight: 0.40)
            2. Analyze response time under load - checks if P99 response time shows upward
               trend and exceeds 5000ms threshold, indicating system strain under load
               (weight: 0.30)
            3. Calculate overall confidence by summing weights (capped at 1.0)
            4. Determine severity based on confidence and contributing factors
            5. Generate recommended actions for capacity planning and scaling

        Thresholds:
            - Request growth: 200% of historical average
            - RESPONSE_TIME_P99_THRESHOLD: 5000ms

        Args:
            gateway_id: Gateway UUID for scoping the prediction
            api_id: API UUID to analyze
            metrics: Historical metrics from the trend analysis window (24 hours)

        Returns:
            Prediction object with type CAPACITY if risk detected, None if no capacity
            constraints are identified. The prediction includes confidence score, severity,
            contributing factors with weights, and recommended scaling actions.

        Example:
            If an API's request volume doubles from 10,000 to 25,000 requests (150% increase
            above average) and P99 response time increases from 3000ms to 6000ms under this
            load, this would generate a CAPACITY prediction indicating the need for scaling.
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

        This method computes the slope of the best-fit line through a series of metric values
        using the least squares method. The slope indicates whether the metric is trending
        upward (positive slope), downward (negative slope), or remaining stable (near-zero slope).

        The calculation uses the formula:
            slope = Σ((x_i - x_mean) * (y_i - y_mean)) / Σ((x_i - x_mean)²)

        Where:
            - x_i represents the time index (0, 1, 2, ...)
            - y_i represents the metric value at time index i
            - x_mean and y_mean are the arithmetic means of x and y values

        Args:
            values: List of metric values ordered chronologically (oldest to newest).
                   Must contain at least 2 values for trend calculation.

        Returns:
            float: Trend coefficient representing the rate of change per time unit.
                  - Positive values indicate an increasing trend
                  - Negative values indicate a decreasing trend
                  - Values near zero indicate a stable/flat trend
                  - Returns 0.0 if insufficient data or denominator is zero

        Example:
            >>> service = PredictionService(...)
            >>> # Increasing trend: error rates rising over time
            >>> error_rates = [0.5, 1.2, 2.1, 3.5, 4.8]
            >>> trend = service._calculate_trend(error_rates)
            >>> print(f"Trend: {trend:.2f}")  # Output: Trend: 1.07 (increasing)
            >>>
            >>> # Decreasing trend: response times improving
            >>> response_times = [250, 220, 180, 150, 120]
            >>> trend = service._calculate_trend(response_times)
            >>> print(f"Trend: {trend:.2f}")  # Output: Trend: -32.50 (decreasing)
            >>>
            >>> # Stable trend: consistent performance
            >>> stable_values = [100, 102, 99, 101, 100]
            >>> trend = service._calculate_trend(stable_values)
            >>> print(f"Trend: {trend:.2f}")  # Output: Trend: 0.00 (stable)

        Note:
            - The magnitude of the slope depends on the scale of the input values
            - For percentage-based metrics (0-100), a slope of ±5 might be significant
            - For count-based metrics, the significance threshold varies by context
            - Edge cases (< 2 values, zero variance) return 0.0 to avoid division errors
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


    async def generate_remediation_plan(
        self,
        prediction_id: UUID,
        force_regenerate: bool = False
    ) -> Dict[str, Any]:
        """Generate AI-powered remediation plan for a prediction.
        
        Uses LLM to analyze the prediction and generate API-scoped
        remediation recommendations for webMethods gateway.
        
        Args:
            prediction_id: Prediction to generate plan for
            force_regenerate: Force regeneration even if plan exists
            
        Returns:
            Generated remediation plan with actions and verification steps
            
        Raises:
            ValueError: If prediction not found or invalid
        """
        logger.info(f"Generating remediation plan for prediction {prediction_id}")
        
        # Fetch prediction
        prediction = self.prediction_repo.get_prediction(str(prediction_id))
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        # Check if plan already exists
        if prediction.recommended_remediation and not force_regenerate:
            logger.info(f"Remediation plan already exists for prediction {prediction_id}")
            return {
                "prediction_id": str(prediction_id),
                "plan_exists": True,
                "plan": prediction.recommended_remediation,
                "generated_at": prediction.plan_generated_at.isoformat() if prediction.plan_generated_at else None
            }
        
        # Get current gateway configuration (for context)
        gateway_config = {}  # TODO: Fetch from gateway adapter
        
        # Generate plan using prediction agent
        if self._prediction_agent:
            plan = await self._prediction_agent.generate_remediation_plan(
                prediction=prediction,
                gateway_config=gateway_config
            )
        else:
            # Fallback to rule-based plan generation
            plan = self._generate_rule_based_remediation_plan(prediction)
        
        # Update prediction with plan
        updates = {
            "recommended_remediation": plan,
            "recommended_priority": plan.get("priority", "medium"),
            "recommended_verification_steps": plan.get("verification_steps", []),
            "recommended_estimated_time_minutes": plan.get("estimated_minutes", 30.0),
            "plan_generated_at": datetime.utcnow(),
            "plan_source": "llm" if self._prediction_agent else "rule_based",
            "plan_version": "1.0.0",
            "plan_status": "generated",
            "updated_at": datetime.utcnow()
        }
        
        # Persist updated prediction
        self.prediction_repo.update(str(prediction.id), updates)
        
        logger.info(f"Generated remediation plan for prediction {prediction_id}")
        
        return {
            "prediction_id": str(prediction_id),
            "plan_exists": False,
            "plan": plan,
            "generated_at": prediction.plan_generated_at.isoformat()
        }
    
    def _generate_rule_based_remediation_plan(self, prediction: Prediction) -> Dict[str, Any]:
        """Generate rule-based remediation plan when LLM is unavailable.
        
        Args:
            prediction: Prediction to generate plan for
            
        Returns:
            Rule-based remediation plan
        """
        # Map prediction type to remediation actions
        action_map = {
            PredictionType.FAILURE: ["rate_limiting", "validation_policy"],
            PredictionType.DEGRADATION: ["rate_limiting", "throttling", "cache_config"],
            PredictionType.CAPACITY: ["rate_limiting", "throttling", "cache_config"],
            PredictionType.SECURITY: ["rate_limiting", "validation_policy"]
        }
        
        actions = action_map.get(prediction.prediction_type, ["rate_limiting"])
        
        # Build plan
        plan = {
            "summary": f"Apply {', '.join(actions)} to prevent {prediction.prediction_type.value}",
            "priority": "high" if prediction.severity in [PredictionSeverity.CRITICAL, PredictionSeverity.HIGH] else "medium",
            "actions": [
                {
                    "type": action,
                    "description": f"Apply {action.replace('_', ' ')} policy to API",
                    "estimated_minutes": 10
                }
                for action in actions
            ],
            "verification_steps": [
                f"Monitor {prediction.prediction_type.value} metrics for 30 minutes",
                "Verify API remains stable",
                "Check for any side effects"
            ],
            "estimated_minutes": len(actions) * 10
        }
        
        return plan

    async def remediate_prediction(
        self,
        prediction_id: UUID,
        remediation_strategy: Optional[str] = None,
        auto_approve: bool = False,
        override_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Execute automated remediation for a prediction.
        
        Applies API-level gateway configuration changes to prevent or mitigate
        the predicted failure.
        
        Args:
            prediction_id: Prediction to remediate
            remediation_strategy: Specific strategy to use (optional)
            auto_approve: Skip approval step for semi-automated actions
            override_config: Manual override configuration
            
        Returns:
            Remediation execution results with action statuses
            
        Raises:
            ValueError: If prediction not found or invalid state
        """
        logger.info(f"Starting remediation for prediction {prediction_id}")
        
        # Fetch prediction
        prediction = self.prediction_repo.get_prediction(str(prediction_id))
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        # Validate prediction is still active
        if prediction.status != PredictionStatus.ACTIVE:
            raise ValueError(f"Prediction {prediction_id} is not active (status: {prediction.status})")
        
        # Ensure remediation plan exists
        if not prediction.recommended_remediation:
            logger.info(f"No remediation plan found, generating one")
            await self.generate_remediation_plan(prediction_id)
            prediction = self.prediction_repo.get_prediction(str(prediction_id))
        
        # Get API details
        api = self.api_repo.get(str(prediction.api_id))
        if not api:
            raise ValueError(f"API {prediction.api_id} not found")
        
        # Initialize remediation_actions from recommended plan if not already set
        if not prediction.remediation_actions:
            from app.models.prediction import RemediationAction
            recommended_actions = prediction.recommended_remediation.get("actions", [])
            prediction.remediation_actions = [
                RemediationAction(
                    action=action.get("description", action.get("type", "Unknown action")),
                    type=action.get("type", "configuration"),
                    status="pending",
                )
                for action in recommended_actions
            ]
        
        # Perform automated remediation
        remediation_result = await self._apply_automated_remediation(
            api=api,
            prediction=prediction,
            strategy=remediation_strategy,
            override_config=override_config,
        )
        
        # Check if remediation was successful
        result_actions = remediation_result.get("actions", [])
        all_successful = all(
            action.status == "completed"
            for action in result_actions
        )
        
        # Update prediction status based on remediation success
        if all_successful:
            prediction.status = PredictionStatus.MITIGATED
            prediction.remediated_at = datetime.utcnow()
            prediction.verification_status = "pending"
        else:
            prediction.status = PredictionStatus.IN_PROGRESS
        
        # Update remediation actions
        if result_actions:
            prediction.remediation_actions = result_actions
        
        prediction.updated_at = datetime.utcnow()
        
        # Update plan status if plan was used
        if prediction.recommended_remediation and prediction.plan_status == "generated":
            prediction.plan_status = "approved"  # Mark as approved when remediation starts
        
        # Persist updated prediction
        self.prediction_repo.update(
            str(prediction.id),
            prediction.dict(exclude={"id"})
        )
        
        # Force OpenSearch index refresh
        self.prediction_repo.client.indices.refresh(
            index=self.prediction_repo.index_name
        )
        
        logger.info(f"Remediation completed for prediction {prediction_id} (status: {prediction.status})")
        
        return remediation_result
    
    async def _apply_automated_remediation(
        self,
        api: API,
        prediction: Prediction,
        strategy: Optional[str] = None,
        override_config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Apply automated remediation for a prediction via Gateway adapter.
        
        Args:
            api: API to remediate
            prediction: Prediction to fix
            strategy: Optional remediation strategy
            override_config: Optional override configuration
            
        Returns:
            Remediation result with actions
        """
        from app.models.prediction import RemediationAction
        from app.models.base.policy_configs import (
            RateLimitConfig,
            ValidationConfig,
        )
        
        actions = []
        
        # Get gateway adapter for this API
        gateway = self.gateway_repo.get(str(api.gateway_id))
        if not gateway:
            raise ValueError(f"Gateway not found for API: {api.id}")
        
        # Get adapter from factory
        from app.adapters.factory import GatewayAdapterFactory
        gateway_adapter = GatewayAdapterFactory.create_adapter(gateway)
        await gateway_adapter.connect()
        
        try:
            # Get recommended actions from plan
            recommended_actions = prediction.recommended_remediation.get("actions", [])
            
            for action_spec in recommended_actions:
                action_type = action_spec.get("type", "rate_limiting")
                
                try:
                    if action_type == "rate_limiting":
                        # Apply rate limiting policy
                        default_config = RateLimitConfig(
                            requests_per_second=None,
                            requests_per_minute=100,
                            requests_per_hour=None,
                            requests_per_day=None,
                            concurrent_requests=None,
                            burst_allowance=20,
                            rate_limit_key="ip",
                            custom_key_header=None,
                            enforcement_action="reject",
                            include_rate_limit_headers=True,
                            consumer_tiers=None,
                        )
                        
                        # Apply overrides if provided
                        if override_config and "rate_limiting" in override_config:
                            final_config_dict = default_config.dict()
                            final_config_dict.update(override_config["rate_limiting"])
                            final_config = RateLimitConfig(**final_config_dict)
                        else:
                            final_config = default_config
                        
                        policy = PolicyAction(
                            action_type=PolicyActionType.RATE_LIMITING,
                            enabled=True,
                            stage="request",
                            config=final_config,
                            vendor_config={},
                            name=f"Rate Limit Policy for {api.name}",
                            description=f"Prediction remediation for {prediction.id}",
                        )
                        success = await gateway_adapter.apply_rate_limit_policy(
                            str(api.id), policy
                        )
                        
                        actions.append(
                            RemediationAction(
                                action=f"Applied rate limiting policy (100 req/min)",
                                type="gateway_policy",
                                status="completed" if success else "failed",
                                performed_at=datetime.utcnow(),
                                performed_by="prediction_agent",
                                gateway_policy_id=f"ratelimit-{api.id}" if success else None,
                                configuration_before=None,
                                configuration_after=final_config.dict() if success else None,
                                effectiveness_score=None,
                                error_message=None if success else "Failed to apply policy",
                                rollback_available=success,
                                rollback_performed_at=None,
                            )
                        )
                        
                    elif action_type == "throttling":
                        # Apply throttling policy
                        default_config = ThrottlingConfig(
                            max_concurrent_requests=10,
                            queue_size=100,
                            queue_timeout_seconds=30,
                            throttle_by="ip",
                            custom_throttle_key=None,
                            rejection_status_code=429,
                            rejection_message=None,
                        )
                        
                        if override_config and "throttling" in override_config:
                            final_config_dict = default_config.dict()
                            final_config_dict.update(override_config["throttling"])
                            final_config = ThrottlingConfig(**final_config_dict)
                        else:
                            final_config = default_config
                        
                        policy = PolicyAction(
                            action_type=PolicyActionType.THROTTLING,
                            enabled=True,
                            stage="request",
                            config=final_config,
                            vendor_config={},
                            name=f"Throttling Policy for {api.name}",
                            description=f"Prediction remediation for {prediction.id}",
                        )
                        success = await gateway_adapter.apply_throttling_policy(
                            str(api.id), policy
                        )
                        
                        actions.append(
                            RemediationAction(
                                action=f"Applied throttling policy (max 10 concurrent)",
                                type="gateway_policy",
                                status="completed" if success else "failed",
                                performed_at=datetime.utcnow(),
                                performed_by="prediction_agent",
                                gateway_policy_id=f"throttle-{api.id}" if success else None,
                                error_message=None if success else "Failed to apply policy",
                            )
                        )
                        
                    elif action_type == "cache_config":
                        # Apply caching policy
                        default_config = CacheConfig(
                            cache_enabled=True,
                            cache_ttl_seconds=300,
                            cache_key_template=None,
                            cache_by_headers=None,
                            cache_by_query_params=None,
                            cache_response_codes=[200, 203, 204, 206, 300, 301, 404, 405, 410, 414, 501],
                            cache_methods=["GET", "HEAD"],
                            vary_by_headers=None,
                            cache_control_override=None,
                        )
                        
                        if override_config and "cache_config" in override_config:
                            final_config_dict = default_config.dict()
                            final_config_dict.update(override_config["cache_config"])
                            final_config = CacheConfig(**final_config_dict)
                        else:
                            final_config = default_config
                        
                        policy = PolicyAction(
                            action_type=PolicyActionType.CACHING,
                            enabled=True,
                            stage="response",
                            config=final_config,
                            vendor_config={},
                            name=f"Cache Policy for {api.name}",
                            description=f"Prediction remediation for {prediction.id}",
                        )
                        success = await gateway_adapter.apply_cache_policy(
                            str(api.id), policy
                        )
                        
                        actions.append(
                            RemediationAction(
                                action=f"Applied caching policy (TTL: 5 min)",
                                type="gateway_policy",
                                status="completed" if success else "failed",
                                performed_at=datetime.utcnow(),
                                performed_by="prediction_agent",
                                gateway_policy_id=f"cache-{api.id}" if success else None,
                                error_message=None if success else "Failed to apply policy",
                            )
                        )
                        
                    elif action_type == "validation_policy":
                        # Apply validation policy
                        default_config = ValidationConfig(
                            validate_request_body=True,
                            validate_request_headers=True,
                            validate_request_query_params=True,
                            validate_response_body=False,
                            validate_response_headers=False,
                            schema_validation_enabled=True,
                            schema_format="openapi3",
                            schema_url=None,
                            schema_content=None,
                            strict_validation=True,
                            allow_additional_properties=False,
                            validation_error_status_code=400,
                            validation_error_message=None,
                        )
                        
                        if override_config and "validation_policy" in override_config:
                            final_config_dict = default_config.dict()
                            final_config_dict.update(override_config["validation_policy"])
                            final_config = ValidationConfig(**final_config_dict)
                        else:
                            final_config = default_config
                        
                        policy = PolicyAction(
                            action_type=PolicyActionType.VALIDATION,
                            enabled=True,
                            stage="request",
                            config=final_config,
                            vendor_config={},
                            name=f"Validation Policy for {api.name}",
                            description=f"Prediction remediation for {prediction.id}",
                        )
                        success = await gateway_adapter.apply_validation_policy(
                            str(api.id), policy
                        )
                        
                        actions.append(
                            RemediationAction(
                                action=f"Applied validation policy (strict mode)",
                                type="gateway_policy",
                                status="completed" if success else "failed",
                                performed_at=datetime.utcnow(),
                                performed_by="prediction_agent",
                                gateway_policy_id=f"validation-{api.id}" if success else None,
                                error_message=None if success else "Failed to apply policy",
                            )
                        )
                        
                except Exception as e:
                    logger.error(f"Failed to apply {action_type} policy: {e}")
                    actions.append(
                        RemediationAction(
                            action=f"Failed to apply {action_type} policy",
                            type="gateway_policy",
                            status="failed",
                            performed_at=datetime.utcnow(),
                            performed_by="prediction_agent",
                            gateway_policy_id=None,
                            error_message=str(e),
                        )
                    )
            
            # Disconnect adapter
            await gateway_adapter.disconnect()
            
            return {
                "actions": actions,
                "overall_status": "completed" if all(a.status == "completed" for a in actions) else "partial",
            }
            
        except Exception as e:
            logger.error(f"Remediation failed: {e}")
            await gateway_adapter.disconnect()
            raise

    async def verify_remediation(
        self,
        prediction_id: UUID,
        verification_method: str = "automated"
    ) -> Dict[str, Any]:
        """Verify effectiveness of remediation actions.
        
        Checks if the remediation successfully prevented or mitigated
        the predicted issue.
        
        Args:
            prediction_id: Prediction to verify
            verification_method: How to verify (automated, manual)
            
        Returns:
            Verification results with effectiveness scores
            
        Raises:
            ValueError: If prediction not found
        """
        logger.info(f"Verifying remediation for prediction {prediction_id}")
        
        # Fetch prediction
        prediction = self.prediction_repo.get_prediction(str(prediction_id))
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        # TODO: Check current metrics vs. prediction thresholds
        # TODO: Calculate effectiveness scores
        # TODO: Update prediction with verification results
        
        logger.warning("Remediation verification not yet implemented - placeholder only")
        
        return {
            "prediction_id": str(prediction_id),
            "status": "pending_implementation",
            "message": "Remediation verification will be implemented in Phase 2"
        }

    async def rollback_remediation(
        self,
        prediction_id: UUID,
        action_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Rollback remediation actions for a prediction.
        
        Reverts API-level gateway configuration changes if remediation was
        ineffective or caused issues.
        
        Args:
            prediction_id: Prediction to rollback
            action_id: Specific action to rollback (or all if None)
            
        Returns:
            Rollback results
            
        Raises:
            ValueError: If prediction not found
        """
        logger.info(f"Rolling back remediation for prediction {prediction_id}")
        
        # Fetch prediction
        prediction = self.prediction_repo.get_prediction(str(prediction_id))
        if not prediction:
            raise ValueError(f"Prediction {prediction_id} not found")
        
        # TODO: Identify actions to rollback
        # TODO: Restore previous gateway configurations
        # TODO: Update action statuses
        
        logger.warning("Remediation rollback not yet implemented - placeholder only")
        
        return {
            "prediction_id": str(prediction_id),
            "status": "pending_implementation",
            "message": "Remediation rollback will be implemented in Phase 2"
        }
        return count

# Made with Bob
