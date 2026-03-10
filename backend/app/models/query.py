"""Query model for API Intelligence Plane.

Represents a natural language query with original text, interpreted intent,
results, and user feedback.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class QueryType(str, Enum):
    """Classified query type."""

    STATUS = "status"
    TREND = "trend"
    PREDICTION = "prediction"
    SECURITY = "security"
    PERFORMANCE = "performance"
    COMPARISON = "comparison"
    GENERAL = "general"


class UserFeedback(str, Enum):
    """User feedback on query results."""

    HELPFUL = "helpful"
    NOT_HELPFUL = "not_helpful"
    PARTIALLY_HELPFUL = "partially_helpful"


class TimeRange(BaseModel):
    """Time range filter for queries."""

    start: datetime = Field(..., description="Start timestamp")
    end: datetime = Field(..., description="End timestamp")


class InterpretedIntent(BaseModel):
    """Parsed intent from natural language query."""

    action: str = Field(..., description="Action to perform (e.g., 'list', 'show', 'compare')")
    entities: list[str] = Field(..., description="Entities involved (e.g., ['api', 'vulnerability'])")
    filters: dict[str, Any] = Field(
        default_factory=dict, description="Filter conditions"
    )
    time_range: Optional[TimeRange] = Field(None, description="Time range filter")


class QueryResults(BaseModel):
    """Query execution results."""

    data: list[dict[str, Any]] = Field(..., description="Result data")
    count: int = Field(..., ge=0, description="Number of results")
    execution_time: int = Field(..., ge=0, description="Execution time in milliseconds")
    aggregations: Optional[dict[str, Any]] = Field(None, description="Aggregation results")


class Query(BaseModel):
    """Query entity representing a natural language query.

    Attributes:
        id: Unique identifier (UUID v4)
        session_id: Conversation session (UUID v4)
        user_id: User identifier (1-255 characters)
        query_text: Original query (1-5000 characters)
        query_type: Classified query type
        interpreted_intent: Parsed intent
        opensearch_query: Generated query DSL
        results: Query results
        response_text: Natural language response (1-10000 characters)
        confidence_score: Intent confidence (0-1)
        execution_time_ms: Query execution time (non-negative)
        feedback: User feedback
        feedback_comment: Feedback details (max 1000 characters)
        follow_up_queries: Suggested follow-ups (max 5)
        metadata: Additional data
        created_at: Query timestamp
    """

    id: UUID = Field(default_factory=uuid4, description="Unique identifier")
    session_id: UUID = Field(..., description="Conversation session")
    user_id: Optional[str] = Field(
        None, min_length=1, max_length=255, description="User identifier"
    )
    query_text: str = Field(
        ..., min_length=1, max_length=5000, description="Original query"
    )
    query_type: QueryType = Field(..., description="Classified query type")
    interpreted_intent: InterpretedIntent = Field(..., description="Parsed intent")
    opensearch_query: Optional[dict[str, Any]] = Field(
        None, description="Generated query DSL"
    )
    results: QueryResults = Field(..., description="Query results")
    response_text: str = Field(
        ..., min_length=1, max_length=10000, description="Natural language response"
    )
    confidence_score: float = Field(..., ge=0, le=1, description="Intent confidence (0-1)")
    execution_time_ms: int = Field(..., ge=0, description="Query execution time")
    feedback: Optional[UserFeedback] = Field(None, description="User feedback")
    feedback_comment: Optional[str] = Field(
        None, max_length=1000, description="Feedback details"
    )
    follow_up_queries: Optional[list[str]] = Field(
        None, max_length=5, description="Suggested follow-ups"
    )
    metadata: Optional[dict[str, Any]] = Field(None, description="Additional data")
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Query timestamp"
    )

    @field_validator("query_text")
    @classmethod
    def validate_query_text(cls, v: str) -> str:
        """Validate query_text is not empty."""
        if not v.strip():
            raise ValueError("query_text must not be empty")
        return v

    @field_validator("follow_up_queries")
    @classmethod
    def validate_follow_up_queries(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        """Validate follow_up_queries max 5 items."""
        if v and len(v) > 5:
            raise ValueError("follow_up_queries can have maximum 5 items")
        return v

    @field_validator("feedback")
    @classmethod
    def validate_feedback(cls, v: Optional[UserFeedback], info) -> Optional[UserFeedback]:
        """Validate if feedback is set, query must have been executed."""
        if v is not None and "results" not in info.data:
            raise ValueError("feedback can only be set if query has been executed")
        return v

    class Config:
        """Pydantic model configuration."""

        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440007",
                "session_id": "550e8400-e29b-41d4-a716-446655440008",
                "user_id": "user123",
                "query_text": "Show me all critical vulnerabilities in the last week",
                "query_type": "security",
                "interpreted_intent": {
                    "action": "list",
                    "entities": ["vulnerability"],
                    "filters": {
                        "severity": "critical",
                        "status": "open",
                    },
                    "time_range": {
                        "start": "2026-03-02T00:00:00Z",
                        "end": "2026-03-09T23:59:59Z",
                    },
                },
                "opensearch_query": {
                    "query": {
                        "bool": {
                            "must": [
                                {"term": {"severity": "critical"}},
                                {"term": {"status": "open"}},
                                {
                                    "range": {
                                        "detected_at": {
                                            "gte": "2026-03-02T00:00:00Z",
                                            "lte": "2026-03-09T23:59:59Z",
                                        }
                                    }
                                },
                            ]
                        }
                    }
                },
                "results": {
                    "data": [
                        {
                            "id": "vuln-001",
                            "title": "SQL Injection",
                            "severity": "critical",
                        }
                    ],
                    "count": 1,
                    "execution_time": 245,
                },
                "response_text": "I found 1 critical vulnerability in the last week: SQL Injection vulnerability detected in the User API.",
                "confidence_score": 0.95,
                "execution_time_ms": 245,
                "follow_up_queries": [
                    "Show me the remediation status",
                    "What APIs are affected?",
                    "Show vulnerability trends",
                ],
            }
        }

# Made with Bob
