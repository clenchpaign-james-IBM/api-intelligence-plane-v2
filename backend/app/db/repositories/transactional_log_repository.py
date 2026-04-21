"""
Transactional Log Repository

Provides CRUD operations and query helpers for TransactionalLog entities.
Supports daily index rotation for raw analytics events and drill-down queries.
"""

import logging
from datetime import datetime
from typing import Optional

from app.db.repositories.base import BaseRepository
from app.models.base.transaction import TransactionalLog

logger = logging.getLogger(__name__)


class TransactionalLogRepository(BaseRepository[TransactionalLog]):
    """Repository for raw transactional log events."""

    def __init__(self):
        """Initialize the transactional log repository."""
        super().__init__(index_name="transactional-logs-*", model_class=TransactionalLog)

    def _get_index_name(self, timestamp: datetime) -> str:
        """
        Get the daily index name for a specific timestamp.

        Args:
            timestamp: Event timestamp

        Returns:
            Daily index name in format transactional-logs-YYYY.MM.DD
        """
        return f"transactional-logs-{timestamp.strftime('%Y.%m.%d')}"

    def create(self, document: TransactionalLog, doc_id: Optional[str] = None) -> TransactionalLog:
        """
        Create a new transactional log document in the appropriate daily index.
        """
        original_index = self.index_name
        event_time = datetime.utcfromtimestamp(document.timestamp / 1000)
        self.index_name = self._get_index_name(event_time)

        try:
            return super().create(document, doc_id)
        finally:
            self.index_name = original_index

    def bulk_create(self, documents: list[TransactionalLog]) -> int:
        """
        Bulk create transactional logs grouped by daily index.

        Args:
            documents: Transactional log documents to persist

        Returns:
            Number of successfully created documents
        """
        if not documents:
            return 0

        created_count = 0
        original_index = self.index_name

        try:
            grouped_documents: dict[str, list[TransactionalLog]] = {}
            for document in documents:
                event_time = datetime.utcfromtimestamp(document.timestamp / 1000)
                index_name = self._get_index_name(event_time)
                grouped_documents.setdefault(index_name, []).append(document)

            for index_name, daily_documents in grouped_documents.items():
                self.index_name = index_name
                created_count += super().bulk_create(daily_documents)

            return created_count
        finally:
            self.index_name = original_index

    def find_logs(
        self,
        gateway_id: Optional[str] = None,
        api_id: Optional[str] = None,
        application_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        size: int = 100,
        from_: int = 0,
    ) -> tuple[list[TransactionalLog], int]:
        """
        Query transactional logs with common analytics filters.

        Args:
            gateway_id: Optional gateway filter
            api_id: Optional API filter
            application_id: Optional application filter
            start_time: Optional start time
            end_time: Optional end time
            size: Number of results
            from_: Offset for pagination

        Returns:
            Matching logs and total count
        """
        must_clauses: list[dict] = []

        if gateway_id:
            must_clauses.append({"term": {"gateway_id": gateway_id}})
        if api_id:
            must_clauses.append({"term": {"api_id": api_id}})
        if application_id:
            must_clauses.append({"term": {"client_id": application_id}})

        if start_time or end_time:
            range_query: dict[str, str] = {}
            if start_time:
                range_query["gte"] = str(int(start_time.timestamp() * 1000))
            if end_time:
                range_query["lte"] = str(int(end_time.timestamp() * 1000))
            must_clauses.append({"range": {"timestamp": range_query}})

        query = {"bool": {"must": must_clauses}} if must_clauses else {"match_all": {}}
        sort = [{"timestamp": {"order": "desc"}}]

        original_index = self.index_name
        self.index_name = "transactional-logs-*"

        try:
            return self.search(query, size=size, from_=from_, sort=sort)
        finally:
            self.index_name = original_index

# Made with Bob
