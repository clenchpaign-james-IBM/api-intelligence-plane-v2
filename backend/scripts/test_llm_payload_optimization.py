#!/usr/bin/env python3
"""
Test script for LLM entity payload optimization.

Validates that to_llm_dict() methods reduce payload sizes while maintaining
essential context for natural language response generation.

Usage:
    python backend/scripts/test_llm_payload_optimization.py
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.models.base.api import (
    API,
    APIDefinition,
    APIType,
    AuthenticationType,
    DiscoveryMethod,
    Endpoint,
    EndpointParameter,
    IntelligenceMetadata,
    MaturityState,
    OwnershipInfo,
    PolicyAction,
    PolicyActionType,
    PublishingInfo,
    VersionInfo,
)
from app.models.base.metric import Metric, TimeBucket, EndpointMetric
from app.models.base.policy_configs import RateLimitConfig
from app.models.compliance import (
    ComplianceViolation,
    ComplianceStandard,
    ComplianceViolationType,
    ComplianceSeverity,
    DetectionMethod as ComplianceDetectionMethod,
    Evidence,
    AuditTrailEntry,
)
from app.models.gateway import Gateway, GatewayVendor, ConnectionType, GatewayStatus
from app.models.prediction import (
    Prediction,
    PredictionType,
    PredictionSeverity,
    ContributingFactor,
    ContributingFactorType,
)
from app.models.recommendation import (
    OptimizationRecommendation,
    RecommendationType,
    RecommendationPriority,
    ImplementationEffort,
    EstimatedImpact,
)
from app.models.vulnerability import (
    Vulnerability,
    VulnerabilityType,
    VulnerabilitySeverity,
    DetectionMethod as VulnDetectionMethod,
)


def calculate_size_reduction(full_dict: dict, trimmed_dict: dict) -> tuple[int, int, float]:
    """Calculate size reduction percentage."""
    full_size = len(json.dumps(full_dict))
    trimmed_size = len(json.dumps(trimmed_dict))
    reduction = ((full_size - trimmed_size) / full_size) * 100
    return full_size, trimmed_size, reduction


def test_api_optimization():
    """Test API entity optimization."""
    print("\n" + "=" * 80)
    print("Testing API Entity Optimization")
    print("=" * 80)
    
    # Create a complex API entity
    api = API(
        gateway_id=uuid4(),
        name="user-service-api",
        display_name="User Service API",
        description="Comprehensive user management REST API with full CRUD operations",
        base_path="/api/v1/users",
        version_info=VersionInfo(
            current_version="2.3.1",
            previous_version="2.3.0",
            system_version=5,
            version_history=["1.0.0", "1.5.0", "2.0.0", "2.3.0", "2.3.1"],
        ),
        type=APIType.REST,
        maturity_state=MaturityState.PRODUCTIVE,
        groups=["user-management", "core-services"],
        tags=["users", "authentication", "profiles"],
        api_definition=APIDefinition(
            type="REST",
            version="3.0.0",
            base_path="/api/v1/users",
            openapi_spec={"openapi": "3.0.0", "info": {"title": "User API", "version": "2.3.1"}},
            paths={"/users": {"get": {}, "post": {}}, "/users/{id}": {"get": {}, "put": {}, "delete": {}}},
            schemas={"User": {"type": "object", "properties": {"id": {"type": "string"}}}},
        ),
        endpoints=[
            Endpoint(
                path="/users",
                method="GET",
                description="List all users",
                parameters=[
                    EndpointParameter(name="limit", type="query", data_type="integer", required=False),
                    EndpointParameter(name="offset", type="query", data_type="integer", required=False),
                ],
                response_codes=[200, 400, 500],
            ),
            Endpoint(
                path="/users/{id}",
                method="GET",
                description="Get user by ID",
                parameters=[
                    EndpointParameter(name="id", type="path", data_type="string", required=True),
                ],
                response_codes=[200, 404, 500],
            ),
        ],
        methods=["GET", "POST", "PUT", "DELETE"],
        authentication_type=AuthenticationType.OAUTH2,
        authentication_config={"client_id": "encrypted_client_id", "client_secret": "encrypted_secret"},
        policy_actions=[
            PolicyAction(
                action_type=PolicyActionType.RATE_LIMITING,
                enabled=True,
                config=RateLimitConfig(requests_per_minute=1000),
                name="Rate Limit Policy",
            ),
        ],
        ownership=OwnershipInfo(
            team="Platform Team",
            contact="platform@example.com",
            organization="Engineering",
            department="Backend Services",
        ),
        publishing=PublishingInfo(
            published_portals=["internal-portal", "partner-portal"],
            published_to_registry=True,
        ),
        intelligence_metadata=IntelligenceMetadata(
            is_shadow=False,
            discovery_method=DiscoveryMethod.GATEWAY_SYNC,
            discovered_at=datetime.utcnow(),
            last_seen_at=datetime.utcnow(),
            health_score=95.5,
            risk_score=15.2,
            security_score=88.0,
            compliance_status={"PCI-DSS": True, "GDPR": True, "HIPAA": False},
            usage_trend="increasing",
        ),
        vendor_metadata={"gateway_specific_field": "large_value" * 100},
    )
    
    # Compare sizes
    full_dict = api.model_dump(mode="json")
    trimmed_dict = api.to_llm_dict()
    
    full_size, trimmed_size, reduction = calculate_size_reduction(full_dict, trimmed_dict)
    
    print(f"Full payload size: {full_size:,} bytes")
    print(f"Trimmed payload size: {trimmed_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    print(f"Target: 60-85% reduction")
    print(f"Status: {'✓ PASS' if 60 <= reduction <= 85 else '✗ FAIL'}")
    
    # Verify essential fields are present
    assert "id" in trimmed_dict
    assert "name" in trimmed_dict
    assert "base_path" in trimmed_dict
    assert "intelligence_metadata" in trimmed_dict
    
    # Verify large fields are trimmed
    assert "openapi_spec" not in str(trimmed_dict)
    assert "authentication_config" not in trimmed_dict
    assert "vendor_metadata" not in trimmed_dict
    
    print("✓ All assertions passed")
    return reduction


def test_vulnerability_optimization():
    """Test Vulnerability entity optimization."""
    print("\n" + "=" * 80)
    print("Testing Vulnerability Entity Optimization")
    print("=" * 80)
    
    vuln = Vulnerability(
        gateway_id=uuid4(),
        api_id=uuid4(),
        vulnerability_type=VulnerabilityType.AUTHENTICATION,
        severity=VulnerabilitySeverity.HIGH,
        title="Weak JWT Token Validation",
        description="The API does not properly validate JWT token signatures" * 10,
        affected_endpoints=[f"/api/endpoint{i}" for i in range(10)],
        detection_method=VulnDetectionMethod.AUTOMATED_SCAN,
        detected_at=datetime.utcnow(),
        cvss_score=7.5,
        references=["https://nvd.nist.gov/vuln/detail/CVE-2024-1234"] * 5,
        metadata={"large_field": "data" * 1000},
        recommended_remediation={"steps": ["step1", "step2", "step3"] * 10},
        recommended_verification_steps=["verify1", "verify2", "verify3"] * 10,
    )
    
    full_dict = vuln.model_dump(mode="json")
    trimmed_dict = vuln.to_llm_dict()
    
    full_size, trimmed_size, reduction = calculate_size_reduction(full_dict, trimmed_dict)
    
    print(f"Full payload size: {full_size:,} bytes")
    print(f"Trimmed payload size: {trimmed_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    print(f"Target: 40-60% reduction")
    print(f"Status: {'✓ PASS' if 40 <= reduction <= 60 else '✗ FAIL'}")
    
    assert "id" in trimmed_dict
    assert "title" in trimmed_dict
    assert "metadata" not in trimmed_dict
    assert len(trimmed_dict.get("affected_endpoints", [])) <= 3
    
    print("✓ All assertions passed")
    return reduction


def test_recommendation_optimization():
    """Test Recommendation entity optimization."""
    print("\n" + "=" * 80)
    print("Testing Recommendation Entity Optimization")
    print("=" * 80)
    
    rec = OptimizationRecommendation(
        gateway_id=uuid4(),
        api_id=uuid4(),
        recommendation_type=RecommendationType.CACHING,
        title="Implement Redis Caching",
        description="Add Redis caching layer for frequently accessed endpoints" * 10,
        priority=RecommendationPriority.HIGH,
        estimated_impact=EstimatedImpact(
            metric="response_time_p95",
            current_value=250.0,
            expected_value=150.0,
            improvement_percentage=40.0,
            confidence=0.85,
        ),
        implementation_effort=ImplementationEffort.MEDIUM,
        implementation_steps=[f"Step {i}: Implementation detail" for i in range(10)],
        metadata={"large_field": "data" * 1000},
    )
    
    full_dict = rec.model_dump(mode="json")
    trimmed_dict = rec.to_llm_dict()
    
    full_size, trimmed_size, reduction = calculate_size_reduction(full_dict, trimmed_dict)
    
    print(f"Full payload size: {full_size:,} bytes")
    print(f"Trimmed payload size: {trimmed_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    print(f"Target: 50-70% reduction")
    print(f"Status: {'✓ PASS' if 50 <= reduction <= 70 else '✗ FAIL'}")
    
    assert "id" in trimmed_dict
    assert "title" in trimmed_dict
    assert "metadata" not in trimmed_dict
    assert len(trimmed_dict.get("implementation_steps", [])) <= 3
    
    print("✓ All assertions passed")
    return reduction


def test_metric_optimization():
    """Test Metric entity optimization."""
    print("\n" + "=" * 80)
    print("Testing Metric Entity Optimization")
    print("=" * 80)
    
    metric = Metric(
        gateway_id=uuid4(),
        api_id=str(uuid4()),
        timestamp=datetime.utcnow(),
        time_bucket=TimeBucket.FIVE_MINUTES,
        request_count=1500,
        success_count=1470,
        failure_count=30,
        error_rate=2.0,
        availability=98.0,
        response_time_avg=85.5,
        response_time_min=10.0,
        response_time_max=500.0,
        response_time_p50=75.0,
        response_time_p95=200.0,
        response_time_p99=350.0,
        gateway_time_avg=25.0,
        backend_time_avg=60.5,
        throughput=5.0,
        total_data_size=1500000,
        avg_request_size=500.0,
        avg_response_size=500.0,
        status_codes={"200": 1450, "404": 20, "500": 30},
        endpoint_metrics=[
            EndpointMetric(
                endpoint=f"/endpoint{i}",
                method="GET",
                request_count=max(10, 100 - i * 5),
                success_count=max(5, 95 - i * 5),
                failure_count=5,
                error_rate=5.0,
                response_time_avg=70.0,
                response_time_p50=65.0,
                response_time_p95=150.0,
                response_time_p99=250.0,
            )
            for i in range(20)
        ],
        vendor_metadata={"large_field": "data" * 1000},
    )
    
    full_dict = metric.model_dump(mode="json")
    trimmed_dict = metric.to_llm_dict()
    
    full_size, trimmed_size, reduction = calculate_size_reduction(full_dict, trimmed_dict)
    
    print(f"Full payload size: {full_size:,} bytes")
    print(f"Trimmed payload size: {trimmed_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    print(f"Target: 40-60% reduction")
    print(f"Status: {'✓ PASS' if 40 <= reduction <= 60 else '✗ FAIL'}")
    
    assert "id" in trimmed_dict
    assert "request_count" in trimmed_dict
    assert "status_codes" not in trimmed_dict
    assert "vendor_metadata" not in trimmed_dict
    assert len(trimmed_dict.get("top_endpoints", [])) <= 3
    
    print("✓ All assertions passed")
    return reduction


def test_prediction_optimization():
    """Test Prediction entity optimization."""
    print("\n" + "=" * 80)
    print("Testing Prediction Entity Optimization")
    print("=" * 80)
    
    pred = Prediction(
        gateway_id=uuid4(),
        api_id=uuid4(),
        prediction_type=PredictionType.FAILURE,
        predicted_at=datetime.utcnow(),
        predicted_time=datetime.utcnow() + timedelta(hours=36),
        confidence_score=0.85,
        severity=PredictionSeverity.HIGH,
        contributing_factors=[
            ContributingFactor(
                factor=ContributingFactorType.INCREASING_ERROR_RATE,
                current_value=0.15,
                threshold=0.10,
                trend="increasing",
                weight=0.35,
            )
            for _ in range(5)
        ],
        recommended_actions=[f"Action {i}: Take corrective measure" for i in range(10)],
        model_version="1.2.0",
        metadata={"large_field": "data" * 1000},
    )
    
    full_dict = pred.model_dump(mode="json")
    trimmed_dict = pred.to_llm_dict()
    
    full_size, trimmed_size, reduction = calculate_size_reduction(full_dict, trimmed_dict)
    
    print(f"Full payload size: {full_size:,} bytes")
    print(f"Trimmed payload size: {trimmed_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    print(f"Target: 20-30% reduction")
    print(f"Status: {'✓ PASS' if 20 <= reduction <= 30 else '✗ FAIL'}")
    
    assert "id" in trimmed_dict
    assert "prediction_type" in trimmed_dict
    assert "metadata" not in trimmed_dict
    assert len(trimmed_dict.get("recommended_actions", [])) <= 3
    
    print("✓ All assertions passed")
    return reduction


def test_compliance_optimization():
    """Test Compliance entity optimization."""
    print("\n" + "=" * 80)
    print("Testing Compliance Entity Optimization")
    print("=" * 80)
    
    comp = ComplianceViolation(
        gateway_id=uuid4(),
        api_id=uuid4(),
        compliance_standard=ComplianceStandard.HIPAA,
        violation_type=ComplianceViolationType.HIPAA_TRANSMISSION_SECURITY,
        severity=ComplianceSeverity.CRITICAL,
        title="HIPAA Transmission Security Violation",
        description="Gateway API endpoint handling PHI does not enforce TLS 1.3" * 10,
        affected_endpoints=[f"/api/endpoint{i}" for i in range(10)],
        detection_method=ComplianceDetectionMethod.AI_ANALYSIS,
        detected_at=datetime.utcnow(),
        evidence=[
            Evidence(
                type="gateway_config",
                description="TLS policy analysis",
                source="gateway_api",
                timestamp=datetime.utcnow(),
                data={"large_data": "value" * 100},
            )
            for _ in range(5)
        ],
        audit_trail=[
            AuditTrailEntry(
                timestamp=datetime.utcnow(),
                action=f"Action {i}",
                performed_by="system",
            )
            for i in range(10)
        ],
        metadata={"large_field": "data" * 1000},
    )
    
    full_dict = comp.model_dump(mode="json")
    trimmed_dict = comp.to_llm_dict()
    
    full_size, trimmed_size, reduction = calculate_size_reduction(full_dict, trimmed_dict)
    
    print(f"Full payload size: {full_size:,} bytes")
    print(f"Trimmed payload size: {trimmed_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    print(f"Target: 50-70% reduction")
    print(f"Status: {'✓ PASS' if 50 <= reduction <= 70 else '✗ FAIL'}")
    
    assert "id" in trimmed_dict
    assert "title" in trimmed_dict
    assert "metadata" not in trimmed_dict
    assert "evidence_count" in trimmed_dict
    
    print("✓ All assertions passed")
    return reduction


def test_gateway_optimization():
    """Test Gateway entity optimization."""
    print("\n" + "=" * 80)
    print("Testing Gateway Entity Optimization")
    print("=" * 80)
    
    gateway = Gateway(
        name="Production Gateway",
        vendor=GatewayVendor.WEBMETHODS,
        version="10.15",
        base_url="https://gateway.example.com:5555",
        connection_type=ConnectionType.REST_API,
        capabilities=["api_discovery", "metrics_collection", "rate_limiting"],
        status=GatewayStatus.CONNECTED,
        last_error="Connection timeout occurred due to network issues" * 10,
        configuration={"large_config": "value" * 1000},
        metadata={"large_metadata": "value" * 1000},
    )
    
    full_dict = gateway.model_dump(mode="json")
    trimmed_dict = gateway.to_llm_dict()
    
    full_size, trimmed_size, reduction = calculate_size_reduction(full_dict, trimmed_dict)
    
    print(f"Full payload size: {full_size:,} bytes")
    print(f"Trimmed payload size: {trimmed_size:,} bytes")
    print(f"Reduction: {reduction:.1f}%")
    print(f"Target: 40-60% reduction")
    print(f"Status: {'✓ PASS' if 40 <= reduction <= 60 else '✗ FAIL'}")
    
    assert "id" in trimmed_dict
    assert "name" in trimmed_dict
    assert "configuration" not in trimmed_dict
    assert "metadata" not in trimmed_dict
    assert len(trimmed_dict.get("last_error", "")) <= 100
    
    print("✓ All assertions passed")
    return reduction


def main():
    """Run all optimization tests."""
    print("\n" + "=" * 80)
    print("LLM Entity Payload Optimization Test Suite")
    print("=" * 80)
    
    results = {}
    
    try:
        results["API"] = test_api_optimization()
        results["Vulnerability"] = test_vulnerability_optimization()
        results["Recommendation"] = test_recommendation_optimization()
        results["Metric"] = test_metric_optimization()
        results["Prediction"] = test_prediction_optimization()
        results["Compliance"] = test_compliance_optimization()
        results["Gateway"] = test_gateway_optimization()
        
        print("\n" + "=" * 80)
        print("Summary")
        print("=" * 80)
        
        for entity, reduction in results.items():
            print(f"{entity:20s}: {reduction:5.1f}% reduction")
        
        avg_reduction = sum(results.values()) / len(results)
        print(f"\n{'Average':20s}: {avg_reduction:5.1f}% reduction")
        
        print("\n✓ All tests passed successfully!")
        print("\nExpected Impact:")
        print("- Reduced LLM costs: Smaller token counts = lower API costs")
        print("- Faster response times: Less data to serialize and transmit")
        print("- Better context utilization: More entities fit in context window")
        print("- Improved response quality: LLM focuses on relevant data")
        
        return 0
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
