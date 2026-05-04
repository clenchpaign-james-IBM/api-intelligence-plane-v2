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
    AuditTrailEntry,
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

            # Store or update violations (deduplication)
            stored_violations = []
            for violation_data in analysis_result.get("violations", []):
                # Convert dict to ComplianceViolation if needed
                if isinstance(violation_data, dict):
                    violation = ComplianceViolation(**violation_data)
                else:
                    violation = violation_data

                # Check if violation already exists
                existing = await self.compliance_repository.find_existing_violation(
                    gateway_id=violation.gateway_id,
                    api_id=violation.api_id,
                    violation_type=violation.violation_type.value,
                    compliance_standard=violation.compliance_standard.value,
                )

                if existing:
                    # Update existing violation
                    updated_violation = await self._update_existing_violation(
                        existing, violation
                    )
                    stored_violations.append(updated_violation)
                    logger.info(
                        f"Updated existing violation {existing.id} for API {api_id}"
                    )
                else:
                    # Create new violation
                    self.compliance_repository.create(violation)
                    stored_violations.append(violation)
                    logger.info(
                        f"Created new violation for API {api_id}: {violation.violation_type.value}"
                    )

            # Update API's violation count in intelligence metadata
            if api.intelligence_metadata:
                api.intelligence_metadata.violation_count = len(stored_violations)
                self.api_repository.update(
                    str(api_id),
                    {"intelligence_metadata": api.intelligence_metadata.model_dump()}
                )
                logger.info(
                    f"Updated API {api_id} violation count to {len(stored_violations)}"
                )

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
        gateway_id: UUID,
        api_ids: Optional[List[UUID]] = None,
        standards: Optional[List[ComplianceStandard]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Generate comprehensive audit report for a gateway.

        Args:
            gateway_id: Gateway UUID (required for scoping)
            api_ids: Optional API filters (multiple)
            standards: Optional compliance standard filters (multiple)
            start_date: Report start date (default: 90 days ago)
            end_date: Report end date (default: now)

        Returns:
            Comprehensive audit report with evidence
        """
        try:
            from uuid import uuid4
            
            logger.info(f"Generating audit report for gateway {gateway_id}")

            # Set default date range
            if not end_date:
                # Use end of current day to include today's violations
                end_date = datetime.utcnow().replace(hour=23, minute=59, second=59, microsecond=999999)
            else:
                # If end_date is provided but has no time component (midnight), set to end of day
                if end_date.hour == 0 and end_date.minute == 0 and end_date.second == 0:
                    end_date = end_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            if not start_date:
                # Use start of day 90 days ago
                start_date = (end_date - timedelta(days=90)).replace(hour=0, minute=0, second=0, microsecond=0)
            else:
                # Ensure start_date is at start of day
                if start_date.hour != 0 or start_date.minute != 0 or start_date.second != 0:
                    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            
            logger.info(f"Using date range: {start_date.isoformat()} to {end_date.isoformat()}")

            # Query violations directly from OpenSearch by gateway_id
            # This is more efficient than iterating through APIs
            query = {
                "bool": {
                    "must": [
                        {"term": {"gateway_id": str(gateway_id)}}
                    ]
                }
            }
            
            # Add API filter if specified
            if api_ids and len(api_ids) > 0:
                logger.info(f"Filtering by {len(api_ids)} specific APIs")
                query["bool"]["must"].append({
                    "terms": {"api_id": [str(api_id) for api_id in api_ids]}
                })
            
            # Query OpenSearch
            body = {
                "query": query,
                "size": 10000,  # Get all violations
                "sort": [{"detected_at": {"order": "desc"}}]
            }
            
            response = self.compliance_repository.client.search(
                index=self.compliance_repository.index_name,
                body=body
            )
            
            # Convert to ComplianceViolation objects
            all_violations = [
                self.compliance_repository.model_class(**hit["_source"])
                for hit in response["hits"]["hits"]
            ]
            
            logger.info(f"Total violations found for gateway: {len(all_violations)}")
            
            # Filter by date range
            filtered_violations = []
            logger.info(f"Date range filter: {start_date.isoformat()} to {end_date.isoformat()}")
            
            for v in all_violations:
                try:
                    # Handle both datetime objects and ISO strings
                    if isinstance(v.detected_at, str):
                        # Remove timezone info and parse
                        detected_str = v.detected_at.replace('Z', '').replace('+00:00', '')
                        if '.' in detected_str:
                            # Has microseconds
                            detected_dt = datetime.strptime(detected_str.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                        else:
                            detected_dt = datetime.strptime(detected_str, '%Y-%m-%dT%H:%M:%S')
                    else:
                        detected_dt = v.detected_at
                        # Make timezone-naive for comparison
                        if detected_dt.tzinfo is not None:
                            detected_dt = detected_dt.replace(tzinfo=None)
                    
                    # Log first few for debugging
                    if len(filtered_violations) < 3:
                        logger.info(f"Violation {v.id} detected_at: {detected_dt.isoformat()}, in range: {start_date <= detected_dt <= end_date}")
                    
                    if start_date <= detected_dt <= end_date:
                        filtered_violations.append(v)
                except Exception as e:
                    logger.warning(f"Failed to parse detected_at '{v.detected_at}' for violation {v.id}: {e}")
                    # Include violation if we can't parse the date - better to include than exclude
                    filtered_violations.append(v)
            
            all_violations = filtered_violations
            logger.info(f"Total violations after date filtering: {len(all_violations)}")
            
            # Filter by standards if specified
            if standards and len(standards) > 0:
                standard_values = [s.value for s in standards]
                logger.info(f"Filtering by standards: {standard_values}")
                all_violations = [
                    v for v in all_violations
                    if v.compliance_standard in standard_values
                ]
                logger.info(f"Total violations after standard filtering: {len(all_violations)}")
            
            # Calculate aggregations
            total_violations = len(all_violations)
            by_severity = {"critical": 0, "high": 0, "medium": 0, "low": 0}
            by_standard = {}
            by_status = {"open": 0, "in_progress": 0, "resolved": 0, "accepted_risk": 0, "false_positive": 0}
            remediated_count = 0
            open_count = 0
            
            for v in all_violations:
                # Count by severity
                if v.severity in by_severity:
                    by_severity[v.severity] += 1
                
                # Count by standard
                std = v.compliance_standard
                by_standard[std] = by_standard.get(std, 0) + 1
                
                # Count by status
                if v.status in by_status:
                    by_status[v.status] += 1
                
                if v.status == "resolved":
                    remediated_count += 1
                elif v.status == "open":
                    open_count += 1
            
            remediation_rate = (remediated_count / total_violations * 100) if total_violations > 0 else 0

            # Get violations needing audit attention
            violations_needing_audit = await self.compliance_repository.find_violations_needing_audit(
                days_until_audit=30
            )
            # Filter to this gateway
            violations_needing_audit = [
                v for v in violations_needing_audit
                if str(v.gateway_id) == str(gateway_id)
            ]

            # Build report data structure
            report_data = {
                "summary": {
                    "total_violations": total_violations,
                    "remediated_violations": remediated_count,
                    "open_violations": open_count,
                    "remediation_rate": round(remediation_rate, 2),
                },
                "by_severity": by_severity,
                "by_standard": by_standard,
                "by_status": by_status,
            }

            # Enhance with AI-generated executive summary if enabled
            executive_summary = await self._generate_executive_summary(
                report_data,
                violations_needing_audit
            )
            
            # Generate recommendations based on violations
            recommendations = []
            if by_severity.get("critical", 0) > 0:
                recommendations.append(f"Address {by_severity['critical']} critical violations immediately to reduce compliance risk")
            if by_severity.get("high", 0) > 0:
                recommendations.append(f"Prioritize remediation of {by_severity['high']} high-severity violations")
            if remediation_rate < 50:
                recommendations.append(f"Current remediation rate is {remediation_rate:.1f}%. Increase remediation efforts to improve compliance posture")
            for standard, count in by_standard.items():
                if count > 0:
                    recommendations.append(f"Review {count} {standard.upper()} violations for regulatory compliance")

            return {
                "report_id": str(uuid4()),  # Generate proper unique report ID
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
                "audit_evidence": [],
                "recommendations": recommendations,
                "detailed_violations": [v.dict() for v in all_violations[:50]],  # Include first 50 violations for details
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

    def _merge_report_data(self, report_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge multiple report data dictionaries into one.

        Args:
            report_data_list: List of report data dictionaries

        Returns:
            Merged report data
        """
        if not report_data_list:
            return {}
        
        if len(report_data_list) == 1:
            return report_data_list[0]
        
        # Initialize merged data with first report
        merged = report_data_list[0].copy()
        
        # Merge subsequent reports
        for report_data in report_data_list[1:]:
            # Merge summary
            if "summary" in report_data:
                summary = merged.get("summary", {})
                for key, value in report_data["summary"].items():
                    if isinstance(value, (int, float)):
                        summary[key] = summary.get(key, 0) + value
                    else:
                        summary[key] = value
                merged["summary"] = summary
            
            # Merge by_standard
            if "by_standard" in report_data:
                by_standard = merged.get("by_standard", {})
                for standard, count in report_data["by_standard"].items():
                    by_standard[standard] = by_standard.get(standard, 0) + count
                merged["by_standard"] = by_standard
            
            # Merge by_severity
            if "by_severity" in report_data:
                by_severity = merged.get("by_severity", {})
                for severity, count in report_data["by_severity"].items():
                    by_severity[severity] = by_severity.get(severity, 0) + count
                merged["by_severity"] = by_severity
            
            # Merge audit_evidence
            if "audit_evidence" in report_data:
                evidence = merged.get("audit_evidence", [])
                evidence.extend(report_data["audit_evidence"])
                merged["audit_evidence"] = evidence
            
            # Merge recommendations
            if "recommendations" in report_data:
                recommendations = merged.get("recommendations", [])
                recommendations.extend(report_data["recommendations"])
                merged["recommendations"] = recommendations
        
        return merged

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

    async def _update_existing_violation(
        self,
        existing: ComplianceViolation,
        new_violation: ComplianceViolation,
    ) -> ComplianceViolation:
        """Update existing violation with new data while preserving history.

        Args:
            existing: Existing violation from database
            new_violation: New violation data from scan

        Returns:
            Updated violation
        """
        # Preserve original detection time and ID
        updated_data = existing.model_dump()
        
        # Update key fields that may have changed
        updated_data["severity"] = new_violation.severity
        updated_data["description"] = new_violation.description
        updated_data["affected_endpoints"] = new_violation.affected_endpoints
        updated_data["updated_at"] = datetime.utcnow()
        
        # If violation was previously remediated but detected again, reopen it
        if existing.status == ComplianceStatus.REMEDIATED:
            updated_data["status"] = ComplianceStatus.OPEN
            updated_data["remediated_at"] = None
            
            # Add audit trail entry for reopening
            audit_entry = AuditTrailEntry(
                timestamp=datetime.utcnow(),
                action="violation_reopened",
                performed_by="compliance_agent",
                details="Violation detected again after previous remediation",
                status_before=ComplianceStatus.REMEDIATED.value,
                status_after=ComplianceStatus.OPEN.value,
            )
            updated_data["audit_trail"].append(audit_entry.model_dump())
        
        # Merge evidence - add new evidence without duplicating
        # Use type, source, and description as key (not timestamp, as it changes on each scan)
        existing_evidence_keys = {
            (e.type, e.source, e.description)
            for e in existing.evidence
        }
        for new_evidence in new_violation.evidence:
            evidence_key = (
                new_evidence.type,
                new_evidence.source,
                new_evidence.description,
            )
            if evidence_key not in existing_evidence_keys:
                updated_data["evidence"].append(new_evidence.model_dump())
                existing_evidence_keys.add(evidence_key)  # Add to set to prevent duplicates in this update
        
        # Add audit trail entry for update
        audit_entry = AuditTrailEntry(
            timestamp=datetime.utcnow(),
            action="violation_updated",
            performed_by="compliance_agent",
            details="Violation re-detected during compliance scan, evidence updated",
            status_before=existing.status.value,
            status_after=updated_data["status"],
        )
        updated_data["audit_trail"].append(audit_entry.model_dump())
        
        # Update in database
        updated_violation = ComplianceViolation(**updated_data)
        self.compliance_repository.update(
            str(existing.id),
            updated_violation.model_dump()
        )
        
        return updated_violation

# Made with Bob
