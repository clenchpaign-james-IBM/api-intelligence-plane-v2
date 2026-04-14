"""
Migration 005: Security Findings Index

Creates the security-findings index for storing vulnerability scan results,
remediation status, and security posture information.
"""

from opensearchpy import OpenSearch


def create_security_findings_index(client: OpenSearch):
    """
    Create the security-findings index with appropriate mappings.
    
    This index stores:
    - Security vulnerabilities discovered in APIs
    - CVE identifiers and CVSS scores
    - Remediation status and actions
    - Verification results
    - Affected endpoints and detection methods
    """
    
    index_name = "security-findings"
    
    index_body = {
        "settings": {
            "number_of_shards": 2,
            "number_of_replicas": 1,
            "refresh_interval": "30s",
        },
        "mappings": {
            "properties": {
                "id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "vulnerability_type": {"type": "keyword"},
                "cve_id": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "title": {
                    "type": "text",
                    "fields": {"keyword": {"type": "keyword", "ignore_above": 256}},
                },
                "description": {"type": "text"},
                "affected_endpoints": {"type": "keyword"},
                "detection_method": {"type": "keyword"},
                "detected_at": {"type": "date"},
                "status": {"type": "keyword"},
                "remediation_type": {"type": "keyword"},
                "remediation_actions": {
                    "type": "nested",
                    "properties": {
                        "action": {"type": "text"},
                        "type": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "performed_at": {"type": "date"},
                        "performed_by": {"type": "keyword"},
                    },
                },
                "remediated_at": {"type": "date"},
                "verification_status": {"type": "keyword"},
                "cvss_score": {"type": "float"},
                "references": {"type": "keyword"},
                "metadata": {"type": "object", "enabled": True},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)

# Made with Bob
