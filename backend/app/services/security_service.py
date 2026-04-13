"""Security Service for API Intelligence Plane.

Orchestrates security scanning, vulnerability management, and automated remediation.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import UUID

from app.agents.security_agent import SecurityAgent
from app.config import Settings
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.models.base.api import API, PolicyActionType
from app.models.vulnerability import (
    Vulnerability,
    VulnerabilityStatus,
    VulnerabilityType,
    RemediationType,
    RemediationAction,
    VerificationStatus,
)
from app.services.llm_service import LLMService

logger = logging.getLogger(__name__)


class SecurityService:
    """Service for security scanning and vulnerability management.
    
    This service provides:
    1. Hybrid security policy coverage analysis (rule-based + AI)
    2. Vulnerability detection and tracking
    3. Automated remediation workflows via Gateway adapters
    4. Real remediation verification
    5. Security posture reporting with compliance
    """

    def __init__(
        self,
        settings: Settings,
        api_repository: Optional[APIRepository] = None,
        vulnerability_repository: Optional[VulnerabilityRepository] = None,
        llm_service: Optional[LLMService] = None,
        security_agent: Optional[SecurityAgent] = None,
        metrics_repository: Optional[Any] = None,
        gateway_repository: Optional[GatewayRepository] = None,
        gateway_adapter: Optional[Any] = None,
    ):
        """Initialize security service.

        Args:
            settings: Application settings
            api_repository: API repository instance
            vulnerability_repository: Vulnerability repository instance
            llm_service: LLM service instance
            security_agent: Security agent instance
            metrics_repository: Metrics repository instance
            gateway_repository: Gateway repository instance
            gateway_adapter: Gateway adapter instance for policy application
        """
        self.settings = settings
        self.api_repository = api_repository or APIRepository()
        self.vulnerability_repository = vulnerability_repository or VulnerabilityRepository()
        self.llm_service = llm_service or LLMService(settings)
        
        # Import here to avoid circular dependency
        from app.db.repositories.metrics_repository import MetricsRepository
        
        self.metrics_repository = metrics_repository or MetricsRepository()
        self.gateway_repository = gateway_repository or GatewayRepository()
        
        self.security_agent = security_agent or SecurityAgent(
            self.llm_service,
            self.metrics_repository
        )
        
        # Gateway adapter for applying policies
        self.gateway_adapter = gateway_adapter

    async def scan_api_security(
        self,
        api_id: UUID,
    ) -> Dict[str, Any]:
        """Scan API for security policy coverage issues using hybrid approach.

        Args:
            api_id: API to scan

        Returns:
            Scan results with vulnerabilities, compliance issues, and remediation plan
        """
        try:
            logger.info(f"Starting hybrid security scan for API: {api_id}")

            # Get API details
            api = self.api_repository.get(str(api_id))
            if not api:
                raise ValueError(f"API not found: {api_id}")

            # Perform hybrid security analysis (always uses both rule-based and AI)
            analysis_result = await self.security_agent.analyze_api_security(api)

            # Store vulnerabilities
            stored_vulnerabilities = []
            for vuln_data in analysis_result.get("vulnerabilities", []):
                # Convert dict to Vulnerability if needed
                if isinstance(vuln_data, dict):
                    vulnerability = Vulnerability(**vuln_data)
                else:
                    vulnerability = vuln_data

                # Store in database
                self.vulnerability_repository.create(vulnerability)
                stored_vulnerabilities.append(vulnerability)

            logger.info(
                f"Security scan complete. Found {len(stored_vulnerabilities)} vulnerabilities"
            )

            return {
                "scan_id": str(UUID(int=0)),  # Generate proper scan ID
                "api_id": str(api_id),
                "api_name": api.name,
                "scan_completed_at": datetime.utcnow().isoformat(),
                "vulnerabilities_found": len(stored_vulnerabilities),
                "severity_breakdown": self._calculate_severity_breakdown(
                    stored_vulnerabilities
                ),
                "vulnerabilities": [v.dict() for v in stored_vulnerabilities],
                "compliance_issues": analysis_result.get("compliance_issues", []),
                "remediation_plan": analysis_result.get("remediation_plan", {}),
                "metrics_analyzed": analysis_result.get("metrics_analyzed", 0),
            }

        except Exception as e:
            logger.error(f"Security scan failed for API {api_id}: {str(e)}")
            raise

    async def scan_all_apis(self) -> Dict[str, Any]:
        """Scan all active APIs for security issues.


        Returns:
            Aggregated scan results
        """
        try:
            logger.info("Starting security scan for all APIs")

            # Get all active APIs
            # Use search with match_all query
            from opensearchpy import OpenSearch
            response = self.api_repository.client.search(
                index=self.api_repository.index_name,
                body={"query": {"match_all": {}}, "size": 1000}
            )
            apis = [self.api_repository.model_class(**hit["_source"]) for hit in response["hits"]["hits"]]
            
            scan_results = []
            total_vulnerabilities = 0

            for api in apis:
                try:
                    result = await self.scan_api_security(api.id)
                    scan_results.append(result)
                    total_vulnerabilities += result["vulnerabilities_found"]
                except Exception as e:
                    logger.error(f"Failed to scan API {api.name}: {str(e)}")
                    continue

            logger.info(
                f"Completed security scan. Scanned {len(scan_results)} APIs, "
                f"found {total_vulnerabilities} vulnerabilities"
            )

            return {
                "scan_completed_at": datetime.utcnow().isoformat(),
                "apis_scanned": len(scan_results),
                "total_vulnerabilities": total_vulnerabilities,
                "scan_results": scan_results,
            }

        except Exception as e:
            logger.error(f"Bulk security scan failed: {str(e)}")
            raise

    async def remediate_vulnerability(
        self,
        vulnerability_id: UUID,
        remediation_strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Trigger automated remediation for a vulnerability.

        Args:
            vulnerability_id: Vulnerability to remediate
            remediation_strategy: Optional specific strategy to use

        Returns:
            Remediation result
        """
        try:
            logger.info(f"Starting remediation for vulnerability: {vulnerability_id}")

            # Get vulnerability
            vulnerability = self.vulnerability_repository.get(str(vulnerability_id))
            if not vulnerability:
                raise ValueError(f"Vulnerability not found: {vulnerability_id}")

            # Check if already remediated
            if vulnerability.status == VulnerabilityStatus.REMEDIATED:
                return {
                    "vulnerability_id": str(vulnerability_id),
                    "status": "already_remediated",
                    "message": "Vulnerability already remediated",
                }

            # Check if automated remediation is possible
            if vulnerability.remediation_type != RemediationType.AUTOMATED:
                remediation_type_str = vulnerability.remediation_type.value if vulnerability.remediation_type else "manual"
                return {
                    "vulnerability_id": str(vulnerability_id),
                    "status": "manual_required",
                    "message": f"Vulnerability requires {remediation_type_str} remediation",
                    "recommendation": "Manual intervention required",
                }

            # Get API details
            api = self.api_repository.get(str(vulnerability.api_id))
            if not api:
                raise ValueError(f"API not found: {vulnerability.api_id}")

            # Perform automated remediation
            remediation_result = await self._apply_automated_remediation(
                api=api,
                vulnerability=vulnerability,
                strategy=remediation_strategy,
            )

            # Update vulnerability status
            vulnerability.status = VulnerabilityStatus.IN_PROGRESS
            vulnerability.remediation_actions = remediation_result.get("actions", [])
            vulnerability.updated_at = datetime.utcnow()

            self.vulnerability_repository.update(
                str(vulnerability.id),
                vulnerability.dict(exclude={"id"})
            )

            # Verify remediation
            verification_result = await self.verify_remediation(vulnerability_id)

            logger.info(f"Remediation completed for vulnerability: {vulnerability_id}")

            return {
                "vulnerability_id": str(vulnerability_id),
                "status": "remediation_applied",
                "remediation_result": remediation_result,
                "verification_result": verification_result,
            }

        except Exception as e:
            logger.error(f"Remediation failed for vulnerability {vulnerability_id}: {str(e)}")
            raise

    async def verify_remediation(
        self,
        vulnerability_id: UUID,
    ) -> Dict[str, Any]:
        """Verify that remediation was successful.

        Args:
            vulnerability_id: Vulnerability to verify

        Returns:
            Verification result
        """
        try:
            logger.info(f"Verifying remediation for vulnerability: {vulnerability_id}")

            # Get vulnerability
            vulnerability = self.vulnerability_repository.get(str(vulnerability_id))
            if not vulnerability:
                raise ValueError(f"Vulnerability not found: {vulnerability_id}")

            # Get API
            api = self.api_repository.get(str(vulnerability.api_id))
            if not api:
                raise ValueError(f"API not found: {vulnerability.api_id}")

            # Re-scan the specific vulnerability area
            verification_result = await self._verify_vulnerability_fixed(
                api=api,
                vulnerability=vulnerability,
            )

            # Update vulnerability based on verification
            if verification_result["is_fixed"]:
                vulnerability.status = VulnerabilityStatus.REMEDIATED
                vulnerability.remediated_at = datetime.utcnow()
                vulnerability.verification_status = VerificationStatus.VERIFIED
            else:
                vulnerability.verification_status = VerificationStatus.FAILED

            vulnerability.updated_at = datetime.utcnow()
            self.vulnerability_repository.update(
                str(vulnerability.id),
                vulnerability.dict(exclude={"id"})
            )

            logger.info(
                f"Verification complete for vulnerability {vulnerability_id}: "
                f"{'FIXED' if verification_result['is_fixed'] else 'NOT FIXED'}"
            )

            return verification_result

        except Exception as e:
            logger.error(f"Verification failed for vulnerability {vulnerability_id}: {str(e)}")
            raise

    async def get_security_posture(
        self,
        api_id: Optional[UUID] = None,
    ) -> Dict[str, Any]:
        """Get security posture metrics.

        Args:
            api_id: Optional API filter

        Returns:
            Security posture metrics
        """
        try:
            posture = await self.vulnerability_repository.get_security_posture(api_id)

            # Calculate additional metrics
            total = posture["total_vulnerabilities"]
            by_status = posture["by_status"]
            
            remediation_rate = 0
            if total > 0:
                remediated = by_status.get("remediated", 0)
                remediation_rate = (remediated / total) * 100

            # Calculate risk score (0-100, higher is worse)
            risk_score = self._calculate_risk_score(posture)

            return {
                **posture,
                "remediation_rate": round(remediation_rate, 2),
                "risk_score": risk_score,
                "risk_level": self._get_risk_level(risk_score),
            }

        except Exception as e:
            logger.error(f"Failed to get security posture: {str(e)}")
            raise

    async def get_vulnerabilities(
        self,
        api_id: Optional[UUID] = None,
        status: Optional[VulnerabilityStatus] = None,
        severity: Optional[str] = None,
        limit: int = 100,
    ) -> List[Vulnerability]:
        """Get vulnerabilities with optional filters.

        Args:
            api_id: Optional API filter
            status: Optional status filter
            severity: Optional severity filter
            limit: Maximum results

        Returns:
            List of vulnerabilities
        """
        try:
            if api_id:
                return await self.vulnerability_repository.find_by_api_id(
                    api_id, status, limit
                )
            elif severity:
                return await self.vulnerability_repository.find_by_severity(
                    severity, status, limit
                )
            else:
                return await self.vulnerability_repository.find_open_vulnerabilities(
                    api_id, limit
                )

        except Exception as e:
            logger.error(f"Failed to get vulnerabilities: {str(e)}")
            raise

    # Private helper methods

    async def _apply_automated_remediation(
        self,
        api: API,
        vulnerability: Vulnerability,
        strategy: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Apply automated remediation for a vulnerability via Gateway adapter."""
        actions = []
        
        # Get gateway adapter for this API
        if not self.gateway_adapter:
            # Get gateway for this API
            gateway = self.gateway_repository.get(str(api.gateway_id))
            if not gateway:
                raise ValueError(f"Gateway not found for API: {api.id}")
            
            # Get adapter from factory
            from app.adapters.factory import GatewayAdapterFactory
            self.gateway_adapter = GatewayAdapterFactory.create_adapter(gateway)
            await self.gateway_adapter.connect()
        
        try:
            # Apply remediation based on vulnerability type
            if vulnerability.vulnerability_type == VulnerabilityType.AUTHENTICATION:
                policy = {
                    "auth_type": "oauth2",
                    "provider": "default",
                    "scopes": ["read", "write"],
                    "validation_rules": {"require_valid_token": True}
                }
                success = await self.gateway_adapter.apply_authentication_policy(
                    str(api.id), policy
                )
                actions.append(
                    RemediationAction(
                        action="Applied OAuth2 authentication policy at gateway",
                        type="gateway_policy",
                        status="completed" if success else "failed",
                        performed_at=datetime.utcnow(),
                        performed_by="security_agent",
                        gateway_policy_id=f"auth-{api.id}" if success else None,
                        error_message=None if success else "Failed to apply policy",
                    )
                )
                
            elif vulnerability.vulnerability_type == VulnerabilityType.AUTHORIZATION:
                policy = {
                    "policy_type": "rbac",
                    "roles": ["user", "admin"],
                    "permissions": {"user": ["read"], "admin": ["read", "write", "delete"]},
                    "rules": []
                }
                success = await self.gateway_adapter.apply_authorization_policy(
                    str(api.id), policy
                )
                actions.append(
                    RemediationAction(
                        action="Applied RBAC authorization policy at gateway",
                        type="gateway_policy",
                        status="completed" if success else "failed",
                        performed_at=datetime.utcnow(),
                        performed_by="security_agent",
                        gateway_policy_id=f"authz-{api.id}" if success else None,
                        error_message=None if success else "Failed to apply policy",
                    )
                )
                
            elif vulnerability.vulnerability_type == VulnerabilityType.CONFIGURATION:
                if "rate limit" in vulnerability.title.lower():
                    policy = {
                        "requests_per_minute": 100,
                        "burst_size": 20,
                        "key_strategy": "ip_address"
                    }
                    success = await self.gateway_adapter.apply_rate_limit_policy(
                        str(api.id), policy
                    )
                    actions.append(
                        RemediationAction(
                            action="Applied rate limiting policy (100 req/min)",
                            type="gateway_policy",
                            status="completed" if success else "failed",
                            performed_at=datetime.utcnow(),
                            performed_by="security_agent",
                            gateway_policy_id=f"ratelimit-{api.id}" if success else None,
                            error_message=None if success else "Failed to apply policy",
                        )
                    )
                    
                elif "tls" in vulnerability.title.lower() or "https" in vulnerability.title.lower():
                    policy = {
                        "enforce_https": True,
                        "min_tls_version": "1.2",
                        "cipher_suites": ["TLS_AES_128_GCM_SHA256", "TLS_AES_256_GCM_SHA384"],
                        "hsts_enabled": True
                    }
                    success = await self.gateway_adapter.apply_tls_policy(
                        str(api.id), policy
                    )
                    actions.append(
                        RemediationAction(
                            action="Enforced HTTPS-only with TLS 1.2+ at gateway",
                            type="gateway_policy",
                            status="completed" if success else "failed",
                            performed_at=datetime.utcnow(),
                            performed_by="security_agent",
                            gateway_policy_id=f"tls-{api.id}" if success else None,
                            error_message=None if success else "Failed to apply policy",
                        )
                    )
                    
                elif "cors" in vulnerability.title.lower():
                    # Get base_path from API (now a top-level field)
                    base_path = api.base_path if hasattr(api, 'base_path') else "/"
                    policy = {
                        "allowed_origins": [base_path],
                        "allowed_methods": ["GET", "POST", "PUT", "DELETE"],
                        "allowed_headers": ["Content-Type", "Authorization"],
                        "expose_headers": [],
                        "max_age": 3600,
                        "allow_credentials": True
                    }
                    success = await self.gateway_adapter.apply_cors_policy(
                        str(api.id), policy
                    )
                    actions.append(
                        RemediationAction(
                            action="Applied secure CORS policy at gateway",
                            type="gateway_policy",
                            status="completed" if success else "failed",
                            performed_at=datetime.utcnow(),
                            performed_by="security_agent",
                            gateway_policy_id=f"cors-{api.id}" if success else None,
                            error_message=None if success else "Failed to apply policy",
                        )
                    )
                    
                elif "validation" in vulnerability.title.lower():
                    policy = {
                        "schema_validation": True,
                        "content_type_validation": True,
                        "size_limits": {"request": 10485760, "response": 10485760},
                        "sanitization_rules": ["strip_html", "escape_sql"]
                    }
                    success = await self.gateway_adapter.apply_validation_policy(
                        str(api.id), policy
                    )
                    actions.append(
                        RemediationAction(
                            action="Applied input validation policy at gateway",
                            type="gateway_policy",
                            status="completed" if success else "failed",
                            performed_at=datetime.utcnow(),
                            performed_by="security_agent",
                            gateway_policy_id=f"validation-{api.id}" if success else None,
                            error_message=None if success else "Failed to apply policy",
                        )
                    )
                    
                elif "security header" in vulnerability.title.lower():
                    policy = {
                        "hsts": "max-age=31536000; includeSubDomains",
                        "x_frame_options": "DENY",
                        "x_content_type_options": "nosniff",
                        "csp": "default-src 'self'",
                        "x_xss_protection": "1; mode=block"
                    }
                    success = await self.gateway_adapter.apply_security_headers_policy(
                        str(api.id), policy
                    )
                    actions.append(
                        RemediationAction(
                            action="Applied security headers policy at gateway",
                            type="gateway_policy",
                            status="completed" if success else "failed",
                            performed_at=datetime.utcnow(),
                            performed_by="security_agent",
                            gateway_policy_id=f"headers-{api.id}" if success else None,
                            error_message=None if success else "Failed to apply policy",
                        )
                    )

            return {
                "actions": actions,
                "applied_at": datetime.utcnow().isoformat(),
                "strategy_used": strategy or "default",
            }
            
        except Exception as e:
            logger.error(f"Remediation failed: {e}")
            actions.append(
                RemediationAction(
                    action=f"Failed to apply remediation: {str(e)}",
                    type="gateway_policy",
                    status="failed",
                    performed_at=datetime.utcnow(),
                    performed_by="security_agent",
                    gateway_policy_id=None,
                    error_message=str(e),
                )
            )
            return {
                "actions": actions,
                "applied_at": datetime.utcnow().isoformat(),
                "strategy_used": strategy or "default",
                "error": str(e),
            }

    async def _verify_vulnerability_fixed(
        self,
        api: API,
        vulnerability: Vulnerability,
    ) -> Dict[str, Any]:
        """Verify that a vulnerability has been fixed by re-scanning."""
        try:
            # Re-run security analysis for this specific API
            analysis_result = await self.security_agent.analyze_api_security(api)
            
            # Check if the same vulnerability still exists
            is_fixed = True
            for vuln_data in analysis_result.get("vulnerabilities", []):
                if isinstance(vuln_data, dict):
                    vuln = Vulnerability(**vuln_data)
                else:
                    vuln = vuln_data
                    
                # Check if same type and title (indicating same issue)
                if (vuln.vulnerability_type == vulnerability.vulnerability_type and
                    vuln.title == vulnerability.title):
                    is_fixed = False
                    break
            
            return {
                "vulnerability_id": str(vulnerability.id),
                "is_fixed": is_fixed,
                "verified_at": datetime.utcnow().isoformat(),
                "verification_method": "automated_rescan",
                "details": "Policy verified through re-scanning" if is_fixed else "Vulnerability still detected",
            }
            
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {
                "vulnerability_id": str(vulnerability.id),
                "is_fixed": False,
                "verified_at": datetime.utcnow().isoformat(),
                "verification_method": "automated_rescan",
                "details": f"Verification failed: {str(e)}",
                "error": str(e),
            }

    def _calculate_severity_breakdown(
        self,
        vulnerabilities: List[Vulnerability],
    ) -> Dict[str, int]:
        """Calculate severity breakdown from vulnerabilities."""
        breakdown = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0,
        }

        for vuln in vulnerabilities:
            severity = vuln.severity.value
            if severity in breakdown:
                breakdown[severity] += 1

        return breakdown

    def _calculate_risk_score(self, posture: Dict[str, Any]) -> int:
        """Calculate overall risk score (0-100, higher is worse)."""
        by_severity = posture.get("by_severity", {})
        
        # Weight by severity
        score = (
            by_severity.get("critical", 0) * 40 +
            by_severity.get("high", 0) * 25 +
            by_severity.get("medium", 0) * 15 +
            by_severity.get("low", 0) * 5
        )

        # Cap at 100
        return min(score, 100)

    def _get_risk_level(self, risk_score: int) -> str:
        """Get risk level from risk score."""
        if risk_score >= 75:
            return "critical"
        elif risk_score >= 50:
            return "high"
        elif risk_score >= 25:
            return "medium"
        else:
            return "low"

    def check_missing_security_policies(self, api: API) -> List[str]:
        """
        Check for missing security policies in API's policy_actions array.
        
        This method analyzes the vendor-neutral policy_actions to identify
        missing security policies that should be present.
        
        Args:
            api: API to check
            
        Returns:
            List of missing policy types
        """
        missing_policies = []
        
        # Get existing policy action types
        existing_types = set()
        if api.policy_actions:
            for policy_action in api.policy_actions:
                if policy_action.enabled:
                    existing_types.add(policy_action.action_type)
        
        # Check for required security policies
        required_policies = {
            PolicyActionType.AUTHENTICATION: "Authentication policy missing",
            PolicyActionType.AUTHORIZATION: "Authorization policy missing",
            PolicyActionType.TLS: "TLS/HTTPS enforcement missing",
            PolicyActionType.CORS: "CORS policy missing",
            PolicyActionType.VALIDATION: "Input validation policy missing",
        }
        
        for policy_type, message in required_policies.items():
            if policy_type not in existing_types:
                missing_policies.append(message)
        
        # Check for security headers (custom policy type)
        has_security_headers = False
        if api.policy_actions:
            for policy_action in api.policy_actions:
                if (policy_action.action_type == PolicyActionType.CUSTOM and
                    policy_action.enabled and
                    policy_action.config and
                    any(header in str(policy_action.config).lower()
                        for header in ['hsts', 'x-frame-options', 'x-content-type-options'])):
                    has_security_headers = True
                    break
        
        if not has_security_headers:
            missing_policies.append("Security headers policy missing")
        
        return missing_policies


# Made with Bob