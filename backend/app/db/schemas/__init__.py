"""
OpenSearch Index Schema Definitions

This module contains index schema definitions (templates and mappings) for the
API Intelligence Plane. These schemas define the structure of OpenSearch indices
for storing vendor-neutral data.

Note: These are schema definitions only - no data migration is performed.
All indices start empty and are populated by:
- Mock data generation scripts (backend/scripts/)
- Real-time data collection from connected gateways
- Scheduled aggregation jobs

Schema Files:
- 010_api_inventory_v2.py: Vendor-neutral API metadata index
- 011_metrics_1m.py: 1-minute aggregated metrics (7-day retention)
- 012_metrics_5m.py: 5-minute aggregated metrics (30-day retention)
- 013_metrics_1h.py: 1-hour aggregated metrics (90-day retention)
- 014_metrics_1d.py: 1-day aggregated metrics (365-day retention)
- 015_transactional_logs.py: Raw transactional events (7-day retention)
"""

from app.db.schemas.schema_010_api_inventory_v2 import (
    create_api_inventory_v2_index,
)
from app.db.schemas.schema_011_metrics_1m import (
    create_metrics_1m_index_template,
    create_metrics_1m_ilm_policy,
)
from app.db.schemas.schema_012_metrics_5m import (
    create_metrics_5m_index_template,
    create_metrics_5m_ilm_policy,
)
from app.db.schemas.schema_013_metrics_1h import (
    create_metrics_1h_index_template,
    create_metrics_1h_ilm_policy,
)
from app.db.schemas.schema_014_metrics_1d import (
    create_metrics_1d_index_template,
    create_metrics_1d_ilm_policy,
)
from app.db.schemas.schema_015_transactional_logs import (
    create_transactional_logs_index_template,
    create_transactional_logs_ilm_policy,
)

__all__ = [
    "create_api_inventory_v2_index",
    "create_metrics_1m_index_template",
    "create_metrics_1m_ilm_policy",
    "create_metrics_5m_index_template",
    "create_metrics_5m_ilm_policy",
    "create_metrics_1h_index_template",
    "create_metrics_1h_ilm_policy",
    "create_metrics_1d_index_template",
    "create_metrics_1d_ilm_policy",
    "create_transactional_logs_index_template",
    "create_transactional_logs_ilm_policy",
]


# Made with Bob