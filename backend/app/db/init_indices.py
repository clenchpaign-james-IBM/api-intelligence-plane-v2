"""
Initialize OpenSearch Infrastructure

Unified initialization for all OpenSearch indices, templates, and ILM policies.
This module serves as the single source of truth for database initialization,
used by both application startup and CLI tools.
"""

import logging
from typing import Optional, Dict, List, Tuple, Callable, Any
from opensearchpy import OpenSearch, exceptions

from app.db.schemas import (
    create_api_inventory_index,
    create_gateway_registry_index,
    create_api_metrics_index_template,
    create_predictions_index,
    create_security_findings_index,
    create_optimization_recommendations_index,
    create_rate_limit_policies_index,
    create_query_history_index,
    create_compliance_violations_index,
    create_transactional_logs_index_template,
    create_metrics_1m_index_template,
    create_metrics_5m_index_template,
    create_metrics_1h_index_template,
    create_metrics_1d_index_template,
)
from app.db.ilm_policies import create_all_ilm_policies
from app.db.index_templates import create_transactional_logs_template

logger = logging.getLogger(__name__)


# Define all schemas to initialize
SCHEMA_DEFINITIONS: List[Tuple[str, str, Callable[[OpenSearch], None]]] = [
    ("api-inventory", "API Inventory", create_api_inventory_index),
    ("gateway-registry", "Gateway Registry", create_gateway_registry_index),
    ("api-metrics-*", "API Metrics Template", create_api_metrics_index_template),
    ("api-predictions", "Predictions", create_predictions_index),
    ("security-findings", "Security Findings", create_security_findings_index),
    ("optimization-recommendations", "Optimization Recommendations", create_optimization_recommendations_index),
    ("rate-limit-policies", "Rate Limit Policies", create_rate_limit_policies_index),
    ("query-history", "Query History", create_query_history_index),
    ("compliance-violations", "Compliance Violations", create_compliance_violations_index),
    ("transactional-logs-*", "Transactional Logs Template", create_transactional_logs_index_template),
    ("api-metrics-1m-*", "1-Minute Metrics Template", create_metrics_1m_index_template),
    ("api-metrics-5m-*", "5-Minute Metrics Template", create_metrics_5m_index_template),
    ("api-metrics-1h-*", "1-Hour Metrics Template", create_metrics_1h_index_template),
    ("api-metrics-1d-*", "1-Day Metrics Template", create_metrics_1d_index_template),
]


def initialize_indices(
    client: OpenSearch,
    force: bool = False,
    skip_existing: bool = True,
    raise_on_error: bool = False
) -> Dict[str, bool]:
    """
    Initialize all required OpenSearch indices and templates.
    
    This is the main entry point for database initialization, used by:
    - Application startup (main.py)
    - CLI initialization scripts
    - Testing infrastructure
    
    Args:
        client: OpenSearch client instance
        force: If True, delete and recreate existing indices (DESTRUCTIVE!)
        skip_existing: If True, skip indices that already exist
        raise_on_error: If True, raise exceptions on errors; if False, log and continue
        
    Returns:
        Dictionary mapping index names to success status
        
    Example:
        >>> client = get_opensearch_client()
        >>> results = initialize_indices(client)
        >>> print(f"Created {sum(results.values())}/{len(results)} indices")
    """
    logger.info("=" * 80)
    logger.info("Initializing OpenSearch Infrastructure")
    logger.info("=" * 80)
    
    results = {}
    
    for index_name, display_name, create_func in SCHEMA_DEFINITIONS:
        try:
            logger.info(f"\n{display_name} ({index_name}):")
            
            # Check if index/template exists
            is_template = "*" in index_name
            exists = _check_exists(client, index_name, is_template)
            
            if exists:
                if force:
                    logger.info(f"  Deleting existing {'template' if is_template else 'index'}...")
                    _delete_if_exists(client, index_name, is_template)
                elif skip_existing:
                    logger.info(f"  Already exists, skipping")
                    results[index_name] = True
                    continue
            
            # Create index/template
            create_func(client)
            logger.info(f"  ✓ Created successfully")
            results[index_name] = True
            
        except Exception as e:
            logger.error(f"  ✗ Failed to create {display_name}: {e}")
            results[index_name] = False
            if raise_on_error:
                raise
    
    # Summary
    success_count = sum(1 for success in results.values() if success)
    total_count = len(results)
    logger.info(f"\n{'=' * 80}")
    logger.info(f"Initialization Summary: {success_count}/{total_count} successful")
    logger.info(f"{'=' * 80}\n")
    
    return results


def initialize_ilm_policies(
    client: OpenSearch,
    raise_on_error: bool = False
) -> Dict[str, bool]:
    """
    Initialize Index Lifecycle Management (ILM) policies for metrics.
    
    Creates retention policies for time-bucketed metrics:
    - 1m metrics: 24h retention
    - 5m metrics: 7d retention
    - 1h metrics: 30d retention
    - 1d metrics: 90d retention
    
    Args:
        client: OpenSearch client instance
        raise_on_error: If True, raise exceptions on errors
        
    Returns:
        Dictionary mapping time bucket names to success status
    """
    logger.info("Initializing ILM policies for time-bucketed metrics...")
    
    try:
        results = create_all_ilm_policies(client)
        
        # Convert TimeBucket enum keys to strings
        str_results: Dict[str, bool] = {bucket.value: success for bucket, success in results.items()}
        
        success_count = sum(1 for success in str_results.values() if success)
        total_count = len(str_results)
        
        for bucket_name, success in str_results.items():
            status = "✓" if success else "✗"
            logger.info(f"  {status} ILM policy for {bucket_name} bucket")
        
        logger.info(f"ILM policies: {success_count}/{total_count} successful")
        return str_results
        
    except Exception as e:
        logger.error(f"Failed to create ILM policies: {e}")
        if raise_on_error:
            raise
        return {}


def initialize_all_infrastructure(
    client: OpenSearch,
    force: bool = False,
    include_ilm: bool = True,
    raise_on_error: bool = False
) -> Tuple[Dict[str, bool], Dict[str, bool]]:
    """
    Initialize complete OpenSearch infrastructure.
    
    This is the comprehensive initialization function that sets up:
    1. All indices and index templates
    2. ILM policies (optional)
    
    Args:
        client: OpenSearch client instance
        force: If True, recreate existing indices (DESTRUCTIVE!)
        include_ilm: If True, also create ILM policies
        raise_on_error: If True, raise exceptions on errors
        
    Returns:
        Tuple of (indices_results, ilm_results)
        
    Example:
        >>> client = get_opensearch_client()
        >>> indices, ilm = initialize_all_infrastructure(client, include_ilm=True)
        >>> print(f"Indices: {sum(indices.values())}/{len(indices)}")
        >>> print(f"ILM: {sum(ilm.values())}/{len(ilm)}")
    """
    # Initialize indices and templates
    indices_results = initialize_indices(
        client,
        force=force,
        skip_existing=not force,
        raise_on_error=raise_on_error
    )
    
    # Initialize ILM policies if requested
    ilm_results = {}
    if include_ilm:
        ilm_results = initialize_ilm_policies(client, raise_on_error=raise_on_error)
    
    return indices_results, ilm_results


def verify_infrastructure(client: OpenSearch) -> Dict[str, bool]:
    """
    Verify that all required infrastructure exists.
    
    Checks for the existence of all indices and templates without creating them.
    Useful for health checks and validation.
    
    Args:
        client: OpenSearch client instance
        
    Returns:
        Dictionary mapping index names to existence status
    """
    logger.info("Verifying OpenSearch infrastructure...")
    
    results = {}
    
    for index_name, display_name, _ in SCHEMA_DEFINITIONS:
        is_template = "*" in index_name
        exists = _check_exists(client, index_name, is_template)
        results[index_name] = exists
        
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {display_name}")
    
    all_exist = all(results.values())
    if all_exist:
        logger.info("✓ All infrastructure components verified")
    else:
        missing = [name for name, exists in results.items() if not exists]
        logger.warning(f"✗ Missing components: {', '.join(missing)}")
    
    return results


def _check_exists(client: OpenSearch, index_name: str, is_template: bool) -> bool:
    """Check if an index or template exists."""
    try:
        if is_template:
            template_name = index_name.replace("*", "template")
            return client.indices.exists_index_template(name=template_name)
        else:
            return client.indices.exists(index=index_name)
    except Exception:
        return False


def _delete_if_exists(client: OpenSearch, index_name: str, is_template: bool) -> None:
    """Delete an index or template if it exists."""
    try:
        if is_template:
            template_name = index_name.replace("*", "template")
            if client.indices.exists_index_template(name=template_name):
                client.indices.delete_index_template(name=template_name)
        else:
            if client.indices.exists(index=index_name):
                client.indices.delete(index=index_name)
    except Exception as e:
        logger.warning(f"Failed to delete {index_name}: {e}")


# Made with Bob
