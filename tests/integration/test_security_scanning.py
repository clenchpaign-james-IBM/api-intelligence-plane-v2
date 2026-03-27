"""Integration tests for security scanning functionality.

Tests the complete security scanning workflow including:
- API security scanning
- Vulnerability detection
- AI-enhanced analysis
- Security posture calculation
"""

import pytest
import asyncio
from datetime import datetime
from uuid import uuid4

from backend.app.services.security_service import SecurityService
from backend.app.services.llm_service import LLMService
from backend.app.db.repositories.api_repository import APIRepository
from backend.app.db.repositories.gateway_repository import GatewayRepository
from backend.app.db.repositories.metrics_repository import MetricsRepository
from backend.app.db.repositories.vulnerability_repository import VulnerabilityRepository
from backend.app.models.api import API, Endpoint, AuthenticationType, DiscoveryMethod, APIStatus
from backend.app.models.gateway import Gateway, GatewayVendor, ConnectionType, GatewayStatus
from backend.app.models.metric import Metric
from backend.app.models.vulnerability import VulnerabilityStatus


@pytest.fixture
def test_api():
    """Create a test API with security issues."""
    return API(
        id=str(uuid4()),
        gateway_id=str(uuid4()),
        name="Test Insecure API",
        version="1.0.0",
        base_path="/api/v1/test",
        endpoints=[
            Endpoint(
                path="/users",
                method="GET",
                description="Get users",
                parameters=[],
                response_codes=[200, 401, 500],
            ),
            Endpoint(
                path="/users/{id}",
                method="DELETE",
                description="Delete user",
                parameters=[],
                response_codes=[204, 401, 403, 500],
            ),
        ],
        methods=["GET", "DELETE"],
        authentication_type=AuthenticationType.NONE,  # Security issue!
        authentication_config=None,
        ownership=None,
        tags=["test", "insecure"],
        is_shadow=False,
        discovery_method=DiscoveryMethod.REGISTERED,
        discovered_at=datetime.utcnow().isoformat(),
        last_seen_at=datetime.utcnow().isoformat(),
        status=APIStatus.ACTIVE,
        health_score=75.0,
        current_metrics={
            "response_time_p50": 150.0,
            "response_time_p95": 300.0,
            "response_time_p99": 500.0,
            "error_rate": 0.05,
            "throughput": 100.0,
            "availability": 0.99,
            "measured_at": datetime.utcnow().isoformat(),
        },
        metadata={},
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def test_gateway():
    """Create a test gateway."""
    return Gateway(
        id=str(uuid4()),
        name="Test Gateway",
        vendor=GatewayVendor.NATIVE,
        version="1.0.0",
        connection_url="http://localhost:8080",
        connection_type=ConnectionType.REST,
        credentials={"type": "none"},
        capabilities=["discovery", "metrics", "security"],
        status=GatewayStatus.CONNECTED,
        last_connected_at=datetime.utcnow().isoformat(),
        api_count=1,
        metrics_enabled=True,
        security_scanning_enabled=True,
        rate_limiting_enabled=True,
        configuration={},
        metadata={},
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )


@pytest.fixture
def test_metrics(test_api):
    """Create test metrics with security indicators."""
    metrics = []
    
    # Add metrics showing high 401 rate (authentication issues)
    for i in range(10):
        metric = Metric(
            id=str(uuid4()),
            api_id=test_api.id,
            timestamp=datetime.utcnow().isoformat(),
            request_count=1000,
            error_count=50,  # 5% error rate
            response_time_p50=150.0,
            response_time_p95=300.0,
            response_time_p99=500.0,
            status_codes={
                "200": 850,
                "401": 100,  # High 401 rate - authentication issue
                "403": 20,   # Some 403s - authorization issue
                "500": 30,
            },
            throughput=100.0,
            error_rate=0.05,
            availability=0.95,
            metadata={},
            created_at=datetime.utcnow().isoformat(),
        )
        metrics.append(metric)
    
    return metrics


@pytest.mark.asyncio
async def test_security_scan_basic(opensearch_client, test_api, test_gateway, test_metrics):
    """Test basic security scanning without AI enhancement."""
    # Setup repositories
    api_repo = APIRepository(opensearch_client)
    gateway_repo = GatewayRepository(opensearch_client)
    metrics_repo = MetricsRepository(opensearch_client)
    vuln_repo = VulnerabilityRepository(opensearch_client)
    llm_service = LLMService()
    
    # Create security service
    security_service = SecurityService(
        api_repository=api_repo,
        gateway_repository=gateway_repo,
        metrics_repository=metrics_repo,
        vulnerability_repository=vuln_repo,
        llm_service=llm_service,
    )
    
    # Store test data
    api_repo.create(test_api)
    gateway_repo.create(test_gateway)
    for metric in test_metrics:
        metrics_repo.create(metric)
    
    # Wait for indexing
    await asyncio.sleep(2)
    
    # Perform security scan without AI
    result = await security_service.scan_api_security(
        api_id=test_api.id,
        use_ai_enhancement=False,
    )
    
    # Verify scan results
    assert result["api_id"] == test_api.id
    assert result["api_name"] == test_api.name
    assert result["vulnerabilities_found"] > 0
    assert "severity_breakdown" in result
    assert "vulnerabilities" in result
    assert "remediation_plan" in result
    assert result["ai_enhanced"] is False
    
    # Verify vulnerabilities were detected
    vulnerabilities = result["vulnerabilities"]
    assert len(vulnerabilities) > 0
    
    # Should detect missing authentication
    auth_vulns = [v for v in vulnerabilities if v["category"] == "authentication"]
    assert len(auth_vulns) > 0
    
    # Verify vulnerability was stored
    stored_vulns = vuln_repo.find_by_api_id(test_api.id)
    assert len(stored_vulns) > 0


@pytest.mark.asyncio
async def test_security_scan_with_ai(opensearch_client, test_api, test_gateway, test_metrics):
    """Test security scanning with AI enhancement."""
    # Setup repositories
    api_repo = APIRepository(opensearch_client)
    gateway_repo = GatewayRepository(opensearch_client)
    metrics_repo = MetricsRepository(opensearch_client)
    vuln_repo = VulnerabilityRepository(opensearch_client)
    llm_service = LLMService()
    
    # Create security service
    security_service = SecurityService(
        api_repository=api_repo,
        gateway_repository=gateway_repo,
        metrics_repository=metrics_repo,
        vulnerability_repository=vuln_repo,
        llm_service=llm_service,
    )
    
    # Store test data
    api_repo.create(test_api)
    gateway_repo.create(test_gateway)
    for metric in test_metrics:
        metrics_repo.create(metric)
    
    # Wait for indexing
    await asyncio.sleep(2)
    
    # Perform security scan with AI
    result = await security_service.scan_api_security(
        api_id=test_api.id,
        use_ai_enhancement=True,
    )
    
    # Verify scan results
    assert result["api_id"] == test_api.id
    assert result["vulnerabilities_found"] > 0
    assert result["ai_enhanced"] is True
    
    # AI-enhanced scan should provide more detailed analysis
    vulnerabilities = result["vulnerabilities"]
    for vuln in vulnerabilities:
        assert "title" in vuln
        assert "description" in vuln
        assert "severity" in vuln
        assert "remediation" in vuln


@pytest.mark.asyncio
async def test_security_posture_calculation(opensearch_client, test_api, test_gateway):
    """Test security posture calculation."""
    # Setup repositories
    api_repo = APIRepository(opensearch_client)
    gateway_repo = GatewayRepository(opensearch_client)
    metrics_repo = MetricsRepository(opensearch_client)
    vuln_repo = VulnerabilityRepository(opensearch_client)
    llm_service = LLMService()
    
    # Create security service
    security_service = SecurityService(
        api_repository=api_repo,
        gateway_repository=gateway_repo,
        metrics_repository=metrics_repo,
        vulnerability_repository=vuln_repo,
        llm_service=llm_service,
    )
    
    # Store test data
    api_repo.create(test_api)
    gateway_repo.create(test_gateway)
    
    # Wait for indexing
    await asyncio.sleep(2)
    
    # Scan API to create vulnerabilities
    await security_service.scan_api_security(
        api_id=test_api.id,
        use_ai_enhancement=False,
    )
    
    # Wait for vulnerability indexing
    await asyncio.sleep(2)
    
    # Get security posture
    posture = await security_service.get_security_posture()
    
    # Verify posture metrics
    assert "total_vulnerabilities" in posture
    assert "by_severity" in posture
    assert "by_status" in posture
    assert "by_type" in posture
    assert "remediation_rate" in posture
    assert "risk_score" in posture
    assert "risk_level" in posture
    
    assert posture["total_vulnerabilities"] > 0
    assert 0 <= posture["risk_score"] <= 100
    assert posture["risk_level"] in ["low", "medium", "high", "critical"]


@pytest.mark.asyncio
async def test_vulnerability_filtering(opensearch_client, test_api, test_gateway):
    """Test vulnerability filtering by severity and status."""
    # Setup repositories
    api_repo = APIRepository(opensearch_client)
    gateway_repo = GatewayRepository(opensearch_client)
    metrics_repo = MetricsRepository(opensearch_client)
    vuln_repo = VulnerabilityRepository(opensearch_client)
    llm_service = LLMService()
    
    # Create security service
    security_service = SecurityService(
        api_repository=api_repo,
        gateway_repository=gateway_repo,
        metrics_repository=metrics_repo,
        vulnerability_repository=vuln_repo,
        llm_service=llm_service,
    )
    
    # Store test data
    api_repo.create(test_api)
    gateway_repo.create(test_gateway)
    
    # Wait for indexing
    await asyncio.sleep(2)
    
    # Scan API to create vulnerabilities
    await security_service.scan_api_security(
        api_id=test_api.id,
        use_ai_enhancement=False,
    )
    
    # Wait for vulnerability indexing
    await asyncio.sleep(2)
    
    # Test filtering by API ID
    api_vulns = await security_service.get_vulnerabilities(api_id=test_api.id)
    assert len(api_vulns) > 0
    assert all(v.api_id == test_api.id for v in api_vulns)
    
    # Test filtering by status
    open_vulns = await security_service.get_vulnerabilities(status=VulnerabilityStatus.OPEN)
    assert len(open_vulns) > 0
    assert all(v.status == VulnerabilityStatus.OPEN for v in open_vulns)
    
    # Test filtering by severity
    critical_vulns = await security_service.get_vulnerabilities(severity="critical")
    # May or may not have critical vulnerabilities depending on API config


# Made with Bob