"""Integration tests for Enhanced Intent Extractor.

Tests the complete flow of context-aware intent extraction including:
- Reference detection
- Entity resolution
- Relationship identification
- Context dependency tracking
- Multi-index query planning
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.models.enhanced_intent import (
    ReferenceType,
    ContextDependency,
)
from app.models.query import QueryType
from app.services.llm_service import LLMService
from app.services.query.context_manager import ContextManager
from app.services.query.intent_extractor import EnhancedIntentExtractor
from app.services.query.relationship_graph import RelationshipGraph
from app.config import Settings


@pytest.fixture
def settings():
    """Create test settings."""
    return Settings()


@pytest.fixture
def llm_service(settings):
    """Create LLM service for testing."""
    return LLMService(settings)


@pytest.fixture
def context_manager():
    """Create context manager for testing."""
    return ContextManager(session_ttl_minutes=30)


@pytest.fixture
def relationship_graph():
    """Create relationship graph for testing."""
    return RelationshipGraph()


@pytest.fixture
def intent_extractor(llm_service, context_manager, relationship_graph):
    """Create enhanced intent extractor for testing."""
    return EnhancedIntentExtractor(llm_service, context_manager, relationship_graph)


@pytest.mark.asyncio
class TestEnhancedIntentExtractor:
    """Test suite for EnhancedIntentExtractor."""
    
    async def test_basic_intent_extraction_no_context(self, intent_extractor):
        """Test basic intent extraction without context."""
        session_id = uuid4()
        query_text = "Show me all critical vulnerabilities"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.SECURITY
        )
        
        # Verify basic intent
        assert intent.action in ["list", "show"]
        assert "vulnerability" in intent.entities
        assert not intent.has_references()
        assert not intent.requires_context()
        assert len(intent.target_indices) > 0
    
    async def test_demonstrative_reference_detection(self, intent_extractor, context_manager):
        """Test detection of demonstrative references like 'these APIs'."""
        session_id = uuid4()
        
        # First query - establish context
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Which APIs are insecure?",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001", "API-002", "API-003"]},
            result_count=3
        )
        
        # Second query with reference
        query_text = "What vulnerabilities affect these APIs?"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.SECURITY
        )
        
        # Verify reference detection
        assert intent.has_references()
        assert len(intent.references) > 0
        
        # Find the demonstrative reference
        demo_refs = [r for r in intent.references if r.reference_type == ReferenceType.DEMONSTRATIVE]
        assert len(demo_refs) > 0
        assert demo_refs[0].entity_type == "api"
        assert len(demo_refs[0].resolved_ids) == 3
        
        # Verify context dependency
        assert intent.requires_context()
        assert intent.context_dependency.depends_on_previous
        assert "api" in intent.context_dependency.required_entity_types
    
    async def test_entity_resolution_from_context(self, intent_extractor, context_manager):
        """Test entity resolution from session context."""
        session_id = uuid4()
        
        # Store context with API IDs
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Show APIs on gateway GW-001",
            target_indices=["api-inventory"],
            entity_ids={
                "api_id": ["API-001", "API-002"],
                "gateway_id": ["GW-001"]
            },
            result_count=2
        )
        
        # Query with reference
        query_text = "Show vulnerabilities for these APIs"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.SECURITY
        )
        
        # Verify entity resolution
        assert "api_id" in intent.resolved_entities
        assert len(intent.resolved_entities["api_id"]) == 2
        assert "API-001" in intent.resolved_entities["api_id"]
        assert "API-002" in intent.resolved_entities["api_id"]
    
    async def test_relationship_identification(self, intent_extractor, context_manager):
        """Test identification of entity relationships."""
        session_id = uuid4()
        
        # Store context with API IDs
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Which APIs are slow?",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001", "API-002"]},
            result_count=2
        )
        
        # Query that requires relationship
        query_text = "Show predictions for these APIs"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.PREDICTION
        )
        
        # Verify relationship identification
        assert intent.has_relationships()
        assert len(intent.relationships) > 0
        
        # Check relationship details
        rel = intent.relationships[0]
        assert rel.source_entity == "api"
        assert rel.target_entity == "prediction"
        assert "api_id" in rel.join_fields
    
    async def test_multi_index_query_planning(self, intent_extractor, context_manager):
        """Test multi-index query planning."""
        session_id = uuid4()
        
        # Store context
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Show insecure APIs",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001"]},
            result_count=1
        )
        
        # Query requiring multiple indices
        query_text = "What vulnerabilities and compliance violations affect these APIs?"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.SECURITY
        )
        
        # Verify multi-index planning
        assert len(intent.target_indices) >= 2
        assert intent.requires_join
        assert "security-findings" in intent.target_indices or any(
            "security" in idx for idx in intent.target_indices
        )
    
    async def test_implicit_reference_detection(self, intent_extractor, context_manager):
        """Test detection of implicit references."""
        session_id = uuid4()
        
        # Store context
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="List all APIs",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001", "API-002"]},
            result_count=2
        )
        
        # Query with implicit reference
        query_text = "Show metrics for the APIs"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.PERFORMANCE
        )
        
        # Verify implicit reference or context usage
        assert intent.requires_context() or len(intent.resolved_entities) > 0
    
    async def test_no_context_fallback(self, intent_extractor):
        """Test fallback behavior when no context is available."""
        session_id = uuid4()
        
        # Query with reference but no context
        query_text = "Show vulnerabilities for these APIs"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.SECURITY
        )
        
        # Should still extract intent, but with empty resolved entities
        assert intent is not None
        assert "vulnerability" in intent.entities
        # References may be detected but not resolved
        if intent.has_references():
            for ref in intent.references:
                assert len(ref.resolved_ids) == 0
    
    async def test_context_dependency_tracking(self, intent_extractor, context_manager):
        """Test context dependency tracking."""
        session_id = uuid4()
        
        # Store context
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Show critical APIs",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001"]},
            result_count=1
        )
        
        # Dependent query
        query_text = "What are the security issues for these?"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id,
            query_type=QueryType.SECURITY
        )
        
        # Verify context dependency
        assert intent.context_dependency.depends_on_previous
        assert len(intent.context_dependency.required_entity_types) > 0
        assert intent.context_dependency.context_window >= 1
    
    async def test_session_isolation(self, intent_extractor, context_manager):
        """Test that sessions are properly isolated."""
        session_id_1 = uuid4()
        session_id_2 = uuid4()
        
        # Store context in session 1
        context_manager.store_query_context(
            session_id=session_id_1,
            query_id=uuid4(),
            query_text="Show APIs",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001"]},
            result_count=1
        )
        
        # Query in session 2 (should not have access to session 1 context)
        query_text = "Show vulnerabilities for these APIs"
        
        intent = await intent_extractor.extract_intent(
            query_text=query_text,
            session_id=session_id_2,
            query_type=QueryType.SECURITY
        )
        
        # Should not resolve entities from session 1
        assert len(intent.resolved_entities) == 0 or "api_id" not in intent.resolved_entities


@pytest.mark.asyncio
class TestReferenceDetection:
    """Test suite for reference detection logic."""
    
    def test_demonstrative_patterns(self, intent_extractor, context_manager):
        """Test detection of demonstrative reference patterns."""
        session_id = uuid4()
        session_context = context_manager.create_session(session_id)
        
        # Test various demonstrative patterns
        test_cases = [
            ("these APIs", "api"),
            ("those vulnerabilities", "vulnerability"),
            ("this gateway", "gateway"),
            ("that prediction", "prediction"),
            ("the above APIs", "api"),
            ("the following services", "api"),
        ]
        
        for query_text, expected_entity in test_cases:
            references = intent_extractor._detect_references(query_text, session_context)
            assert len(references) > 0, f"Failed to detect reference in: {query_text}"
            assert any(
                ref.reference_type == ReferenceType.DEMONSTRATIVE and ref.entity_type == expected_entity
                for ref in references
            ), f"Failed to correctly identify entity type in: {query_text}"
    
    def test_entity_word_mapping(self, intent_extractor):
        """Test mapping of words to entity types."""
        test_cases = [
            ("api", "api"),
            ("apis", "api"),
            ("endpoint", "api"),
            ("service", "api"),
            ("gateway", "gateway"),
            ("vulnerability", "vulnerability"),
            ("vuln", "vulnerability"),
            ("metric", "metric"),
            ("prediction", "prediction"),
        ]
        
        for word, expected_type in test_cases:
            entity_type = intent_extractor._map_word_to_entity_type(word)
            assert entity_type == expected_type, f"Failed to map '{word}' to '{expected_type}'"


@pytest.mark.asyncio
class TestRelationshipIdentification:
    """Test suite for relationship identification."""
    
    def test_api_to_vulnerability_relationship(self, intent_extractor):
        """Test identification of API to vulnerability relationship."""
        entities = ["vulnerability"]
        query_text = "Show vulnerabilities for the APIs"
        resolved_entities = {"api_id": ["API-001", "API-002"]}
        
        relationships = intent_extractor._identify_relationships(
            entities, query_text, resolved_entities
        )
        
        assert len(relationships) > 0
        rel = relationships[0]
        assert rel.source_entity == "api"
        assert rel.target_entity == "vulnerability"
        assert "api_id" in rel.join_fields
    
    def test_api_to_metrics_relationship(self, intent_extractor):
        """Test identification of API to metrics relationship."""
        entities = ["metric"]
        query_text = "Show metrics for these APIs"
        resolved_entities = {"api_id": ["API-001"]}
        
        relationships = intent_extractor._identify_relationships(
            entities, query_text, resolved_entities
        )
        
        assert len(relationships) > 0
        rel = relationships[0]
        assert rel.source_entity == "api"
        assert rel.target_entity == "metric"


# Made with Bob