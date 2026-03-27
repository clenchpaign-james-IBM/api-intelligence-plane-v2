"""Generate mock security vulnerability data for API Intelligence Plane.

This script generates realistic mock data for the Security feature use case:
"Monitor security vulnerabilities and track automated remediation"

It creates:
- Security vulnerabilities across different severity levels
- Various vulnerability types (authentication, authorization, injection, etc.)
- Remediation actions and tracking
- Verification status
- CVE identifiers and CVSS scores
"""

import asyncio
import logging
import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.client import get_opensearch_client
from app.models.vulnerability import (
    VulnerabilityType,
    VulnerabilitySeverity,
    DetectionMethod,
    VulnerabilityStatus,
    RemediationType,
    VerificationStatus,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SecurityMockDataGenerator:
    """Generate mock security vulnerability data."""

    def __init__(self):
        """Initialize security mock data generator."""
        self.os_client = get_opensearch_client()
        self.api_ids = []
        self.vulnerability_ids = []

    def get_existing_apis(self):
        """Fetch existing API IDs from OpenSearch."""
        try:
            response = self.os_client.client.search(
                index="api-inventory",
                body={"query": {"match_all": {}}, "size": 100},
            )
            self.api_ids = [hit["_source"]["id"] for hit in response["hits"]["hits"]]
            logger.info(f"Found {len(self.api_ids)} existing APIs")
        except Exception as e:
            logger.warning(f"Could not fetch existing APIs: {e}")
            # Generate some mock API IDs if none exist
            self.api_ids = [str(uuid4()) for _ in range(10)]
            logger.info(f"Generated {len(self.api_ids)} mock API IDs")

    def generate_all(self, num_vulnerabilities: int = 50):
        """Generate all mock security data.

        Args:
            num_vulnerabilities: Number of vulnerabilities to create
        """
        logger.info("Starting security mock data generation...")

        # Get existing APIs
        self.get_existing_apis()

        if not self.api_ids:
            logger.error("No APIs available. Please generate API data first.")
            return

        # Generate vulnerabilities with various statuses
        self.generate_vulnerabilities(num_vulnerabilities)

        logger.info("Security mock data generation complete!")
        logger.info(f"Created {len(self.vulnerability_ids)} vulnerabilities")

    def generate_vulnerabilities(self, count: int = 50):
        """Generate mock vulnerabilities with realistic scenarios.

        Args:
            count: Number of vulnerabilities to create
        """
        logger.info(f"Generating {count} mock vulnerabilities...")

        # Vulnerability templates with realistic scenarios
        vulnerability_templates = [
            {
                "type": VulnerabilityType.AUTHENTICATION,
                "titles": [
                    "Weak JWT Token Validation",
                    "Missing API Key Validation",
                    "Insecure Basic Authentication",
                    "OAuth2 Token Expiration Not Enforced",
                    "API Key Transmitted in URL Parameters",
                ],
                "descriptions": [
                    "The API does not properly validate JWT token signatures, allowing potential token forgery attacks.",
                    "API endpoints are accessible without proper API key validation, exposing sensitive operations.",
                    "Basic authentication is used over non-HTTPS connections, exposing credentials.",
                    "OAuth2 access tokens do not expire or have excessively long expiration times.",
                    "API keys are transmitted in URL query parameters instead of headers, exposing them in logs.",
                ],
            },
            {
                "type": VulnerabilityType.AUTHORIZATION,
                "titles": [
                    "Missing Role-Based Access Control",
                    "Broken Object Level Authorization",
                    "Privilege Escalation Vulnerability",
                    "Insufficient Function Level Authorization",
                    "Missing Resource-Level Permissions",
                ],
                "descriptions": [
                    "API endpoints lack proper role-based access control, allowing unauthorized access to admin functions.",
                    "Users can access or modify objects belonging to other users by manipulating object IDs.",
                    "Regular users can escalate privileges to admin level through API manipulation.",
                    "Function-level authorization checks are missing, allowing access to sensitive operations.",
                    "Resource-level permissions are not enforced, allowing cross-tenant data access.",
                ],
            },
            {
                "type": VulnerabilityType.INJECTION,
                "titles": [
                    "SQL Injection Vulnerability",
                    "NoSQL Injection Risk",
                    "Command Injection Vulnerability",
                    "LDAP Injection Vulnerability",
                    "XML External Entity (XXE) Injection",
                ],
                "descriptions": [
                    "User input is not properly sanitized before being used in SQL queries, allowing SQL injection attacks.",
                    "NoSQL query parameters are not validated, allowing NoSQL injection attacks.",
                    "User input is passed directly to system commands without sanitization.",
                    "LDAP queries are constructed using unsanitized user input.",
                    "XML parser processes external entities, allowing XXE attacks.",
                ],
            },
            {
                "type": VulnerabilityType.EXPOSURE,
                "titles": [
                    "Sensitive Data Exposure in Logs",
                    "API Keys Exposed in Response Headers",
                    "PII Data Returned Without Encryption",
                    "Internal System Details Leaked",
                    "Excessive Data Exposure in API Response",
                ],
                "descriptions": [
                    "Sensitive information including passwords and tokens are logged in plain text.",
                    "API keys and secrets are inadvertently exposed in HTTP response headers.",
                    "Personally Identifiable Information (PII) is transmitted without encryption.",
                    "Error messages reveal internal system architecture and database structure.",
                    "API responses include unnecessary sensitive fields that should be filtered.",
                ],
            },
            {
                "type": VulnerabilityType.CONFIGURATION,
                "titles": [
                    "Missing Rate Limiting",
                    "CORS Misconfiguration",
                    "Insecure TLS Configuration",
                    "Default Credentials in Use",
                    "Debug Mode Enabled in Production",
                ],
                "descriptions": [
                    "API endpoints lack rate limiting, making them vulnerable to DoS attacks.",
                    "CORS policy allows requests from any origin, enabling cross-site attacks.",
                    "TLS configuration uses weak ciphers or outdated protocols (TLS 1.0/1.1).",
                    "Default administrative credentials have not been changed.",
                    "Debug mode is enabled in production, exposing sensitive debugging information.",
                ],
            },
            {
                "type": VulnerabilityType.DEPENDENCY,
                "titles": [
                    "Vulnerable Third-Party Library",
                    "Outdated Framework Version",
                    "Known CVE in Dependency",
                    "Unpatched Security Vulnerability",
                    "End-of-Life Software Component",
                ],
                "descriptions": [
                    "Third-party library has known security vulnerabilities that need updating.",
                    "Framework version is outdated and contains multiple security patches.",
                    "Dependency has a known CVE with available security patches.",
                    "Security vulnerability in dependency has been disclosed but not patched.",
                    "Software component has reached end-of-life and no longer receives security updates.",
                ],
            },
        ]

        # Status distribution (realistic scenario)
        status_distribution = [
            (VulnerabilityStatus.OPEN, 0.30),  # 30% open
            (VulnerabilityStatus.IN_PROGRESS, 0.25),  # 25% in progress
            (VulnerabilityStatus.REMEDIATED, 0.35),  # 35% remediated
            (VulnerabilityStatus.ACCEPTED_RISK, 0.05),  # 5% accepted risk
            (VulnerabilityStatus.FALSE_POSITIVE, 0.05),  # 5% false positive
        ]

        # Severity distribution (realistic scenario)
        severity_distribution = [
            (VulnerabilitySeverity.CRITICAL, 0.10),  # 10% critical
            (VulnerabilitySeverity.HIGH, 0.25),  # 25% high
            (VulnerabilitySeverity.MEDIUM, 0.40),  # 40% medium
            (VulnerabilitySeverity.LOW, 0.25),  # 25% low
        ]

        for i in range(count):
            # Select random template
            template = random.choice(vulnerability_templates)
            vuln_type = template["type"]
            title_idx = random.randint(0, len(template["titles"]) - 1)
            title = template["titles"][title_idx]
            description = template["descriptions"][title_idx]

            # Select severity based on distribution
            severity = self._weighted_choice(severity_distribution)

            # Select status based on distribution
            status = self._weighted_choice(status_distribution)

            # Generate CVE ID (50% chance)
            cve_id = None
            if random.random() < 0.5:
                year = random.randint(2022, 2026)
                cve_num = random.randint(1000, 9999)
                cve_id = f"CVE-{year}-{cve_num}"

            # Generate CVSS score based on severity
            cvss_score = self._generate_cvss_score(severity)

            # Generate detection timestamp (within last 90 days)
            detected_at = datetime.utcnow() - timedelta(
                days=random.randint(1, 90),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59),
            )

            # Generate affected endpoints
            num_endpoints = random.randint(1, 5)
            affected_endpoints = [
                f"/api/v{random.randint(1,3)}/{random.choice(['users', 'orders', 'products', 'payments', 'admin'])}/{random.choice(['', '{id}', 'list', 'search'])}"
                for _ in range(num_endpoints)
            ]

            # Determine remediation type
            remediation_type = None
            if status != VulnerabilityStatus.OPEN:
                if vuln_type in [
                    VulnerabilityType.CONFIGURATION,
                    VulnerabilityType.AUTHENTICATION,
                ]:
                    remediation_type = RemediationType.AUTOMATED
                elif vuln_type == VulnerabilityType.DEPENDENCY:
                    remediation_type = RemediationType.UPGRADE
                else:
                    remediation_type = random.choice(
                        [RemediationType.MANUAL, RemediationType.CONFIGURATION]
                    )

            # Generate remediation actions if not open
            remediation_actions = None
            remediated_at = None
            if status in [
                VulnerabilityStatus.IN_PROGRESS,
                VulnerabilityStatus.REMEDIATED,
            ]:
                remediation_actions = self._generate_remediation_actions(
                    vuln_type, status, detected_at
                )
                if status == VulnerabilityStatus.REMEDIATED:
                    # Remediated 1-30 days after detection
                    remediated_at = detected_at + timedelta(
                        days=random.randint(1, 30),
                        hours=random.randint(0, 23),
                    )

            # Generate verification status
            verification_status = None
            if status == VulnerabilityStatus.REMEDIATED:
                verification_status = random.choice(
                    [
                        VerificationStatus.VERIFIED,
                        VerificationStatus.VERIFIED,
                        VerificationStatus.VERIFIED,
                        VerificationStatus.PENDING,
                    ]
                )  # 75% verified
            elif status == VulnerabilityStatus.IN_PROGRESS:
                verification_status = VerificationStatus.PENDING

            # Generate references
            references = []
            if cve_id:
                references.append(f"https://nvd.nist.gov/vuln/detail/{cve_id}")
            references.extend(
                [
                    "https://owasp.org/www-project-top-ten/",
                    f"https://cwe.mitre.org/data/definitions/{random.randint(1, 1000)}.html",
                ]
            )

            # Generate remediation text based on type
            remediation_texts = {
                VulnerabilityType.AUTHENTICATION: "Implement proper authentication mechanisms and enforce strong token validation.",
                VulnerabilityType.AUTHORIZATION: "Apply role-based access control (RBAC) and enforce authorization checks at all levels.",
                VulnerabilityType.INJECTION: "Sanitize all user inputs and use parameterized queries to prevent injection attacks.",
                VulnerabilityType.EXPOSURE: "Remove sensitive data from logs and responses, implement proper data encryption.",
                VulnerabilityType.CONFIGURATION: "Update security configurations, apply recommended policies at gateway level.",
                VulnerabilityType.DEPENDENCY: "Update vulnerable dependencies to latest secure versions and apply security patches.",
            }
            remediation = remediation_texts.get(vuln_type, "Review and apply security best practices.")

            vulnerability_id = str(uuid4())
            vulnerability = {
                "id": vulnerability_id,
                "api_id": random.choice(self.api_ids),
                "vulnerability_type": vuln_type.value,
                "category": vuln_type.value,  # Add category field for frontend compatibility
                "cve_id": cve_id,
                "severity": severity.value,
                "title": title,
                "description": description,
                "affected_endpoints": affected_endpoints,
                "remediation": remediation,
                "detection_method": random.choice(
                    [
                        DetectionMethod.AUTOMATED_SCAN.value,
                        DetectionMethod.AUTOMATED_SCAN.value,
                        DetectionMethod.AUTOMATED_SCAN.value,
                        DetectionMethod.MANUAL_REVIEW.value,
                        DetectionMethod.EXTERNAL_REPORT.value,
                    ]
                ),  # 60% automated
                "detected_at": detected_at.isoformat(),
                "status": status.value,
                "remediation_type": remediation_type.value if remediation_type else None,
                "remediation_actions": remediation_actions,
                "remediated_at": remediated_at.isoformat() if remediated_at else None,
                "resolved_at": remediated_at.isoformat() if remediated_at else None,  # Add resolved_at for frontend
                "verification_status": (
                    verification_status.value if verification_status else None
                ),
                "cvss_score": cvss_score,
                "references": references,
                "metadata": {
                    "scanner": "API Security Scanner v2.1",
                    "scan_id": str(uuid4()),
                    "confidence": random.choice(["high", "medium", "low"]),
                },
                "created_at": detected_at.isoformat(),
                "updated_at": (
                    remediated_at.isoformat()
                    if remediated_at
                    else detected_at.isoformat()
                ),
            }

            # Store in OpenSearch
            try:
                self.os_client.client.index(
                    index="security-findings",
                    id=vulnerability_id,
                    body=vulnerability,
                )
                # Refresh index to make data immediately available
                self.os_client.client.indices.refresh(index="security-findings")
                self.vulnerability_ids.append(vulnerability_id)

                if (i + 1) % 10 == 0:
                    logger.info(f"Generated {i + 1}/{count} vulnerabilities...")

            except Exception as e:
                logger.error(f"Failed to store vulnerability: {e}")

        logger.info(f"Successfully generated {len(self.vulnerability_ids)} vulnerabilities")

    def _weighted_choice(self, choices):
        """Make a weighted random choice.

        Args:
            choices: List of (value, weight) tuples

        Returns:
            Selected value
        """
        values, weights = zip(*choices)
        return random.choices(values, weights=weights)[0]

    def _generate_cvss_score(self, severity: VulnerabilitySeverity) -> float:
        """Generate CVSS score based on severity.

        Args:
            severity: Vulnerability severity

        Returns:
            CVSS score (0.0-10.0)
        """
        if severity == VulnerabilitySeverity.CRITICAL:
            return round(random.uniform(9.0, 10.0), 1)
        elif severity == VulnerabilitySeverity.HIGH:
            return round(random.uniform(7.0, 8.9), 1)
        elif severity == VulnerabilitySeverity.MEDIUM:
            return round(random.uniform(4.0, 6.9), 1)
        else:  # LOW
            return round(random.uniform(0.1, 3.9), 1)

    def _generate_remediation_actions(
        self,
        vuln_type: VulnerabilityType,
        status: VulnerabilityStatus,
        detected_at: datetime,
    ) -> list:
        """Generate remediation actions based on vulnerability type.

        Args:
            vuln_type: Type of vulnerability
            status: Current status
            detected_at: When vulnerability was detected

        Returns:
            List of remediation actions
        """
        actions = []

        # Action templates by vulnerability type
        action_templates = {
            VulnerabilityType.AUTHENTICATION: [
                {
                    "action": "Apply OAuth2 authentication policy at gateway",
                    "type": "configuration",
                },
                {
                    "action": "Enable JWT token signature validation",
                    "type": "configuration",
                },
                {
                    "action": "Enforce API key validation middleware",
                    "type": "code_change",
                },
            ],
            VulnerabilityType.AUTHORIZATION: [
                {
                    "action": "Implement RBAC authorization policy",
                    "type": "configuration",
                },
                {
                    "action": "Add object-level permission checks",
                    "type": "code_change",
                },
                {
                    "action": "Deploy authorization middleware",
                    "type": "deployment",
                },
            ],
            VulnerabilityType.INJECTION: [
                {
                    "action": "Implement input validation and sanitization",
                    "type": "code_change",
                },
                {
                    "action": "Use parameterized queries",
                    "type": "code_change",
                },
                {
                    "action": "Deploy WAF rules for injection prevention",
                    "type": "configuration",
                },
            ],
            VulnerabilityType.EXPOSURE: [
                {
                    "action": "Remove sensitive data from logs",
                    "type": "code_change",
                },
                {
                    "action": "Implement response filtering",
                    "type": "code_change",
                },
                {
                    "action": "Enable field-level encryption",
                    "type": "configuration",
                },
            ],
            VulnerabilityType.CONFIGURATION: [
                {
                    "action": "Apply rate limiting policy (100 req/min)",
                    "type": "configuration",
                },
                {
                    "action": "Update CORS policy to whitelist origins",
                    "type": "configuration",
                },
                {
                    "action": "Enforce TLS 1.3 minimum version",
                    "type": "configuration",
                },
            ],
            VulnerabilityType.DEPENDENCY: [
                {
                    "action": "Update vulnerable dependency to latest version",
                    "type": "upgrade",
                },
                {
                    "action": "Apply security patches",
                    "type": "upgrade",
                },
                {
                    "action": "Replace end-of-life component",
                    "type": "upgrade",
                },
            ],
        }

        # Get templates for this vulnerability type
        templates = action_templates.get(
            vuln_type,
            [{"action": "Manual remediation required", "type": "manual"}],
        )

        # Generate 1-3 actions
        num_actions = random.randint(1, min(3, len(templates)))
        selected_templates = random.sample(templates, num_actions)

        for idx, template in enumerate(selected_templates):
            # Calculate action timing
            action_delay_days = random.randint(1, 15)
            performed_at = detected_at + timedelta(days=action_delay_days)

            # Determine action status
            if status == VulnerabilityStatus.REMEDIATED:
                action_status = "completed"
            elif status == VulnerabilityStatus.IN_PROGRESS:
                if idx == 0:
                    action_status = "completed"
                else:
                    action_status = random.choice(["in_progress", "pending"])
            else:
                action_status = "pending"

            action = {
                "action": template["action"],
                "type": template["type"],
                "status": action_status,
                "performed_at": (
                    performed_at.isoformat()
                    if action_status == "completed"
                    else None
                ),
                "performed_by": random.choice(
                    [
                        "security_agent",
                        "security_team",
                        "devops_team",
                        "automated_system",
                    ]
                ),
            }
            actions.append(action)

        return actions

    def generate_summary_report(self):
        """Generate and display summary report of created vulnerabilities."""
        try:
            # Query for statistics
            response = self.os_client.client.search(
                index="security-findings",
                body={
                    "size": 0,
                    "aggs": {
                        "by_severity": {"terms": {"field": "severity"}},
                        "by_status": {"terms": {"field": "status"}},
                        "by_type": {"terms": {"field": "vulnerability_type"}},
                    },
                },
            )

            aggs = response["aggregations"]
            total = response["hits"]["total"]["value"]

            logger.info("\n" + "=" * 80)
            logger.info("SECURITY MOCK DATA SUMMARY")
            logger.info("=" * 80)
            logger.info(f"Total Vulnerabilities: {total}")
            logger.info("")
            logger.info("By Severity:")
            for bucket in aggs["by_severity"]["buckets"]:
                logger.info(f"  {bucket['key'].upper()}: {bucket['doc_count']}")
            logger.info("")
            logger.info("By Status:")
            for bucket in aggs["by_status"]["buckets"]:
                logger.info(f"  {bucket['key'].upper()}: {bucket['doc_count']}")
            logger.info("")
            logger.info("By Type:")
            for bucket in aggs["by_type"]["buckets"]:
                logger.info(f"  {bucket['key'].upper()}: {bucket['doc_count']}")
            logger.info("=" * 80)

        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Generate mock security vulnerability data"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=50,
        help="Number of vulnerabilities to generate (default: 50)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Display summary report after generation",
    )

    args = parser.parse_args()

    generator = SecurityMockDataGenerator()
    generator.generate_all(num_vulnerabilities=args.count)

    if args.summary:
        generator.generate_summary_report()


if __name__ == "__main__":
    main()

# Made with Bob