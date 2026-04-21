"""
Index Templates for Time-Bucketed Metrics

Manages OpenSearch index templates for metrics indices.
Templates ensure consistent mappings, settings, and ILM policies across all indices.
"""

import logging
from typing import Dict, Any, Union
from opensearchpy import OpenSearch

from app.models.base.metric import TimeBucket

# Type alias for OpenSearch client (supports both OpenSearch and OpenSearchClient)
OpenSearchClientType = Union[OpenSearch, Any]

logger = logging.getLogger(__name__)


def get_metrics_index_template(bucket: TimeBucket) -> Dict[str, Any]:
    """
    Get index template configuration for a specific time bucket.
    
    Args:
        bucket: Time bucket to create template for
        
    Returns:
        Index template configuration
    """
    template_name = f"api-metrics-{bucket.value}-template"
    policy_name = f"api-metrics-{bucket.value}-policy"
    
    # Adjust refresh interval based on bucket size
    refresh_intervals = {
        TimeBucket.ONE_MINUTE: "5s",
        TimeBucket.FIVE_MINUTES: "15s",
        TimeBucket.ONE_HOUR: "30s",
        TimeBucket.ONE_DAY: "60s",
    }
    
    template = {
        "index_patterns": [f"api-metrics-{bucket.value}-*"],
        "template": {
            "settings": {
                "number_of_shards": 2,
                "number_of_replicas": 1,
                "refresh_interval": refresh_intervals.get(bucket, "30s"),
                "index.codec": "best_compression",
                "index.mapping.total_fields.limit": 2000,
                "plugins.index_state_management.policy_id": policy_name,
            },
            "mappings": {
                "properties": {
                    # Core Identification
                    "id": {"type": "keyword"},
                    "gateway_id": {"type": "keyword"},
                    "api_id": {"type": "keyword"},
                    "application_id": {"type": "keyword"},
                    "operation": {"type": "keyword"},
                    
                    # Time Bucketing
                    "timestamp": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "time_bucket": {"type": "keyword"},
                    
                    # Request Counts
                    "request_count": {"type": "long"},
                    "success_count": {"type": "long"},
                    "failure_count": {"type": "long"},
                    "timeout_count": {"type": "long"},
                    "error_rate": {"type": "float"},
                    "availability": {"type": "float"},
                    
                    # Response Time Metrics (milliseconds)
                    "response_time_avg": {"type": "float"},
                    "response_time_min": {"type": "float"},
                    "response_time_max": {"type": "float"},
                    "response_time_p50": {"type": "float"},
                    "response_time_p95": {"type": "float"},
                    "response_time_p99": {"type": "float"},
                    
                    # Timing Breakdown
                    "gateway_time_avg": {"type": "float"},
                    "backend_time_avg": {"type": "float"},
                    
                    # Throughput
                    "throughput": {"type": "float"},
                    
                    # Data Transfer
                    "total_data_size": {"type": "long"},
                    "avg_request_size": {"type": "float"},
                    "avg_response_size": {"type": "float"},
                    
                    # Cache Metrics
                    "cache_hit_count": {"type": "long"},
                    "cache_miss_count": {"type": "long"},
                    "cache_bypass_count": {"type": "long"},
                    "cache_hit_rate": {"type": "float"},
                    
                    # HTTP Status Codes
                    "status_2xx_count": {"type": "long"},
                    "status_3xx_count": {"type": "long"},
                    "status_4xx_count": {"type": "long"},
                    "status_5xx_count": {"type": "long"},
                    "status_codes": {"type": "object", "enabled": False},
                    
                    # Per-Endpoint Breakdown
                    "endpoint_metrics": {
                        "type": "nested",
                        "properties": {
                            "endpoint": {"type": "keyword"},
                            "method": {"type": "keyword"},
                            "request_count": {"type": "long"},
                            "success_count": {"type": "long"},
                            "failure_count": {"type": "long"},
                            "error_rate": {"type": "float"},
                            "response_time_avg": {"type": "float"},
                            "response_time_p50": {"type": "float"},
                            "response_time_p95": {"type": "float"},
                            "response_time_p99": {"type": "float"},
                        }
                    },
                    
                    # Vendor-Specific Extensions
                    "vendor_metadata": {"type": "object", "enabled": False},
                    
                    # Metadata
                    "created_at": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                    "updated_at": {
                        "type": "date",
                        "format": "strict_date_optional_time||epoch_millis"
                    },
                }
            }
        },
        "priority": 100,
        "version": 1,
        "_meta": {
            "description": f"Template for {bucket.value} time-bucketed metrics",
            "managed_by": "api-intelligence-plane"
        }
    }
    
    return template


def create_index_template(client: OpenSearchClientType, bucket: TimeBucket) -> bool:
    """
    Create or update index template for a specific time bucket.
    
    Args:
        client: OpenSearch client instance
        bucket: Time bucket to create template for
        
    Returns:
        True if template created/updated successfully, False otherwise
    """
    template_name = f"api-metrics-{bucket.value}-template"
    template = get_metrics_index_template(bucket)
    
    try:
        # Use index templates API (OpenSearch 1.x+)
        client.indices.put_index_template(
            name=template_name,
            body=template
        )
        logger.info(f"Created/updated index template: {template_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create index template {template_name}: {e}", exc_info=True)
        return False


def create_all_index_templates(client: OpenSearchClientType) -> Dict[TimeBucket, bool]:
    """
    Create index templates for all time buckets.
    
    Args:
        client: OpenSearch client instance
        
    Returns:
        Dictionary mapping time buckets to success status
    """
    results = {}
    
    for bucket in TimeBucket:
        success = create_index_template(client, bucket)
        results[bucket] = success
    
    successful = sum(1 for success in results.values() if success)
    logger.info(f"Created {successful}/{len(results)} index templates")
    
    return results


def delete_index_template(client: OpenSearchClientType, bucket: TimeBucket) -> bool:
    """
    Delete index template for a specific time bucket.
    
    Args:
        client: OpenSearch client instance
        bucket: Time bucket to delete template for
        
    Returns:
        True if template deleted successfully, False otherwise
    """
    template_name = f"api-metrics-{bucket.value}-template"
    
    try:
        client.indices.delete_index_template(name=template_name)
        logger.info(f"Deleted index template: {template_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to delete index template {template_name}: {e}", exc_info=True)
        return False


def get_index_template_status(client: OpenSearchClientType, bucket: TimeBucket) -> Dict[str, Any]:
    """
    Get status of index template for a specific time bucket.
    
    Args:
        client: OpenSearch client instance
        bucket: Time bucket to check template for
        
    Returns:
        Dictionary with template status information
    """
    template_name = f"api-metrics-{bucket.value}-template"
    
    try:
        response = client.indices.get_index_template(name=template_name)
        
        return {
            "exists": True,
            "template_name": template_name,
            "bucket": bucket.value,
            "template": response
        }
        
    except Exception as e:
        return {
            "exists": False,
            "template_name": template_name,
            "bucket": bucket.value,
            "error": str(e)
        }


def create_transactional_logs_template(client: OpenSearchClientType) -> bool:
    """
    Create index template for transactional logs (daily indices).
    
    Args:
        client: OpenSearch client instance
        
    Returns:
        True if template created successfully, False otherwise
    """
    template_name = "transactional-logs-template"
    
    template = {
        "index_patterns": ["transactional-logs-*"],
        "template": {
            "settings": {
                "number_of_shards": 3,
                "number_of_replicas": 1,
                "refresh_interval": "5s",
                "index.codec": "best_compression",
            },
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "gateway_id": {"type": "keyword"},
                    "api_id": {"type": "keyword"},
                    "timestamp": {
                        "type": "date",
                        "format": "epoch_millis"
                    },
                    "method": {"type": "keyword"},
                    "path": {"type": "keyword"},
                    "status_code": {"type": "integer"},
                    "total_time_ms": {"type": "float"},
                    "gateway_time_ms": {"type": "float"},
                    "backend_time_ms": {"type": "float"},
                    "request_size": {"type": "long"},
                    "response_size": {"type": "long"},
                    "client_id": {"type": "keyword"},
                    "client_ip": {"type": "ip"},
                    "user_agent": {"type": "text"},
                    "error_message": {"type": "text"},
                    "external_calls": {"type": "object", "enabled": False},
                    "vendor_metadata": {"type": "object", "enabled": False},
                }
            }
        },
        "priority": 100,
        "version": 1,
        "_meta": {
            "description": "Template for daily transactional logs",
            "managed_by": "api-intelligence-plane"
        }
    }
    
    try:
        client.indices.put_index_template(
            name=template_name,
            body=template
        )
        logger.info(f"Created/updated index template: {template_name}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create transactional logs template: {e}", exc_info=True)
        return False


# Made with Bob