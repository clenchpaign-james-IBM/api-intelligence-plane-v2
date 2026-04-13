"""Security Agent for API Intelligence Plane.

AI-driven security analysis and automated remediation using LangChain/LangGraph.
This agent analyzes vendor-neutral API security policy coverage and recommends
appropriate gateway-level protections.

The agent uses a HYBRID approach:
- Rule-based checks for deterministic security factors
- AI enhancement for context-aware severity assessment and insights
- Combined API metadata, metrics, and traffic analysis for comprehensive assessment
- Vendor-neutral policy action analysis across supported gateway adapters
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
from app.models.vulnerability import (
    Vulnerability,
    VulnerabilityType,
    VulnerabilitySeverity,
    DetectionMethod,
    VulnerabilityStatus,
    RemediationType,
    ComplianceStandard,
)
from app.services.llm_service import LLMService
from app.db.repositories.metrics_repository import MetricsRepository

logger = logging.getLogger(__name__)


class SecurityAnalysisState(TypedDict):
    """State for security analysis workflow."""

    api_id: str
    api_name: str
    api_data: Dict[str, Any]
    metrics_data: Dict[str, Any]
    vulnerabilities: List[Dict[str, Any]]
    remediation_plan: Dict[str, Any]
    analysis_complete: bool
    error: str


class SecurityAgent:
    """AI-driven security agent for policy coverage analysis and remediation.

    This agent uses a HYBRID approach:
    1. Rule-based checks for deterministic security factors
    2. AI enhancement for context-aware analysis where beneficial
    3. Metrics and traffic analysis for data-driven insights
    4. Generate automated remediation actions for gateway policies
    5. Remain vendor-neutral by analyzing normalized `policy_actions`
    """

    def __init__(
        self,
        llm_service: LLMService,
        metrics_repository: Optional[MetricsRepository] = None,
    ):
        """Initialize security agent.

        Args:
            llm_service: LLM service for AI-powered analysis
            metrics_repository: Metrics repository for traffic analytics
        """
        self.llm_service = llm_service
        self.metrics_repository = metrics_repository or MetricsRepository()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> Any:
        """Build LangGraph workflow for security analysis.
        
        Returns:
            Compiled StateGraph workflow or None if LangGraph unavailable
        """
        if not LANGGRAPH_AVAILABLE or StateGraph is None:
            logger.warning("LangGraph not available. Security analysis will use direct execution.")
            return None

        try:
            # Create workflow with TypedDict state schema
            workflow = StateGraph(SecurityAnalysisState)

            # Define workflow nodes
            workflow.add_node("analyze_authentication", self._analyze_authentication_node)
            workflow.add_node("analyze_authorization", self._analyze_authorization_node)
            workflow.add_node("analyze_rate_limiting", self._analyze_rate_limiting_node)
            workflow.add_node("analyze_tls_config", self._analyze_tls_config_node)
            workflow.add_node("analyze_cors_policy", self._analyze_cors_policy_node)
            workflow.add_node("analyze_validation", self._analyze_validation_node)
            workflow.add_node("analyze_security_headers", self._analyze_security_headers_node)
            workflow.add_node("generate_remediation_plan", self._generate_remediation_plan_node)

            # Define workflow edges
            workflow.set_entry_point("analyze_authentication")
            workflow.add_edge("analyze_authentication", "analyze_authorization")
            workflow.add_edge("analyze_authorization", "analyze_rate_limiting")
            workflow.add_edge("analyze_rate_limiting", "analyze_tls_config")
            workflow.add_edge("analyze_tls_config", "analyze_cors_policy")
            workflow.add_edge("analyze_cors_policy", "analyze_validation")
            workflow.add_edge("analyze_validation", "analyze_security_headers")
            workflow.add_edge("analyze_security_headers", "generate_remediation_plan")
            workflow.add_edge("generate_remediation_plan", END if END else "__end__")

            return workflow.compile()
        except Exception as e:
            logger.error(f"Failed to build LangGraph workflow: {e}")
            return None

    async def analyze_api_security(self, api: API) -> Dict[str, Any]:
        """Analyze API security policy coverage using hybrid approach.

        Args:
            api: API to analyze

        Returns:
            Analysis results with vulnerabilities and remediation plan
        """
        try:
            logger.info(f"Starting hybrid security analysis for API: {api.name}")

            # Fetch recent metrics for traffic analysis
            recent_metrics = await self._fetch_recent_metrics(api.id)
            traffic_analysis = self._analyze_traffic_patterns(recent_metrics)
            
            # If workflow available, use it
            if self.workflow:
                initial_state: SecurityAnalysisState = {
                    "api_id": str(api.id),
                    "api_name": api.name,
                    "api_data": api.dict(),
                    "metrics_data": traffic_analysis,
                    "vulnerabilities": [],
                    "remediation_plan": {},
                    "analysis_complete": False,
                    "error": "",
                }

                final_state = await self.workflow.ainvoke(initial_state)
                
                return {
                    "api_id": final_state["api_id"],
                    "api_name": final_state["api_name"],
                    "vulnerabilities": final_state["vulnerabilities"],
                    "remediation_plan": final_state["remediation_plan"],
                    "metrics_analyzed": len(recent_metrics),
                    "analysis_timestamp": datetime.utcnow().isoformat(),
                }
            else:
                # Fallback to direct execution
                return await self._analyze_direct(api, recent_metrics, traffic_analysis)

        except Exception as e:
            logger.error(f"Security analysis failed: {str(e)}")
            return {
                "api_id": str(api.id),
                "api_name": api.name,
                "error": str(e),
                "vulnerabilities": [],
            }

    async def _analyze_direct(
        self, api: API, metrics: List[Metric], traffic_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Direct analysis without LangGraph workflow."""
        vulnerabilities = []
        
        # Run all analysis steps with metrics context
        vulnerabilities.extend(await self._check_authentication(api, metrics, traffic_analysis))
        vulnerabilities.extend(await self._check_authorization(api, metrics, traffic_analysis))
        vulnerabilities.extend(await self._check_rate_limiting(api, metrics, traffic_analysis))
        vulnerabilities.extend(await self._check_tls_config(api, metrics, traffic_analysis))
        vulnerabilities.extend(await self._check_cors_policy(api, metrics, traffic_analysis))
        vulnerabilities.extend(await self._check_validation(api, metrics, traffic_analysis))
        vulnerabilities.extend(await self._check_security_headers(api, metrics, traffic_analysis))
        
        # Generate remediation plan
        remediation_plan = await self._create_remediation_plan(api, vulnerabilities)

        return {
            "api_id": str(api.id),
            "api_name": api.name,
            "vulnerabilities": [v.dict() for v in vulnerabilities],
            "remediation_plan": remediation_plan,
            "metrics_analyzed": len(metrics),
            "analysis_timestamp": datetime.utcnow().isoformat(),
        }

    # Workflow nodes
    async def _analyze_authentication_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze authentication policy coverage."""
        api = API(**state["api_data"])
        vulns = await self._check_authentication(api, [], state["metrics_data"])
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_authorization_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze authorization policy coverage."""
        api = API(**state["api_data"])
        vulns = await self._check_authorization(api, [], state["metrics_data"])
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_rate_limiting_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze rate limiting policy coverage."""
        api = API(**state["api_data"])
        vulns = await self._check_rate_limiting(api, [], state["metrics_data"])
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_tls_config_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze TLS/SSL configuration."""
        api = API(**state["api_data"])
        vulns = await self._check_tls_config(api, [], state["metrics_data"])
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_cors_policy_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze CORS policy configuration."""
        api = API(**state["api_data"])
        vulns = await self._check_cors_policy(api, [], state["metrics_data"])
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_validation_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze request/response validation policies."""
        api = API(**state["api_data"])
        vulns = await self._check_validation(api, [], state["metrics_data"])
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_security_headers_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze security headers configuration."""
        api = API(**state["api_data"])
        vulns = await self._check_security_headers(api, [], state["metrics_data"])
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _generate_remediation_plan_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Generate remediation plan."""
        if state["vulnerabilities"]:
            api = API(**state["api_data"])
            vulns = [Vulnerability(**v) for v in state["vulnerabilities"]]
            plan = await self._create_remediation_plan(api, vulns)
            state["remediation_plan"] = plan
        
        state["analysis_complete"] = True
        return state

    # Helper methods
    async def _fetch_recent_metrics(self, api_id: UUID, hours: int = 24) -> List[Metric]:
        """Fetch recent metrics for traffic analysis.
        
        Args:
            api_id: API identifier
            hours: Hours of historical data to fetch
            
        Returns:
            List of recent metrics
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            # Query metrics using OpenSearch
            from opensearchpy import OpenSearch
            index_pattern = self.metrics_repository._get_index_pattern(start_time, end_time)
            
            query = {
                "query": {
                    "bool": {
                        "must": [
                            {"term": {"api_id": str(api_id)}},
                            {"range": {"timestamp": {"gte": start_time.isoformat(), "lte": end_time.isoformat()}}}
                        ]
                    }
                },
                "sort": [{"timestamp": {"order": "desc"}}],
                "size": 1000
            }
            
            response = self.metrics_repository.client.search(
                index=index_pattern,
                body=query
            )
            
            metrics = [
                self.metrics_repository.model_class(**hit["_source"])
                for hit in response["hits"]["hits"]
            ]
            
            logger.info(f"Fetched {len(metrics)} metrics for API {api_id}")
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to fetch metrics for API {api_id}: {e}")
            return []

    def _analyze_traffic_patterns(self, metrics: List[Metric]) -> Dict[str, Any]:
        """Analyze traffic patterns from metrics for security insights.
        
        Args:
            metrics: List of metrics to analyze
            
        Returns:
            Traffic analysis summary
        """
        if not metrics:
            return {
                "has_traffic": False,
                "total_requests": 0,
                "avg_error_rate": 0.0,
                "suspicious_patterns": [],
            }

        total_requests = sum(m.request_count for m in metrics)
        total_errors = sum(m.failure_count for m in metrics)
        avg_error_rate = (total_errors / total_requests) * 100 if total_requests > 0 else 0.0
        
        # Detect suspicious patterns
        suspicious_patterns = []
        
        # High 401/403 rates suggest auth issues
        auth_errors = sum(
            m.status_codes.get("401", 0) + m.status_codes.get("403", 0)
            for m in metrics
        )
        if auth_errors > total_requests * 0.1:  # >10% auth errors
            suspicious_patterns.append("high_auth_failure_rate")
        
        # High 429 rates suggest rate limiting needed
        rate_limit_hits = sum(m.status_codes.get("429", 0) for m in metrics)
        if rate_limit_hits > 0:
            suspicious_patterns.append("rate_limit_violations")
        
        # High 5xx rates suggest backend issues
        server_errors = sum(
            m.status_codes.get("500", 0) +
            m.status_codes.get("502", 0) +
            m.status_codes.get("503", 0)
            for m in metrics
        )
        if server_errors > total_requests * 0.05:  # >5% server errors
            suspicious_patterns.append("high_server_error_rate")
        
        return {
            "has_traffic": total_requests > 0,
            "total_requests": total_requests,
            "avg_error_rate": avg_error_rate,
            "auth_errors": auth_errors,
            "rate_limit_hits": rate_limit_hits,
            "server_errors": server_errors,
            "suspicious_patterns": suspicious_patterns,
        }

    # Security check methods (hybrid approach)
    async def _check_authentication(
        self,
        api: API,
        metrics: Optional[List[Metric]],
        traffic_analysis: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check authentication policy coverage using hybrid approach."""
        vulnerabilities = []

        # Check if authentication is missing or weak
        if api.authentication_type == AuthenticationType.NONE:
            # Use LLM to determine severity based on API context AND traffic patterns
            severity = await self._determine_severity_with_ai(
                api=api,
                vulnerability_type="missing_authentication",
                context={
                    "api_name": api.name,
                    "base_path": api.base_path,
                    "endpoints": [e.path for e in api.endpoints],
                    "is_shadow": api.intelligence_metadata.is_shadow,
                    "traffic_analysis": traffic_analysis,
                },
            )

            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.AUTHENTICATION,
                cve_id=None,
                severity=severity,
                title=f"Missing Authentication Policy for {api.name}",
                description=f"API {api.name} at {api.base_path} accepts requests without authentication. "
                f"This exposes the API to unauthorized access.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
                remediation_actions=None,
                remediated_at=None,
                verification_status=None,
                cvss_score=None,
                references=None,
                compliance_violations=None,
                metadata={"policy_action_type": PolicyActionType.AUTHENTICATION.value},
            )

            vulnerabilities.append(vulnerability)
            logger.info(f"Detected missing authentication for API: {api.name}")

        elif api.authentication_type == AuthenticationType.BASIC:
            # Basic auth is weak - recommend upgrade
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.AUTHENTICATION,
                cve_id=None,
                severity=VulnerabilitySeverity.MEDIUM,
                title=f"Weak Authentication Mechanism for {api.name}",
                description=f"API {api.name} uses Basic authentication which is less secure. "
                f"Consider upgrading to OAuth2 or JWT-based authentication.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.CONFIGURATION,
                remediation_actions=None,
                remediated_at=None,
                verification_status=None,
                cvss_score=None,
                references=None,
                compliance_violations=None,
                metadata={"authentication_type": api.authentication_type.value},
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_authorization(
        self,
        api: API,
        metrics: Optional[List[Metric]],
        traffic_analysis: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check authorization policy coverage using policy_actions."""
        vulnerabilities = []

        # Check if authorization policy exists in policy_actions
        has_authorization_policy = self._has_policy_action(api, PolicyActionType.AUTHORIZATION)
        
        if not has_authorization_policy:
            # Use AI to analyze if authorization is needed based on API characteristics
            needs_authorization = await self._check_authorization_need_with_ai(
                api, traffic_analysis
            )

            if needs_authorization:
                vulnerability = Vulnerability(
                    id=uuid4(),
                    api_id=api.id,
                    vulnerability_type=VulnerabilityType.AUTHORIZATION,
                    cve_id=None,
                    severity=VulnerabilitySeverity.HIGH,
                    title=f"Missing Authorization Policy for {api.name}",
                    description=f"API {api.name} lacks role-based or scope-based authorization controls. "
                    f"Authenticated users may access resources beyond their permissions.",
                    affected_endpoints=[e.path for e in api.endpoints],
                    detection_method=DetectionMethod.AUTOMATED_SCAN,
                    detected_at=datetime.utcnow(),
                    status=VulnerabilityStatus.OPEN,
                    remediation_type=RemediationType.AUTOMATED,
                    remediation_actions=None,
                    remediated_at=None,
                    verification_status=None,
                    cvss_score=None,
                    references=None,
                    compliance_violations=None,
                    metadata={"policy_action_type": PolicyActionType.AUTHORIZATION.value},
                )

                vulnerabilities.append(vulnerability)
                logger.info(f"Detected missing authorization for API: {api.name}")

        return vulnerabilities

    async def _check_rate_limiting(
        self,
        api: API,
        metrics: Optional[List[Metric]],
        traffic_analysis: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check rate limiting policy coverage using policy_actions and traffic analysis."""
        vulnerabilities = []

        # Check if rate limiting policy exists in policy_actions
        has_rate_limit = self._has_policy_action(api, PolicyActionType.RATE_LIMITING)
        
        # Analyze if rate limiting is needed based on traffic patterns
        needs_rate_limit = (
            not has_rate_limit and (
                traffic_analysis.get("total_requests", 0) > 1000 or  # High traffic
                "rate_limit_violations" in traffic_analysis.get("suspicious_patterns", []) or
                traffic_analysis.get("has_traffic", False)  # Any traffic suggests need
            )
        )

        if needs_rate_limit:
            # Determine severity based on traffic volume
            severity = VulnerabilitySeverity.HIGH if traffic_analysis.get("total_requests", 0) > 10000 else VulnerabilitySeverity.MEDIUM
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                cve_id=None,
                severity=severity,
                title=f"Missing Rate Limiting Policy for {api.name}",
                description=f"API {api.name} has no rate limiting configured. "
                f"This exposes the API to DDoS attacks and resource exhaustion. "
                f"Traffic analysis shows {traffic_analysis.get('total_requests', 0)} requests, "
                f"indicating need for rate limiting protection.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
                remediation_actions=None,
                remediated_at=None,
                verification_status=None,
                cvss_score=None,
                references=None,
                compliance_violations=None,
                metadata={"policy_action_type": PolicyActionType.RATE_LIMITING.value},
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_tls_config(
        self,
        api: API,
        metrics: Optional[List[Metric]],
        traffic_analysis: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check TLS/SSL configuration."""
        vulnerabilities = []

        # Check if HTTPS is enforced
        if api.base_path.startswith("http://"):
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                cve_id=None,
                severity=VulnerabilitySeverity.HIGH,
                title=f"Insecure HTTP Protocol for {api.name}",
                description=f"API {api.name} accepts HTTP traffic without TLS encryption. "
                f"This exposes data to man-in-the-middle attacks.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
                remediation_actions=None,
                remediated_at=None,
                verification_status=None,
                cvss_score=None,
                references=None,
                compliance_violations=None,
                metadata={"policy_action_type": PolicyActionType.TLS.value},
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_cors_policy(
        self,
        api: API,
        metrics: Optional[List[Metric]],
        traffic_analysis: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check CORS policy configuration using AI with proper context."""
        vulnerabilities = []

        # Use AI to determine if CORS policy is needed and properly configured
        # Provide comprehensive context including endpoints and traffic patterns
        cors_issues = await self._check_cors_with_ai(api, traffic_analysis)

        if cors_issues:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                cve_id=None,
                severity=VulnerabilitySeverity.MEDIUM,
                title=f"Insecure CORS Policy for {api.name}",
                description=f"API {api.name} has overly permissive CORS configuration. "
                f"Issues detected: {cors_issues}",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.CONFIGURATION,
                remediation_actions=None,
                remediated_at=None,
                verification_status=None,
                cvss_score=None,
                references=None,
                compliance_violations=None,
                metadata={"policy_action_type": PolicyActionType.CORS.value},
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_validation(
        self,
        api: API,
        metrics: Optional[List[Metric]],
        traffic_analysis: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check request/response validation policies using policy_actions and traffic analysis."""
        vulnerabilities = []

        # Check for validation policy in policy_actions
        has_validation = self._has_policy_action(api, PolicyActionType.VALIDATION)
        
        # Analyze if validation is needed based on error patterns
        needs_validation = (
            not has_validation and (
                traffic_analysis.get("avg_error_rate", 0) > 0.05 or  # >5% errors
                traffic_analysis.get("server_errors", 0) > 0 or
                traffic_analysis.get("has_traffic", False)
            )
        )

        if needs_validation:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                cve_id=None,
                severity=VulnerabilitySeverity.MEDIUM,
                title=f"Missing Input Validation Policy for {api.name}",
                description=f"API {api.name} lacks input validation policies at gateway level. "
                f"This may allow malformed or malicious requests. "
                f"Traffic analysis shows {traffic_analysis.get('avg_error_rate', 0):.1f}% error rate, "
                f"suggesting validation issues.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.CONFIGURATION,
                remediation_actions=None,
                remediated_at=None,
                verification_status=None,
                cvss_score=None,
                references=None,
                compliance_violations=None,
                metadata={"policy_action_type": PolicyActionType.VALIDATION.value},
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_security_headers(
        self,
        api: API,
        metrics: Optional[List[Metric]],
        traffic_analysis: Dict[str, Any]
    ) -> List[Vulnerability]:
        """Check security headers configuration using AI with proper context."""
        vulnerabilities = []

        # Check for security headers using AI with comprehensive context
        missing_headers = await self._check_security_headers_with_ai(api, traffic_analysis)

        if missing_headers:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                cve_id=None,
                severity=VulnerabilitySeverity.LOW,
                title=f"Missing Security Headers for {api.name}",
                description=f"API {api.name} responses lack important security headers. "
                f"Missing: {', '.join(missing_headers)}. "
                f"These headers protect against common web vulnerabilities.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
                remediation_actions=None,
                remediated_at=None,
                verification_status=None,
                cvss_score=None,
                references=None,
                compliance_violations=None,
                metadata={"missing_headers": missing_headers},
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    def _has_policy_action(self, api: API, action_type: PolicyActionType) -> bool:
        """Check whether a vendor-neutral policy action exists and is enabled."""
        if not api.policy_actions:
            return False

        return any(
            policy_action.action_type == action_type and policy_action.enabled
            for policy_action in api.policy_actions
        )

    # AI helper methods
    async def _determine_severity_with_ai(
        self,
        api: API,
        vulnerability_type: str,
        context: Dict[str, Any],
    ) -> VulnerabilitySeverity:
        """Use LLM to determine vulnerability severity based on context."""
        try:
            prompt = f"""Analyze the severity of a {vulnerability_type} vulnerability for an API.

API Context:
- Name: {context['api_name']}
- Base Path: {context['base_path']}
- Endpoints: {', '.join(context['endpoints'][:5])}
- Is Shadow API: {context['is_shadow']}

Determine the severity level (critical, high, medium, low) based on:
1. API sensitivity (payment, user data, admin functions)
2. Exposure level (public, internal, shadow)
3. Potential impact of exploitation

Respond with ONLY one word: critical, high, medium, or low"""

            messages = [
                {"role": "system", "content": "You are a security expert analyzing API vulnerabilities."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=10)
            severity_str = result.get("content", "high").strip().lower()

            severity_map = {
                "critical": VulnerabilitySeverity.CRITICAL,
                "high": VulnerabilitySeverity.HIGH,
                "medium": VulnerabilitySeverity.MEDIUM,
                "low": VulnerabilitySeverity.LOW,
            }

            return severity_map.get(severity_str, VulnerabilitySeverity.HIGH)

        except Exception as e:
            logger.error(f"AI severity determination failed: {e}")
            # Default to HIGH for safety
            return VulnerabilitySeverity.HIGH

    async def _check_authorization_need_with_ai(
        self, api: API, traffic_analysis: Dict[str, Any]
    ) -> bool:
        """Use LLM to determine if authorization policies are needed."""
        try:
            prompt = f"""Analyze if this API needs authorization policies beyond authentication.

API: {api.name}
Base Path: {api.base_path}
Endpoints: {', '.join([e.path + ' [' + e.method + ']' for e in api.endpoints[:5]])}
Authentication: {api.authentication_type.value}
Traffic: {traffic_analysis.get('total_requests', 0)} requests
Auth Errors: {traffic_analysis.get('auth_errors', 0)}

Consider:
1. Does this API handle sensitive operations (admin, delete, modify, payment)?
2. Should different users have different access levels?
3. Are there endpoints that need role-based access control?
4. Do HTTP methods suggest privileged operations (PUT, DELETE, PATCH)?
5. Do endpoint paths suggest resource ownership (/users/{{id}}, /accounts/{{id}})?

Respond with ONLY: yes or no"""

            messages = [
                {"role": "system", "content": "You are a security expert analyzing API access control needs."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=10)
            return result.get("content", "yes").strip().lower() == "yes"

        except Exception as e:
            logger.error(f"AI authorization check failed: {e}")
            # Default to requiring authorization for safety
            return True

    async def _check_cors_with_ai(
        self, api: API, traffic_analysis: Dict[str, Any]
    ) -> Optional[str]:
        """Use LLM to check CORS configuration issues with proper context."""
        try:
            prompt = f"""Analyze potential CORS security issues for this API.

API: {api.name}
Base Path: {api.base_path}
Endpoints: {', '.join([e.path for e in api.endpoints[:5]])}
Authentication: {api.authentication_type.value}
Traffic: {traffic_analysis.get('total_requests', 0)} requests

Common CORS issues to check:
1. Allowing all origins (*) with credentials
2. Missing CORS policy for browser-accessed APIs
3. Overly permissive allowed methods
4. Credentials allowed with wildcard origins

Based on the API characteristics:
- Is this likely a browser-accessed API (REST, public endpoints)?
- Does it handle sensitive data requiring CORS restrictions?
- Should CORS be configured?

If CORS issues are likely, respond with a brief description.
If no issues or CORS not needed, respond with: none"""

            messages = [
                {"role": "system", "content": "You are a security expert analyzing CORS configurations."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=100)
            response = result.get("content", "none").strip()

            return None if response.lower() == "none" else response

        except Exception as e:
            logger.error(f"AI CORS check failed: {e}")
            return "Unable to verify CORS configuration"

    async def _check_security_headers_with_ai(
        self, api: API, traffic_analysis: Dict[str, Any]
    ) -> List[str]:
        """Use LLM to identify missing security headers with proper context."""
        try:
            prompt = f"""List security headers that should be configured for this API.

API: {api.name}
Base Path: {api.base_path}
Endpoints: {', '.join([e.path for e in api.endpoints[:5]])}
Authentication: {api.authentication_type.value}
Uses TLS Protection: {self._has_policy_action(api, PolicyActionType.TLS)}
Traffic: {traffic_analysis.get('total_requests', 0)} requests

Common security headers:
- Strict-Transport-Security (HSTS) - for HTTPS APIs
- X-Frame-Options - prevent clickjacking
- X-Content-Type-Options - prevent MIME sniffing
- Content-Security-Policy - XSS protection
- X-XSS-Protection - legacy XSS protection

Based on the API characteristics, which headers are likely missing or needed?
Respond with a comma-separated list of missing headers, or "none" if all are likely present."""

            messages = [
                {"role": "system", "content": "You are a security expert analyzing HTTP security headers."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=100)
            response = result.get("content", "").strip()

            if response.lower() == "none":
                return []

            return [h.strip() for h in response.split(",")]

        except Exception as e:
            logger.error(f"AI security headers check failed: {e}")
            return ["HSTS", "X-Frame-Options", "CSP"]
    async def _requires_gdpr_compliance(self, api_context: Dict[str, Any]) -> bool:
        """Determine if API requires GDPR compliance using AI."""
        try:
            prompt = f"""Determine if this API likely handles personal data requiring GDPR compliance.

API: {api_context['name']}
Base Path: {api_context['base_path']}
Endpoints: {', '.join(api_context['endpoints'][:5])}

GDPR applies if the API processes personal data of EU residents, such as:
- User profiles, accounts, authentication
- Email addresses, phone numbers, names
- Location data, IP addresses
- Payment information, financial data
- Health information, biometric data

Based on the API name and endpoints, does this API likely handle personal data?
Respond with ONLY: yes or no"""

            messages = [
                {"role": "system", "content": "You are a compliance expert analyzing GDPR requirements."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=10)
            return result.get("content", "no").strip().lower() == "yes"

        except Exception as e:
            logger.error(f"GDPR compliance check failed: {e}")
            return False

    async def _requires_hipaa_compliance(self, api_context: Dict[str, Any]) -> bool:
        """Determine if API requires HIPAA compliance using AI."""
        try:
            prompt = f"""Determine if this API likely handles protected health information (PHI) requiring HIPAA compliance.

API: {api_context['name']}
Base Path: {api_context['base_path']}
Endpoints: {', '.join(api_context['endpoints'][:5])}

HIPAA applies if the API processes PHI, such as:
- Patient records, medical history
- Health insurance information
- Prescription data, lab results
- Healthcare provider information
- Medical billing data

Based on the API name and endpoints, does this API likely handle PHI?
Respond with ONLY: yes or no"""

            messages = [
                {"role": "system", "content": "You are a compliance expert analyzing HIPAA requirements."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=10)
            return result.get("content", "no").strip().lower() == "yes"

        except Exception as e:
            logger.error(f"HIPAA compliance check failed: {e}")
            return False

    async def _requires_pci_dss_compliance(self, api_context: Dict[str, Any]) -> bool:
        """Determine if API requires PCI-DSS compliance using AI."""
        try:
            prompt = f"""Determine if this API likely handles payment card data requiring PCI-DSS compliance.

API: {api_context['name']}
Base Path: {api_context['base_path']}
Endpoints: {', '.join(api_context['endpoints'][:5])}

PCI-DSS applies if the API processes payment card data, such as:
- Credit/debit card numbers
- Card verification codes (CVV)
- Payment processing, transactions
- Billing information
- Cardholder data

Based on the API name and endpoints, does this API likely handle payment card data?
Respond with ONLY: yes or no"""

            messages = [
                {"role": "system", "content": "You are a compliance expert analyzing PCI-DSS requirements."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=10)
            return result.get("content", "no").strip().lower() == "yes"

        except Exception as e:
            logger.error(f"PCI-DSS compliance check failed: {e}")
            return False

    async def _requires_soc2_compliance(self, api_context: Dict[str, Any]) -> bool:
        """Determine if API requires SOC2 compliance using AI."""
        try:
            prompt = f"""Determine if this API likely requires SOC2 compliance.

API: {api_context['name']}
Base Path: {api_context['base_path']}
Endpoints: {', '.join(api_context['endpoints'][:5])}

SOC2 applies to service providers handling customer data, particularly:
- SaaS applications
- Cloud services
- Data processing services
- Customer-facing APIs
- Business-critical systems

Based on the API characteristics, does this API likely require SOC2 compliance?
Respond with ONLY: yes or no"""

            messages = [
                {"role": "system", "content": "You are a compliance expert analyzing SOC2 requirements."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=10)
            return result.get("content", "no").strip().lower() == "yes"

        except Exception as e:
            logger.error(f"SOC2 compliance check failed: {e}")
            return False


    async def _create_remediation_plan(
        self,
        api: API,
        vulnerabilities: List[Vulnerability],
    ) -> Dict[str, Any]:
        """Generate comprehensive remediation plan using AI."""
        if not vulnerabilities:
            return {
                "priority": "none",
                "estimated_time_hours": 0,
                "actions": [],
                "verification_steps": [],
            }

        try:
            vuln_summary = "\n".join([
                f"- {v.severity.value.upper()}: {v.title}"
                for v in vulnerabilities
            ])

            prompt = f"""Create a prioritized remediation plan for these API security vulnerabilities.

API: {api.name}
Vulnerabilities:
{vuln_summary}

Generate a JSON remediation plan with:
1. Priority order (critical first)
2. Specific gateway configuration changes
3. Estimated implementation time
4. Verification steps

Format:
{{
  "priority": "high|medium|low",
  "estimated_time_hours": <number>,
  "actions": [
    {{
      "step": <number>,
      "action": "<description>",
      "type": "configuration|policy|upgrade",
      "estimated_minutes": <number>
    }}
  ],
  "verification_steps": ["<step1>", "<step2>"]
}}"""

            messages = [
                {"role": "system", "content": "You are a security expert creating remediation plans. Respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ]

            result = await self.llm_service.generate_completion(messages, temperature=0.3, max_tokens=1000)
            response_text = result.get("content", "")

            # Parse JSON response
            import json
            plan = json.loads(response_text)

            return plan

        except Exception as e:
            logger.error(f"AI remediation plan generation failed: {e}")
            # Return basic plan
            return {
                "priority": "high",
                "estimated_time_hours": len(vulnerabilities) * 0.5,
                "actions": [
                    {
                        "step": i + 1,
                        "action": f"Remediate: {v.title}",
                        "type": "configuration",
                        "estimated_minutes": 30,
                    }
                    for i, v in enumerate(vulnerabilities)
                ],
                "verification_steps": ["Test API with security scanner", "Verify policies applied"],
            }


# Made with Bob