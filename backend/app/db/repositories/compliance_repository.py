"""Compliance Violation repository for API Intelligence Plane.

Provides CRUD operations and queries for compliance violations.
"""

from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from opensearchpy import OpenSearch

from app.db.repositories.base import BaseRepository
from app.models.compliance import ComplianceViolation, ComplianceStatus, ComplianceStandard


class ComplianceRepository(BaseRepository[ComplianceViolation]):
    """Repository for ComplianceViolation entities."""

    def __init__(self):
        """Initialize repository."""
        super().__init__(
            index_name="compliance-violations",
            model_class=ComplianceViolation,
        )

    async def find_by_api_id(
        self,
        api_id: UUID,
        status: Optional[ComplianceStatus] = None,
        limit: int = 100,
    ) -> list[ComplianceViolation]:
        """Find compliance violations for a specific API.

        Args:
            api_id: API identifier
            status: Optional status filter
            limit: Maximum results to return

        Returns:
            List of compliance violations
        """
        query: dict[str, Any] = {
            "bool": {
                "must": [
                    {"term": {"api_id": str(api_id)}},
                ]
            }
        }

        if status:
            query["bool"]["must"].append({"term": {"status": status.value}})

        body = {
            "query": query,
            "sort": [{"detected_at": {"order": "desc"}}],
            "size": limit,
        }

        response = self.client.search(index=self.index_name, body=body)
        return [
            self.model_class(**hit["_source"]) for hit in response["hits"]["hits"]
        ]

    async def find_by_standard(
        self,
        standard: ComplianceStandard,
        status: Optional[ComplianceStatus] = None,
        limit: int = 100,
    ) -> list[ComplianceViolation]:
        """Find violations by compliance standard.

        Args:
            standard: Compliance standard (GDPR, HIPAA, SOC2, PCI-DSS, ISO 27001)
            status: Optional status filter
            limit: Maximum results to return

        Returns:
            List of compliance violations
        """
        query: dict[str, Any] = {
            "bool": {
                "must": [
                    {"term": {"compliance_standard": standard.value}},
                ]
            }
        }

        if status:
            query["bool"]["must"].append({"term": {"status": status.value}})

        body = {
            "query": query,
            "sort": [{"detected_at": {"order": "desc"}}],
            "size": limit,
        }

        response = self.client.search(index=self.index_name, body=body)
        return [
            self.model_class(**hit["_source"]) for hit in response["hits"]["hits"]
        ]

    async def find_by_severity(
        self,
        severity: str,
        status: Optional[ComplianceStatus] = None,
        limit: int = 100,
    ) -> list[ComplianceViolation]:
        """Find violations by severity level.

        Args:
            severity: Severity level (critical, high, medium, low)
            status: Optional status filter
            limit: Maximum results to return

        Returns:
            List of compliance violations
        """
        query: dict[str, Any] = {
            "bool": {
                "must": [
                    {"term": {"severity": severity}},
                ]
            }
        }

        if status:
            query["bool"]["must"].append({"term": {"status": status.value}})

        body = {
            "query": query,
            "sort": [{"detected_at": {"order": "desc"}}],
            "size": limit,
        }

        response = self.client.search(index=self.index_name, body=body)
        return [
            self.model_class(**hit["_source"]) for hit in response["hits"]["hits"]
        ]

    async def find_open_violations(
        self,
        api_id: Optional[UUID] = None,
        standard: Optional[ComplianceStandard] = None,
        limit: int = 100,
    ) -> list[ComplianceViolation]:
        """Find all open compliance violations.

        Args:
            api_id: Optional API filter
            standard: Optional compliance standard filter
            limit: Maximum results to return

        Returns:
            List of open compliance violations
        """
        query: dict[str, Any] = {
            "bool": {
                "must": [
                    {"term": {"status": ComplianceStatus.OPEN.value}},
                ]
            }
        }

        if api_id:
            query["bool"]["must"].append({"term": {"api_id": str(api_id)}})
        
        if standard:
            query["bool"]["must"].append({"term": {"compliance_standard": standard.value}})

        body = {
            "query": query,
            "sort": [
                {"severity": {"order": "asc"}},  # Critical first
                {"detected_at": {"order": "desc"}},
            ],
            "size": limit,
        }

        response = self.client.search(index=self.index_name, body=body)
        return [
            self.model_class(**hit["_source"]) for hit in response["hits"]["hits"]
        ]

    async def get_compliance_posture(
        self,
        api_id: Optional[UUID] = None,
        standard: Optional[ComplianceStandard] = None,
    ) -> dict[str, Any]:
        """Get compliance posture statistics.

        Args:
            api_id: Optional API filter
            standard: Optional compliance standard filter

        Returns:
            Compliance posture metrics
        """
        query: dict[str, Any] = {"bool": {"must": []}}

        if api_id:
            query["bool"]["must"].append({"term": {"api_id": str(api_id)}})
        
        if standard:
            query["bool"]["must"].append({"term": {"compliance_standard": standard.value}})

        if not query["bool"]["must"]:
            query = {"match_all": {}}

        body = {
            "query": query,
            "size": 0,
            "aggs": {
                "by_severity": {
                    "terms": {"field": "severity", "size": 10}
                },
                "by_status": {
                    "terms": {"field": "status", "size": 10}
                },
                "by_standard": {
                    "terms": {"field": "compliance_standard", "size": 10}
                },
                "by_violation_type": {
                    "terms": {"field": "violation_type", "size": 20}
                },
                "avg_remediation_time": {
                    "avg": {
                        "script": {
                            "source": """
                                if (doc['remediated_at'].size() > 0 && doc['detected_at'].size() > 0) {
                                    return doc['remediated_at'].value.toInstant().toEpochMilli() - 
                                           doc['detected_at'].value.toInstant().toEpochMilli();
                                }
                                return null;
                            """
                        }
                    }
                },
                "violations_by_month": {
                    "date_histogram": {
                        "field": "detected_at",
                        "calendar_interval": "month"
                    }
                },
            },
        }

        response = self.client.search(index=self.index_name, body=body)
        aggs = response["aggregations"]

        return {
            "total_violations": response["hits"]["total"]["value"],
            "by_severity": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_severity"]["buckets"]
            },
            "by_status": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_status"]["buckets"]
            },
            "by_standard": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_standard"]["buckets"]
            },
            "by_violation_type": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_violation_type"]["buckets"]
            },
            "avg_remediation_time_ms": aggs["avg_remediation_time"].get("value"),
            "violations_by_month": [
                {
                    "month": bucket["key_as_string"],
                    "count": bucket["doc_count"]
                }
                for bucket in aggs["violations_by_month"]["buckets"]
            ],
        }

    async def find_violations_needing_audit(
        self,
        days_until_audit: int = 30,
        limit: int = 100,
    ) -> list[ComplianceViolation]:
        """Find violations that need attention before upcoming audit.

        Args:
            days_until_audit: Days until next audit
            limit: Maximum results to return

        Returns:
            List of violations needing attention
        """
        from datetime import timedelta
        
        audit_date = datetime.utcnow() + timedelta(days=days_until_audit)
        
        query = {
            "bool": {
                "should": [
                    # Open violations
                    {"term": {"status": ComplianceStatus.OPEN.value}},
                    # In progress violations
                    {"term": {"status": ComplianceStatus.IN_PROGRESS.value}},
                ],
                "minimum_should_match": 1,
                "must": [
                    # Next audit date is approaching
                    {
                        "range": {
                            "next_audit_date": {
                                "lte": audit_date.isoformat()
                            }
                        }
                    }
                ]
            }
        }

        body = {
            "query": query,
            "sort": [
                {"severity": {"order": "asc"}},  # Critical first
                {"next_audit_date": {"order": "asc"}},  # Soonest audit first
            ],
            "size": limit,
        }

        response = self.client.search(index=self.index_name, body=body)
        return [
            self.model_class(**hit["_source"]) for hit in response["hits"]["hits"]
        ]

    async def generate_audit_report_data(
        self,
        standard: Optional[ComplianceStandard] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict[str, Any]:
        """Generate data for audit report.

        Args:
            standard: Optional compliance standard filter
            start_date: Optional start date for report period
            end_date: Optional end date for report period

        Returns:
            Audit report data
        """
        query: dict[str, Any] = {"bool": {"must": []}}

        if standard:
            query["bool"]["must"].append({"term": {"compliance_standard": standard.value}})
        
        if start_date or end_date:
            date_range: dict[str, Any] = {}
            if start_date:
                date_range["gte"] = start_date.isoformat()
            if end_date:
                date_range["lte"] = end_date.isoformat()
            query["bool"]["must"].append({"range": {"detected_at": date_range}})

        if not query["bool"]["must"]:
            query = {"match_all": {}}

        body = {
            "query": query,
            "size": 0,
            "aggs": {
                "total_violations": {
                    "value_count": {"field": "id"}
                },
                "by_severity": {
                    "terms": {"field": "severity", "size": 10}
                },
                "by_status": {
                    "terms": {"field": "status", "size": 10}
                },
                "by_standard": {
                    "terms": {"field": "compliance_standard", "size": 10}
                },
                "by_violation_type": {
                    "terms": {"field": "violation_type", "size": 30}
                },
                "remediated_count": {
                    "filter": {"term": {"status": ComplianceStatus.REMEDIATED.value}}
                },
                "open_count": {
                    "filter": {"term": {"status": ComplianceStatus.OPEN.value}}
                },
                "critical_count": {
                    "filter": {"term": {"severity": "critical"}}
                },
                "high_count": {
                    "filter": {"term": {"severity": "high"}}
                },
            },
        }

        response = self.client.search(index=self.index_name, body=body)
        aggs = response["aggregations"]

        total = response["hits"]["total"]["value"]
        remediated = aggs["remediated_count"]["doc_count"]
        
        return {
            "report_period": {
                "start_date": start_date.isoformat() if start_date else None,
                "end_date": end_date.isoformat() if end_date else None,
            },
            "summary": {
                "total_violations": total,
                "remediated_violations": remediated,
                "open_violations": aggs["open_count"]["doc_count"],
                "critical_violations": aggs["critical_count"]["doc_count"],
                "high_violations": aggs["high_count"]["doc_count"],
                "remediation_rate": (remediated / total * 100) if total > 0 else 0,
            },
            "by_severity": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_severity"]["buckets"]
            },
            "by_status": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_status"]["buckets"]
            },
            "by_standard": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_standard"]["buckets"]
            },
            "by_violation_type": {
                bucket["key"]: bucket["doc_count"]
                for bucket in aggs["by_violation_type"]["buckets"]
            },
        }


# Made with Bob