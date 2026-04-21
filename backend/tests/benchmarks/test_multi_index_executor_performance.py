"""
Performance Benchmarks for Multi-Index Executor

Measures execution time, throughput, and resource usage for different
query execution strategies and scenarios.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import List
from uuid import uuid4

import pytest

from app.db.repositories.api_repository import APIRepository
from app.db.repositories.compliance_repository import ComplianceRepository
from app.db.repositories.gateway_repository import GatewayRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.db.repositories.transactional_log_repository import TransactionalLogRepository
from app.db.repositories.vulnerability_repository import VulnerabilityRepository
from app.models.query import (
    ExecutionStrategy,
    IndexQuery,
    InterpretedIntent,
    QueryPlan,
)
from app.services.query import ContextManager, MultiIndexExecutor


@pytest.fixture
def multi_index_executor():
    """Create a multi-index executor for benchmarking."""
    return MultiIndexExecutor(
        api_repository=APIRepository(),
        gateway_repository=GatewayRepository(),
        metrics_repository=MetricsRepository(),
        prediction_repository=PredictionRepository(),
        recommendation_repository=RecommendationRepository(),
        compliance_repository=ComplianceRepository(),
        vulnerability_repository=VulnerabilityRepository(),
        transactional_log_repository=TransactionalLogRepository(),
        context_manager=ContextManager(),
    )


class TestSingleIndexPerformance:
    """Benchmark single-index query performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_single_index_query_latency(
        self,
        multi_index_executor,
        benchmark
    ):
        """Benchmark single-index query latency."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={},
            time_range=None
        )
        
        index_query = IndexQuery(
            index="api-inventory",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id", "name"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show all APIs",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SINGLE_INDEX,
            index_queries=[index_query],
            estimated_cost=0.2,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        async def execute():
            return await multi_index_executor.execute_plan(plan)
        
        # Benchmark execution
        result = benchmark(lambda: asyncio.run(execute()))
        
        # Verify performance target: < 5 seconds
        assert result.execution_time < 5000
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_single_index_throughput(self, multi_index_executor):
        """Benchmark single-index query throughput."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api"],
            filters={},
            time_range=None
        )
        
        index_query = IndexQuery(
            index="api-inventory",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show all APIs",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SINGLE_INDEX,
            index_queries=[index_query],
            estimated_cost=0.2,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        # Execute multiple queries
        num_queries = 10
        start_time = time.time()
        
        tasks = [
            multi_index_executor.execute_plan(plan)
            for _ in range(num_queries)
        ]
        results = await asyncio.gather(*tasks)
        
        elapsed_time = time.time() - start_time
        throughput = num_queries / elapsed_time
        
        print(f"\nThroughput: {throughput:.2f} queries/second")
        print(f"Average latency: {(elapsed_time / num_queries) * 1000:.2f}ms")
        
        # Verify all queries succeeded
        assert all(r.count >= 0 for r in results)
        assert throughput > 1.0  # At least 1 query per second


class TestSequentialExecutionPerformance:
    """Benchmark sequential multi-index query performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_sequential_two_index_latency(self, multi_index_executor):
        """Benchmark sequential execution with two indices."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "vulnerability"],
            filters={},
            time_range=None
        )
        
        api_query = IndexQuery(
            index="api-inventory",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id", "name"],
            join_fields={"id": "api_id"},
            depends_on=[]
        )
        
        vuln_query = IndexQuery(
            index="security-findings",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id", "api_id", "severity"],
            join_fields={},
            depends_on=["api-inventory"]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show vulnerabilities for all APIs",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SEQUENTIAL,
            index_queries=[api_query, vuln_query],
            estimated_cost=0.5,
            requires_join=True,
            join_strategy="api_id",
            context_filters={}
        )
        
        start_time = time.time()
        result = await multi_index_executor.execute_plan(plan)
        elapsed_time = (time.time() - start_time) * 1000
        
        print(f"\nSequential execution time: {elapsed_time:.2f}ms")
        print(f"Results count: {result.count}")
        
        # Verify performance target: < 5 seconds
        assert elapsed_time < 5000
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_sequential_with_context_filters(self, multi_index_executor):
        """Benchmark sequential execution with context filters."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["vulnerability"],
            filters={"severity": "critical"},
            time_range=None
        )
        
        # Simulate context from previous query
        context_filters = {
            "api_id": [f"API-{i:03d}" for i in range(1, 51)]  # 50 API IDs
        }
        
        vuln_query = IndexQuery(
            index="security-findings",
            query_dsl={
                "query": {"term": {"severity": "critical"}}
            },
            filters={"severity": "critical"},
            required_fields=["id", "api_id", "severity"],
            join_fields={},
            depends_on=[]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show critical vulnerabilities for these APIs",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SEQUENTIAL,
            index_queries=[vuln_query],
            estimated_cost=0.3,
            requires_join=False,
            join_strategy=None,
            context_filters=context_filters
        )
        
        start_time = time.time()
        result = await multi_index_executor.execute_plan(plan)
        elapsed_time = (time.time() - start_time) * 1000
        
        print(f"\nContext-filtered execution time: {elapsed_time:.2f}ms")
        print(f"Context filters applied: {len(context_filters)}")
        
        # Context filtering should still be fast
        assert elapsed_time < 5000


class TestParallelExecutionPerformance:
    """Benchmark parallel multi-index query performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_parallel_vs_sequential_speedup(self, multi_index_executor):
        """Compare parallel vs sequential execution performance."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["api", "gateway", "vulnerability"],
            filters={},
            time_range=None
        )
        
        # Create three independent queries
        queries = [
            IndexQuery(
                index="api-inventory",
                query_dsl={"query": {"match_all": {}}},
                filters={},
                required_fields=["id"],
                join_fields={},
                depends_on=[]
            ),
            IndexQuery(
                index="gateway-registry",
                query_dsl={"query": {"match_all": {}}},
                filters={},
                required_fields=["id"],
                join_fields={},
                depends_on=[]
            ),
            IndexQuery(
                index="security-findings",
                query_dsl={"query": {"match_all": {}}},
                filters={},
                required_fields=["id"],
                join_fields={},
                depends_on=[]
            ),
        ]
        
        # Test parallel execution
        parallel_plan = QueryPlan(
            session_id=session_id,
            original_query="Show all data",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.PARALLEL,
            index_queries=queries,
            estimated_cost=0.6,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        start_time = time.time()
        parallel_result = await multi_index_executor.execute_plan(parallel_plan)
        parallel_time = (time.time() - start_time) * 1000
        
        # Test sequential execution
        sequential_plan = QueryPlan(
            session_id=session_id,
            original_query="Show all data",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.SEQUENTIAL,
            index_queries=queries,
            estimated_cost=0.6,
            requires_join=False,
            join_strategy=None,
            context_filters={}
        )
        
        start_time = time.time()
        sequential_result = await multi_index_executor.execute_plan(sequential_plan)
        sequential_time = (time.time() - start_time) * 1000
        
        speedup = sequential_time / parallel_time if parallel_time > 0 else 0
        
        print(f"\nParallel execution time: {parallel_time:.2f}ms")
        print(f"Sequential execution time: {sequential_time:.2f}ms")
        print(f"Speedup: {speedup:.2f}x")
        
        # Parallel should be faster or comparable
        assert parallel_time <= sequential_time * 1.2  # Allow 20% margin
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_parallel_scalability(self, multi_index_executor):
        """Test parallel execution scalability with increasing query count."""
        session_id = uuid4()
        
        for num_queries in [2, 4, 6, 8]:
            intent = InterpretedIntent(
                action="list",
                entities=["api"] * num_queries,
                filters={},
                time_range=None
            )
            
            # Create multiple queries
            queries = [
                IndexQuery(
                    index="api-inventory",
                    query_dsl={"query": {"match_all": {}}},
                    filters={},
                    required_fields=["id"],
                    join_fields={},
                    depends_on=[]
                )
                for _ in range(num_queries)
            ]
            
            plan = QueryPlan(
                session_id=session_id,
                original_query=f"Execute {num_queries} queries",
                interpreted_intent=intent,
                strategy=ExecutionStrategy.PARALLEL,
                index_queries=queries,
                estimated_cost=0.2 * num_queries,
                requires_join=False,
                join_strategy=None,
                context_filters={}
            )
            
            start_time = time.time()
            result = await multi_index_executor.execute_plan(plan)
            elapsed_time = (time.time() - start_time) * 1000
            
            print(f"\n{num_queries} parallel queries: {elapsed_time:.2f}ms")
            
            # Should scale reasonably
            assert elapsed_time < 10000  # Less than 10 seconds


class TestNestedExecutionPerformance:
    """Benchmark nested multi-index query performance."""
    
    @pytest.mark.benchmark
    @pytest.mark.asyncio
    async def test_nested_three_hop_latency(self, multi_index_executor):
        """Benchmark nested execution with three-hop relationship."""
        session_id = uuid4()
        intent = InterpretedIntent(
            action="list",
            entities=["gateway", "api", "vulnerability"],
            filters={},
            time_range=None
        )
        
        gateway_query = IndexQuery(
            index="gateway-registry",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id"],
            join_fields={"id": "gateway_id"},
            depends_on=[]
        )
        
        api_query = IndexQuery(
            index="api-inventory",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id", "gateway_id"],
            join_fields={"id": "api_id"},
            depends_on=["gateway-registry"]
        )
        
        vuln_query = IndexQuery(
            index="security-findings",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id", "api_id"],
            join_fields={},
            depends_on=["api-inventory"]
        )
        
        plan = QueryPlan(
            session_id=session_id,
            original_query="Show vulnerabilities for APIs in all gateways",
            interpreted_intent=intent,
            strategy=ExecutionStrategy.NESTED,
            index_queries=[gateway_query, api_query, vuln_query],
            estimated_cost=0.7,
            requires_join=True,
            join_strategy="gateway_id",
            context_filters={}
        )
        
        start_time = time.time()
        result = await multi_index_executor.execute_plan(plan)
        elapsed_time = (time.time() - start_time) * 1000
        
        print(f"\nNested 3-hop execution time: {elapsed_time:.2f}ms")
        print(f"Results count: {result.count}")
        
        # Nested queries should complete within target
        assert elapsed_time < 5000


class TestResultMergingPerformance:
    """Benchmark result merging performance."""
    
    @pytest.mark.benchmark
    def test_merge_large_result_set(self, multi_index_executor):
        """Benchmark merging large result sets."""
        # Create large result set with duplicates
        num_results = 10000
        results = [
            {"id": f"ID-{i % 1000}", "name": f"Item {i}"}
            for i in range(num_results)
        ]
        
        start_time = time.time()
        merged = multi_index_executor._merge_results(results, requires_join=False)
        elapsed_time = (time.time() - start_time) * 1000
        
        print(f"\nMerged {num_results} results in {elapsed_time:.2f}ms")
        print(f"Unique results: {len(merged)}")
        
        # Merging should be fast
        assert elapsed_time < 1000  # Less than 1 second
        assert len(merged) == 1000  # Should deduplicate to 1000 unique
    
    @pytest.mark.benchmark
    def test_extract_field_values_performance(self, multi_index_executor):
        """Benchmark field value extraction performance."""
        # Create large result set
        num_results = 10000
        results = [
            {"id": f"ID-{i}", "api_id": f"API-{i % 100}"}
            for i in range(num_results)
        ]
        
        start_time = time.time()
        api_ids = multi_index_executor._extract_field_values(results, "api_id")
        elapsed_time = (time.time() - start_time) * 1000
        
        print(f"\nExtracted field values from {num_results} results in {elapsed_time:.2f}ms")
        print(f"Unique values: {len(api_ids)}")
        
        # Extraction should be fast
        assert elapsed_time < 500  # Less than 500ms
        assert len(api_ids) == 100  # Should extract 100 unique API IDs


class TestContextFilteringPerformance:
    """Benchmark context filtering performance."""
    
    @pytest.mark.benchmark
    def test_apply_many_context_filters(self, multi_index_executor):
        """Benchmark applying many context filters."""
        index_query = IndexQuery(
            index="security-findings",
            query_dsl={"query": {"match_all": {}}},
            filters={},
            required_fields=["id"],
            join_fields={},
            depends_on=[]
        )
        
        # Create many context filters
        context_filters = {
            f"field_{i}": [f"value_{j}" for j in range(10)]
            for i in range(10)
        }
        
        start_time = time.time()
        filtered_query = multi_index_executor._apply_context_filters(
            index_query,
            context_filters
        )
        elapsed_time = (time.time() - start_time) * 1000
        
        print(f"\nApplied {len(context_filters)} context filters in {elapsed_time:.2f}ms")
        
        # Filter application should be fast
        assert elapsed_time < 100  # Less than 100ms


# Performance Summary Report
@pytest.mark.benchmark
def test_performance_summary():
    """Print performance summary and targets."""
    print("\n" + "=" * 60)
    print("MULTI-INDEX EXECUTOR PERFORMANCE TARGETS")
    print("=" * 60)
    print("\nQuery Latency Targets:")
    print("  - Single-index query: < 5 seconds")
    print("  - Sequential 2-index: < 5 seconds")
    print("  - Parallel 3-index: < 5 seconds")
    print("  - Nested 3-hop: < 5 seconds")
    print("\nThroughput Targets:")
    print("  - Single-index: > 1 query/second")
    print("\nScalability:")
    print("  - Parallel speedup: >= 1.0x")
    print("  - 8 parallel queries: < 10 seconds")
    print("\nResult Processing:")
    print("  - Merge 10K results: < 1 second")
    print("  - Extract fields: < 500ms")
    print("  - Apply filters: < 100ms")
    print("=" * 60)


# Made with Bob