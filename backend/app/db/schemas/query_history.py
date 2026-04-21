"""
Schema: Query History Index

Creates the query-history index for storing natural language queries,
interpreted intents, results, and user feedback for continuous improvement.
"""

from opensearchpy import OpenSearch


def create_query_history_index(client: OpenSearch):
    """
    Create the query-history index with appropriate mappings.
    
    This index stores:
    - Natural language queries from users
    - Interpreted intents and entity extraction
    - Generated OpenSearch queries
    - Query results and execution metrics
    - User feedback for improvement
    """
    
    index_name = "query-history"
    
    index_body = {
        "settings": {
            "number_of_shards": 1,
            "number_of_replicas": 1,
            "refresh_interval": "10s",
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "session_id": {"type": "keyword"},
                "user_id": {"type": "keyword"},
                "query_text": {"type": "text"},
                "query_type": {"type": "keyword"},
                "interpreted_intent": {
                    "type": "object",
                    "properties": {
                        "action": {"type": "keyword"},
                        "entities": {"type": "keyword"},
                        "filters": {"type": "object", "enabled": True},
                        "time_range": {
                            "type": "object",
                            "properties": {
                                "start": {"type": "date"},
                                "end": {"type": "date"},
                            },
                        },
                    },
                },
                "opensearch_query": {"type": "object", "enabled": True},
                "results": {
                    "type": "object",
                    "properties": {
                        "data": {"type": "object", "enabled": False},
                        "count": {"type": "integer"},
                        "execution_time": {"type": "integer"},
                        "aggregations": {"type": "object", "enabled": True},
                    },
                },
                "response_text": {"type": "text"},
                "confidence_score": {"type": "float"},
                "execution_time_ms": {"type": "integer"},
                "feedback": {"type": "keyword"},
                "feedback_comment": {"type": "text"},
                "follow_up_queries": {"type": "keyword"},
                "metadata": {"type": "object", "enabled": True},
                "created_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
