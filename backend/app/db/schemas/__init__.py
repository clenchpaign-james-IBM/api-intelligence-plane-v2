"""
OpenSearch Index Schemas

This module contains all index schema definitions for OpenSearch.
Each schema file defines the structure for a specific index or index template.
"""

from .api_inventory import create_api_inventory_index
from .gateway_registry import create_gateway_registry_index
from .api_metrics import create_api_metrics_index_template
from .predictions import create_predictions_index
from .security_findings import create_security_findings_index
from .optimization_recommendations import create_optimization_recommendations_index
from .rate_limit_policies import create_rate_limit_policies_index
from .query_history import create_query_history_index
from .compliance_violations import create_compliance_violations_index
from .transactional_logs import create_transactional_logs_index_template
from .metrics_1m import create_metrics_1m_index_template
from .metrics_5m import create_metrics_5m_index_template
from .metrics_1h import create_metrics_1h_index_template
from .metrics_1d import create_metrics_1d_index_template

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
    "create_metrics_1m_index_template",
    "create_metrics_5m_index_template",
    "create_metrics_1h_index_template",
    "create_metrics_1d_index_template",
]

# Made with Bob