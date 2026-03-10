"""Optimization MCP Server for API Intelligence Plane.

This MCP server provides tools for performance optimization, predictions, and
rate limiting for APIs. It exposes tools that AI agents can use to interact
with optimization functionality.

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

from common.health import HealthChecker, create_health_tool
from common.http_health import HTTPHealthServer
from common.mcp_base import BaseMCPServer
from common.opensearch import MCPOpenSearchClient

logger = logging.getLogger(__name__)


class OptimizationMCPServer(BaseMCPServer):
    """MCP Server for API Optimization operations.
    
    Provides tools for:
    - Generating failure predictions
    - Creating optimization recommendations
    - Managing rate limit policies
    - Analyzing rate limit effectiveness
    """

    def __init__(self):
        """Initialize Optimization MCP server."""
        super().__init__(name="optimization-server", version="1.0.0")
        
        # Initialize OpenSearch client
        self.opensearch = MCPOpenSearchClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        self.health_checker.set_opensearch_client(self.opensearch)
        
        # Register tools
        self._register_tools()
        
        logger.info("Optimization MCP server initialized")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        health_tool = create_health_tool(self.health_checker)
        
        @self.tool(description="Check Optimization server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.
            
            Returns:
                dict: Health status including OpenSearch connectivity
            """
            return await health_tool()
        
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
                
                # Build query for predictions
                query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"range": {"confidence": {"gte": min_confidence}}},
                                {"term": {"status": "active"}}
                            ]
                        }
                    },
                    "sort": [{"confidence": {"order": "desc"}}],
                    "size": 1000
                }
                
                # Add API filter if specified
                if api_id:
                    try:
                        UUID(api_id)  # Validate UUID format
                        query["query"]["bool"]["must"].append(
                            {"term": {"api_id": api_id}}
                        )
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
                
                # Query OpenSearch for predictions
                # Build complete query body
                query_body = query.copy()
                
                result = await self.opensearch.search(
                    index="api-predictions",
                    query=query_body.get("query", {}),
                    size=query_body.get("size", 1000)
                )
                
                predictions = []
                for hit in result.get("hits", {}).get("hits", []):
                    source = hit["_source"]
                    predictions.append({
                        "id": hit["_id"],
                        "api_id": source.get("api_id"),
                        "api_name": source.get("api_name"),
                        "prediction_type": source.get("prediction_type"),
                        "severity": source.get("severity"),
                        "confidence": source.get("confidence"),
                        "predicted_time": source.get("predicted_time"),
                        "description": source.get("description"),
                        "recommended_actions": source.get("recommended_actions", []),
                        "contributing_factors": source.get("contributing_factors", []),
                        "created_at": source.get("created_at")
                    })
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "predictions_generated": len(predictions),
                        "predictions": predictions,
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
                
                # Query for recommendations
                query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"api_id": api_id}},
                                {"range": {"expected_improvement_percentage": {"gte": min_impact_percentage}}}
                            ]
                        }
                    },
                    "sort": [{"expected_improvement_percentage": {"order": "desc"}}],
                    "size": 100
                }
                
                # Add focus area filter if specified
                if focus_areas:
                    query["query"]["bool"]["must"].append(
                        {"terms": {"optimization_type": focus_areas}}
                    )
                
                # Build complete query body
                query_body = query.copy()
                
                result = await self.opensearch.search(
                    index="optimization-recommendations",
                    query=query_body.get("query", {}),
                    size=query_body.get("size", 100)
                )
                
                recommendations = []
                total_savings = 0.0
                
                for hit in result.get("hits", {}).get("hits", []):
                    source = hit["_source"]
                    recommendations.append({
                        "id": hit["_id"],
                        "optimization_type": source.get("optimization_type"),
                        "title": source.get("title"),
                        "description": source.get("description"),
                        "expected_improvement_percentage": source.get("expected_improvement_percentage"),
                        "implementation_effort": source.get("implementation_effort"),
                        "estimated_savings_usd_monthly": source.get("estimated_savings_usd_monthly", 0),
                        "recommended_actions": source.get("recommended_actions", []),
                        "created_at": source.get("created_at")
                    })
                    total_savings += source.get("estimated_savings_usd_monthly", 0)
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "recommendations_count": len(recommendations),
                        "recommendations": recommendations,
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
                
                # Create policy document
                policy_id = f"{api_id}-{policy_type}-{int(datetime.utcnow().timestamp())}"
                policy_doc = {
                    "api_id": api_id,
                    "policy_type": policy_type,
                    "limit_thresholds": limit_thresholds,
                    "enforcement_action": enforcement_action,
                    "status": "active",
                    "created_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat()
                }
                
                # Index policy using raw client
                client = await self.opensearch.connect()
                await client.index(
                    index="rate-limit-policies",
                    id=policy_id,
                    body=policy_doc
                )
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "policy_id": policy_id,
                        "status": "created",
                        "policy": policy_doc
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
                # Calculate time range
                end_time = datetime.utcnow()
                start_analysis_time = end_time - timedelta(hours=analysis_period_hours)
                
                # Query metrics for analysis
                query = {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"api_id": api_id}},
                                {"range": {"timestamp": {
                                    "gte": start_analysis_time.isoformat(),
                                    "lte": end_time.isoformat()
                                }}}
                            ]
                        }
                    },
                    "aggs": {
                        "throttled": {"sum": {"field": "requests_throttled"}},
                        "rejected": {"sum": {"field": "requests_rejected"}},
                        "total": {"sum": {"field": "request_count"}}
                    },
                    "size": 0
                }
                
                # Build complete query body
                query_body = query.copy()
                
                result = await self.opensearch.search(
                    index="api-metrics-*",
                    query=query_body.get("query", {}),
                    size=query_body.get("size", 0)
                )
                
                aggs = result.get("aggregations", {})
                throttled = int(aggs.get("throttled", {}).get("value", 0))
                rejected = int(aggs.get("rejected", {}).get("value", 0))
                total = int(aggs.get("total", {}).get("value", 1))
                
                # Calculate effectiveness score
                effectiveness_score = 1.0 - ((throttled + rejected) / max(total, 1))
                effectiveness_score = max(0.0, min(1.0, effectiveness_score))
                
                # Generate recommendations
                recommendations = []
                if effectiveness_score < 0.7:
                    recommendations.append("Consider adjusting rate limits - too restrictive")
                if throttled > rejected * 2:
                    recommendations.append("Throttling is working well, consider reducing rejections")
                if rejected > throttled * 2:
                    recommendations.append("Too many rejections, consider throttling instead")
                
                execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
                
                return {
                    "success": True,
                    "data": {
                        "effectiveness_score": effectiveness_score,
                        "metrics": {
                            "requests_throttled": throttled,
                            "requests_rejected": rejected,
                            "legitimate_users_affected": int(throttled * 0.1),  # Estimate
                            "abuse_prevented": int(rejected * 0.9)  # Estimate
                        },
                        "recommendations": recommendations
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


def main():
    """Main entry point for Optimization MCP server."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Create server
    server = OptimizationMCPServer()
    
    # Start HTTP health server in background thread on port 8000
    health_server = HTTPHealthServer(server.health_checker, port=8000)
    health_server.start()
    
    try:
        # Run MCP server on port 8004 (this will block)
        server.run(transport="streamable-http", port=8004)
    finally:
        # Cleanup
        health_server.stop()


if __name__ == "__main__":
    main()

# Made with Bob
