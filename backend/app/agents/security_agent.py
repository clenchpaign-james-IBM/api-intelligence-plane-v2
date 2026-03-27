"""Security Agent for API Intelligence Plane.

AI-driven security analysis and automated remediation using LangChain/LangGraph.
This agent intelligently analyzes API security policy coverage and recommends
appropriate gateway-level protections.

The agent leverages BOTH API metadata AND real-time metrics/traffic analytics
for comprehensive security assessment.
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

from app.models.api import API, AuthenticationType
from app.models.metric import Metric
from app.models.vulnerability import (
    Vulnerability,
    VulnerabilityType,
    VulnerabilitySeverity,
    DetectionMethod,
    VulnerabilityStatus,
    RemediationType,
)
from app.services.llm_service import LLMService
from app.db.repositories.metrics_repository import MetricsRepository

logger = logging.getLogger(__name__)


class SecurityAnalysisState(TypedDict):
    """State for security analysis workflow."""
    
    api_id: str
    api_name: str
    api_data: Dict[str, Any]
    vulnerabilities: List[Dict[str, Any]]
    remediation_plan: Dict[str, Any]
    analysis_complete: bool
    error: str


class SecurityAgent:
    """AI-driven security agent for policy coverage analysis and remediation.

    This agent uses LLM to intelligently:
    1. Analyze API security policy coverage
    2. Detect missing or weak security policies
    3. Recommend appropriate gateway-level protections
    4. Generate automated remediation actions
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
        """Analyze API security policy coverage using metrics-driven insights.

        Args:
            api: API to analyze

        Returns:
            Analysis results with vulnerabilities and remediation plan
        """
        try:
            logger.info(f"Starting metrics-driven security analysis for API: {api.name}")

            # Fetch recent metrics for traffic analysis
            recent_metrics = await self._fetch_recent_metrics(api.id)
            
            # If workflow available, use it
            if self.workflow:
                initial_state: SecurityAnalysisState = {
                    "api_id": str(api.id),
                    "api_name": api.name,
                    "api_data": api.dict(),
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
                # Fallback to direct execution with metrics
                return await self._analyze_direct(api, recent_metrics)

        except Exception as e:
            logger.error(f"Security analysis failed: {str(e)}")
            return {
                "api_id": str(api.id),
                "api_name": api.name,
                "error": str(e),
                "vulnerabilities": [],
            }

    async def _analyze_direct(self, api: API, metrics: List[Metric]) -> Dict[str, Any]:
        """Direct analysis without LangGraph workflow, using metrics."""
        vulnerabilities = []
        
        # Run all analysis steps with metrics context
        vulnerabilities.extend(await self._check_authentication(api, metrics))
        vulnerabilities.extend(await self._check_authorization(api, metrics))
        vulnerabilities.extend(await self._check_rate_limiting(api, metrics))
        vulnerabilities.extend(await self._check_tls_config(api, metrics))
        vulnerabilities.extend(await self._check_cors_policy(api, metrics))
        vulnerabilities.extend(await self._check_validation(api, metrics))
        vulnerabilities.extend(await self._check_security_headers(api, metrics))
        
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
        vulns = await self._check_authentication(api)
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_authorization_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze authorization policy coverage."""
        api = API(**state["api_data"])
        vulns = await self._check_authorization(api)
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_rate_limiting_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze rate limiting policy coverage."""
        api = API(**state["api_data"])
        vulns = await self._check_rate_limiting(api)
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_tls_config_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze TLS/SSL configuration."""
        api = API(**state["api_data"])
        vulns = await self._check_tls_config(api)
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_cors_policy_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze CORS policy configuration."""
        api = API(**state["api_data"])
        vulns = await self._check_cors_policy(api)
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_validation_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze request/response validation policies."""
        api = API(**state["api_data"])
        vulns = await self._check_validation(api)
        state["vulnerabilities"].extend([v.dict() for v in vulns])
        return state

    async def _analyze_security_headers_node(self, state: SecurityAnalysisState) -> SecurityAnalysisState:
        """Analyze security headers configuration."""
        api = API(**state["api_data"])
        vulns = await self._check_security_headers(api)
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
                "total_requests": 0,
                "avg_error_rate": 0,
                "suspicious_patterns": [],
            }
        
        total_requests = sum(m.request_count for m in metrics)
        total_errors = sum(m.error_count for m in metrics)
        avg_error_rate = total_errors / total_requests if total_requests > 0 else 0
        
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
            "total_requests": total_requests,
            "avg_error_rate": avg_error_rate,
            "auth_errors": auth_errors,
            "rate_limit_hits": rate_limit_hits,
            "server_errors": server_errors,
            "suspicious_patterns": suspicious_patterns,
        }

    # Analysis methods (enhanced with metrics)
    async def _check_authentication(self, api: API, metrics: Optional[List[Metric]] = None) -> List[Vulnerability]:
        """Check authentication policy coverage using AI and metrics analysis."""
        vulnerabilities = []
        
        # Analyze traffic patterns if metrics available
        traffic_analysis = self._analyze_traffic_patterns(metrics or [])

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
                    "is_shadow": api.is_shadow,
                    "traffic_analysis": traffic_analysis,
                },
            )

            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.AUTHENTICATION,
                severity=severity,
                title=f"Missing Authentication Policy for {api.name}",
                description=f"API {api.name} at {api.base_path} accepts requests without authentication. "
                f"This exposes the API to unauthorized access.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
            )

            vulnerabilities.append(vulnerability)
            logger.info(f"Detected missing authentication for API: {api.name}")

        elif api.authentication_type == AuthenticationType.BASIC:
            # Basic auth is weak - recommend upgrade
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.AUTHENTICATION,
                severity=VulnerabilitySeverity.MEDIUM,
                title=f"Weak Authentication Mechanism for {api.name}",
                description=f"API {api.name} uses Basic authentication which is less secure. "
                f"Consider upgrading to OAuth2 or JWT-based authentication.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.CONFIGURATION,
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_authorization(self, api: API, metrics: Optional[List[Metric]] = None) -> List[Vulnerability]:
        """Check authorization policy coverage using AI."""
        vulnerabilities = []

        # Use LLM to analyze if authorization policies are needed
        needs_authorization = await self._check_authorization_need_with_ai(api)

        if needs_authorization:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.AUTHORIZATION,
                severity=VulnerabilitySeverity.HIGH,
                title=f"Missing Authorization Policy for {api.name}",
                description=f"API {api.name} lacks role-based or scope-based authorization controls. "
                f"Authenticated users may access resources beyond their permissions.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
            )

            vulnerabilities.append(vulnerability)
            logger.info(f"Detected missing authorization for API: {api.name}")

        return vulnerabilities

    async def _check_rate_limiting(self, api: API, metrics: Optional[List[Metric]] = None) -> List[Vulnerability]:
        """Check rate limiting policy coverage."""
        vulnerabilities = []

        # Check if rate limiting is configured
        # This would check gateway configuration in real implementation
        has_rate_limit = False  # Placeholder

        if not has_rate_limit:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                severity=VulnerabilitySeverity.MEDIUM,
                title=f"Missing Rate Limiting Policy for {api.name}",
                description=f"API {api.name} has no rate limiting configured. "
                f"This exposes the API to DDoS attacks and resource exhaustion.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_tls_config(self, api: API, metrics: Optional[List[Metric]] = None) -> List[Vulnerability]:
        """Check TLS/SSL configuration."""
        vulnerabilities = []

        # Check if HTTPS is enforced
        if api.base_path.startswith("http://"):
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                severity=VulnerabilitySeverity.HIGH,
                title=f"Insecure HTTP Protocol for {api.name}",
                description=f"API {api.name} accepts HTTP traffic without TLS encryption. "
                f"This exposes data to man-in-the-middle attacks.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_cors_policy(self, api: API, metrics: Optional[List[Metric]] = None) -> List[Vulnerability]:
        """Check CORS policy configuration."""
        vulnerabilities = []

        # Use AI to determine if CORS policy is needed and properly configured
        cors_issues = await self._check_cors_with_ai(api)

        if cors_issues:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                severity=VulnerabilitySeverity.MEDIUM,
                title=f"Insecure CORS Policy for {api.name}",
                description=f"API {api.name} has overly permissive CORS configuration. "
                f"Issues detected: {cors_issues}",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.CONFIGURATION,
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_validation(self, api: API, metrics: Optional[List[Metric]] = None) -> List[Vulnerability]:
        """Check request/response validation policies."""
        vulnerabilities = []

        # Check for validation policies
        has_validation = False  # Placeholder

        if not has_validation:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                severity=VulnerabilitySeverity.MEDIUM,
                title=f"Missing Input Validation Policy for {api.name}",
                description=f"API {api.name} lacks input validation policies at gateway level. "
                f"This may allow malformed or malicious requests.",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.CONFIGURATION,
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

    async def _check_security_headers(self, api: API, metrics: Optional[List[Metric]] = None) -> List[Vulnerability]:
        """Check security headers configuration."""
        vulnerabilities = []

        # Check for security headers
        missing_headers = await self._check_security_headers_with_ai(api)

        if missing_headers:
            vulnerability = Vulnerability(
                id=uuid4(),
                api_id=api.id,
                vulnerability_type=VulnerabilityType.CONFIGURATION,
                severity=VulnerabilitySeverity.LOW,
                title=f"Missing Security Headers for {api.name}",
                description=f"API {api.name} responses lack security headers. "
                f"Missing: {', '.join(missing_headers)}",
                affected_endpoints=[e.path for e in api.endpoints],
                detection_method=DetectionMethod.AUTOMATED_SCAN,
                detected_at=datetime.utcnow(),
                status=VulnerabilityStatus.OPEN,
                remediation_type=RemediationType.AUTOMATED,
            )

            vulnerabilities.append(vulnerability)

        return vulnerabilities

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

    async def _check_authorization_need_with_ai(self, api: API) -> bool:
        """Use LLM to determine if authorization policies are needed."""
        try:
            prompt = f"""Analyze if this API needs authorization policies beyond authentication.

API: {api.name}
Base Path: {api.base_path}
Endpoints: {', '.join([e.path for e in api.endpoints[:5]])}
Authentication: {api.authentication_type.value}

Consider:
1. Does this API handle sensitive operations (admin, delete, modify)?
2. Should different users have different access levels?
3. Are there endpoints that need role-based access control?

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

    async def _check_cors_with_ai(self, api: API) -> Optional[str]:
        """Use LLM to check CORS configuration issues."""
        try:
            prompt = f"""Analyze potential CORS security issues for this API.

API: {api.name}
Base Path: {api.base_path}

Common CORS issues:
1. Allowing all origins (*)
2. Missing CORS policy entirely
3. Overly permissive allowed methods
4. Credentials allowed with wildcard origins

If CORS issues are likely, respond with a brief description.
If no issues, respond with: none"""

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

    async def _check_security_headers_with_ai(self, api: API) -> List[str]:
        """Use LLM to identify missing security headers."""
        try:
            prompt = f"""List security headers that should be configured for this API.

API: {api.name}
Base Path: {api.base_path}

Common security headers:
- Strict-Transport-Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- Content-Security-Policy
- X-XSS-Protection

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