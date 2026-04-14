"""Prediction MCP Server for API Intelligence Plane.

This MCP server provides read-only access to scheduler-generated predictions and
their AI enrichment metadata. It acts as a thin wrapper around the backend REST
API, exposing tools that AI agents can use to inspect predictions, retrieve
per-prediction explanations, and review prediction accuracy statistics.

Port: 8006
Transport: Streamable HTTP
"""

import logging
import os
import sys
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.backend_client import BackendClient
from common.health import HealthChecker
from common.mcp_base import BaseMCPServer

logger = logging.getLogger(__name__)


class PredictionMCPServer(BaseMCPServer):
    """MCP Server for prediction operations.

    Provides tools for:
    - Listing scheduler-generated predictions with filters
    - Retrieving detailed prediction records
    - Getting AI-generated prediction explanations
    - Reviewing prediction accuracy statistics

    This server acts as a thin wrapper around the backend REST API,
    delegating all business logic to the backend services. Prediction
    generation is scheduler-driven and is intentionally not exposed as
    an MCP tool.
    """

    def __init__(self):
        """Initialize Prediction MCP server."""
        super().__init__(name="prediction-server", version="1.0.0")

        self.backend_client = BackendClient()
        self.health_checker = HealthChecker(self.name, self.version)

        self._register_tools()

        logger.info("Prediction MCP server initialized (using backend API)")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""

        @self.tool(description="Check Prediction server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.

            Returns:
                dict: Health status including backend connectivity
            """
            try:
                # Test backend connectivity by making a simple request to gateways endpoint
                response = await self.backend_client.client.get("/gateways", params={"page": 1, "page_size": 1})
                response.raise_for_status()
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

        @self.tool(description="Get Prediction server information")
        def server_info() -> dict[str, Any]:
            """Get server information.

            Returns:
                dict: Server metadata and capabilities
            """
            info = self.get_server_info()
            info.update(
                {
                    "port": 8006,
                    "transport": "streamable-http",
                    "architecture": "thin_wrapper",
                    "backend_url": self.backend_client.base_url,
                    "capabilities": [
                        "prediction_listing",
                        "prediction_details",
                        "prediction_explanations",
                        "prediction_accuracy_statistics",
                    ],
                    "prediction_generation_mode": "scheduler_driven_read_only",
                }
            )
            return info

        @self.tool(description="List failure predictions with optional filters")
        async def list_predictions(
            gateway_id: str,
            api_id: Optional[str] = None,
            severity: Optional[str] = None,
            status: Optional[str] = None,
            page: int = 1,
            page_size: int = 20,
        ) -> dict[str, Any]:
            """List predictions with filters for a specific gateway.

            Args:
                gateway_id: Gateway UUID (required)
                api_id: Filter by API UUID
                severity: Filter by severity (critical, high, medium, low)
                status: Filter by status (active, resolved, false_positive, expired)
                page: Page number (1-indexed)
                page_size: Items per page (1-100)

            Returns:
                dict: Predictions list with pagination
            """
            start_time = datetime.utcnow()

            try:
                # Validate gateway_id
                try:
                    UUID(gateway_id)
                except ValueError:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "Invalid gateway ID format",
                            "details": {"gateway_id": gateway_id},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }
                
                if api_id:
                    try:
                        UUID(api_id)
                    except ValueError:
                        return {
                            "success": False,
                            "error": {
                                "code": "INVALID_INPUT",
                                "message": "Invalid API ID format",
                                "details": {"api_id": api_id},
                            },
                            "metadata": {"timestamp": start_time.isoformat()},
                        }

                valid_severities = {"critical", "high", "medium", "low"}
                if severity and severity not in valid_severities:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "severity must be one of critical, high, medium, low",
                            "details": {"severity": severity},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }

                valid_statuses = {"active", "resolved", "false_positive", "expired"}
                if status and status not in valid_statuses:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": (
                                "status must be one of active, resolved, false_positive, expired"
                            ),
                            "details": {"status": status},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }

                if page < 1:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "page must be greater than or equal to 1",
                            "details": {"page": page},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }

                if page_size < 1 or page_size > 100:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "page_size must be between 1 and 100",
                            "details": {"page_size": page_size},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }

                response = await self.backend_client.list_predictions(
                    gateway_id=gateway_id,
                    api_id=api_id,
                    severity=severity,
                    status=status,
                    page=page,
                    page_size=page_size,
                )

                execution_time = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                return {
                    "success": True,
                    "data": response,
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

            except Exception as e:
                logger.error(f"Error listing predictions: {e}", exc_info=True)
                return {
                    "success": False,
                    "error": {
                        "code": "PREDICTION_LIST_FAILED",
                        "message": str(e),
                        "details": {},
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()},
                }

        @self.tool(description="Get detailed information for a specific prediction")
        async def get_prediction(gateway_id: str, prediction_id: str) -> dict[str, Any]:
            """Get prediction details.

            Args:
                gateway_id: Gateway UUID
                prediction_id: Prediction UUID

            Returns:
                dict: Complete prediction details with contributing factors
            """
            start_time = datetime.utcnow()

            try:
                try:
                    UUID(gateway_id)
                    UUID(prediction_id)
                except ValueError as e:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": f"Invalid UUID format: {e}",
                            "details": {"gateway_id": gateway_id, "prediction_id": prediction_id},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }

                response = await self.backend_client.get_prediction(gateway_id, prediction_id)

                execution_time = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                return {
                    "success": True,
                    "data": response,
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

            except Exception as e:
                logger.error(
                    f"Error getting prediction {prediction_id}: {e}",
                    exc_info=True,
                )
                return {
                    "success": False,
                    "error": {
                        "code": "PREDICTION_GET_FAILED",
                        "message": str(e),
                        "details": {"prediction_id": prediction_id},
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()},
                }

        @self.tool(description="Get AI-generated explanation for a prediction")
        async def get_prediction_explanation(gateway_id: str, prediction_id: str) -> dict[str, Any]:
            """Get AI explanation for prediction.

            Args:
                gateway_id: Gateway UUID
                prediction_id: Prediction UUID

            Returns:
                dict: Natural language explanation with insights
            """
            start_time = datetime.utcnow()

            try:
                try:
                    UUID(gateway_id)
                    UUID(prediction_id)
                except ValueError as e:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": f"Invalid UUID format: {e}",
                            "details": {"gateway_id": gateway_id, "prediction_id": prediction_id},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }

                response = await self.backend_client.get_prediction_explanation(
                    gateway_id, prediction_id
                )

                execution_time = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                return {
                    "success": True,
                    "data": response,
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

            except Exception as e:
                logger.error(
                    f"Error getting explanation for prediction {prediction_id}: {e}",
                    exc_info=True,
                )
                return {
                    "success": False,
                    "error": {
                        "code": "PREDICTION_EXPLANATION_FAILED",
                        "message": str(e),
                        "details": {"prediction_id": prediction_id},
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()},
                }

        @self.tool(description="Get prediction accuracy statistics")
        async def get_accuracy_stats(
            gateway_id: str,
            api_id: Optional[str] = None,
            days: int = 30,
        ) -> dict[str, Any]:
            """Get accuracy statistics for a gateway.

            Args:
                gateway_id: Gateway UUID (required)
                api_id: Optional API UUID filter
                days: Number of days to analyze (1-90)

            Returns:
                dict: Accuracy metrics and trends
            """
            start_time = datetime.utcnow()

            try:
                # Validate gateway_id
                try:
                    UUID(gateway_id)
                except ValueError:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "Invalid gateway ID format",
                            "details": {"gateway_id": gateway_id},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }
                
                if api_id:
                    try:
                        UUID(api_id)
                    except ValueError:
                        return {
                            "success": False,
                            "error": {
                                "code": "INVALID_INPUT",
                                "message": "Invalid API ID format",
                                "details": {"api_id": api_id},
                            },
                            "metadata": {"timestamp": start_time.isoformat()},
                        }

                if days < 1 or days > 90:
                    return {
                        "success": False,
                        "error": {
                            "code": "INVALID_INPUT",
                            "message": "days must be between 1 and 90",
                            "details": {"days": days},
                        },
                        "metadata": {"timestamp": start_time.isoformat()},
                    }

                response = await self.backend_client.get_prediction_accuracy_stats(
                    gateway_id=gateway_id,
                    api_id=api_id,
                    days=days,
                )

                execution_time = int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                )

                return {
                    "success": True,
                    "data": response,
                    "metadata": {
                        "execution_time_ms": execution_time,
                        "timestamp": datetime.utcnow().isoformat(),
                    },
                }

            except Exception as e:
                logger.error("Error getting prediction accuracy statistics: %s", e, exc_info=True)
                return {
                    "success": False,
                    "error": {
                        "code": "PREDICTION_ACCURACY_STATS_FAILED",
                        "message": str(e),
                        "details": {},
                    },
                    "metadata": {"timestamp": datetime.utcnow().isoformat()},
                }

    async def cleanup(self) -> None:
        """Cleanup server resources."""
        await self.backend_client.close()
        await super().cleanup()


def main() -> None:
    """Run the Prediction MCP server."""
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    server = PredictionMCPServer()
    server.run(transport="streamable-http", port=8000, host="0.0.0.0")


if __name__ == "__main__":
    main()

# Made with Bob
