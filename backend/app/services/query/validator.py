"""
Query Validator for OpenSearch DSL Validation

Validates OpenSearch queries before execution and provides error recovery.
Includes field validation, type checking, operator validation, and helpful error suggestions.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple, Set
from difflib import get_close_matches

from .schema_registry import SchemaRegistry

logger = logging.getLogger(__name__)


class QueryValidator:
    """
    Validates OpenSearch queries and provides error recovery.
    
    Features:
    - Field validation against schema
    - Type checking
    - Operator validation
    - Error suggestions with fuzzy matching
    - Nested query validation
    
    Example:
        >>> validator = QueryValidator(schema_registry)
        >>> is_valid, error = validator.validate(dsl_query, "api-inventory")
        >>> if not is_valid:
        ...     print(f"Validation error: {error}")
    """
    
    # Valid OpenSearch operators
    VALID_OPERATORS = {
        "term", "terms", "match", "match_phrase", "multi_match",
        "range", "exists", "prefix", "wildcard", "regexp",
        "fuzzy", "ids", "bool", "nested", "has_child", "has_parent"
    }
    
    # Valid range operators
    RANGE_OPERATORS = {"gte", "gt", "lte", "lt"}
    
    # Valid bool clauses
    BOOL_CLAUSES = {"must", "filter", "should", "must_not"}
    
    def __init__(self, schema_registry: SchemaRegistry):
        """
        Initialize the query validator.
        
        Args:
            schema_registry: Schema registry instance for field validation
        """
        self.schema_registry = schema_registry
    
    def validate(self, dsl: Dict[str, Any], index: str) -> Tuple[bool, Optional[str]]:
        """
        Validate DSL query against schema.
        
        Args:
            dsl: OpenSearch DSL query dictionary
            index: Target index name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Check basic structure
            if not isinstance(dsl, dict):
                return False, "Query must be a dictionary"
            
            if "query" not in dsl:
                return False, "Missing 'query' key in DSL"
            
            # Validate query structure
            query = dsl["query"]
            if not isinstance(query, dict):
                return False, "Query value must be a dictionary"
            
            # Validate bool query structure first (before field extraction)
            if "bool" in query:
                is_valid, error = self._validate_bool_query(query["bool"])
                if not is_valid:
                    return False, error
            
            # Validate operators
            is_valid, error = self._validate_operators(query)
            if not is_valid:
                return False, error
            
            # Validate nested queries
            is_valid, error = self._validate_nested_queries(query, index)
            if not is_valid:
                return False, error
            
            # Extract and validate fields (excluding nested query fields)
            fields = self._extract_fields(query, exclude_nested=True)
            for field in fields:
                # Skip validation for known operator keys
                if field in self.VALID_OPERATORS or field in self.BOOL_CLAUSES:
                    continue
                    
                if not self.schema_registry.validate_field(index, field):
                    suggestion = self._suggest_field(field, index)
                    if suggestion:
                        return False, f"Invalid field '{field}'. Did you mean '{suggestion}'?"
                    else:
                        return False, f"Invalid field '{field}'. Field does not exist in schema."
            
            # Validate range queries
            is_valid, error = self._validate_range_queries(query, index)
            if not is_valid:
                return False, error
            
            return True, None
            
        except Exception as e:
            logger.error(f"Validation error: {e}", exc_info=True)
            return False, f"Validation error: {str(e)}"
    
    def _extract_fields(self, query: Dict[str, Any], fields: Optional[Set[str]] = None, exclude_nested: bool = False) -> Set[str]:
        """
        Recursively extract all field references from query.
        
        Args:
            query: Query dictionary
            fields: Set to accumulate fields (used for recursion)
            exclude_nested: If True, skip fields inside nested queries
            
        Returns:
            Set of field names
        """
        if fields is None:
            fields = set()
        
        if not isinstance(query, dict):
            return fields
        
        for key, value in query.items():
            # Skip nested queries if exclude_nested is True
            if exclude_nested and key == "nested":
                continue
            
            # Skip operator keys
            if key in self.VALID_OPERATORS or key in self.BOOL_CLAUSES:
                if isinstance(value, dict):
                    self._extract_fields(value, fields, exclude_nested)
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            self._extract_fields(item, fields, exclude_nested)
            
            # Field reference found
            elif key not in ["query", "path", "score_mode", "boost", "_name"]:
                # This is likely a field name
                if isinstance(value, dict):
                    # Check if it's a field with operators
                    if any(op in value for op in self.RANGE_OPERATORS) or \
                       any(op in value for op in ["value", "values", "query"]):
                        fields.add(key)
                    else:
                        # Recurse into nested structure
                        self._extract_fields(value, fields, exclude_nested)
                else:
                    fields.add(key)
        
        return fields
    
    def _validate_operators(self, query: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate query operators.
        
        Args:
            query: Query dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(query, dict):
            return True, None
        
        for key, value in query.items():
            # Check if key is a valid operator
            if key in self.VALID_OPERATORS:
                # Recursively validate nested queries
                if isinstance(value, dict):
                    is_valid, error = self._validate_operators(value)
                    if not is_valid:
                        return False, error
                elif isinstance(value, list):
                    for item in value:
                        if isinstance(item, dict):
                            is_valid, error = self._validate_operators(item)
                            if not is_valid:
                                return False, error
            
            # Recursively check nested structures
            elif isinstance(value, dict):
                is_valid, error = self._validate_operators(value)
                if not is_valid:
                    return False, error
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        is_valid, error = self._validate_operators(item)
                        if not is_valid:
                            return False, error
        
        return True, None
    
    def _validate_bool_query(self, bool_query: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        Validate bool query structure.
        
        Args:
            bool_query: Bool query dictionary
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(bool_query, dict):
            return False, "Bool query must be a dictionary"
        
        # Check for valid bool clauses
        for key in bool_query.keys():
            if key not in self.BOOL_CLAUSES and key not in ["minimum_should_match", "boost"]:
                return False, f"Invalid bool clause '{key}'. Valid clauses: {', '.join(self.BOOL_CLAUSES)}"
        
        # Validate each clause contains valid queries
        for clause in self.BOOL_CLAUSES:
            if clause in bool_query:
                clause_value = bool_query[clause]
                if not isinstance(clause_value, list):
                    return False, f"Bool clause '{clause}' must be a list"
                
                for query in clause_value:
                    if not isinstance(query, dict):
                        return False, f"Each query in '{clause}' must be a dictionary"
        
        return True, None
    
    def _validate_range_queries(self, query: Dict[str, Any], index: str) -> Tuple[bool, Optional[str]]:
        """
        Validate range queries have appropriate field types.
        
        Args:
            query: Query dictionary
            index: Target index name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(query, dict):
            return True, None
        
        # Check for range queries
        if "range" in query:
            range_query = query["range"]
            if isinstance(range_query, dict):
                for field, conditions in range_query.items():
                    # Get field type
                    field_type = self.schema_registry.get_field_type(index, field)
                    
                    if field_type and field_type not in ["long", "integer", "float", "double", "date"]:
                        return False, f"Range query on field '{field}' requires numeric or date type, got '{field_type}'"
                    
                    # Validate range operators
                    if isinstance(conditions, dict):
                        for op in conditions.keys():
                            if op not in self.RANGE_OPERATORS:
                                return False, f"Invalid range operator '{op}'. Valid operators: {', '.join(self.RANGE_OPERATORS)}"
        
        # Recursively check nested queries
        for key, value in query.items():
            if isinstance(value, dict):
                is_valid, error = self._validate_range_queries(value, index)
                if not is_valid:
                    return False, error
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        is_valid, error = self._validate_range_queries(item, index)
                        if not is_valid:
                            return False, error
        
        return True, None
    
    def _validate_nested_queries(self, query: Dict[str, Any], index: str) -> Tuple[bool, Optional[str]]:
        """
        Validate nested queries structure.
        
        Args:
            query: Query dictionary
            index: Target index name
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(query, dict):
            return True, None
        
        # Check for nested queries
        if "nested" in query:
            nested_query = query["nested"]
            if not isinstance(nested_query, dict):
                return False, "Nested query must be a dictionary"
            
            # Validate path field
            if "path" not in nested_query:
                return False, "Nested query must have 'path' field"
            
            path = nested_query["path"]
            
            # Get schema for index
            base_index = self.schema_registry._get_base_index_name(index)
            if base_index in self.schema_registry.schemas:
                schema = self.schema_registry.schemas[base_index]
                nested_fields = schema.get("nested", [])
                
                # Validate that path is a nested field
                if path not in nested_fields:
                    return False, f"Field '{path}' is not configured as nested type in schema"
            
            # Validate nested query structure
            if "query" not in nested_query:
                return False, "Nested query must have 'query' field"
        
        # Recursively check nested structures
        for key, value in query.items():
            if isinstance(value, dict):
                is_valid, error = self._validate_nested_queries(value, index)
                if not is_valid:
                    return False, error
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        is_valid, error = self._validate_nested_queries(item, index)
                        if not is_valid:
                            return False, error
        
        return True, None
    
    def _suggest_field(self, invalid_field: str, index: str) -> Optional[str]:
        """
        Suggest correct field name using fuzzy matching.
        
        Args:
            invalid_field: Invalid field name
            index: Target index name
            
        Returns:
            Suggested field name or None
        """
        # Try using schema registry's suggestion method first
        suggestions = self.schema_registry.get_field_suggestions(index, invalid_field, limit=1)
        if suggestions:
            return suggestions[0]
        
        # Fallback to direct fuzzy matching
        base_index = self.schema_registry._get_base_index_name(index)
        
        if base_index not in self.schema_registry._field_cache:
            return None
        
        valid_fields = list(self.schema_registry._field_cache[base_index])
        
        # Use fuzzy matching to find similar fields
        matches = get_close_matches(invalid_field, valid_fields, n=1, cutoff=0.6)
        
        return matches[0] if matches else None
    
    def validate_and_suggest(self, dsl: Dict[str, Any], index: str) -> Dict[str, Any]:
        """
        Validate query and provide detailed feedback with suggestions.
        
        Args:
            dsl: OpenSearch DSL query dictionary
            index: Target index name
            
        Returns:
            Dictionary with validation results and suggestions
        """
        is_valid, error = self.validate(dsl, index)
        
        result: Dict[str, Any] = {
            "is_valid": is_valid,
            "error": error,
            "suggestions": []
        }
        
        if not is_valid and error:
            # Extract field name from error if present
            if "Invalid field" in error:
                # Try to extract field name and provide additional suggestions
                fields = self._extract_fields(dsl.get("query", {}))
                for field in fields:
                    if not self.schema_registry.validate_field(index, field):
                        suggestions = self.schema_registry.get_field_suggestions(index, field, limit=3)
                        if suggestions and isinstance(result["suggestions"], list):
                            result["suggestions"].extend(suggestions)
        
        return result
    
    def get_validation_report(self, dsl: Dict[str, Any], index: str) -> Dict[str, Any]:
        """
        Get detailed validation report with all issues and suggestions.
        
        Args:
            dsl: OpenSearch DSL query dictionary
            index: Target index name
            
        Returns:
            Detailed validation report
        """
        report = {
            "is_valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": {},
            "field_count": 0,
            "operator_count": 0,
        }
        
        try:
            # Extract fields
            fields = self._extract_fields(dsl.get("query", {}))
            report["field_count"] = len(fields)
            
            # Validate each field
            for field in fields:
                if not self.schema_registry.validate_field(index, field):
                    report["is_valid"] = False
                    if isinstance(report["errors"], list):
                        report["errors"].append(f"Invalid field: {field}")
                    
                    # Get suggestions
                    suggestions = self.schema_registry.get_field_suggestions(index, field, limit=3)
                    if suggestions and isinstance(report["suggestions"], dict):
                        report["suggestions"][field] = suggestions
            
            # Count operators
            operators = self._count_operators(dsl.get("query", {}))
            report["operator_count"] = len(operators)
            
            # Validate structure
            is_valid, error = self.validate(dsl, index)
            if not is_valid and error:
                if isinstance(report["errors"], list) and error not in report["errors"]:
                    report["errors"].append(error)
                    report["is_valid"] = False
            
        except Exception as e:
            report["is_valid"] = False
            if isinstance(report["errors"], list):
                report["errors"].append(f"Validation exception: {str(e)}")
        
        return report
    
    def _count_operators(self, query: Dict[str, Any], operators: Optional[Set[str]] = None) -> Set[str]:
        """
        Count unique operators in query.
        
        Args:
            query: Query dictionary
            operators: Set to accumulate operators
            
        Returns:
            Set of operator names
        """
        if operators is None:
            operators = set()
        
        if not isinstance(query, dict):
            return operators
        
        for key, value in query.items():
            if key in self.VALID_OPERATORS:
                operators.add(key)
            
            if isinstance(value, dict):
                self._count_operators(value, operators)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._count_operators(item, operators)
        
        return operators

# Made with Bob
