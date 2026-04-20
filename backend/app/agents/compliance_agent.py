"""Compliance Agent for API Intelligence Plane.

HYBRID compliance analysis combining rule-based detection with AI-enhanced insights.
Analyzes APIs for compliance with GDPR, HIPAA, SOC2, PCI-DSS, and ISO 27001.

HYBRID APPROACH:
- Rule-based checks provide deterministic baseline detection
- AI enhancement adds context-aware severity assessment and natural language explanations
- Both work together seamlessly for comprehensive compliance analysis

SCOPE: Gateway-level compliance only. Monitors compliance requirements that can be
observed and verified at the API Gateway layer.

DISTINCTION: Compliance violations are regulatory requirement failures, distinct from
security vulnerabilities which are threat-based.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, TypedDict
from uuid import UUID, uuid4

# Try to import LangGraph components
try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    StateGraph = None
    END = None

from app.models.base.api import API, AuthenticationType, PolicyActionType
from app.models.base.metric import Metric
from app.models.compliance import (
    ComplianceViolation,
    ComplianceViolationType,
    ComplianceSeverity,
    ComplianceStandard,
    ComplianceStatus,
    DetectionMethod,
    Evidence,
    AuditTrailEntry,
)
from app.services.llm_service import LLMService
from app.db.repositories.metrics_repository import MetricsRepository

logger = logging.getLogger(__name__)


class ComplianceAnalysisState(TypedDict):
    """State for compliance analysis workflow."""
    
    api_id: str
    api_name: str
    api_data: Dict[str, Any]
    metrics_data: Dict[str, Any]
    violations: List[Dict[str, Any]]
    audit_evidence: List[Dict[str, Any]]
    analysis_complete: bool
    error: str


class ComplianceAgent:
    """HYBRID compliance agent for Gateway-level regulatory analysis.

    This agent uses a HYBRID approach:
    1. Rule-based checks for deterministic compliance violation detection
    2. AI enhancement for context-aware severity assessment and insights
    3. Metrics and traffic analysis for data-driven compliance evaluation

    Analyzes compliance with:
    - GDPR (General Data Protection Regulation)
    - HIPAA (Health Insurance Portability and Accountability Act)
    - SOC2 (Service Organization Control 2)
    - PCI-DSS (Payment Card Industry Data Security Standard)
    - ISO 27001 (Information Security Management)

    Focus: Gateway-observable compliance requirements only.
    """

    def __init__(
        self,
        llm_service: LLMService,
        metrics_repository: Optional[MetricsRepository] = None,
    ):
        """Initialize compliance agent.

        Args:
            llm_service: LLM service for AI-powered analysis
            metrics_repository: Metrics repository for traffic analytics
        """
        self.llm_service = llm_service
        self.metrics_repository = metrics_repository or MetricsRepository()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> Any:
        """Build LangGraph workflow for compliance analysis.
        
        Returns:
            Compiled StateGraph workflow or None if LangGraph unavailable
        """
        if not LANGGRAPH_AVAILABLE or StateGraph is None:
            logger.warning("LangGraph not available. Compliance analysis will use direct execution.")
            return None

        try:
            # Create workflow with TypedDict state schema
            workflow = StateGraph(ComplianceAnalysisState)

            # Define workflow nodes for each compliance standard
            workflow.add_node("analyze_gdpr", self._analyze_gdpr_node)
            workflow.add_node("analyze_hipaa", self._analyze_hipaa_node)
            workflow.add_node("analyze_soc2", self._analyze_soc2_node)
            workflow.add_node("analyze_pci_dss", self._analyze_pci_dss_node)
            workflow.add_node("analyze_iso_27001", self._analyze_iso_27001_node)
            workflow.add_node("collect_audit_evidence", self._collect_audit_evidence_node)

            # Define workflow edges
            workflow.set_entry_point("analyze_gdpr")
            workflow.add_edge("analyze_gdpr", "analyze_hipaa")
            workflow.add_edge("analyze_hipaa", "analyze_soc2")
            workflow.add_edge("analyze_soc2", "analyze_pci_dss")
            workflow.add_edge("analyze_pci_dss", "analyze_iso_27001")
            workflow.add_edge("analyze_iso_27001", "collect_audit_evidence")
            workflow.add_edge("collect_audit_evidence", END if END else "__end__")

            return workflow.compile()
        except Exception as e:
            logger.error(f"Failed to build LangGraph workflow: {e}")
            return None

    async def analyze_api_compliance(self, api: API) -> Dict[str, Any]:
        """Analyze API compliance with regulatory standards using HYBRID approach.

        Args:
            api: API to analyze

        Returns:
            Analysis results with violations and audit evidence
        """
        try:
            logger.info(f"Starting HYBRID compliance analysis for API: {api.name}")

            # Fetch recent metrics for traffic analysis
            recent_metrics = await self._fetch_recent_metrics(api.id)
            traffic_analysis = self._analyze_traffic_patterns(recent_metrics)
            
            # If workflow available, use it
            if self.workflow:
                initial_state: ComplianceAnalysisState = {
                    "api_id": str(api.id),
                    "api_name": api.name,
                    "api_data": api.dict(),
                    "metrics_data": traffic_analysis,
                    "violations": [],
                    "audit_evidence": [],
                    "analysis_complete": False,
                    "error": "",
                }

                final_state = await self.workflow.ainvoke(initial_state)
                
                return {
                    "api_id": final_state["api_id"],
                    "api_name": final_state["api_name"],
                    "violations": final_state["violations"],
                    "audit_evidence": final_state["audit_evidence"],
                    "metrics_analyzed": len(recent_metrics),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                }
            else:
                # Fallback to direct execution
                return await self._analyze_direct(api, recent_metrics, traffic_analysis)

        except Exception as e:
            logger.error(f"Compliance analysis failed: {str(e)}")
            return {
                "api_id": str(api.id),
                "api_name": api.name,
                "error": str(e),
                "violations": [],
                "audit_evidence": [],
            }

    async def _analyze_direct(
        self, api: API, metrics: List[Metric], traffic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Direct analysis without LangGraph workflow."""
        violations = []
        
        # Run all compliance checks with HYBRID approach
        violations.extend(await self._check_gdpr_compliance(api, metrics, traffic_analysis))
        violations.extend(await self._check_hipaa_compliance(api, metrics, traffic_analysis))
        violations.extend(await self._check_soc2_compliance(api, metrics, traffic_analysis))
        violations.extend(await self._check_pci_dss_compliance(api, metrics, traffic_analysis))
        violations.extend(await self._check_iso_27001_compliance(api, metrics, traffic_analysis))
        
        # Collect audit evidence
        audit_evidence = await self._collect_audit_evidence(api, violations)
        
        return {
            "api_id": str(api.id),
            "api_name": api.name,
            "violations": [v.dict() for v in violations],
            "audit_evidence": audit_evidence,
            "metrics_analyzed": len(metrics),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # Workflow nodes
    async def _analyze_gdpr_node(self, state: ComplianceAnalysisState) -> ComplianceAnalysisState:
        """Analyze GDPR compliance."""
        api = API(**state["api_data"])
        violations = await self._check_gdpr_compliance(api, [], state["metrics_data"])
        state["violations"].extend([v.dict() for v in violations])
        return state

    async def _analyze_hipaa_node(self, state: ComplianceAnalysisState) -> ComplianceAnalysisState:
        """Analyze HIPAA compliance."""
        api = API(**state["api_data"])
        violations = await self._check_hipaa_compliance(api, [], state["metrics_data"])
        state["violations"].extend([v.dict() for v in violations])
        return state

    async def _analyze_soc2_node(self, state: ComplianceAnalysisState) -> ComplianceAnalysisState:
        """Analyze SOC2 compliance."""
        api = API(**state["api_data"])
        violations = await self._check_soc2_compliance(api, [], state["metrics_data"])
        state["violations"].extend([v.dict() for v in violations])
        return state

    async def _analyze_pci_dss_node(self, state: ComplianceAnalysisState) -> ComplianceAnalysisState:
        """Analyze PCI-DSS compliance."""
        api = API(**state["api_data"])
        violations = await self._check_pci_dss_compliance(api, [], state["metrics_data"])
        state["violations"].extend([v.dict() for v in violations])
        return state

    async def _analyze_iso_27001_node(self, state: ComplianceAnalysisState) -> ComplianceAnalysisState:
        """Analyze ISO 27001 compliance."""
        api = API(**state["api_data"])
        violations = await self._check_iso_27001_compliance(api, [], state["metrics_data"])
        state["violations"].extend([v.dict() for v in violations])
        return state

    async def _collect_audit_evidence_node(self, state: ComplianceAnalysisState) -> ComplianceAnalysisState:
        """Collect audit evidence."""
        api = API(**state["api_data"])
        violations = [ComplianceViolation(**v) for v in state["violations"]]
        evidence = await self._collect_audit_evidence(api, violations)
        state["audit_evidence"] = evidence
        state["analysis_complete"] = True
        return state

    # Helper methods
    async def _fetch_recent_metrics(self, api_id: UUID, hours: int = 24) -> List[Metric]:
        """Fetch recent metrics for traffic analysis."""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            metrics, _ = self.metrics_repository.find_by_api(
                api_id=api_id,
                start_time=start_time,
                end_time=end_time,
                size=1000
            )
            
            return metrics
        except Exception as e:
            logger.warning(f"Failed to fetch metrics: {e}")
            return []

    def _analyze_traffic_patterns(self, metrics: List[Metric]) -> Dict[str, Any]:
        """Analyze traffic patterns from metrics."""
        if not metrics:
            return {
                "has_traffic": False,
                "avg_requests_per_minute": 0,
                "peak_requests_per_minute": 0,
                "error_rate": 0,
            }

        total_requests = sum(m.request_count for m in metrics)
        total_errors = sum(m.failure_count for m in metrics)
        total_throughput = sum(m.throughput for m in metrics if m.throughput)

        return {
            "has_traffic": len(metrics) > 0,
            "total_requests": total_requests,
            "avg_requests_per_minute": total_requests / len(metrics) if metrics else 0,
            "peak_requests_per_minute": max((m.throughput for m in metrics if m.throughput), default=0),
            "avg_throughput": total_throughput / len(metrics) if metrics else 0,
            "error_rate": (total_errors / total_requests) * 100 if total_requests > 0 else 0,
            "metrics_count": len(metrics),
        }

    # HYBRID Compliance check methods (Rule-based + AI-enhanced)
    async def _check_gdpr_compliance(
        self, api: API, metrics: List[Metric], traffic_analysis: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check GDPR compliance using HYBRID approach (Gateway-level)."""
        violations = []
        
        # RULE-BASED: GDPR Art. 32 - Security of Processing
        if not self._has_tls_encryption(api):
            # AI ENHANCEMENT: Assess severity based on context
            severity = await self._assess_compliance_severity(
                api=api,
                violation_type="gdpr_security_of_processing",
                context={
                    "api_name": api.name,
                    "base_path": api.base_path,
                    "has_traffic": traffic_analysis.get("has_traffic", False),
                    "traffic_volume": traffic_analysis.get("total_requests", 0),
                    "is_shadow": api.intelligence_metadata.is_shadow,
                },
            )
            
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.GDPR,
                violation_type=ComplianceViolationType.GDPR_SECURITY_OF_PROCESSING,
                severity=severity,
                title="GDPR Security of Processing Violation - Missing TLS Encryption",
                description="API does not enforce TLS encryption for data in transit, violating GDPR Article 32 requirements for appropriate technical measures.",
                regulatory_reference="GDPR Article 32 - Security of processing",
                evidence_type="gateway_config",
                evidence_description="Gateway TLS configuration analysis shows no TLS enforcement"
            ))
        
        # RULE-BASED: GDPR Art. 30 - Records of Processing Activities
        if not self._has_audit_logging(api):
            severity = await self._assess_compliance_severity(
                api=api,
                violation_type="gdpr_records_of_processing",
                context={
                    "api_name": api.name,
                    "has_traffic": traffic_analysis.get("has_traffic", False),
                },
            )
            
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.GDPR,
                violation_type=ComplianceViolationType.GDPR_RECORDS_OF_PROCESSING,
                severity=severity,
                title="GDPR Records of Processing Violation - Insufficient Audit Logging",
                description="API lacks comprehensive audit logging at Gateway level, making it difficult to maintain records of processing activities as required by GDPR Article 30.",
                regulatory_reference="GDPR Article 30 - Records of processing activities",
                evidence_type="gateway_config",
                evidence_description="Gateway logging configuration shows insufficient audit trail"
            ))
        
        return violations

    async def _check_hipaa_compliance(
        self, api: API, metrics: List[Metric], traffic_analysis: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check HIPAA compliance using HYBRID approach (Gateway-level)."""
        violations = []
        
        # RULE-BASED: HIPAA § 164.312(e)(1) - Transmission Security
        if not self._has_strong_tls(api):
            severity = await self._assess_compliance_severity(
                api=api,
                violation_type="hipaa_transmission_security",
                context={
                    "api_name": api.name,
                    "handles_phi": True,  # Assume true for HIPAA checks
                    "traffic_volume": traffic_analysis.get("total_requests", 0),
                },
            )
            
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.HIPAA,
                violation_type=ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY,
                severity=severity,
                title="HIPAA Transmission Security Violation",
                description="API does not enforce TLS 1.3 encryption for PHI transmission, violating HIPAA Security Rule § 164.312(e)(1).",
                regulatory_reference="HIPAA Security Rule § 164.312(e)(1) - Transmission Security",
                evidence_type="gateway_config",
                evidence_description="Gateway TLS policy shows TLS 1.2 or lower allowed"
            ))
        
        # RULE-BASED: HIPAA § 164.312(a)(1) - Access Control
        if api.authentication_type == AuthenticationType.NONE:
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.HIPAA,
                violation_type=ComplianceViolationType.HIPAA_ACCESS_CONTROL,
                severity=ComplianceSeverity.CRITICAL,  # Always critical for missing auth
                title="HIPAA Access Control Violation - Missing Authentication",
                description="API lacks authentication controls, violating HIPAA Security Rule § 164.312(a)(1) requirements for access control.",
                regulatory_reference="HIPAA Security Rule § 164.312(a)(1) - Access Control",
                evidence_type="gateway_config",
                evidence_description="Gateway authentication policy shows no authentication required"
            ))
        
        # RULE-BASED: HIPAA § 164.312(b) - Audit Controls
        if not self._has_audit_logging(api):
            severity = await self._assess_compliance_severity(
                api=api,
                violation_type="hipaa_audit_controls",
                context={"api_name": api.name, "handles_phi": True},
            )
            
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.HIPAA,
                violation_type=ComplianceViolationType.HIPAA_AUDIT_CONTROLS,
                severity=severity,
                title="HIPAA Audit Controls Violation",
                description="API lacks audit controls to record and examine activity, violating HIPAA Security Rule § 164.312(b).",
                regulatory_reference="HIPAA Security Rule § 164.312(b) - Audit Controls",
                evidence_type="gateway_config",
                evidence_description="Gateway audit logging configuration is insufficient"
            ))
        
        return violations

    async def _check_soc2_compliance(
        self, api: API, metrics: List[Metric], traffic_analysis: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check SOC2 compliance using HYBRID approach (Gateway-level)."""
        violations = []
        
        # RULE-BASED: SOC2 CC6.1 - Logical and Physical Access Controls
        if api.authentication_type == AuthenticationType.NONE:
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.SOC2,
                violation_type=ComplianceViolationType.SOC2_LOGICAL_ACCESS,
                severity=ComplianceSeverity.HIGH,
                title="SOC2 Logical Access Control Violation",
                description="API lacks logical access controls (authentication), violating SOC2 CC6.1 requirements.",
                regulatory_reference="SOC2 Trust Services Criteria CC6.1 - Logical and Physical Access Controls",
                evidence_type="gateway_config",
                evidence_description="Gateway shows no authentication policy configured"
            ))
        
        # RULE-BASED: SOC2 CC7.2 - System Monitoring
        if not self._has_monitoring(api, traffic_analysis):
            severity = await self._assess_compliance_severity(
                api=api,
                violation_type="soc2_system_monitoring",
                context={
                    "api_name": api.name,
                    "has_traffic": traffic_analysis.get("has_traffic", False),
                    "metrics_count": traffic_analysis.get("metrics_count", 0),
                },
            )
            
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.SOC2,
                violation_type=ComplianceViolationType.SOC2_SYSTEM_MONITORING,
                severity=severity,
                title="SOC2 System Monitoring Violation",
                description="API lacks adequate system monitoring capabilities, violating SOC2 CC7.2 requirements.",
                regulatory_reference="SOC2 Trust Services Criteria CC7.2 - System Monitoring",
                evidence_type="metrics",
                evidence_description="Insufficient metrics collection and monitoring detected"
            ))
        
        return violations

    async def _check_pci_dss_compliance(
        self, api: API, metrics: List[Metric], traffic_analysis: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check PCI-DSS compliance using HYBRID approach (Gateway-level)."""
        violations = []
        
        # RULE-BASED: PCI-DSS Requirement 4 - Encrypt transmission of cardholder data
        if not self._has_strong_tls(api):
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.PCI_DSS,
                violation_type=ComplianceViolationType.PCI_DSS_ENCRYPTION_IN_TRANSIT,
                severity=ComplianceSeverity.CRITICAL,
                title="PCI-DSS Encryption in Transit Violation",
                description="API does not enforce strong TLS encryption for cardholder data transmission, violating PCI-DSS Requirement 4.",
                regulatory_reference="PCI-DSS Requirement 4 - Encrypt transmission of cardholder data across open, public networks",
                evidence_type="gateway_config",
                evidence_description="Gateway TLS configuration does not meet PCI-DSS requirements"
            ))
        
        # RULE-BASED: PCI-DSS Requirement 7 - Restrict access to cardholder data
        if api.authentication_type == AuthenticationType.NONE:
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.PCI_DSS,
                violation_type=ComplianceViolationType.PCI_DSS_ACCESS_CONTROL,
                severity=ComplianceSeverity.CRITICAL,
                title="PCI-DSS Access Control Violation",
                description="API lacks access controls to restrict access to cardholder data, violating PCI-DSS Requirement 7.",
                regulatory_reference="PCI-DSS Requirement 7 - Restrict access to cardholder data by business need to know",
                evidence_type="gateway_config",
                evidence_description="Gateway authentication policy shows unrestricted access"
            ))
        
        return violations

    async def _check_iso_27001_compliance(
        self, api: API, metrics: List[Metric], traffic_analysis: Dict[str, Any]
    ) -> List[ComplianceViolation]:
        """Check ISO 27001 compliance using HYBRID approach (Gateway-level)."""
        violations = []
        
        # RULE-BASED: ISO 27001 A.9 - Access Control
        if api.authentication_type == AuthenticationType.NONE:
            severity = await self._assess_compliance_severity(
                api=api,
                violation_type="iso_27001_access_control",
                context={
                    "api_name": api.name,
                    "is_shadow": api.intelligence_metadata.is_shadow,
                    "traffic_volume": traffic_analysis.get("total_requests", 0),
                },
            )
            
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.ISO_27001,
                violation_type=ComplianceViolationType.ISO_27001_ACCESS_CONTROL,
                severity=severity,
                title="ISO 27001 Access Control Violation",
                description="API lacks access control mechanisms, violating ISO 27001 Annex A.9 requirements.",
                regulatory_reference="ISO 27001 Annex A.9 - Access Control",
                evidence_type="gateway_config",
                evidence_description="Gateway access control policy is not configured"
            ))
        
        # RULE-BASED: ISO 27001 A.10 - Cryptography
        if not self._has_tls_encryption(api):
            violations.append(self._create_violation(
                api=api,
                standard=ComplianceStandard.ISO_27001,
                violation_type=ComplianceViolationType.ISO_27001_CRYPTOGRAPHY,
                severity=ComplianceSeverity.HIGH,
                title="ISO 27001 Cryptography Violation",
                description="API does not implement cryptographic controls for data in transit, violating ISO 27001 Annex A.10.",
                regulatory_reference="ISO 27001 Annex A.10 - Cryptography",
                evidence_type="gateway_config",
                evidence_description="Gateway cryptographic controls are insufficient"
            ))
        
        return violations

    # AI Enhancement Methods
    async def _assess_compliance_severity(
        self,
        api: API,
        violation_type: str,
        context: Dict[str, Any],
    ) -> ComplianceSeverity:
        """AI-enhanced severity assessment based on context.
        
        Uses LLM to assess severity considering:
        - API characteristics (shadow API, traffic volume, etc.)
        - Business context
        - Risk factors
        
        Falls back to rule-based severity if AI unavailable.
        """
        try:
            # Build context-rich prompt
            prompt = f"""Assess the severity of a compliance violation for an API Gateway endpoint.

API: {api.name}
Violation Type: {violation_type}
Context: {context}

Consider:
1. Traffic volume and API usage patterns
2. Whether this is a shadow API (undocumented)
3. Potential business impact
4. Regulatory penalties for this violation type

Respond with ONLY one word: CRITICAL, HIGH, MEDIUM, or LOW"""

            messages = [{"role": "user", "content": prompt}]
            response = await self.llm_service.generate_completion(
                messages=messages,
                max_tokens=10,
                temperature=0.3,
            )
            
            severity_str = response["content"].strip().upper()
            if severity_str in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
                return ComplianceSeverity(severity_str.lower())
            
        except Exception as e:
            logger.warning(f"AI severity assessment failed, using rule-based: {e}")
        
        # Fallback to rule-based severity
        return self._rule_based_severity(violation_type, context)

    def _rule_based_severity(self, violation_type: str, context: Dict[str, Any]) -> ComplianceSeverity:
        """Rule-based severity assessment as fallback."""
        # High traffic or shadow APIs get higher severity
        if context.get("traffic_volume", 0) > 10000 or context.get("is_shadow", False):
            return ComplianceSeverity.HIGH
        
        # Default to medium
        return ComplianceSeverity.MEDIUM

    async def _collect_audit_evidence(
        self, api: API, violations: List[ComplianceViolation]
    ) -> List[Dict[str, Any]]:
        """Collect audit evidence for compliance reporting."""
        evidence = []
        
        # Collect Gateway configuration evidence
        evidence.append({
            "type": "gateway_configuration",
            "timestamp": datetime.utcnow().isoformat(),
            "api_id": str(api.id),
            "api_name": api.name,
            "authentication_type": api.authentication_type.value if api.authentication_type else "none",
            "total_violations": len(violations),
            "violations_by_severity": self._count_by_severity(violations),
            "violations_by_standard": self._count_by_standard(violations),
        })
        
        return evidence

    # Utility methods
    def _create_violation(
        self,
        api: API,
        standard: ComplianceStandard,
        violation_type: ComplianceViolationType,
        severity: ComplianceSeverity,
        title: str,
        description: str,
        regulatory_reference: str,
        evidence_type: str,
        evidence_description: str,
    ) -> ComplianceViolation:
        """Create a compliance violation with evidence and audit trail."""
        now = datetime.utcnow()
        
        return ComplianceViolation(
            id=uuid4(),
            api_id=api.id,
            compliance_standard=standard,
            violation_type=violation_type,
            severity=severity,
            title=title,
            description=description,
            affected_endpoints=[e.path for e in api.endpoints] if hasattr(api, 'endpoints') and api.endpoints else None,
            detection_method=DetectionMethod.AI_ANALYSIS,
            detected_at=now,
            status=ComplianceStatus.OPEN,
            evidence=[
                Evidence(
                    type=evidence_type,
                    description=evidence_description,
                    source="compliance_agent",
                    data={},  # Empty dict for now
                    timestamp=now,
                )
            ],
            audit_trail=[
                AuditTrailEntry(
                    timestamp=now,
                    action="violation_detected",
                    performed_by="compliance_agent",
                    status_before=None,
                    status_after=ComplianceStatus.OPEN,
                    details=f"HYBRID compliance scan detected {standard.value} violation",
                )
            ],
            regulatory_reference=regulatory_reference,
            risk_level="financial",
            remediation_deadline=now + timedelta(days=30),
            next_audit_date=now + timedelta(days=90),
            remediation_documentation=None,
            remediated_at=None,
            last_audit_date=None,
            metadata={},
        )

    def _has_policy_action(self, api: API, action_type: PolicyActionType) -> bool:
        """
        Check if API has a specific policy action configured.
        
        Args:
            api: API object
            action_type: Policy action type to check for
            
        Returns:
            True if policy action exists and is enabled
        """
        if not api.policy_actions:
            return False
        
        return any(
            pa.action_type == action_type and pa.enabled
            for pa in api.policy_actions
        )
    
    def _has_tls_encryption(self, api: API) -> bool:
        """Check if API has TLS encryption configured."""
        from app.utils.tls_config import has_tls_enforced
        return has_tls_enforced(api)

    def _has_strong_tls(self, api: API) -> bool:
        """Check if API has strong TLS (1.3) configured."""
        # Check if TLS policy action exists
        if not api.policy_actions:
            return False
        
        # Look for TLS policy with strong configuration
        for pa in api.policy_actions:
            if pa.action_type == PolicyActionType.TLS and pa.enabled:
                # Check vendor_config for TLS version
                if pa.vendor_config and pa.vendor_config.get("min_tls_version") == "1.3":
                    return True
                # Check config for TLS version (TlsConfig model)
                if pa.config:
                    from app.models.base.policy_configs import TlsConfig
                    if isinstance(pa.config, TlsConfig) and pa.config.min_tls_version == "1.3":
                        return True
        
        return False

    def _has_audit_logging(self, api: API) -> bool:
        """Check if API has audit logging configured."""
        # Check if logging policy action exists in policy_actions
        return self._has_policy_action(api, PolicyActionType.LOGGING)

    def _has_monitoring(self, api: API, traffic_analysis: Dict[str, Any]) -> bool:
        """Check if API has adequate monitoring."""
        return traffic_analysis.get("has_traffic", False) and traffic_analysis.get("metrics_count", 0) > 0

    def _count_by_severity(self, violations: List[ComplianceViolation]) -> Dict[str, int]:
        """Count violations by severity."""
        counts = {}
        for v in violations:
            severity = v.severity.value
            counts[severity] = counts.get(severity, 0) + 1
        return counts

    def _count_by_standard(self, violations: List[ComplianceViolation]) -> Dict[str, int]:
        """Count violations by compliance standard."""
        counts = {}
        for v in violations:
            standard = v.compliance_standard.value
            counts[standard] = counts.get(standard, 0) + 1
        return counts


# Made with Bob