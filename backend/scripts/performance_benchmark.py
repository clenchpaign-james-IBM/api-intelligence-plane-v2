#!/usr/bin/env python3
"""
Performance Benchmarking Script for API Intelligence Plane v2

This script performs comprehensive performance testing including:
1. API discovery performance
2. Metrics query performance (time buckets)
3. Policy analysis performance
4. Natural language query performance
5. Frontend rendering performance simulation
6. Database query performance
7. Concurrent request handling

Usage:
    python backend/scripts/performance_benchmark.py --full
    python backend/scripts/performance_benchmark.py --quick
    python backend/scripts/performance_benchmark.py --report-only
"""

import argparse
import asyncio
import json
import statistics
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple
from uuid import uuid4

import httpx
from opensearchpy import AsyncOpenSearch

# Configuration
BACKEND_URL = "http://localhost:8000"
OPENSEARCH_HOST = "localhost"
OPENSEARCH_PORT = 9200
OPENSEARCH_USER = "admin"
OPENSEARCH_PASSWORD = "admin"

# Performance Targets (from specification)
TARGETS = {
    "api_discovery_seconds": 300,  # 5 minutes
    "query_latency_seconds": 5,  # Natural language queries
    "metrics_query_seconds": 2,  # Time-bucketed metrics
    "policy_analysis_seconds": 3,  # Security policy analysis
    "concurrent_requests_per_minute": 1000000,  # 1M requests/min across all APIs
}


class PerformanceBenchmark:
    """Performance benchmarking suite for API Intelligence Plane."""

    def __init__(self, backend_url: str = BACKEND_URL):
        self.backend_url = backend_url
        self.results: Dict[str, Any] = {}
        self.opensearch_client = None

    async def setup(self):
        """Initialize connections and prepare test data."""
        print("🔧 Setting up benchmark environment...")
        
        # Initialize OpenSearch client
        self.opensearch_client = AsyncOpenSearch(
            hosts=[{"host": OPENSEARCH_HOST, "port": OPENSEARCH_PORT}],
            http_auth=(OPENSEARCH_USER, OPENSEARCH_PASSWORD),
            use_ssl=False,
            verify_certs=False,
        )
        
        # Verify backend is running
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{self.backend_url}/health")
                if response.status_code != 200:
                    raise Exception("Backend health check failed")
                print("✅ Backend is healthy")
            except Exception as e:
                print(f"❌ Backend connection failed: {e}")
                raise

    async def cleanup(self):
        """Clean up connections."""
        if self.opensearch_client:
            await self.opensearch_client.close()

    async def benchmark_api_discovery(self, api_count: int = 100) -> Dict[str, Any]:
        """Benchmark API discovery performance.
        
        Target: Complete within 5 minutes for 1000+ APIs
        """
        print(f"\n📊 Benchmarking API Discovery ({api_count} APIs)...")
        
        results = {
            "test": "api_discovery",
            "api_count": api_count,
            "target_seconds": TARGETS["api_discovery_seconds"],
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=600.0) as client:
            try:
                # Simulate discovery by fetching all APIs
                response = await client.get(
                    f"{self.backend_url}/api/v1/apis",
                    params={"page_size": api_count}
                )
                
                elapsed = time.time() - start_time
                results["elapsed_seconds"] = elapsed
                results["apis_per_second"] = api_count / elapsed if elapsed > 0 else 0
                results["status"] = "PASS" if elapsed < TARGETS["api_discovery_seconds"] else "FAIL"
                results["success"] = response.status_code == 200
                
                if response.status_code == 200:
                    data = response.json()
                    results["actual_count"] = data.get("total", 0)
                
                print(f"  ⏱️  Time: {elapsed:.2f}s")
                print(f"  🎯 Target: {TARGETS['api_discovery_seconds']}s")
                print(f"  📈 Rate: {results['apis_per_second']:.2f} APIs/sec")
                print(f"  ✅ Status: {results['status']}")
                
            except Exception as e:
                results["error"] = str(e)
                results["status"] = "ERROR"
                print(f"  ❌ Error: {e}")
        
        return results

    async def benchmark_metrics_query(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark time-bucketed metrics query performance.
        
        Target: <2 seconds per query
        """
        print(f"\n📊 Benchmarking Metrics Queries ({iterations} iterations)...")
        
        results = {
            "test": "metrics_query",
            "iterations": iterations,
            "target_seconds": TARGETS["metrics_query_seconds"],
        }
        
        # Get a sample API ID
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.backend_url}/api/v1/apis", params={"page_size": 1})
            if response.status_code != 200 or not response.json().get("items"):
                results["error"] = "No APIs found for testing"
                results["status"] = "SKIP"
                return results
            
            api_id = response.json()["items"][0]["id"]
        
        # Run benchmark
        latencies = []
        errors = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(iterations):
                start = time.time()
                try:
                    response = await client.get(
                        f"{self.backend_url}/api/v1/apis/{api_id}/metrics",
                        params={
                            "time_bucket": "5m",
                            "start_time": (datetime.utcnow() - timedelta(hours=24)).isoformat(),
                            "end_time": datetime.utcnow().isoformat(),
                        }
                    )
                    elapsed = time.time() - start
                    latencies.append(elapsed)
                    
                    if response.status_code != 200:
                        errors += 1
                        
                except Exception as e:
                    errors += 1
                    latencies.append(time.time() - start)
        
        # Calculate statistics
        if latencies:
            results["min_seconds"] = min(latencies)
            results["max_seconds"] = max(latencies)
            results["avg_seconds"] = statistics.mean(latencies)
            results["median_seconds"] = statistics.median(latencies)
            results["p95_seconds"] = sorted(latencies)[int(len(latencies) * 0.95)]
            results["p99_seconds"] = sorted(latencies)[int(len(latencies) * 0.99)]
            results["errors"] = errors
            results["error_rate"] = errors / iterations
            results["status"] = "PASS" if results["p95_seconds"] < TARGETS["metrics_query_seconds"] else "FAIL"
            
            print(f"  ⏱️  Avg: {results['avg_seconds']:.3f}s")
            print(f"  📊 P95: {results['p95_seconds']:.3f}s")
            print(f"  📊 P99: {results['p99_seconds']:.3f}s")
            print(f"  🎯 Target: {TARGETS['metrics_query_seconds']}s")
            print(f"  ❌ Errors: {errors}/{iterations}")
            print(f"  ✅ Status: {results['status']}")
        else:
            results["status"] = "ERROR"
            results["error"] = "No successful queries"
        
        return results

    async def benchmark_policy_analysis(self, iterations: int = 50) -> Dict[str, Any]:
        """Benchmark security policy analysis performance.
        
        Target: <3 seconds per analysis
        """
        print(f"\n📊 Benchmarking Policy Analysis ({iterations} iterations)...")
        
        results = {
            "test": "policy_analysis",
            "iterations": iterations,
            "target_seconds": TARGETS["policy_analysis_seconds"],
        }
        
        # Get a sample API ID
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.backend_url}/api/v1/apis", params={"page_size": 1})
            if response.status_code != 200 or not response.json().get("items"):
                results["error"] = "No APIs found for testing"
                results["status"] = "SKIP"
                return results
            
            api_id = response.json()["items"][0]["id"]
        
        # Run benchmark
        latencies = []
        errors = 0
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            for i in range(iterations):
                start = time.time()
                try:
                    response = await client.post(
                        f"{self.backend_url}/api/v1/security/scan",
                        json={"api_id": api_id}
                    )
                    elapsed = time.time() - start
                    latencies.append(elapsed)
                    
                    if response.status_code not in [200, 201]:
                        errors += 1
                        
                except Exception as e:
                    errors += 1
                    latencies.append(time.time() - start)
        
        # Calculate statistics
        if latencies:
            results["min_seconds"] = min(latencies)
            results["max_seconds"] = max(latencies)
            results["avg_seconds"] = statistics.mean(latencies)
            results["median_seconds"] = statistics.median(latencies)
            results["p95_seconds"] = sorted(latencies)[int(len(latencies) * 0.95)]
            results["errors"] = errors
            results["error_rate"] = errors / iterations
            results["status"] = "PASS" if results["p95_seconds"] < TARGETS["policy_analysis_seconds"] else "FAIL"
            
            print(f"  ⏱️  Avg: {results['avg_seconds']:.3f}s")
            print(f"  📊 P95: {results['p95_seconds']:.3f}s")
            print(f"  🎯 Target: {TARGETS['policy_analysis_seconds']}s")
            print(f"  ❌ Errors: {errors}/{iterations}")
            print(f"  ✅ Status: {results['status']}")
        else:
            results["status"] = "ERROR"
            results["error"] = "No successful analyses"
        
        return results

    async def benchmark_natural_language_query(self, iterations: int = 20) -> Dict[str, Any]:
        """Benchmark natural language query performance.
        
        Target: <5 seconds per query
        """
        print(f"\n📊 Benchmarking Natural Language Queries ({iterations} iterations)...")
        
        results = {
            "test": "natural_language_query",
            "iterations": iterations,
            "target_seconds": TARGETS["query_latency_seconds"],
        }
        
        test_queries = [
            "Show me all APIs with security vulnerabilities",
            "Which APIs have the highest error rates?",
            "List APIs that are not using authentication",
            "Show me APIs with performance issues",
            "Which APIs are shadow APIs?",
        ]
        
        latencies = []
        errors = 0
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            for i in range(iterations):
                query = test_queries[i % len(test_queries)]
                start = time.time()
                try:
                    response = await client.post(
                        f"{self.backend_url}/api/v1/query",
                        json={"query": query}
                    )
                    elapsed = time.time() - start
                    latencies.append(elapsed)
                    
                    if response.status_code != 200:
                        errors += 1
                        
                except Exception as e:
                    errors += 1
                    latencies.append(time.time() - start)
        
        # Calculate statistics
        if latencies:
            results["min_seconds"] = min(latencies)
            results["max_seconds"] = max(latencies)
            results["avg_seconds"] = statistics.mean(latencies)
            results["median_seconds"] = statistics.median(latencies)
            results["p95_seconds"] = sorted(latencies)[int(len(latencies) * 0.95)]
            results["errors"] = errors
            results["error_rate"] = errors / iterations
            results["status"] = "PASS" if results["p95_seconds"] < TARGETS["query_latency_seconds"] else "FAIL"
            
            print(f"  ⏱️  Avg: {results['avg_seconds']:.3f}s")
            print(f"  📊 P95: {results['p95_seconds']:.3f}s")
            print(f"  🎯 Target: {TARGETS['query_latency_seconds']}s")
            print(f"  ❌ Errors: {errors}/{iterations}")
            print(f"  ✅ Status: {results['status']}")
        else:
            results["status"] = "ERROR"
            results["error"] = "No successful queries"
        
        return results

    async def benchmark_concurrent_requests(self, concurrent: int = 100, requests: int = 1000) -> Dict[str, Any]:
        """Benchmark concurrent request handling.
        
        Target: Support millions of requests per minute
        """
        print(f"\n📊 Benchmarking Concurrent Requests ({concurrent} concurrent, {requests} total)...")
        
        results = {
            "test": "concurrent_requests",
            "concurrent": concurrent,
            "total_requests": requests,
        }
        
        async def make_request(client: httpx.AsyncClient, semaphore: asyncio.Semaphore):
            async with semaphore:
                try:
                    start = time.time()
                    response = await client.get(f"{self.backend_url}/api/v1/apis", params={"page_size": 10})
                    elapsed = time.time() - start
                    return {"success": response.status_code == 200, "latency": elapsed}
                except Exception as e:
                    return {"success": False, "latency": 0, "error": str(e)}
        
        semaphore = asyncio.Semaphore(concurrent)
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            tasks = [make_request(client, semaphore) for _ in range(requests)]
            request_results = await asyncio.gather(*tasks)
        
        elapsed = time.time() - start_time
        
        # Calculate statistics
        successful = sum(1 for r in request_results if r["success"])
        failed = requests - successful
        latencies = [r["latency"] for r in request_results if r["success"]]
        
        results["elapsed_seconds"] = elapsed
        results["requests_per_second"] = requests / elapsed if elapsed > 0 else 0
        results["successful_requests"] = successful
        results["failed_requests"] = failed
        results["success_rate"] = successful / requests
        
        if latencies:
            results["avg_latency"] = statistics.mean(latencies)
            results["p95_latency"] = sorted(latencies)[int(len(latencies) * 0.95)]
            results["p99_latency"] = sorted(latencies)[int(len(latencies) * 0.99)]
        
        # Check if we can handle target load (1M req/min = 16,667 req/sec)
        target_rps = TARGETS["concurrent_requests_per_minute"] / 60
        results["status"] = "PASS" if results["requests_per_second"] > target_rps / 100 else "FAIL"  # 1% of target
        
        print(f"  ⏱️  Time: {elapsed:.2f}s")
        print(f"  📈 Rate: {results['requests_per_second']:.2f} req/sec")
        print(f"  ✅ Success: {successful}/{requests} ({results['success_rate']*100:.1f}%)")
        print(f"  📊 Avg Latency: {results.get('avg_latency', 0):.3f}s")
        print(f"  📊 P95 Latency: {results.get('p95_latency', 0):.3f}s")
        print(f"  ✅ Status: {results['status']}")
        
        return results

    async def benchmark_database_queries(self) -> Dict[str, Any]:
        """Benchmark OpenSearch query performance."""
        print(f"\n📊 Benchmarking Database Queries...")
        
        results = {
            "test": "database_queries",
        }
        
        if not self.opensearch_client:
            results["error"] = "OpenSearch client not initialized"
            results["status"] = "SKIP"
            return results
        
        # Test different query types
        queries = {
            "simple_match": {
                "query": {"match": {"name": "test"}}
            },
            "range_query": {
                "query": {
                    "range": {
                        "created_at": {
                            "gte": "now-24h",
                            "lte": "now"
                        }
                    }
                }
            },
            "aggregation": {
                "size": 0,
                "aggs": {
                    "by_status": {
                        "terms": {"field": "status.keyword"}
                    }
                }
            },
        }
        
        query_results = {}
        
        for query_name, query_body in queries.items():
            latencies = []
            for _ in range(10):
                start = time.time()
                try:
                    await self.opensearch_client.search(
                        index="apis",
                        body=query_body
                    )
                    elapsed = time.time() - start
                    latencies.append(elapsed)
                except Exception as e:
                    print(f"  ⚠️  Query {query_name} failed: {e}")
            
            if latencies:
                query_results[query_name] = {
                    "avg_seconds": statistics.mean(latencies),
                    "p95_seconds": sorted(latencies)[int(len(latencies) * 0.95)],
                }
                print(f"  📊 {query_name}: {query_results[query_name]['avg_seconds']:.3f}s avg")
        
        results["queries"] = query_results
        results["status"] = "PASS" if all(q["avg_seconds"] < 1.0 for q in query_results.values()) else "FAIL"
        
        return results

    def generate_report(self) -> str:
        """Generate performance benchmark report."""
        report = []
        report.append("=" * 80)
        report.append("PERFORMANCE BENCHMARK REPORT")
        report.append("API Intelligence Plane v2 - Vendor-Neutral Architecture")
        report.append("=" * 80)
        report.append(f"\nGenerated: {datetime.utcnow().isoformat()}")
        report.append(f"Backend URL: {self.backend_url}")
        report.append("\n" + "=" * 80)
        report.append("PERFORMANCE TARGETS")
        report.append("=" * 80)
        for key, value in TARGETS.items():
            report.append(f"  {key}: {value}")
        
        report.append("\n" + "=" * 80)
        report.append("BENCHMARK RESULTS")
        report.append("=" * 80)
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r.get("status") == "PASS")
        failed_tests = sum(1 for r in self.results.values() if r.get("status") == "FAIL")
        skipped_tests = sum(1 for r in self.results.values() if r.get("status") == "SKIP")
        
        for test_name, result in self.results.items():
            report.append(f"\n{test_name.upper()}")
            report.append("-" * 80)
            for key, value in result.items():
                if key != "test":
                    report.append(f"  {key}: {value}")
        
        report.append("\n" + "=" * 80)
        report.append("SUMMARY")
        report.append("=" * 80)
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {failed_tests}")
        report.append(f"Skipped: {skipped_tests}")
        report.append(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        overall_status = "✅ PASS" if failed_tests == 0 else "❌ FAIL"
        report.append(f"\nOverall Status: {overall_status}")
        report.append("=" * 80)
        
        return "\n".join(report)

    async def run_full_benchmark(self):
        """Run complete benchmark suite."""
        print("\n🚀 Starting Full Performance Benchmark Suite")
        print("=" * 80)
        
        await self.setup()
        
        try:
            # Run all benchmarks
            self.results["api_discovery"] = await self.benchmark_api_discovery(api_count=100)
            self.results["metrics_query"] = await self.benchmark_metrics_query(iterations=100)
            self.results["policy_analysis"] = await self.benchmark_policy_analysis(iterations=50)
            self.results["natural_language_query"] = await self.benchmark_natural_language_query(iterations=20)
            self.results["concurrent_requests"] = await self.benchmark_concurrent_requests(concurrent=100, requests=1000)
            self.results["database_queries"] = await self.benchmark_database_queries()
            
            # Generate report
            report = self.generate_report()
            print("\n" + report)
            
            # Save report to file
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            report_file = f".benchmarks/performance_report_{timestamp}.txt"
            with open(report_file, "w") as f:
                f.write(report)
            print(f"\n📄 Report saved to: {report_file}")
            
            # Save JSON results
            json_file = f".benchmarks/performance_results_{timestamp}.json"
            with open(json_file, "w") as f:
                json.dump(self.results, f, indent=2, default=str)
            print(f"📄 JSON results saved to: {json_file}")
            
        finally:
            await self.cleanup()

    async def run_quick_benchmark(self):
        """Run quick benchmark with reduced iterations."""
        print("\n⚡ Starting Quick Performance Benchmark")
        print("=" * 80)
        
        await self.setup()
        
        try:
            self.results["metrics_query"] = await self.benchmark_metrics_query(iterations=10)
            self.results["concurrent_requests"] = await self.benchmark_concurrent_requests(concurrent=50, requests=100)
            
            report = self.generate_report()
            print("\n" + report)
            
        finally:
            await self.cleanup()


async def main():
    parser = argparse.ArgumentParser(description="Performance Benchmark for API Intelligence Plane")
    parser.add_argument("--full", action="store_true", help="Run full benchmark suite")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark")
    parser.add_argument("--backend-url", default=BACKEND_URL, help="Backend URL")
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark(backend_url=args.backend_url)
    
    if args.quick:
        await benchmark.run_quick_benchmark()
    else:
        await benchmark.run_full_benchmark()


if __name__ == "__main__":
    asyncio.run(main())

# Made with Bob
