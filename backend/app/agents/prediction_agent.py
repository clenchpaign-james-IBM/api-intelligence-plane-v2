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
from app.models.metric import Metric

logger = logging.getLogger(__name__)


class PredictionState(TypedDict):
    """State for prediction generation workflow."""
    
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
        api_id: UUID,
        api_name: str,
        metrics: List[Metric],
    ) -> Dict[str, Any]:
        """
        Generate enhanced predictions with LLM analysis.
        
        Args:
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
        system_prompt = """You are an expert API performance analyst. Analyze the provided metrics data and identify:
1. Key trends (increasing, decreasing, stable)
2. Anomalies or concerning patterns
3. Potential risk factors
4. Overall health assessment

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
            predictions = self.prediction_service.generate_predictions_for_api(
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
            metrics: List of metrics
            
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
        
        summary = f"""Metrics Summary ({len(metrics)} data points over {(metrics[0].timestamp - metrics[-1].timestamp).total_seconds() / 3600:.1f} hours):

Error Rate:
  - Current: {error_rates[0]:.2%}
  - Average: {sum(error_rates) / len(error_rates):.2%}
  - Min: {min(error_rates):.2%}
  - Max: {max(error_rates):.2%}

Response Time (P95):
  - Current: {response_times_p95[0]:.0f}ms
  - Average: {sum(response_times_p95) / len(response_times_p95):.0f}ms
  - Min: {min(response_times_p95):.0f}ms
  - Max: {max(response_times_p95):.0f}ms

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

Recent Trend (last 5 points):
  - Error Rate: {error_rates[:5]}
  - Response Time P95: {[f'{rt:.0f}ms' for rt in response_times_p95[:5]]}
  - Throughput: {[f'{t:.0f}' for t in throughputs[:5]]}
"""
        
        return summary

# Made with Bob
