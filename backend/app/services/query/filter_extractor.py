"""
Filter Extractor for Natural Language Query Processing

Extracts structured filters from natural language queries with improved
accuracy using examples and field validation.

Based on: docs/query-service-holistic-fix-analysis.md
"""

import logging
import re
from typing import Any, Dict, List, Optional

from app.services.query.entity_registry import EntityRegistry

logger = logging.getLogger(__name__)


class FilterExtractor:
    """
    Extract structured filters from natural language queries.
    
    Features:
    - Keyword-based filter detection
    - Numeric range extraction
    - Status/severity mapping
    - Field validation against entity schemas
    - Common filter patterns
    
    Example:
        >>> extractor = FilterExtractor()
        >>> filters = extractor.extract("Show critical vulnerabilities")
        {'severity': 'critical'}
        >>> filters = extractor.extract("APIs with error rate above 5%")
        {'error_rate': {'gte': 0.05}}
    """
    
    # Common filter keywords and their mappings
    FILTER_KEYWORDS = {
        # Severity levels
        'critical': {'severity': 'critical'},
        'high': {'severity': 'high'},
        'medium': {'severity': 'medium'},
        'low': {'severity': 'low'},
        
        # Status values
        'active': {'status': 'active'},
        'inactive': {'status': 'inactive'},
        'deprecated': {'status': 'deprecated'},
        'offline': {'status': 'offline'},
        'online': {'status': 'online'},
        'pending': {'status': 'pending'},
        'resolved': {'status': 'resolved'},
        'open': {'status': 'open'},
        'closed': {'status': 'closed'},
        
        # Priority levels
        'high priority': {'priority': 'high'},
        'medium priority': {'priority': 'medium'},
        'low priority': {'priority': 'low'},
        
        # Environment
        'production': {'environment': 'production'},
        'staging': {'environment': 'staging'},
        'development': {'environment': 'development'},
        
        # Boolean flags
        'shadow': {'intelligence_metadata.is_shadow': True},
        'insecure': {'intelligence_metadata.security_score': {'lt': 0.5}},
        'vulnerable': {'intelligence_metadata.security_score': {'lt': 0.5}},
        'unhealthy': {'intelligence_metadata.health_score': {'lt': 0.5}},
        
        # Compliance
        'gdpr': {'regulation': 'GDPR'},
        'hipaa': {'regulation': 'HIPAA'},
        'pci': {'regulation': 'PCI'},
        'pci-dss': {'regulation': 'PCI-DSS'},
        'sox': {'regulation': 'SOX'},
        
        # Recommendation types
        'rate limiting': {'recommendation_type': 'rate_limiting'},
        'caching': {'recommendation_type': 'caching'},
        'circuit breaker': {'recommendation_type': 'circuit_breaker'},
        'retry': {'recommendation_type': 'retry'},
        
        # Prediction types
        'failure': {'prediction_type': 'failure'},
        'performance': {'prediction_type': 'performance'},
        'traffic': {'prediction_type': 'traffic'},
    }
    
    # Numeric comparison patterns
    NUMERIC_PATTERNS = [
        # Greater than
        (r'(?:above|over|greater than|more than|>)\s+(\d+(?:\.\d+)?)\s*(%)?',
         lambda m: {'gte': float(m.group(1)) / (100 if m.group(2) else 1)}),
        
        # Less than
        (r'(?:below|under|less than|fewer than|<)\s+(\d+(?:\.\d+)?)\s*(%)?',
         lambda m: {'lte': float(m.group(1)) / (100 if m.group(2) else 1)}),
        
        # Between
        (r'between\s+(\d+(?:\.\d+)?)\s+and\s+(\d+(?:\.\d+)?)',
         lambda m: {'gte': float(m.group(1)), 'lte': float(m.group(2))}),
        
        # Equals
        (r'(?:equals?|is|=)\s+(\d+(?:\.\d+)?)\s*(%)?',
         lambda m: float(m.group(1)) / (100 if m.group(2) else 1)),
    ]
    
    # Field name patterns for numeric filters
    NUMERIC_FIELD_PATTERNS = {
        r'error\s+rate': 'error_rate',
        r'response\s+time': 'response_time_avg',
        r'latency': 'response_time_avg',
        r'throughput': 'throughput',
        r'confidence': 'confidence',
        r'score': 'score',  # Generic, will be refined by context
        r'cvss': 'cvss_score',
    }
    
    @classmethod
    def extract(
        cls,
        query_text: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract filters from query text.
        
        Args:
            query_text: Natural language query text
            entity_types: Optional list of entity types for context
            
        Returns:
            Dictionary of filters
        """
        filters = {}
        query_lower = query_text.lower()
        
        # Extract keyword-based filters
        keyword_filters = cls._extract_keyword_filters(query_lower)
        filters.update(keyword_filters)
        
        # Extract numeric filters
        numeric_filters = cls._extract_numeric_filters(query_lower, entity_types)
        filters.update(numeric_filters)
        
        # Extract UUID filters
        uuid_filters = cls._extract_uuid_filters(query_text)
        filters.update(uuid_filters)
        
        # Validate filters against entity schemas
        if entity_types:
            filters = cls._validate_filters(filters, entity_types)
        
        logger.info(f"Extracted filters: {filters}")
        return filters
    
    @classmethod
    def _extract_keyword_filters(cls, query_text: str) -> Dict[str, Any]:
        """
        Extract filters based on keyword matching.
        
        Args:
            query_text: Query text (lowercase)
            
        Returns:
            Dictionary of filters
        """
        filters: Dict[str, Any] = {}
        
        # Check for each keyword (longest first to avoid partial matches)
        sorted_keywords = sorted(cls.FILTER_KEYWORDS.keys(), key=len, reverse=True)
        
        for keyword in sorted_keywords:
            if keyword in query_text:
                filter_dict = cls.FILTER_KEYWORDS[keyword]
                if isinstance(filter_dict, dict):
                    filters.update(filter_dict)
                    logger.debug(f"Matched keyword '{keyword}' -> {filter_dict}")
        
        return filters
    
    @classmethod
    def _extract_numeric_filters(
        cls,
        query_text: str,
        entity_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Extract numeric comparison filters.
        
        Args:
            query_text: Query text (lowercase)
            entity_types: Optional entity types for field context
            
        Returns:
            Dictionary of numeric filters
        """
        filters: Dict[str, Any] = {}
        
        # Find field name
        field_name = None
        for pattern, field in cls.NUMERIC_FIELD_PATTERNS.items():
            if re.search(pattern, query_text):
                field_name = field
                break
        
        # If no field found, try to infer from entity type
        if not field_name and entity_types:
            if 'vulnerability' in entity_types:
                field_name = 'cvss_score'
            elif 'metric' in entity_types:
                field_name = 'error_rate'
            elif 'prediction' in entity_types:
                field_name = 'confidence'
        
        if not field_name:
            return filters
        
        # Extract numeric comparison
        for pattern, value_func in cls.NUMERIC_PATTERNS:
            match = re.search(pattern, query_text)
            if match:
                try:
                    value = value_func(match)
                    filters[field_name] = value
                    logger.debug(f"Extracted numeric filter: {field_name} = {value}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to extract numeric value: {e}")
        
        return filters
    
    @classmethod
    def _extract_uuid_filters(cls, query_text: str) -> Dict[str, Any]:
        """
        Extract UUID filters from query text.
        
        Args:
            query_text: Query text
            
        Returns:
            Dictionary of UUID filters
        """
        filters = {}
        
        # UUID pattern
        uuid_pattern = r'\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b'
        uuids = re.findall(uuid_pattern, query_text, re.IGNORECASE)
        
        if uuids:
            # Try to determine which field the UUID belongs to
            query_lower = query_text.lower()
            
            for uuid in uuids:
                # Find context around UUID
                uuid_pos = query_lower.find(uuid.lower())
                context_before = query_lower[max(0, uuid_pos - 50):uuid_pos]
                
                # Determine field based on context
                if any(word in context_before for word in ['gateway', 'gw']):
                    filters['gateway_id'] = uuid
                elif any(word in context_before for word in ['api', 'endpoint']):
                    filters['api_id'] = uuid
                else:
                    # Default to api_id if ambiguous
                    filters['api_id'] = uuid
                
                logger.debug(f"Extracted UUID filter: {filters}")
        
        return filters
    
    @classmethod
    def _validate_filters(
        cls,
        filters: Dict[str, Any],
        entity_types: List[str]
    ) -> Dict[str, Any]:
        """
        Validate filters against entity schemas.
        
        Args:
            filters: Extracted filters
            entity_types: Entity types for validation
            
        Returns:
            Validated filters (invalid ones removed)
        """
        validated = {}
        
        for field, value in filters.items():
            # Check if field is valid for any of the entity types
            is_valid = False
            for entity_type in entity_types:
                if EntityRegistry.validate_filter_field(entity_type, field):
                    is_valid = True
                    break
            
            if is_valid:
                validated[field] = value
            else:
                logger.warning(f"Filter field '{field}' not valid for entities {entity_types}")
        
        return validated
    
    @classmethod
    def get_filter_examples(cls) -> str:
        """
        Get filter extraction examples for LLM prompts.
        
        Returns:
            Formatted examples string
        """
        return """
Filter Extraction Examples:

Query: "Show critical vulnerabilities"
Filters: {"severity": "critical"}

Query: "List active APIs"
Filters: {"status": "active"}

Query: "APIs with error rate above 5%"
Filters: {"error_rate": {"gte": 0.05}}

Query: "Show high priority recommendations"
Filters: {"priority": "high"}

Query: "List GDPR violations"
Filters: {"regulation": "GDPR"}

Query: "Show APIs with response time over 1000ms"
Filters: {"response_time_avg": {"gte": 1000}}

Query: "List predictions with confidence above 0.8"
Filters: {"confidence": {"gte": 0.8}}

Query: "Show deprecated APIs"
Filters: {"status": "deprecated"}

Query: "List rate limiting recommendations"
Filters: {"recommendation_type": "rate_limiting"}

Query: "Show shadow APIs"
Filters: {"intelligence_metadata.is_shadow": true}
"""


# Made with Bob