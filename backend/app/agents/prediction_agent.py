"""
Prediction Agent

AI agent for enhanced prediction generation using LangChain/LangGraph.
Provides LLM-powered analysis of metrics trends and prediction explanations.
"""

import logging
from typing import List, Dict, Any, Optional, TypedDict
from datetime import datetime
from uuid import UUID

# Try to import LangGraph components
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

from app.services.llm_service import LLMService
from app.services.prediction_service import PredictionService
from app.models.prediction import Prediction, ContributingFactor
from app.models.base.metric import Metric

logger = logging.getLogger(__name__)


class PredictionState(TypedDict):
    """State for prediction generation workflow."""
    
    gateway_id: str
    api_id: str
    api_name: str
    metrics: List[Any]
    analysis: str
    predictions: List[Any]
    enhanced_predictions: List[Dict[str, Any]]
    error: str


class PredictionAgent:
    """
    AI agent for enhanced prediction generation.
    
    Uses LangChain for LLM integration and LangGraph for workflow orchestration.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        prediction_service: PredictionService,
    ):
        """
        Initialize the Prediction Agent.
        
        Args:
            llm_service: LLM service for AI-powered analysis
            prediction_service: Prediction service for ML-based predictions
        """
        self.llm_service = llm_service
        self.prediction_service = prediction_service
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> Any:
        """
        Build the prediction generation workflow using LangGraph.
        
        Returns:
            Compiled StateGraph workflow or None if LangGraph unavailable
        """
        if not LANGGRAPH_AVAILABLE or StateGraph is None:
            logger.warning("LangGraph not available. AI-enhanced predictions will use direct execution.")
            return None
        
        try:
            # Create workflow with TypedDict state schema
            workflow = StateGraph(PredictionState)
            
            # Define workflow nodes
            workflow.add_node("analyze_metrics", self._analyze_metrics_node)
            workflow.add_node("generate_predictions", self._generate_predictions_node)
            workflow.add_node("enhance_predictions", self._enhance_predictions_node)
            
            # Define workflow edges
            workflow.set_entry_point("analyze_metrics")
            workflow.add_edge("analyze_metrics", "generate_predictions")
            workflow.add_edge("generate_predictions", "enhance_predictions")
            workflow.add_edge("enhance_predictions", END if END else "__end__")
            
            return workflow.compile()
        except Exception as e:
            logger.error(f"Failed to build LangGraph workflow: {e}")
            return None
    
    async def generate_enhanced_predictions(
        self,
        gateway_id: UUID,
        api_id: UUID,
        api_name: str,
        metrics: List[Metric],
    ) -> Dict[str, Any]:
        """
        Generate enhanced predictions with LLM analysis.
        
        Args:
            gateway_id: Gateway UUID
            api_id: API UUID
            api_name: API name
            metrics: Historical metrics
            
        Returns:
            Dict with predictions and analysis
        """
        logger.info(f"Generating enhanced predictions for API {api_name}")
        
        # Initialize state
        initial_state: PredictionState = {
            "api_id": str(api_id),
            "gateway_id": str(gateway_id),
            "api_name": api_name,
            "metrics": metrics,
            "analysis": "",
            "predictions": [],
            "enhanced_predictions": [],
            "error": "",
        }
        
        try:
            # Run workflow if available, otherwise execute directly
            if self.workflow is not None:
                final_state = await self.workflow.ainvoke(initial_state)
            else:
                # Direct execution without LangGraph
                final_state = initial_state
                final_state = await self._analyze_metrics_node(final_state)
                final_state = await self._generate_predictions_node(final_state)
                final_state = await self._enhance_predictions_node(final_state)
            
            return {
                "api_id": str(api_id),
                "api_name": api_name,
                "analysis": final_state.get("analysis"),
                "predictions": final_state.get("enhanced_predictions", []),
                "metrics_analyzed": len(metrics),
            }
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced predictions: {e}")
            return {
                "api_id": str(api_id),
                "api_name": api_name,
                "error": str(e),
                "predictions": [],
            }
    
    async def _analyze_metrics_node(self, state: PredictionState) -> PredictionState:
        """
        Analyze metrics using LLM to identify trends and patterns.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with analysis
        """
        logger.info(f"Analyzing metrics for API {state['api_name']}")
        
        if not state["metrics"] or len(state["metrics"]) < 5:
            state["analysis"] = "Insufficient metrics data for analysis"
            state["error"] = "Not enough metrics data points"
            return state
        
        # Prepare metrics summary for LLM
        metrics_summary = self._prepare_metrics_summary(state["metrics"])
        
        # Create analysis prompt
        system_prompt = """You are an expert API performance analyst. Analyze vendor-neutral, time-bucketed API metrics and identify:
1. Key trends (increasing, decreasing, stable)
2. Anomalies or concerning patterns
3. Potential risk factors
4. Overall health assessment
5. Whether gateway processing, backend latency, cache performance, or error patterns are driving degradation

Provide a concise, technical analysis focusing on actionable insights."""
        
        user_prompt = f"""Analyze the following metrics for API '{state['api_name']}':

{metrics_summary}

Provide a detailed analysis of trends, risks, and health status."""
        
        try:
            # Generate analysis using LLM
            response = await self.llm_service.generate_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Lower temperature for more focused analysis
                max_tokens=500,
            )
            
            analysis = response.get("content", "Analysis unavailable")
            logger.info(f"Generated metrics analysis for API {state['api_name']}")
            
            state["analysis"] = analysis
            return state
            
        except Exception as e:
            logger.error(f"Failed to generate metrics analysis: {e}")
            state["analysis"] = "LLM analysis unavailable"
            state["error"] = str(e)
            return state
    
    async def _generate_predictions_node(self, state: PredictionState) -> PredictionState:
        """
        Generate predictions using the prediction service.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with predictions
        """
        logger.info(f"Generating predictions for API {state['api_name']}")
        
        try:
            # Use prediction service to generate ML-based predictions
            api_id = UUID(state["api_id"]) if isinstance(state["api_id"], str) else state["api_id"]
            gateway_id = UUID(state["gateway_id"]) if isinstance(state["gateway_id"], str) else state["gateway_id"]
            predictions = await self.prediction_service.generate_predictions_for_api(
                gateway_id=gateway_id,
                api_id=api_id,
                min_confidence=0.7,
            )
            
            logger.info(f"Generated {len(predictions)} predictions for API {state['api_name']}")
            
            state["predictions"] = predictions
            return state
            
        except Exception as e:
            logger.error(f"Failed to generate predictions: {e}")
            state["predictions"] = []
            state["error"] = str(e)
            return state
    
    async def _enhance_predictions_node(self, state: PredictionState) -> PredictionState:
        """
        Enhance predictions with LLM-generated explanations and recommendations.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with enhanced predictions
        """
        logger.info(f"Enhancing predictions for API {state['api_name']}")
        
        predictions = state.get("predictions", [])
        if not predictions:
            state["enhanced_predictions"] = []
            return state
        
        enhanced_predictions = []
        
        for prediction in predictions:
            try:
                # Generate detailed explanation using LLM
                explanation = await self._generate_prediction_explanation(
                    prediction=prediction,
                    api_name=state["api_name"],
                    metrics_analysis=state["analysis"] or "",
                )
                
                # Create enhanced prediction dict
                enhanced = {
                    "id": str(prediction.id),
                    "api_id": str(prediction.api_id),
                    "prediction_type": prediction.prediction_type.value,
                    "predicted_at": prediction.predicted_at.isoformat(),
                    "predicted_time": prediction.predicted_time.isoformat(),
                    "confidence_score": prediction.confidence_score,
                    "severity": prediction.severity.value,
                    "status": prediction.status.value,
                    "contributing_factors": [
                        {
                            "factor": f.factor,
                            "current_value": f.current_value,
                            "threshold": f.threshold,
                            "trend": f.trend,
                            "weight": f.weight,
                        }
                        for f in prediction.contributing_factors
                    ],
                    "recommended_actions": prediction.recommended_actions,
                    "llm_explanation": explanation,
                    "model_version": prediction.model_version,
                }
                
                enhanced_predictions.append(enhanced)
                
            except Exception as e:
                logger.error(f"Failed to enhance prediction {prediction.id}: {e}")
                # Include prediction without enhancement
                enhanced_predictions.append({
                    "id": str(prediction.id),
                    "api_id": str(prediction.api_id),
                    "prediction_type": prediction.prediction_type.value,
                    "confidence_score": prediction.confidence_score,
                    "severity": prediction.severity.value,
                    "error": "Enhancement failed",
                })
        
        state["enhanced_predictions"] = enhanced_predictions
        return state
    
    async def _generate_prediction_explanation(
        self,
        prediction: Prediction,
        api_name: str,
        metrics_analysis: str,
    ) -> str:
        """
        Generate detailed explanation for a prediction using LLM.
        
        Args:
            prediction: Prediction to explain
            api_name: API name
            metrics_analysis: Previous metrics analysis
            
        Returns:
            Detailed explanation text
        """
        # Prepare contributing factors summary
        factors_text = "\n".join([
            f"- {f.factor}: current={f.current_value:.2f}, threshold={f.threshold:.2f}, "
            f"trend={f.trend}, weight={f.weight:.2f}"
            for f in prediction.contributing_factors
        ])
        
        # Create explanation prompt
        system_prompt = """You are an expert API reliability engineer. Explain the prediction in clear, actionable terms that help engineers understand:
1. Why this prediction was made
2. What the contributing factors mean
3. The potential impact
4. Priority of recommended actions

Be concise but thorough. Focus on practical insights."""
        
        user_prompt = f"""Explain this {prediction.prediction_type.value} prediction for API '{api_name}':

Confidence: {prediction.confidence_score:.2%}
Severity: {prediction.severity.value}
Predicted Time: {prediction.predicted_time.strftime('%Y-%m-%d %H:%M UTC')}

Contributing Factors:
{factors_text}

Recommended Actions:
{chr(10).join(f'{i+1}. {action}' for i, action in enumerate(prediction.recommended_actions))}

Previous Analysis:
{metrics_analysis}

Provide a clear explanation of this prediction and why the recommended actions are important."""
        
        try:
            response = await self.llm_service.generate_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.4,
                max_tokens=400,
            )
            
            return response.get("content", "Explanation unavailable")
            
        except Exception as e:
            logger.error(f"Failed to generate prediction explanation: {e}")
            return "LLM explanation unavailable due to error"
    
    def _prepare_metrics_summary(self, metrics: List[Metric]) -> str:
        """
        Prepare a summary of metrics for LLM analysis.
        
        Args:
            metrics: List of time-bucketed metrics
            
        Returns:
            Formatted metrics summary
        """
        if not metrics:
            return "No metrics available"
        
        # Calculate statistics
        error_rates = [m.error_rate for m in metrics]
        response_times_p95 = [m.response_time_p95 for m in metrics]
        throughputs = [m.throughput for m in metrics]
        availabilities = [m.availability for m in metrics]
        cache_hit_rates = [m.cache_hit_rate for m in metrics]
        gateway_times = [m.gateway_time_avg for m in metrics]
        backend_times = [m.backend_time_avg for m in metrics]
        
        # Get time bucket info from first metric
        time_bucket = metrics[0].time_bucket.value if hasattr(metrics[0], 'time_bucket') else "unknown"
        
        hours_covered = abs((metrics[0].timestamp - metrics[-1].timestamp).total_seconds()) / 3600

        summary = f"""Metrics Summary ({len(metrics)} data points, {time_bucket} buckets, over {hours_covered:.1f} hours):

Error Rate (% of requests):
  - Current: {error_rates[0]:.2f}%
  - Average: {sum(error_rates) / len(error_rates):.2f}%
  - Min: {min(error_rates):.2f}%
  - Max: {max(error_rates):.2f}%

Response Time (P95):
  - Current: {response_times_p95[0]:.0f}ms
  - Average: {sum(response_times_p95) / len(response_times_p95):.0f}ms
  - Min: {min(response_times_p95):.0f}ms
  - Max: {max(response_times_p95):.0f}ms

Timing Breakdown:
  - Gateway Time (avg): {gateway_times[0]:.0f}ms (current), {sum(gateway_times) / len(gateway_times):.0f}ms (avg)
  - Backend Time (avg): {backend_times[0]:.0f}ms (current), {sum(backend_times) / len(backend_times):.0f}ms (avg)

Throughput:
  - Current: {throughputs[0]:.0f} req/s
  - Average: {sum(throughputs) / len(throughputs):.0f} req/s
  - Min: {min(throughputs):.0f} req/s
  - Max: {max(throughputs):.0f} req/s

Availability:
  - Current: {availabilities[0]:.2f}%
  - Average: {sum(availabilities) / len(availabilities):.2f}%
  - Min: {min(availabilities):.2f}%
  - Max: {max(availabilities):.2f}%

Cache Performance:
  - Hit Rate (current): {cache_hit_rates[0]:.2f}%
  - Hit Rate (average): {sum(cache_hit_rates) / len(cache_hit_rates):.2f}%

Recent Trend (last 5 points):
  - Error Rate: {[f'{rate:.2f}%' for rate in error_rates[:5]]}
  - Response Time P95: {[f'{rt:.0f}ms' for rt in response_times_p95[:5]]}
  - Throughput: {[f'{t:.0f}' for t in throughputs[:5]]}
  - Cache Hit Rate: {[f'{rate:.1f}%' for rate in cache_hit_rates[:5]]}
"""
        
        return summary

    async def generate_remediation_plan(
        self,
        prediction: Prediction,
        gateway_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate AI-powered remediation plan for a prediction.
        
        Uses LLM to analyze the prediction and generate API-scoped
        remediation recommendations for webMethods gateway.
        
        Args:
            prediction: Prediction entity to generate plan for
            gateway_config: Current gateway configuration for context
            
        Returns:
            Structured remediation plan with actions and verification steps
        """
        logger.info(f"Generating remediation plan for prediction {prediction.id}")
        
        try:
            # Build context for LLM
            context = self._build_remediation_context(prediction, gateway_config)
            
            # Generate plan using LLM
            response = await self.llm_service.generate_completion(
                messages=[
                    {
                        "role": "system",
                        "content": self._get_remediation_planning_prompt()
                    },
                    {
                        "role": "user",
                        "content": context
                    }
                ],
                temperature=0.2,  # Low temperature for consistent, focused plans
                max_tokens=1000,
            )
            
            # Parse LLM response into structured plan
            plan_text = response.get("content", "")
            plan = self._parse_remediation_plan(plan_text, prediction)
            
            logger.info(f"Generated remediation plan with {len(plan.get('actions', []))} actions")
            
            return plan
            
        except Exception as e:
            logger.error(f"Failed to generate remediation plan: {e}")
            # Fallback to rule-based plan
            return self._generate_fallback_remediation_plan(prediction)
    
    def _get_remediation_planning_prompt(self) -> str:
        """Get system prompt for remediation planning.
        
        Returns:
            System prompt for LLM
        """
        return """You are an expert API gateway engineer specializing in preventive remediation.

Your task is to analyze API failure predictions and generate actionable remediation plans.

SCOPE: API-level policies only (webMethods API Gateway)
- Rate limiting policies
- Request throttling
- Response caching
- Request/response validation

DO NOT suggest:
- Gateway deployment scaling
- Backend service changes
- Infrastructure modifications
- Code changes

For each prediction, provide:
1. A clear summary of the remediation approach
2. Specific actions with estimated time and effectiveness
3. Verification steps to confirm success
4. Priority level (critical, high, medium, low)

Format your response as JSON:
{
  "summary": "Brief description of remediation approach",
  "priority": "high",
  "actions": [
    {
      "type": "rate_limiting",
      "description": "Apply rate limiting: 1000 requests/minute",
      "estimated_minutes": 10,
      "effectiveness_estimate": 0.85,
      "configuration": {
        "requests_per_minute": 1000
      }
    }
  ],
  "verification_steps": [
    "Monitor error rate for 30 minutes",
    "Verify API remains stable"
  ],
  "estimated_minutes": 20,
  "rollback_plan": "Remove rate limiting policy if ineffective"
}

Be specific, actionable, and focused on prevention."""
    
    def _build_remediation_context(
        self,
        prediction: Prediction,
        gateway_config: Dict[str, Any]
    ) -> str:
        """Build context for remediation planning.
        
        Args:
            prediction: Prediction to remediate
            gateway_config: Current gateway configuration
            
        Returns:
            Formatted context string for LLM
        """
        # Format contributing factors
        factors_text = "\n".join([
            f"- {f.factor.value}: current={f.current_value}, threshold={f.threshold}, trend={f.trend}"
            for f in prediction.contributing_factors
        ])
        
        context = f"""Prediction Analysis:

API: {prediction.api_name or prediction.api_id}
Prediction Type: {prediction.prediction_type.value}
Severity: {prediction.severity.value}
Confidence: {prediction.confidence_score:.2f}
Predicted Time: {prediction.predicted_time.isoformat()}

Contributing Factors:
{factors_text}

Current Recommended Actions:
{chr(10).join(f"- {action}" for action in prediction.recommended_actions)}

Gateway Configuration:
{gateway_config.get('summary', 'No configuration available')}

Generate a remediation plan to prevent this {prediction.prediction_type.value} prediction."""
        
        return context
    
    def _parse_remediation_plan(
        self,
        plan_text: str,
        prediction: Prediction
    ) -> Dict[str, Any]:
        """Parse LLM response into structured remediation plan.
        
        Args:
            plan_text: LLM response text
            prediction: Original prediction
            
        Returns:
            Structured remediation plan
        """
        import json
        import re
        
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', plan_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
            else:
                # Fallback if no JSON found
                logger.warning("No JSON found in LLM response, using fallback")
                return self._generate_fallback_remediation_plan(prediction)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._generate_fallback_remediation_plan(prediction)
    
    def _generate_fallback_remediation_plan(
        self,
        prediction: Prediction
    ) -> Dict[str, Any]:
        """Generate fallback remediation plan when LLM fails.
        
        Args:
            prediction: Prediction to remediate
            
        Returns:
            Rule-based remediation plan
        """
        from app.models.prediction import PredictionType, PredictionSeverity
        
        # Map prediction type to actions
        action_map = {
            PredictionType.FAILURE: [
                {
                    "type": "rate_limiting",
                    "description": "Apply rate limiting to prevent overload",
                    "estimated_minutes": 10,
                    "effectiveness_estimate": 0.75,
                    "configuration": {"requests_per_minute": 1000}
                },
                {
                    "type": "validation_policy",
                    "description": "Add request validation to catch errors early",
                    "estimated_minutes": 15,
                    "effectiveness_estimate": 0.65,
                    "configuration": {"validate_request": True}
                }
            ],
            PredictionType.DEGRADATION: [
                {
                    "type": "rate_limiting",
                    "description": "Apply rate limiting to reduce load",
                    "estimated_minutes": 10,
                    "effectiveness_estimate": 0.80,
                    "configuration": {"requests_per_minute": 800}
                },
                {
                    "type": "cache_config",
                    "description": "Enable response caching to reduce backend load",
                    "estimated_minutes": 10,
                    "effectiveness_estimate": 0.70,
                    "configuration": {"ttl_seconds": 300}
                }
            ],
            PredictionType.CAPACITY: [
                {
                    "type": "throttling",
                    "description": "Apply request throttling to manage capacity",
                    "estimated_minutes": 10,
                    "effectiveness_estimate": 0.85,
                    "configuration": {"max_concurrent_requests": 100}
                },
                {
                    "type": "cache_config",
                    "description": "Enable caching to reduce backend requests",
                    "estimated_minutes": 10,
                    "effectiveness_estimate": 0.75,
                    "configuration": {"ttl_seconds": 600}
                }
            ],
            PredictionType.SECURITY: [
                {
                    "type": "rate_limiting",
                    "description": "Apply strict rate limiting for security",
                    "estimated_minutes": 10,
                    "effectiveness_estimate": 0.80,
                    "configuration": {"requests_per_minute": 500}
                },
                {
                    "type": "validation_policy",
                    "description": "Add strict request validation",
                    "estimated_minutes": 15,
                    "effectiveness_estimate": 0.70,
                    "configuration": {"validate_request": True, "validate_response": False}
                }
            ]
        }
        
        actions = action_map.get(prediction.prediction_type, action_map[PredictionType.DEGRADATION])
        
        # Determine priority based on severity
        priority_map = {
            PredictionSeverity.CRITICAL: "critical",
            PredictionSeverity.HIGH: "high",
            PredictionSeverity.MEDIUM: "medium",
            PredictionSeverity.LOW: "low"
        }
        priority = priority_map.get(prediction.severity, "medium")
        
        return {
            "summary": f"Apply {len(actions)} API-level policies to prevent {prediction.prediction_type.value}",
            "priority": priority,
            "actions": actions,
            "verification_steps": [
                f"Monitor {prediction.prediction_type.value} metrics for 30 minutes",
                "Verify API remains stable and responsive",
                "Check for any unintended side effects"
            ],
            "estimated_minutes": sum(a["estimated_minutes"] for a in actions),
            "rollback_plan": "Remove applied policies if prediction was false positive or remediation causes issues"
        }

# Made with Bob
