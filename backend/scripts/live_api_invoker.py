#!/usr/bin/env python3
"""
Very simple live API invoker for demo traffic generation.

Prints one line per request:
METHOD URL -> STATUS_CODE REASON | LATENCYms | RESPONSE

Stops with Ctrl+C.

Examples:
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/health
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --method POST --payload '{"name":"demo"}'
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --username admin --password admin
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern increasing-error-trend
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern burst
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern traffic-ramp-up
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern error-burst
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern increasing-response-time
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern rate-limit-hit
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern auth-failures
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --pattern shadow-api-probe
    python backend/scripts/live_api_invoker.py --url http://localhost:8080/test --rps 5
"""

import argparse
import json
import random
import signal
import sys
import time
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

RUNNING = True


def handle_interrupt(signum: int, frame: Any) -> None:
    """Stop the loop on Ctrl+C."""
    del signum, frame
    global RUNNING
    RUNNING = False
    print("\nStopped.")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Simple live API invoker for demo traffic")
    parser.add_argument("--url", required=True, help="Target URL")
    parser.add_argument("--method", default="GET", help="HTTP method, default GET")
    parser.add_argument("--payload", help="JSON request payload for POST/PUT/PATCH")
    parser.add_argument("--username", help="Basic auth username")
    parser.add_argument("--password", help="Basic auth password")
    parser.add_argument(
        "--pattern",
        default="steady",
        choices=[
            "steady",
            "increasing-error-trend",
            "decreasing-response-time",
            "decreasing-availability",
            "burst",
            "traffic-ramp-up",
            "error-burst",
            "increasing-response-time",
            "rate-limit-hit",
            "auth-failures",
            "shadow-api-probe",
        ],
        help="Traffic pattern for demo behavior",
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        help="Base delay between requests in seconds, default 1.0",
    )
    parser.add_argument(
        "--rps",
        type=float,
        help="Requests per second. If provided, overrides --interval",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds, default 10",
    )
    return parser.parse_args()


def parse_payload(payload: str | None) -> Any:
    """Parse JSON payload if provided."""
    if not payload:
        return None
    return json.loads(payload)


def build_pattern_request(
    pattern: str,
    base_url: str,
    request_number: int,
    method: str,
    base_payload: Any,
    base_interval: float,
) -> tuple[str | None, str, Any, float]:
    """Return url, method, payload and sleep override based on pattern.
    
    Returns None for url when the request should be skipped (simulated error/downtime).
    """
    url = base_url
    current_method = method
    payload = base_payload
    sleep_seconds = base_interval

    if pattern == "steady":
        sleep_seconds = base_interval

    elif pattern == "increasing-error-trend":
        # Client-side simulation: skip requests to simulate errors
        error_ratio = min(0.8, request_number / 20.0)
        should_skip = random.random() < error_ratio
        if should_skip:
            # Return None to signal skipping this request
            return None, method, base_payload, base_interval
        sleep_seconds = base_interval

    elif pattern == "decreasing-response-time":
        # Pattern relies on actual API response times
        # No client-side simulation needed
        sleep_seconds = base_interval

    elif pattern == "decreasing-availability":
        # Client-side simulation: skip requests to simulate downtime
        outage_window = max(2, request_number // 5)
        should_skip = request_number % 10 < min(9, outage_window)
        if should_skip:
            # Return None to signal skipping this request
            return None, method, base_payload, base_interval
        sleep_seconds = base_interval

    elif pattern == "burst":
        phase = request_number % 12
        if phase < 3:
            sleep_seconds = max(0.1, base_interval / 5)
        else:
            sleep_seconds = base_interval

    elif pattern == "traffic-ramp-up":
        sleep_seconds = max(0.1, base_interval / min(10, 1 + request_number // 5))

    elif pattern == "error-burst":
        # Client-side simulation: skip requests during burst window
        burst_window = request_number % 20
        if 8 <= burst_window <= 12:
            # Return None to signal skipping this request
            return None, method, base_payload, base_interval
        sleep_seconds = base_interval

    elif pattern == "increasing-response-time":
        # Pattern relies on actual API response times
        # No client-side simulation needed
        sleep_seconds = base_interval

    elif pattern == "rate-limit-hit":
        # Send requests faster to trigger real rate limits
        sleep_seconds = max(0.1, base_interval / 3)

    elif pattern == "auth-failures":
        # Alternate between valid and invalid credentials
        # This requires auth to be configured; if not, just send normal requests
        sleep_seconds = base_interval

    elif pattern == "shadow-api-probe":
        shadow_paths = [
            "/api/internal/debug",
            "/api/internal/metrics",
            "/api/v1/admin/users",
            "/api/v1/admin/config",
            "/api/legacy/v0/data",
        ]
        if base_url.startswith("http://") or base_url.startswith("https://"):
            base_root = base_url.split("/", 3)
            if len(base_root) >= 3:
                url = f"{base_root[0]}//{base_root[2]}{random.choice(shadow_paths)}?n={request_number}"
        sleep_seconds = base_interval

    if payload is None and current_method in {"POST", "PUT", "PATCH"}:
        payload = {"request_number": request_number, "pattern": pattern}

    return url, current_method, payload, sleep_seconds


def shorten_response_text(text: str, max_length: int = 120) -> str:
    """Keep response output to one line and short."""
    one_line = " ".join(text.split())
    if len(one_line) <= max_length:
        return one_line
    return one_line[: max_length - 3] + "..."


def main() -> int:
    """Run the request loop."""
    args = parse_args()
    method = args.method.upper()
    payload = parse_payload(args.payload)
    base_interval = args.interval

    if args.rps is not None:
        if args.rps <= 0:
            raise ValueError("--rps must be greater than 0")
        base_interval = 1.0 / args.rps

    signal.signal(signal.SIGINT, handle_interrupt)

    auth = None
    if args.username is not None or args.password is not None:
        auth = HTTPBasicAuth(args.username or "", args.password or "")

    session = requests.Session()
    request_number = 0

    while RUNNING:
        request_number += 1
        url, current_method, current_payload, pattern_sleep = build_pattern_request(
            args.pattern,
            args.url,
            request_number,
            method,
            payload,
            base_interval,
        )

        # Skip request if pattern returns None (simulated error/downtime)
        if url is None:
            print(f"SKIPPED request #{request_number} (simulated error/downtime)")
            time.sleep(max(0.0, pattern_sleep))
            continue

        # Handle auth-failures pattern by alternating credentials
        request_auth = auth
        if args.pattern == "auth-failures":
            if request_number % 2 == 0:
                # Use invalid credentials
                request_auth = HTTPBasicAuth("invalid_user", "invalid_pass")
            # else use the original auth (which might be None or valid)

        start = time.perf_counter()
        try:
            response = session.request(
                method=current_method,
                url=url,
                json=current_payload if current_method in {"POST", "PUT", "PATCH"} else None,
                auth=request_auth,
                timeout=args.timeout,
            )
            latency_ms = (time.perf_counter() - start) * 1000
            body = shorten_response_text(response.text)
            print(
                f"{current_method} {url} -> "
                f"{response.status_code} {response.reason} | "
                f"{latency_ms:.0f} ms | {body}"
            )
        except requests.RequestException as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            print(f"{current_method} {url} -> ERROR {exc} | {latency_ms:.0f} ms |")

        time.sleep(max(0.0, pattern_sleep))

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
