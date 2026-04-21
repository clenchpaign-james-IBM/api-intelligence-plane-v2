"""Enhanced Intent Model for Context-Aware Natural Language Query Processing.

Extends the base InterpretedIntent model with context tracking, reference detection,
entity resolution, and relationship identification capabilities.

Based on: docs/enterprise-nlq-multi-index-analysis.md Phase 2
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.query import InterpretedIntent, TimeRange


class ReferenceType(str, Enum):
    """Type of reference in a query.
    
    Attributes:
        DEMONSTRATIVE: References like "these", "those", "this", "that"
        PRONOUN: References like "them", "it", "they"
        IMPLICIT: Implicit references to previous context
        EXPLICIT: Explicit entity references by ID or name
        NONE: No reference detected
    """
    
    DEMONSTRATIVE = "demonstrative"
    PRONOUN = "pronoun"
    IMPLICIT = "implicit"
    EXPLICIT = "explicit"
    NONE = "none"


class EntityReference(BaseModel):
    """Represents a reference to entities from previous queries.
    
    Attributes:
        reference_type: Type of reference detected
        reference_text: Original text that triggered the reference
        entity_type: Type of entity being referenced (e.g., 'api', 'vulnerability')
        resolved_ids: List of resolved entity IDs from context
        confidence: Confidence score for the reference resolution (0-1)
    """
    
    reference_type: ReferenceType = Field(..., description="Type of reference")
    reference_text: str = Field(..., description="Original reference text")
    entity_type: str = Field(..., description="Type of entity referenced")
    resolved_ids: List[str] = Field(default_factory=list, description="Resolved entity IDs")
    confidence: float = Field(default=1.0, ge=0, le=1, description="Resolution confidence")


class EntityRelationship(BaseModel):
    """Represents a relationship between entities in the query.
    
    Attributes:
        source_entity: Source entity type (e.g., 'api')
        target_entity: Target entity type (e.g., 'vulnerability')
        relationship_type: Type of relationship (e.g., 'has', 'belongs_to')
        join_fields: Fields to use for joining (e.g., {'api_id': 'api_id'})
        description: Human-readable description of the relationship
    """
    
    source_entity: str = Field(..., description="Source entity type")
    target_entity: str = Field(..., description="Target entity type")
    relationship_type: str = Field(..., description="Relationship type")
    join_fields: Dict[str, str] = Field(..., description="Join field mapping")
    description: str = Field(..., description="Relationship description")


class ContextDependency(BaseModel):
    """Represents a dependency on previous query context.
    
    Attributes:
        depends_on_previous: Whether this query depends on previous queries
        required_entity_types: Entity types needed from previous context
        context_window: Number of previous queries to consider
        fallback_strategy: Strategy if context is not available
    """
    
    depends_on_previous: bool = Field(default=False, description="Depends on previous queries")
    required_entity_types: List[str] = Field(
        default_factory=list,
        description="Required entity types from context"
    )
    context_window: int = Field(default=1, ge=1, le=10, description="Number of previous queries")
    fallback_strategy: str = Field(
        default="error",
        description="Strategy when context unavailable: 'error', 'all', 'ask'"
    )


class EnhancedInterpretedIntent(InterpretedIntent):
    """Enhanced intent with context awareness and relationship tracking.
    
    Extends InterpretedIntent with:
    - Reference detection and resolution
    - Entity relationship identification
    - Context dependency tracking
    - Multi-index query support
    
    Attributes:
        references: List of detected entity references
        relationships: List of entity relationships in the query
        context_dependency: Context dependency information
        target_indices: List of target indices for multi-index queries
        requires_join: Whether query requires joining multiple indices
        previous_query_id: ID of the previous query in the session
        session_id: Session ID for context tracking
        resolved_entities: Entities resolved from context
    """
    
    references: List[EntityReference] = Field(
        default_factory=list,
        description="Detected entity references from previous queries"
    )
    relationships: List[EntityRelationship] = Field(
        default_factory=list,
        description="Entity relationships identified in the query"
    )
    context_dependency: ContextDependency = Field(
        default_factory=ContextDependency,
        description="Context dependency information"
    )
    target_indices: List[str] = Field(
        default_factory=list,
        description="Target OpenSearch indices for this query"
    )
    requires_join: bool = Field(
        default=False,
        description="Whether query requires joining multiple indices"
    )
    previous_query_id: Optional[UUID] = Field(
        None,
        description="ID of the previous query in the session"
    )
    session_id: Optional[UUID] = Field(
        None,
        description="Session ID for context tracking"
    )
    resolved_entities: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Entities resolved from context by type"
    )
    
    def has_references(self) -> bool:
        """Check if the intent contains any entity references.
        
        Returns:
            True if references are present, False otherwise
        """
        return len(self.references) > 0 and any(
            ref.reference_type != ReferenceType.NONE for ref in self.references
        )
    
    def has_relationships(self) -> bool:
        """Check if the intent contains entity relationships.
        
        Returns:
            True if relationships are present, False otherwise
        """
        return len(self.relationships) > 0
    
    def requires_context(self) -> bool:
        """Check if the intent requires previous query context.
        
        Returns:
            True if context is required, False otherwise
        """
        return self.context_dependency.depends_on_previous or self.has_references()
    
    def get_all_entity_types(self) -> Set[str]:
        """Get all entity types involved in this query.
        
        Includes entities from:
        - Base intent entities
        - References
        - Relationships
        
        Returns:
            Set of all entity types
        """
        entity_types = set(self.entities)
        
        # Add referenced entity types
        for ref in self.references:
            entity_types.add(ref.entity_type)
        
        # Add relationship entity types
        for rel in self.relationships:
            entity_types.add(rel.source_entity)
            entity_types.add(rel.target_entity)
        
        return entity_types
    
    def get_required_indices(self) -> List[str]:
        """Get list of required indices based on entities and relationships.
        
        Returns:
            List of index names required for this query
        """
        if self.target_indices:
            return self.target_indices
        
        # Map entities to indices (basic mapping)
        entity_to_index = {
            "api": "api-inventory",
            "gateway": "gateway-registry",
            "vulnerability": "security-findings",
            "metric": "api-metrics-*",
            "prediction": "predictions",
            "recommendation": "optimization-recommendations",
            "compliance": "compliance-violations",
            "transaction": "transactional-logs",
            "log": "transactional-logs",
        }
        
        indices = set()
        for entity_type in self.get_all_entity_types():
            if entity_type in entity_to_index:
                indices.add(entity_to_index[entity_type])
        
        return list(indices)
    
    class Config:
        """Pydantic model configuration."""
        
        json_schema_extra = {
            "example": {
                "action": "list",
                "entities": ["vulnerability"],
                "filters": {"severity": "critical"},
                "time_range": None,
                "references": [
                    {
                        "reference_type": "demonstrative",
                        "reference_text": "these APIs",
                        "entity_type": "api",
                        "resolved_ids": ["API-001", "API-002"],
                        "confidence": 0.95
                    }
                ],
                "relationships": [
                    {
                        "source_entity": "api",
                        "target_entity": "vulnerability",
                        "relationship_type": "has",
                        "join_fields": {"id": "api_id"},
                        "description": "API has vulnerabilities"
                    }
                ],
                "context_dependency": {
                    "depends_on_previous": True,
                    "required_entity_types": ["api"],
                    "context_window": 1,
                    "fallback_strategy": "error"
                },
                "target_indices": ["security-findings"],
                "requires_join": True,
                "previous_query_id": "550e8400-e29b-41d4-a716-446655440007",
                "session_id": "550e8400-e29b-41d4-a716-446655440008",
                "resolved_entities": {
                    "api_id": ["API-001", "API-002"]
                }
            }
        }


# Made with Bob