"""
Migration 004: Predictions Index

Creates the api-predictions index for storing AI-generated failure predictions
with confidence scores, contributing factors, and recommended actions.
"""

from opensearchpy import OpenSearch


def create_predictions_index(client: OpenSearch):
    """
    Create the api-predictions index with appropriate mappings.
    
    This index stores:
    - Failure predictions for APIs
    - Confidence scores and severity levels
    - Contributing factors and analysis
    - Recommended preventive actions
    - Actual outcomes for accuracy tracking
    """
    
    index_name = "api-predictions"
    
    index_body = {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "refresh_interval": "15s",
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "prediction_type": {"type": "keyword"},
                "predicted_at": {"type": "date"},
                "predicted_time": {"type": "date"},
                "confidence_score": {"type": "float"},
                "severity": {"type": "keyword"},
                "status": {"type": "keyword"},
                "contributing_factors": {
                    "type": "nested",
                    "properties": {
                        "factor": {"type": "keyword"},
                        "current_value": {"type": "float"},
                        "threshold": {"type": "float"},
                        "trend": {"type": "keyword"},
                        "weight": {"type": "float"},
                    },
                },
                "recommended_actions": {"type": "text"},
                "actual_outcome": {"type": "keyword"},
                "actual_time": {"type": "date"},
                "accuracy_score": {"type": "float"},
                "model_version": {"type": "keyword"},
                "metadata": {"type": "object", "enabled": True},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
