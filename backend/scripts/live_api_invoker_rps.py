#!/usr/bin/env python3
"""
Live API invoker with real requests-per-second scheduling.

Unlike `live_api_invoker.py`, this script can launch requests concurrently,
so `--rps` means approximately that many requests are started every second.

Prints one line per request:
METHOD URL -> STATUS_CODE REASON | LATENCYms | RESPONSE

Stops with Ctrl+C.
"""

import argparse
import json
import random
import signal
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import requests
from requests.auth import HTTPBasicAuth

RUNNING = True
PRINT_LOCK = threading.Lock()


def handle_interrupt(signum: int, frame: Any) -> None:
    """Stop the loop on Ctrl+C."""
    del signum, frame
    global RUNNING
    RUNNING = False
    with PRINT_LOCK:
        print("\nStopped.")


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = argparse.ArgumentParser(description="Live API invoker with real RPS scheduling")
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
            "bucketed-error-trend",
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
        help="Base delay between requests in seconds for non-rps mode",
    )
    parser.add_argument(
        "--rps",
        type=float,
        default=1.0,
        help="Requests started per second",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="Request timeout in seconds, default 10",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=50,
        help="Maximum concurrent worker threads, default 50",
    )
    parser.add_argument(
        "--expected-total-requests",
        type=int,
        default=100,
        help="Expected total requests used to shape gradual demo patterns",
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
    total_requests: int,
    method: str,
    base_payload: Any,
    base_interval: float,
) -> tuple[str | None, str, Any, float]:
    """Return url, method, payload and scheduling override based on pattern.
    
    Returns None for url when the request should be skipped (simulated error/downtime).
    """
    url = base_url
    current_method = method
    payload = base_payload
    interval_seconds = base_interval

    if pattern == "steady":
        interval_seconds = base_interval

    elif pattern == "increasing-error-trend":
        # Shape the error probability across the full planned run so the trend
        # increases gradually from mostly successful to more failure-prone.
        safe_total_requests = max(2, total_requests)
        progress = min(1.0, max(0.0, (request_number - 1) / (safe_total_requests - 1)))
        error_ratio = min(0.85, 0.05 + (progress * 0.75))

        should_error = random.random() < error_ratio
        if should_error:
            # Append invalid resource paths to generate 404 errors for this API
            error_suffixes = [
                "/nonexistent",
                "/invalid_id_999999",
                "/missing_resource",
                "/error_trigger",
            ]
            url = f"{base_url.rstrip('/')}{random.choice(error_suffixes)}?error=true&n={request_number}"
        interval_seconds = base_interval

    elif pattern == "bucketed-error-trend":
        # Increase the planned error ratio in discrete bands so each group of
        # requests can map to a later metrics bucket with a clearly higher
        # observed error rate than the previous one.
        safe_total_requests = max(1, total_requests)
        bucket_count = min(6, safe_total_requests)
        bucket_size = max(1, safe_total_requests // bucket_count)
        bucket_index = min(bucket_count - 1, (request_number - 1) // bucket_size)
        error_ratio = min(0.95, 0.05 + (bucket_index * 0.15))

        should_error = random.random() < error_ratio
        if should_error:
            error_suffixes = [
                "/nonexistent",
                "/invalid_id_999999",
                "/missing_resource",
                "/error_trigger",
            ]
            url = f"{base_url.rstrip('/')}{random.choice(error_suffixes)}?bucket_error=true&bucket={bucket_index + 1}&n={request_number}"
        interval_seconds = base_interval

    elif pattern == "decreasing-response-time":
        # Pattern relies on actual API response times
        # No client-side simulation needed
        interval_seconds = base_interval

    elif pattern == "decreasing-availability":
        # Generate actual error requests to simulate downtime/unavailability
        outage_window = max(2, request_number // 5)
        should_error = request_number % 10 < min(9, outage_window)
        if should_error:
            # Append paths that might trigger errors or use invalid IDs
            error_suffixes = [
                "/unavailable",
                "/timeout_trigger",
                "/slow_endpoint",
            ]
            url = f"{base_url.rstrip('/')}{random.choice(error_suffixes)}?unavailable=true&n={request_number}"
        interval_seconds = base_interval

    elif pattern == "burst":
        phase = request_number % 12
        if phase < 3:
            # During burst, send faster and include some errors
            interval_seconds = max(0.02, base_interval / 5)
            # 30% chance of error during burst
            if random.random() < 0.3:
                error_suffixes = [
                    "/overload",
                    "/burst_error",
                    "/capacity_exceeded",
                ]
                url = f"{base_url.rstrip('/')}{random.choice(error_suffixes)}?burst=true&n={request_number}"
        else:
            interval_seconds = base_interval

    elif pattern == "traffic-ramp-up":
        interval_seconds = max(0.02, base_interval / min(10, 1 + request_number // 5))

    elif pattern == "error-burst":
        # Generate actual error requests during burst window
        burst_window = request_number % 20
        if 8 <= burst_window <= 12:
            # Append error-inducing paths during burst window
            error_suffixes = [
                "/error_burst",
                "/failure",
                "/broken",
                "/timeout",
            ]
            url = f"{base_url.rstrip('/')}{random.choice(error_suffixes)}?error_burst=true&n={request_number}"
        interval_seconds = base_interval

    elif pattern == "increasing-response-time":
        # Pattern relies on actual API response times
        # No client-side simulation needed
        interval_seconds = base_interval

    elif pattern == "rate-limit-hit":
        # Send requests much faster to trigger real rate limits
        # Progressively increase speed to ensure rate limit is hit
        speed_multiplier = min(20, 3 + request_number // 10)
        interval_seconds = max(0.01, base_interval / speed_multiplier)

    elif pattern == "auth-failures":
        # Alternate between valid and invalid credentials
        # The fire_request function handles credential alternation
        # Just add a marker to help identify auth failure attempts
        interval_seconds = base_interval
        if request_number % 2 == 0:
            # Add auth failure marker to URL for tracking
            url = f"{base_url}{'&' if '?' in base_url else '?'}auth_test=invalid&n={request_number}"

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
        interval_seconds = base_interval

    if payload is None and current_method in {"POST", "PUT", "PATCH"}:
        payload = {"request_number": request_number, "pattern": pattern}

    return url, current_method, payload, interval_seconds


def shorten_response_text(text: str, max_length: int = 120) -> str:
    """Keep response output to one line and short."""
    one_line = " ".join(text.split())
    if len(one_line) <= max_length:
        return one_line
    return one_line[: max_length - 3] + "..."


def fire_request(
    request_number: int,
    url: str | None,
    method: str,
    payload: Any,
    auth: HTTPBasicAuth | None,
    timeout: float,
    pattern: str,
) -> None:
    """Execute one request and print result."""
    # Skip request if url is None (simulated error/downtime)
    if url is None:
        with PRINT_LOCK:
            print(f"SKIPPED request #{request_number} (simulated error/downtime)")
        return

    # Handle auth-failures pattern by alternating credentials
    request_auth = auth
    if pattern == "auth-failures":
        if request_number % 2 == 0:
            # Use invalid credentials
            request_auth = HTTPBasicAuth("invalid_user", "invalid_pass")
        # else use the original auth (which might be None or valid)

    start = time.perf_counter()
    try:
        response = requests.request(
            method=method,
            url=url,
            json=payload if method in {"POST", "PUT", "PATCH"} else None,
            auth=request_auth,
            timeout=timeout,
        )
        latency_ms = (time.perf_counter() - start) * 1000
        body = shorten_response_text(response.text)
        with PRINT_LOCK:
            print(
                f"{method} {url} -> "
                f"{response.status_code} {response.reason} | "
                f"{latency_ms:.0f} ms | {body}"
            )
    except requests.RequestException as exc:
        latency_ms = (time.perf_counter() - start) * 1000
        with PRINT_LOCK:
            print(f"{method} {url} -> ERROR {exc} | {latency_ms:.0f} ms |")


def main() -> int:
    """Run the request scheduler loop."""
    args = parse_args()
    method = args.method.upper()
    payload = parse_payload(args.payload)

    if args.rps <= 0:
        raise ValueError("--rps must be greater than 0")
    if args.max_workers <= 0:
        raise ValueError("--max-workers must be greater than 0")

    signal.signal(signal.SIGINT, handle_interrupt)

    auth = None
    if args.username is not None or args.password is not None:
        auth = HTTPBasicAuth(args.username or "", args.password or "")

    base_interval = 1.0 / args.rps
    request_number = 0
    next_run = time.perf_counter()

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        while RUNNING:
            request_number += 1
            url, current_method, current_payload, pattern_interval = build_pattern_request(
                args.pattern,
                args.url,
                request_number,
                args.expected_total_requests,
                method,
                payload,
                base_interval,
            )

            executor.submit(
                fire_request,
                request_number,
                url,
                current_method,
                current_payload,
                auth,
                args.timeout,
                args.pattern,
            )

            next_run += pattern_interval
            sleep_for = next_run - time.perf_counter()
            if sleep_for > 0:
                time.sleep(sleep_for)
            else:
                next_run = time.perf_counter()

    return 0


if __name__ == "__main__":
    sys.exit(main())

# Made with Bob
