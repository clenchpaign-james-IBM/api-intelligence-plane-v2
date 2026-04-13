"""
OpenSearch Index Migrations

This module contains all index creation and migration functions for OpenSearch.
Each migration file defines the schema for a specific index or index template.
"""

from .migration_001_api_inventory import create_api_inventory_index
from .migration_002_gateway_registry import create_gateway_registry_index
from .migration_003_api_metrics import create_api_metrics_index_template
from .migration_004_predictions import create_predictions_index
from .migration_005_security_findings import create_security_findings_index
from .migration_006_optimization_recommendations import (
    create_optimization_recommendations_index,
)
from .migration_007_rate_limit_policies import create_rate_limit_policies_index
from .migration_008_query_history import create_query_history_index
from .migration_009_compliance_violations import create_compliance_violations_index
from .migration_010_wm_transactional_logs import create_transactional_logs_index_template
from .migration_011_wm_metrics_1m import create_wm_metrics_1m_index_template
from .migration_012_wm_metrics_5m import create_wm_metrics_5m_index_template
from .migration_013_wm_metrics_1h import create_wm_metrics_1h_index_template
from .migration_014_wm_metrics_1d import create_wm_metrics_1d_index_template

__all__ = [
    "create_api_inventory_index",
    "create_gateway_registry_index",
    "create_api_metrics_index_template",
    "create_predictions_index",
    "create_security_findings_index",
    "create_optimization_recommendations_index",
    "create_rate_limit_policies_index",
    "create_query_history_index",
    "create_compliance_violations_index",
    "create_transactional_logs_index_template",
    "create_wm_metrics_1m_index_template",
    "create_wm_metrics_5m_index_template",
    "create_wm_metrics_1h_index_template",
    "create_wm_metrics_1d_index_template",
]

# Made with Bob
