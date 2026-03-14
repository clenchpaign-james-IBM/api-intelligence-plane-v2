"""
Cleanup script to remove recommendations with invalid types from OpenSearch.

This script deletes recommendations with types that are no longer supported:
- query_optimization
- resource_allocation
- connection_pooling
"""

from opensearchpy import OpenSearch
import os

def cleanup_invalid_recommendations():
    """Delete recommendations with invalid types using raw OpenSearch client."""
    
    # Create OpenSearch client
    client = OpenSearch(
        hosts=[{
            'host': os.getenv('OPENSEARCH_HOST', 'opensearch'),
            'port': int(os.getenv('OPENSEARCH_PORT', 9200))
        }],
        http_auth=(
            os.getenv('OPENSEARCH_USER', 'admin'),
            os.getenv('OPENSEARCH_PASSWORD', 'admin')
        ),
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False
    )
    
    # Invalid types to remove
    invalid_types = ["query_optimization", "resource_allocation", "connection_pooling"]
    
    try:
        # Search for recommendations with invalid types (without validation)
        query = {
            "query": {
                "terms": {
                    "recommendation_type": invalid_types
                }
            },
            "size": 1000
        }
        
        response = client.search(
            index="optimization-recommendations",
            body=query
        )
        
        hits = response["hits"]["hits"]
        print(f"Found {len(hits)} recommendations with invalid types")
        
        # Delete each one
        deleted_count = 0
        for hit in hits:
            doc_id = hit["_id"]
            rec_type = hit["_source"]["recommendation_type"]
            api_id = hit["_source"].get("api_id", "unknown")
            
            try:
                client.delete(
                    index="optimization-recommendations",
                    id=doc_id
                )
                deleted_count += 1
                print(f"Deleted recommendation {doc_id} (type: {rec_type}, api: {api_id})")
            except Exception as e:
                print(f"Failed to delete {doc_id}: {e}")
        
        print(f"\nSuccessfully deleted {deleted_count} invalid recommendations")
        
    except Exception as e:
        print(f"Error during cleanup: {e}")
        raise
    finally:
        client.close()

if __name__ == "__main__":
    cleanup_invalid_recommendations()

# Made with Bob
