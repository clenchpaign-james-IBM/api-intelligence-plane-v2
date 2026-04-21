"""
Unit tests for RelationshipGraph

Tests index relationship management, path finding, and join generation
for multi-index query orchestration.
"""

import pytest

from app.services.query.relationship_graph import (
    RelationshipGraph,
    RelationshipType,
    IndexRelationship,
    RelationshipPath,
)


class TestRelationshipGraph:
    """Test suite for RelationshipGraph."""
    
    @pytest.fixture
    def graph(self):
        """Create a RelationshipGraph instance for testing."""
        return RelationshipGraph()
    
    def test_initialization(self, graph):
        """Test that graph initializes with predefined relationships."""
        summary = graph.get_relationship_summary()
        
        assert summary["total_relationships"] > 0
        assert summary["total_indices"] > 0
        assert summary["indices_with_relationships"] > 0
    
    def test_get_relationships_gateway(self, graph):
        """Test getting relationships for gateway-registry."""
        relationships = graph.get_relationships("gateway-registry")
        
        assert len(relationships) > 0
        # Gateway should have relationship to api-inventory
        target_indices = {rel.target_index for rel in relationships}
        assert "api-inventory" in target_indices
    
    def test_get_relationships_api_inventory(self, graph):
        """Test getting relationships for api-inventory."""
        relationships = graph.get_relationships("api-inventory")
        
        assert len(relationships) > 0
        target_indices = {rel.target_index for rel in relationships}
        
        # API should have relationships to multiple indices
        assert "security-findings" in target_indices
        assert "predictions" in target_indices
        assert "optimization-recommendations" in target_indices
    
    def test_get_related_indices(self, graph):
        """Test getting all related indices for an index."""
        related = graph.get_related_indices("api-inventory")
        
        assert len(related) > 0
        assert "security-findings" in related
        assert "predictions" in related
    
    def test_get_join_fields(self, graph):
        """Test getting join fields between two indices."""
        join_fields = graph.get_join_fields("api-inventory", "security-findings")
        
        assert join_fields is not None
        assert "id" in join_fields
        assert join_fields["id"] == "api_id"
        assert "gateway_id" in join_fields
        assert join_fields["gateway_id"] == "gateway_id"
    
    def test_get_join_fields_nonexistent(self, graph):
        """Test getting join fields for non-existent relationship."""
        join_fields = graph.get_join_fields("predictions", "gateway-registry")
        
        # This relationship doesn't exist directly
        assert join_fields is None
    
    def test_has_relationship(self, graph):
        """Test checking if relationship exists."""
        # Direct relationship exists
        assert graph.has_relationship("api-inventory", "security-findings")
        
        # Reverse relationship exists (due to bidirectional setup)
        assert graph.has_relationship("security-findings", "api-inventory")
        
        # No direct relationship
        assert not graph.has_relationship("predictions", "gateway-registry")
    
    def test_find_path_direct(self, graph):
        """Test finding a direct path between two indices."""
        path = graph.find_path("api-inventory", "security-findings")
        
        assert path is not None
        assert path.start_index == "api-inventory"
        assert path.end_index == "security-findings"
        assert len(path.path) == 2
        assert path.path == ["api-inventory", "security-findings"]
        assert len(path.relationships) == 1
        assert len(path.join_conditions) == 1
    
    def test_find_path_multi_hop(self, graph):
        """Test finding a multi-hop path between indices."""
        path = graph.find_path("gateway-registry", "security-findings")
        
        assert path is not None
        assert path.start_index == "gateway-registry"
        assert path.end_index == "security-findings"
        assert len(path.path) >= 2
        # Path should go through api-inventory
        assert "api-inventory" in path.path
    
    def test_find_path_same_index(self, graph):
        """Test finding path when start and end are the same."""
        path = graph.find_path("api-inventory", "api-inventory")
        
        assert path is not None
        assert path.start_index == "api-inventory"
        assert path.end_index == "api-inventory"
        assert len(path.path) == 1
        assert len(path.relationships) == 0
    
    def test_find_path_max_hops(self, graph):
        """Test that path finding respects max_hops limit."""
        # Try to find path with very limited hops
        path = graph.find_path("gateway-registry", "compliance-violations", max_hops=1)
        
        # Should not find path with only 1 hop
        assert path is None
    
    def test_find_path_nonexistent(self, graph):
        """Test finding path when no path exists."""
        # Create a graph with isolated indices
        isolated_graph = RelationshipGraph()
        isolated_graph._relationships = []
        isolated_graph._index_map = {}
        
        path = isolated_graph.find_path("index-a", "index-b")
        assert path is None
    
    def test_add_relationship(self):
        """Test adding a custom relationship."""
        graph = RelationshipGraph()
        graph._relationships = []
        graph._index_map = {}
        
        graph.add_relationship(
            source_index="test-index-a",
            target_index="test-index-b",
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "ref_id"},
            description="Test relationship"
        )
        
        relationships = graph.get_relationships("test-index-a")
        assert len(relationships) == 1
        assert relationships[0].target_index == "test-index-b"
        assert relationships[0].join_fields == {"id": "ref_id"}
    
    def test_add_bidirectional_relationship(self):
        """Test adding a bidirectional relationship."""
        graph = RelationshipGraph()
        graph._relationships = []
        graph._index_map = {}
        
        graph.add_relationship(
            source_index="test-index-a",
            target_index="test-index-b",
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "ref_id"},
            description="Test relationship",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # Check forward relationship
        forward = graph.get_relationships("test-index-a")
        assert len(forward) == 1
        
        # Check reverse relationship
        reverse = graph.get_relationships("test-index-b")
        assert len(reverse) == 1
        assert reverse[0].target_index == "test-index-a"
        assert reverse[0].join_fields == {"ref_id": "id"}
    
    def test_get_all_indices(self, graph):
        """Test getting all indices in the graph."""
        indices = graph.get_all_indices()
        
        assert len(indices) > 0
        assert "gateway-registry" in indices
        assert "api-inventory" in indices
        assert "security-findings" in indices
        assert "predictions" in indices
    
    def test_validate_relationship(self, graph):
        """Test validating a relationship."""
        # Valid relationship
        is_valid = graph.validate_relationship(
            source_index="api-inventory",
            target_index="security-findings",
            join_fields={"id": "api_id", "gateway_id": "gateway_id"}
        )
        assert is_valid
        
        # Invalid join fields
        is_valid = graph.validate_relationship(
            source_index="api-inventory",
            target_index="security-findings",
            join_fields={"wrong_field": "api_id"}
        )
        assert not is_valid
        
        # Non-existent relationship
        is_valid = graph.validate_relationship(
            source_index="predictions",
            target_index="gateway-registry",
            join_fields={"id": "gateway_id"}
        )
        assert not is_valid
    
    def test_relationship_summary(self, graph):
        """Test getting relationship summary statistics."""
        summary = graph.get_relationship_summary()
        
        assert "total_relationships" in summary
        assert "total_indices" in summary
        assert "indices_with_relationships" in summary
        assert "relationship_types" in summary
        
        assert summary["total_relationships"] > 0
        assert summary["total_indices"] > 0
        
        # Check relationship type counts
        rel_types = summary["relationship_types"]
        assert isinstance(rel_types, dict)
        assert "one_to_many" in rel_types
        assert "many_to_one" in rel_types
    
    def test_wildcard_index_pattern(self, graph):
        """Test handling wildcard index patterns."""
        # api-metrics-* should match
        relationships = graph.get_relationships("api-metrics-*")
        
        # Should find relationships for the wildcard pattern
        assert len(relationships) > 0
    
    def test_path_join_conditions(self, graph):
        """Test that path includes correct join conditions."""
        path = graph.find_path("api-inventory", "security-findings")
        
        assert path is not None
        assert len(path.join_conditions) == len(path.relationships)
        
        # First join condition should map api-inventory to security-findings
        join_condition = path.join_conditions[0]
        assert "id" in join_condition
        assert join_condition["id"] == "api_id"
    
    def test_complex_path_finding(self, graph):
        """Test finding path through multiple hops."""
        # Find path from gateway to compliance violations
        # Should go: gateway -> api -> security-findings -> compliance
        path = graph.find_path("gateway-registry", "compliance-violations")
        
        assert path is not None
        assert len(path.path) >= 3
        assert path.path[0] == "gateway-registry"
        assert path.path[-1] == "compliance-violations"
    
    def test_relationship_types(self, graph):
        """Test that different relationship types are properly set."""
        relationships = graph.get_relationships("api-inventory")
        
        # Find one-to-many relationships
        one_to_many = [
            rel for rel in relationships
            if rel.relationship_type == RelationshipType.ONE_TO_MANY
        ]
        assert len(one_to_many) > 0
        
        # Check that security-findings relationship is one-to-many
        security_rel = next(
            (rel for rel in relationships if rel.target_index == "security-findings"),
            None
        )
        assert security_rel is not None
        assert security_rel.relationship_type == RelationshipType.ONE_TO_MANY
    
    def test_reverse_relationship_lookup(self, graph):
        """Test looking up reverse relationships."""
        # security-findings should have reverse relationship to api-inventory
        relationships = graph.get_relationships("security-findings")
        
        api_rel = next(
            (rel for rel in relationships if rel.target_index == "api-inventory"),
            None
        )
        
        assert api_rel is not None
        assert api_rel.relationship_type == RelationshipType.MANY_TO_ONE
    
    def test_multiple_join_fields(self, graph):
        """Test relationships with multiple join fields."""
        join_fields = graph.get_join_fields("api-inventory", "security-findings")
        
        assert join_fields is not None
        # Should have both api_id and gateway_id
        assert len(join_fields) >= 2
        assert "id" in join_fields
        assert "gateway_id" in join_fields
    
    def test_path_finding_efficiency(self, graph):
        """Test that path finding returns shortest path."""
        path = graph.find_path("gateway-registry", "predictions")
        
        assert path is not None
        # Should find shortest path (gateway -> api -> predictions)
        assert len(path.path) <= 3
    
    def test_no_circular_paths(self, graph):
        """Test that path finding doesn't create circular paths."""
        path = graph.find_path("api-inventory", "predictions")
        
        assert path is not None
        # Check no index appears twice in path
        assert len(path.path) == len(set(path.path))

# Made with Bob
