"""Compliance Service for API Intelligence Plane.

Orchestrates compliance monitoring, violation management, and audit reporting.
Focuses on scheduled audit preparation and regulatory reporting (distinct from immediate security threat response).
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.compliance_agent import ComplianceAgent
from app.config import Settings
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.models.base.api import API, PolicyActionType
from app.models.compliance import (
    ComplianceViolation,
    ComplianceStandard,
    ComplianceStatus,
    ComplianceSeverity,
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class ComplianceService:
    """Service for compliance monitoring and audit reporting.
    
    This service provides:
    1. AI-driven compliance detection for 5 standards (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
    2. Violation tracking and management
    3. Compliance posture reporting
    4. Audit report generation with evidence collection
    5. Scheduled compliance scanning (24-hour cycle)
    
    Key Distinction from SecurityService:
    - SecurityService: Immediate threat response, vulnerability remediation
    - ComplianceService: Scheduled audit preparation, regulatory reporting
    """

    def __init__(
        self,
        settings: Settings,
        api_repository: Optional[APIRepository] = None,
        compliance_repository: Optional[ComplianceRepository] = None,
        llm_service: Optional[LLMService] = None,
        compliance_agent: Optional[ComplianceAgent] = None,
        metrics_repository: Optional[Any] = None,
        gateway_repository: Optional[GatewayRepository] = None,
    ):
        """Initialize compliance service.

        Args:
            settings: Application settings
            api_repository: API repository instance
            compliance_repository: Compliance repository instance
            llm_service: LLM service instance
            compliance_agent: Compliance agent instance
            metrics_repository: Metrics repository instance
            gateway_repository: Gateway repository instance
        """
        self.settings = settings
        self.api_repository = api_repository or APIRepository()
        self.compliance_repository = compliance_repository or ComplianceRepository()
        self.llm_service = llm_service or LLMService(settings)
        
        # Import here to avoid circular dependency
        from app.db.repositories.metrics_repository import MetricsRepository
        
        self.metrics_repository = metrics_repository or MetricsRepository()
        self.gateway_repository = gateway_repository or GatewayRepository()
        
        self.compliance_agent = compliance_agent or ComplianceAgent(
            self.llm_service,
            self.metrics_repository
        )

    async def scan_api_compliance(
        self,
        gateway_id: UUID,
        api_id: UUID,
        standards: Optional[List[ComplianceStandard]] = None,
    ) -> Dict[str, Any]:
        """Scan API for compliance violations using AI-driven analysis.

        Args:
            gateway_id: Gateway UUID (primary scope dimension)
            api_id: API to scan (secondary scope dimension)
            standards: Optional list of specific standards to check (default: all 5)

        Returns:
            Scan results with violations, evidence, and audit trail
        """
        try:
            logger.info(f"Starting compliance scan for API {api_id} in gateway {gateway_id}")

            # Get API details
            api = self.api_repository.get(str(api_id))
            if not api:
                raise ValueError(f"API not found: {api_id}")
            
            # Verify API belongs to gateway
            if api.gateway_id != gateway_id:
                raise ValueError(f"API {api_id} does not belong to gateway {gateway_id}")

            # Perform AI-driven compliance analysis
            # Note: ComplianceAgent.analyze_api_compliance only takes 'api' parameter
            # It always checks all 5 standards (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
            analysis_result = await self.compliance_agent.analyze_api_compliance(api=api)
            
            # Filter violations by requested standards if specified
            if standards:
                filtered_violations = [
                    v for v in analysis_result.get("violations", [])
                    if v.get("compliance_standard") in [s.value for s in standards]
                ]
                analysis_result["violations"] = filtered_violations

            # Store violations
            stored_violations = []
            for violation_data in analysis_result.get("violations", []):
                # Convert dict to ComplianceViolation if needed
                if isinstance(violation_data, dict):
                    violation = ComplianceViolation(**violation_data)
                else:
                    violation = violation_data

                # Store in database
                self.compliance_repository.create(violation)
                stored_violations.append(violation)

            logger.info(
                f"Compliance scan complete. Found {len(stored_violations)} violations"
            )

            return {
                "scan_id": str(UUID(int=0)),  # Generate proper scan ID
                "gateway_id": str(gateway_id),
                "api_id": str(api_id),
                "api_name": api.name,
                "scan_completed_at": datetime.utcnow().isoformat(),
                "violations_found": len(stored_violations),
                "severity_breakdown": self._calculate_severity_breakdown(
                    stored_violations
                ),
                "standard_breakdown": self._calculate_standard_breakdown(
                    stored_violations
                ),
                "violations": [v.dict() for v in stored_violations],
                "audit_evidence": analysis_result.get("audit_evidence", []),
                "metrics_analyzed": analysis_result.get("metrics_analyzed", 0),
            }

        except Exception as e:
            logger.error(f"Compliance scan failed for API {api_id}: {str(e)}")
            raise

    async def scan_gateway_apis(
        self,
        gateway_id: UUID,
        standards: Optional[List[ComplianceStandard]] = None,
    ) -> Dict[str, Any]:
        """Scan all APIs within a specific gateway for compliance violations.

        Args:
            gateway_id: Gateway UUID (primary scope dimension)
            standards: Optional list of specific standards to check

        Returns:
            Aggregated scan results for the gateway
        """
        try:
            logger.info(f"Starting compliance scan for all APIs in gateway {gateway_id}")

            # Get all APIs for this gateway
            apis, _ = self.api_repository.find_by_gateway(gateway_id, size=1000)
            
            scan_results = []
            total_violations = 0

            for api in apis:
                try:
                    result = await self.scan_api_compliance(gateway_id, api.id, standards)
                    scan_results.append(result)
                    total_violations += result["violations_found"]
                except Exception as e:
                    logger.error(f"Failed to scan API {api.name}: {str(e)}")
                    continue

            logger.info(
                f"Completed compliance scan. Scanned {len(scan_results)} APIs, "
                f"found {total_violations} violations"
            )

            return {
                "gateway_id": str(gateway_id),
                "scan_completed_at": datetime.utcnow().isoformat(),
                "apis_scanned": len(scan_results),
                "total_violations": total_violations,
                "scan_results": scan_results,
            }

        except Exception as e:
            logger.error(f"Bulk compliance scan failed: {str(e)}")
            raise

    async def get_compliance_posture(
        self,
        api_id: Optional[UUID] = None,
        standard: Optional[ComplianceStandard] = None,
    ) -> Dict[str, Any]:
        """Get compliance posture metrics.

        Args:
            api_id: Optional API filter
            standard: Optional compliance standard filter

        Returns:
            Compliance posture metrics
        """
        try:
            posture = await self.compliance_repository.get_compliance_posture(
                api_id=api_id,
                standard=standard
            )

            # Calculate additional metrics
            total = posture["total_violations"]
            by_status = posture["by_status"]
            
            remediation_rate = 0
            if total > 0:
                remediated = by_status.get("remediated", 0)
                remediation_rate = (remediated / total) * 100

            # Calculate compliance score (0-100, higher is better)
            compliance_score = self._calculate_compliance_score(posture)

            return {
                "total_violations": total,
                "by_severity": posture["by_severity"],
                "by_status": by_status,
                "by_standard": posture["by_standard"],
                "remediation_rate": round(remediation_rate, 2),
                "compliance_score": compliance_score,
                "last_scan": posture.get("last_scan"),
                "next_audit_date": self._calculate_next_audit_date(),
            }

        except Exception as e:
            logger.error(f"Failed to get compliance posture: {str(e)}")
            raise

    async def generate_audit_report(
        self,
        api_id: Optional[UUID] = None,
        standard: Optional[ComplianceStandard] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report.

        Args:
            api_id: Optional API filter
            standard: Optional compliance standard filter
            start_date: Report start date (default: 90 days ago)
            end_date: Report end date (default: now)

        Returns:
            Comprehensive audit report with evidence
        """
        try:
            logger.info("Generating audit report")

            # Set default date range
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=90)

            # Get audit report data from repository
            # Note: generate_audit_report_data doesn't take api_id parameter
            report_data = await self.compliance_repository.generate_audit_report_data(
                standard=standard,
                start_date=start_date,
                end_date=end_date
            )
            
            # If api_id specified, filter violations
            if api_id:
                # Get violations for specific API
                violations = await self.compliance_repository.find_by_api_id(api_id)
                report_data["api_specific_violations"] = [v.dict() for v in violations]

            # Get violations needing audit attention
            violations_needing_audit = await self.compliance_repository.find_violations_needing_audit(
                days_until_audit=30
            )

            # Enhance with AI-generated executive summary if enabled
            executive_summary = await self._generate_executive_summary(
                report_data,
                violations_needing_audit
            )

            return {
                "report_id": str(UUID(int=0)),  # Generate proper report ID
                "generated_at": datetime.utcnow().isoformat(),
                "report_period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
                "executive_summary": executive_summary,
                "compliance_posture": report_data.get("summary", {}),
                "violations_by_standard": report_data.get("by_standard", {}),
                "violations_by_severity": report_data.get("by_severity", {}),
                "remediation_status": {
                    "total_violations": report_data.get("summary", {}).get("total_violations", 0),
                    "remediated_violations": report_data.get("summary", {}).get("remediated_violations", 0),
                    "open_violations": report_data.get("summary", {}).get("open_violations", 0),
                    "remediation_rate": report_data.get("summary", {}).get("remediation_rate", 0),
                },
                "violations_needing_audit": [v.dict() for v in violations_needing_audit],
                "audit_evidence": report_data.get("audit_evidence", []),
                "recommendations": report_data.get("recommendations", []),
            }

        except Exception as e:
            logger.error(f"Failed to generate audit report: {str(e)}")
            raise

    async def _generate_executive_summary(
        self,
        report_data: Dict[str, Any],
        violations_needing_audit: List[ComplianceViolation],
    ) -> str:
        """Generate AI-powered executive summary for audit report.

        Args:
            report_data: Audit report data
            violations_needing_audit: Violations requiring audit attention

        Returns:
            Executive summary text
        """
        try:
            # Build context for LLM
            summary = report_data.get('summary', {})
            context = f"""
Generate an executive summary for a compliance audit report with the following data:

Total Violations: {summary.get('total_violations', 0)}
Open Violations: {summary.get('open_violations', 0)}
Critical Violations: {summary.get('critical_violations', 0)}
High Violations: {summary.get('high_violations', 0)}
Remediation Rate: {summary.get('remediation_rate', 0)}%
By Severity: {report_data.get('by_severity', {})}
By Standard: {report_data.get('by_standard', {})}
Violations Needing Audit: {len(violations_needing_audit)}

Provide a concise 2-3 paragraph executive summary highlighting:
1. Overall compliance posture
2. Key risks and concerns
3. Recommended actions for audit preparation
"""

            messages = [{"role": "user", "content": context}]
            response = await self.llm_service.generate_completion(
                messages=messages,
                temperature=0.3,
                max_tokens=500
            )

            return response["content"]

        except Exception as e:
            logger.warning(f"Failed to generate AI summary: {str(e)}")
            # Fallback to basic summary
            return self._generate_basic_summary(report_data, violations_needing_audit)

    def _generate_basic_summary(
        self,
        report_data: Dict[str, Any],
        violations_needing_audit: List[ComplianceViolation],
    ) -> str:
        """Generate basic executive summary without AI.

        Args:
            report_data: Audit report data
            violations_needing_audit: Violations requiring audit attention

        Returns:
            Basic summary text
        """
        total = report_data['compliance_posture']['total_violations']
        critical = report_data['violations_by_severity'].get('critical', 0)
        high = report_data['violations_by_severity'].get('high', 0)
        
        return f"""
Compliance Audit Summary:

Total violations identified: {total}
Critical severity: {critical}
High severity: {high}
Violations requiring audit attention: {len(violations_needing_audit)}

Immediate action required for {critical + high} high-priority violations.
Recommend addressing violations needing audit attention within 30 days.
"""

    def _calculate_severity_breakdown(
        self,
        violations: List[ComplianceViolation]
    ) -> Dict[str, int]:
        """Calculate violation count by severity.

        Args:
            violations: List of violations

        Returns:
            Count by severity level
        """
        breakdown = {}
        for violation in violations:
            severity = violation.severity.value
            breakdown[severity] = breakdown.get(severity, 0) + 1
        return breakdown

    def _calculate_standard_breakdown(
        self,
        violations: List[ComplianceViolation]
    ) -> Dict[str, int]:
        """Calculate violation count by compliance standard.

        Args:
            violations: List of violations

        Returns:
            Count by standard
        """
        breakdown = {}
        for violation in violations:
            standard = violation.compliance_standard.value
            breakdown[standard] = breakdown.get(standard, 0) + 1
        return breakdown

    def _calculate_compliance_score(
        self,
        posture: Dict[str, Any]
    ) -> float:
        """Calculate overall compliance score (0-100, higher is better).

        Args:
            posture: Compliance posture data

        Returns:
            Compliance score
        """
        total = posture["total_violations"]
        if total == 0:
            return 100.0

        by_severity = posture["by_severity"]
        
        # Weight violations by severity
        critical_weight = 10
        high_weight = 5
        medium_weight = 2
        low_weight = 1
        
        weighted_violations = (
            by_severity.get("critical", 0) * critical_weight +
            by_severity.get("high", 0) * high_weight +
            by_severity.get("medium", 0) * medium_weight +
            by_severity.get("low", 0) * low_weight
        )
        
        # Calculate score (inverse of weighted violations, normalized to 0-100)
        # Assume 100 weighted violations = 0 score
        max_weighted = 100
        score = max(0, 100 - (weighted_violations / max_weighted * 100))
        
        return round(score, 2)

    def _calculate_next_audit_date(self) -> str:
        """Calculate next recommended audit date.

        Returns:
            ISO format date string
        """
        # Default: 90 days from now
        next_audit = datetime.utcnow() + timedelta(days=90)
        return next_audit.isoformat()

    def check_compliance_policies(self, api: API) -> List[Dict[str, Any]]:
        """Check API policy_actions for compliance violations.

        Analyzes the vendor-neutral policy_actions array to identify:
        - Missing data masking policies (GDPR, HIPAA compliance)
        - Missing logging policies (audit trail requirements)
        - Missing authentication/authorization (access control)
        - Missing encryption policies (data protection)

        Args:
            api: API object with policy_actions array

        Returns:
            List of compliance issues found
        """
        issues = []
        
        # Extract policy action types and configs from the API
        policy_types = set()
        policy_configs: Dict[PolicyActionType, Any] = {}
        if api.policy_actions:
            for action in api.policy_actions:
                policy_types.add(action.action_type)
                if action.enabled and action.config is not None:
                    policy_configs[action.action_type] = action.config
        
        # Check for data masking (GDPR, HIPAA)
        data_masking_config = policy_configs.get(PolicyActionType.DATA_MASKING)
        if PolicyActionType.DATA_MASKING not in policy_types or not data_masking_config:
            issues.append({
                "type": "missing_data_masking",
                "severity": "high",
                "message": "API lacks data masking policy (GDPR/HIPAA requirement)",
                "standards": ["GDPR", "HIPAA"],
                "recommendation": "Add DATA_MASKING policy action to protect sensitive data"
            })
        
        # Check for logging (audit trail)
        logging_config = policy_configs.get(PolicyActionType.LOGGING)
        if PolicyActionType.LOGGING not in policy_types or not logging_config:
            issues.append({
                "type": "missing_logging",
                "severity": "medium",
                "message": "API lacks logging policy (audit trail requirement)",
                "standards": ["SOC2", "PCI_DSS"],
                "recommendation": "Add LOGGING policy action for audit compliance"
            })
        
        # Check for authentication
        authentication_config = policy_configs.get(PolicyActionType.AUTHENTICATION)
        if PolicyActionType.AUTHENTICATION not in policy_types or not authentication_config:
            issues.append({
                "type": "missing_authentication",
                "severity": "critical",
                "message": "API lacks authentication policy (access control requirement)",
                "standards": ["SOC2", "ISO27001", "PCI_DSS"],
                "recommendation": "Add AUTHENTICATION policy action to secure API access"
            })
        
        # Check for authorization
        authorization_config = policy_configs.get(PolicyActionType.AUTHORIZATION)
        if PolicyActionType.AUTHORIZATION not in policy_types or not authorization_config:
            issues.append({
                "type": "missing_authorization",
                "severity": "high",
                "message": "API lacks authorization policy (access control requirement)",
                "standards": ["SOC2", "ISO27001"],
                "recommendation": "Add AUTHORIZATION policy action for role-based access control"
            })
        
        # Check for TLS/encryption
        tls_config = policy_configs.get(PolicyActionType.TLS)
        if (
            PolicyActionType.TLS not in policy_types
            or not tls_config
            or (
                hasattr(tls_config, "enforce_tls")
                and not tls_config.enforce_tls
            )
        ):
            issues.append({
                "type": "missing_tls",
                "severity": "critical",
                "message": "API lacks TLS policy (data protection requirement)",
                "standards": ["PCI_DSS", "HIPAA", "GDPR"],
                "recommendation": "Add TLS policy action to encrypt data in transit"
            })
        
        # Check for validation (input sanitization)
        validation_config = policy_configs.get(PolicyActionType.VALIDATION)
        if PolicyActionType.VALIDATION not in policy_types or not validation_config:
            issues.append({
                "type": "missing_validation",
                "severity": "medium",
                "message": "API lacks validation policy (security requirement)",
                "standards": ["OWASP", "PCI_DSS"],
                "recommendation": "Add VALIDATION policy action to prevent injection attacks"
            })
        
        return issues

# Made with Bob
