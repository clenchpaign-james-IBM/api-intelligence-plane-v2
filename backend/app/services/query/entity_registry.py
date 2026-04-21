"""
Entity Registry for Natural Language Query Processing

Single source of truth for entity-to-index mapping, ensuring consistency
across all query service components.

Based on: docs/query-service-holistic-fix-analysis.md
"""

import logging
from typing import Dict, List, Optional, Set
from enum import Enum

logger = logging.getLogger(__name__)


class EntityType(str, Enum):
    """Supported entity types in the system."""
    
    API = "api"
    GATEWAY = "gateway"
    VULNERABILITY = "vulnerability"
    METRIC = "metric"
    PREDICTION = "prediction"
    RECOMMENDATION = "recommendation"
    COMPLIANCE = "compliance"
    TRANSACTION = "transaction"


class EntityConfig:
    """Configuration for an entity type."""
    
    def __init__(
        self,
        entity_type: str,
        index: str,
        id_field: str,
        aliases: List[str],
        filterable_fields: Dict[str, str],
        time_field: str = "created_at",
    ):
        self.entity_type = entity_type
        self.index = index
        self.id_field = id_field
        self.aliases = aliases
        self.filterable_fields = filterable_fields
        self.time_field = time_field


class EntityRegistry:
    """
    Single source of truth for entity-to-index mapping.
    
    Provides:
    - Consistent entity-to-index mapping
    - Entity alias resolution
    - Filterable field definitions
    - Time field mapping
    
    Used by:
    - IntentExtractor: Entity detection and resolution
    - QueryPlanner: Index selection
    - MultiIndexExecutor: Repository lookup
    - RelationshipGraph: Relationship definitions
    
    Example:
        >>> EntityRegistry.get_index("api")
        'api-inventory'
        >>> EntityRegistry.resolve_entity("security issue")
        'vulnerability'
        >>> EntityRegistry.get_filterable_fields("vulnerability")
        {'severity': 'keyword', 'status': 'keyword', ...}
    """
    
    # Entity configurations
    ENTITIES: Dict[str, EntityConfig] = {
        "api": EntityConfig(
            entity_type="api",
            index="api-inventory",
            id_field="id",
            aliases=["apis", "endpoint", "endpoints", "service", "services"],
            filterable_fields={
                "status": "keyword",
                "authentication_type": "keyword",
                "gateway_id": "keyword",
                "intelligence_metadata.is_shadow": "boolean",
                "intelligence_metadata.health_score": "float",
                "intelligence_metadata.risk_score": "float",
                "intelligence_metadata.security_score": "float",
                "intelligence_metadata.has_active_predictions": "boolean",
            },
            time_field="created_at",
        ),
        "gateway": EntityConfig(
            entity_type="gateway",
            index="gateway-registry",
            id_field="id",
            aliases=["gateways"],
            filterable_fields={
                "status": "keyword",
                "type": "keyword",
                "environment": "keyword",
            },
            time_field="created_at",
        ),
        "vulnerability": EntityConfig(
            entity_type="vulnerability",
            index="security-findings",
            id_field="id",
            aliases=[
                "vulnerabilities", "vuln", "vulns",
                "security issue", "security issues",
                "cve", "cves", "security finding", "security findings"
            ],
            filterable_fields={
                "severity": "keyword",
                "status": "keyword",
                "cve_id": "keyword",
                "cvss_score": "float",
            },
            time_field="detected_at",
        ),
        "metric": EntityConfig(
            entity_type="metric",
            index="api-metrics-5m",  # Default bucket
            id_field="id",
            aliases=["metrics", "measurement", "measurements", "performance"],
            filterable_fields={
                "gateway_id": "keyword",
                "api_id": "keyword",
                "time_bucket": "keyword",
                "error_rate": "float",
                "response_time_avg": "float",
                "response_time_p50": "float",
                "response_time_p95": "float",
                "response_time_p99": "float",
                "request_count": "long",
                "success_count": "long",
                "failure_count": "long",
                "throughput": "float",
            },
            time_field="timestamp",
        ),
        "prediction": EntityConfig(
            entity_type="prediction",
            index="api-predictions",  # Standardized name
            id_field="id",
            aliases=["predictions", "forecast", "forecasts"],
            filterable_fields={
                "gateway_id": "keyword",
                "api_id": "keyword",
                "prediction_type": "keyword",
                "confidence": "float",
                "severity": "keyword",
            },
            time_field="predicted_at",
        ),
        "recommendation": EntityConfig(
            entity_type="recommendation",
            index="optimization-recommendations",
            id_field="id",
            aliases=[
                "recommendations", "optimization", "optimizations",
                "suggestion", "suggestions", "rate limit", "rate limiting",
                "caching", "cache"
            ],
            filterable_fields={
                "gateway_id": "keyword",
                "api_id": "keyword",
                "recommendation_type": "keyword",
                "priority": "keyword",
                "status": "keyword",
            },
            time_field="created_at",
        ),
        "compliance": EntityConfig(
            entity_type="compliance",
            index="compliance-violations",
            id_field="id",
            aliases=["violation", "violations", "regulatory", "gdpr", "hipaa", "pci"],
            filterable_fields={
                "gateway_id": "keyword",
                "api_id": "keyword",
                "regulation": "keyword",
                "severity": "keyword",
                "status": "keyword",
            },
            time_field="detected_at",
        ),
        "transaction": EntityConfig(
            entity_type="transaction",
            index="transactional-logs",
            id_field="id",
            aliases=["transactions", "log", "logs", "request", "requests"],
            filterable_fields={
                "gateway_id": "keyword",
                "api_id": "keyword",
                "status_code": "integer",
                "method": "keyword",
                "response_time": "float",
            },
            time_field="timestamp",
        ),
    }
    
    # Reverse mapping: alias -> entity_type
    _ALIAS_MAP: Optional[Dict[str, str]] = None
    
    @classmethod
    def _build_alias_map(cls) -> Dict[str, str]:
        """Build reverse mapping from aliases to entity types."""
        if cls._ALIAS_MAP is not None:
            return cls._ALIAS_MAP
        
        alias_map = {}
        for entity_type, config in cls.ENTITIES.items():
            # Add entity type itself
            alias_map[entity_type] = entity_type
            # Add all aliases
            for alias in config.aliases:
                alias_map[alias.lower()] = entity_type
        
        cls._ALIAS_MAP = alias_map
        return alias_map
    
    @classmethod
    def get_index(cls, entity_type: str) -> Optional[str]:
        """
        Get index name for entity type.
        
        Args:
            entity_type: Entity type (e.g., "api", "vulnerability")
            
        Returns:
            Index name or None if entity type not found
        """
        config = cls.ENTITIES.get(entity_type)
        return config.index if config else None
    
    @classmethod
    def get_id_field(cls, entity_type: str) -> str:
        """
        Get ID field name for entity type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            ID field name (default: "id")
        """
        config = cls.ENTITIES.get(entity_type)
        return config.id_field if config else "id"
    
    @classmethod
    def get_time_field(cls, entity_type: str) -> str:
        """
        Get time field name for entity type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            Time field name (default: "created_at")
        """
        config = cls.ENTITIES.get(entity_type)
        return config.time_field if config else "created_at"
    
    @classmethod
    def get_filterable_fields(cls, entity_type: str) -> Dict[str, str]:
        """
        Get filterable fields for entity type.
        
        Args:
            entity_type: Entity type
            
        Returns:
            Dictionary of field name to field type
        """
        config = cls.ENTITIES.get(entity_type)
        return config.filterable_fields if config else {}
    
    @classmethod
    def resolve_entity(cls, text: str) -> Optional[str]:
        """
        Resolve text to entity type using aliases.
        
        Args:
            text: Text to resolve (e.g., "security issue", "APIs")
            
        Returns:
            Entity type or None if not found
        """
        alias_map = cls._build_alias_map()
        text_lower = text.lower().strip()
        
        # Direct lookup
        if text_lower in alias_map:
            return alias_map[text_lower]
        
        # Try singular/plural variations
        if text_lower.endswith('s'):
            singular = text_lower[:-1]
            if singular in alias_map:
                return alias_map[singular]
        else:
            plural = text_lower + 's'
            if plural in alias_map:
                return alias_map[plural]
        
        return None
    
    @classmethod
    def get_all_entity_types(cls) -> List[str]:
        """
        Get list of all entity types.
        
        Returns:
            List of entity type strings
        """
        return list(cls.ENTITIES.keys())
    
    @classmethod
    def get_all_indices(cls) -> List[str]:
        """
        Get list of all indices.
        
        Returns:
            List of index names
        """
        return [config.index for config in cls.ENTITIES.values()]
    
    @classmethod
    def get_entity_for_index(cls, index: str) -> Optional[str]:
        """
        Get entity type for an index name.
        
        Args:
            index: Index name
            
        Returns:
            Entity type or None if not found
        """
        # Handle wildcard patterns
        if '*' in index:
            index_prefix = index.replace('*', '')
            for entity_type, config in cls.ENTITIES.items():
                if config.index.startswith(index_prefix):
                    return entity_type
        else:
            for entity_type, config in cls.ENTITIES.items():
                if config.index == index:
                    return entity_type
        return None
    
    @classmethod
    def validate_filter_field(cls, entity_type: str, field: str) -> bool:
        """
        Check if field is filterable for entity type.
        
        Args:
            entity_type: Entity type
            field: Field name
            
        Returns:
            True if field is filterable, False otherwise
        """
        filterable_fields = cls.get_filterable_fields(entity_type)
        return field in filterable_fields
    
    @classmethod
    def get_field_type(cls, entity_type: str, field: str) -> Optional[str]:
        """
        Get field type for a filterable field.
        
        Args:
            entity_type: Entity type
            field: Field name
            
        Returns:
            Field type or None if field not found
        """
        filterable_fields = cls.get_filterable_fields(entity_type)
        return filterable_fields.get(field)


# Export for convenience
def get_index(entity_type: str) -> Optional[str]:
    """Get index name for entity type."""
    return EntityRegistry.get_index(entity_type)


def resolve_entity(text: str) -> Optional[str]:
    """Resolve text to entity type."""
    return EntityRegistry.resolve_entity(text)


# Made with Bob