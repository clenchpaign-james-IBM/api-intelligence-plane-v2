#!/usr/bin/env python3
"""
Mock WebMethods transactional log generator.

Generates vendor-neutral transactional log records for analytics development,
testing, and demo scenarios. This script creates fresh analytics data only.
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.models.base.transaction import (  # noqa: E402
    CacheStatus,
    ErrorOrigin,
    EventStatus,
    EventType,
    ExternalCall,
    ExternalCallType,
    TransactionalLog,
)


class MockWMLogGenerator:
    """Generate mock transactional logs for WebMethods analytics flows."""

    def __init__(self):
        self.repository = TransactionalLogRepository()
        self.api_catalog = [
            ("orders-api", "Orders API", "/orders"),
            ("inventory-api", "Inventory API", "/inventory"),
            ("payments-api", "Payments API", "/payments"),
            ("customers-api", "Customers API", "/customers"),
        ]
        self.applications = [
            ("portal-app", "Portal App"),
            ("mobile-app", "Mobile App"),
            ("partner-app", "Partner App"),
        ]

    def generate_logs(self, count: int = 100, gateway_id: str | None = None) -> list[TransactionalLog]:
        """Generate and persist a batch of transactional logs."""
        generated_logs = [
            self._create_transactional_log(index=index, gateway_id=gateway_id)
            for index in range(count)
        ]
        created_count = self.repository.bulk_create(generated_logs)
        print(f"Generated and stored {created_count} transactional logs")
        return generated_logs

    def _create_transactional_log(
        self,
        index: int,
        gateway_id: str | None = None,
    ) -> TransactionalLog:
        """Create a single transactional log with realistic timing and status."""
        api_id, api_name, base_path = random.choice(self.api_catalog)
        application_id, application_name = random.choice(self.applications)

        event_time = datetime.utcnow() - timedelta(minutes=random.randint(0, 180))
        timestamp_ms = int(event_time.timestamp() * 1000)

        status_code = random.choices(
            population=[200, 201, 202, 400, 401, 404, 429, 500, 502, 504],
            weights=[28, 8, 2, 6, 3, 4, 5, 5, 3, 2],
            k=1,
        )[0]

        is_success = status_code < 400
        total_time_ms = random.randint(40, 1200)
        gateway_time_ms = max(5, int(total_time_ms * random.uniform(0.1, 0.35)))
        backend_time_ms = max(10, total_time_ms - gateway_time_ms)

        cache_status = random.choices(
            population=[
                CacheStatus.HIT,
                CacheStatus.MISS,
                CacheStatus.BYPASS,
                CacheStatus.DISABLED,
            ],
            weights=[20, 55, 15, 10],
            k=1,
        )[0]

        if status_code >= 500:
            event_status = EventStatus.FAILURE
            error_origin = ErrorOrigin.BACKEND
            error_message = "Upstream service unavailable"
            error_code = "UPSTREAM_5XX"
        elif status_code in (429, 504):
            event_status = EventStatus.TIMEOUT if status_code == 504 else EventStatus.FAILURE
            error_origin = ErrorOrigin.GATEWAY
            error_message = "Gateway enforcement or timeout condition"
            error_code = "GATEWAY_LIMIT"
        elif status_code >= 400:
            event_status = EventStatus.FAILURE
            error_origin = ErrorOrigin.CLIENT
            error_message = "Client request validation failed"
            error_code = "CLIENT_4XX"
        else:
            event_status = EventStatus.SUCCESS
            error_origin = None
            error_message = None
            error_code = None

        request_path = f"{base_path}/{(index % 25) + 1}"
        correlation_id = f"corr-{uuid4()}"
        trace_id = f"trace-{uuid4()}"

        external_call = ExternalCall(
            call_type=ExternalCallType.BACKEND_SERVICE,
            url=f"http://backend.internal{request_path}",
            method="GET",
            start_time=timestamp_ms + gateway_time_ms,
            end_time=timestamp_ms + gateway_time_ms + backend_time_ms,
            duration_ms=backend_time_ms,
            status_code=status_code,
            success=is_success,
            request_size=random.randint(200, 800),
            response_size=random.randint(800, 5000),
            error_message=None if is_success else error_message,
        )

        return TransactionalLog(
            id=uuid4(),
            event_type=EventType.TRANSACTIONAL,
            timestamp=timestamp_ms,
            api_id=api_id,
            api_name=api_name,
            api_version="v1",
            operation=f"operation-{index % 6}",
            http_method=random.choice(["GET", "POST", "PUT"]),
            request_path=request_path,
            request_headers={
                "accept": "application/json",
                "x-correlation-id": correlation_id,
            },
            request_payload=None if index % 3 == 0 else '{"sample":"payload"}',
            request_size=random.randint(200, 900),
            query_parameters={"page": index % 10, "includeDetails": index % 2 == 0},
            status_code=status_code,
            response_headers={"content-type": "application/json"},
            response_payload='{"status":"ok"}' if is_success else '{"error":"request failed"}',
            response_size=random.randint(500, 6000),
            client_id=application_id,
            client_name=application_name,
            client_ip=f"10.0.{index % 10}.{(index % 200) + 1}",
            user_agent="wm-log-generator/1.0",
            total_time_ms=total_time_ms,
            gateway_time_ms=gateway_time_ms,
            backend_time_ms=backend_time_ms,
            status=event_status,
            correlation_id=correlation_id,
            session_id=f"session-{uuid4()}",
            trace_id=trace_id,
            cache_status=cache_status,
            backend_url=f"http://backend.internal{base_path}",
            backend_method="GET",
            backend_request_headers={"x-trace-id": trace_id},
            backend_response_headers={"content-type": "application/json"},
            error_origin=error_origin,
            error_message=error_message,
            error_code=error_code,
            external_calls=[external_call],
            gateway_id=gateway_id or str(uuid4()),
            gateway_node=f"wm-node-{(index % 3) + 1}",
            vendor_metadata={
                "vendor": "webmethods",
                "environment": "mock",
                "scenario": "analytics-seed",
            },
            created_at=event_time,
        )


def main() -> None:
    """CLI entry point."""
    count = 100
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
        except ValueError:
            print("Usage: python backend/scripts/generate_wm_logs.py [count]")
            sys.exit(1)

    generator = MockWMLogGenerator()
    generator.generate_logs(count=count)


if __name__ == "__main__":
    main()

# Made with Bob