"""
Vector Store Module

This module provides ChromaDB integration for storing and retrieving document embeddings.
Supports project-based isolation via separate collections and metadata filtering.
"""

from typing import List, Dict, Any, Optional
import uuid
from pathlib import Path

import chromadb
from chromadb.config import Settings

from .config import settings


class VectorStore:
    """
    Manages ChromaDB operations for document embeddings.

    Features:
    - Project-based collection isolation
    - Vector storage and retrieval
    - Metadata filtering
    - Similarity search with configurable top-k
    """

    def __init__(self):
        """Initialize ChromaDB client with persistent storage."""
        # Ensure storage directory exists
        Path(settings.CHROMA_PERSIST_DIR).mkdir(parents=True, exist_ok=True)

        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(
            path=settings.CHROMA_PERSIST_DIR,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )

    def get_or_create_collection(self, project_id: int) -> chromadb.Collection:
        """
        Get or create a collection for a specific project.

        Args:
            project_id: The project ID to create/get collection for

        Returns:
            ChromaDB collection instance
        """
        collection_name = f"project_{project_id}"

        # ChromaDB collection names must be 3-63 characters and contain only alphanumeric, underscore, or hyphen
        collection_name = collection_name.replace(" ", "_").lower()

        collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"project_id": str(project_id)}
        )

        return collection

    def delete_collection(self, project_id: int) -> bool:
        """
        Delete a project's collection.

        Args:
            project_id: The project ID whose collection to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = f"project_{project_id}"
            collection_name = collection_name.replace(" ", "_").lower()
            self.client.delete_collection(name=collection_name)
            return True
        except Exception as e:
            print(f"Error deleting collection: {e}")
            return False

    def add_documents(
        self,
        project_id: int,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: Optional[List[Dict[str, Any]]] = None,
        ids: Optional[List[str]] = None
    ) -> bool:
        """
        Add documents and their embeddings to the vector store.

        Args:
            project_id: The project ID
            documents: List of document texts (chunks)
            embeddings: List of embedding vectors
            metadatas: Optional list of metadata dicts for each document
            ids: Optional list of unique IDs for each document

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(project_id)

            # Generate IDs if not provided
            if ids is None:
                ids = [str(uuid.uuid4()) for _ in documents]

            # Add default metadata if not provided
            if metadatas is None:
                metadatas = [{"chunk_index": i} for i in range(len(documents))]

            collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )

            return True
        except Exception as e:
            print(f"Error adding documents: {e}")
            return False

    def search(
        self,
        project_id: int,
        query_embedding: List[float],
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Search for similar documents using vector similarity.

        Args:
            project_id: The project ID
            query_embedding: The query embedding vector
            n_results: Number of results to return (default: 5)
            where: Optional metadata filter (e.g., {"document_id": "123"})
            where_document: Optional document content filter

        Returns:
            Dictionary containing ids, documents, metadatas, and distances
        """
        try:
            collection = self.get_or_create_collection(project_id)

            results = collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=where,
                where_document=where_document
            )

            # Flatten results from list of lists to single lists
            return {
                "ids": results["ids"][0] if results["ids"] else [],
                "documents": results["documents"][0] if results["documents"] else [],
                "metadatas": results["metadatas"][0] if results["metadatas"] else [],
                "distances": results["distances"][0] if results["distances"] else []
            }
        except Exception as e:
            print(f"Error searching documents: {e}")
            return {
                "ids": [],
                "documents": [],
                "metadatas": [],
                "distances": []
            }

    def delete_documents(
        self,
        project_id: int,
        ids: Optional[List[str]] = None,
        where: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Delete documents from the vector store.

        Args:
            project_id: The project ID
            ids: Optional list of document IDs to delete
            where: Optional metadata filter for deletion

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(project_id)

            if ids:
                collection.delete(ids=ids)
            elif where:
                collection.delete(where=where)
            else:
                raise ValueError("Either ids or where filter must be provided")

            return True
        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False

    def get_collection_count(self, project_id: int) -> int:
        """
        Get the number of documents in a project's collection.

        Args:
            project_id: The project ID

        Returns:
            Number of documents in the collection
        """
        try:
            collection = self.get_or_create_collection(project_id)
            return collection.count()
        except Exception as e:
            print(f"Error getting collection count: {e}")
            return 0

    def list_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections in the vector store.

        Returns:
            List of collection information
        """
        try:
            collections = self.client.list_collections()
            return [
                {
                    "name": col.name,
                    "metadata": col.metadata,
                    "count": col.count()
                }
                for col in collections
            ]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []

    def update_document(
        self,
        project_id: int,
        document_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Update a document in the vector store.

        Args:
            project_id: The project ID
            document_id: The document ID to update
            document: Optional new document text
            embedding: Optional new embedding vector
            metadata: Optional new metadata

        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.get_or_create_collection(project_id)

            collection.update(
                ids=[document_id],
                documents=[document] if document else None,
                embeddings=[embedding] if embedding else None,
                metadatas=[metadata] if metadata else None
            )

            return True
        except Exception as e:
            print(f"Error updating document: {e}")
            return False

    def reset_all(self) -> bool:
        """
        Reset the entire vector store (delete all collections).
        WARNING: This will delete all data!

        Returns:
            True if successful, False otherwise
        """
        try:
            self.client.reset()
            return True
        except Exception as e:
            print(f"Error resetting vector store: {e}")
            return False


# Create a global vector store instance
vector_store = VectorStore()
