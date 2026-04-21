"""
Unit tests for ConceptMapper

Tests concept mapping, synonym handling, negation detection, and OpenSearch clause generation.
"""

import pytest
from app.services.query.concept_mapper import ConceptMapper, ConceptCategory


@pytest.fixture
def concept_mapper():
    """Create a ConceptMapper instance."""
    return ConceptMapper()


class TestConceptMapper:
    """Test suite for ConceptMapper."""
    
    def test_initialization(self, concept_mapper):
        """Test ConceptMapper initialization."""
        assert concept_mapper is not None
        assert len(ConceptMapper.CONCEPT_MAPPINGS) > 0
        assert len(ConceptMapper.SYNONYMS) > 0
    
    def test_map_concept_security(self, concept_mapper):
        """Test mapping security concepts."""
        # Test "secure" concept
        mapping = concept_mapper.map_concept("secure")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.security_score"
        assert mapping["operator"] == "gte"
        assert mapping["value"] == 70
        assert mapping["category"] == ConceptCategory.SECURITY
        
        # Test "insecure" concept
        mapping = concept_mapper.map_concept("insecure")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.security_score"
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 50
    
    def test_map_concept_health(self, concept_mapper):
        """Test mapping health concepts."""
        # Test "healthy" concept
        mapping = concept_mapper.map_concept("healthy")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.health_score"
        assert mapping["operator"] == "gte"
        assert mapping["value"] == 80
        
        # Test "failing" concept
        mapping = concept_mapper.map_concept("failing")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.health_score"
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 30
    
    def test_map_concept_risk(self, concept_mapper):
        """Test mapping risk concepts."""
        # Test "high risk" concept
        mapping = concept_mapper.map_concept("high risk")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.risk_score"
        assert mapping["operator"] == "gte"
        assert mapping["value"] == 70
        
        # Test "low risk" concept
        mapping = concept_mapper.map_concept("low risk")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.risk_score"
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 40
    
    def test_map_concept_status(self, concept_mapper):
        """Test mapping status concepts."""
        # Test "active" concept
        mapping = concept_mapper.map_concept("active")
        assert mapping is not None
        assert mapping["field"] == "status"
        assert mapping["operator"] == "term"
        assert mapping["value"] == "active"
        
        # Test "inactive" concept
        mapping = concept_mapper.map_concept("inactive")
        assert mapping is not None
        assert mapping["field"] == "status"
        assert mapping["operator"] == "term"
        assert mapping["value"] == "inactive"
    
    def test_map_concept_with_negation(self, concept_mapper):
        """Test concept mapping with negation."""
        # Test "secure" negated (should become "not secure")
        mapping = concept_mapper.map_concept("secure", negated=True)
        assert mapping is not None
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 70
        
        # Test "healthy" negated
        mapping = concept_mapper.map_concept("healthy", negated=True)
        assert mapping is not None
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 80
    
    def test_map_concept_synonyms(self, concept_mapper):
        """Test synonym handling."""
        # Test "unsafe" (synonym for "insecure")
        mapping = concept_mapper.map_concept("unsafe")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.security_score"
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 50
        
        # Test "broken" (synonym for "failing")
        mapping = concept_mapper.map_concept("broken")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.health_score"
        assert mapping["operator"] == "lt"
        assert mapping["value"] == 30
    
    def test_map_concept_case_insensitive(self, concept_mapper):
        """Test case-insensitive concept mapping."""
        # Test various cases
        mapping1 = concept_mapper.map_concept("SECURE")
        mapping2 = concept_mapper.map_concept("Secure")
        mapping3 = concept_mapper.map_concept("secure")
        
        assert mapping1 is not None
        assert mapping2 is not None
        assert mapping3 is not None
        assert mapping1["field"] == mapping2["field"] == mapping3["field"]
    
    def test_map_concept_unknown(self, concept_mapper):
        """Test mapping unknown concept."""
        mapping = concept_mapper.map_concept("unknown_concept_xyz")
        assert mapping is None
    
    def test_extract_concepts_simple(self, concept_mapper):
        """Test extracting concepts from simple queries."""
        # Test single concept
        concepts = concept_mapper.extract_concepts("Show me insecure APIs")
        assert len(concepts) > 0
        assert any(concept == "insecure" for concept, _ in concepts)
        
        # Test multiple concepts
        concepts = concept_mapper.extract_concepts("Find active APIs with high risk")
        assert len(concepts) >= 2
        concept_names = [c for c, _ in concepts]
        assert "active" in concept_names
        assert "high risk" in concept_names
    
    def test_extract_concepts_with_negation(self, concept_mapper):
        """Test extracting concepts with negation detection."""
        # Test "not secure"
        concepts = concept_mapper.extract_concepts("Show me APIs that are not secure")
        secure_concepts = [(c, neg) for c, neg in concepts if c == "secure"]
        assert len(secure_concepts) > 0
        assert secure_concepts[0][1] is True  # Should be negated
        
        # Test "no active"
        concepts = concept_mapper.extract_concepts("Find APIs with no active status")
        active_concepts = [(c, neg) for c, neg in concepts if c == "active"]
        if active_concepts:
            assert active_concepts[0][1] is True
    
    def test_extract_concepts_multi_word(self, concept_mapper):
        """Test extracting multi-word concepts."""
        concepts = concept_mapper.extract_concepts("Show me APIs with high risk and low risk")
        concept_names = [c for c, _ in concepts]
        
        # Should match "high risk" and "low risk", not just "risk"
        assert "high risk" in concept_names
        assert "low risk" in concept_names
    
    def test_get_concepts_by_category(self, concept_mapper):
        """Test getting concepts by category."""
        # Test security category
        security_concepts = concept_mapper.get_concepts_by_category(ConceptCategory.SECURITY)
        assert len(security_concepts) > 0
        assert "secure" in security_concepts
        assert "insecure" in security_concepts
        
        # Test health category
        health_concepts = concept_mapper.get_concepts_by_category(ConceptCategory.HEALTH)
        assert len(health_concepts) > 0
        assert "healthy" in health_concepts
        assert "failing" in health_concepts
    
    def test_suggest_concepts(self, concept_mapper):
        """Test concept suggestions."""
        # Test partial match
        suggestions = concept_mapper.suggest_concepts("sec", limit=5)
        assert len(suggestions) <= 5
        assert any("secure" in s for s in suggestions)
        
        # Test another partial match
        suggestions = concept_mapper.suggest_concepts("risk", limit=3)
        assert len(suggestions) <= 3
        assert any("risk" in s for s in suggestions)
    
    def test_build_opensearch_clause_term(self, concept_mapper):
        """Test building OpenSearch term clause."""
        mapping = {"field": "status", "operator": "term", "value": "active"}
        clause = concept_mapper.build_opensearch_clause(mapping)
        
        assert "term" in clause
        assert clause["term"]["status"] == "active"
    
    def test_build_opensearch_clause_range(self, concept_mapper):
        """Test building OpenSearch range clause."""
        mapping = {
            "field": "intelligence_metadata.security_score",
            "operator": "gte",
            "value": 70
        }
        clause = concept_mapper.build_opensearch_clause(mapping)
        
        assert "range" in clause
        assert "intelligence_metadata.security_score" in clause["range"]
        assert clause["range"]["intelligence_metadata.security_score"]["gte"] == 70
    
    def test_build_opensearch_clause_range_dict(self, concept_mapper):
        """Test building OpenSearch range clause with dict value."""
        mapping = {
            "field": "intelligence_metadata.health_score",
            "operator": "range",
            "value": {"gte": 30, "lt": 70}
        }
        clause = concept_mapper.build_opensearch_clause(mapping)
        
        assert "range" in clause
        assert clause["range"]["intelligence_metadata.health_score"]["gte"] == 30
        assert clause["range"]["intelligence_metadata.health_score"]["lt"] == 70
    
    def test_build_opensearch_clause_must_not(self, concept_mapper):
        """Test building OpenSearch must_not clause."""
        mapping = {"field": "status", "operator": "must_not_term", "value": "active"}
        clause = concept_mapper.build_opensearch_clause(mapping)
        
        assert "bool" in clause
        assert "must_not" in clause["bool"]
        assert clause["bool"]["must_not"][0]["term"]["status"] == "active"
    
    def test_get_all_concepts(self, concept_mapper):
        """Test getting all concepts."""
        concepts = concept_mapper.get_all_concepts()
        
        assert isinstance(concepts, list)
        assert len(concepts) > 0
        assert "secure" in concepts
        assert "insecure" in concepts
        assert "healthy" in concepts
    
    def test_get_concept_info(self, concept_mapper):
        """Test getting concept information."""
        # Test existing concept
        info = concept_mapper.get_concept_info("secure")
        assert info is not None
        assert "field" in info
        assert "operator" in info
        assert "value" in info
        assert "category" in info
        
        # Test synonym
        info = concept_mapper.get_concept_info("unsafe")
        assert info is not None
        assert info["field"] == "intelligence_metadata.security_score"
        
        # Test unknown concept
        info = concept_mapper.get_concept_info("unknown_xyz")
        assert info is None
    
    def test_performance_concepts_require_join(self, concept_mapper):
        """Test that performance concepts are marked as requiring join."""
        # Test "slow" concept
        mapping = concept_mapper.map_concept("slow")
        assert mapping is not None
        assert mapping.get("requires_join") is True
        assert "join_index" in mapping
        
        # Test "fast" concept
        mapping = concept_mapper.map_concept("fast")
        assert mapping is not None
        assert mapping.get("requires_join") is True
    
    def test_shadow_api_concepts(self, concept_mapper):
        """Test shadow API concepts."""
        # Test "shadow" concept
        mapping = concept_mapper.map_concept("shadow")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.is_shadow"
        assert mapping["operator"] == "term"
        assert mapping["value"] is True
        
        # Test "undocumented" concept
        mapping = concept_mapper.map_concept("undocumented")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.is_shadow"
    
    def test_prediction_concepts(self, concept_mapper):
        """Test prediction-related concepts."""
        # Test "predicted to fail" concept
        mapping = concept_mapper.map_concept("predicted to fail")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.has_active_predictions"
        assert mapping["value"] is True
        
        # Test "at risk" concept
        mapping = concept_mapper.map_concept("at risk")
        assert mapping is not None
        assert mapping["field"] == "intelligence_metadata.has_active_predictions"

# Made with Bob
