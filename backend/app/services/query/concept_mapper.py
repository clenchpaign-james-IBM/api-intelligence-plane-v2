"""
Concept Mapper for Natural Language to Schema Field Mapping

Maps natural language concepts to OpenSearch schema fields and conditions.
Handles domain-specific terminology, synonyms, negations, and thresholds.
"""

import logging
import re
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class ConceptCategory(str, Enum):
    """Categories of domain concepts."""
    SECURITY = "security"
    HEALTH = "health"
    RISK = "risk"
    PERFORMANCE = "performance"
    STATUS = "status"
    COMPLIANCE = "compliance"
    PREDICTION = "prediction"


class ConceptMapper:
    """
    Maps natural language concepts to schema fields and conditions.
    
    Features:
    - Domain-specific concept mappings
    - Synonym handling
    - Negation support
    - Threshold definitions
    - Extensible mapping system
    
    Example:
        >>> mapper = ConceptMapper()
        >>> mapping = mapper.map_concept("insecure", negated=False)
        >>> # Returns: {"field": "intelligence_metadata.security_score", "operator": "lt", "value": 50}
        >>> 
        >>> mapping = mapper.map_concept("secure", negated=True)
        >>> # Returns: {"field": "intelligence_metadata.security_score", "operator": "lt", "value": 70}
    """
    
    # Concept mappings with field, operator, value, and optional negation handling
    CONCEPT_MAPPINGS: Dict[str, Dict[str, Any]] = {
        # Security concepts
        "secure": {
            "field": "intelligence_metadata.security_score",
            "operator": "gte",
            "value": 70,
            "category": ConceptCategory.SECURITY,
            "negation": {"operator": "lt", "value": 70}
        },
        "insecure": {
            "field": "intelligence_metadata.security_score",
            "operator": "lt",
            "value": 50,
            "category": ConceptCategory.SECURITY,
            "negation": {"operator": "gte", "value": 50}
        },
        "vulnerable": {
            "field": "intelligence_metadata.security_score",
            "operator": "lt",
            "value": 40,
            "category": ConceptCategory.SECURITY,
            "negation": {"operator": "gte", "value": 40}
        },
        "highly secure": {
            "field": "intelligence_metadata.security_score",
            "operator": "gte",
            "value": 85,
            "category": ConceptCategory.SECURITY,
        },
        
        # Health concepts
        "healthy": {
            "field": "intelligence_metadata.health_score",
            "operator": "gte",
            "value": 80,
            "category": ConceptCategory.HEALTH,
            "negation": {"operator": "lt", "value": 80}
        },
        "unhealthy": {
            "field": "intelligence_metadata.health_score",
            "operator": "lt",
            "value": 50,
            "category": ConceptCategory.HEALTH,
            "negation": {"operator": "gte", "value": 50}
        },
        "failing": {
            "field": "intelligence_metadata.health_score",
            "operator": "lt",
            "value": 30,
            "category": ConceptCategory.HEALTH,
            "negation": {"operator": "gte", "value": 30}
        },
        "degraded": {
            "field": "intelligence_metadata.health_score",
            "operator": "range",
            "value": {"gte": 30, "lt": 70},
            "category": ConceptCategory.HEALTH,
        },
        
        # Risk concepts
        "high risk": {
            "field": "intelligence_metadata.risk_score",
            "operator": "gte",
            "value": 70,
            "category": ConceptCategory.RISK,
            "negation": {"operator": "lt", "value": 70}
        },
        "medium risk": {
            "field": "intelligence_metadata.risk_score",
            "operator": "range",
            "value": {"gte": 40, "lt": 70},
            "category": ConceptCategory.RISK,
        },
        "low risk": {
            "field": "intelligence_metadata.risk_score",
            "operator": "lt",
            "value": 40,
            "category": ConceptCategory.RISK,
            "negation": {"operator": "gte", "value": 40}
        },
        "risky": {
            "field": "intelligence_metadata.risk_score",
            "operator": "gte",
            "value": 60,
            "category": ConceptCategory.RISK,
        },
        
        # Status concepts
        "active": {
            "field": "status",
            "operator": "term",
            "value": "active",
            "category": ConceptCategory.STATUS,
            "negation": {"operator": "must_not_term", "value": "active"}
        },
        "inactive": {
            "field": "status",
            "operator": "term",
            "value": "inactive",
            "category": ConceptCategory.STATUS,
            "negation": {"operator": "must_not_term", "value": "inactive"}
        },
        "deprecated": {
            "field": "status",
            "operator": "term",
            "value": "deprecated",
            "category": ConceptCategory.STATUS,
        },
        "failed": {
            "field": "status",
            "operator": "term",
            "value": "failed",
            "category": ConceptCategory.STATUS,
        },
        
        # Performance concepts (requires metrics join)
        "slow": {
            "field": "response_time_avg",
            "operator": "gte",
            "value": 1000,  # ms
            "category": ConceptCategory.PERFORMANCE,
            "requires_join": True,
            "join_index": "api-metrics-5m",
            "negation": {"operator": "lt", "value": 1000}
        },
        "fast": {
            "field": "response_time_avg",
            "operator": "lt",
            "value": 200,  # ms
            "category": ConceptCategory.PERFORMANCE,
            "requires_join": True,
            "join_index": "api-metrics-5m",
            "negation": {"operator": "gte", "value": 200}
        },
        "high latency": {
            "field": "response_time_p95",
            "operator": "gte",
            "value": 2000,  # ms
            "category": ConceptCategory.PERFORMANCE,
            "requires_join": True,
            "join_index": "api-metrics-5m",
        },
        "high error rate": {
            "field": "error_rate",
            "operator": "gte",
            "value": 0.05,  # 5%
            "category": ConceptCategory.PERFORMANCE,
            "requires_join": True,
            "join_index": "api-metrics-5m",
        },
        
        # Shadow API concepts
        "shadow": {
            "field": "intelligence_metadata.is_shadow",
            "operator": "term",
            "value": True,
            "category": ConceptCategory.SECURITY,
            "negation": {"operator": "term", "value": False}
        },
        "undocumented": {
            "field": "intelligence_metadata.is_shadow",
            "operator": "term",
            "value": True,
            "category": ConceptCategory.SECURITY,
        },
        
        # Prediction concepts
        "predicted to fail": {
            "field": "intelligence_metadata.has_active_predictions",
            "operator": "term",
            "value": True,
            "category": ConceptCategory.PREDICTION,
        },
        "at risk": {
            "field": "intelligence_metadata.has_active_predictions",
            "operator": "term",
            "value": True,
            "category": ConceptCategory.PREDICTION,
        },
    }
    
    # Synonyms for concepts
    SYNONYMS: Dict[str, str] = {
        "unsafe": "insecure",
        "not safe": "insecure",
        "weak": "insecure",
        "compromised": "vulnerable",
        "exposed": "vulnerable",
        "broken": "failing",
        "down": "failing",
        "unstable": "unhealthy",
        "problematic": "unhealthy",
        "dangerous": "high risk",
        "critical": "high risk",
        "enabled": "active",
        "running": "active",
        "disabled": "inactive",
        "stopped": "inactive",
        "sluggish": "slow",
        "laggy": "slow",
        "responsive": "fast",
        "quick": "fast",
        "hidden": "shadow",
        "rogue": "shadow",
        "unauthorized": "shadow",
    }
    
    def __init__(self):
        """Initialize the concept mapper."""
        self._negation_patterns = [
            r'\bnot\s+',
            r'\bno\s+',
            r'\bnon-',
            r'\bwithout\s+',
            r'\blacking\s+',
            r'\bmissing\s+',
        ]
        self._negation_regex = re.compile('|'.join(self._negation_patterns), re.IGNORECASE)
    
    def map_concept(self, concept: str, negated: bool = False) -> Optional[Dict[str, Any]]:
        """
        Map a concept to schema field and condition.
        
        Args:
            concept: Natural language concept (e.g., "secure", "slow")
            negated: Whether the concept is negated (e.g., "not secure")
            
        Returns:
            Mapping dictionary with field, operator, value, and metadata, or None if not found
        """
        concept_lower = concept.lower().strip()
        
        # Check for synonym
        if concept_lower in self.SYNONYMS:
            concept_lower = self.SYNONYMS[concept_lower]
        
        # Look up concept
        if concept_lower in self.CONCEPT_MAPPINGS:
            mapping = self.CONCEPT_MAPPINGS[concept_lower].copy()
            
            # Handle negation
            if negated and "negation" in mapping:
                negation_config = mapping.pop("negation")
                mapping.update(negation_config)
            
            return mapping
        
        return None
    
    def extract_concepts(self, query_text: str) -> List[Tuple[str, bool]]:
        """
        Extract concepts from query text with negation detection.
        
        Args:
            query_text: Natural language query
            
        Returns:
            List of (concept, is_negated) tuples
        """
        concepts = []
        query_lower = query_text.lower()
        
        # Sort concepts by length (longest first) to match multi-word concepts first
        sorted_concepts = sorted(
            list(self.CONCEPT_MAPPINGS.keys()) + list(self.SYNONYMS.keys()),
            key=len,
            reverse=True
        )
        
        for concept in sorted_concepts:
            # Check if concept appears in query
            pattern = r'\b' + re.escape(concept) + r'\b'
            matches = list(re.finditer(pattern, query_lower))
            
            for match in matches:
                # Check for negation before the concept
                start_pos = max(0, match.start() - 20)
                context = query_lower[start_pos:match.start()]
                is_negated = bool(self._negation_regex.search(context))
                
                concepts.append((concept, is_negated))
        
        return concepts
    
    def get_concepts_by_category(self, category: ConceptCategory) -> List[str]:
        """
        Get all concepts in a specific category.
        
        Args:
            category: Concept category
            
        Returns:
            List of concept names
        """
        return [
            concept for concept, mapping in self.CONCEPT_MAPPINGS.items()
            if mapping.get("category") == category
        ]
    
    def suggest_concepts(self, partial: str, limit: int = 5) -> List[str]:
        """
        Suggest concepts based on partial input.
        
        Args:
            partial: Partial concept name
            limit: Maximum number of suggestions
            
        Returns:
            List of suggested concept names
        """
        partial_lower = partial.lower()
        
        # Search in both concepts and synonyms
        all_terms = list(self.CONCEPT_MAPPINGS.keys()) + list(self.SYNONYMS.keys())
        
        suggestions = [
            term for term in all_terms
            if partial_lower in term.lower()
        ]
        
        return sorted(suggestions)[:limit]
    
    def build_opensearch_clause(self, mapping: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build OpenSearch query clause from concept mapping.
        
        Args:
            mapping: Concept mapping dictionary
            
        Returns:
            OpenSearch query clause
        """
        field = mapping["field"]
        operator = mapping["operator"]
        value = mapping["value"]
        
        if operator == "term":
            return {"term": {field: value}}
        
        elif operator == "must_not_term":
            return {"bool": {"must_not": [{"term": {field: value}}]}}
        
        elif operator in ["gte", "lte", "gt", "lt"]:
            return {"range": {field: {operator: value}}}
        
        elif operator == "range":
            return {"range": {field: value}}
        
        else:
            logger.warning(f"Unknown operator: {operator}")
            return {}
    
    def get_all_concepts(self) -> List[str]:
        """
        Get list of all available concepts.
        
        Returns:
            List of concept names
        """
        return list(self.CONCEPT_MAPPINGS.keys())
    
    def get_concept_info(self, concept: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed information about a concept.
        
        Args:
            concept: Concept name
            
        Returns:
            Concept information dictionary or None
        """
        concept_lower = concept.lower().strip()
        
        # Check for synonym
        if concept_lower in self.SYNONYMS:
            concept_lower = self.SYNONYMS[concept_lower]
        
        if concept_lower in self.CONCEPT_MAPPINGS:
            return self.CONCEPT_MAPPINGS[concept_lower].copy()
        
        return None

# Made with Bob
