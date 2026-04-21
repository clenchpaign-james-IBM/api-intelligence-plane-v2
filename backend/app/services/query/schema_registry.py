"""
Schema Registry for OpenSearch Index Schemas

Maintains OpenSearch index schemas for query validation and context generation.
Provides field validation, type checking, and schema context for LLM prompts.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from enum import Enum

from opensearchpy import OpenSearch

logger = logging.getLogger(__name__)


class FieldType(str, Enum):
    """OpenSearch field types."""
    KEYWORD = "keyword"
    TEXT = "text"
    LONG = "long"
    INTEGER = "integer"
    FLOAT = "float"
    DOUBLE = "double"
    BOOLEAN = "boolean"
    DATE = "date"
    OBJECT = "object"
    NESTED = "nested"


class SchemaRegistry:
    """
    Maintains OpenSearch index schemas for query validation and context generation.
    
    Features:
    - Load schemas from OpenSearch mappings
    - Validate field existence and types
    - Generate schema context for LLM prompts
    - Support nested fields and arrays
    - Cache schema metadata
    
    Example:
        >>> registry = SchemaRegistry(client)
        >>> await registry.load_schemas()
        >>> is_valid = registry.validate_field("api-inventory", "intelligence_metadata.security_score")
        >>> field_type = registry.get_field_type("api-inventory", "status")
        >>> context = registry.get_schema_context("api-inventory")
    """
    
    def __init__(self, client: OpenSearch):
        """
        Initialize the schema registry.
        
        Args:
            client: OpenSearch client instance
        """
        self.client = client
        self.schemas: Dict[str, Dict[str, Any]] = {}
        self._field_cache: Dict[str, Set[str]] = {}
        
    async def load_schemas(self) -> None:
        """
        Load schemas from OpenSearch indices.
        
        Fetches mappings for all relevant indices and builds internal schema representation.
        """
        try:
            # Define indices to load (matching actual index names from init_indices.py)
            indices = [
                "api-inventory",
                "gateway-registry",
                "api-metrics-1m-*",
                "api-metrics-5m-*",
                "api-metrics-1h-*",
                "api-metrics-1d-*",
                "api-predictions",
                "security-findings",
                "optimization-recommendations",
                "query-history",
                "compliance-violations",
                "transactional-logs-*",
            ]
            
            for index_pattern in indices:
                try:
                    # Get mapping for index pattern
                    mappings = self.client.indices.get_mapping(index=index_pattern)
                    
                    # Process each index in the response
                    for index_name, index_data in mappings.items():
                        if "mappings" in index_data:
                            # Extract base index name (remove date suffix for time-series indices)
                            base_index = self._get_base_index_name(index_name)
                            
                            # Only process if not already loaded
                            if base_index not in self.schemas:
                                schema = self._build_schema(index_data["mappings"])
                                self.schemas[base_index] = schema
                                self._field_cache[base_index] = self._extract_all_fields(schema)
                                logger.info(f"Loaded schema for index: {base_index}")
                                
                except Exception as e:
                    logger.warning(f"Failed to load schema for {index_pattern}: {e}")
                    continue
                    
            logger.info(f"Loaded {len(self.schemas)} index schemas")
            
            # If no schemas were loaded, use fallback
            if len(self.schemas) == 0:
                logger.warning("No schemas loaded from OpenSearch, using fallback schemas")
                self._load_fallback_schemas()
            
        except Exception as e:
            logger.error(f"Failed to load schemas: {e}", exc_info=True)
            # Load fallback schemas
            self._load_fallback_schemas()
    
    def _get_base_index_name(self, index_name: str) -> str:
        """
        Extract base index name from time-series index.
        
        Args:
            index_name: Full index name (e.g., "api-metrics-1m-2026-04-20")
            
        Returns:
            Base index name (e.g., "api-metrics-1m")
        """
        # Handle time-series indices with date suffixes
        if "api-metrics-" in index_name:
            parts = index_name.split("-")
            if len(parts) >= 3:
                return f"{parts[0]}-{parts[1]}-{parts[2]}"
        return index_name
    
    def _build_schema(self, mappings: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build internal schema representation from OpenSearch mappings.
        
        Args:
            mappings: OpenSearch mappings dictionary
            
        Returns:
            Internal schema representation
        """
        schema: Dict[str, Any] = {
            "fields": {},
            "nested": [],
        }
        
        if "properties" in mappings:
            self._extract_fields(mappings["properties"], schema, prefix="")
            
        return schema
    
    def _extract_fields(
        self,
        properties: Dict[str, Any],
        schema: Dict[str, Any],
        prefix: str = ""
    ) -> None:
        """
        Recursively extract fields from OpenSearch properties.
        
        Args:
            properties: OpenSearch properties dictionary
            schema: Schema dictionary to populate
            prefix: Field name prefix for nested fields
        """
        for field_name, field_config in properties.items():
            full_field_name = f"{prefix}{field_name}" if prefix else field_name
            field_type = field_config.get("type", "object")
            
            # Store field metadata
            field_meta = {
                "type": field_type,
            }
            
            # Handle nested fields
            if field_type == "nested":
                schema["nested"].append(full_field_name)
                if "properties" in field_config:
                    self._extract_fields(
                        field_config["properties"],
                        schema,
                        prefix=f"{full_field_name}."
                    )
            
            # Handle object fields (nested properties)
            elif field_type == "object" or "properties" in field_config:
                if "properties" in field_config:
                    self._extract_fields(
                        field_config["properties"],
                        schema,
                        prefix=f"{full_field_name}."
                    )
            
            # Store field
            schema["fields"][full_field_name] = field_meta
    
    def _extract_all_fields(self, schema: Dict[str, Any]) -> Set[str]:
        """
        Extract all field names from schema for quick lookup.
        
        Args:
            schema: Schema dictionary
            
        Returns:
            Set of all field names
        """
        return set(schema["fields"].keys())
    
    def _load_fallback_schemas(self) -> None:
        """Load fallback schemas when OpenSearch is unavailable."""
        logger.info("Loading fallback schemas")
        
        # API Inventory schema
        self.schemas["api-inventory"] = {
            "fields": {
                "id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "name": {"type": "text"},
                "base_path": {"type": "keyword"},
                "status": {"type": "keyword"},
                "authentication_type": {"type": "keyword"},
                "intelligence_metadata.is_shadow": {"type": "boolean"},
                "intelligence_metadata.health_score": {"type": "float"},
                "intelligence_metadata.risk_score": {"type": "float"},
                "intelligence_metadata.security_score": {"type": "float"},
                "intelligence_metadata.has_active_predictions": {"type": "boolean"},
                "policy_actions.action_type": {"type": "keyword"},
                "policy_actions.enabled": {"type": "boolean"},
                "endpoints.path": {"type": "keyword"},
                "endpoints.method": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            },
            "nested": ["policy_actions", "endpoints"],
        }
        
        # Metrics schema
        metrics_schema = {
            "fields": {
                "id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "timestamp": {"type": "date"},
                "time_bucket": {"type": "keyword"},
                "request_count": {"type": "long"},
                "success_count": {"type": "long"},
                "failure_count": {"type": "long"},
                "error_rate": {"type": "float"},
                "response_time_avg": {"type": "float"},
                "response_time_p50": {"type": "float"},
                "response_time_p95": {"type": "float"},
                "response_time_p99": {"type": "float"},
                "throughput": {"type": "float"},
            },
            "nested": ["endpoint_metrics"],
        }
        
        for bucket in ["1m", "5m", "1h", "1d"]:
            self.schemas[f"api-metrics-{bucket}"] = metrics_schema.copy()
        
        # Gateway schema
        self.schemas["gateway-registry"] = {
            "fields": {
                "id": {"type": "keyword"},
                "name": {"type": "text"},
                "type": {"type": "keyword"},
                "status": {"type": "keyword"},
                "environment": {"type": "keyword"},
                "created_at": {"type": "date"},
                "updated_at": {"type": "date"},
            },
            "nested": [],
        }
        
        # Security findings schema
        self.schemas["security-findings"] = {
            "fields": {
                "id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "status": {"type": "keyword"},
                "cve_id": {"type": "keyword"},
                "cvss_score": {"type": "float"},
                "detected_at": {"type": "date"},
                "created_at": {"type": "date"},
            },
            "nested": [],
        }
        
        # Predictions schema
        self.schemas["api-predictions"] = {
            "fields": {
                "id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "prediction_type": {"type": "keyword"},
                "confidence": {"type": "float"},
                "severity": {"type": "keyword"},
                "predicted_at": {"type": "date"},
                "created_at": {"type": "date"},
            },
            "nested": [],
        }
        
        # Recommendations schema
        self.schemas["optimization-recommendations"] = {
            "fields": {
                "id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "recommendation_type": {"type": "keyword"},
                "priority": {"type": "keyword"},
                "status": {"type": "keyword"},
                "created_at": {"type": "date"},
            },
            "nested": [],
        }
        
        # Compliance violations schema
        self.schemas["compliance-violations"] = {
            "fields": {
                "id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "regulation": {"type": "keyword"},
                "severity": {"type": "keyword"},
                "status": {"type": "keyword"},
                "detected_at": {"type": "date"},
                "created_at": {"type": "date"},
            },
            "nested": [],
        }
        
        # Transactional logs schema
        self.schemas["transactional-logs"] = {
            "fields": {
                "id": {"type": "keyword"},
                "api_id": {"type": "keyword"},
                "gateway_id": {"type": "keyword"},
                "method": {"type": "keyword"},
                "status_code": {"type": "integer"},
                "response_time": {"type": "float"},
                "timestamp": {"type": "date"},
            },
            "nested": [],
        }
        
        # Build field caches
        for index, schema in self.schemas.items():
            self._field_cache[index] = self._extract_all_fields(schema)
    
    def validate_field(self, index: str, field: str) -> bool:
        """
        Check if field exists in schema.
        
        Args:
            index: Index name
            field: Field name (supports dot notation for nested fields)
            
        Returns:
            True if field exists, False otherwise
        """
        # Get base index name
        base_index = self._get_base_index_name(index)
        
        if base_index not in self._field_cache:
            return False
            
        return field in self._field_cache[base_index]
    
    def get_field_type(self, index: str, field: str) -> Optional[str]:
        """
        Get field data type.
        
        Args:
            index: Index name
            field: Field name
            
        Returns:
            Field type or None if field doesn't exist
        """
        base_index = self._get_base_index_name(index)
        
        if base_index not in self.schemas:
            return None
            
        schema = self.schemas[base_index]
        if field in schema["fields"]:
            field_type = schema["fields"][field].get("type")
            return field_type if isinstance(field_type, str) else None
            
        return None
    
    def get_schema_context(self, index: str) -> str:
        """
        Generate schema context for LLM prompts.
        
        Args:
            index: Index name
            
        Returns:
            Formatted schema context string
        """
        base_index = self._get_base_index_name(index)
        
        if base_index not in self.schemas:
            return f"Schema not found for index: {index}"
        
        schema = self.schemas[base_index]
        context = f"Index: {base_index}\n\nAvailable Fields:\n"
        
        # Group fields by category
        categorized_fields = self._categorize_fields(schema["fields"])
        
        for category, fields in categorized_fields.items():
            if fields:
                context += f"\n{category}:\n"
                for field, meta in sorted(fields.items()):
                    context += f"  - {field} ({meta['type']})\n"
        
        # Add nested fields info
        if schema["nested"]:
            context += f"\nNested Fields: {', '.join(schema['nested'])}\n"
        
        return context
    
    def _categorize_fields(self, fields: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """
        Categorize fields by prefix for better organization.
        
        Args:
            fields: Dictionary of fields
            
        Returns:
            Categorized fields dictionary
        """
        categories: Dict[str, Dict[str, Any]] = {
            "Core Fields": {},
            "Intelligence Metadata": {},
            "Metrics": {},
            "Time Fields": {},
            "Other": {},
        }
        
        for field, meta in fields.items():
            if field.startswith("intelligence_metadata."):
                categories["Intelligence Metadata"][field] = meta
            elif any(metric in field for metric in ["response_time", "request_count", "error_rate", "throughput"]):
                categories["Metrics"][field] = meta
            elif field in ["timestamp", "created_at", "updated_at"]:
                categories["Time Fields"][field] = meta
            elif field in ["id", "gateway_id", "api_id", "name", "status"]:
                categories["Core Fields"][field] = meta
            else:
                categories["Other"][field] = meta
        
        return categories
    
    def get_all_indices(self) -> List[str]:
        """
        Get list of all loaded indices.
        
        Returns:
            List of index names
        """
        return list(self.schemas.keys())
    
    def get_field_suggestions(self, index: str, partial_field: str, limit: int = 5) -> List[str]:
        """
        Get field name suggestions based on partial input.
        
        Args:
            index: Index name
            partial_field: Partial field name
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested field names
        """
        base_index = self._get_base_index_name(index)
        
        if base_index not in self._field_cache:
            return []
        
        partial_lower = partial_field.lower()
        suggestions = [
            field for field in self._field_cache[base_index]
            if partial_lower in field.lower()
        ]
        
        return sorted(suggestions)[:limit]

# Made with Bob
