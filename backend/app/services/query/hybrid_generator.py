"""
Hybrid Query Generator

Combines rule-based and LLM-based query generation for optimal performance.
Uses fast rule-based approach for common patterns, falls back to LLM for complex queries.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple

from .schema_registry import SchemaRegistry
from .concept_mapper import ConceptMapper
from .llm_generator import SchemaAwareLLMQueryGenerator
from .validator import QueryValidator

logger = logging.getLogger(__name__)


class HybridQueryGenerator:
    """
    Combines rule-based and LLM-based query generation.
    
    Features:
    - Fast rule-based path for common patterns
    - LLM fallback for complex queries
    - Query caching for performance
    - Automatic complexity detection
    - Validation of all generated queries
    
    Example:
        >>> generator = HybridQueryGenerator(schema_registry, concept_mapper, llm_generator, validator)
        >>> dsl = await generator.generate_query("Show me insecure APIs", "api-inventory")
        >>> # Uses rule-based if possible, LLM if needed
    """
    
    def __init__(
        self,
        schema_registry: SchemaRegistry,
        concept_mapper: ConceptMapper,
        llm_generator: SchemaAwareLLMQueryGenerator,
        validator: QueryValidator
    ):
        """
        Initialize the hybrid query generator.
        
        Args:
            schema_registry: Schema registry for field validation
            concept_mapper: Concept mapper for rule-based generation
            llm_generator: LLM generator for complex queries
            validator: Query validator for DSL validation
        """
        self.schema_registry = schema_registry
        self.concept_mapper = concept_mapper
        self.llm_generator = llm_generator
        self.validator = validator
        self.query_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        self.rule_based_success = 0
        self.llm_fallback_count = 0
    
    async def generate_query(
        self,
        query_text: str,
        index: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate query using hybrid approach.
        
        Args:
            query_text: Natural language query
            index: Target OpenSearch index
            context: Optional context (e.g., time range, filters)
            
        Returns:
            OpenSearch DSL query dictionary
        """
        # Check cache first
        cache_key = self._build_cache_key(query_text, index, context)
        if cache_key in self.query_cache:
            self.cache_hits += 1
            logger.debug(f"Cache hit for query: {query_text}")
            return self.query_cache[cache_key]
        
        self.cache_misses += 1
        
        # Assess query complexity
        complexity = self._assess_complexity(query_text)
        
        # Try rule-based approach first for simple queries
        if complexity == "simple":
            try:
                dsl = self._try_rule_based(query_text, index, context)
                if dsl:
                    # Validate before returning
                    is_valid, error = self.validator.validate(dsl, index)
                    if is_valid:
                        self.rule_based_success += 1
                        logger.info(f"Rule-based generation succeeded for: {query_text}")
                        self.query_cache[cache_key] = dsl
                        return dsl
                    else:
                        logger.debug(f"Rule-based query invalid: {error}")
            except Exception as e:
                logger.debug(f"Rule-based generation failed: {e}")
        
        # Fall back to LLM (slow path but more flexible)
        logger.info(f"Using LLM fallback for query: {query_text}")
        self.llm_fallback_count += 1
        dsl = await self.llm_generator.generate_query(query_text, index, context)
        self.query_cache[cache_key] = dsl
        return dsl
    
    def _build_cache_key(
        self,
        query_text: str,
        index: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Build cache key from query parameters.
        
        Args:
            query_text: Natural language query
            index: Target index
            context: Optional context
            
        Returns:
            Cache key string
        """
        key = f"{index}:{query_text.lower()}"
        if context:
            # Include relevant context in cache key
            if "time_range" in context:
                key += f":time_range"
            if "filters" in context:
                key += f":filters:{len(context['filters'])}"
        return key
    
    def _assess_complexity(self, query_text: str) -> str:
        """
        Assess query complexity to determine generation strategy.
        
        Args:
            query_text: Natural language query
            
        Returns:
            Complexity level: "simple", "medium", or "complex"
        """
        query_lower = query_text.lower()
        
        # Complex indicators
        complex_indicators = [
            r'\band\b.*\band\b',  # Multiple AND conditions
            r'\bor\b',  # OR conditions
            r'\bbut\s+not\b',  # Complex negations
            r'\bexcept\b',  # Exclusions
            r'\bcompare\b',  # Comparisons
            r'\bversus\b',  # Comparisons
            r'\bwith\b.*\bwithout\b',  # Mixed conditions
            r'\btop\s+\d+\b',  # Aggregations
            r'\baverage\b',  # Aggregations
            r'\bcount\b.*\bby\b',  # Group by
        ]
        
        for pattern in complex_indicators:
            if re.search(pattern, query_lower):
                return "complex"
        
        # Medium complexity indicators
        medium_indicators = [
            r'\band\b',  # Single AND
            r'\bnot\b',  # Negation
            r'\bwithout\b',  # Negation
            r'\bbetween\b',  # Range
        ]
        
        for pattern in medium_indicators:
            if re.search(pattern, query_lower):
                return "medium"
        
        # Simple query (single concept)
        return "simple"
    
    def _try_rule_based(
        self,
        query_text: str,
        index: str,
        context: Optional[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """
        Try to generate query using rules and concept mapping.
        
        Args:
            query_text: Natural language query
            index: Target index
            context: Optional context
            
        Returns:
            DSL query dictionary or None if rule-based generation fails
        """
        # Extract concepts from query
        concepts = self.concept_mapper.extract_concepts(query_text)
        
        if not concepts:
            return None
        
        # Build query from concepts
        must_clauses = []
        must_not_clauses = []
        should_clauses: List[Dict[str, Any]] = []
        
        for concept, negated in concepts:
            mapping = self.concept_mapper.map_concept(concept, negated)
            if not mapping:
                # Unknown concept, need LLM
                return None
            
            # Check if field exists in schema
            field = mapping.get("field")
            if field and not self.schema_registry.validate_field(index, field):
                logger.debug(f"Field {field} not found in schema, falling back to LLM")
                return None
            
            # Build clause based on mapping
            clause = self.concept_mapper.build_opensearch_clause(mapping)
            if not clause:
                return None
            
            # Handle negation at bool level if needed
            if "must_not" in clause.get("bool", {}):
                must_not_clauses.extend(clause["bool"]["must_not"])
            elif negated and mapping.get("operator") != "must_not_term":
                must_not_clauses.append(clause)
            else:
                must_clauses.append(clause)
        
        # Build final query
        if not must_clauses and not must_not_clauses:
            return None
        
        query: Dict[str, Any] = {"query": {"bool": {}}}
        
        if must_clauses:
            query["query"]["bool"]["must"] = must_clauses
        if must_not_clauses:
            query["query"]["bool"]["must_not"] = must_not_clauses
        if should_clauses:
            query["query"]["bool"]["should"] = should_clauses
        
        # Add context if provided
        if context:
            if "time_range" in context:
                time_range = context["time_range"]
                time_clause = {
                    "range": {
                        "timestamp": {
                            "gte": time_range.get("start"),
                            "lte": time_range.get("end")
                        }
                    }
                }
                if "must" not in query["query"]["bool"]:
                    query["query"]["bool"]["must"] = []
                query["query"]["bool"]["must"].append(time_clause)
            
            if "filters" in context:
                for field, value in context["filters"].items():
                    filter_clause = {"term": {field: value}}
                    if "filter" not in query["query"]["bool"]:
                        query["query"]["bool"]["filter"] = []
                    query["query"]["bool"]["filter"].append(filter_clause)
        
        return query
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        self.query_cache.clear()
        logger.info("Query cache cleared")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.query_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": f"{hit_rate:.2f}%",
            "rule_based_success": self.rule_based_success,
            "llm_fallback_count": self.llm_fallback_count,
            "total_requests": total_requests,
        }
    
    def reset_stats(self) -> None:
        """Reset statistics counters."""
        self.cache_hits = 0
        self.cache_misses = 0
        self.rule_based_success = 0
        self.llm_fallback_count = 0
        logger.info("Statistics reset")
    
    async def warm_cache(self, common_queries: List[Tuple[str, str]]) -> None:
        """
        Warm up cache with common queries.
        
        Args:
            common_queries: List of (query_text, index) tuples
        """
        logger.info(f"Warming cache with {len(common_queries)} queries")
        
        for query_text, index in common_queries:
            try:
                await self.generate_query(query_text, index)
            except Exception as e:
                logger.warning(f"Failed to warm cache for query '{query_text}': {e}")
        
        logger.info(f"Cache warmed. Size: {len(self.query_cache)}")
    
    def get_cached_query(self, query_text: str, index: str) -> Optional[Dict[str, Any]]:
        """
        Get cached query without generating new one.
        
        Args:
            query_text: Natural language query
            index: Target index
            
        Returns:
            Cached DSL query or None
        """
        cache_key = self._build_cache_key(query_text, index, None)
        return self.query_cache.get(cache_key)

# Made with Bob