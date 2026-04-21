"""
Integration tests for enhanced query service with Phase 2 components.

Tests the complete query generation pipeline including:
- Schema-aware LLM query generation
- Hybrid query generation (rule-based + LLM)
- Query validation
- Integration with QueryService
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

from app.services.query_service import QueryService
from app.services.llm_service import LLMService
from app.services.query import (
    SchemaRegistry,
    ConceptMapper,
    QueryValidator,
    SchemaAwareLLMQueryGenerator,
    HybridQueryGenerator,
)
from app.models.query import QueryType, InterpretedIntent, TimeRange


@pytest.fixture
def mock_opensearch_client():
    """Mock OpenSearch client."""
    client = Mock()
    client.indices.get_mapping.return_value = {
        "api-inventory": {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text"},
                    "status": {"type": "keyword"},
                    "intelligence_metadata": {
                        "properties": {
                            "security_score": {"type": "float"},
                            "health_score": {"type": "float"},
                            "risk_score": {"type": "float"},
                            "is_shadow": {"type": "boolean"},
                        }
                    }
                }
            }
        }
    }
    return client


@pytest.fixture
def schema_registry(mock_opensearch_client):
    """Create schema registry with mock client."""
    registry = SchemaRegistry(mock_opensearch_client)
    return registry


@pytest.fixture
def concept_mapper():
    """Create concept mapper."""
    return ConceptMapper()


@pytest.fixture
def query_validator(schema_registry):
    """Create query validator."""
    return QueryValidator(schema_registry)


@pytest.fixture
def mock_llm_service():
    """Mock LLM service."""
    service = Mock(spec=LLMService)
    service.generate_completion = AsyncMock()
    return service


@pytest.fixture
def llm_generator(mock_llm_service, schema_registry, concept_mapper, query_validator):
    """Create LLM query generator."""
    return SchemaAwareLLMQueryGenerator(
        mock_llm_service,
        schema_registry,
        concept_mapper,
        query_validator
    )


@pytest.fixture
def hybrid_generator(schema_registry, concept_mapper, llm_generator, query_validator):
    """Create hybrid query generator."""
    return HybridQueryGenerator(
        schema_registry,
        concept_mapper,
        llm_generator,
        query_validator
    )


class TestSchemaRegistry:
    """Test schema registry functionality."""
    
    @pytest.mark.asyncio
    async def test_load_schemas(self, schema_registry):
        """Test loading schemas from OpenSearch."""
        await schema_registry.load_schemas()
        
        assert "api-inventory" in schema_registry.schemas
        assert "id" in schema_registry.schemas["api-inventory"]["fields"]
        assert "intelligence_metadata.security_score" in schema_registry.schemas["api-inventory"]["fields"]
    
    @pytest.mark.asyncio
    async def test_validate_field(self, schema_registry):
        """Test field validation."""
        await schema_registry.load_schemas()
        
        # Valid fields
        assert schema_registry.validate_field("api-inventory", "id")
        assert schema_registry.validate_field("api-inventory", "intelligence_metadata.security_score")
        
        # Invalid fields
        assert not schema_registry.validate_field("api-inventory", "nonexistent_field")
    
    @pytest.mark.asyncio
    async def test_get_field_type(self, schema_registry):
        """Test getting field types."""
        await schema_registry.load_schemas()
        
        assert schema_registry.get_field_type("api-inventory", "id") == "keyword"
        assert schema_registry.get_field_type("api-inventory", "intelligence_metadata.security_score") == "float"
    
    @pytest.mark.asyncio
    async def test_get_schema_context(self, schema_registry):
        """Test generating schema context for LLM."""
        await schema_registry.load_schemas()
        
        context = schema_registry.get_schema_context("api-inventory")
        
        assert "api-inventory" in context
        assert "intelligence_metadata.security_score" in context
        assert "float" in context


class TestConceptMapper:
    """Test concept mapper functionality."""
    
    def test_map_simple_concept(self, concept_mapper):
        """Test mapping simple concepts."""
        # Security concepts
        mapping = concept_mapper.map_concept("insecure")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.security_score"
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 50
    
    def test_map_negated_concept(self, concept_mapper):
        """Test mapping negated concepts."""
        mapping = concept_mapper.map_concept("secure", negated=True)
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.security_score"
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 70
    
    def test_map_synonym(self, concept_mapper):
        """Test mapping synonyms."""
        mapping = concept_mapper.map_concept("unsafe")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.security_score"
    
    def test_extract_concepts(self, concept_mapper):
        """Test extracting concepts from query text."""
        concepts = concept_mapper.extract_concepts("Show me insecure APIs")
        
        assert len(concepts) > 0
        assert any(concept == "insecure" for concept, _ in concepts)
    
    def test_extract_negated_concepts(self, concept_mapper):
        """Test extracting negated concepts."""
        concepts = concept_mapper.extract_concepts("Show me APIs that are not secure")
        
        # Should detect "secure" with negation
        secure_concepts = [(c, neg) for c, neg in concepts if c == "secure"]
        assert len(secure_concepts) > 0
        assert secure_concepts[0][1] is True  # negated
    
    def test_build_opensearch_clause(self, concept_mapper):
        """Test building OpenSearch clauses."""
        mapping = concept_mapper.map_concept("insecure")
        clause = concept_mapper.build_opensearch_clause(mapping)
        
        assert "range" in clause
        assert "intelligence_metadata.security_score" in clause["range"]


class TestQueryValidator:
    """Test query validator functionality."""
    
    @pytest.mark.asyncio
    async def test_validate_valid_query(self, query_validator, schema_registry):
        """Test validating a valid query."""
        await schema_registry.load_schemas()
        
        dsl = {
            "query": {
                "range": {
                    "intelligence_metadata.security_score": {
                        "lt": 50
                    }
                }
            }
        }
        
        is_valid, error = query_validator.validate(dsl, "api-inventory")
        assert is_valid
        assert error is None
    
    @pytest.mark.asyncio
    async def test_validate_invalid_field(self, query_validator, schema_registry):
        """Test validating query with invalid field."""
        await schema_registry.load_schemas()
        
        dsl = {
            "query": {
                "term": {
                    "nonexistent_field": "value"
                }
            }
        }
        
        is_valid, error = query_validator.validate(dsl, "api-inventory")
        assert not is_valid
        assert "Invalid field" in error
    
    @pytest.mark.asyncio
    async def test_validate_missing_query_key(self, query_validator):
        """Test validating query without 'query' key."""
        dsl = {
            "term": {
                "status": "active"
            }
        }
        
        is_valid, error = query_validator.validate(dsl, "api-inventory")
        assert not is_valid
        assert "Missing 'query' key" in error


class TestSchemaAwareLLMQueryGenerator:
    """Test LLM query generator functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_simple_query(self, llm_generator, mock_llm_service, schema_registry):
        """Test generating a simple query."""
        await schema_registry.load_schemas()
        
        # Mock LLM response
        mock_llm_service.generate_completion.return_value = {
            "content": '{"query": {"range": {"intelligence_metadata.security_score": {"lt": 50}}}}',
            "model": "gpt-4",
            "usage": {"total_tokens": 100},
            "cost": 0.001
        }
        
        dsl = await llm_generator.generate_query("Show me insecure APIs", "api-inventory")
        
        assert "query" in dsl
        assert "range" in dsl["query"]
        mock_llm_service.generate_completion.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_query_with_retry(self, llm_generator, mock_llm_service, schema_registry):
        """Test query generation with retry on invalid output."""
        await schema_registry.load_schemas()
        
        # First call returns invalid query, second call returns valid
        mock_llm_service.generate_completion.side_effect = [
            {
                "content": '{"query": {"term": {"invalid_field": "value"}}}',
                "model": "gpt-4",
                "usage": {"total_tokens": 100},
                "cost": 0.001
            },
            {
                "content": '{"query": {"range": {"intelligence_metadata.security_score": {"lt": 50}}}}',
                "model": "gpt-4",
                "usage": {"total_tokens": 100},
                "cost": 0.001
            }
        ]
        
        dsl = await llm_generator.generate_query("Show me insecure APIs", "api-inventory")
        
        assert "query" in dsl
        assert mock_llm_service.generate_completion.call_count == 2


class TestHybridQueryGenerator:
    """Test hybrid query generator functionality."""
    
    @pytest.mark.asyncio
    async def test_generate_simple_query_rule_based(self, hybrid_generator, schema_registry):
        """Test generating simple query using rule-based approach."""
        await schema_registry.load_schemas()
        
        dsl = await hybrid_generator.generate_query("Show me insecure APIs", "api-inventory")
        
        assert "query" in dsl
        assert hybrid_generator.rule_based_success > 0
    
    @pytest.mark.asyncio
    async def test_generate_complex_query_llm_fallback(self, hybrid_generator, mock_llm_service, schema_registry):
        """Test generating complex query with LLM fallback."""
        await schema_registry.load_schemas()
        
        # Mock LLM response for complex query
        mock_llm_service.generate_completion.return_value = {
            "content": '{"query": {"bool": {"must": [{"range": {"intelligence_metadata.security_score": {"lt": 50}}}, {"term": {"status": "active"}}]}}}',
            "model": "gpt-4",
            "usage": {"total_tokens": 150},
            "cost": 0.002
        }
        
        dsl = await hybrid_generator.generate_query(
            "Show me active APIs with security issues and high error rates",
            "api-inventory"
        )
        
        assert "query" in dsl
        assert hybrid_generator.llm_fallback_count > 0
    
    @pytest.mark.asyncio
    async def test_query_caching(self, hybrid_generator, schema_registry):
        """Test query caching functionality."""
        await schema_registry.load_schemas()
        
        query_text = "Show me insecure APIs"
        
        # First call
        dsl1 = await hybrid_generator.generate_query(query_text, "api-inventory")
        cache_misses_1 = hybrid_generator.cache_misses
        
        # Second call (should hit cache)
        dsl2 = await hybrid_generator.generate_query(query_text, "api-inventory")
        cache_hits = hybrid_generator.cache_hits
        
        assert dsl1 == dsl2
        assert cache_hits > 0
    
    def test_assess_complexity(self, hybrid_generator):
        """Test query complexity assessment."""
        # Simple query
        assert hybrid_generator._assess_complexity("Show me insecure APIs") == "simple"
        
        # Medium complexity
        assert hybrid_generator._assess_complexity("Show me APIs that are not secure") == "medium"
        
        # Complex query
        assert hybrid_generator._assess_complexity("Show me APIs with high error rates and low security or compliance issues") == "complex"
    
    def test_get_cache_stats(self, hybrid_generator):
        """Test getting cache statistics."""
        stats = hybrid_generator.get_cache_stats()
        
        assert "cache_size" in stats
        assert "cache_hits" in stats
        assert "cache_misses" in stats
        assert "hit_rate" in stats
        assert "rule_based_success" in stats
        assert "llm_fallback_count" in stats


class TestQueryServiceIntegration:
    """Test integration with QueryService."""
    
    @pytest.mark.asyncio
    async def test_enhanced_query_generation_in_service(self, mock_opensearch_client):
        """Test that QueryService uses enhanced query generation."""
        # Create mock repositories
        query_repo = Mock()
        api_repo = Mock()
        api_repo.client = mock_opensearch_client
        metrics_repo = Mock()
        prediction_repo = Mock()
        recommendation_repo = Mock()
        
        # Create mock LLM service
        llm_service = Mock(spec=LLMService)
        llm_service.generate_completion = AsyncMock()
        llm_service.generate_completion.return_value = {
            "content": '{"action": "list", "entities": ["api"], "filters": {}, "confidence": 0.9}',
            "model": "gpt-4",
            "usage": {"total_tokens": 100},
            "cost": 0.001
        }
        
        # Create QueryService
        service = QueryService(
            query_repository=query_repo,
            api_repository=api_repo,
            metrics_repository=metrics_repo,
            prediction_repository=prediction_repo,
            recommendation_repository=recommendation_repo,
            llm_service=llm_service
        )
        
        # Verify enhanced components are initialized
        assert hasattr(service, 'hybrid_generator')
        assert hasattr(service, 'schema_registry')
        assert hasattr(service, 'concept_mapper')
        assert hasattr(service, 'query_validator')


# Made with Bob