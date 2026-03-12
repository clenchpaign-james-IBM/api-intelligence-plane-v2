"""Optimization MCP Server for API Intelligence Plane.

This MCP server provides tools for performance optimization, predictions, and
rate limiting for APIs. It acts as a thin wrapper around the backend REST API,
exposing tools that AI agents can use to interact with optimization functionality.

Port: 8004
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


class OptimizationMCPServer(BaseMCPServer):
    """MCP Server for API Optimization operations.
    
    Provides tools for:
    - Generating failure predictions
    - Creating optimization recommendations
    - Managing rate limit policies
    - Analyzing rate limit effectiveness
    
    This server acts as a thin wrapper around the backend REST API,
    delegating all business logic to the backend services.
    """

    def __init__(self):
        """Initialize Optimization MCP server."""
        super().__init__(name="optimization-server", version="1.0.0")
        
        # Initialize backend client instead of OpenSearch
        self.backend_client = BackendClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        
        # Register tools
        self._register_tools()
        
        logger.info("Optimization MCP server initialized (using backend API)")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        @self.tool(description="Check Optimization server health and status")
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
        @self.tool(description="Get Optimization server information")
        def server_info() -> dict[str, Any]:
            """Get server information.
            
            Returns:
                dict: Server metadata and capabilities
            """
            info = self.get_server_info()
            info.update({
                "port": 8004,
                "transport": "streamable-http",
                "architecture": "thin_wrapper",
                "backend_url": self.backend_client.base_url,
                "capabilities": [
                    "failure_prediction",
                    "performance_optimization",
                    "rate_limiting",
                    "capacity_planning"
                ]
            })
            return info
        
        # Prediction tools
        @self.tool(description="Generate failure predictions for APIs")
        async def generate_predictions(
            api_id: Optional[str] = None,
            prediction_window_hours: int = 48,
            min_confidence: float = 0.7
        ) -> dict[str, Any]:
            """Generate failure predictions for APIs.
            
            Args:
                api_id: Specific API UUID (empty = all APIs)
                prediction_window_hours: Prediction time window (24-72 hours)
                min_confidence: Minimum confidence threshold (0-1)
                
            Returns:
                dict: Generated predictions with metadata
            """
            start_time = datetime.utcnow()
            
            try:
                # Validate inputs
                if prediction_window_hours < 24 or prediction_window_hours > 72:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "prediction_window_hours must be between 24 and 72",
                            "details": {"provided": prediction_window_hours}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                if min_confidence < 0 or min_confidence > 1:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "min_confidence must be between 0 and 1",
                            "details": {"provided": min_confidence}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                # Validate API ID if provided
                if api_id:
                    try:
                        UUID(api_id)
                    except ValueError:
                        return {
                            "success": False,
                            "error": {
                                "code": "INVALID_INPUT",
                                "message": "Invalid API ID format",
                                "details": {"api_id": api_id}
                            },
                            "metadata": {"timestamp": start_time.isoformat()}
                        }
                
                # Trigger prediction generation via backend
                result = await self.backend_client.generate_predictions(
                    api_id=api_id,
                    min_confidence=min_confidence,
                    use_ai=False
                )
                
                # Get generated predictions
                predictions_response = await self.backend_client.list_predictions(
                    api_id=api_id,
                    status="active",
                    page_size=1000
                )
                
                predictions = predictions_response.get("predictions", [])
                
                # Filter by confidence
                predictions = [
                    p for p in predictions
                    if p.get("confidence_score", 0) >= min_confidence
                ]
                
                # Format predictions
                formatted_predictions = [
                    {
                        "id": p.get("id"),
                        "api_id": p.get("api_id"),
                        "api_name": p.get("api_name", "Unknown"),
                        "prediction_type": p.get("prediction_type"),
                        "severity": p.get("severity"),
                        "confidence": p.get("confidence_score"),
                        "predicted_time": p.get("predicted_time"),
                        "description": f"{p.get('prediction_type')} prediction with {p.get('severity')} severity",
                        "recommended_actions": p.get("recommended_actions", []),
                        "contributing_factors": [
                            {
                                "factor": f.get("factor"),
                                "current_value": f.get("current_value"),
                                "threshold": f.get("threshold")
                            }
                            for f in p.get("contributing_factors", [])
                        ],
                        "created_at": p.get("created_at")
                    }
                    for p in predictions
                ]
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "predictions_generated": len(formatted_predictions),
                        "predictions": formatted_predictions,
                        "model_version": "1.0.0",
                        "generated_at": datetime.utcnow().isoformat()
                    },
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error generating predictions: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": {
                        "code": "PREDICTION_FAILED",
                        "message": str(e),
                        "details": {}
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()}
                }
        
        # Optimization recommendation tools
        @self.tool(description="Generate performance optimization recommendations")
        async def generate_optimization_recommendations(
            api_id: str,
            focus_areas: Optional[List[str]] = None,
            min_impact_percentage: float = 10.0
        ) -> dict[str, Any]:
            """Generate performance optimization recommendations.
            
            Args:
                api_id: Target API UUID
                focus_areas: Specific areas (caching, query_optimization, resource_allocation, compression)
                min_impact_percentage: Minimum expected improvement (0-100)
                
            Returns:
                dict: Optimization recommendations with potential savings
            """
            start_time = datetime.utcnow()
            
            try:
                # Validate API ID
                try:
                    UUID(api_id)
                except ValueError:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "Invalid API ID format",
                            "details": {"api_id": api_id}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                # Trigger recommendation generation via backend
                await self.backend_client.generate_recommendations(
                    api_id=api_id,
                    min_impact=min_impact_percentage,
                    use_ai=False
                )
                
                # Get generated recommendations
                recommendations_response = await self.backend_client.list_recommendations(
                    api_id=api_id,
                    status="pending",
                    recommendation_type=focus_areas[0] if focus_areas else None,
                    page_size=100
                )
                
                recommendations = recommendations_response.get("recommendations", [])
                
                # Filter by impact if needed
                recommendations = [
                    r for r in recommendations
                    if r.get("estimated_impact", {}).get("improvement_percentage", 0) >= min_impact_percentage
                ]
                
                # Format recommendations
                formatted_recommendations = [
                    {
                        "id": r.get("id"),
                        "optimization_type": r.get("recommendation_type"),
                        "title": r.get("title"),
                        "description": r.get("description"),
                        "expected_improvement_percentage": r.get("estimated_impact", {}).get("improvement_percentage", 0),
                        "implementation_effort": r.get("implementation_effort"),
                        "estimated_savings_usd_monthly": r.get("cost_savings", 0),
                        "recommended_actions": r.get("implementation_steps", []),
                        "created_at": r.get("created_at")
                    }
                    for r in recommendations
                ]
                
                total_savings = sum(r.get("estimated_savings_usd_monthly", 0) for r in formatted_recommendations)
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "recommendations_count": len(formatted_recommendations),
                        "recommendations": formatted_recommendations,
                        "total_potential_savings": total_savings
                    },
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error generating recommendations: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": {
                        "code": "RECOMMENDATION_FAILED",
                        "message": str(e),
                        "details": {}
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()}
                }
        
        # Rate limiting tools
        @self.tool(description="Create or update rate limit policy")
        async def manage_rate_limit(
            api_id: str,
            policy_type: str,
            limit_thresholds: dict[str, int],
            enforcement_action: str = "throttle"
        ) -> dict[str, Any]:
            """Create or update rate limit policy.
            
            Args:
                api_id: Target API UUID
                policy_type: Policy type (fixed, adaptive, priority_based, burst_allowance)
                limit_thresholds: Thresholds (requests_per_second, requests_per_minute, requests_per_hour)
                enforcement_action: Action (throttle, reject, queue)
                
            Returns:
                dict: Created/updated policy information
            """
            start_time = datetime.utcnow()
            
            try:
                # Validate inputs
                valid_policy_types = ["fixed", "adaptive", "priority_based", "burst_allowance"]
                if policy_type not in valid_policy_types:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": f"policy_type must be one of {valid_policy_types}",
                            "details": {"provided": policy_type}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                valid_actions = ["throttle", "reject", "queue"]
                if enforcement_action not in valid_actions:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": f"enforcement_action must be one of {valid_actions}",
                            "details": {"provided": enforcement_action}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                # Validate API ID
                try:
                    UUID(api_id)
                except ValueError:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "Invalid API ID format",
                            "details": {"api_id": api_id}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                # Create policy via backend
                policy_name = f"{policy_type}-policy-{int(datetime.utcnow().timestamp())}"
                
                policy = await self.backend_client.create_rate_limit_policy(
                    api_id=api_id,
                    policy_name=policy_name,
                    policy_type=policy_type,
                    limit_thresholds=limit_thresholds,
                    enforcement_action=enforcement_action
                )
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "policy_id": policy.get("id"),
                        "status": "created",
                        "policy": policy
                    },
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error managing rate limit: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": {
                        "code": "RATE_LIMIT_FAILED",
                        "message": str(e),
                        "details": {}
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()}
                }
        
        @self.tool(description="Analyze effectiveness of rate limiting policies")
        async def analyze_rate_limit_effectiveness(
            api_id: str,
            policy_id: Optional[str] = None,
            analysis_period_hours: int = 24
        ) -> dict[str, Any]:
            """Analyze effectiveness of rate limiting policies.
            
            Args:
                api_id: Target API UUID
                policy_id: Specific policy UUID (optional)
                analysis_period_hours: Analysis period in hours
                
            Returns:
                dict: Effectiveness analysis with metrics and recommendations
            """
            start_time = datetime.utcnow()
            
            try:
                # Validate API ID
                try:
                    UUID(api_id)
                except ValueError:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "Invalid API ID format",
                            "details": {"api_id": api_id}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                # Get policies for this API
                policies_response = await self.backend_client.list_rate_limit_policies(
                    api_id=api_id,
                    status="active",
                    page_size=100
                )
                
                policies = policies_response.get("items", [])
                
                # Filter by specific policy if provided
                if policy_id:
                    policies = [p for p in policies if p.get("id") == policy_id]
                
                if not policies:
                    return {
                        "success": False,
                        "error": {
                            "code": "NOT_FOUND",
                            "message": "No active rate limit policies found",
                            "details": {"api_id": api_id, "policy_id": policy_id}
                        },
                        "metadata": {"timestamp": start_time.isoformat()}
                    }
                
                # Analyze the first policy (or specified policy)
                policy = policies[0]
                
                # Get effectiveness analysis from backend
                analysis = await self.backend_client.analyze_rate_limit_effectiveness(
                    policy_id=policy.get("id"),
                    analysis_period_hours=analysis_period_hours
                )
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "effectiveness_score": analysis.get("effectiveness_score", 0),
                        "metrics": analysis.get("metrics", {}),
                        "recommendations": analysis.get("recommendations", [])
                    },
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                }
                
            except Exception as e:
                logger.error(f"Error analyzing rate limit effectiveness: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": {
                        "code": "ANALYSIS_FAILED",
                        "message": str(e),
                        "details": {}
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()}
                }

    async def initialize(self) -> None:
        """Initialize server resources."""
        await super().initialize()
        logger.info("Optimization server initialized and ready")
    
    async def cleanup(self) -> None:
        """Cleanup server resources."""
        await super().cleanup()
        
        # Close backend client connection
        await self.backend_client.close()
        logger.info("Optimization server disconnected from backend")


def main():
    """Main entry point for Optimization MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create server
    server = OptimizationMCPServer()
    
    # Run MCP server on port 8000 (matches Docker port mapping)
    # FastMCP's built-in server will handle both MCP and health endpoints
    server.run(transport="streamable-http", port=8000)


if __name__ == "__main__":
    main()

# Made with Bob
