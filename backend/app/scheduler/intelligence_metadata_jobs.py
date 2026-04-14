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
    Compute health scores for all APIs based on metrics.
    
    Runs every 5 minutes.
    
    Algorithm:
    1. Query all active APIs
    2. For each API:
       a. Query metrics from last 24 hours (1m bucket)
       b. Calculate health score based on:
          - Error rate (weight: 30%)
          - Response time (weight: 25%)
          - Availability (weight: 25%)
          - Throughput stability (weight: 20%)
       c. Update API.intelligence_metadata.health_score
    """
    try:
        api_repo = APIRepository()
        metrics_repo = MetricsRepository()
        
        # Get all active APIs
        apis, total = api_repo.find_by_status(APIStatus.ACTIVE, size=10000)
        
        logger.info(f"Computing health scores for {len(apis)} APIs")
        
        updated_count = 0
        failed_count = 0
        
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
                    logger.debug(f"No metrics found for API {api.name}, keeping default health score")
                    continue
                
                # Calculate health score
                health_score = calculate_health_score(metrics)
                
                # Update intelligence_metadata
                api_repo.update(str(api.id), {
                    "intelligence_metadata.health_score": health_score,
                    "intelligence_metadata.last_seen_at": datetime.utcnow().isoformat(),
                    "updated_at": datetime.utcnow().isoformat(),
                })
                
                updated_count += 1
                logger.debug(f"Updated health score for API {api.name}: {health_score}")
                
            except Exception as e:
                failed_count += 1
                logger.error(f"Failed to compute health score for API {api.id}: {e}")
        
        logger.info(
            f"Health score computation complete: {updated_count} updated, "
            f"{failed_count} failed, {len(apis) - updated_count - failed_count} skipped"
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
                
                # Update intelligence_metadata
                api_repo.update(str(api.id), {
                    "intelligence_metadata.risk_score": risk_score,
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
                
                # Update intelligence_metadata
                api_repo.update(str(api.id), {
                    "intelligence_metadata.security_score": round(security_score, 2),
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
    score = 100.0
    
    # Check for HTTPS enforcement
    if api.base_path and not api.base_path.startswith("https://"):
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
                
                # Update intelligence_metadata
                api_repo.update(str(api.id), {
                    "intelligence_metadata.usage_trend": usage_trend,
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

async def detect_shadow_apis_job() -> None:
    """
    Detect shadow APIs by analyzing traffic patterns.
    
    Runs every 5 minutes.
    
    Algorithm:
    1. Query transactional logs for recent traffic
    2. Extract unique API paths from logs
    3. Compare with registered APIs
    4. Mark unregistered paths as shadow APIs
    """
    try:
        api_repo = APIRepository()
        log_repo = TransactionalLogRepository()
        
        # Query all registered APIs
        registered_apis, _ = api_repo.list_all(size=10000)
        registered_paths = {api.base_path for api in registered_apis}
        
        # Query recent transactional logs (last 5 minutes)
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=5)
        
        logs, _ = log_repo.find_logs(
            start_time=start_time,
            end_time=end_time,
            size=10000
        )
        
        if not logs:
            logger.debug("No transactional logs found for shadow API detection")
            return
        
        # Extract unique paths from logs
        observed_paths = set()
        for log in logs:
            if hasattr(log, 'request_path') and log.request_path:
                observed_paths.add(log.request_path)
        
        # Find shadow paths (observed but not registered)
        shadow_paths = observed_paths - registered_paths
        
        if not shadow_paths:
            logger.debug("No shadow APIs detected")
            return
        
        logger.warning(f"Detected {len(shadow_paths)} potential shadow API paths")
        
        detected_count = 0
        
        for path in shadow_paths:
            try:
                # Check if already exists
                existing_api = api_repo.find_by_base_path(path)
                
                if existing_api:
                    # Update to mark as shadow
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
                    # Note: This requires gateway_id from logs
                    gateway_id_str = logs[0].gateway_id if logs else None
                    if not gateway_id_str:
                        continue
                    
                    # Convert gateway_id string to UUID
                    try:
                        gateway_uuid = UUID(gateway_id_str) if isinstance(gateway_id_str, str) else gateway_id_str
                    except (ValueError, AttributeError):
                        logger.warning(f"Invalid gateway_id format: {gateway_id_str}")
                        continue
                    
                    shadow_api = API(
                        id=uuid4(),
                        gateway_id=gateway_uuid,
                        name=f"Shadow API: {path}",
                        display_name=f"Shadow API: {path}",
                        description=f"Undocumented API detected from traffic analysis",
                        icon="warning",
                        base_path=path,
                        version_info=VersionInfo(
                            current_version="unknown",
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
                            base_path=path,
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
                        vendor_metadata={"detected_from": "traffic_analysis"},
                        endpoints=[],
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
                    logger.warning(f"Created new shadow API entry: {path}")
                    
            except Exception as e:
                logger.error(f"Failed to process shadow API {path}: {e}")
        
        logger.info(f"Shadow API detection complete: {detected_count} shadow APIs processed")
        
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