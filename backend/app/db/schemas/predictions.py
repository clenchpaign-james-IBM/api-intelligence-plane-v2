"""
Schema: Predictions Index

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
                "gateway_id": {"type": "keyword"},
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
                
                # Remediation fields
                "remediation_type": {"type": "keyword"},
                "remediation_actions": {
                    "type": "nested",
                    "properties": {
                        "action": {"type": "text"},
                        "type": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "performed_at": {"type": "date"},
                        "performed_by": {"type": "keyword"},
                        "gateway_policy_id": {"type": "keyword"},
                        "configuration_before": {"type": "object", "enabled": False},
                        "configuration_after": {"type": "object", "enabled": False},
                        "effectiveness_score": {"type": "float"},
                        "error_message": {"type": "text"},
                        "rollback_available": {"type": "boolean"},
                        "rollback_performed_at": {"type": "date"},
                    },
                },
                "remediation_effectiveness": {"type": "float"},
                
                # Per-prediction remediation plan fields
                "recommended_remediation": {"type": "object", "enabled": True},
                "recommended_priority": {"type": "keyword"},
                "recommended_verification_steps": {"type": "text"},
                "recommended_estimated_time_minutes": {"type": "float"},
                "plan_generated_at": {"type": "date"},
                "plan_source": {"type": "keyword"},
                "plan_version": {"type": "keyword"},
                "plan_status": {"type": "keyword"},
                
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
