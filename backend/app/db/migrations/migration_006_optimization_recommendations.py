"""
Migration 006: Optimization Recommendations Index

Creates the optimization-recommendations index for storing performance
optimization suggestions with estimated impact and implementation tracking.
"""

from opensearchpy import OpenSearch


def create_optimization_recommendations_index(client: OpenSearch):
    """
    Create the optimization-recommendations index with appropriate mappings.
    
    This index stores:
    - Performance optimization recommendations
    - Estimated impact and cost savings
    - Implementation effort and steps
    - Validation results and actual impact
    - Priority and status tracking
    """
    
    index_name = "optimization-recommendations"
    
    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": "30s",
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "recommendation_type": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "description": {"type": "text"},
                "priority": {"type": "keyword"},
                "estimated_impact": {
                    "type": "object",
                    "properties": {
                        "metric": {"type": "keyword"},
                        "current_value": {"type": "float"},
                        "expected_value": {"type": "float"},
                        "improvement_percentage": {"type": "float"},
                        "confidence": {"type": "float"},
                    },
                },
                "implementation_effort": {"type": "keyword"},
                "implementation_steps": {"type": "text"},
                "status": {"type": "keyword"},
                "implemented_at": {"type": "date"},
                "validation_results": {
                    "type": "object",
                    "properties": {
                        "actual_impact": {
                            "type": "object",
                            "properties": {
                                "metric": {"type": "keyword"},
                                "before_value": {"type": "float"},
                                "after_value": {"type": "float"},
                                "actual_improvement": {"type": "float"},
                            },
                        },
                        "success": {"type": "boolean"},
                        "measured_at": {"type": "date"},
                    },
                },
                "cost_savings": {"type": "float"},
                "metadata": {"type": "object", "enabled": True},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
                "expires_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
