"""
Query API Endpoints

REST API endpoints for natural language query interface.
"""

import logging
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status as http_status
from pydantic import BaseModel, Field

from app.db.repositories.query_repository import QueryRepository
from app.db.repositories.api_repository import APIRepository
from app.db.repositories.metrics_repository import MetricsRepository
from app.db.repositories.prediction_repository import PredictionRepository
from app.db.repositories.recommendation_repository import RecommendationRepository
from app.services.query_service import QueryService
from app.services.llm_service import LLMService
from app.models.query import Query, UserFeedback
from app.config import Settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Query"])


# Request Models
class QueryRequest(BaseModel):
    """Request model for executing a natural language query."""
    
    query_text: str = Field(..., min_length=1, max_length=5000, description="Natural language query")
    session_id: Optional[UUID] = Field(None, description="Conversation session ID")


class FeedbackRequest(BaseModel):
    """Request model for providing feedback on a query."""
    
    feedback: UserFeedback = Field(..., description="User feedback")
    comment: Optional[str] = Field(None, max_length=1000, description="Optional feedback comment")


# Response Models
class QueryResponse(BaseModel):
    """Response model for query execution."""
    
    query_id: UUID = Field(..., description="Query ID")
    query_text: str = Field(..., description="Original query text")
    response_text: str = Field(..., description="Natural language response")
    confidence_score: float = Field(..., description="Confidence score (0-1)")
    results: dict = Field(..., description="Query results")
    follow_up_queries: Optional[list[str]] = Field(None, description="Suggested follow-up queries")
    execution_time_ms: int = Field(..., description="Execution time in milliseconds")


class QueryHistoryResponse(BaseModel):
    """Response model for query history."""
    
    items: list[Query]
    total: int
    page: int
    page_size: int


# Initialize dependencies
settings = Settings()
query_repo = QueryRepository()
api_repo = APIRepository()
metrics_repo = MetricsRepository()
prediction_repo = PredictionRepository()
recommendation_repo = RecommendationRepository()
llm_service = LLMService(settings)

query_service = QueryService(
    query_repository=query_repo,
    api_repository=api_repo,
    metrics_repository=metrics_repo,
    prediction_repository=prediction_repo,
    recommendation_repository=recommendation_repo,
    llm_service=llm_service,
)


@router.post(
    "/query",
    response_model=QueryResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Execute natural language query",
    description="Process a natural language query and return results with AI-generated response",
)
async def execute_query(request: QueryRequest) -> QueryResponse:
    """
    Execute a natural language query.
    
    Args:
        request: Query request with query text and optional session ID
        
    Returns:
        Query response with results and natural language answer
        
    Raises:
        HTTPException: If query processing fails
    """
    try:
        # Generate session ID if not provided
        session_id = request.session_id or UUID("00000000-0000-0000-0000-000000000000")
        
        # Process query
        query = await query_service.process_query(
            query_text=request.query_text,
            session_id=session_id,
        )
        
        logger.info(f"Processed query {query.id} with confidence {query.confidence_score}")
        
        return QueryResponse(
            query_id=query.id,
            query_text=query.query_text,
            response_text=query.response_text,
            confidence_score=query.confidence_score,
            results=query.results.model_dump(),
            follow_up_queries=query.follow_up_queries,
            execution_time_ms=query.execution_time_ms,
        )
        
    except Exception as e:
        logger.error(f"Failed to execute query: {e}")
        raise HTTPException(
            status_code=http_status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process query: {str(e)}",
        )


@router.get(
    "/query/{query_id}",
    response_model=Query,
    status_code=http_status.HTTP_200_OK,
    summary="Get query by ID",
    description="Retrieve a specific query by its ID",
)
async def get_query(query_id: UUID) -> Query:
    """
    Get a query by ID.
    
    Args:
        query_id: Query UUID
        
    Returns:
        Query object
        
    Raises:
        HTTPException: If query not found
    """
    query = query_repo.get(str(query_id))
    
    if not query:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Query {query_id} not found",
        )
    
    return query


@router.get(
    "/query/session/{session_id}",
    response_model=QueryHistoryResponse,
    status_code=http_status.HTTP_200_OK,
    summary="Get queries by session",
    description="Retrieve all queries for a specific conversation session",
)
async def get_session_queries(
    session_id: UUID,
    page: int = 1,
    page_size: int = 50,
) -> QueryHistoryResponse:
    """
    Get all queries for a session.
    
    Args:
        session_id: Session UUID
        page: Page number (1-based)
        page_size: Number of items per page
        
    Returns:
        Query history response
    """
    from_ = (page - 1) * page_size
    
    queries, total = query_repo.get_by_session(
        session_id=session_id,
        size=page_size,
        from_=from_,
    )
    
    return QueryHistoryResponse(
        items=queries,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/query/recent",
    response_model=list[Query],
    status_code=http_status.HTTP_200_OK,
    summary="Get recent queries",
    description="Retrieve recent queries, optionally filtered by user",
)
async def get_recent_queries(
    user_id: Optional[str] = None,
    hours: int = 24,
    size: int = 20,
) -> list[Query]:
    """
    Get recent queries.
    
    Args:
        user_id: Optional user identifier
        hours: Number of hours to look back
        size: Maximum number of results
        
    Returns:
        List of recent queries
    """
    queries = query_repo.get_recent_queries(
        user_id=user_id,
        hours=hours,
        size=size,
    )
    
    return queries


@router.post(
    "/query/{query_id}/feedback",
    response_model=Query,
    status_code=http_status.HTTP_200_OK,
    summary="Provide feedback on query",
    description="Submit user feedback on a query result",
)
async def submit_feedback(
    query_id: UUID,
    request: FeedbackRequest,
) -> Query:
    """
    Submit feedback on a query.
    
    Args:
        query_id: Query UUID
        request: Feedback request
        
    Returns:
        Updated query
        
    Raises:
        HTTPException: If query not found
    """
    updated_query = query_repo.update_feedback(
        query_id=str(query_id),
        feedback=request.feedback,
        comment=request.comment,
    )
    
    if not updated_query:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail=f"Query {query_id} not found",
        )
    
    logger.info(f"Updated feedback for query {query_id}: {request.feedback}")
    
    return updated_query


@router.get(
    "/query/statistics",
    response_model=dict,
    status_code=http_status.HTTP_200_OK,
    summary="Get query statistics",
    description="Retrieve query analytics and statistics",
)
async def get_query_statistics(
    session_id: Optional[UUID] = None,
    hours: int = 24,
) -> dict:
    """
    Get query statistics.
    
    Args:
        session_id: Optional session to filter by
        hours: Number of hours to look back
        
    Returns:
        Query statistics
    """
    stats = query_repo.get_query_statistics(
        session_id=session_id,
        hours=hours,
    )
    
    return stats


# Made with Bob