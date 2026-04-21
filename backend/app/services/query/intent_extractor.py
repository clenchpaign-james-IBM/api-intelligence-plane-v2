"""Enhanced Intent Extractor for Context-Aware Natural Language Query Processing.

Extracts structured intent from natural language queries with support for:
- Reference detection ("these APIs", "those vulnerabilities")
- Entity resolution from session context
- Relationship identification between entities
- Context dependency tracking
- Multi-index query planning

Based on: docs/enterprise-nlq-multi-index-analysis.md Phase 2
Updated: 2026-04-21 - Integrated EntityRegistry, FilterExtractor, TimeParser
"""

import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from app.models.enhanced_intent import (
    ContextDependency,
    EnhancedInterpretedIntent,
    EntityReference,
    EntityRelationship,
    ReferenceType,
)
from app.models.query import InterpretedIntent, QueryType, TimeRange
from app.services.llm_service import LLMService
from app.services.query.context_manager import ContextManager
from app.services.query.relationship_graph import RelationshipGraph
from app.services.query.entity_registry import EntityRegistry
from app.services.query.filter_extractor import FilterExtractor
from app.services.query.time_parser import TimeRangeParser

logger = logging.getLogger(__name__)


class EnhancedIntentExtractor:
    """Extracts enhanced intent from natural language queries with context awareness.
    
    Features:
    - Reference detection and resolution
    - Entity relationship identification
    - Context dependency tracking
    - Multi-index query planning
    - LLM-powered intent extraction with context
    
    Example:
        >>> extractor = EnhancedIntentExtractor(llm_service, context_manager)
        >>> intent = await extractor.extract_intent(
        ...     query_text="What vulnerabilities affect these APIs?",
        ...     session_id=session_id,
        ...     query_type=QueryType.SECURITY
        ... )
        >>> print(intent.references)  # [EntityReference(type=DEMONSTRATIVE, ...)]
        >>> print(intent.resolved_entities)  # {"api_id": ["API-001", "API-002"]}
    """
    
    # Reference detection patterns
    REFERENCE_PATTERNS = {
        ReferenceType.DEMONSTRATIVE: [
            r'\b(these|those|this|that)\s+(\w+)',
            r'\b(the\s+above|the\s+following|the\s+previous)\s+(\w+)',
        ],
        ReferenceType.PRONOUN: [
            r'\b(them|it|they|their|its)\b',
        ],
        ReferenceType.IMPLICIT: [
            r'\bfor\s+(the\s+)?(\w+)\b',
            r'\bof\s+(the\s+)?(\w+)\b',
            r'\bin\s+(the\s+)?(\w+)\b',
        ],
    }
    
    # Entity type keywords for reference resolution (now using EntityRegistry)
    @classmethod
    def _get_entity_keywords(cls) -> Dict[str, List[str]]:
        """Get entity keywords from EntityRegistry."""
        keywords = {}
        for entity_type in EntityRegistry.get_all_entity_types():
            config = EntityRegistry.ENTITIES[entity_type]
            keywords[entity_type] = [entity_type] + config.aliases
        return keywords
    
    ENTITY_KEYWORDS = None  # Will be populated from EntityRegistry
    
    # Relationship keywords
    RELATIONSHIP_KEYWORDS = {
        "has": ["has", "have", "with", "containing", "includes"],
        "belongs_to": ["belongs to", "in", "on", "from", "of"],
        "affects": ["affects", "affecting", "impact", "impacting"],
        "generates": ["generates", "generating", "produces", "producing"],
        "receives": ["receives", "receiving", "gets", "getting"],
    }
    
    def __init__(
        self,
        llm_service: LLMService,
        context_manager: ContextManager,
        relationship_graph: Optional[RelationshipGraph] = None
    ):
        """Initialize the enhanced intent extractor.
        
        Args:
            llm_service: LLM service for intent extraction
            context_manager: Context manager for session tracking
            relationship_graph: Optional relationship graph for entity relationships
        """
        self.llm_service = llm_service
        self.context_manager = context_manager
        self.relationship_graph = relationship_graph or RelationshipGraph()
        logger.info("EnhancedIntentExtractor initialized")
    
    async def extract_intent(
        self,
        query_text: str,
        session_id: UUID,
        query_type: QueryType,
        previous_query_id: Optional[UUID] = None,
        user_id: Optional[str] = None,
    ) -> EnhancedInterpretedIntent:
        """Extract enhanced intent from a natural language query.
        
        Args:
            query_text: Natural language query text
            session_id: Session ID for context tracking
            query_type: Classified query type
            previous_query_id: Optional ID of previous query
            user_id: Optional user identifier
            
        Returns:
            Enhanced interpreted intent with context and relationships
        """
        logger.info(f"Extracting enhanced intent for query: {query_text[:50]}...")
        
        # Step 1: Get session context
        session_context = self.context_manager.get_session_context(session_id)
        previous_query = self.context_manager.get_previous_query(session_id) if session_context else None
        
        # Step 2: Detect references in query text
        references = self._detect_references(query_text, session_context)
        
        # Step 3: Extract base intent using LLM with context
        base_intent, confidence = await self._extract_base_intent_with_context(
            query_text, query_type, session_context, references
        )
        
        # Step 4: Resolve entity references from context
        resolved_entities = self._resolve_entity_references(references, session_context)
        
        # Step 5: Identify entity relationships
        relationships = self._identify_relationships(
            base_intent.entities, query_text, resolved_entities
        )
        
        # Step 6: Determine context dependency
        context_dependency = self._determine_context_dependency(
            references, relationships, base_intent.entities
        )
        
        # Step 7: Determine target indices
        target_indices = self._determine_target_indices(
            base_intent.entities, relationships, resolved_entities
        )
        
        # Step 8: Check if join is required
        requires_join = len(target_indices) > 1 or len(relationships) > 0
        
        # Create enhanced intent
        enhanced_intent = EnhancedInterpretedIntent(
            action=base_intent.action,
            entities=base_intent.entities,
            filters=base_intent.filters,
            time_range=base_intent.time_range,
            references=references,
            relationships=relationships,
            context_dependency=context_dependency,
            target_indices=target_indices,
            requires_join=requires_join,
            previous_query_id=previous_query_id or (previous_query.query_id if previous_query else None),
            session_id=session_id,
            resolved_entities=resolved_entities,
        )
        
        logger.info(
            f"Enhanced intent extracted: entities={base_intent.entities}, "
            f"references={len(references)}, relationships={len(relationships)}, "
            f"requires_join={requires_join}, confidence={confidence}"
        )
        
        return enhanced_intent
    
    def _detect_references(
        self,
        query_text: str,
        session_context: Optional[Any]
    ) -> List[EntityReference]:
        """Detect entity references in query text.
        
        Args:
            query_text: Query text to analyze
            session_context: Optional session context
            
        Returns:
            List of detected entity references
        """
        references = []
        query_lower = query_text.lower()
        
        # Check for demonstrative references
        for pattern in self.REFERENCE_PATTERNS[ReferenceType.DEMONSTRATIVE]:
            matches = re.finditer(pattern, query_lower)
            for match in matches:
                reference_text = match.group(0)
                entity_word = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
                
                # Map entity word to entity type
                entity_type = self._map_word_to_entity_type(entity_word)
                if entity_type:
                    references.append(EntityReference(
                        reference_type=ReferenceType.DEMONSTRATIVE,
                        reference_text=reference_text,
                        entity_type=entity_type,
                        resolved_ids=[],
                        confidence=0.9
                    ))
        
        # Check for pronoun references
        for pattern in self.REFERENCE_PATTERNS[ReferenceType.PRONOUN]:
            if re.search(pattern, query_lower):
                # Pronoun reference - need to infer entity type from context
                if session_context and session_context.query_history:
                    last_query = session_context.query_history[-1]
                    if last_query.entity_ids:
                        # Use the most recent entity type
                        entity_type = list(last_query.entity_ids.keys())[0].replace('_id', '')
                        pronoun_match = re.search(pattern, query_lower)
                        if pronoun_match:
                            references.append(EntityReference(
                                reference_type=ReferenceType.PRONOUN,
                                reference_text=pronoun_match.group(0),
                                entity_type=entity_type if entity_type else "api",
                                resolved_ids=[],
                                confidence=0.7
                            ))
        
        # Check for implicit references
        if not references and session_context and session_context.query_history:
            # If no explicit references but we have context, check for implicit references
            for pattern in self.REFERENCE_PATTERNS[ReferenceType.IMPLICIT]:
                matches = re.finditer(pattern, query_lower)
                for match in matches:
                    entity_word = match.group(2) if match.lastindex and match.lastindex >= 2 else match.group(1)
                    entity_type = self._map_word_to_entity_type(entity_word)
                    
                    if entity_type and entity_type in [
                        key.replace('_id', '') for key in session_context.accumulated_entities.keys()
                    ]:
                        references.append(EntityReference(
                            reference_type=ReferenceType.IMPLICIT,
                            reference_text=match.group(0),
                            entity_type=entity_type,
                            resolved_ids=[],
                            confidence=0.6
                        ))
        
        return references
    
    def _map_word_to_entity_type(self, word: str) -> Optional[str]:
        """Map a word to an entity type using EntityRegistry.
        
        Args:
            word: Word to map
            
        Returns:
            Entity type or None if not found
        """
        # Use EntityRegistry for consistent entity resolution
        return EntityRegistry.resolve_entity(word)
    
    async def _extract_base_intent_with_context(
        self,
        query_text: str,
        query_type: QueryType,
        session_context: Optional[Any],
        references: List[EntityReference]
    ) -> Tuple[InterpretedIntent, float]:
        """Extract base intent using LLM with context awareness and enhanced extractors.
        
        Args:
            query_text: Query text
            query_type: Query type
            session_context: Optional session context
            references: Detected references
            
        Returns:
            Tuple of (InterpretedIntent, confidence_score)
        """
        # Step 1: Extract time range using TimeRangeParser
        time_range = TimeRangeParser.parse(query_text)
        if time_range:
            logger.info(f"Extracted time range: {time_range.start} to {time_range.end}")
        
        # Step 2: Pre-extract filters using FilterExtractor
        # (Will be merged with LLM-extracted filters)
        pre_extracted_filters = FilterExtractor.extract(query_text)
        if pre_extracted_filters:
            logger.info(f"Pre-extracted filters: {pre_extracted_filters}")
        
        # Build context-aware prompt with filter examples
        system_prompt = self._build_context_aware_prompt(
            query_type, session_context, references
        )
        
        # Add filter extraction examples to prompt
        filter_examples = FilterExtractor.get_filter_examples()
        
        # Build user message
        user_message = f"""Extract structured intent from this query:

Query: "{query_text}"
Query Type: {query_type.value}

{filter_examples}

Provide the response in JSON format with these fields:
- action: The primary action (list, show, count, analyze, compare, etc.)
- entities: List of entity types (api, gateway, vulnerability, metric, prediction, recommendation, compliance, transaction)
- filters: Dictionary of filter conditions (see examples above)
- time_range: Optional time range with start and end (ISO format) - leave null if already extracted
- confidence: Confidence score (0-1)

Example response:
{{
  "action": "list",
  "entities": ["vulnerability"],
  "filters": {{"severity": "critical"}},
  "time_range": null,
  "confidence": 0.95
}}"""
        
        # Call LLM
        try:
            response = await self.llm_service.generate_completion(
                messages=[{"role": "user", "content": user_message}],
                system_prompt=system_prompt,
                temperature=0.3,
                max_tokens=500
            )
            
            # Parse response
            import json
            content = response.get("content", "")
            
            # Check if content is empty
            if not content or not content.strip():
                logger.warning("LLM returned empty content, using fallback")
                return self._fallback_intent_extraction(query_text, query_type), 0.5
            
            # Extract JSON from response (handle markdown code blocks)
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
            if json_match:
                content = json_match.group(1)
            else:
                # Try to find JSON object directly
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    content = json_match.group(0)
            
            # Check if we have valid JSON string
            if not content or not content.strip():
                logger.warning("No JSON found in LLM response, using fallback")
                return self._fallback_intent_extraction(query_text, query_type), 0.5
            
            try:
                intent_data = json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from LLM response: {e}")
                return self._fallback_intent_extraction(query_text, query_type), 0.5
            
            # Merge pre-extracted filters with LLM-extracted filters
            llm_filters = intent_data.get("filters", {})
            merged_filters = {**pre_extracted_filters, **llm_filters}
            
            # Use pre-extracted time range if LLM didn't extract one
            llm_time_range = self._parse_time_range(intent_data.get("time_range"))
            final_time_range = time_range or llm_time_range
            
            # Resolve entity aliases using EntityRegistry
            raw_entities = intent_data.get("entities", [])
            resolved_entities = []
            for entity in raw_entities:
                resolved = EntityRegistry.resolve_entity(entity)
                if resolved:
                    resolved_entities.append(resolved)
                else:
                    # Keep original if can't resolve
                    resolved_entities.append(entity)
                    logger.warning(f"Could not resolve entity: {entity}")
            
            # Create InterpretedIntent
            intent = InterpretedIntent(
                action=intent_data.get("action", "list"),
                entities=resolved_entities,
                filters=merged_filters,
                time_range=final_time_range
            )
            
            confidence = intent_data.get("confidence", 0.8)
            
            # Boost confidence if we extracted filters/time independently
            if pre_extracted_filters or time_range:
                confidence = min(1.0, confidence + 0.1)
            
            return intent, confidence
            
        except Exception as e:
            logger.error(f"Error extracting intent with LLM: {e}")
            # Fallback to basic extraction
            return self._fallback_intent_extraction(query_text, query_type), 0.5
    
    def _build_context_aware_prompt(
        self,
        query_type: QueryType,
        session_context: Optional[Any],
        references: List[EntityReference]
    ) -> str:
        """Build context-aware system prompt for LLM.
        
        Args:
            query_type: Query type
            session_context: Optional session context
            references: Detected references
            
        Returns:
            System prompt string
        """
        prompt = """You are an AI assistant that extracts structured intent from natural language queries about API management and monitoring.

Your task is to analyze queries and extract:
1. Action: What the user wants to do (list, show, count, analyze, compare, etc.)
2. Entities: What entities are involved (api, gateway, vulnerability, metric, prediction, recommendation, compliance, transaction)
3. Filters: Any filter conditions mentioned (severity, status, etc.)
4. Time Range: If mentioned, extract start and end times

"""
        
        # Add context information if available
        if session_context and session_context.query_history:
            prompt += "\n**IMPORTANT: This query is part of an ongoing conversation.**\n\n"
            prompt += "Previous query context:\n"
            
            # Add last query info
            last_query = session_context.query_history[-1]
            prompt += f"- Last query: \"{last_query.query_text}\"\n"
            prompt += f"- Entities queried: {list(last_query.entity_ids.keys())}\n"
            prompt += f"- Result count: {last_query.result_count}\n"
            
            # Add accumulated entities
            if session_context.accumulated_entities:
                prompt += f"\nAccumulated entity IDs from previous queries:\n"
                for entity_type, ids in session_context.accumulated_entities.items():
                    prompt += f"- {entity_type}: {len(ids)} entities\n"
        
        # Add reference information
        if references:
            prompt += "\n**DETECTED REFERENCES:**\n"
            for ref in references:
                prompt += f"- \"{ref.reference_text}\" refers to {ref.entity_type} entities from previous query\n"
            prompt += "\nWhen references are detected, the entities list should include the referenced entity type.\n"
        
        # Add relationship awareness
        prompt += "\n**RELATIONSHIP AWARENESS:**\n"
        prompt += "Consider these common relationships between entities:\n"
        prompt += "- APIs have vulnerabilities, metrics, predictions, recommendations, compliance violations, and transaction logs\n"
        prompt += "- Gateways manage APIs\n"
        prompt += "- Vulnerabilities link to compliance violations\n"
        prompt += "- Metrics are analyzed to generate predictions\n"
        
        prompt += "\nProvide accurate, structured intent extraction in JSON format."
        
        return prompt
    
    def _parse_time_range(self, time_range_data: Optional[Dict[str, str]]) -> Optional[TimeRange]:
        """Parse time range from LLM response.
        
        Args:
            time_range_data: Time range dictionary
            
        Returns:
            TimeRange object or None
        """
        if not time_range_data or not isinstance(time_range_data, dict):
            return None
        
        try:
            from datetime import datetime
            start = datetime.fromisoformat(time_range_data["start"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(time_range_data["end"].replace("Z", "+00:00"))
            return TimeRange(start=start, end=end)
        except Exception as e:
            logger.warning(f"Error parsing time range: {e}")
            return None
    
    def _fallback_intent_extraction(
        self,
        query_text: str,
        query_type: QueryType
    ) -> InterpretedIntent:
        """Fallback intent extraction without LLM.
        
        Args:
            query_text: Query text
            query_type: Query type
            
        Returns:
            Basic InterpretedIntent
        """
        query_lower = query_text.lower()
        
        # Extract action
        action = "list"
        if any(word in query_lower for word in ["count", "how many"]):
            action = "count"
        elif any(word in query_lower for word in ["compare", "versus", "vs"]):
            action = "compare"
        elif any(word in query_lower for word in ["analyze", "analysis"]):
            action = "analyze"
        
        # Extract entities using EntityRegistry
        entities = []
        for entity_type in EntityRegistry.get_all_entity_types():
            config = EntityRegistry.ENTITIES[entity_type]
            all_keywords = [entity_type] + config.aliases
            if any(keyword in query_lower for keyword in all_keywords):
                entities.append(entity_type)
        
        if not entities:
            entities = ["api"]  # Default to API
        
        # Extract filters using FilterExtractor
        filters = FilterExtractor.extract(query_text, entities)
        
        # Extract time range using TimeRangeParser
        time_range = TimeRangeParser.parse(query_text)
        
        return InterpretedIntent(
            action=action,
            entities=entities,
            filters=filters,
            time_range=time_range
        )
    
    def _resolve_entity_references(
        self,
        references: List[EntityReference],
        session_context: Optional[Any]
    ) -> Dict[str, List[str]]:
        """Resolve entity references to actual entity IDs from context.
        
        Args:
            references: Detected references
            session_context: Session context
            
        Returns:
            Dictionary of entity type to list of resolved IDs
        """
        resolved: Dict[str, List[str]] = {}
        
        if not session_context:
            return resolved
        
        for ref in references:
            entity_id_key = f"{ref.entity_type}_id"
            
            # Get IDs from context based on reference type
            if ref.reference_type in [ReferenceType.DEMONSTRATIVE, ReferenceType.PRONOUN]:
                # Use IDs from last query only
                ids = self.context_manager.get_entity_ids(
                    session_context.session_id,
                    entity_id_key,
                    from_last_query_only=True
                )
            else:
                # Use all accumulated IDs
                ids = self.context_manager.get_entity_ids(
                    session_context.session_id,
                    entity_id_key,
                    from_last_query_only=False
                )
            
            if ids:
                ref.resolved_ids = list(ids)
                resolved[entity_id_key] = list(ids)
        
        return resolved
    
    def _identify_relationships(
        self,
        entities: List[str],
        query_text: str,
        resolved_entities: Dict[str, List[str]]
    ) -> List[EntityRelationship]:
        """Identify relationships between entities in the query.
        
        Args:
            entities: List of entity types
            query_text: Query text
            resolved_entities: Resolved entity IDs from context
            
        Returns:
            List of identified relationships
        """
        relationships = []
        query_lower = query_text.lower()
        
        # If we have resolved entities and new entities, there's likely a relationship
        if resolved_entities and entities:
            source_entities = [key.replace('_id', '') for key in resolved_entities.keys()]
            target_entities = [e for e in entities if e not in source_entities]
            
            for source in source_entities:
                for target in target_entities:
                    # Check if relationship exists in graph
                    source_index = self._entity_to_index(source)
                    target_index = self._entity_to_index(target)
                    
                    if source_index and target_index:
                        join_fields = self.relationship_graph.get_join_fields(source_index, target_index)
                        if join_fields:
                            # Determine relationship type from query text
                            rel_type = self._infer_relationship_type(query_lower)
                            
                            relationships.append(EntityRelationship(
                                source_entity=source,
                                target_entity=target,
                                relationship_type=rel_type,
                                join_fields=join_fields,
                                description=f"{source} {rel_type} {target}"
                            ))
        
        return relationships
    
    def _infer_relationship_type(self, query_text: str) -> str:
        """Infer relationship type from query text.
        
        Args:
            query_text: Query text
            
        Returns:
            Relationship type string
        """
        for rel_type, keywords in self.RELATIONSHIP_KEYWORDS.items():
            if any(keyword in query_text for keyword in keywords):
                return rel_type
        return "has"  # Default relationship
    
    def _entity_to_index(self, entity_type: str) -> Optional[str]:
        """Map entity type to index name using EntityRegistry.
        
        Args:
            entity_type: Entity type
            
        Returns:
            Index name or None
        """
        return EntityRegistry.get_index(entity_type)
    
    def _determine_context_dependency(
        self,
        references: List[EntityReference],
        relationships: List[EntityRelationship],
        entities: List[str]
    ) -> ContextDependency:
        """Determine context dependency for the query.
        
        Args:
            references: Detected references
            relationships: Identified relationships
            entities: Entity types in query
            
        Returns:
            Context dependency information
        """
        depends_on_previous = len(references) > 0 or len(relationships) > 0
        
        required_entity_types = []
        if references:
            required_entity_types = [ref.entity_type for ref in references]
        elif relationships:
            required_entity_types = [rel.source_entity for rel in relationships]
        
        fallback_strategy = "error" if depends_on_previous else "all"
        
        return ContextDependency(
            depends_on_previous=depends_on_previous,
            required_entity_types=required_entity_types,
            context_window=1,
            fallback_strategy=fallback_strategy
        )
    
    def _determine_target_indices(
        self,
        entities: List[str],
        relationships: List[EntityRelationship],
        resolved_entities: Dict[str, List[str]]
    ) -> List[str]:
        """Determine target indices for the query.
        
        Args:
            entities: Entity types
            relationships: Entity relationships
            resolved_entities: Resolved entities from context
            
        Returns:
            List of target index names
        """
        indices = set()
        
        # Add indices for primary entities
        for entity in entities:
            index = self._entity_to_index(entity)
            if index:
                indices.add(index)
        
        # Add indices for relationship sources
        for rel in relationships:
            source_index = self._entity_to_index(rel.source_entity)
            if source_index:
                indices.add(source_index)
        
        return list(indices)


# Made with Bob