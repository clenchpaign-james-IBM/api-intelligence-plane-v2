"""Integration tests for security summary endpoints.

Tests the security summary aggregation functionality across:
- Global security summary (all gateways)
- Gateway-filtered security summary
- Gateway-specific security summary endpoint
"""

import pytest
from uuid import uuid4

from app.models.vulnerability import (
    DetectionMethod,
    RemediationType,
    Vulnerability,
    VulnerabilitySeverity,
    VulnerabilityStatus,
    VulnerabilityType,
)


@pytest.mark.asyncio
async def test_global_security_summary_empty(client, vulnerability_repository):
    """Test global security summary with no vulnerabilities."""
    response = await client.get("/api/v1/security/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_vulnerabilities"] == 0
    assert data["critical_vulnerabilities"] == 0
    assert data["high_vulnerabilities"] == 0
    assert data["medium_vulnerabilities"] == 0
    assert data["low_vulnerabilities"] == 0


@pytest.mark.asyncio
async def test_global_security_summary_with_data(
    client, gateway_fixture, api_fixture, vulnerability_repository
):
    """Test global security summary with vulnerability data."""
    # Create test vulnerabilities with different severities
    vulnerabilities = [
        Vulnerability(
            gateway_id=gateway_fixture.id,
            api_id=api_fixture.id,
            vulnerability_type=VulnerabilityType.AUTHENTICATION,
            severity=VulnerabilitySeverity.CRITICAL,
            title="Critical Auth Issue",
            description="Critical authentication vulnerability",
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.AUTOMATED,
        ),
        Vulnerability(
            gateway_id=gateway_fixture.id,
            api_id=api_fixture.id,
            vulnerability_type=VulnerabilityType.AUTHORIZATION,
            severity=VulnerabilitySeverity.HIGH,
            title="High Authz Issue",
            description="High severity authorization vulnerability",
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.AUTOMATED,
        ),
        Vulnerability(
            gateway_id=gateway_fixture.id,
            api_id=api_fixture.id,
            vulnerability_type=VulnerabilityType.CONFIGURATION,
            severity=VulnerabilitySeverity.MEDIUM,
            title="Medium Config Issue",
            description="Medium severity configuration vulnerability",
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.MANUAL,
        ),
        Vulnerability(
            gateway_id=gateway_fixture.id,
            api_id=api_fixture.id,
            vulnerability_type=VulnerabilityType.EXPOSURE,
            severity=VulnerabilitySeverity.LOW,
            title="Low Exposure Issue",
            description="Low severity exposure vulnerability",
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.MANUAL,
        ),
    ]
    
    # Store vulnerabilities
    for vuln in vulnerabilities:
        vulnerability_repository.create(vuln)
    
    # Wait for indexing
    import asyncio
    await asyncio.sleep(1)
    
    # Test global summary
    response = await client.get("/api/v1/security/summary")
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_vulnerabilities"] == 4
    assert data["critical_vulnerabilities"] == 1
    assert data["high_vulnerabilities"] == 1
    assert data["medium_vulnerabilities"] == 1
    assert data["low_vulnerabilities"] == 1


@pytest.mark.asyncio
async def test_gateway_filtered_security_summary(
    client, gateway_fixture, api_fixture, vulnerability_repository
):
    """Test global security summary with gateway filter."""
    # Create vulnerability for specific gateway
    vuln = Vulnerability(
        gateway_id=gateway_fixture.id,
        api_id=api_fixture.id,
        vulnerability_type=VulnerabilityType.AUTHENTICATION,
        severity=VulnerabilitySeverity.CRITICAL,
        title="Gateway-specific vulnerability",
        description="Vulnerability for specific gateway",
        detection_method=DetectionMethod.AUTOMATED_SCAN,
        status=VulnerabilityStatus.OPEN,
        remediation_type=RemediationType.AUTOMATED,
    )
    
    vulnerability_repository.create(vuln)
    
    # Wait for indexing
    import asyncio
    await asyncio.sleep(1)
    
    # Test with gateway filter
    response = await client.get(
        "/api/v1/security/summary",
        params={"gateway_id": str(gateway_fixture.id)}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_vulnerabilities"] >= 1
    assert data["critical_vulnerabilities"] >= 1


@pytest.mark.asyncio
async def test_gateway_specific_security_summary(
    client, gateway_fixture, api_fixture, vulnerability_repository
):
    """Test gateway-specific security summary endpoint."""
    # Create vulnerabilities for gateway
    vulnerabilities = [
        Vulnerability(
            gateway_id=gateway_fixture.id,
            api_id=api_fixture.id,
            vulnerability_type=VulnerabilityType.AUTHENTICATION,
            severity=VulnerabilitySeverity.CRITICAL,
            title=f"Vulnerability {i}",
            description=f"Test vulnerability {i}",
            detection_method=DetectionMethod.AUTOMATED_SCAN,
            status=VulnerabilityStatus.OPEN,
            remediation_type=RemediationType.AUTOMATED,
        )
        for i in range(3)
    ]
    
    for vuln in vulnerabilities:
        vulnerability_repository.create(vuln)
    
    # Wait for indexing
    import asyncio
    await asyncio.sleep(1)
    
    # Test gateway-specific endpoint
    response = await client.get(
        f"/api/v1/gateways/{gateway_fixture.id}/security/summary"
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert "gateway_id" in data
    assert data["gateway_id"] == str(gateway_fixture.id)
    assert data["total_vulnerabilities"] >= 3
    assert data["critical_vulnerabilities"] >= 3


@pytest.mark.asyncio
async def test_security_summary_multiple_gateways(
    client, gateway_repository, api_repository, vulnerability_repository
):
    """Test that gateway filter correctly isolates vulnerabilities."""
    from app.models.base.gateway import Gateway
    from app.models.base.api import API
    
    # Create two gateways
    gateway1 = Gateway(
        name="Gateway 1",
        type="webmethods",
        base_url="http://gateway1.example.com",
        version="10.15"
    )
    gateway2 = Gateway(
        name="Gateway 2",
        type="kong",
        base_url="http://gateway2.example.com",
        version="3.0"
    )
    
    gateway_repository.create(gateway1)
    gateway_repository.create(gateway2)
    
    # Create APIs for each gateway
    api1 = API(
        gateway_id=gateway1.id,
        name="API 1",
        version="1.0",
        type="REST"
    )
    api2 = API(
        gateway_id=gateway2.id,
        name="API 2",
        version="1.0",
        type="REST"
    )
    
    api_repository.create(api1)
    api_repository.create(api2)
    
    # Create vulnerabilities for each gateway
    vuln1 = Vulnerability(
        gateway_id=gateway1.id,
        api_id=api1.id,
        vulnerability_type=VulnerabilityType.AUTHENTICATION,
        severity=VulnerabilitySeverity.CRITICAL,
        title="Gateway 1 vulnerability",
        description="Vulnerability in gateway 1",
        detection_method=DetectionMethod.AUTOMATED_SCAN,
        status=VulnerabilityStatus.OPEN,
        remediation_type=RemediationType.AUTOMATED,
    )
    
    vuln2 = Vulnerability(
        gateway_id=gateway2.id,
        api_id=api2.id,
        vulnerability_type=VulnerabilityType.AUTHORIZATION,
        severity=VulnerabilitySeverity.HIGH,
        title="Gateway 2 vulnerability",
        description="Vulnerability in gateway 2",
        detection_method=DetectionMethod.AUTOMATED_SCAN,
        status=VulnerabilityStatus.OPEN,
        remediation_type=RemediationType.AUTOMATED,
    )
    
    vulnerability_repository.create(vuln1)
    vulnerability_repository.create(vuln2)
    
    # Wait for indexing
    import asyncio
    await asyncio.sleep(1)
    
    # Test gateway 1 summary
    response1 = await client.get(
        "/api/v1/security/summary",
        params={"gateway_id": str(gateway1.id)}
    )
    
    assert response1.status_code == 200
    data1 = response1.json()
    
    # Should only include gateway 1 vulnerabilities
    assert data1["critical_vulnerabilities"] >= 1
    assert data1["high_vulnerabilities"] == 0  # Gateway 2's vulnerability
    
    # Test gateway 2 summary
    response2 = await client.get(
        "/api/v1/security/summary",
        params={"gateway_id": str(gateway2.id)}
    )
    
    assert response2.status_code == 200
    data2 = response2.json()
    
    # Should only include gateway 2 vulnerabilities
    assert data2["critical_vulnerabilities"] == 0  # Gateway 1's vulnerability
    assert data2["high_vulnerabilities"] >= 1


@pytest.mark.asyncio
async def test_security_summary_nonexistent_gateway(client):
    """Test security summary with nonexistent gateway ID."""
    fake_gateway_id = uuid4()
    
    response = await client.get(
        "/api/v1/security/summary",
        params={"gateway_id": str(fake_gateway_id)}
    )
    
    # Should return empty counts, not error
    assert response.status_code == 200
    data = response.json()
    
    assert data["total_vulnerabilities"] == 0
    assert data["critical_vulnerabilities"] == 0
    assert data["high_vulnerabilities"] == 0
    assert data["medium_vulnerabilities"] == 0
    assert data["low_vulnerabilities"] == 0

# Made with Bob
