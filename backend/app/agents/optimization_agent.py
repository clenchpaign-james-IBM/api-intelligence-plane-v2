"""
Optimization Agent

AI agent for enhanced optimization recommendation generation using LangChain/LangGraph.
Provides LLM-powered analysis of performance patterns and recommendation prioritization.
"""

import logging
from typing import List, Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from langchain.prompts import ChatPromptTemplate
    from langchain.schema import HumanMessage, SystemMessage
    from langgraph.graph import StateGraph, END
else:
    try:
        from langchain.prompts import ChatPromptTemplate
        from langchain.schema import HumanMessage, SystemMessage
        from langgraph.graph import StateGraph, END
    except ImportError:
        # LangChain/LangGraph are optional dependencies
        StateGraph = None
        END = None
        ChatPromptTemplate = None
        HumanMessage = None
        SystemMessage = None

from app.services.llm_service import LLMService
from app.services.optimization_service import OptimizationService
from app.models.recommendation import OptimizationRecommendation, RecommendationType
from app.models.metric import Metric

logger = logging.getLogger(__name__)


class OptimizationState(BaseModel):
    """State for optimization recommendation workflow."""
    
    api_id: UUID
    api_name: str
    metrics: List[Metric] = Field(default_factory=list)
    performance_analysis: Optional[str] = None
    recommendations: List[OptimizationRecommendation] = Field(default_factory=list)
    enhanced_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    prioritization: Optional[str] = None
    error: Optional[str] = None


class OptimizationAgent:
    """
    AI agent for enhanced optimization recommendation generation.
    
    Uses LangChain for LLM integration and LangGraph for workflow orchestration.
    """
    
    def __init__(
        self,
        llm_service: LLMService,
        optimization_service: OptimizationService,
    ):
        """
        Initialize the Optimization Agent.
        
        Args:
            llm_service: LLM service for AI-powered analysis
            optimization_service: Optimization service for recommendation generation
        """
        self.llm_service = llm_service
        self.optimization_service = optimization_service
        self.workflow = self._build_workflow()
    
    def _build_workflow(self) -> Any:
        """
        Build the optimization recommendation workflow using LangGraph.
        
        Returns:
            Compiled StateGraph workflow
        """
        if StateGraph is None:
            raise ImportError(
                "LangGraph is required for OptimizationAgent. "
                "Install with: pip install langgraph"
            )
        
        workflow = StateGraph(OptimizationState)
        
        # Define workflow nodes
        workflow.add_node("analyze_performance", self._analyze_performance_node)
        workflow.add_node("generate_recommendations", self._generate_recommendations_node)
        workflow.add_node("enhance_recommendations", self._enhance_recommendations_node)
        workflow.add_node("prioritize_recommendations", self._prioritize_recommendations_node)
        
        # Define workflow edges
        workflow.set_entry_point("analyze_performance")
        workflow.add_edge("analyze_performance", "generate_recommendations")
        workflow.add_edge("generate_recommendations", "enhance_recommendations")
        workflow.add_edge("enhance_recommendations", "prioritize_recommendations")
        workflow.add_edge("prioritize_recommendations", END)
        
        return workflow.compile()
    
    async def generate_enhanced_recommendations(
        self,
        api_id: UUID,
        api_name: str,
        metrics: List[Metric],
        focus_areas: Optional[List[RecommendationType]] = None,
    ) -> Dict[str, Any]:
        """
        Generate enhanced optimization recommendations with LLM analysis.
        
        Args:
            api_id: API UUID
            api_name: API name
            metrics: Historical metrics
            focus_areas: Specific optimization types to focus on
            
        Returns:
            Dict with recommendations and analysis
        """
        logger.info(f"Generating enhanced optimization recommendations for API {api_name}")
        
        # Initialize state
        initial_state = OptimizationState(
            api_id=api_id,
            api_name=api_name,
            metrics=metrics,
        )
        
        try:
            # Run workflow
            final_state = await self.workflow.ainvoke(initial_state)
            
            return {
                "api_id": str(api_id),
                "api_name": api_name,
                "performance_analysis": final_state.get("performance_analysis"),
                "recommendations": final_state.get("enhanced_recommendations", []),
                "prioritization": final_state.get("prioritization"),
                "metrics_analyzed": len(metrics),
            }
            
        except Exception as e:
            logger.error(f"Failed to generate enhanced recommendations: {e}")
            return {
                "api_id": str(api_id),
                "api_name": api_name,
                "error": str(e),
                "recommendations": [],
            }
    
    async def _analyze_performance_node(self, state: OptimizationState) -> Dict[str, Any]:
        """
        Analyze performance metrics using LLM to identify optimization opportunities.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with performance analysis
        """
        logger.info(f"Analyzing performance for API {state.api_name}")
        
        if not state.metrics or len(state.metrics) < 5:
            return {
                "performance_analysis": "Insufficient metrics data for analysis",
                "error": "Not enough metrics data points",
            }
        
        # Prepare metrics summary for LLM
        metrics_summary = self._prepare_metrics_summary(state.metrics)
        
        # Create analysis prompt
        system_prompt = """You are an expert performance optimization consultant. Analyze the provided metrics data and identify:
1. Performance bottlenecks (response time, throughput, error rates)
2. Resource utilization patterns
3. Scalability concerns
4. Optimization opportunities with highest impact
5. Quick wins vs. long-term improvements

Provide a concise, technical analysis focusing on actionable optimization opportunities."""
        
        user_prompt = f"""Analyze the following performance metrics for API '{state.api_name}':

{metrics_summary}

Identify the top optimization opportunities and their potential impact."""
        
        try:
            # Generate analysis using LLM
            response = await self.llm_service.generate_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,  # Lower temperature for more focused analysis
                max_tokens=600,
            )
            
            analysis = response.get("content", "Analysis unavailable")
            logger.info(f"Generated performance analysis for API {state.api_name}")
            
            return {"performance_analysis": analysis}
            
        except Exception as e:
            logger.error(f"Failed to generate performance analysis: {e}")
            return {
                "performance_analysis": f"Analysis failed: {str(e)}",
                "error": str(e),
            }
    
    async def _generate_recommendations_node(
        self, state: OptimizationState
    ) -> Dict[str, Any]:
        """
        Generate optimization recommendations using the optimization service.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with recommendations
        """
        logger.info(f"Generating recommendations for API {state.api_name}")
        
        try:
            # Generate recommendations using optimization service
            recommendations = self.optimization_service.generate_recommendations_for_api(
                api_id=state.api_id,
                min_impact=10.0,
            )
            
            logger.info(
                f"Generated {len(recommendations)} recommendations for API {state.api_name}"
            )
            
            return {"recommendations": recommendations}
            
        except Exception as e:
            logger.error(f"Failed to generate recommendations: {e}")
            return {
                "recommendations": [],
                "error": str(e),
            }
    
    async def _enhance_recommendations_node(
        self, state: OptimizationState
    ) -> Dict[str, Any]:
        """
        Enhance recommendations with LLM-generated insights and explanations.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with enhanced recommendations
        """
        logger.info(f"Enhancing recommendations for API {state.api_name}")
        
        if not state.recommendations:
            return {"enhanced_recommendations": []}
        
        enhanced = []
        
        for rec in state.recommendations:
            try:
                # Create enhancement prompt
                system_prompt = """You are an expert performance optimization consultant. 
Enhance the given optimization recommendation by:
1. Adding specific implementation details
2. Identifying potential challenges and mitigation strategies
3. Suggesting monitoring metrics to track success
4. Providing realistic timeline estimates

Keep the response concise and actionable."""
                
                user_prompt = f"""Enhance this optimization recommendation:

Type: {rec.recommendation_type.value}
Title: {rec.title}
Description: {rec.description}
Expected Improvement: {rec.estimated_impact.improvement_percentage:.1f}%
Effort: {rec.implementation_effort.value}

Provide enhanced implementation guidance and success metrics."""
                
                # Generate enhancement using LLM
                response = await self.llm_service.generate_completion(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.4,
                    max_tokens=400,
                )
                
                enhancement = response.get("content", "")
                
                # Create enhanced recommendation dict
                enhanced_rec = {
                    "id": str(rec.id),
                    "api_id": str(rec.api_id),
                    "type": rec.recommendation_type.value,
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority.value,
                    "estimated_impact": {
                        "metric": rec.estimated_impact.metric,
                        "current_value": rec.estimated_impact.current_value,
                        "expected_value": rec.estimated_impact.expected_value,
                        "improvement_percentage": rec.estimated_impact.improvement_percentage,
                        "confidence": rec.estimated_impact.confidence,
                    },
                    "implementation_effort": rec.implementation_effort.value,
                    "implementation_steps": rec.implementation_steps,
                    "cost_savings": rec.cost_savings,
                    "ai_enhancement": enhancement,
                    "status": rec.status.value,
                }
                
                enhanced.append(enhanced_rec)
                
            except Exception as e:
                logger.error(f"Failed to enhance recommendation {rec.id}: {e}")
                # Include original recommendation without enhancement
                enhanced.append({
                    "id": str(rec.id),
                    "api_id": str(rec.api_id),
                    "type": rec.recommendation_type.value,
                    "title": rec.title,
                    "description": rec.description,
                    "priority": rec.priority.value,
                    "estimated_impact": {
                        "metric": rec.estimated_impact.metric,
                        "improvement_percentage": rec.estimated_impact.improvement_percentage,
                    },
                    "implementation_effort": rec.implementation_effort.value,
                    "status": rec.status.value,
                    "error": f"Enhancement failed: {str(e)}",
                })
        
        logger.info(f"Enhanced {len(enhanced)} recommendations for API {state.api_name}")
        
        return {"enhanced_recommendations": enhanced}
    
    async def _prioritize_recommendations_node(
        self, state: OptimizationState
    ) -> Dict[str, Any]:
        """
        Generate prioritization guidance using LLM.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with prioritization guidance
        """
        logger.info(f"Prioritizing recommendations for API {state.api_name}")
        
        if not state.enhanced_recommendations:
            return {"prioritization": "No recommendations to prioritize"}
        
        # Prepare recommendations summary
        recs_summary = "\n".join([
            f"{i+1}. {rec['title']} - {rec['type']} "
            f"(Impact: {rec['estimated_impact']['improvement_percentage']:.1f}%, "
            f"Effort: {rec['implementation_effort']}, Priority: {rec['priority']})"
            for i, rec in enumerate(state.enhanced_recommendations)
        ])
        
        # Create prioritization prompt
        system_prompt = """You are an expert performance optimization consultant. 
Review the list of optimization recommendations and provide:
1. Recommended implementation order
2. Rationale for prioritization
3. Dependencies between recommendations
4. Quick wins to implement first
5. Long-term strategic improvements

Be concise and actionable."""
        
        user_prompt = f"""Prioritize these optimization recommendations for API '{state.api_name}':

{recs_summary}

Performance Analysis:
{state.performance_analysis}

Provide a clear implementation roadmap."""
        
        try:
            # Generate prioritization using LLM
            response = await self.llm_service.generate_completion(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )
            
            prioritization = response.get("content", "Prioritization unavailable")
            logger.info(f"Generated prioritization guidance for API {state.api_name}")
            
            return {"prioritization": prioritization}
            
        except Exception as e:
            logger.error(f"Failed to generate prioritization: {e}")
            return {
                "prioritization": f"Prioritization failed: {str(e)}",
                "error": str(e),
            }
    
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
        
        # Calculate averages
        avg_p50 = sum(m.response_time_p50 for m in metrics) / len(metrics)
        avg_p95 = sum(m.response_time_p95 for m in metrics) / len(metrics)
        avg_p99 = sum(m.response_time_p99 for m in metrics) / len(metrics)
        avg_error_rate = sum(m.error_rate for m in metrics) / len(metrics)
        avg_throughput = sum(m.throughput for m in metrics) / len(metrics)
        avg_availability = sum(m.availability for m in metrics) / len(metrics)
        
        # Calculate trends (compare first half vs second half)
        mid = len(metrics) // 2
        first_half_p95 = sum(m.response_time_p95 for m in metrics[:mid]) / mid
        second_half_p95 = sum(m.response_time_p95 for m in metrics[mid:]) / (len(metrics) - mid)
        p95_trend = ((second_half_p95 - first_half_p95) / first_half_p95 * 100) if first_half_p95 > 0 else 0
        
        first_half_error = sum(m.error_rate for m in metrics[:mid]) / mid
        second_half_error = sum(m.error_rate for m in metrics[mid:]) / (len(metrics) - mid)
        error_trend = ((second_half_error - first_half_error) / first_half_error * 100) if first_half_error > 0 else 0
        
        summary = f"""
Metrics Summary ({len(metrics)} data points):

Response Times:
- P50: {avg_p50:.1f}ms
- P95: {avg_p95:.1f}ms (trend: {p95_trend:+.1f}%)
- P99: {avg_p99:.1f}ms

Error Rate: {avg_error_rate*100:.2f}% (trend: {error_trend:+.1f}%)
Throughput: {avg_throughput:.1f} req/s
Availability: {avg_availability:.2f}%

Recent Metrics (last 5):
"""
        
        for i, m in enumerate(metrics[-5:], 1):
            summary += f"\n{i}. P95: {m.response_time_p95:.0f}ms, Errors: {m.error_rate*100:.1f}%, Throughput: {m.throughput:.0f} req/s"
        
        return summary


# Made with Bob