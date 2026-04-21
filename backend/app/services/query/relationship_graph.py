"""
Relationship Graph for Multi-Index Query Orchestration

Defines and manages relationships between OpenSearch indices, enabling
automatic join generation and multi-index query planning.

Based on: docs/enterprise-nlq-multi-index-analysis.md
Updated: 2026-04-21 - Integrated EntityRegistry for consistent index names
"""

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field
from app.services.query.entity_registry import EntityRegistry

logger = logging.getLogger(__name__)


class RelationshipType(str, Enum):
    """Type of relationship between indices.
    
    Attributes:
        ONE_TO_MANY: One entity in source index relates to many in target
        MANY_TO_ONE: Many entities in source index relate to one in target
        MANY_TO_MANY: Many-to-many relationship between indices
        ONE_TO_ONE: One-to-one relationship between indices
    """
    
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"
    ONE_TO_ONE = "one_to_one"


class IndexRelationship(BaseModel):
    """Defines a relationship between two indices.
    
    Attributes:
        source_index: Source index name
        target_index: Target index name
        relationship_type: Type of relationship
        join_fields: Mapping of source field to target field for joins
        description: Human-readable description of the relationship
        reverse_relationship: Optional reverse relationship type
    """
    
    source_index: str = Field(..., description="Source index name")
    target_index: str = Field(..., description="Target index name")
    relationship_type: RelationshipType = Field(..., description="Type of relationship")
    join_fields: Dict[str, str] = Field(
        ...,
        description="Mapping of source field to target field (e.g., {'api_id': 'api_id'})"
    )
    description: str = Field(..., description="Human-readable description")
    reverse_relationship: Optional[RelationshipType] = Field(
        None,
        description="Reverse relationship type (if bidirectional)"
    )


class RelationshipPath(BaseModel):
    """Represents a path between two indices through relationships.
    
    Attributes:
        start_index: Starting index
        end_index: Ending index
        path: List of index names in the path
        relationships: List of relationships traversed
        join_conditions: List of join conditions for each hop
    """
    
    start_index: str = Field(..., description="Starting index")
    end_index: str = Field(..., description="Ending index")
    path: List[str] = Field(..., description="List of indices in path")
    relationships: List[IndexRelationship] = Field(..., description="Relationships traversed")
    join_conditions: List[Dict[str, str]] = Field(..., description="Join conditions for each hop")


class RelationshipGraph:
    """Manages relationships between OpenSearch indices.
    
    Provides relationship definitions, path finding, and join generation
    for multi-index query orchestration.
    
    Features:
    - Predefined relationships for all system indices
    - Bidirectional relationship support
    - Path finding between any two indices
    - Join condition generation
    - Relationship validation
    
    Example:
        >>> graph = RelationshipGraph()
        >>> # Find path from api-inventory to security-findings
        >>> path = graph.find_path("api-inventory", "security-findings")
        >>> # Get direct relationships for an index
        >>> relationships = graph.get_relationships("api-inventory")
        >>> # Get join fields between two indices
        >>> join_fields = graph.get_join_fields("api-inventory", "security-findings")
    """
    
    def __init__(self):
        """Initialize the relationship graph with predefined relationships."""
        self._relationships: List[IndexRelationship] = []
        self._index_map: Dict[str, List[IndexRelationship]] = {}
        self._initialize_relationships()
        logger.info("RelationshipGraph initialized with system index relationships")
    
    def _initialize_relationships(self) -> None:
        """Initialize all system index relationships.
        
        Defines relationships based on the index relationship map from:
        docs/enterprise-nlq-multi-index-analysis.md
        """
        # Use EntityRegistry for consistent index names
        api_index = EntityRegistry.get_index("api")
        gateway_index = EntityRegistry.get_index("gateway")
        vulnerability_index = EntityRegistry.get_index("vulnerability")
        metric_index = EntityRegistry.get_index("metric")
        prediction_index = EntityRegistry.get_index("prediction")
        recommendation_index = EntityRegistry.get_index("recommendation")
        compliance_index = EntityRegistry.get_index("compliance")
        transaction_index = EntityRegistry.get_index("transaction")
        
        # Gateway → API relationships
        if gateway_index and api_index:
            self.add_relationship(
                source_index=gateway_index,
                target_index=api_index,
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "gateway_id"},
            description="Gateway manages multiple APIs",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # API → Security Findings relationships
        if api_index and vulnerability_index:
            self.add_relationship(
                source_index=api_index,
                target_index=vulnerability_index,
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "api_id", "gateway_id": "gateway_id"},
            description="API has multiple security vulnerabilities",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # API → Metrics relationships (use wildcard for time-bucketed indices)
        if api_index:
            self.add_relationship(
                source_index=api_index,
            target_index="api-metrics-*",
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "api_id", "gateway_id": "gateway_id"},
            description="API generates multiple metric records",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # API → Predictions relationships
        if api_index and prediction_index:
            self.add_relationship(
                source_index=api_index,
                target_index=prediction_index,
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "api_id", "gateway_id": "gateway_id"},
            description="API has multiple predictions",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # API → Optimization Recommendations relationships
        if api_index and recommendation_index:
            self.add_relationship(
                source_index=api_index,
                target_index=recommendation_index,
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "api_id", "gateway_id": "gateway_id"},
            description="API receives multiple optimization recommendations",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # API → Compliance Violations relationships
        if api_index and compliance_index:
            self.add_relationship(
                source_index=api_index,
                target_index=compliance_index,
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "api_id", "gateway_id": "gateway_id"},
            description="API has multiple compliance violations",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # API → Transactional Logs relationships
        if api_index and transaction_index:
            self.add_relationship(
                source_index=api_index,
                target_index=transaction_index,
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "api_id", "gateway_id": "gateway_id"},
            description="API generates multiple transaction logs",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # Security Findings → Compliance Violations relationships
        if vulnerability_index and compliance_index:
            self.add_relationship(
                source_index=vulnerability_index,
                target_index=compliance_index,
            relationship_type=RelationshipType.ONE_TO_MANY,
            join_fields={"id": "vulnerability_id", "api_id": "api_id"},
            description="Vulnerability links to compliance violations",
            reverse_relationship=RelationshipType.MANY_TO_ONE
        )
        
        # Metrics → Predictions relationships
        if prediction_index:
            self.add_relationship(
                source_index="api-metrics-*",
                target_index=prediction_index,
            relationship_type=RelationshipType.MANY_TO_ONE,
            join_fields={"api_id": "api_id", "gateway_id": "gateway_id"},
            description="Metrics are analyzed to generate predictions",
            reverse_relationship=RelationshipType.ONE_TO_MANY
        )
        
        # Gateway → All other indices (indirect through API)
        # These are implicit through the API relationship
        
        logger.info(f"Initialized {len(self._relationships)} index relationships")
    
    def add_relationship(
        self,
        source_index: str,
        target_index: str,
        relationship_type: RelationshipType,
        join_fields: Dict[str, str],
        description: str,
        reverse_relationship: Optional[RelationshipType] = None
    ) -> None:
        """Add a relationship between two indices.
        
        Args:
            source_index: Source index name
            target_index: Target index name
            relationship_type: Type of relationship
            join_fields: Mapping of source to target fields
            description: Human-readable description
            reverse_relationship: Optional reverse relationship type
        """
        relationship = IndexRelationship(
            source_index=source_index,
            target_index=target_index,
            relationship_type=relationship_type,
            join_fields=join_fields,
            description=description,
            reverse_relationship=reverse_relationship
        )
        
        self._relationships.append(relationship)
        
        # Add to index map for quick lookup
        if source_index not in self._index_map:
            self._index_map[source_index] = []
        self._index_map[source_index].append(relationship)
        
        # Add reverse relationship if specified
        if reverse_relationship:
            reverse_rel = IndexRelationship(
                source_index=target_index,
                target_index=source_index,
                relationship_type=reverse_relationship,
                join_fields={v: k for k, v in join_fields.items()},
                description=f"Reverse: {description}",
                reverse_relationship=relationship_type
            )
            self._relationships.append(reverse_rel)
            
            if target_index not in self._index_map:
                self._index_map[target_index] = []
            self._index_map[target_index].append(reverse_rel)
    
    def get_relationships(self, index_name: str) -> List[IndexRelationship]:
        """Get all relationships for a given index.
        
        Args:
            index_name: Index name
            
        Returns:
            List of relationships where index is the source
        """
        # Handle wildcard patterns (e.g., api-metrics-*)
        if '*' in index_name:
            pattern = index_name.replace('*', '')
            return [
                rel for idx, rels in self._index_map.items()
                if idx.startswith(pattern)
                for rel in rels
            ]
        
        return self._index_map.get(index_name, [])
    
    def get_related_indices(self, index_name: str) -> Set[str]:
        """Get all indices directly related to the given index.
        
        Args:
            index_name: Index name
            
        Returns:
            Set of related index names
        """
        relationships = self.get_relationships(index_name)
        return {rel.target_index for rel in relationships}
    
    def get_join_fields(
        self,
        source_index: str,
        target_index: str
    ) -> Optional[Dict[str, str]]:
        """Get join fields between two indices.
        
        Args:
            source_index: Source index name
            target_index: Target index name
            
        Returns:
            Dictionary mapping source fields to target fields, or None if no relationship
        """
        relationships = self.get_relationships(source_index)
        for rel in relationships:
            if rel.target_index == target_index:
                return rel.join_fields
        
        return None
    
    def has_relationship(self, source_index: str, target_index: str) -> bool:
        """Check if a direct relationship exists between two indices.
        
        Args:
            source_index: Source index name
            target_index: Target index name
            
        Returns:
            True if relationship exists, False otherwise
        """
        return self.get_join_fields(source_index, target_index) is not None
    
    def find_path(
        self,
        start_index: str,
        end_index: str,
        max_hops: int = 3
    ) -> Optional[RelationshipPath]:
        """Find a path between two indices using BFS.
        
        Args:
            start_index: Starting index
            end_index: Target index
            max_hops: Maximum number of hops allowed (default: 3)
            
        Returns:
            RelationshipPath if path found, None otherwise
        """
        if start_index == end_index:
            return RelationshipPath(
                start_index=start_index,
                end_index=end_index,
                path=[start_index],
                relationships=[],
                join_conditions=[]
            )
        
        # BFS to find shortest path
        queue: List[Tuple[str, List[str], List[IndexRelationship]]] = [
            (start_index, [start_index], [])
        ]
        visited: Set[str] = {start_index}
        
        while queue:
            current_index, path, relationships = queue.pop(0)
            
            # Check if we've exceeded max hops
            if len(path) > max_hops:
                continue
            
            # Get all relationships from current index
            current_relationships = self.get_relationships(current_index)
            
            for rel in current_relationships:
                target = rel.target_index
                
                # Handle wildcard patterns
                if '*' in target:
                    # For wildcard patterns, check if end_index matches
                    pattern = target.replace('*', '')
                    if not end_index.startswith(pattern):
                        continue
                    target = end_index
                
                if target == end_index:
                    # Found the target!
                    final_path = path + [target]
                    final_relationships = relationships + [rel]
                    join_conditions = [rel.join_fields for rel in final_relationships]
                    
                    return RelationshipPath(
                        start_index=start_index,
                        end_index=end_index,
                        path=final_path,
                        relationships=final_relationships,
                        join_conditions=join_conditions
                    )
                
                if target not in visited:
                    visited.add(target)
                    queue.append((target, path + [target], relationships + [rel]))
        
        logger.warning(f"No path found from {start_index} to {end_index}")
        return None
    
    def get_all_indices(self) -> Set[str]:
        """Get all indices in the relationship graph.
        
        Returns:
            Set of all index names
        """
        indices = set(self._index_map.keys())
        for relationships in self._index_map.values():
            for rel in relationships:
                indices.add(rel.target_index)
        return indices
    
    def validate_relationship(
        self,
        source_index: str,
        target_index: str,
        join_fields: Dict[str, str]
    ) -> bool:
        """Validate that a relationship exists with the given join fields.
        
        Args:
            source_index: Source index name
            target_index: Target index name
            join_fields: Expected join fields
            
        Returns:
            True if relationship is valid, False otherwise
        """
        actual_join_fields = self.get_join_fields(source_index, target_index)
        return actual_join_fields == join_fields
    
    def get_relationship_summary(self) -> Dict[str, Any]:
        """Get summary statistics about the relationship graph.
        
        Returns:
            Dictionary with summary statistics
        """
        return {
            "total_relationships": len(self._relationships),
            "total_indices": len(self.get_all_indices()),
            "indices_with_relationships": len(self._index_map),
            "relationship_types": {
                rel_type.value: sum(
                    1 for rel in self._relationships
                    if rel.relationship_type == rel_type
                )
                for rel_type in RelationshipType
            }
        }

# Made with Bob
