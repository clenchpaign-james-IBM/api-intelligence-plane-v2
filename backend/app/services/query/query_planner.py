"""
Query Planner for Multi-Index Query Orchestration

Plans and optimizes execution of natural language queries that span multiple
OpenSearch indices with relationships. Implements index selection, relationship
resolution, and execution optimization.

Based on: docs/enterprise-nlq-multi-index-analysis.md Phase 3
Updated: 2026-04-21 - Integrated EntityRegistry for consistent mapping
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from app.models.query import (
    ExecutionStrategy,
    IndexQuery,
    InterpretedIntent,
    QueryPlan,
)
from app.services.query.context_manager import ContextManager
from app.services.query.relationship_graph import RelationshipGraph, RelationshipPath
from app.services.query.schema_registry import SchemaRegistry
from app.services.query.entity_registry import EntityRegistry

logger = logging.getLogger(__name__)


class QueryPlanner:
    """Plans and optimizes multi-index query execution.
    
    Analyzes natural language query intent to determine:
    - Which indices to query
    - Optimal execution order
    - Join strategies for related data
    - Context filters from session history
    
    Features:
    - Multi-index query planning
    - Relationship-based join resolution
    - Execution cost estimation
    - Context-aware filtering
    - Strategy selection (single, sequential, parallel, nested)
    
    Example:
        >>> planner = QueryPlanner(schema_registry, relationship_graph, context_manager)
        >>> plan = planner.create_plan(
        ...     session_id=session_id,
        ...     query_text="Show APIs with critical vulnerabilities",
        ...     intent=intent
        ... )
        >>> # Execute plan using MultiIndexExecutor
    """
    
    # Entity to index mapping (now using EntityRegistry)
    @classmethod
    def _get_entity_index_map(cls) -> Dict[str, str]:
        """Get entity-to-index mapping from EntityRegistry."""
        return {
            entity_type: index
            for entity_type in EntityRegistry.get_all_entity_types()
            if (index := EntityRegistry.get_index(entity_type)) is not None
        }
    
    # Cost weights for different operations
    COST_WEIGHTS = {
        "index_query": 0.2,
        "join": 0.3,
        "filter": 0.1,
        "aggregation": 0.2,
        "sort": 0.1,
    }
    
    def __init__(
        self,
        schema_registry: SchemaRegistry,
        relationship_graph: RelationshipGraph,
        context_manager: Optional[ContextManager] = None,
    ):
        """Initialize the query planner.
        
        Args:
            schema_registry: Schema registry for field validation
            relationship_graph: Relationship graph for join resolution
            context_manager: Optional context manager for session context
        """
        self.schema_registry = schema_registry
        self.relationship_graph = relationship_graph
        self.context_manager = context_manager
        logger.info("QueryPlanner initialized")
    
    def create_plan(
        self,
        session_id: UUID,
        query_text: str,
        intent: InterpretedIntent,
    ) -> QueryPlan:
        """Create an execution plan for a query.
        
        Args:
            session_id: Session identifier
            query_text: Original natural language query
            intent: Interpreted intent from query
            
        Returns:
            Complete query execution plan
        """
        logger.info(f"Creating query plan for: {query_text}")
        
        # Step 1: Select target indices based on entities
        target_indices = self._select_indices(intent)
        logger.debug(f"Selected indices: {target_indices}")
        
        # Step 2: Get context filters from session
        context_filters = self._get_context_filters(session_id, intent)
        logger.debug(f"Context filters: {context_filters}")
        
        # Step 3: Determine execution strategy
        strategy = self._determine_strategy(target_indices, intent)
        logger.debug(f"Execution strategy: {strategy}")
        
        # Step 4: Resolve relationships if multi-index
        if len(target_indices) > 1:
            index_queries, requires_join, join_strategy = self._resolve_relationships(
                target_indices, intent, context_filters
            )
        else:
            index_queries = [self._create_single_index_query(
                target_indices[0], intent, context_filters
            )]
            requires_join = False
            join_strategy = None
        
        # Step 5: Optimize execution order
        optimized_queries = self._optimize_execution_order(index_queries, strategy)
        
        # Step 6: Estimate execution cost
        estimated_cost = self._estimate_cost(optimized_queries, requires_join)
        
        # Create query plan
        plan = QueryPlan(
            session_id=session_id,
            original_query=query_text,
            interpreted_intent=intent,
            strategy=strategy,
            index_queries=optimized_queries,
            estimated_cost=estimated_cost,
            requires_join=requires_join,
            join_strategy=join_strategy,
            context_filters=context_filters,
        )
        
        logger.info(
            f"Created query plan: strategy={strategy}, "
            f"indices={len(optimized_queries)}, cost={estimated_cost:.2f}"
        )
        
        return plan
    
    def _select_indices(self, intent: InterpretedIntent) -> List[str]:
        """Select target indices based on query intent using EntityRegistry.
        
        Args:
            intent: Interpreted query intent
            
        Returns:
            List of target index names
        """
        indices = []
        
        for entity in intent.entities:
            index = EntityRegistry.get_index(entity)
            if index and index not in indices:
                indices.append(index)
            else:
                logger.warning(f"Unknown entity type or no index mapping: {entity}")
        
        # Default to api-inventory if no entities specified
        if not indices:
            indices = ["api-inventory"]
        
        return indices
    
    def _get_context_filters(
        self,
        session_id: UUID,
        intent: InterpretedIntent
    ) -> Dict[str, Any]:
        """Get context filters from session history.
        
        Args:
            session_id: Session identifier
            intent: Query intent
            
        Returns:
            Dictionary of context filters
        """
        if not self.context_manager:
            return {}
        
        context_filters = {}
        
        # Get session context
        session = self.context_manager.get_session_context(session_id)
        if not session:
            return {}
        
        # If intent already has explicit filters (e.g., gateway_id, api_id from UUID extraction),
        # don't add context filters as they may conflict
        if intent.filters:
            logger.debug(f"Skipping context filters - intent has explicit filters: {intent.filters}")
            return {}
        
        # Add entity IDs from previous queries if relevant
        for entity_type in intent.entities:
            # Map entity type to ID field
            id_field = f"{entity_type}_id"
            entity_ids = self.context_manager.get_entity_ids(
                session_id,
                id_field,
                from_last_query_only=True
            )
            
            if entity_ids:
                context_filters[id_field] = list(entity_ids)
                logger.debug(f"Added context filter: {id_field}={len(entity_ids)} IDs")
        
        # Add active filters from session
        if session.active_filters:
            context_filters.update(session.active_filters)
        
        return context_filters
    
    def _determine_strategy(
        self,
        indices: List[str],
        intent: InterpretedIntent
    ) -> ExecutionStrategy:
        """Determine optimal execution strategy.
        
        Args:
            indices: Target indices
            intent: Query intent
            
        Returns:
            Execution strategy
        """
        # Single index - simple query
        if len(indices) == 1:
            return ExecutionStrategy.SINGLE_INDEX
        
        # Check if indices have direct relationships
        has_direct_relationships = all(
            self.relationship_graph.has_relationship(indices[i], indices[i + 1])
            for i in range(len(indices) - 1)
        )
        
        # Determine based on query characteristics
        if has_direct_relationships:
            # Sequential for simple joins
            if len(indices) == 2:
                return ExecutionStrategy.SEQUENTIAL
            # Nested for complex multi-hop joins
            else:
                return ExecutionStrategy.NESTED
        else:
            # Parallel for independent queries
            return ExecutionStrategy.PARALLEL
    
    def _resolve_relationships(
        self,
        indices: List[str],
        intent: InterpretedIntent,
        context_filters: Dict[str, Any]
    ) -> Tuple[List[IndexQuery], bool, Optional[str]]:
        """Resolve relationships between indices.
        
        Args:
            indices: Target indices
            intent: Query intent
            context_filters: Context filters
            
        Returns:
            Tuple of (index queries, requires_join, join_strategy)
        """
        index_queries = []
        requires_join = len(indices) > 1
        join_strategy = None
        
        if len(indices) == 1:
            # Single index - no join needed
            query = self._create_single_index_query(indices[0], intent, context_filters)
            return [query], False, None
        
        # Find relationship path between first and last index
        primary_index = indices[0]
        secondary_index = indices[-1]
        
        path = self.relationship_graph.find_path(primary_index, secondary_index)
        
        if path:
            # Create queries following the relationship path
            for i, index in enumerate(path.path):
                depends_on = [path.path[i - 1]] if i > 0 else []
                join_fields = path.join_conditions[i - 1] if i > 0 else {}
                
                query = self._create_index_query(
                    index=index,
                    intent=intent,
                    context_filters=context_filters,
                    join_fields=join_fields,
                    depends_on=depends_on
                )
                index_queries.append(query)
            
            # Determine join strategy from first relationship
            if path.relationships:
                first_rel = path.relationships[0]
                join_strategy = list(first_rel.join_fields.keys())[0]
        else:
            # No direct path - create independent queries
            logger.warning(f"No relationship path found between {primary_index} and {secondary_index}")
            for index in indices:
                query = self._create_single_index_query(index, intent, context_filters)
                index_queries.append(query)
            requires_join = False
        
        return index_queries, requires_join, join_strategy
    
    def _create_single_index_query(
        self,
        index: str,
        intent: InterpretedIntent,
        context_filters: Dict[str, Any]
    ) -> IndexQuery:
        """Create a query for a single index.
        
        Args:
            index: Target index
            intent: Query intent
            context_filters: Context filters
            
        Returns:
            Index query
        """
        return self._create_index_query(
            index=index,
            intent=intent,
            context_filters=context_filters,
            join_fields={},
            depends_on=[]
        )
    
    def _create_index_query(
        self,
        index: str,
        intent: InterpretedIntent,
        context_filters: Dict[str, Any],
        join_fields: Dict[str, str],
        depends_on: List[str]
    ) -> IndexQuery:
        """Create an index query with filters and joins.
        
        Args:
            index: Target index
            intent: Query intent
            context_filters: Context filters
            join_fields: Join field mappings
            depends_on: Dependencies
            
        Returns:
            Index query
        """
        # Build query DSL
        must_clauses = []
        
        # Add intent filters
        for field, value in intent.filters.items():
            # Validate field exists in schema
            if self.schema_registry.validate_field(index, field):
                must_clauses.append({"term": {field: value}})
            else:
                logger.warning(f"Field {field} not found in {index} schema")
        
        # Add context filters
        for field, value in context_filters.items():
            if self.schema_registry.validate_field(index, field):
                if isinstance(value, list):
                    must_clauses.append({"terms": {field: value}})
                else:
                    must_clauses.append({"term": {field: value}})
        
        # Add time range filter if present
        if intent.time_range:
            # Determine time field based on index
            time_field = self._get_time_field(index)
            if time_field:
                must_clauses.append({
                    "range": {
                        time_field: {
                            "gte": intent.time_range.start.isoformat(),
                            "lte": intent.time_range.end.isoformat(),
                        }
                    }
                })
        
        # Build query DSL
        if must_clauses:
            query_dsl = {
                "query": {
                    "bool": {
                        "must": must_clauses
                    }
                }
            }
        else:
            query_dsl = {
                "query": {
                    "match_all": {}
                }
            }
        
        # Determine required fields
        required_fields = self._get_required_fields(index, intent)
        
        return IndexQuery(
            index=index,
            query_dsl=query_dsl,
            filters=intent.filters,
            required_fields=required_fields,
            join_fields=join_fields,
            depends_on=depends_on
        )
    
    def _get_time_field(self, index: str) -> Optional[str]:
        """Get the time field name for an index using EntityRegistry.
        
        Args:
            index: Index name
            
        Returns:
            Time field name or None
        """
        # Get entity type for index
        entity_type = EntityRegistry.get_entity_for_index(index)
        if entity_type:
            return EntityRegistry.get_time_field(entity_type)
        
        return "created_at"  # Default fallback
    
    def _get_required_fields(self, index: str, intent: InterpretedIntent) -> List[str]:
        """Get required fields for an index query.
        
        Args:
            index: Index name
            intent: Query intent
            
        Returns:
            List of required field names
        """
        # Base fields always needed
        base_fields = ["id"]
        
        # Add gateway_id if available
        if self.schema_registry.validate_field(index, "gateway_id"):
            base_fields.append("gateway_id")
        
        # Add api_id if available
        if self.schema_registry.validate_field(index, "api_id"):
            base_fields.append("api_id")
        
        # Add entity-specific fields
        if index == "api-inventory":
            base_fields.extend(["name", "base_path", "status"])
        elif index == "security-findings":
            base_fields.extend(["title", "severity", "status"])
        elif index.startswith("api-metrics-"):
            base_fields.extend(["timestamp", "request_count", "error_rate"])
        elif index == "api-predictions":
            base_fields.extend(["prediction_type", "confidence", "predicted_at"])
        elif index == "optimization-recommendations":
            base_fields.extend(["recommendation_type", "priority", "status"])
        elif index == "compliance-violations":
            base_fields.extend(["regulation", "severity", "status"])
        
        return base_fields
    
    def _optimize_execution_order(
        self,
        queries: List[IndexQuery],
        strategy: ExecutionStrategy
    ) -> List[IndexQuery]:
        """Optimize query execution order.
        
        Args:
            queries: List of index queries
            strategy: Execution strategy
            
        Returns:
            Optimized list of queries
        """
        if strategy == ExecutionStrategy.SINGLE_INDEX:
            return queries
        
        if strategy == ExecutionStrategy.PARALLEL:
            # No ordering needed for parallel execution
            return queries
        
        # For sequential and nested, order by dependencies
        ordered: List[IndexQuery] = []
        remaining = queries.copy()
        
        while remaining:
            # Find queries with no unmet dependencies
            ready = [
                q for q in remaining
                if all(dep in [oq.index for oq in ordered] for dep in q.depends_on)
            ]
            
            if not ready:
                # Circular dependency or error - return as-is
                logger.warning("Could not resolve query dependencies")
                return queries
            
            # Add ready queries (prefer smaller result sets first)
            ready.sort(key=lambda q: len(q.filters))
            ordered.extend(ready)
            
            # Remove from remaining
            for q in ready:
                remaining.remove(q)
        
        return ordered
    
    def _estimate_cost(self, queries: List[IndexQuery], requires_join: bool) -> float:
        """Estimate execution cost for a query plan.
        
        Args:
            queries: List of index queries
            requires_join: Whether join is required
            
        Returns:
            Estimated cost (0-1, higher = more expensive)
        """
        cost = 0.0
        
        # Base cost per index query
        cost += len(queries) * self.COST_WEIGHTS["index_query"]
        
        # Join cost
        if requires_join:
            cost += self.COST_WEIGHTS["join"] * (len(queries) - 1)
        
        # Filter cost (more filters = lower cost due to selectivity)
        total_filters = sum(len(q.filters) for q in queries)
        if total_filters > 0:
            cost -= self.COST_WEIGHTS["filter"] * min(total_filters, 5) / 5
        
        # Normalize to 0-1 range
        cost = max(0.0, min(1.0, cost))
        
        return cost
    
    def validate_plan(self, plan: QueryPlan) -> Tuple[bool, List[str]]:
        """Validate a query plan.
        
        Args:
            plan: Query plan to validate
            
        Returns:
            Tuple of (is_valid, list of validation errors)
        """
        errors = []
        
        # Check that all indices exist in schema
        for query in plan.index_queries:
            if query.index not in self.schema_registry.get_all_indices():
                # Check if it's a pattern
                if not any(
                    idx.startswith(query.index.replace('*', ''))
                    for idx in self.schema_registry.get_all_indices()
                ):
                    errors.append(f"Index not found: {query.index}")
        
        # Check that dependencies are valid
        index_names = {q.index for q in plan.index_queries}
        for query in plan.index_queries:
            for dep in query.depends_on:
                if dep not in index_names:
                    errors.append(f"Invalid dependency: {query.index} depends on {dep}")
        
        # Check that join fields are valid
        for query in plan.index_queries:
            for source_field, target_field in query.join_fields.items():
                if not self.schema_registry.validate_field(query.index, target_field):
                    errors.append(
                        f"Invalid join field: {target_field} not found in {query.index}"
                    )
        
        return len(errors) == 0, errors


# Made with Bob