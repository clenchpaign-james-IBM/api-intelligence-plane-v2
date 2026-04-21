"""
Context Manager for Natural Language Query Processing

Maintains conversational context across queries, enabling follow-up questions
and multi-index query orchestration. Implements session-based storage with TTL
for entity IDs, query history, and result caching.

Based on: docs/enterprise-nlq-multi-index-analysis.md
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import UUID

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class QueryContext(BaseModel):
    """Context information for a single query in a session.
    
    Attributes:
        query_id: Unique identifier for the query
        query_text: Original natural language query text
        timestamp: When the query was executed
        target_indices: List of indices queried
        entity_ids: Extracted entity IDs from query results
        result_count: Number of results returned
        filters_applied: Filters that were applied in the query
    """
    
    query_id: UUID = Field(..., description="Unique identifier for the query")
    query_text: str = Field(..., description="Original natural language query text")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Query execution timestamp")
    target_indices: List[str] = Field(default_factory=list, description="Indices queried")
    entity_ids: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Extracted entity IDs by type (e.g., {'api_id': ['API-001', 'API-002']})"
    )
    result_count: int = Field(default=0, description="Number of results returned")
    filters_applied: Dict[str, Any] = Field(default_factory=dict, description="Filters applied")


class SessionContext(BaseModel):
    """Complete context for a user session.
    
    Attributes:
        session_id: Unique session identifier
        user_id: Optional user identifier
        created_at: Session creation timestamp
        last_accessed: Last query timestamp
        query_history: List of queries in this session (most recent last)
        accumulated_entities: All entity IDs accumulated across queries
        active_filters: Currently active filters from previous queries
    """
    
    session_id: UUID = Field(..., description="Unique session identifier")
    user_id: Optional[str] = Field(None, description="Optional user identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session creation time")
    last_accessed: datetime = Field(default_factory=datetime.utcnow, description="Last access time")
    query_history: List[QueryContext] = Field(default_factory=list, description="Query history")
    accumulated_entities: Dict[str, Set[str]] = Field(
        default_factory=dict,
        description="Accumulated entity IDs by type across all queries"
    )
    active_filters: Dict[str, Any] = Field(default_factory=dict, description="Active filters")
    
    class Config:
        arbitrary_types_allowed = True


class ContextManager:
    """Manages conversational context across natural language queries.
    
    Provides session-based storage for query history, entity IDs, and context
    propagation to enable follow-up questions and multi-index queries.
    
    Features:
    - Session storage with configurable TTL (default: 30 minutes)
    - Entity ID extraction and accumulation
    - Query history tracking
    - Context retrieval for follow-up queries
    - Reference resolution support ("these APIs", "those vulnerabilities")
    - Automatic session cleanup
    
    Example:
        >>> manager = ContextManager()
        >>> # First query
        >>> manager.store_query_context(
        ...     session_id=session_id,
        ...     query_id=query_id,
        ...     query_text="Which APIs are insecure?",
        ...     target_indices=["api-inventory"],
        ...     entity_ids={"api_id": ["API-001", "API-002"]},
        ...     result_count=2
        ... )
        >>> # Follow-up query
        >>> context = manager.get_session_context(session_id)
        >>> api_ids = context.accumulated_entities.get("api_id", set())
        >>> # Use api_ids to filter next query
    """
    
    def __init__(self, session_ttl_minutes: int = 30):
        """Initialize the context manager.
        
        Args:
            session_ttl_minutes: Session time-to-live in minutes (default: 30)
        """
        self.session_ttl = timedelta(minutes=session_ttl_minutes)
        self._sessions: Dict[UUID, SessionContext] = {}
        logger.info(f"ContextManager initialized with TTL: {session_ttl_minutes} minutes")
    
    def create_session(self, session_id: UUID, user_id: Optional[str] = None) -> SessionContext:
        """Create a new session context.
        
        Args:
            session_id: Unique session identifier
            user_id: Optional user identifier
            
        Returns:
            Created session context
        """
        session = SessionContext(session_id=session_id, user_id=user_id)
        self._sessions[session_id] = session
        logger.info(f"Created new session: {session_id} for user: {user_id}")
        return session
    
    def get_session_context(self, session_id: UUID) -> Optional[SessionContext]:
        """Retrieve session context by ID.
        
        Automatically cleans up expired sessions.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session context if found and not expired, None otherwise
        """
        session = self._sessions.get(session_id)
        
        if not session:
            logger.debug(f"Session not found: {session_id}")
            return None
        
        # Check if session has expired
        if self._is_session_expired(session):
            logger.info(f"Session expired: {session_id}")
            del self._sessions[session_id]
            return None
        
        return session
    
    def store_query_context(
        self,
        session_id: UUID,
        query_id: UUID,
        query_text: str,
        target_indices: List[str],
        entity_ids: Dict[str, List[str]],
        result_count: int,
        filters_applied: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> None:
        """Store context for a query execution.
        
        Creates session if it doesn't exist. Accumulates entity IDs across queries.
        
        Args:
            session_id: Session identifier
            query_id: Query identifier
            query_text: Original query text
            target_indices: List of indices queried
            entity_ids: Extracted entity IDs by type
            result_count: Number of results returned
            filters_applied: Optional filters that were applied
            user_id: Optional user identifier (for new sessions)
        """
        # Get or create session
        session = self.get_session_context(session_id)
        if not session:
            session = self.create_session(session_id, user_id)
        
        # Create query context
        query_context = QueryContext(
            query_id=query_id,
            query_text=query_text,
            target_indices=target_indices,
            entity_ids=entity_ids,
            result_count=result_count,
            filters_applied=filters_applied or {},
        )
        
        # Add to query history
        session.query_history.append(query_context)
        
        # Accumulate entity IDs
        for entity_type, ids in entity_ids.items():
            if entity_type not in session.accumulated_entities:
                session.accumulated_entities[entity_type] = set()
            session.accumulated_entities[entity_type].update(ids)
        
        # Update active filters if provided
        if filters_applied:
            session.active_filters.update(filters_applied)
        
        # Update last accessed time
        session.last_accessed = datetime.utcnow()
        
        logger.info(
            f"Stored query context for session {session_id}: "
            f"query_id={query_id}, indices={target_indices}, "
            f"entities={len(entity_ids)}, results={result_count}"
        )
    
    def get_previous_query(self, session_id: UUID) -> Optional[QueryContext]:
        """Get the most recent query from session history.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Most recent query context, or None if no history
        """
        session = self.get_session_context(session_id)
        if not session or not session.query_history:
            return None
        
        return session.query_history[-1]
    
    def get_entity_ids(
        self,
        session_id: UUID,
        entity_type: str,
        from_last_query_only: bool = False
    ) -> Set[str]:
        """Get entity IDs of a specific type from session context.
        
        Args:
            session_id: Session identifier
            entity_type: Type of entity (e.g., 'api_id', 'gateway_id')
            from_last_query_only: If True, only return IDs from last query
            
        Returns:
            Set of entity IDs, empty set if none found
        """
        session = self.get_session_context(session_id)
        if not session:
            return set()
        
        if from_last_query_only:
            last_query = self.get_previous_query(session_id)
            if last_query and entity_type in last_query.entity_ids:
                return set(last_query.entity_ids[entity_type])
            return set()
        
        return session.accumulated_entities.get(entity_type, set())
    
    def get_all_entity_ids(self, session_id: UUID) -> Dict[str, Set[str]]:
        """Get all accumulated entity IDs from session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Dictionary of entity type to set of IDs
        """
        session = self.get_session_context(session_id)
        if not session:
            return {}
        
        return session.accumulated_entities
    
    def clear_session(self, session_id: UUID) -> bool:
        """Clear a specific session.
        
        Args:
            session_id: Session identifier
            
        Returns:
            True if session was cleared, False if not found
        """
        if session_id in self._sessions:
            del self._sessions[session_id]
            logger.info(f"Cleared session: {session_id}")
            return True
        return False
    
    def cleanup_expired_sessions(self) -> int:
        """Remove all expired sessions.
        
        Returns:
            Number of sessions cleaned up
        """
        expired_sessions = [
            session_id
            for session_id, session in self._sessions.items()
            if self._is_session_expired(session)
        ]
        
        for session_id in expired_sessions:
            del self._sessions[session_id]
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")
        
        return len(expired_sessions)
    
    def get_active_session_count(self) -> int:
        """Get count of active (non-expired) sessions.
        
        Returns:
            Number of active sessions
        """
        return len(self._sessions)
    
    def extract_entity_ids_from_results(
        self,
        results: List[Dict[str, Any]],
        entity_type_mapping: Optional[Dict[str, str]] = None
    ) -> Dict[str, List[str]]:
        """Extract entity IDs from query results.
        
        Args:
            results: List of result documents
            entity_type_mapping: Optional mapping of field names to entity types
                                (e.g., {'id': 'api_id', 'gateway_id': 'gateway_id'})
            
        Returns:
            Dictionary of entity type to list of IDs
        """
        if not entity_type_mapping:
            # Default mapping for common fields
            entity_type_mapping = {
                'id': 'api_id',
                'api_id': 'api_id',
                'gateway_id': 'gateway_id',
                'vulnerability_id': 'vulnerability_id',
                'prediction_id': 'prediction_id',
                'recommendation_id': 'recommendation_id',
            }
        
        entity_ids: Dict[str, List[str]] = {}
        
        for result in results:
            for field_name, entity_type in entity_type_mapping.items():
                if field_name in result and result[field_name]:
                    if entity_type not in entity_ids:
                        entity_ids[entity_type] = []
                    
                    value = result[field_name]
                    if isinstance(value, list):
                        entity_ids[entity_type].extend([str(v) for v in value])
                    else:
                        entity_ids[entity_type].append(str(value))
        
        # Remove duplicates while preserving order
        for entity_type in entity_ids:
            entity_ids[entity_type] = list(dict.fromkeys(entity_ids[entity_type]))
        
        return entity_ids
    
    def _is_session_expired(self, session: SessionContext) -> bool:
        """Check if a session has expired.
        
        Args:
            session: Session context to check
            
        Returns:
            True if session has expired, False otherwise
        """
        return datetime.utcnow() - session.last_accessed > self.session_ttl

# Made with Bob
