"""
Base Repository Pattern

Provides abstract base class for all repository implementations with
common CRUD operations and OpenSearch query patterns.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, List, Optional, TypeVar
from datetime import datetime

from opensearchpy import OpenSearch, exceptions
from pydantic import BaseModel

from app.db.client import get_client

logger = logging.getLogger(__name__)

# Type variable for Pydantic models
T = TypeVar("T", bound=BaseModel)


class BaseRepository(ABC, Generic[T]):
    """
    Abstract base repository for OpenSearch operations.
    
    Provides common CRUD operations and query patterns that can be
    inherited by specific repository implementations.
    
    Type Parameters:
        T: The Pydantic model type for this repository
    """
    
    def __init__(self, index_name: str, model_class: type[T]):
        """
        Initialize the repository.
        
        Args:
            index_name: Name of the OpenSearch index
            model_class: Pydantic model class for type validation
        """
        self.index_name = index_name
        self.model_class = model_class
        self._client: Optional[OpenSearch] = None
    
    @property
    def client(self) -> OpenSearch:
        """Get the OpenSearch client instance."""
        if self._client is None:
            self._client = get_client()
        return self._client
    
    def create(self, document: T, doc_id: Optional[str] = None) -> T:
        """
        Create a new document in the index.
        
        Args:
            document: Pydantic model instance to create
            doc_id: Optional document ID (generated if not provided)
            
        Returns:
            The created document with ID
            
        Raises:
            exceptions.ConflictError: If document with ID already exists
        """
        try:
            doc_dict = document.model_dump(mode="json", exclude_none=True)
            
            # Add timestamps if not present
            if "created_at" not in doc_dict:
                doc_dict["created_at"] = datetime.utcnow().isoformat()
            if "updated_at" not in doc_dict:
                doc_dict["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.client.index(
                index=self.index_name,
                body=doc_dict,
                id=doc_id,
                refresh=True,
            )
            
            # Update document with generated ID
            if hasattr(document, "id") and not document.id:
                doc_dict["id"] = response["_id"]
            
            logger.info(
                f"Created document in {self.index_name}: {response['_id']}"
            )
            return self.model_class(**doc_dict)
            
        except exceptions.ConflictError:
            logger.error(f"Document with ID {doc_id} already exists")
            raise
        except Exception as e:
            logger.error(f"Failed to create document: {e}")
            raise
    
    def get(self, doc_id: str) -> Optional[T]:
        """
        Get a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document if found, None otherwise
        """
        try:
            response = self.client.get(
                index=self.index_name,
                id=doc_id,
            )
            return self.model_class(**response["_source"])
            
        except exceptions.NotFoundError:
            logger.warning(f"Document not found: {doc_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            raise
    
    def update(self, doc_id: str, updates: Dict[str, Any]) -> Optional[T]:
        """
        Update a document by ID.
        
        Args:
            doc_id: Document ID
            updates: Dictionary of fields to update
            
        Returns:
            Updated document if found, None otherwise
        """
        try:
            # Add updated_at timestamp
            updates["updated_at"] = datetime.utcnow().isoformat()
            
            response = self.client.update(
                index=self.index_name,
                id=doc_id,
                body={"doc": updates},
                refresh=True,
            )
            
            logger.info(f"Updated document in {self.index_name}: {doc_id}")
            
            # Fetch and return updated document
            return self.get(doc_id)
            
        except exceptions.NotFoundError:
            logger.warning(f"Document not found for update: {doc_id}")
            return None
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
            raise
    
    def delete(self, doc_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            self.client.delete(
                index=self.index_name,
                id=doc_id,
                refresh=True,
            )
            logger.info(f"Deleted document from {self.index_name}: {doc_id}")
            return True
            
        except exceptions.NotFoundError:
            logger.warning(f"Document not found for deletion: {doc_id}")
            return False
        except Exception as e:
            logger.error(f"Failed to delete document {doc_id}: {e}")
            raise
    
    def search(
        self,
        query: Dict[str, Any],
        size: int = 10,
        from_: int = 0,
        sort: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[List[T], int]:
        """
        Search documents using OpenSearch query DSL.
        
        Args:
            query: OpenSearch query DSL
            size: Number of results to return
            from_: Offset for pagination
            sort: Sort criteria
            
        Returns:
            Tuple of (list of documents, total count)
        """
        try:
            body: Dict[str, Any] = {"query": query, "size": size, "from": from_}
            
            if sort:
                body["sort"] = sort
            
            response = self.client.search(
                index=self.index_name,
                body=body,
            )
            
            documents = [
                self.model_class(**hit["_source"])
                for hit in response["hits"]["hits"]
            ]
            total = response["hits"]["total"]["value"]
            
            return documents, total
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise
    
    def list_all(
        self,
        size: int = 100,
        from_: int = 0,
        sort: Optional[List[Dict[str, Any]]] = None,
    ) -> tuple[List[T], int]:
        """
        List all documents in the index.
        
        Args:
            size: Number of results to return
            from_: Offset for pagination
            sort: Sort criteria
            
        Returns:
            Tuple of (list of documents, total count)
        """
        query = {"match_all": {}}
        return self.search(query, size=size, from_=from_, sort=sort)
    
    def count(self, query: Optional[Dict[str, Any]] = None) -> int:
        """
        Count documents matching a query.
        
        Args:
            query: OpenSearch query DSL (counts all if None)
            
        Returns:
            Number of matching documents
        """
        try:
            body = {"query": query} if query else None
            response = self.client.count(
                index=self.index_name,
                body=body,
            )
            return response["count"]
            
        except Exception as e:
            logger.error(f"Count failed: {e}")
            raise
    
    def exists(self, doc_id: str) -> bool:
        """
        Check if a document exists.
        
        Args:
            doc_id: Document ID
            
        Returns:
            True if document exists
        """
        try:
            return self.client.exists(
                index=self.index_name,
                id=doc_id,
            )
        except Exception as e:
            logger.error(f"Exists check failed for {doc_id}: {e}")
            return False
    
    def bulk_create(self, documents: List[T]) -> int:
        """
        Bulk create multiple documents.
        
        Args:
            documents: List of Pydantic model instances
            
        Returns:
            Number of successfully created documents
        """
        try:
            from opensearchpy import helpers
            
            actions = []
            for doc in documents:
                doc_dict = doc.model_dump(mode="json", exclude_none=True)
                
                # Add timestamps
                if "created_at" not in doc_dict:
                    doc_dict["created_at"] = datetime.utcnow().isoformat()
                if "updated_at" not in doc_dict:
                    doc_dict["updated_at"] = datetime.utcnow().isoformat()
                
                action = {
                    "_index": self.index_name,
                    "_source": doc_dict,
                }
                
                # Add ID if present
                if hasattr(doc, "id") and doc.id:
                    action["_id"] = doc.id
                
                actions.append(action)
            
            success, failed = helpers.bulk(
                self.client,
                actions,
                refresh=True,
            )
            
            logger.info(
                f"Bulk created {success} documents in {self.index_name}, "
                f"{failed} failed"
            )
            return success
            
        except Exception as e:
            logger.error(f"Bulk create failed: {e}")
            raise

# Made with Bob
