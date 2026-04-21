"""
Unit tests for QueryValidator

Tests query validation, field checking, operator validation, and error suggestions.
"""

import pytest
from unittest.mock import Mock
from app.services.query.validator import QueryValidator
from app.services.query.schema_registry import SchemaRegistry


@pytest.fixture
def mock_schema_registry():
    """Create a mock SchemaRegistry."""
    registry = Mock(spec=SchemaRegistry)
    
    # Mock valid fields
    valid_fields = {
        "id", "name", "status",
        "intelligence_metadata.security_score",
        "intelligence_metadata.health_score",
        "intelligence_metadata.risk_score",
        "response_time_avg", "error_rate"
    }
    
    registry.validate_field.side_effect = lambda index, field: field in valid_fields
    
    registry.get_field_type.side_effect = lambda index, field: {
        "id": "keyword",
        "name": "text",
        "status": "keyword",
        "intelligence_metadata.security_score": "float",
        "intelligence_metadata.health_score": "float",
        "intelligence_metadata.risk_score": "float",
        "response_time_avg": "float",
        "error_rate": "float",
    }.get(field)
    
    registry.get_field_suggestions.return_value = ["intelligence_metadata.security_score"]
    registry._get_base_index_name.side_effect = lambda x: x.split("-")[0] if "-" in x else x
    registry._field_cache = {"api-inventory": valid_fields}
    
    return registry


@pytest.fixture
def validator(mock_schema_registry):
    """Create a QueryValidator instance."""
    return QueryValidator(mock_schema_registry)


class TestQueryValidator:
    """Test suite for QueryValidator."""
    
    def test_initialization(self, mock_schema_registry):
        """Test QueryValidator initialization."""
        validator = QueryValidator(mock_schema_registry)
        assert validator.schema_registry == mock_schema_registry
    
    def test_validate_valid_query(self, validator):
        """Test validation of a valid query."""
        query = {
            "query": {
                "term": {
                    "status": "active"
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is True
        assert error is None
    
    def test_validate_missing_query_key(self, validator):
        """Test validation fails when query key is missing."""
        query = {
            "size": 10
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is False
        assert "Missing 'query' key" in error
    
    def test_validate_invalid_field(self, validator, mock_schema_registry):
        """Test validation fails for invalid field."""
        query = {
            "query": {
                "term": {
                    "nonexistent_field": "value"
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is False
        assert "Invalid field" in error
        assert "nonexistent_field" in error
    
    def test_validate_with_field_suggestion(self, validator, mock_schema_registry):
        """Test validation provides field suggestions."""
        query = {
            "query": {
                "term": {
                    "security_score": "value"
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is False
        assert "Did you mean" in error
    
    def test_validate_range_query(self, validator):
        """Test validation of range query."""
        query = {
            "query": {
                "range": {
                    "intelligence_metadata.security_score": {
                        "gte": 70
                    }
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is True
        assert error is None
    
    def test_validate_range_query_invalid_type(self, validator, mock_schema_registry):
        """Test validation fails for range query on non-numeric field."""
        # Mock status as keyword type
        query = {
            "query": {
                "range": {
                    "status": {
                        "gte": "active"
                    }
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is False
        assert "requires numeric or date type" in error
    
    def test_validate_bool_query(self, validator):
        """Test validation of bool query."""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": "active"}},
                        {"range": {"intelligence_metadata.security_score": {"gte": 70}}}
                    ]
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is True
        assert error is None
    
    def test_validate_bool_query_invalid_clause(self, validator):
        """Test validation fails for invalid bool clause."""
        query = {
            "query": {
                "bool": {
                    "invalid_clause": [
                        {"term": {"status": "active"}}
                    ]
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is False
        assert "Invalid bool clause" in error
    
    def test_validate_nested_query(self, validator):
        """Test validation of nested query structure."""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "bool": {
                                "should": [
                                    {"term": {"status": "active"}},
                                    {"term": {"status": "inactive"}}
                                ]
                            }
                        }
                    ]
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is True
        assert error is None
    
    def test_extract_fields_simple(self, validator):
        """Test extracting fields from simple query."""
        query = {
            "term": {
                "status": "active"
            }
        }
        
        fields = validator._extract_fields(query)
        assert "status" in fields
    
    def test_extract_fields_nested(self, validator):
        """Test extracting fields from nested query."""
        query = {
            "bool": {
                "must": [
                    {"term": {"status": "active"}},
                    {"range": {"intelligence_metadata.security_score": {"gte": 70}}}
                ]
            }
        }
        
        fields = validator._extract_fields(query)
        assert "status" in fields
        assert "intelligence_metadata.security_score" in fields
    
    def test_validate_operators(self, validator):
        """Test operator validation."""
        query = {
            "term": {"status": "active"},
            "range": {"intelligence_metadata.security_score": {"gte": 70}}
        }
        
        is_valid, error = validator._validate_operators(query)
        assert is_valid is True
        assert error is None
    
    def test_validate_bool_query_structure(self, validator):
        """Test bool query structure validation."""
        # Valid bool query
        bool_query = {
            "must": [{"term": {"status": "active"}}],
            "should": [{"term": {"status": "inactive"}}]
        }
        
        is_valid, error = validator._validate_bool_query(bool_query)
        assert is_valid is True
        assert error is None
        
        # Invalid bool query (not a dict)
        is_valid, error = validator._validate_bool_query("invalid")
        assert is_valid is False
        
        # Invalid bool query (clause not a list)
        bool_query = {
            "must": {"term": {"status": "active"}}
        }
        is_valid, error = validator._validate_bool_query(bool_query)
        assert is_valid is False
    
    def test_validate_range_queries(self, validator):
        """Test range query validation."""
        query = {
            "range": {
                "intelligence_metadata.security_score": {
                    "gte": 70,
                    "lte": 100
                }
            }
        }
        
        is_valid, error = validator._validate_range_queries(query, "api-inventory")
        assert is_valid is True
        assert error is None
    
    def test_validate_range_invalid_operator(self, validator):
        """Test range query with invalid operator."""
        query = {
            "range": {
                "intelligence_metadata.security_score": {
                    "invalid_op": 70
                }
            }
        }
        
        is_valid, error = validator._validate_range_queries(query, "api-inventory")
        assert is_valid is False
        assert "Invalid range operator" in error
    
    def test_suggest_field(self, validator, mock_schema_registry):
        """Test field suggestion."""
        suggestion = validator._suggest_field("security_score", "api-inventory")
        assert suggestion is not None
        assert "security" in suggestion.lower()
    
    def test_validate_and_suggest(self, validator):
        """Test validation with suggestions."""
        query = {
            "query": {
                "term": {
                    "invalid_field": "value"
                }
            }
        }
        
        result = validator.validate_and_suggest(query, "api-inventory")
        
        assert result["is_valid"] is False
        assert result["error"] is not None
        assert isinstance(result["suggestions"], list)
    
    def test_get_validation_report(self, validator):
        """Test getting detailed validation report."""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": "active"}},
                        {"range": {"intelligence_metadata.security_score": {"gte": 70}}}
                    ]
                }
            }
        }
        
        report = validator.get_validation_report(query, "api-inventory")
        
        assert "is_valid" in report
        assert "errors" in report
        assert "warnings" in report
        assert "field_count" in report
        assert "operator_count" in report
        assert report["field_count"] == 2
        assert report["operator_count"] > 0
    
    def test_get_validation_report_with_errors(self, validator):
        """Test validation report with errors."""
        query = {
            "query": {
                "term": {
                    "nonexistent_field": "value"
                }
            }
        }
        
        report = validator.get_validation_report(query, "api-inventory")
        
        assert report["is_valid"] is False
        assert len(report["errors"]) > 0
        assert any("Invalid field" in error for error in report["errors"])
    
    def test_count_operators(self, validator):
        """Test counting operators in query."""
        query = {
            "bool": {
                "must": [
                    {"term": {"status": "active"}},
                    {"range": {"intelligence_metadata.security_score": {"gte": 70}}}
                ]
            }
        }
        
        operators = validator._count_operators(query)
        
        assert "bool" in operators
        assert "term" in operators
        assert "range" in operators
        assert len(operators) == 3
    
    def test_validate_complex_query(self, validator):
        """Test validation of complex multi-level query."""
        query = {
            "query": {
                "bool": {
                    "must": [
                        {"term": {"status": "active"}},
                        {
                            "bool": {
                                "should": [
                                    {"range": {"intelligence_metadata.security_score": {"gte": 70}}},
                                    {"range": {"intelligence_metadata.health_score": {"gte": 80}}}
                                ]
                            }
                        }
                    ],
                    "must_not": [
                        {"term": {"status": "deprecated"}}
                    ]
                }
            }
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is True
        assert error is None
    
    def test_validate_query_not_dict(self, validator):
        """Test validation fails when query is not a dictionary."""
        query = "invalid query"
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is False
        assert "must be a dictionary" in error
    
    def test_validate_query_value_not_dict(self, validator):
        """Test validation fails when query value is not a dictionary."""
        query = {
            "query": "invalid"
        }
        
        is_valid, error = validator.validate(query, "api-inventory")
        assert is_valid is False
        assert "must be a dictionary" in error

# Made with Bob
