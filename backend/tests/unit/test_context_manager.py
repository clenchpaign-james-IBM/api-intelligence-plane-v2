"""
Unit tests for ContextManager

Tests session management, entity ID extraction, and context tracking
for natural language query processing.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from app.services.query.context_manager import (
    ContextManager,
    QueryContext,
    SessionContext,
)


class TestContextManager:
    """Test suite for ContextManager."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a ContextManager instance for testing."""
        return ContextManager(session_ttl_minutes=30)
    
    @pytest.fixture
    def session_id(self):
        """Generate a test session ID."""
        return uuid4()
    
    @pytest.fixture
    def query_id(self):
        """Generate a test query ID."""
        return uuid4()
    
    def test_create_session(self, context_manager, session_id):
        """Test creating a new session."""
        user_id = "test_user"
        session = context_manager.create_session(session_id, user_id)
        
        assert session.session_id == session_id
        assert session.user_id == user_id
        assert len(session.query_history) == 0
        assert len(session.accumulated_entities) == 0
        assert isinstance(session.created_at, datetime)
    
    def test_get_session_context(self, context_manager, session_id):
        """Test retrieving session context."""
        # Create session
        context_manager.create_session(session_id)
        
        # Retrieve session
        session = context_manager.get_session_context(session_id)
        assert session is not None
        assert session.session_id == session_id
    
    def test_get_nonexistent_session(self, context_manager):
        """Test retrieving a session that doesn't exist."""
        session = context_manager.get_session_context(uuid4())
        assert session is None
    
    def test_store_query_context(self, context_manager, session_id, query_id):
        """Test storing query context."""
        query_text = "Which APIs are insecure?"
        target_indices = ["api-inventory"]
        entity_ids = {"api_id": ["API-001", "API-002", "API-003"]}
        result_count = 3
        
        context_manager.store_query_context(
            session_id=session_id,
            query_id=query_id,
            query_text=query_text,
            target_indices=target_indices,
            entity_ids=entity_ids,
            result_count=result_count,
            user_id="test_user"
        )
        
        # Verify session was created and query stored
        session = context_manager.get_session_context(session_id)
        assert session is not None
        assert len(session.query_history) == 1
        
        query_context = session.query_history[0]
        assert query_context.query_id == query_id
        assert query_context.query_text == query_text
        assert query_context.target_indices == target_indices
        assert query_context.result_count == result_count
    
    def test_entity_accumulation(self, context_manager, session_id):
        """Test that entity IDs accumulate across queries."""
        # First query
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Query 1",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001", "API-002"]},
            result_count=2
        )
        
        # Second query with overlapping and new entities
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Query 2",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-002", "API-003"]},
            result_count=2
        )
        
        # Check accumulated entities
        session = context_manager.get_session_context(session_id)
        api_ids = session.accumulated_entities.get("api_id", set())
        assert len(api_ids) == 3
        assert "API-001" in api_ids
        assert "API-002" in api_ids
        assert "API-003" in api_ids
    
    def test_get_previous_query(self, context_manager, session_id, query_id):
        """Test retrieving the most recent query."""
        # Store multiple queries
        for i in range(3):
            context_manager.store_query_context(
                session_id=session_id,
                query_id=uuid4(),
                query_text=f"Query {i}",
                target_indices=["api-inventory"],
                entity_ids={},
                result_count=0
            )
        
        # Get previous query
        previous = context_manager.get_previous_query(session_id)
        assert previous is not None
        assert previous.query_text == "Query 2"
    
    def test_get_entity_ids(self, context_manager, session_id):
        """Test retrieving entity IDs by type."""
        entity_ids = {
            "api_id": ["API-001", "API-002"],
            "gateway_id": ["GW-001"]
        }
        
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Test query",
            target_indices=["api-inventory"],
            entity_ids=entity_ids,
            result_count=2
        )
        
        # Get API IDs
        api_ids = context_manager.get_entity_ids(session_id, "api_id")
        assert len(api_ids) == 2
        assert "API-001" in api_ids
        assert "API-002" in api_ids
        
        # Get gateway IDs
        gateway_ids = context_manager.get_entity_ids(session_id, "gateway_id")
        assert len(gateway_ids) == 1
        assert "GW-001" in gateway_ids
        
        # Get non-existent entity type
        vuln_ids = context_manager.get_entity_ids(session_id, "vulnerability_id")
        assert len(vuln_ids) == 0
    
    def test_get_entity_ids_from_last_query_only(self, context_manager, session_id):
        """Test retrieving entity IDs from only the last query."""
        # First query
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Query 1",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-001", "API-002"]},
            result_count=2
        )
        
        # Second query
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Query 2",
            target_indices=["api-inventory"],
            entity_ids={"api_id": ["API-003"]},
            result_count=1
        )
        
        # Get from last query only
        api_ids = context_manager.get_entity_ids(
            session_id, "api_id", from_last_query_only=True
        )
        assert len(api_ids) == 1
        assert "API-003" in api_ids
        
        # Get accumulated
        all_api_ids = context_manager.get_entity_ids(session_id, "api_id")
        assert len(all_api_ids) == 3
    
    def test_get_all_entity_ids(self, context_manager, session_id):
        """Test retrieving all entity IDs."""
        entity_ids = {
            "api_id": ["API-001"],
            "gateway_id": ["GW-001"],
            "vulnerability_id": ["VULN-001"]
        }
        
        context_manager.store_query_context(
            session_id=session_id,
            query_id=uuid4(),
            query_text="Test query",
            target_indices=["api-inventory"],
            entity_ids=entity_ids,
            result_count=1
        )
        
        all_entities = context_manager.get_all_entity_ids(session_id)
        assert len(all_entities) == 3
        assert "api_id" in all_entities
        assert "gateway_id" in all_entities
        assert "vulnerability_id" in all_entities
    
    def test_clear_session(self, context_manager, session_id):
        """Test clearing a session."""
        # Create session
        context_manager.create_session(session_id)
        assert context_manager.get_session_context(session_id) is not None
        
        # Clear session
        result = context_manager.clear_session(session_id)
        assert result is True
        assert context_manager.get_session_context(session_id) is None
        
        # Try clearing non-existent session
        result = context_manager.clear_session(uuid4())
        assert result is False
    
    def test_session_expiration(self):
        """Test that sessions expire after TTL."""
        # Create manager with 1-minute TTL
        manager = ContextManager(session_ttl_minutes=1)
        session_id = uuid4()
        
        # Create session
        manager.create_session(session_id)
        session = manager.get_session_context(session_id)
        assert session is not None
        
        # Manually set last_accessed to past
        session.last_accessed = datetime.utcnow() - timedelta(minutes=2)
        
        # Try to retrieve - should be None (expired)
        expired_session = manager.get_session_context(session_id)
        assert expired_session is None
    
    def test_cleanup_expired_sessions(self):
        """Test cleaning up expired sessions."""
        manager = ContextManager(session_ttl_minutes=1)
        
        # Create multiple sessions
        session_ids = [uuid4() for _ in range(3)]
        for sid in session_ids:
            manager.create_session(sid)
        
        # Expire first two sessions
        for sid in session_ids[:2]:
            session = manager.get_session_context(sid)
            if session:
                session.last_accessed = datetime.utcnow() - timedelta(minutes=2)
        
        # Cleanup
        cleaned = manager.cleanup_expired_sessions()
        assert cleaned == 2
        
        # Verify only one session remains
        assert manager.get_active_session_count() == 1
        assert manager.get_session_context(session_ids[2]) is not None
    
    def test_extract_entity_ids_from_results(self, context_manager):
        """Test extracting entity IDs from query results."""
        results = [
            {"id": "API-001", "gateway_id": "GW-001", "name": "API 1"},
            {"id": "API-002", "gateway_id": "GW-001", "name": "API 2"},
            {"id": "API-003", "gateway_id": "GW-002", "name": "API 3"},
        ]
        
        entity_ids = context_manager.extract_entity_ids_from_results(results)
        
        assert "api_id" in entity_ids
        assert len(entity_ids["api_id"]) == 3
        assert "API-001" in entity_ids["api_id"]
        
        assert "gateway_id" in entity_ids
        assert len(entity_ids["gateway_id"]) == 2
        assert "GW-001" in entity_ids["gateway_id"]
        assert "GW-002" in entity_ids["gateway_id"]
    
    def test_extract_entity_ids_custom_mapping(self, context_manager):
        """Test extracting entity IDs with custom field mapping."""
        results = [
            {"vuln_id": "VULN-001", "api_ref": "API-001"},
            {"vuln_id": "VULN-002", "api_ref": "API-001"},
        ]
        
        mapping = {
            "vuln_id": "vulnerability_id",
            "api_ref": "api_id"
        }
        
        entity_ids = context_manager.extract_entity_ids_from_results(
            results, mapping
        )
        
        assert "vulnerability_id" in entity_ids
        assert len(entity_ids["vulnerability_id"]) == 2
        assert "api_id" in entity_ids
        assert len(entity_ids["api_id"]) == 1
    
    def test_filters_applied_tracking(self, context_manager, session_id, query_id):
        """Test tracking of applied filters."""
        filters = {"severity": "critical", "status": "open"}
        
        context_manager.store_query_context(
            session_id=session_id,
            query_id=query_id,
            query_text="Test query",
            target_indices=["security-findings"],
            entity_ids={},
            result_count=0,
            filters_applied=filters
        )
        
        session = context_manager.get_session_context(session_id)
        assert session.active_filters == filters
    
    def test_multiple_indices_tracking(self, context_manager, session_id, query_id):
        """Test tracking queries across multiple indices."""
        target_indices = ["api-inventory", "security-findings"]
        
        context_manager.store_query_context(
            session_id=session_id,
            query_id=query_id,
            query_text="Multi-index query",
            target_indices=target_indices,
            entity_ids={},
            result_count=0
        )
        
        previous = context_manager.get_previous_query(session_id)
        assert previous.target_indices == target_indices
    
    def test_active_session_count(self, context_manager):
        """Test getting active session count."""
        assert context_manager.get_active_session_count() == 0
        
        # Create sessions
        for _ in range(3):
            context_manager.create_session(uuid4())
        
        assert context_manager.get_active_session_count() == 3

# Made with Bob
