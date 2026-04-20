"""
Intelligence Metadata Computation Jobs

Scheduled jobs that compute and update intelligence_metadata fields for APIs
based on actual metrics, vulnerabilities, compliance violations, and predictions.

These jobs transform hardcoded default values into real computed intelligence.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from uuid import UUID, uuid4

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.models.base.api import (
    API,
    APIStatus,
    DiscoveryMethod,
    IntelligenceMetadata,
    PolicyActionType,
    VersionInfo,
    MaturityState,
    APIDefinition,
    AuthenticationType,
    Endpoint,
)
from app.models.base.metric import Metric, TimeBucket
from app.models.vulnerability import Vulnerability
from app.models.compliance import ComplianceViolation
from app.models.prediction import Prediction

logger = logging.getLogger(__name__)


# ============================================================================
# Job 1: Health Score Computation
# ============================================================================

async def compute_health_scores_job() -> None:
    """
    Compute health scores for all APIs based on metrics (gateway-aware).
    
    Runs every 5 minutes.
    
    Algorithm:
    1. Fetch all gateways
    2. For each gateway:
       a. Fetch all APIs belonging to that gateway
       b. For each API:
          - Query metrics from last 24 hours (1m bucket)
          - Calculate health score based on:
            * Error rate (weight: 30%)
            * Response time (weight: 25%)
            * Availability (weight: 25%)
            * Throughput stability (weight: 20%)
          - Update API.intelligence_metadata.health_score
    """
    try:
        gateway_repo = GatewayRepository()
        api_repo = APIRepository()
        metrics_repo = MetricsRepository()
        
        # Fetch all gateways
        gateways, total_gateways = gateway_repo.list_all(size=10000)
        
        if not gateways:
            logger.info("No gateways found for health score computation")
            return
        
        logger.info(f"Computing health scores for APIs across {len(gateways)} gateways")
        
        total_updated = 0
        total_failed = 0
        total_skipped = 0
        
        # Process each gateway
        for gateway in gateways:
            try:
                # Fetch all APIs for this gateway
                apis, total_apis = api_repo.find_by_gateway(
                    gateway_id=gateway.id,
                    size=10000
                )
                
                if not apis:
                    logger.debug(f"No APIs found for gateway {gateway.name}")
                    continue
                
                logger.debug(f"Processing {len(apis)} APIs for gateway {gateway.name}")
                
                gateway_updated = 0
                gateway_failed = 0
                gateway_skipped = 0
                
                # Process each API
                for api in apis:
                    try:
                        # Query metrics for last 24 hours
                        end_time = datetime.utcnow()
                        start_time = end_time - timedelta(hours=24)
                        
                        metrics, _ = metrics_repo.find_by_api(
                            api_id=api.id,
                            start_time=start_time,
                            end_time=end_time,
                        )
                        
                        if not metrics:
                            logger.debug(
                                f"No metrics found for API {api.name} (gateway: {gateway.name}), "
                                f"keeping default health score"
                            )
                            gateway_skipped += 1
                            continue
                        
                        # Calculate health score
                        health_score = calculate_health_score(metrics)
                        
                        # Update intelligence_metadata as nested object
                        # Fetch current intelligence_metadata to preserve other fields
                        current_api = api_repo.get(str(api.id))
                        if current_api and current_api.intelligence_metadata:
                            # Update the nested object
                            intelligence_metadata = current_api.intelligence_metadata.model_dump(mode="json", exclude_none=True)
                            intelligence_metadata["health_score"] = health_score
                            intelligence_metadata["last_seen_at"] = datetime.utcnow().isoformat()
                            
                            api_repo.update(str(api.id), {
                                "intelligence_metadata": intelligence_metadata,
                                "updated_at": datetime.utcnow().isoformat(),
                            })
                        else:
                            # Fallback: create new intelligence_metadata object
                            api_repo.update(str(api.id), {
                                "intelligence_metadata": {
                                    "health_score": health_score,
                                    "last_seen_at": datetime.utcnow().isoformat(),
                                    "is_shadow": False,
                                    "discovery_method": "registered",
                                    "discovered_at": datetime.utcnow().isoformat(),
                                },
                                "updated_at": datetime.utcnow().isoformat(),
                            })
                        
                        gateway_updated += 1
                        logger.debug(
                            f"Updated health score for API {api.name} "
                            f"(gateway: {gateway.name}): {health_score}"
                        )
                        
                    except Exception as e:
                        gateway_failed += 1
                        logger.error(
                            f"Failed to compute health score for API {api.id} "
                            f"(gateway: {gateway.name}): {e}"
                        )
                
                logger.info(
                    f"Gateway {gateway.name}: {gateway_updated} updated, "
                    f"{gateway_failed} failed, {gateway_skipped} skipped"
                )
                
                total_updated += gateway_updated
                total_failed += gateway_failed
                total_skipped += gateway_skipped
                
            except Exception as e:
                logger.error(
                    f"Failed to process gateway {gateway.name} (id={gateway.id}): {e}"
                )
        
        logger.info(
            f"Health score computation complete across {len(gateways)} gateways: "
            f"{total_updated} updated, {total_failed} failed, {total_skipped} skipped"
        )
        
    except Exception as e:
        logger.error(f"Health score computation job failed: {e}", exc_info=True)


def calculate_health_score(metrics: List[Metric]) -> float:
    """
    Calculate health score from metrics.
    
    Returns:
        Health score (0-100)
    """
    if not metrics:
        return 100.0
    
    # Calculate component scores
    error_rate_score = calculate_error_rate_score(metrics)      # 0-100
    response_time_score = calculate_response_time_score(metrics) # 0-100
    availability_score = calculate_availability_score(metrics)   # 0-100
    throughput_score = calculate_throughput_score(metrics)       # 0-100
    
    # Weighted average
    health_score = (
        error_rate_score * 0.30 +
        response_time_score * 0.25 +
        availability_score * 0.25 +
        throughput_score * 0.20
    )
    
    return round(health_score, 2)


def calculate_error_rate_score(metrics: List[Metric]) -> float:
    """Calculate score based on error rate (0-100, higher is better)."""
    if not metrics:
        return 100.0
    
    # Calculate average error rate
    total_requests = sum(m.request_count for m in metrics)
    total_failures = sum(m.failure_count for m in metrics)
    
    if total_requests == 0:
        return 100.0
    
    error_rate = (total_failures / total_requests) * 100
    
    # Score: 100 at 0% errors, 0 at 10%+ errors
    if error_rate >= 10:
        return 0.0
    else:
        return 100.0 - (error_rate * 10)


def calculate_response_time_score(metrics: List[Metric]) -> float:
    """Calculate score based on response time (0-100, higher is better)."""
    if not metrics:
        return 100.0
    
    # Calculate average response time
    avg_response_time = sum(m.response_time_avg for m in metrics) / len(metrics)
    
    # Score: 100 at 0ms, 0 at 5000ms+
    if avg_response_time >= 5000:
        return 0.0
    else:
        return 100.0 - (avg_response_time / 50)


def calculate_availability_score(metrics: List[Metric]) -> float:
    """Calculate score based on availability (0-100, higher is better)."""
    if not metrics:
        return 100.0
    
    # Calculate average availability
    avg_availability = sum(m.availability for m in metrics) / len(metrics)
    
    # Availability is already 0-100, use directly
    return avg_availability


def calculate_throughput_score(metrics: List[Metric]) -> float:
    """Calculate score based on throughput stability (0-100, higher is better)."""
    if len(metrics) < 2:
        return 100.0
    
    # Calculate coefficient of variation (CV) for throughput
    throughputs = [m.throughput for m in metrics]
    mean_throughput = sum(throughputs) / len(throughputs)
    
    if mean_throughput == 0:
        return 100.0
    
    variance = sum((t - mean_throughput) ** 2 for t in throughputs) / len(throughputs)
    std_dev = variance ** 0.5
    cv = (std_dev / mean_throughput) * 100
    
    # Score: 100 at CV=0%, 0 at CV=100%+
    if cv >= 100:
        return 0.0
    else:
        return 100.0 - cv


# ============================================================================
# Job 2: Risk Score Computation
# ============================================================================

async def compute_risk_scores_job() -> None:
    """
    Compute risk scores for all APIs based on vulnerabilities.
    
    Runs every 1 hour.
    
    Algorithm:
    1. Query all active APIs
    2. For each API:
       a. Query vulnerabilities for this API
       b. Calculate risk score based on:
          - Critical vulnerabilities (weight: 50%)
          - High vulnerabilities (weight: 30%)
          - Medium vulnerabilities (weight: 15%)
          - Low vulnerabilities (weight: 5%)
       c. Update API.intelligence_metadata.risk_score
    """
    try:
        api_repo = APIRepository()
        vuln_repo = VulnerabilityRepository()
        
        apis, total = api_repo.find_by_status(APIStatus.ACTIVE, size=10000)
        
        logger.info(f"Computing risk scores for {len(apis)} APIs")
        
        updated_count = 0
        failed_count = 0
        
        for api in apis:
            try:
                # Query vulnerabilities for this API
                vulnerabilities = await vuln_repo.find_by_api_id(api.id, limit=1000)
                
                # Calculate risk score
                risk_score = calculate_risk_score(vulnerabilities)
                
                # Update intelligence_metadata as nested object
                current_api = api_repo.get(str(api.id))
                if current_api and current_api.intelligence_metadata:
                    intelligence_metadata = current_api.intelligence_metadata.model_dump(mode="json", exclude_none=True)
                    intelligence_metadata["risk_score"] = risk_score
                    
                    api_repo.update(str(api.id), {
                        "intelligence_metadata": intelligence_metadata,
                        "updated_at": datetime.utcnow().isoformat(),
                    })
                
                updated_count += 1
                logger.debug(f"Updated risk score for API {api.name}: {risk_score}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to compute risk score for API {api.id}: {e}")
        
        logger.info(
            f"Risk score computation complete: {updated_count} updated, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Risk score computation job failed: {e}", exc_info=True)


def calculate_risk_score(vulnerabilities: List[Vulnerability]) -> float:
    """
    Calculate risk score from vulnerabilities.
    
    Returns:
        Risk score (0-100, where 100 is highest risk)
    """
    if not vulnerabilities:
        return 0.0
    
    # Count by severity
    critical_count = sum(1 for v in vulnerabilities if v.severity == "critical")
    high_count = sum(1 for v in vulnerabilities if v.severity == "high")
    medium_count = sum(1 for v in vulnerabilities if v.severity == "medium")
    low_count = sum(1 for v in vulnerabilities if v.severity == "low")
    
    # Calculate weighted score
    risk_score = (
        critical_count * 25.0 +  # Each critical = 25 points
        high_count * 10.0 +      # Each high = 10 points
        medium_count * 3.0 +     # Each medium = 3 points
        low_count * 1.0          # Each low = 1 point
    )
    
    # Cap at 100
    return min(risk_score, 100.0)


# ============================================================================
# Job 3: Security Score Computation
# ============================================================================

async def compute_security_scores_job() -> None:
    """
    Compute security scores for all APIs based on security posture.
    
    Runs every 1 hour.
    
    Algorithm:
    1. Query all active APIs
    2. For each API:
       a. Check security policies (authentication, authorization, TLS, etc.)
       b. Check for security vulnerabilities
       c. Calculate security score based on:
          - Policy coverage (weight: 40%)
          - Vulnerability count (weight: 40%)
          - Security best practices (weight: 20%)
       c. Update API.intelligence_metadata.security_score
    """
    try:
        api_repo = APIRepository()
        vuln_repo = VulnerabilityRepository()
        
        apis, total = api_repo.find_by_status(APIStatus.ACTIVE, size=10000)
        
        logger.info(f"Computing security scores for {len(apis)} APIs")
        
        updated_count = 0
        failed_count = 0
        
        for api in apis:
            try:
                # Check security policies
                policy_score = calculate_policy_coverage_score(api.policy_actions or [])
                
                # Check vulnerabilities
                vulnerabilities = await vuln_repo.find_by_api_id(api.id, limit=1000)
                vuln_score = calculate_vulnerability_impact_score(vulnerabilities)
                
                # Check best practices
                best_practices_score = calculate_best_practices_score(api)
                
                # Calculate overall security score
                security_score = (
                    policy_score * 0.40 +
                    vuln_score * 0.40 +
                    best_practices_score * 0.20
                )
                
                # Update intelligence_metadata as nested object
                current_api = api_repo.get(str(api.id))
                if current_api and current_api.intelligence_metadata:
                    intelligence_metadata = current_api.intelligence_metadata.model_dump(mode="json", exclude_none=True)
                    intelligence_metadata["security_score"] = round(security_score, 2)
                    
                    api_repo.update(str(api.id), {
                        "intelligence_metadata": intelligence_metadata,
                        "updated_at": datetime.utcnow().isoformat(),
                    })
                
                updated_count += 1
                logger.debug(f"Updated security score for API {api.name}: {security_score}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to compute security score for API {api.id}: {e}")
        
        logger.info(
            f"Security score computation complete: {updated_count} updated, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Security score computation job failed: {e}", exc_info=True)


def calculate_policy_coverage_score(policy_actions: List[Any]) -> float:
    """Calculate score based on security policy coverage (0-100)."""
    if not policy_actions:
        return 0.0
    
    # Check for essential security policies
    required_policies = {
        PolicyActionType.AUTHENTICATION,
        PolicyActionType.AUTHORIZATION,
        PolicyActionType.TLS,
    }
    
    recommended_policies = {
        PolicyActionType.VALIDATION,
        PolicyActionType.CORS,
        PolicyActionType.DATA_MASKING,
    }
    
    # Count present policies
    present_policy_types = {pa.type for pa in policy_actions if hasattr(pa, 'type')}
    
    required_count = len(required_policies & present_policy_types)
    recommended_count = len(recommended_policies & present_policy_types)
    
    # Score: 60 points for required, 40 points for recommended
    required_score = (required_count / len(required_policies)) * 60
    recommended_score = (recommended_count / len(recommended_policies)) * 40
    
    return required_score + recommended_score


def calculate_vulnerability_impact_score(vulnerabilities: List[Vulnerability]) -> float:
    """Calculate score based on vulnerability impact (0-100, higher is better)."""
    if not vulnerabilities:
        return 100.0
    
    # Count by severity
    critical_count = sum(1 for v in vulnerabilities if v.severity == "critical")
    high_count = sum(1 for v in vulnerabilities if v.severity == "high")
    medium_count = sum(1 for v in vulnerabilities if v.severity == "medium")
    
    # Calculate penalty
    penalty = (
        critical_count * 30 +  # Each critical = -30 points
        high_count * 15 +      # Each high = -15 points
        medium_count * 5       # Each medium = -5 points
    )
    
    # Score: 100 - penalty, minimum 0
    return max(100.0 - penalty, 0.0)


def calculate_best_practices_score(api: API) -> float:
    """Calculate score based on security best practices (0-100)."""
    from app.utils.tls_config import has_tls_enforced
    
    score = 100.0
    
    # Check if TLS policy exists and enforce_tls is True
    if not has_tls_enforced(api):
        score -= 20
    
    # Check for versioning
    if not api.version_info or not api.version_info.current_version:
        score -= 10
    
    # Check for documentation
    if not api.api_definition or not api.api_definition.openapi_spec:
        score -= 10
    
    # Check for rate limiting
    has_rate_limiting = any(
        pa.action_type == PolicyActionType.RATE_LIMITING
        for pa in (api.policy_actions or [])
        if hasattr(pa, 'type')
    )
    if not has_rate_limiting:
        score -= 10
    
    return max(score, 0.0)


# ============================================================================
# Job 4: Usage Trend Computation
# ============================================================================

async def compute_usage_trends_job() -> None:
    """
    Compute usage trends for all APIs based on metrics.
    
    Runs every 1 hour.
    
    Algorithm:
    1. Query all active APIs
    2. For each API:
       a. Query metrics for last 7 days
       b. Calculate trend (increasing, stable, decreasing)
       c. Update API.intelligence_metadata.usage_trend
    """
    try:
        api_repo = APIRepository()
        metrics_repo = MetricsRepository()
        
        apis, total = api_repo.find_by_status(APIStatus.ACTIVE, size=10000)
        
        logger.info(f"Computing usage trends for {len(apis)} APIs")
        
        updated_count = 0
        failed_count = 0
        
        for api in apis:
            try:
                # Query metrics for last 7 days
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=7)
                
                metrics, _ = metrics_repo.find_by_api(
                    api_id=api.id,
                    start_time=start_time,
                    end_time=end_time,
                )
                
                if not metrics:
                    continue
                
                # Calculate trend
                usage_trend = calculate_usage_trend(metrics)
                
                # Update intelligence_metadata as nested object
                current_api = api_repo.get(str(api.id))
                if current_api and current_api.intelligence_metadata:
                    intelligence_metadata = current_api.intelligence_metadata.model_dump(mode="json", exclude_none=True)
                    intelligence_metadata["usage_trend"] = usage_trend
                    
                    api_repo.update(str(api.id), {
                        "intelligence_metadata": intelligence_metadata,
                        "updated_at": datetime.utcnow().isoformat(),
                    })
                
                updated_count += 1
                logger.debug(f"Updated usage trend for API {api.name}: {usage_trend}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to compute usage trend for API {api.id}: {e}")
        
        logger.info(
            f"Usage trend computation complete: {updated_count} updated, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Usage trend computation job failed: {e}", exc_info=True)


def calculate_usage_trend(metrics: List[Metric]) -> str:
    """
    Calculate usage trend from metrics.
    
    Returns:
        "increasing", "stable", or "decreasing"
    """
    if len(metrics) < 2:
        return "stable"
    
    # Sort by timestamp
    sorted_metrics = sorted(metrics, key=lambda m: m.timestamp)
    
    # Calculate average throughput for first half vs second half
    mid_point = len(sorted_metrics) // 2
    first_half = sorted_metrics[:mid_point]
    second_half = sorted_metrics[mid_point:]
    
    first_half_avg = sum(m.throughput for m in first_half) / len(first_half)
    second_half_avg = sum(m.throughput for m in second_half) / len(second_half)
    
    # Calculate percentage change
    if first_half_avg == 0:
        return "stable"
    
    change_percent = ((second_half_avg - first_half_avg) / first_half_avg) * 100
    
    if change_percent > 20:
        return "increasing"
    elif change_percent < -20:
        return "decreasing"
    else:
        return "stable"


# ============================================================================
# Job 5: Shadow API Detection
# ============================================================================
async def detect_shadow_apis_for_gateway(
    gateway,
    api_repo: APIRepository,
    log_repo: TransactionalLogRepository,
) -> int:
    """
    Detect shadow APIs for a specific gateway.
    
    Args:
        gateway: Gateway object
        api_repo: API repository instance
        log_repo: Transactional log repository instance
    
    Returns:
        Number of shadow APIs detected/processed
    """
    from app.utils.path_matcher import parse_request_path
    
    gateway_id = gateway.id
    gateway_name = gateway.name
    
    logger.debug(f"Detecting shadow APIs for gateway: {gateway_name} (id={gateway_id})")
    
    # Query recent transactional logs for this gateway (last 5 minutes)
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(minutes=5)
    
    logs, _ = log_repo.find_logs(
        gateway_id=str(gateway_id),
        start_time=start_time,
        end_time=end_time,
        size=10000
    )
    
    if not logs:
        logger.debug(f"No transactional logs found for gateway {gateway_name}")
        return 0
    
    # Extract unique request paths from logs
    observed_paths = set()
    for log in logs:
        if hasattr(log, 'request_path') and log.request_path:
            observed_paths.add(log.request_path)
    
    if not observed_paths:
        logger.debug(f"No request paths found in logs for gateway {gateway_name}")
        return 0
    
    logger.debug(
        f"Found {len(observed_paths)} unique request paths for gateway {gateway_name}"
    )
    
    # Check each observed path against registered APIs
    shadow_paths = []
    for request_path in observed_paths:
        # Try to find matching API using enhanced path matching
        matching_api = api_repo.find_by_request_path(request_path, gateway_id)
        
        if not matching_api:
            # No matching API found - potential shadow API
            shadow_paths.append(request_path)
            logger.debug(f"Potential shadow API path: {request_path}")
    
    if not shadow_paths:
        logger.debug(f"No shadow APIs detected for gateway {gateway_name}")
        return 0
    
    logger.warning(
        f"Detected {len(shadow_paths)} potential shadow API paths for gateway "
        f"{gateway_name}"
    )
    
    detected_count = 0
    
    # Process each shadow path
    for path in shadow_paths:
        try:
            # Parse the path to extract components
            components = parse_request_path(path)
            
            if not components:
                logger.debug(f"Could not parse shadow path: {path}")
                continue
            
            # Check if shadow API already exists for this path
            existing_api = api_repo.find_by_request_path(path, gateway_id)
            
            if existing_api and existing_api.intelligence_metadata.is_shadow:
                # Update last_seen_at for existing shadow API
                api_repo.update(str(existing_api.id), {
                    "intelligence_metadata.last_seen_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                })
                detected_count += 1
                logger.debug(f"Updated existing shadow API: {path}")
            elif existing_api:
                # Mark existing non-shadow API as shadow
                api_repo.update(str(existing_api.id), {
                    "intelligence_metadata.is_shadow": True,
                    "intelligence_metadata.discovery_method": DiscoveryMethod.TRAFFIC_ANALYSIS.value,
                    "intelligence_metadata.last_seen_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                })
                detected_count += 1
                logger.info(f"Marked existing API as shadow: {path}")
            else:
                # Create new shadow API entry
                shadow_api = API(
                    id=uuid4(),
                    gateway_id=gateway_id,
                    name=f"Shadow: {components.api_name}",
                    display_name=f"Shadow API: {components.api_name}",
                    description=(
                        f"Undocumented API detected from traffic analysis. "
                        f"Original path: {path}"
                    ),
                    icon="warning",
                    base_path=components.resource_path or "/",
                    version_info=VersionInfo(
                        current_version=components.api_version,
                        previous_version=None,
                        next_version=None,
                        version_history=None,
                    ),
                    maturity_state=MaturityState.TEST,
                    api_definition=APIDefinition(
                        type="REST",
                        version=None,
                        openapi_spec=None,
                        swagger_version=None,
                        base_path=components.resource_path or "/",
                        paths=None,
                        schemas=None,
                        security_schemes=None,
                        vendor_extensions=None,
                    ),
                    methods=[],  # Unknown methods - can be enriched later
                    authentication_type=AuthenticationType.NONE,
                    authentication_config={},
                    policy_actions=[],
                    ownership=None,
                    publishing=None,
                    deployments=None,
                    vendor_metadata={
                        "detected_from": "traffic_analysis",
                        "original_path": path,
                        "gateway_prefix": components.gateway_prefix,
                    },
                    endpoints=[
                        Endpoint(
                            path=components.resource_path or "/",
                            method="UNKNOWN",
                            description="Detected from traffic",
                            connection_timeout=None,
                            read_timeout=None,
                        )
                    ],
                    intelligence_metadata=IntelligenceMetadata(
                        is_shadow=True,
                        discovery_method=DiscoveryMethod.TRAFFIC_ANALYSIS,
                        discovered_at=datetime.utcnow(),
                        last_seen_at=datetime.utcnow(),
                        health_score=50.0,  # Lower default for shadow APIs
                        risk_score=75.0,    # Higher risk for undocumented APIs
                        security_score=25.0, # Lower security for undocumented APIs
                        compliance_status={},
                        usage_trend="unknown",
                    ),
                    status=APIStatus.ACTIVE,
                    is_active=True,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                api_repo.create(shadow_api)
                detected_count += 1
                logger.warning(
                    f"Created new shadow API entry for gateway {gateway_name}: "
                    f"{components.api_name} (path: {path})"
                )
                
        except Exception as e:
            logger.error(f"Failed to process shadow API {path}: {e}")
    
    logger.info(
        f"Shadow API detection for gateway {gateway_name}: "
        f"{detected_count} shadow APIs processed"
    )
    
    return detected_count



async def detect_shadow_apis_job() -> None:
    """
    Detect shadow APIs by analyzing traffic patterns (gateway-aware).
    
    Runs every 5 minutes.
    
    Algorithm:
    1. Fetch all connected gateways
    2. For each gateway:
       a. Query transactional logs for recent traffic
       b. Extract unique request paths from logs
       c. Use path matching to identify unregistered APIs
       d. Mark/create shadow API entries
    
    Improvements:
    - Gateway-aware processing (handles different routing schemes)
    - Path pattern matching (supports path parameters)
    - Eliminates false positives from resource paths
    """
    try:
        gateway_repo = GatewayRepository()
        api_repo = APIRepository()
        log_repo = TransactionalLogRepository()
        
        # Fetch all gateways
        gateways, _ = gateway_repo.list_all(size=1000)
        
        if not gateways:
            logger.debug("No gateways found for shadow API detection")
            return
        
        logger.info(f"Starting shadow API detection for {len(gateways)} gateways")
        
        total_detected = 0
        
        # Process each gateway independently
        for gateway in gateways:
            try:
                detected = await detect_shadow_apis_for_gateway(
                    gateway, api_repo, log_repo
                )
                total_detected += detected
            except Exception as e:
                logger.error(
                    f"Failed to detect shadow APIs for gateway {gateway.name} "
                    f"(id={gateway.id}): {e}"
                )
        
        logger.info(
            f"Shadow API detection complete: {total_detected} shadow APIs processed "
            f"across {len(gateways)} gateways"
        )
        
    except Exception as e:
        logger.error(f"Shadow API detection job failed: {e}", exc_info=True)


# ============================================================================
# Job 6: Compliance Status Computation
# ============================================================================

async def compute_compliance_status_job() -> None:
    """
    Compute compliance status for all APIs.
    
    Runs every 1 hour.
    
    Algorithm:
    1. Query all active APIs
    2. For each API:
       a. Query compliance violations
       b. Calculate compliance status by standard
       c. Update API.intelligence_metadata.compliance_status
    """
    try:
        api_repo = APIRepository()
        compliance_repo = ComplianceRepository()
        
        apis, total = api_repo.find_by_status(APIStatus.ACTIVE, size=10000)
        
        logger.info(f"Computing compliance status for {len(apis)} APIs")
        
        updated_count = 0
        failed_count = 0
        
        for api in apis:
            try:
                # Query compliance violations for this API
                violations = await compliance_repo.find_by_api_id(api.id, limit=1000)
                
                # Calculate compliance status by standard
                compliance_status = calculate_compliance_status(violations)
                
                # Update intelligence_metadata
                api_repo.update(str(api.id), {
                    "intelligence_metadata.compliance_status": compliance_status,
                    "updated_at": datetime.utcnow().isoformat(),
                })
                
                updated_count += 1
                logger.debug(f"Updated compliance status for API {api.name}: {compliance_status}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to compute compliance status for API {api.id}: {e}")
        
        logger.info(
            f"Compliance status computation complete: {updated_count} updated, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Compliance status computation job failed: {e}", exc_info=True)


def calculate_compliance_status(violations: List[ComplianceViolation]) -> Dict[str, bool]:
    """
    Calculate compliance status by standard.
    
    Returns:
        Dict mapping standard to compliance status (True = compliant, False = violations)
    """
    standards = ["GDPR", "HIPAA", "SOC2", "PCI-DSS", "ISO27001"]
    status = {}
    
    for standard in standards:
        # Check if there are any open violations for this standard
        has_violations = any(
            v.compliance_standard.value == standard and v.status.value != "remediated"
            for v in violations
        )
        status[standard] = not has_violations
    
    return status


# ============================================================================
# Job 7: Predictions Status Update
# ============================================================================

async def update_predictions_status_job() -> None:
    """
    Update has_active_predictions flag for all APIs.
    
    Runs every 5 minutes.
    
    Algorithm:
    1. Query all active APIs
    2. For each API:
       a. Query active predictions
       b. Update API.intelligence_metadata.has_active_predictions
    """
    try:
        api_repo = APIRepository()
        prediction_repo = PredictionRepository()
        
        apis, total = api_repo.find_by_status(APIStatus.ACTIVE, size=10000)
        
        logger.info(f"Updating predictions status for {len(apis)} APIs")
        
        updated_count = 0
        failed_count = 0
        
        for api in apis:
            try:
                # Query active predictions for this API
                predictions_result = prediction_repo.list_predictions(
                    api_id=str(api.id),
                    status=None  # Get all active predictions (default filter)
                )
                predictions = predictions_result.get("predictions", [])
                
                has_predictions = len(predictions) > 0
                
                # Update intelligence_metadata
                api_repo.update(str(api.id), {
                    "intelligence_metadata.has_active_predictions": has_predictions,
                    "updated_at": datetime.utcnow().isoformat(),
                })
                
                updated_count += 1
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to update predictions status for API {api.id}: {e}")
        
        logger.info(
            f"Predictions status update complete: {updated_count} updated, {failed_count} failed"
        )
        
    except Exception as e:
        logger.error(f"Predictions status update job failed: {e}", exc_info=True)


# ============================================================================
# Master Job: Run All Intelligence Computations
# ============================================================================

async def run_all_intelligence_jobs() -> None:
    """
    Run all intelligence metadata computation jobs in sequence.
    
    This is useful for initial setup or manual refresh.
    """
    logger.info("Running all intelligence metadata computation jobs")
    
    try:
        await compute_health_scores_job()
        await compute_risk_scores_job()
        await compute_security_scores_job()
        await compute_usage_trends_job()
        await detect_shadow_apis_job()
        await compute_compliance_status_job()
        await update_predictions_status_job()
        
        logger.info("All intelligence metadata computation jobs completed successfully")
        
    except Exception as e:
        logger.error(f"Intelligence metadata computation failed: {e}", exc_info=True)


# Made with Bob