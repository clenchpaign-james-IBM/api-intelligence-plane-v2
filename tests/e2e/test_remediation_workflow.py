"""End-to-end tests for security remediation workflow.

Tests the complete remediation workflow including:
- Vulnerability detection
- Automated remediation via Gateway adapter
- Policy application to Demo Gateway
- Verification through re-scanning
"""

import pytest
from datetime import datetime
from uuid import uuid4
from unittest.mock import Mock, AsyncMock, patch

from backend.app.services.security_service import SecurityService
from backend.app.agents.security_agent import SecurityAgent
from backend.app.models.api import API, AuthenticationType, Endpoint, DiscoveryMethod, APIStatus
from backend.app.models.gateway import Gateway, GatewayType, GatewayCredentials
from backend.app.models.vulnerability import (
    Vulnerability,
    VulnerabilityType,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    DetectionMethod,
    RemediationType,
)
from backend.app.adapters.native_gateway import NativeGatewayAdapter
from backend.app.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings(
        OPENSEARCH_HOST="localhost",
        OPENSEARCH_PORT=9200,
        LLM_PROVIDER="openai",
        LLM_MODEL="gpt-4",
    )


@pytest.fixture
def sample_gateway():
    """Create a sample gateway."""
    return Gateway(
        id=uuid4(),
        name="Test Gateway",
        type=GatewayType.NATIVE,
        connection_url="http://localhost:8080",
        credentials=GatewayCredentials(
            api_key="test-key",
        ),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_api(sample_gateway):
    """Create a sample API with security issues."""
    return API(
        id=uuid4(),
        gateway_id=sample_gateway.id,
        name="Insecure API",
        version="v1",
        base_path="/api/v1/insecure",
        endpoints=[
            Endpoint(
                path="/api/v1/insecure/data",
                method="GET",
                description="Get sensitive data",
            ),
        ],
        methods=["GET"],
        authentication_type=AuthenticationType.NONE,  # Security issue!
        tags=["test"],
        is_shadow=False,
        discovery_method=DiscoveryMethod.REGISTERED,
        discovered_at=datetime.utcnow(),
        last_seen_at=datetime.utcnow(),
        status=APIStatus.ACTIVE,
        health_score=50.0,
    )


@pytest.fixture
def mock_gateway_adapter():
    """Create mock gateway adapter."""
    adapter = Mock(spec=NativeGatewayAdapter)
    adapter.connect = AsyncMock(return_value=True)
    adapter.apply_authentication_policy = AsyncMock(return_value=True)
    adapter.apply_authorization_policy = AsyncMock(return_value=True)
    adapter.apply_tls_policy = AsyncMock(return_value=True)
    adapter.apply_cors_policy = AsyncMock(return_value=True)
    adapter.apply_validation_policy = AsyncMock(return_value=True)
    adapter.apply_security_headers_policy = AsyncMock(return_value=True)
    adapter.apply_rate_limit_policy = AsyncMock(return_value=True)
    return adapter


@pytest.fixture
def security_service_with_adapter(
    settings,
    mock_gateway_adapter,
):
    """Create security service with mocked gateway adapter."""
    api_repo = Mock()
    api_repo.get = AsyncMock()
    
    vuln_repo = Mock()
    vuln_repo.create = AsyncMock()
    vuln_repo.update = AsyncMock()
    vuln_repo.get_by_api = AsyncMock(return_value=[])
    
    gateway_repo = Mock()
    gateway_repo.get = AsyncMock()
    
    metrics_repo = Mock()
    metrics_repo.get_latest_metrics = AsyncMock(return_value={})
    
    llm_service = Mock()
    llm_service.complete = AsyncMock(return_value="AI analysis")
    
    security_agent = SecurityAgent(llm_service, metrics_repo)
    
    service = SecurityService(
        settings=settings,
        api_repository=api_repo,
        vulnerability_repository=vuln_repo,
        llm_service=llm_service,
        security_agent=security_agent,
        metrics_repository=metrics_repo,
        gateway_repository=gateway_repo,
        gateway_adapter=mock_gateway_adapter,
    )
    
    return service, api_repo, vuln_repo, gateway_repo


class TestRemediationWorkflow:
    """Test complete remediation workflow."""

    @pytest.mark.asyncio
    async def test_detect_and_remediate_authentication_issue(
        self, sample_api, sample_gateway, security_service_with_adapter, mock_gateway_adapter
    ):
        """Test detecting and remediating authentication vulnerability."""
        service, api_repo, vuln_repo, gateway_repo = security_service_with_adapter
        
        api_repo.get.return_value = sample_api
        gateway_repo.get.return_value = sample_gateway
        
        # Step 1: Scan API and detect vulnerability
        scan_result = await service.scan_api_security(sample_api.id)
        
        assert scan_result is not None
        assert "vulnerabilities" in scan_result
        
        # Find authentication vulnerability
        auth_vulns = [
            v for v in scan_result["vulnerabilities"]
            if v.vulnerability_type == VulnerabilityType.AUTHENTICATION
        ]
        assert len(auth_vulns) > 0
        
        vulnerability = auth_vulns[0]
        
        # Step 2: Apply automated remediation
        remediation_result = await service.remediate_vulnerability(
            vulnerability.id,
            strategy="automated"
        )
        
        assert remediation_result is not None
        assert "actions" in remediation_result
        assert len(remediation_result["actions"]) > 0
        
        # Verify gateway adapter was called
        mock_gateway_adapter.apply_authentication_policy.assert_called_once()
        
        # Step 3: Verify vulnerability was fixed
        verification_result = await service.verify_remediation(
            vulnerability.id
        )
        
        assert verification_result is not None
        assert verification_result.get("is_fixed") is True

    @pytest.mark.asyncio
    async def test_remediate_multiple_vulnerabilities(
        self, sample_api, sample_gateway, security_service_with_adapter, mock_gateway_adapter
    ):
        """Test remediating multiple vulnerabilities."""
        service, api_repo, vuln_repo, gateway_repo = security_service_with_adapter
        
        api_repo.get.return_value = sample_api
        gateway_repo.get.return_value = sample_gateway
        
        # Scan API
        scan_result = await service.scan_api_security(sample_api.id)
        
        assert scan_result is not None
        vulnerabilities = scan_result["vulnerabilities"]
        
        # Remediate all vulnerabilities
        remediation_results = []
        for vuln in vulnerabilities:
            if vuln.remediation_type == RemediationType.AUTOMATED:
                result = await service.remediate_vulnerability(
                    vuln.id,
                    strategy="automated"
                )
                remediation_results.append(result)
        
        assert len(remediation_results) > 0
        
        # Verify all remediations were attempted
        for result in remediation_results:
            assert "actions" in result
            assert len(result["actions"]) > 0

    @pytest.mark.asyncio
    async def test_remediation_failure_handling(
        self, sample_api, sample_gateway, security_service_with_adapter, mock_gateway_adapter
    ):
        """Test handling of remediation failures."""
        service, api_repo, vuln_repo, gateway_repo = security_service_with_adapter
        
        api_repo.get.return_value = sample_api
        gateway_repo.get.return_value = sample_gateway
        
        # Make gateway adapter fail
        mock_gateway_adapter.apply_authentication_policy.return_value = False
        
        # Scan API
        scan_result = await service.scan_api_security(sample_api.id)
        
        auth_vulns = [
            v for v in scan_result["vulnerabilities"]
            if v.vulnerability_type == VulnerabilityType.AUTHENTICATION
        ]
        vulnerability = auth_vulns[0]
        
        # Attempt remediation
        remediation_result = await service.remediate_vulnerability(
            vulnerability.id,
            strategy="automated"
        )
        
        assert remediation_result is not None
        assert "actions" in remediation_result
        
        # Check that failure was recorded
        action = remediation_result["actions"][0]
        assert action.status == "failed"
        assert action.error_message is not None


class TestPolicyApplication:
    """Test policy application to Gateway."""

    @pytest.mark.asyncio
    async def test_apply_authentication_policy(
        self, sample_api, sample_gateway, security_service_with_adapter, mock_gateway_adapter
    ):
        """Test applying authentication policy."""
        service, api_repo, vuln_repo, gateway_repo = security_service_with_adapter
        
        api_repo.get.return_value = sample_api
        gateway_repo.get.return_value = sample_gateway
        
        # Create authentication vulnerability
        vulnerability = Vulnerability(
            id=uuid4(),
            api_id=sample_api.id,
            vulnerability_type=VulnerabilityType.AUTHENTICATION,
            severity=VulnerabilitySeverity.HIGH,
            title="Missing Authentication",
            description="API lacks authentication",
            affected_endpoints=["/api/v1/insecure/data"],
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            detected_at=datetime.utcnow(),
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.AUTOMATED,
        )
        
        # Apply remediation
        result = await service._apply_automated_remediation(
            sample_api,
            vulnerability,
            strategy="automated"
        )
        
        assert result is not None
        assert "actions" in result
        
        # Verify policy was applied
        mock_gateway_adapter.apply_authentication_policy.assert_called_once()
        call_args = mock_gateway_adapter.apply_authentication_policy.call_args
        
        # Check policy configuration
        policy = call_args[0][1]
        assert "auth_type" in policy
        assert policy["auth_type"] == "oauth2"

    @pytest.mark.asyncio
    async def test_apply_tls_policy(
        self, sample_api, sample_gateway, security_service_with_adapter, mock_gateway_adapter
    ):
        """Test applying TLS policy."""
        service, api_repo, vuln_repo, gateway_repo = security_service_with_adapter
        
        api_repo.get.return_value = sample_api
        gateway_repo.get.return_value = sample_gateway
        
        # Create TLS vulnerability
        vulnerability = Vulnerability(
            id=uuid4(),
            api_id=sample_api.id,
            vulnerability_type=VulnerabilityType.CONFIGURATION,
            severity=VulnerabilitySeverity.HIGH,
            title="Missing TLS Enforcement",
            description="API allows HTTP connections",
            affected_endpoints=["/api/v1/insecure/data"],
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            detected_at=datetime.utcnow(),
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.AUTOMATED,
        )
        
        # Apply remediation
        result = await service._apply_automated_remediation(
            sample_api,
            vulnerability,
            strategy="automated"
        )
        
        assert result is not None
        
        # Verify TLS policy was applied
        mock_gateway_adapter.apply_tls_policy.assert_called_once()
        call_args = mock_gateway_adapter.apply_tls_policy.call_args
        
        # Check policy configuration
        policy = call_args[0][1]
        assert "enforce_https" in policy
        assert policy["enforce_https"] is True


class TestVerification:
    """Test remediation verification."""

    @pytest.mark.asyncio
    async def test_verify_successful_remediation(
        self, sample_api, sample_gateway, security_service_with_adapter
    ):
        """Test verification of successful remediation."""
        service, api_repo, vuln_repo, gateway_repo = security_service_with_adapter
        
        # Create API with authentication (fixed)
        fixed_api = API(
            id=sample_api.id,
            gateway_id=sample_api.gateway_id,
            name=sample_api.name,
            version=sample_api.version,
            base_path=sample_api.base_path,
            endpoints=sample_api.endpoints,
            methods=sample_api.methods,
            authentication_type=AuthenticationType.OAUTH2,  # Fixed!
            tags=sample_api.tags,
            is_shadow=sample_api.is_shadow,
            discovery_method=sample_api.discovery_method,
            discovered_at=sample_api.discovered_at,
            last_seen_at=sample_api.last_seen_at,
            status=sample_api.status,
            health_score=sample_api.health_score,
        )
        
        api_repo.get.return_value = fixed_api
        gateway_repo.get.return_value = sample_gateway
        
        # Create vulnerability
        vulnerability = Vulnerability(
            id=uuid4(),
            api_id=sample_api.id,
            vulnerability_type=VulnerabilityType.AUTHENTICATION,
            severity=VulnerabilitySeverity.HIGH,
            title="Missing Authentication",
            description="API lacks authentication",
            affected_endpoints=["/api/v1/insecure/data"],
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            detected_at=datetime.utcnow(),
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.AUTOMATED,
        )
        
        # Verify remediation
        result = await service._verify_vulnerability_fixed(
            fixed_api,
            vulnerability
        )
        
        assert result is not None
        assert result["is_fixed"] is True
        assert "verified_at" in result


# Made with Bob