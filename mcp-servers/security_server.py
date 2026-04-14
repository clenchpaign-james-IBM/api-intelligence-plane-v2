"""Security MCP Server for API Intelligence Plane.

This MCP server provides tools for security scanning, vulnerability management,
compliance detection, and automated remediation. It acts as a thin wrapper around
the backend REST API, exposing tools that AI agents can use to interact with
security functionality.

All security analysis uses a HYBRID approach:
- Rule-based checks for deterministic security factors
- AI-enhanced analysis for context-aware severity assessment
- Multi-source data analysis (API metadata, metrics, traffic patterns)
- Compliance detection (GDPR, HIPAA, SOC2, PCI-DSS)

Port: 8003
Transport: Streamable HTTP
"""

import asyncio
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


class SecurityMCPServer(BaseMCPServer):
    """MCP Server for Security operations.
    
    Provides tools for:
    - Scanning APIs for security vulnerabilities using hybrid analysis (rule-based + AI)
    - Detecting compliance violations (GDPR, HIPAA, SOC2, PCI-DSS)
    - Remediating vulnerabilities automatically via Gateway policies
    - Verifying remediation effectiveness
    - Getting security posture metrics and risk scores
    
    This server acts as a thin wrapper around the backend REST API,
    delegating all business logic to the backend services. All security
    analysis uses a hybrid approach combining deterministic rule-based
    checks with AI-enhanced context-aware assessment.
    """

    def __init__(self):
        """Initialize Security MCP server."""
        super().__init__(name="security-server", version="1.0.0")
        
        # Initialize backend client
        self.backend_client = BackendClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        
        # Register tools
        self._register_tools()
        
        logger.info("Security MCP server initialized (using backend API)")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        @self.tool(description="Check Security server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.
            
            Returns:
                dict: Health status including backend connectivity
            """
            try:
                # Test backend connectivity using security posture endpoint
                response = await self.backend_client._request("GET", "/security/posture")
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
        @self.tool(description="Get Security server information")
        def server_info() -> dict[str, Any]:
            """Get server information.
            
            Returns:
                dict: Server metadata and capabilities
            """
            info = self.get_server_info()
            info.update({
                "port": 8003,
                "transport": "streamable-http",
                "architecture": "thin_wrapper",
                "backend_url": self.backend_client.base_url,
                "capabilities": [
                    "hybrid_security_scanning",
                    "vulnerability_management",
                    "automated_remediation",
                    "compliance_detection",
                    "security_posture",
                    "metrics_analysis",
                ],
                "analysis_approach": "hybrid",
                "compliance_standards": ["GDPR", "HIPAA", "SOC2", "PCI-DSS"],
            })
            return info
        
        # T119: scan_api_security tool
        @self.tool(description="Scan an API for security vulnerabilities and policy coverage issues using hybrid analysis")
        async def scan_api_security(
            api_id: str,
        ) -> dict[str, Any]:
            """Scan an API for security vulnerabilities.
            
            Performs comprehensive security analysis using HYBRID approach:
            - Rule-based checks for deterministic security factors
            - AI-enhanced analysis for context-aware severity assessment
            - Multi-source data analysis (API metadata, metrics, traffic patterns)
            - Compliance detection (GDPR, HIPAA, SOC2, PCI-DSS)
            
            Security checks include:
            - Authentication policy coverage
            - Authorization policy coverage
            - Rate limiting configuration
            - TLS/SSL configuration
            - CORS policy review
            - Input validation checks
            - Security header analysis
            
            Args:
                api_id: UUID of the API to scan
            
            Returns:
                dict: Scan results including:
                    - scan_id: Unique scan identifier
                    - api_id: API identifier
                    - api_name: API name
                    - scan_completed_at: Scan completion timestamp
                    - vulnerabilities_found: Number of vulnerabilities
                    - severity_breakdown: Vulnerabilities by severity
                    - vulnerabilities: List of vulnerability details
                    - compliance_issues: List of compliance violations
                    - remediation_plan: Automated remediation plan
                    - metrics_analyzed: Number of metrics analyzed for context
            
            Example:
                >>> result = await scan_api_security(
                ...     api_id="550e8400-e29b-41d4-a716-446655440000"
                ... )
                >>> print(f"Found {result['vulnerabilities_found']} vulnerabilities")
                >>> print(f"Compliance issues: {len(result['compliance_issues'])}")
            """
            try:
                logger.info(f"Scanning API {api_id} for security vulnerabilities (hybrid analysis)")
                
                # Call backend API (always uses hybrid approach)
                response = await self.backend_client._request(
                    "POST",
                    "/security/scan",
                    json={"api_id": api_id},
                )
                
                logger.info(
                    f"Scan completed: {response['vulnerabilities_found']} vulnerabilities found"
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Security scan failed: {e}")
                return {
                    "error": str(e),
                    "api_id": api_id,
                    "status": "failed",
                }
        
        # T120: remediate_vulnerability tool
        @self.tool(description="Automatically remediate a security vulnerability")
        async def remediate_vulnerability(
            vulnerability_id: str,
            remediation_strategy: Optional[str] = None,
        ) -> dict[str, Any]:
            """Trigger automated remediation for a vulnerability.
            
            Applies appropriate security policies to the API Gateway to remediate
            the identified vulnerability. Supports various remediation strategies:
            - Authentication: Add OAuth2/JWT authentication
            - Authorization: Add RBAC/ABAC policies
            - Rate limiting: Configure rate limits
            - TLS: Enforce TLS 1.3
            - CORS: Configure CORS policies
            - Headers: Add security headers
            - Validation: Add input validation
            
            Args:
                vulnerability_id: UUID of the vulnerability to remediate
                remediation_strategy: Optional specific strategy to use
            
            Returns:
                dict: Remediation result including:
                    - vulnerability_id: Vulnerability identifier
                    - status: Remediation status (success/failed/pending)
                    - remediation_result: Details of applied remediation
                    - verification_result: Verification of effectiveness
                    - message: Status message
            
            Example:
                >>> result = await remediate_vulnerability(
                ...     vulnerability_id="660e8400-e29b-41d4-a716-446655440000"
                ... )
                >>> print(f"Remediation status: {result['status']}")
            """
            try:
                logger.info(f"Remediating vulnerability {vulnerability_id}")
                
                # Call backend API
                request_body = {}
                if remediation_strategy:
                    request_body["remediation_strategy"] = remediation_strategy
                
                response = await self.backend_client._request(
                    "POST",
                    f"/security/vulnerabilities/{vulnerability_id}/remediate",
                    json=request_body if request_body else None,
                )
                
                logger.info(f"Remediation completed: {response['status']}")
                
                return response
                
            except Exception as e:
                logger.error(f"Remediation failed: {e}")
                return {
                    "error": str(e),
                    "vulnerability_id": vulnerability_id,
                    "status": "failed",
                }
        
        # T121: get_security_posture tool
        @self.tool(description="Get overall security posture metrics and risk score")
        async def get_security_posture(
            api_id: Optional[str] = None,
        ) -> dict[str, Any]:
            """Get security posture metrics.
            
            Provides comprehensive security metrics including:
            - Total vulnerabilities by severity
            - Vulnerabilities by status (open/remediated/in_progress)
            - Vulnerabilities by type
            - Remediation rate percentage
            - Overall risk score (0-100)
            - Risk level (low/medium/high/critical)
            - Average remediation time
            
            Args:
                api_id: Optional UUID to filter by specific API
            
            Returns:
                dict: Security posture metrics including:
                    - total_vulnerabilities: Total count
                    - by_severity: Breakdown by severity level
                    - by_status: Breakdown by status
                    - by_type: Breakdown by vulnerability type
                    - remediation_rate: Percentage of remediated vulnerabilities
                    - risk_score: Overall risk score (0-100)
                    - risk_level: Risk level classification
                    - avg_remediation_time_ms: Average time to remediate
            
            Example:
                >>> posture = await get_security_posture()
                >>> print(f"Risk score: {posture['risk_score']}")
                >>> print(f"Risk level: {posture['risk_level']}")
            """
            try:
                logger.info(f"Fetching security posture (api_id={api_id})")
                
                # Build query parameters
                params = {}
                if api_id:
                    params["api_id"] = api_id
                
                # Call backend API
                response = await self.backend_client._request(
                    "GET",
                    "/security/posture",
                    params=params,
                )
                
                logger.info(
                    f"Security posture: {response['total_vulnerabilities']} vulnerabilities, "
                    f"risk score {response['risk_score']}"
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Failed to fetch security posture: {e}")
                return {
                    "error": str(e),
                    "status": "failed",
                }
        
        # Additional helper tool: list vulnerabilities
        @self.tool(description="List vulnerabilities with optional filters")
        async def list_vulnerabilities(
            api_id: Optional[str] = None,
            status: Optional[str] = None,
            severity: Optional[str] = None,
            limit: int = 100,
        ) -> dict[str, Any]:
            """List vulnerabilities with optional filters.
            
            Args:
                api_id: Optional UUID to filter by API
                status: Optional status filter (open/remediated/in_progress/verified)
                severity: Optional severity filter (critical/high/medium/low)
                limit: Maximum number of results (default: 100)
            
            Returns:
                dict: List of vulnerabilities with metadata
            
            Example:
                >>> vulns = await list_vulnerabilities(
                ...     severity="critical",
                ...     status="open",
                ...     limit=10
                ... )
                >>> print(f"Found {len(vulns['vulnerabilities'])} critical open vulnerabilities")
            """
            try:
                logger.info(
                    f"Listing vulnerabilities (api_id={api_id}, status={status}, "
                    f"severity={severity}, limit={limit})"
                )
                
                # Build query parameters
                params = {"limit": limit}
                if api_id:
                    params["api_id"] = api_id
                if status:
                    params["status"] = status
                if severity:
                    params["severity"] = severity
                
                # Call backend API
                response = await self.backend_client._request(
                    "GET",
                    "/security/vulnerabilities",
                    params=params,
                )
                
                logger.info(f"Found {len(response)} vulnerabilities")
                
                return {
                    "vulnerabilities": response,
                    "count": len(response),
                    "filters": {
                        "api_id": api_id,
                        "status": status,
                        "severity": severity,
                        "limit": limit,
                    },
                }
                
            except Exception as e:
                logger.error(f"Failed to list vulnerabilities: {e}")
                return {
                    "error": str(e),
                    "vulnerabilities": [],
                    "count": 0,
                }
        
        # Additional helper tool: verify remediation
        @self.tool(description="Verify that a vulnerability remediation is effective")
        async def verify_remediation(
            vulnerability_id: str,
        ) -> dict[str, Any]:
            """Verify that remediation was successful.
            
            Re-scans the API to confirm that the vulnerability has been
            effectively remediated and is no longer present.
            
            Args:
                vulnerability_id: UUID of the vulnerability to verify
            
            Returns:
                dict: Verification result including:
                    - vulnerability_id: Vulnerability identifier
                    - verified: Whether remediation was successful
                    - verification_timestamp: When verification was performed
                    - details: Verification details
            
            Example:
                >>> result = await verify_remediation(
                ...     vulnerability_id="660e8400-e29b-41d4-a716-446655440000"
                ... )
                >>> print(f"Verified: {result['verified']}")
            """
            try:
                logger.info(f"Verifying remediation for vulnerability {vulnerability_id}")
                
                # Call backend API
                response = await self.backend_client._request(
                    "POST",
                    f"/security/vulnerabilities/{vulnerability_id}/verify"
                )
                
                logger.info(f"Verification completed: {response.get('verified', False)}")
                
                return response
                
            except Exception as e:
                logger.error(f"Verification failed: {e}")
                return {
                    "error": str(e),
                    "vulnerability_id": vulnerability_id,
                    "verified": False,
                }


def main():
    """Run the Security MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create server
    server = SecurityMCPServer()
    
    # Run MCP server on port 8004 (Security server port)
    # FastMCP's built-in server will handle both MCP and health endpoints
    server.run(transport="streamable-http", port=8000)


if __name__ == "__main__":
    main()

# Made with Bob