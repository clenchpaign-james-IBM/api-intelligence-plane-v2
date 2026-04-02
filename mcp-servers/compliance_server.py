"""Compliance MCP Server for API Intelligence Plane.

This MCP server provides tools for compliance monitoring, violation management,
and audit reporting. It acts as a thin wrapper around the backend REST API,
exposing tools that AI agents can use to interact with compliance functionality.

Focuses on scheduled audit preparation and regulatory reporting (distinct from
immediate security threat response).

Compliance Standards Supported:
- GDPR (General Data Protection Regulation)
- HIPAA (Health Insurance Portability and Accountability Act)
- SOC2 (Service Organization Control 2)
- PCI-DSS (Payment Card Industry Data Security Standard)
- ISO 27001 (Information Security Management)

Port: 8004
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


class ComplianceMCPServer(BaseMCPServer):
    """MCP Server for Compliance operations.
    
    Provides tools for:
    - Scanning APIs for compliance violations across 5 regulatory standards
    - Generating comprehensive audit reports with evidence
    - Getting compliance posture metrics and scores
    
    This server acts as a thin wrapper around the backend REST API,
    delegating all business logic to the backend ComplianceService.
    All compliance analysis uses AI-driven detection with hybrid approach.
    """

    def __init__(self):
        """Initialize Compliance MCP server."""
        super().__init__(name="compliance-server", version="1.0.0")
        
        # Initialize backend client
        self.backend_client = BackendClient()
        
        # Initialize health checker
        self.health_checker = HealthChecker(self.name, self.version)
        
        # Register tools
        self._register_tools()
        
        logger.info("Compliance MCP server initialized (using backend API)")

    def _register_tools(self) -> None:
        """Register all MCP tools for this server."""
        
        # Health check tool
        @self.tool(description="Check Compliance server health and status")
        async def health() -> dict[str, Any]:
            """Check server health.
            
            Returns:
                dict: Health status including backend connectivity
            """
            try:
                # Test backend connectivity using compliance posture endpoint
                response = await self.backend_client._request("GET", "/compliance/posture")
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
        @self.tool(description="Get Compliance server information")
        def server_info() -> dict[str, Any]:
            """Get server information.
            
            Returns:
                dict: Server metadata and capabilities
            """
            info = self.get_server_info()
            info.update({
                "port": 8005,
                "transport": "streamable-http",
                "architecture": "thin_wrapper",
                "backend_url": self.backend_client.base_url,
                "capabilities": [
                    "compliance_scanning",
                    "violation_management",
                    "audit_reporting",
                    "compliance_posture",
                    "ai_driven_analysis",
                ],
                "compliance_standards": [
                    "GDPR",
                    "HIPAA",
                    "SOC2",
                    "PCI-DSS",
                    "ISO_27001",
                ],
                "focus": "scheduled_audit_preparation",
                "scan_frequency": "24_hours",
            })
            return info
        
        # T128l: scan_api_compliance tool
        @self.tool(description="Scan an API for compliance violations across regulatory standards")
        async def scan_api_compliance(
            api_id: str,
            standards: Optional[list[str]] = None,
        ) -> dict[str, Any]:
            """Scan an API for compliance violations.
            
            Performs comprehensive compliance analysis using AI-driven detection:
            - Gateway-level compliance checks (authentication, TLS, logging, etc.)
            - Violation detection mapped to specific regulatory requirements
            - Evidence collection for audit purposes
            - Audit trail generation
            
            Compliance checks include:
            - GDPR: Security of processing, data protection, audit logging
            - HIPAA: Transmission security, access controls, audit controls
            - SOC2: Logical access, system monitoring, change management
            - PCI-DSS: Encryption in transit, access control, logging
            - ISO 27001: Access control, cryptography, operations security
            
            Args:
                api_id: UUID of the API to scan
                standards: Optional list of specific standards to check
                          (default: all 5 standards)
                          Valid values: ["GDPR", "HIPAA", "SOC2", "PCI_DSS", "ISO_27001"]
            
            Returns:
                dict: Scan results including:
                    - scan_id: Unique scan identifier
                    - api_id: API identifier
                    - api_name: API name
                    - scan_completed_at: Scan completion timestamp
                    - violations_found: Number of violations detected
                    - severity_breakdown: Violations by severity (critical/high/medium/low)
                    - standard_breakdown: Violations by compliance standard
                    - violations: List of detailed violation objects
                    - audit_evidence: Collected evidence for auditors
            
            Example:
                >>> result = await scan_api_compliance(
                ...     api_id="550e8400-e29b-41d4-a716-446655440000",
                ...     standards=["GDPR", "HIPAA"]
                ... )
                >>> print(f"Found {result['violations_found']} violations")
            """
            try:
                logger.info(f"Scanning API {api_id} for compliance violations")
                
                # Prepare request payload
                payload: dict[str, Any] = {"api_id": api_id}
                if standards:
                    payload["standards"] = standards
                
                # Call backend API
                response = await self.backend_client._request(
                    "POST",
                    "/compliance/scan",
                    json=payload
                )
                
                logger.info(
                    f"Compliance scan complete: {response.get('violations_found', 0)} violations found"
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Compliance scan failed: {str(e)}")
                return {
                    "error": str(e),
                    "api_id": api_id,
                    "scan_completed_at": datetime.utcnow().isoformat(),
                    "violations_found": 0,
                }
        
        # T128m: generate_audit_report tool
        @self.tool(description="Generate comprehensive audit report with evidence and recommendations")
        async def generate_audit_report(
            api_id: Optional[str] = None,
            standard: Optional[str] = None,
            start_date: Optional[str] = None,
            end_date: Optional[str] = None,
        ) -> dict[str, Any]:
            """Generate comprehensive audit report.
            
            Creates a detailed audit report suitable for external auditors with:
            - AI-generated executive summary
            - Compliance posture analysis
            - Violations breakdown by standard and severity
            - Remediation status tracking
            - Violations needing audit attention
            - Collected audit evidence
            - Actionable recommendations
            
            Args:
                api_id: Optional API filter (UUID string)
                standard: Optional compliance standard filter
                         Valid values: ["GDPR", "HIPAA", "SOC2", "PCI_DSS", "ISO_27001"]
                start_date: Report start date (ISO format, default: 90 days ago)
                end_date: Report end date (ISO format, default: now)
            
            Returns:
                dict: Comprehensive audit report including:
                    - report_id: Unique report identifier
                    - generated_at: Report generation timestamp
                    - report_period: Time period covered (start/end dates)
                    - executive_summary: AI-generated summary for executives
                    - compliance_posture: Overall compliance metrics
                    - violations_by_standard: Breakdown by regulatory standard
                    - violations_by_severity: Breakdown by severity level
                    - remediation_status: Status of remediation efforts
                    - violations_needing_audit: Items requiring audit attention
                    - audit_evidence: Collected evidence for auditors
                    - recommendations: Actionable recommendations
            
            Example:
                >>> report = await generate_audit_report(
                ...     standard="GDPR",
                ...     start_date="2026-01-01T00:00:00Z",
                ...     end_date="2026-03-31T23:59:59Z"
                ... )
                >>> print(report['executive_summary'])
            """
            try:
                logger.info("Generating audit report")
                
                # Prepare request payload
                payload = {}
                if api_id:
                    payload["api_id"] = api_id
                if standard:
                    payload["standard"] = standard
                if start_date:
                    payload["start_date"] = start_date
                if end_date:
                    payload["end_date"] = end_date
                
                # Call backend API
                response = await self.backend_client._request(
                    "POST",
                    "/compliance/reports/audit",
                    json=payload
                )
                
                logger.info(f"Audit report generated: {response.get('report_id')}")
                
                return response
                
            except Exception as e:
                logger.error(f"Audit report generation failed: {str(e)}")
                return {
                    "error": str(e),
                    "generated_at": datetime.utcnow().isoformat(),
                }
        
        # T128n: get_compliance_posture tool
        @self.tool(description="Get overall compliance posture metrics and scores")
        async def get_compliance_posture(
            api_id: Optional[str] = None,
            standard: Optional[str] = None,
        ) -> dict[str, Any]:
            """Get compliance posture metrics.
            
            Provides real-time compliance health metrics including:
            - Total violations count
            - Breakdown by severity, status, and standard
            - Remediation rate percentage
            - Compliance score (0-100, higher is better)
            - Last scan timestamp
            - Next recommended audit date
            
            Args:
                api_id: Optional API filter (UUID string)
                standard: Optional compliance standard filter
                         Valid values: ["GDPR", "HIPAA", "SOC2", "PCI_DSS", "ISO_27001"]
            
            Returns:
                dict: Compliance posture metrics including:
                    - total_violations: Total number of violations
                    - by_severity: Breakdown by severity level
                    - by_status: Breakdown by status (open/in_progress/remediated)
                    - by_standard: Breakdown by compliance standard
                    - remediation_rate: Percentage of violations remediated
                    - compliance_score: Overall score (0-100, higher is better)
                    - last_scan: Last scan timestamp
                    - next_audit_date: Next recommended audit date
            
            Example:
                >>> posture = await get_compliance_posture(standard="HIPAA")
                >>> print(f"Compliance score: {posture['compliance_score']}")
                >>> print(f"Remediation rate: {posture['remediation_rate']}%")
            """
            try:
                logger.info("Getting compliance posture")
                
                # Prepare query parameters
                params = {}
                if api_id:
                    params["api_id"] = api_id
                if standard:
                    params["standard"] = standard
                
                # Call backend API
                response = await self.backend_client._request(
                    "GET",
                    "/compliance/posture",
                    params=params
                )
                
                logger.info(
                    f"Compliance posture retrieved: score={response.get('compliance_score')}"
                )
                
                return response
                
            except Exception as e:
                logger.error(f"Failed to get compliance posture: {str(e)}")
                return {
                    "error": str(e),
                    "total_violations": 0,
                    "compliance_score": 0.0,
                }


def main():
    """Run the Compliance MCP server."""
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    
    # Create server
    server = ComplianceMCPServer()
    
    # Run MCP server on port 8004 (Compliance server port)
    # FastMCP's built-in server will handle both MCP and health endpoints
    server.run(transport="streamable-http", port=8000)


if __name__ == "__main__":
    main()

# Made with Bob
