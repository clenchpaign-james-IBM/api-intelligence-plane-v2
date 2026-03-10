#!/usr/bin/env python3
"""
Traffic generator script for testing API Intelligence Plane.

This script generates simulated API traffic to test:
- API discovery
- Metrics collection
- Shadow API detection
- Performance monitoring
- Anomaly detection

Usage:
    python backend/scripts/generate_traffic.py --gateway-url http://localhost:8081 --duration 60 --rate 10
"""

import argparse
import asyncio
import random
import time
from datetime import datetime
from typing import List, Dict, Any
import httpx
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TrafficGenerator:
    """Generate simulated API traffic for testing."""
    
    def __init__(
        self,
        gateway_url: str,
        rate: int = 10,
        duration: int = 60,
        api_endpoints: List[str] | None = None
    ):
        """
        Initialize traffic generator.
        
        Args:
            gateway_url: Base URL of the Gateway
            rate: Requests per second
            duration: Duration in seconds
            api_endpoints: List of API endpoints to hit
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.rate = rate
        self.duration = duration
        self.api_endpoints = api_endpoints or self._default_endpoints()
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_response_time': 0.0,
            'min_response_time': float('inf'),
            'max_response_time': 0.0,
            'status_codes': {},
        }
    
    def _default_endpoints(self) -> List[str]:
        """Get default API endpoints for testing."""
        return [
            '/api/v1/users',
            '/api/v1/users/123',
            '/api/v1/products',
            '/api/v1/products/456',
            '/api/v1/orders',
            '/api/v1/orders/789',
            '/api/v1/payments',
            '/api/v1/analytics',
            '/api/v1/reports',
            '/api/v1/settings',
        ]
    
    async def make_request(
        self,
        client: httpx.AsyncClient,
        endpoint: str,
        method: str = 'GET'
    ) -> Dict[str, Any]:
        """
        Make a single API request.
        
        Args:
            client: HTTP client
            endpoint: API endpoint
            method: HTTP method
            
        Returns:
            Request result with timing and status
        """
        url = f"{self.gateway_url}{endpoint}"
        start_time = time.time()
        
        try:
            if method == 'GET':
                response = await client.get(url, timeout=10.0)
            elif method == 'POST':
                response = await client.post(
                    url,
                    json={'test': True, 'timestamp': datetime.utcnow().isoformat()},
                    timeout=10.0
                )
            elif method == 'PUT':
                response = await client.put(
                    url,
                    json={'test': True, 'timestamp': datetime.utcnow().isoformat()},
                    timeout=10.0
                )
            elif method == 'DELETE':
                response = await client.delete(url, timeout=10.0)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # Convert to ms
            
            return {
                'success': True,
                'status_code': response.status_code,
                'response_time': response_time,
                'endpoint': endpoint,
                'method': method,
            }
        
        except Exception as e:
            end_time = time.time()
            response_time = (end_time - start_time) * 1000
            
            logger.error(f"Request failed: {method} {url} - {str(e)}")
            
            return {
                'success': False,
                'status_code': 0,
                'response_time': response_time,
                'endpoint': endpoint,
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
        
        status_code = result['status_code']
        self.stats['status_codes'][status_code] = self.stats['status_codes'].get(status_code, 0) + 1
    
    async def generate_traffic_burst(self, client: httpx.AsyncClient, count: int):
        """Generate a burst of traffic."""
        tasks = []
        
        for _ in range(count):
            # Randomly select endpoint and method
            endpoint = random.choice(self.api_endpoints)
            method = random.choices(
                ['GET', 'POST', 'PUT', 'DELETE'],
                weights=[70, 20, 5, 5]  # Weighted distribution
            )[0]
            
            tasks.append(self.make_request(client, endpoint, method))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, dict):
                self.update_stats(result)
            else:
                logger.error(f"Task failed with exception: {result}")
                self.stats['failed_requests'] += 1
    
    async def generate_normal_traffic(self):
        """Generate normal traffic pattern."""
        logger.info(f"Starting normal traffic generation: {self.rate} req/s for {self.duration}s")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            interval = 1.0 / self.rate  # Time between requests
            
            while time.time() - start_time < self.duration:
                await self.generate_traffic_burst(client, 1)
                await asyncio.sleep(interval)
        
        self.print_stats()
    
    async def generate_spike_traffic(self, spike_duration: int = 10):
        """Generate traffic with periodic spikes."""
        logger.info(f"Starting spike traffic generation: {self.duration}s with {spike_duration}s spikes")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            spike_rate = self.rate * 5  # 5x normal rate during spikes
            
            while time.time() - start_time < self.duration:
                # Normal traffic for 30 seconds
                logger.info("Normal traffic period")
                normal_end = time.time() + 30
                while time.time() < normal_end and time.time() - start_time < self.duration:
                    await self.generate_traffic_burst(client, 1)
                    await asyncio.sleep(1.0 / self.rate)
                
                # Spike traffic for spike_duration seconds
                if time.time() - start_time < self.duration:
                    logger.info(f"Traffic spike! ({spike_rate} req/s)")
                    spike_end = time.time() + spike_duration
                    while time.time() < spike_end and time.time() - start_time < self.duration:
                        await self.generate_traffic_burst(client, spike_rate)
                        await asyncio.sleep(1.0)
        
        self.print_stats()
    
    async def generate_shadow_api_traffic(self, shadow_endpoints: List[str] | None = None):
        """Generate traffic to undocumented (shadow) API endpoints."""
        shadow_endpoints = shadow_endpoints or [
            '/api/internal/debug',
            '/api/internal/metrics',
            '/api/v1/admin/users',
            '/api/v1/admin/config',
            '/api/legacy/v0/data',
        ]
        
        logger.info(f"Generating shadow API traffic to {len(shadow_endpoints)} endpoints")
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            while time.time() - start_time < self.duration:
                endpoint = random.choice(shadow_endpoints)
                result = await self.make_request(client, endpoint, 'GET')
                self.update_stats(result)
                await asyncio.sleep(1.0 / self.rate)
        
        self.print_stats()
    
    async def generate_error_traffic(self, error_rate: float = 0.3):
        """Generate traffic with intentional errors."""
        logger.info(f"Generating traffic with {error_rate*100}% error rate")
        
        error_endpoints = [
            '/api/v1/nonexistent',
            '/api/v1/users/invalid-id',
            '/api/v1/products/-1',
            '/api/v1/orders/abc',
        ]
        
        async with httpx.AsyncClient() as client:
            start_time = time.time()
            
            while time.time() - start_time < self.duration:
                # Randomly choose between normal and error endpoint
                if random.random() < error_rate:
                    endpoint = random.choice(error_endpoints)
                else:
                    endpoint = random.choice(self.api_endpoints)
                
                result = await self.make_request(client, endpoint, 'GET')
                self.update_stats(result)
                await asyncio.sleep(1.0 / self.rate)
        
        self.print_stats()
    
    def print_stats(self):
        """Print traffic generation statistics."""
        logger.info("\n" + "="*60)
        logger.info("Traffic Generation Statistics")
        logger.info("="*60)
        logger.info(f"Total Requests: {self.stats['total_requests']}")
        logger.info(f"Successful: {self.stats['successful_requests']}")
        logger.info(f"Failed: {self.stats['failed_requests']}")
        
        if self.stats['total_requests'] > 0:
            success_rate = (self.stats['successful_requests'] / self.stats['total_requests']) * 100
            logger.info(f"Success Rate: {success_rate:.2f}%")
            
            avg_response_time = self.stats['total_response_time'] / self.stats['total_requests']
            logger.info(f"Avg Response Time: {avg_response_time:.2f}ms")
            logger.info(f"Min Response Time: {self.stats['min_response_time']:.2f}ms")
            logger.info(f"Max Response Time: {self.stats['max_response_time']:.2f}ms")
        
        logger.info("\nStatus Code Distribution:")
        for code, count in sorted(self.stats['status_codes'].items()):
            logger.info(f"  {code}: {count}")
        
        logger.info("="*60 + "\n")


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='Generate API traffic for testing')
    parser.add_argument(
        '--gateway-url',
        default='http://localhost:8081',
        help='Gateway base URL (default: http://localhost:8081)'
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
        choices=['normal', 'spike', 'shadow', 'error'],
        default='normal',
        help='Traffic pattern (default: normal)'
    )
    parser.add_argument(
        '--error-rate',
        type=float,
        default=0.3,
        help='Error rate for error pattern (default: 0.3)'
    )
    
    args = parser.parse_args()
    
    generator = TrafficGenerator(
        gateway_url=args.gateway_url,
        rate=args.rate,
        duration=args.duration
    )
    
    logger.info(f"Traffic Generator Configuration:")
    logger.info(f"  Gateway URL: {args.gateway_url}")
    logger.info(f"  Rate: {args.rate} req/s")
    logger.info(f"  Duration: {args.duration}s")
    logger.info(f"  Pattern: {args.pattern}")
    
    try:
        if args.pattern == 'normal':
            await generator.generate_normal_traffic()
        elif args.pattern == 'spike':
            await generator.generate_spike_traffic()
        elif args.pattern == 'shadow':
            await generator.generate_shadow_api_traffic()
        elif args.pattern == 'error':
            await generator.generate_error_traffic(args.error_rate)
    
    except KeyboardInterrupt:
        logger.info("\nTraffic generation interrupted by user")
        generator.print_stats()
    except Exception as e:
        logger.error(f"Error during traffic generation: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())

# Made with Bob
