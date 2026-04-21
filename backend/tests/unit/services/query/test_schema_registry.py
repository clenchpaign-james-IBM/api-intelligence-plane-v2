"""
Unit tests for SchemaRegistry

Tests schema loading, field validation, type checking, and context generation.
"""

import pytest
from unittest.mock import Mock, MagicMock
from app.services.query.schema_registry import SchemaRegistry, FieldType


@pytest.fixture
def mock_opensearch_client():
    """Create a mock OpenSearch client."""
    client = Mock()
    
    # Mock indices.get_mapping response
    client.indices.get_mapping.return_value = {
        "api-inventory": {
            "mappings": {
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "text"},
                    "status": {"type": "keyword"},
                    "intelligence_metadata": {
                        "type": "object",
                        "properties": {
                            "security_score": {"type": "float"},
                            "health_score": {"type": "float"},
                            "risk_score": {"type": "float"},
                            "is_shadow": {"type": "boolean"},
                        }
                    },
                    "policy_actions": {
                        "type": "nested",
                        "properties": {
                            "action_type": {"type": "keyword"},
                            "enabled": {"type": "boolean"},
                        }
                    }
                }
            }
        }
    }
    
    return client


@pytest.fixture
def schema_registry(mock_opensearch_client):
    """Create a SchemaRegistry instance with mock client."""
    registry = SchemaRegistry(mock_opensearch_client)
    return registry


class TestSchemaRegistry:
    """Test suite for SchemaRegistry."""
    
    def test_initialization(self, mock_opensearch_client):
        """Test SchemaRegistry initialization."""
        registry = SchemaRegistry(mock_opensearch_client)
        
        assert registry.client == mock_opensearch_client
        assert isinstance(registry.schemas, dict)
        assert isinstance(registry._field_cache, dict)
    
    @pytest.mark.asyncio
    async def test_load_schemas(self, schema_registry, mock_opensearch_client):
        """Test loading schemas from OpenSearch."""
        await schema_registry.load_schemas()
        
        # Verify schema was loaded
        assert "api-inventory" in schema_registry.schemas
        assert "fields" in schema_registry.schemas["api-inventory"]
        assert "nested" in schema_registry.schemas["api-inventory"]
        
        # Verify field cache was built
        assert "api-inventory" in schema_registry._field_cache
        assert len(schema_registry._field_cache["api-inventory"]) > 0
    
    @pytest.mark.asyncio
    async def test_load_schemas_with_error(self, schema_registry, mock_opensearch_client):
        """Test schema loading with OpenSearch error."""
        # Mock an error
        mock_opensearch_client.indices.get_mapping.side_effect = Exception("Connection error")
        
        # Should not raise, but load fallback schemas
        await schema_registry.load_schemas()
        
        # Verify fallback schemas were loaded
        assert len(schema_registry.schemas) > 0
        assert "api-inventory" in schema_registry.schemas
    
    def test_get_base_index_name(self, schema_registry):
        """Test extracting base index name from time-series indices."""
        # Test time-series index
        assert schema_registry._get_base_index_name("api-metrics-1m-2026-04-20") == "api-metrics-1m"
        assert schema_registry._get_base_index_name("api-metrics-5m-2026.04") == "api-metrics-5m"
        
        # Test regular index
        assert schema_registry._get_base_index_name("api-inventory") == "api-inventory"
    
    @pytest.mark.asyncio
    async def test_validate_field(self, schema_registry):
        """Test field validation."""
        await schema_registry.load_schemas()
        
        # Valid fields
        assert schema_registry.validate_field("api-inventory", "id") is True
        assert schema_registry.validate_field("api-inventory", "name") is True
        assert schema_registry.validate_field("api-inventory", "intelligence_metadata.security_score") is True
        
        # Invalid field
        assert schema_registry.validate_field("api-inventory", "nonexistent_field") is False
        
        # Invalid index
        assert schema_registry.validate_field("nonexistent-index", "id") is False
    
    @pytest.mark.asyncio
    async def test_get_field_type(self, schema_registry):
        """Test getting field type."""
        await schema_registry.load_schemas()
        
        # Test various field types
        assert schema_registry.get_field_type("api-inventory", "id") == "keyword"
        assert schema_registry.get_field_type("api-inventory", "name") == "text"
        assert schema_registry.get_field_type("api-inventory", "intelligence_metadata.security_score") == "float"
        assert schema_registry.get_field_type("api-inventory", "intelligence_metadata.is_shadow") == "boolean"
        
        # Nonexistent field
        assert schema_registry.get_field_type("api-inventory", "nonexistent") is None
    
    @pytest.mark.asyncio
    async def test_get_schema_context(self, schema_registry):
        """Test generating schema context for LLM prompts."""
        await schema_registry.load_schemas()
        
        context = schema_registry.get_schema_context("api-inventory")
        
        # Verify context contains key information
        assert "api-inventory" in context
        assert "Available Fields" in context
        assert "id" in context
        assert "keyword" in context
        assert "intelligence_metadata.security_score" in context
        assert "float" in context
    
    @pytest.mark.asyncio
    async def test_get_all_indices(self, schema_registry):
        """Test getting list of all loaded indices."""
        await schema_registry.load_schemas()
        
        indices = schema_registry.get_all_indices()
        
        assert isinstance(indices, list)
        assert "api-inventory" in indices
        assert len(indices) > 0
    
    @pytest.mark.asyncio
    async def test_get_field_suggestions(self, schema_registry):
        """Test getting field name suggestions."""
        await schema_registry.load_schemas()
        
        # Test partial match
        suggestions = schema_registry.get_field_suggestions("api-inventory", "secur", limit=5)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5
        # Should suggest security_score
        assert any("security" in s for s in suggestions)
    
    @pytest.mark.asyncio
    async def test_nested_field_extraction(self, schema_registry):
        """Test extraction of nested fields."""
        await schema_registry.load_schemas()
        
        # Verify nested fields are properly extracted
        assert schema_registry.validate_field("api-inventory", "intelligence_metadata.security_score")
        assert schema_registry.validate_field("api-inventory", "policy_actions.action_type")
        
        # Verify nested field is marked in schema
        assert "policy_actions" in schema_registry.schemas["api-inventory"]["nested"]
    
    def test_categorize_fields(self, schema_registry):
        """Test field categorization."""
        fields = {
            "id": {"type": "keyword"},
            "name": {"type": "text"},
            "intelligence_metadata.security_score": {"type": "float"},
            "response_time_avg": {"type": "float"},
            "created_at": {"type": "date"},
        }
        
        categorized = schema_registry._categorize_fields(fields)
        
        assert "Core Fields" in categorized
        assert "Intelligence Metadata" in categorized
        assert "Metrics" in categorized
        assert "Time Fields" in categorized
        
        # Verify categorization
        assert "id" in categorized["Core Fields"]
        assert "intelligence_metadata.security_score" in categorized["Intelligence Metadata"]
        assert "response_time_avg" in categorized["Metrics"]
        assert "created_at" in categorized["Time Fields"]
    
    @pytest.mark.asyncio
    async def test_fallback_schemas(self, schema_registry, mock_opensearch_client):
        """Test fallback schema loading when OpenSearch is unavailable."""
        # Force error to trigger fallback
        mock_opensearch_client.indices.get_mapping.side_effect = Exception("Connection failed")
        
        await schema_registry.load_schemas()
        
        # Verify fallback schemas were loaded
        assert "api-inventory" in schema_registry.schemas
        assert "api-metrics-1m" in schema_registry.schemas
        
        # Verify basic fields exist in fallback
        assert "id" in schema_registry.schemas["api-inventory"]["fields"]
        assert "intelligence_metadata.security_score" in schema_registry.schemas["api-inventory"]["fields"]
    
    @pytest.mark.asyncio
    async def test_time_series_index_handling(self, schema_registry, mock_opensearch_client):
        """Test handling of time-series indices with date suffixes."""
        # Mock response with time-series index
        mock_opensearch_client.indices.get_mapping.return_value = {
            "api-metrics-1m-2026.04": {
                "mappings": {
                    "properties": {
                        "timestamp": {"type": "date"},
                        "request_count": {"type": "long"},
                    }
                }
            }
        }
        
        await schema_registry.load_schemas()
        
        # Verify base index name is used
        assert "api-metrics-1m" in schema_registry.schemas
        
        # Verify validation works with full index name
        assert schema_registry.validate_field("api-metrics-1m-2026.04", "timestamp")
        assert schema_registry.validate_field("api-metrics-1m-2026.04", "request_count")

# Made with Bob
