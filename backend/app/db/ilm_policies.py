"""
Index Lifecycle Management (ILM) Policies for Time-Bucketed Metrics

Manages data retention and lifecycle for metrics indices based on time bucket.
Each time bucket has different retention requirements:
- 1m metrics: 24h retention (1 day)
- 5m metrics: 7d retention (7 days)
- 1h metrics: 30d retention (30 days)
- 1d metrics: 90d retention (90 days)
"""

import logging
from typing import Dict, Any, Union
from opensearchpy import OpenSearch

from app.models.base.metric import TimeBucket

# Type alias for OpenSearch client (supports both OpenSearch and OpenSearchClient)
OpenSearchClientType = Union[OpenSearch, Any]

logger = logging.getLogger(__name__)


# Retention policies per time bucket
RETENTION_POLICIES: Dict[TimeBucket, Dict[str, Any]] = {
    TimeBucket.ONE_MINUTE: {
        "days": 1,
        "description": "24 hour retention for 1-minute metrics",
        "max_age": "1d",
        "max_size": "10gb",
    },
    TimeBucket.FIVE_MINUTES: {
        "days": 7,
        "description": "7 day retention for 5-minute metrics",
        "max_age": "7d",
        "max_size": "20gb",
    },
    TimeBucket.ONE_HOUR: {
        "days": 30,
        "description": "30 day retention for 1-hour metrics",
        "max_age": "30d",
        "max_size": "50gb",
    },
    TimeBucket.ONE_DAY: {
        "days": 90,
        "description": "90 day retention for 1-day metrics",
        "max_age": "90d",
        "max_size": "100gb",
    },
}


def create_ilm_policy(client: OpenSearchClientType, bucket: TimeBucket) -> bool:
    """
    Create or update ILM policy for a specific time bucket.
    
    Args:
        client: OpenSearch client instance
        bucket: Time bucket to create policy for
        
    Returns:
        True if policy created/updated successfully, False otherwise
    """
    policy_name = f"api-metrics-{bucket.value}-policy"
    retention = RETENTION_POLICIES[bucket]
    
    policy = {
        "policy": {
            "description": retention["description"],
            "default_state": "hot",
            "states": [
                {
                    "name": "hot",
                    "actions": [],
                    "transitions": [
                        {
                            "state_name": "delete",
                            "conditions": {
                                "min_index_age": retention["max_age"]
                            }
                        }
                    ]
                },
                {
                    "name": "delete",
                    "actions": [
                        {
                            "delete": {}
                        }
                    ],
                    "transitions": []
                }
            ],
            "ism_template": [
                {
                    "index_patterns": [f"api-metrics-{bucket.value}-*"],
                    "priority": 100
                }
            ]
        }
    }
    
    try:
        # Check if policy exists
        try:
            client.transport.perform_request(
                "GET",
                f"/_plugins/_ism/policies/{policy_name}"
            )
            # Policy exists, update it
            client.transport.perform_request(
                "PUT",
                f"/_plugins/_ism/policies/{policy_name}",
                body=policy
            )
            logger.info(f"Updated ILM policy: {policy_name}")
        except Exception:
            # Policy doesn't exist, create it
            client.transport.perform_request(
                "PUT",
                f"/_plugins/_ism/policies/{policy_name}",
                body=policy
            )
            logger.info(f"Created ILM policy: {policy_name}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create/update ILM policy {policy_name}: {e}", exc_info=True)
        return False


def create_all_ilm_policies(client: OpenSearchClientType) -> Dict[TimeBucket, bool]:
    """
    Create ILM policies for all time buckets.
    
    Args:
        client: OpenSearch client instance
        
    Returns:
        Dictionary mapping time buckets to success status
    """
    results = {}
    
    for bucket in TimeBucket:
        success = create_ilm_policy(client, bucket)
        results[bucket] = success
    
    successful = sum(1 for success in results.values() if success)
    logger.info(f"Created {successful}/{len(results)} ILM policies")
    
    return results


def delete_ilm_policy(client: OpenSearchClientType, bucket: TimeBucket) -> bool:
    """
    Delete ILM policy for a specific time bucket.
    
    Args:
        client: OpenSearch client instance
        bucket: Time bucket to delete policy for
        
    Returns:
        True if policy deleted successfully, False otherwise
    """
    policy_name = f"api-metrics-{bucket.value}-policy"
    
    try:
        client.transport.perform_request(
            "DELETE",
            f"/_plugins/_ism/policies/{policy_name}"
        )
        logger.info(f"Deleted ILM policy: {policy_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete ILM policy {policy_name}: {e}", exc_info=True)
        return False


def get_ilm_policy_status(client: OpenSearchClientType, bucket: TimeBucket) -> Dict[str, Any]:
    """
    Get status of ILM policy for a specific time bucket.
    
    Args:
        client: OpenSearch client instance
        bucket: Time bucket to check policy for
        
    Returns:
        Dictionary with policy status information
    """
    policy_name = f"api-metrics-{bucket.value}-policy"
    
    try:
        response = client.transport.perform_request(
            "GET",
            f"/_plugins/_ism/policies/{policy_name}"
        )
        
        return {
            "exists": True,
            "policy_name": policy_name,
            "bucket": bucket.value,
            "retention_days": RETENTION_POLICIES[bucket]["days"],
            "policy": response
        }
        
    except Exception as e:
        return {
            "exists": False,
            "policy_name": policy_name,
            "bucket": bucket.value,
            "retention_days": RETENTION_POLICIES[bucket]["days"],
            "error": str(e)
        }


def apply_policy_to_index(client: OpenSearchClientType, index_name: str, bucket: TimeBucket) -> bool:
    """
    Apply ILM policy to a specific index.
    
    Args:
        client: OpenSearch client instance
        index_name: Name of the index to apply policy to
        bucket: Time bucket (determines which policy to apply)
        
    Returns:
        True if policy applied successfully, False otherwise
    """
    policy_name = f"api-metrics-{bucket.value}-policy"
    
    try:
        client.transport.perform_request(
            "POST",
            f"/_plugins/_ism/add/{index_name}",
            body={"policy_id": policy_name}
        )
        logger.info(f"Applied ILM policy {policy_name} to index {index_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to apply ILM policy to index {index_name}: {e}", exc_info=True)
        return False


# Made with Bob