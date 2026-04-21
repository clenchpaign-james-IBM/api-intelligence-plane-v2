"""
Schema: Rate Limit Policies Index

Creates the rate-limit-policies index for storing dynamic rate limiting
configurations with adaptive thresholds and priority-based rules.
"""

from opensearchpy import OpenSearch


def create_rate_limit_policies_index(client: OpenSearch):
    """
    Create the rate-limit-policies index with appropriate mappings.
    
    This index stores:
    - Rate limiting policy configurations
    - Limit thresholds and burst allowances
    - Priority-based rules and consumer tiers
    - Adaptation parameters for dynamic policies
    - Effectiveness tracking
    """
    
    index_name = "rate-limit-policies"
    
    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": "10s",
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "policy_name": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "policy_type": {"type": "keyword"},
                "status": {"type": "keyword"},
                "limit_thresholds": {
                    "type": "object",
                    "properties": {
                        "requests_per_second": {"type": "integer"},
                        "requests_per_minute": {"type": "integer"},
                        "requests_per_hour": {"type": "integer"},
                        "concurrent_requests": {"type": "integer"},
                    },
                },
                "priority_rules": {
                    "type": "nested",
                    "properties": {
                        "tier": {"type": "keyword"},
                        "multiplier": {"type": "float"},
                        "guaranteed_throughput": {"type": "integer"},
                        "burst_multiplier": {"type": "float"},
                    },
                },
                "burst_allowance": {"type": "integer"},
                "adaptation_parameters": {
                    "type": "object",
                    "properties": {
                        "learning_rate": {"type": "float"},
                        "adjustment_frequency": {"type": "keyword"},
                    },
                },
                "consumer_tiers": {
                    "type": "nested",
                    "properties": {
                        "tier_name": {"type": "keyword"},
                        "tier_level": {"type": "integer"},
                        "rate_multiplier": {"type": "float"},
                        "priority_score": {"type": "integer"},
                    },
                },
                "enforcement_action": {"type": "keyword"},
                "applied_at": {"type": "date"},
                "last_adjusted_at": {"type": "date"},
                "effectiveness_score": {"type": "float"},
                "metadata": {"type": "object", "enabled": True},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
