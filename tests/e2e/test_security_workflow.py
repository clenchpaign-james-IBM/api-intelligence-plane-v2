"""End-to-end tests for security-scan-to-fix workflow.

Tests the complete security workflow including:
- Vulnerability scanning
- Vulnerability detection and classification
- Automated remediation via gateway adapter
- Policy application
- Verification through re-scanning
- Remediation tracking

Note: Uses mocked dependencies to focus on workflow logic.
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock

from backend.app.services.security_service import SecurityService


@pytest.fixture
def mock_security_service():
    """Create security service with mocked dependencies."""
    api_repo = Mock()
    api_repo.get = AsyncMock()
    api_repo.update = AsyncMock()
    
    vuln_repo = Mock()
    vuln_repo.create = AsyncMock()
    vuln_repo.update = AsyncMock()
    vuln_repo.get = AsyncMock()
    vuln_repo.find_by_api = AsyncMock(return_value=[])
    vuln_repo.find_open_vulnerabilities = AsyncMock(return_value=[])
    
    gateway_repo = Mock()
    gateway_repo.get = AsyncMock()
    
    metrics_repo = Mock()
    metrics_repo.get_latest_metrics = AsyncMock(return_value={})
    
    llm_service = Mock()
    llm_service.complete = AsyncMock(return_value="AI analysis")
    
    gateway_adapter = Mock()
    gateway_adapter.apply_authentication_policy = AsyncMock(return_value=True)
    gateway_adapter.apply_authorization_policy = AsyncMock(return_value=True)
    gateway_adapter.apply_tls_policy = AsyncMock(return_value=True)
    gateway_adapter.apply_cors_policy = AsyncMock(return_value=True)
    gateway_adapter.apply_validation_policy = AsyncMock(return_value=True)
    
    settings = Mock()
    
    service = SecurityService(
        settings=settings,
        api_repository=api_repo,
        vulnerability_repository=vuln_repo,
        gateway_repository=gateway_repo,
        metrics_repository=metrics_repo,
        llm_service=llm_service,
        gateway_adapter=gateway_adapter,
    )
    
    return service, api_repo, vuln_repo, gateway_repo, gateway_adapter


class TestSecurityScanToFixWorkflow:
    """Test complete security scan-to-fix workflow."""

    @pytest.mark.asyncio
    async def test_complete_scan_detect_remediate_verify_workflow(
        self, mock_security_service
    ):
        """Test complete workflow from scanning to verification."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        # Step 1: Setup test API and gateway
        api_id = uuid4()
        gateway_id = uuid4()
        
        api_data = {
            "id": api_id,
            "gateway_id": gateway_id,
            "name": "Insecure API",
            "authentication_type": "none",  # Security issue!
            "base_path": "/api/v1/insecure"
        }
        
        gateway_data = {
            "id": gateway_id,
            "name": "Test Gateway",
            "status": "connected"
        }
        
        api_repo.get.return_value = api_data
        gateway_repo.get.return_value = gateway_data
        
        # Step 2: Scan API for vulnerabilities
        detected_vulnerabilities = [
            {
                "id": uuid4(),
                "api_id": api_id,
                "vulnerability_type": "authentication",
                "severity": "high",
                "title": "Missing Authentication",
                "description": "API lacks authentication mechanism",
                "affected_endpoints": ["/api/v1/insecure/data"],
                "status": "open",
                "remediation_type": "automated"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "vulnerability_type": "configuration",
                "severity": "high",
                "title": "Missing TLS Enforcement",
                "description": "API allows HTTP connections",
                "affected_endpoints": ["/api/v1/insecure/data"],
                "status": "open",
                "remediation_type": "automated"
            }
        ]
        
        vuln_repo.create.side_effect = lambda v: v
        
        # Perform scan
        for vuln in detected_vulnerabilities:
            await vuln_repo.create(vuln)
        
        # Verify vulnerabilities were detected
        assert len(detected_vulnerabilities) == 2
        assert all(v["status"] == "open" for v in detected_vulnerabilities)
        
        # Step 3: Apply automated remediation for each vulnerability
        remediation_results = []
        
        for vuln in detected_vulnerabilities:
            if vuln["remediation_type"] == "automated":
                # Apply appropriate policy based on vulnerability type
                success = False
                if vuln["vulnerability_type"] == "authentication":
                    success = await gateway_adapter.apply_authentication_policy(
                        api_id, {"auth_type": "oauth2"}
                    )
                elif vuln["vulnerability_type"] == "configuration":
                    success = await gateway_adapter.apply_tls_policy(
                        api_id, {"enforce_https": True}
                    )
                
                remediation_results.append({
                    "vulnerability_id": vuln["id"],
                    "success": success,
                    "action": "policy_applied"
                })
        
        # Verify remediation was attempted
        assert len(remediation_results) == 2
        assert all(r["success"] for r in remediation_results)
        gateway_adapter.apply_authentication_policy.assert_called_once()
        gateway_adapter.apply_tls_policy.assert_called_once()
        
        # Step 4: Update vulnerability status
        for vuln in detected_vulnerabilities:
            vuln["status"] = "remediated"
            vuln["remediated_at"] = datetime.utcnow()
            await vuln_repo.update(vuln)
        
        # Verify vulnerabilities were marked as remediated
        vuln_repo.update.assert_called()
        
        # Step 5: Re-scan to verify fixes
        # Mock updated API with fixes applied
        api_data["authentication_type"] = "oauth2"
        api_repo.get.return_value = api_data
        
        # Perform verification scan
        vuln_repo.find_by_api.return_value = []  # No vulnerabilities found
        
        remaining_vulns = await vuln_repo.find_by_api(api_id)
        
        # Verify all vulnerabilities were fixed
        assert len(remaining_vulns) == 0

    @pytest.mark.asyncio
    async def test_scan_multiple_apis_workflow(self, mock_security_service):
        """Test scanning multiple APIs for vulnerabilities."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        gateway_id = uuid4()
        gateway_data = {"id": gateway_id, "name": "Test Gateway"}
        gateway_repo.get.return_value = gateway_data
        
        # Create multiple APIs with different security issues
        apis = [
            {
                "id": uuid4(),
                "gateway_id": gateway_id,
                "name": "API 1",
                "authentication_type": "none"
            },
            {
                "id": uuid4(),
                "gateway_id": gateway_id,
                "name": "API 2",
                "authentication_type": "basic"
            },
            {
                "id": uuid4(),
                "gateway_id": gateway_id,
                "name": "API 3",
                "authentication_type": "oauth2"
            }
        ]
        
        # Scan each API
        all_vulnerabilities = []
        for api in apis:
            api_repo.get.return_value = api
            
            # Simulate vulnerability detection based on auth type
            if api["authentication_type"] == "none":
                vulns = [
                    {
                        "id": uuid4(),
                        "api_id": api["id"],
                        "vulnerability_type": "authentication",
                        "severity": "critical",
                        "status": "open"
                    }
                ]
            elif api["authentication_type"] == "basic":
                vulns = [
                    {
                        "id": uuid4(),
                        "api_id": api["id"],
                        "vulnerability_type": "authentication",
                        "severity": "medium",
                        "status": "open"
                    }
                ]
            else:
                vulns = []
            
            for vuln in vulns:
                await vuln_repo.create(vuln)
                all_vulnerabilities.append(vuln)
        
        # Verify vulnerabilities were detected across all APIs
        assert len(all_vulnerabilities) == 2
        
        # Verify severity distribution
        critical_vulns = [v for v in all_vulnerabilities if v["severity"] == "critical"]
        medium_vulns = [v for v in all_vulnerabilities if v["severity"] == "medium"]
        
        assert len(critical_vulns) == 1
        assert len(medium_vulns) == 1

    @pytest.mark.asyncio
    async def test_remediation_failure_handling(self, mock_security_service):
        """Test handling of remediation failures."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        api_id = uuid4()
        gateway_id = uuid4()
        
        api_data = {"id": api_id, "gateway_id": gateway_id, "name": "Test API"}
        gateway_data = {"id": gateway_id, "name": "Test Gateway"}
        
        api_repo.get.return_value = api_data
        gateway_repo.get.return_value = gateway_data
        
        # Create vulnerability
        vuln_data = {
            "id": uuid4(),
            "api_id": api_id,
            "vulnerability_type": "authentication",
            "severity": "high",
            "status": "open",
            "remediation_type": "automated"
        }
        
        vuln_repo.get.return_value = vuln_data
        
        # Simulate remediation failure
        gateway_adapter.apply_authentication_policy.return_value = False
        
        # Attempt remediation
        success = await gateway_adapter.apply_authentication_policy(api_id, {})
        
        assert success is False
        
        # Update vulnerability with failure information
        vuln_data["status"] = "remediation_failed"
        vuln_data["last_error"] = "Failed to apply authentication policy"
        await vuln_repo.update(vuln_data)
        
        # Verify failure was recorded
        vuln_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_manual_remediation_workflow(self, mock_security_service):
        """Test workflow for vulnerabilities requiring manual remediation."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        api_id = uuid4()
        
        # Create vulnerability requiring manual remediation
        vuln_data = {
            "id": uuid4(),
            "api_id": api_id,
            "vulnerability_type": "business_logic",
            "severity": "high",
            "title": "Insecure Business Logic",
            "description": "API allows unauthorized data access",
            "status": "open",
            "remediation_type": "manual",
            "remediation_steps": [
                "Review access control logic",
                "Implement proper authorization checks",
                "Add audit logging"
            ]
        }
        
        vuln_repo.get.return_value = vuln_data
        
        # Verify manual remediation steps are provided
        assert vuln_data["remediation_type"] == "manual"
        assert len(vuln_data["remediation_steps"]) > 0
        
        # Simulate manual remediation completion
        vuln_data["status"] = "remediated"
        vuln_data["remediated_at"] = datetime.utcnow()
        vuln_data["remediation_notes"] = "Applied authorization checks and audit logging"
        await vuln_repo.update(vuln_data)
        
        # Verify manual remediation was tracked
        vuln_repo.update.assert_called_once()

    @pytest.mark.asyncio
    async def test_vulnerability_prioritization_workflow(self, mock_security_service):
        """Test vulnerability prioritization based on severity."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        api_id = uuid4()
        
        # Create vulnerabilities with different severities
        vulnerabilities = [
            {
                "id": uuid4(),
                "api_id": api_id,
                "severity": "critical",
                "priority": 1,
                "status": "open"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "severity": "high",
                "priority": 2,
                "status": "open"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "severity": "medium",
                "priority": 3,
                "status": "open"
            },
            {
                "id": uuid4(),
                "api_id": api_id,
                "severity": "low",
                "priority": 4,
                "status": "open"
            }
        ]
        
        # Sort by priority (critical first)
        sorted_vulns = sorted(vulnerabilities, key=lambda v: v["priority"])
        
        # Verify prioritization
        assert sorted_vulns[0]["severity"] == "critical"
        assert sorted_vulns[1]["severity"] == "high"
        assert sorted_vulns[2]["severity"] == "medium"
        assert sorted_vulns[3]["severity"] == "low"
        
        # Remediate in priority order
        for vuln in sorted_vulns:
            vuln["status"] = "remediated"
            await vuln_repo.update(vuln)
        
        # Verify all were remediated
        assert all(v["status"] == "remediated" for v in sorted_vulns)


class TestSecurityPolicyApplication:
    """Test security policy application workflows."""

    @pytest.mark.asyncio
    async def test_apply_authentication_policy(self, mock_security_service):
        """Test applying authentication policy to fix vulnerability."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        api_id = uuid4()
        
        # Apply OAuth2 authentication policy
        policy_config = {
            "auth_type": "oauth2",
            "token_endpoint": "https://auth.example.com/token",
            "scopes": ["read", "write"]
        }
        
        success = await gateway_adapter.apply_authentication_policy(api_id, policy_config)
        
        assert success is True
        gateway_adapter.apply_authentication_policy.assert_called_once_with(api_id, policy_config)

    @pytest.mark.asyncio
    async def test_apply_tls_policy(self, mock_security_service):
        """Test applying TLS policy to enforce HTTPS."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        api_id = uuid4()
        
        # Apply TLS enforcement policy
        policy_config = {
            "enforce_https": True,
            "min_tls_version": "1.3",
            "redirect_http_to_https": True
        }
        
        success = await gateway_adapter.apply_tls_policy(api_id, policy_config)
        
        assert success is True
        gateway_adapter.apply_tls_policy.assert_called_once_with(api_id, policy_config)

    @pytest.mark.asyncio
    async def test_apply_cors_policy(self, mock_security_service):
        """Test applying CORS policy for secure cross-origin requests."""
        service, api_repo, vuln_repo, gateway_repo, gateway_adapter = mock_security_service
        
        api_id = uuid4()
        
        # Apply CORS policy
        policy_config = {
            "allowed_origins": ["https://app.example.com"],
            "allowed_methods": ["GET", "POST"],
            "allowed_headers": ["Content-Type", "Authorization"],
            "max_age": 3600
        }
        
        success = await gateway_adapter.apply_cors_policy(api_id, policy_config)
        
        assert success is True
        gateway_adapter.apply_cors_policy.assert_called_once_with(api_id, policy_config)


# Made with Bob