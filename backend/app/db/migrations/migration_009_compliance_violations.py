"""
Migration 009: Compliance Violations Index

Creates the compliance-violations index for storing compliance violation findings,
audit trail, remediation documentation, and compliance posture information.
"""

from opensearchpy import OpenSearch


def create_compliance_violations_index(client: OpenSearch):
    """
    Create the compliance-violations index with appropriate mappings.
    
    This index stores:
    - Compliance violations for GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001
    - Evidence from Gateway-level observations
    - Complete audit trail for compliance reporting
    - Remediation documentation suitable for auditors
    - Regulatory references and risk levels
    """
    
    index_name = "compliance-violations"
    
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
                "compliance_standard": {"type": "keyword"},
                "violation_type": {"type": "keyword"},
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
                "evidence": {
                    "type": "nested",
                    "properties": {
                        "type": {"type": "keyword"},
                        "description": {"type": "text"},
                        "source": {"type": "keyword"},
                        "timestamp": {"type": "date"},
                        "data": {"type": "object", "enabled": True},
                    },
                },
                "audit_trail": {
                    "type": "nested",
                    "properties": {
                        "timestamp": {"type": "date"},
                        "action": {"type": "keyword"},
                        "performed_by": {"type": "keyword"},
                        "details": {"type": "text"},
                        "status_before": {"type": "keyword"},
                        "status_after": {"type": "keyword"},
                    },
                },
                "remediation_documentation": {
                    "type": "nested",
                    "properties": {
                        "action": {"type": "text"},
                        "type": {"type": "keyword"},
                        "status": {"type": "keyword"},
                        "performed_at": {"type": "date"},
                        "performed_by": {"type": "keyword"},
                        "gateway_policy_id": {"type": "keyword"},
                        "verification_method": {"type": "keyword"},
                        "verification_status": {"type": "keyword"},
                        "notes": {"type": "text"},
                    },
                },
                "regulatory_reference": {"type": "text"},
                "risk_level": {"type": "keyword"},
                "remediation_deadline": {"type": "date"},
                "remediated_at": {"type": "date"},
                "last_audit_date": {"type": "date"},
                "next_audit_date": {"type": "date"},
                "metadata": {"type": "object", "enabled": True},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            }
        },
    }
    
    client.indices.create(index=index_name, body=index_body)


# Made with Bob