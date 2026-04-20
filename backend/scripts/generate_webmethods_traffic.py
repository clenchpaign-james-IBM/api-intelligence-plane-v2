#!/usr/bin/env python3
"""
Traffic generator for webMethods Gateway API endpoints.

This script generates simulated API traffic to a specific webMethods gateway endpoint
to populate metrics data that will trigger predictions in the API Intelligence Plane.

Usage:
    python backend/scripts/generate_webmethods_traffic.py \
        --url "http://localhost:5555/gateway/Swagger%20Petstore%20-%20OpenAPI%203.0/1.0.27/pet/1" \
        --username admin \
        --password manage \
        --duration 300 \
        --rate 20 \
        --pattern degrading

Patterns:
    - normal: Steady traffic with good performance
    - degrading: Gradually increasing response times and errors
    - spike: Periodic traffic spikes
    - high-error: High error rate to trigger failure predictions
"""

import argparse
import asyncio
import random
import time
import base64
from datetime import datetime
from typing import Dict, Any, Optional
import httpx
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class WebMethodsTrafficGenerator:
    """Generate traffic for webMethods Gateway API endpoints."""
    
    def __init__(
        self,
        url: str,
        username: str,
        password: str,
        rate: int = 10,
        duration: int = 60,
    ):
        """
        Initialize traffic generator.
        
        Args:
            url: Full API endpoint URL
            username: Basic auth username
            password: Basic auth password
            rate: Requests per second
            duration: Duration in seconds
        """
        self.url = url
        self.username = username
        self.password = password
        self.rate = rate
        self.duration = duration
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'status_codes': {},
            'response_times': [],
        }
    
    def _get_auth_header(self) -> str:
        """Generate Basic Auth header."""
        credentials = f"{self.username}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return f"Basic {encoded}"
    
    async def make_request(
        self,
        client: httpx.AsyncClient,
        method: str = 'GET',
        add_delay: float = 0.0,
    ) -> Dict[str, Any]:
        """
        Make a single API request.
        
        Args:
            client: HTTP client
            method: HTTP method
            add_delay: Additional delay to simulate slow responses
            
        Returns:
            Request result with timing and status
        """
        headers = {
            'Authorization': self._get_auth_header(),
            'Content-Type': 'application/json',
        }
        
        start_time = time.time()
        
        try:
            # Add artificial delay if specified (for degrading pattern)
            if add_delay > 0:
                await asyncio.sleep(add_delay)
            
            if method == 'GET':
                response = await client.get(self.url, headers=headers, timeout=30.0)
            elif method == 'POST':
                response = await client.post(
                    self.url,
                    headers=headers,
                    json={
                        'id': random.randint(1, 1000),
                        'name': f'test-pet-{random.randint(1, 100)}',
                        'status': random.choice(['available', 'pending', 'sold']),
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    timeout=30.0
                )
            elif method == 'PUT':
                response = await client.put(
                    self.url,
                    headers=headers,
                    json={
                        'id': 1,
                        'name': f'updated-pet-{random.randint(1, 100)}',
                        'status': random.choice(['available', 'pending', 'sold']),
                        'timestamp': datetime.utcnow().isoformat()
                    },
                    timeout=30.0
                )
            elif method == 'DELETE':
                response = await client.delete(self.url, headers=headers, timeout=30.0)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            return {
                'success': response.status_code < 400,
                'status_code': response.status_code,
                'response_time': response_time,
                'method': method,
            }
        
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            logger.error(f"Request failed: {method} {self.url} - {str(e)}")
            
            return {
                'success': False,
                'status_code': 0,
                'response_time': response_time,
                'method': method,
                'error': str(e),
            }
    
    def update_stats(self, result: Dict[str, Any]):
        """Update statistics with request result."""
        self.stats['total_requests'] += 1
        
        if result['success']:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
        
        response_time = result['response_time']
        self.stats['total_response_time'] += response_time
        self.stats['min_response_time'] = min(self.stats['min_response_time'], response_time)
        self.stats['max_response_time'] = max(self.stats['max_response_time'], response_time)
        self.stats['response_times'].append(response_time)
        
        status_code = result['status_code']
        self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1
    
    async def generate_normal_traffic(self):
        """Generate normal traffic pattern with good performance."""
        logger.info(f"Starting NORMAL traffic: {self.rate} req/s for {self.duration}s")
        logger.info(f"Target: {self.url}")
        
        async with httpx.AsyncClient(verify=False) as client:
            start_time = time.time()
            interval = 1.0 / self.rate
            
            while time.time() - start_time < self.duration:
                # Mostly GET requests with occasional POST/PUT
                method = random.choices(
                    ['GET', 'POST', 'PUT'],
                    weights=[80, 15, 5]
                )[0]
                
                result = await self.make_request(client, method)
                self.update_stats(result)
                
                await asyncio.sleep(interval)
                
                # Progress update every 30 seconds
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    logger.info(f"Progress: {int(elapsed)}s / {self.duration}s - "
                              f"{self.stats['total_requests']} requests sent")
        
        self.print_stats()
    
    async def generate_degrading_traffic(self):
        """Generate traffic with gradually degrading performance."""
        logger.info(f"Starting DEGRADING traffic: {self.rate} req/s for {self.duration}s")
        logger.info(f"Target: {self.url}")
        logger.info("Performance will gradually degrade to trigger predictions")
        
        async with httpx.AsyncClient(verify=False) as client:
            start_time = time.time()
            interval = 1.0 / self.rate
            
            while time.time() - start_time < self.duration:
                elapsed = time.time() - start_time
                progress = elapsed / self.duration
                
                # Gradually increase error rate (0% -> 15%)
                error_threshold = progress * 0.15
                
                # Gradually increase response time delay (0ms -> 500ms)
                artificial_delay = progress * 0.5
                
                # Decide if this request should fail
                should_fail = random.random() < error_threshold
                
                if should_fail:
                    # Simulate various failure scenarios
                    method = random.choice(['GET', 'POST', 'PUT'])
                    result = {
                        'success': False,
                        'status_code': random.choice([500, 503, 504]),
                        'response_time': random.uniform(2000, 5000),
                        'method': method,
                    }
                else:
                    method = random.choices(
                        ['GET', 'POST', 'PUT'],
                        weights=[80, 15, 5]
                    )[0]
                    result = await self.make_request(client, method, add_delay=artificial_delay)
                
                self.update_stats(result)
                await asyncio.sleep(interval)
                
                # Progress update
                if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    error_rate = (self.stats['failed_requests'] / self.stats['total_requests']) * 100
                    avg_rt = self.stats['total_response_time'] / self.stats['total_requests']
                    logger.info(f"Progress: {int(elapsed)}s / {self.duration}s - "
                              f"Error Rate: {error_rate:.1f}%, Avg RT: {avg_rt:.0f}ms")
        
        self.print_stats()
    
    async def generate_spike_traffic(self):
        """Generate traffic with periodic spikes."""
        logger.info(f"Starting SPIKE traffic: {self.duration}s with periodic spikes")
        logger.info(f"Target: {self.url}")
        
        async with httpx.AsyncClient(verify=False) as client:
            start_time = time.time()
            spike_rate = self.rate * 5
            
            while time.time() - start_time < self.duration:
                # Normal traffic for 20 seconds
                logger.info("Normal traffic period")
                normal_end = time.time() + 20
                while time.time() < normal_end and time.time() - start_time < self.duration:
                    method = random.choices(['GET', 'POST', 'PUT'], weights=[80, 15, 5])[0]
                    result = await self.make_request(client, method)
                    self.update_stats(result)
                    await asyncio.sleep(1.0 / self.rate)
                
                # Spike traffic for 10 seconds
                if time.time() - start_time < self.duration:
                    logger.info(f"Traffic spike! ({spike_rate} req/s)")
                    spike_end = time.time() + 10
                    while time.time() < spike_end and time.time() - start_time < self.duration:
                        # Generate burst of requests
                        tasks = []
                        for _ in range(spike_rate):
                            method = random.choices(['GET', 'POST', 'PUT'], weights=[80, 15, 5])[0]
                            tasks.append(self.make_request(client, method))
                        
                        results = await asyncio.gather(*tasks, return_exceptions=True)
                        for result in results:
                            if isinstance(result, dict):
                                self.update_stats(result)
                        
                        await asyncio.sleep(1.0)
        
        self.print_stats()
    
    async def generate_high_error_traffic(self):
        """Generate traffic with high error rate to trigger failure predictions."""
        logger.info(f"Starting HIGH-ERROR traffic: {self.rate} req/s for {self.duration}s")
        logger.info(f"Target: {self.url}")
        logger.info("High error rate (30%) to trigger failure predictions")
        
        async with httpx.AsyncClient(verify=False) as client:
            start_time = time.time()
            interval = 1.0 / self.rate
            error_rate = 0.30
            
            while time.time() - start_time < self.duration:
                should_fail = random.random() < error_rate
                
                if should_fail:
                    # Simulate failure
                    result = {
                        'success': False,
                        'status_code': random.choice([500, 503, 504, 429]),
                        'response_time': random.uniform(3000, 8000),
                        'method': 'GET',
                    }
                else:
                    method = random.choices(['GET', 'POST', 'PUT'], weights=[80, 15, 5])[0]
                    result = await self.make_request(client, method)
                
                self.update_stats(result)
                await asyncio.sleep(interval)
                
                # Progress update
                elapsed = time.time() - start_time
                if int(elapsed) % 30 == 0 and int(elapsed) > 0:
                    current_error_rate = (self.stats['failed_requests'] / self.stats['total_requests']) * 100
                    logger.info(f"Progress: {int(elapsed)}s / {self.duration}s - "
                              f"Error Rate: {current_error_rate:.1f}%")
        
        self.print_stats()
    
    def print_stats(self):
        """Print traffic generation statistics."""
        logger.info("\n" + "="*70)
        logger.info("Traffic Generation Statistics")
        logger.info("="*70)
        logger.info(f"Total Requests: {self.stats['total_requests']}")
        logger.info(f"Successful: {self.stats['successful_requests']}")
        logger.info(f"Failed: {self.stats['failed_requests']}")
        
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            error_rate = (self.stats['failed_requests'] / self.stats['total_requests']) * 100
            logger.info(f"Success Rate: {success_rate:.2f}%")
            logger.info(f"Error Rate: {error_rate:.2f}%")
            
            avg_response_time = self.stats['total_response_time'] / self.stats['total_requests']
            logger.info(f"\nResponse Times:")
            logger.info(f"  Average: {avg_response_time:.2f}ms")
            logger.info(f"  Min: {self.stats['min_response_time']:.2f}ms")
            logger.info(f"  Max: {self.stats['max_response_time']:.2f}ms")
            
            # Calculate percentiles
            if self.stats['response_times']:
                sorted_times = sorted(self.stats['response_times'])
                p50_idx = int(len(sorted_times) * 0.50)
                p95_idx = int(len(sorted_times) * 0.95)
                p99_idx = int(len(sorted_times) * 0.99)
                logger.info(f"  P50: {sorted_times[p50_idx]:.2f}ms")
                logger.info(f"  P95: {sorted_times[p95_idx]:.2f}ms")
                logger.info(f"  P99: {sorted_times[p99_idx]:.2f}ms")
        
        logger.info("\nStatus Code Distribution:")
        for code, count in sorted(self.stats['status_codes'].items()):
            percentage = (count / self.stats['total_requests']) * 100
            logger.info(f"  {code}: {count} ({percentage:.1f}%)")
        
        logger.info("="*70)
        logger.info("\nNext Steps:")
        logger.info("1. Wait 5-10 minutes for metrics to be aggregated")
        logger.info("2. Run prediction generation:")
        logger.info("   python backend/scripts/generate_mock_predictions.py")
        logger.info("3. Check predictions in the UI or via API:")
        logger.info("   curl http://localhost:8000/api/v1/predictions")
        logger.info("="*70 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Generate traffic for webMethods Gateway API endpoints',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Normal traffic for 5 minutes
  python backend/scripts/generate_webmethods_traffic.py \\
      --url "http://localhost:5555/gateway/Swagger%20Petstore%20-%20OpenAPI%203.0/1.0.27/pet/1" \\
      --username admin --password manage --duration 300 --rate 20

  # Degrading performance to trigger predictions
  python backend/scripts/generate_webmethods_traffic.py \\
      --url "http://localhost:5555/gateway/Swagger%20Petstore%20-%20OpenAPI%203.0/1.0.27/pet/1" \\
      --username admin --password manage --duration 300 --rate 20 --pattern degrading

  # High error rate
  python backend/scripts/generate_webmethods_traffic.py \\
      --url "http://localhost:5555/gateway/Swagger%20Petstore%20-%20OpenAPI%203.0/1.0.27/pet/1" \\
      --username admin --password manage --duration 180 --rate 15 --pattern high-error
        """
    )
    parser.add_argument(
        '--url',
        required=True,
        help='Full API endpoint URL (e.g., http://localhost:5555/gateway/API/version/path)'
    )
    parser.add_argument(
        '--username',
        required=True,
        help='Basic auth username'
    )
    parser.add_argument(
        '--password',
        required=True,
        help='Basic auth password'
    )
    parser.add_argument(
        '--rate',
        type=int,
        default=10,
        help='Requests per second (default: 10)'
    )
    parser.add_argument(
        '--duration',
        type=int,
        default=60,
        help='Duration in seconds (default: 60)'
    )
    parser.add_argument(
        '--pattern',
        choices=['normal', 'degrading', 'spike', 'high-error'],
        default='normal',
        help='Traffic pattern (default: normal)'
    )
    
    args = parser.parse_args()
    
    generator = WebMethodsTrafficGenerator(
        url=args.url,
        username=args.username,
        password=args.password,
        rate=args.rate,
        duration=args.duration
    )
    
    logger.info("="*70)
    logger.info("webMethods Gateway Traffic Generator")
    logger.info("="*70)
    logger.info(f"Configuration:")
    logger.info(f"  URL: {args.url}")
    logger.info(f"  Username: {args.username}")
    logger.info(f"  Rate: {args.rate} req/s")
    logger.info(f"  Duration: {args.duration}s")
    logger.info(f"  Pattern: {args.pattern}")
    logger.info(f"  Total Expected Requests: ~{args.rate * args.duration}")
    logger.info("="*70 + "\n")
    
    try:
        if args.pattern == 'normal':
            await generator.generate_normal_traffic()
        elif args.pattern == 'degrading':
            await generator.generate_degrading_traffic()
        elif args.pattern == 'spike':
            await generator.generate_spike_traffic()
        elif args.pattern == 'high-error':
            await generator.generate_high_error_traffic()
    
    except KeyboardInterrupt:
        logger.info("\nTraffic generation interrupted by user")
        generator.print_stats()
    except Exception as e:
        logger.error(f"Error during traffic generation: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    asyncio.run(main())

# Made with Bob
