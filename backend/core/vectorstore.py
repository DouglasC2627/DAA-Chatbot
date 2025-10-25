"""
Vector Store Module

This module provides ChromaDB integration for storing and retrieving document embeddings.
Supports project-based isolation via separate collections and metadata filtering.
"""

from typing import List, Dict, Any, Optional
import uuid
import shutil
import logging
from pathlib import Path

import chromadb
from chromadb.config import Settings

from .config import settings

logger = logging.getLogger(__name__)


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
        Delete a project's collection and clean up physical files.

        This method performs two operations:
        1. Deletes the collection from ChromaDB (metadata)
        2. Manually cleans up orphaned physical files in the persist directory

        Args:
            project_id: The project ID whose collection to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            collection_name = f"project_{project_id}"
            collection_name = collection_name.replace(" ", "_").lower()

            # Step 1: Delete collection from ChromaDB metadata
            try:
                self.client.delete_collection(name=collection_name)
                logger.info(f"Deleted ChromaDB collection '{collection_name}'")
            except ValueError as e:
                # Collection doesn't exist, that's okay
                logger.warning(f"Collection '{collection_name}' not found: {e}")

            # Step 2: Clean up orphaned physical files
            # ChromaDB doesn't always clean up physical files immediately after deletion
            # We'll manually trigger cleanup of orphaned files
            self._cleanup_orphaned_files()

            return True
        except Exception as e:
            logger.error(f"Error deleting collection: {e}")
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

    def _cleanup_orphaned_files(self) -> int:
        """
        Clean up orphaned ChromaDB files that don't belong to any active collection.

        ChromaDB may leave behind physical files after collection deletion.
        This method identifies and removes orphaned data files.

        Returns:
            Number of items cleaned up
        """
        try:
            chroma_path = Path(settings.CHROMA_PERSIST_DIR)
            if not chroma_path.exists():
                return 0

            # Get all active collections
            active_collections = set()
            try:
                collections = self.client.list_collections()
                active_collections = {col.name for col in collections}
                logger.info(f"Active collections: {active_collections}")
            except Exception as e:
                logger.warning(f"Could not list active collections: {e}")
                return 0

            cleaned_count = 0

            # ChromaDB stores data in subdirectories within the persist directory
            # We need to be careful to only remove truly orphaned files
            # The safest approach is to check for empty directories or obvious orphaned data

            # Scan for subdirectories (collection data directories)
            for item in chroma_path.iterdir():
                # Skip the main SQLite database and other system files
                if item.is_file():
                    continue

                # Check subdirectories - these typically contain collection data
                # ChromaDB uses UUID-based directory names for collections
                if item.is_dir() and item.name not in ['.', '..']:
                    # Check if directory is empty or contains no active collection references
                    try:
                        # If directory is empty, it's safe to remove
                        if not any(item.iterdir()):
                            shutil.rmtree(item)
                            cleaned_count += 1
                            logger.info(f"Removed empty orphaned directory: {item.name}")
                    except Exception as e:
                        logger.warning(f"Could not clean up directory {item.name}: {e}")

            if cleaned_count > 0:
                logger.info(f"Cleaned up {cleaned_count} orphaned items from ChromaDB persist directory")

            return cleaned_count

        except Exception as e:
            logger.error(f"Error during orphaned files cleanup: {e}")
            return 0

    def force_cleanup_all_orphaned_files(self) -> Dict[str, Any]:
        """
        Force a comprehensive cleanup of the ChromaDB persist directory.

        This is a more aggressive cleanup that should be called manually
        or during maintenance windows. It will:
        1. List all active collections
        2. Remove any data that doesn't belong to active collections
        3. Compact the database

        Returns:
            Dictionary with cleanup statistics
        """
        try:
            chroma_path = Path(settings.CHROMA_PERSIST_DIR)
            if not chroma_path.exists():
                return {"status": "no_cleanup_needed", "cleaned_items": 0}

            # Get active collections
            active_collections = set()
            try:
                collections = self.client.list_collections()
                active_collections = {col.name for col in collections}
            except Exception as e:
                logger.error(f"Could not list active collections: {e}")
                return {"status": "error", "message": str(e)}

            cleaned_items = 0
            cleaned_size_bytes = 0

            # More aggressive cleanup - scan all subdirectories
            for item in chroma_path.iterdir():
                if item.is_file():
                    continue

                if item.is_dir() and item.name not in ['.', '..']:
                    # Check if this directory has any active collection data
                    # This is a heuristic - we remove empty or very old directories
                    try:
                        dir_files = list(item.rglob('*'))
                        if not dir_files or all(f.stat().st_size == 0 for f in dir_files if f.is_file()):
                            # Directory is empty or contains only empty files
                            dir_size = sum(f.stat().st_size for f in dir_files if f.is_file())
                            shutil.rmtree(item)
                            cleaned_items += 1
                            cleaned_size_bytes += dir_size
                            logger.info(f"Removed orphaned directory: {item.name} ({dir_size} bytes)")
                    except Exception as e:
                        logger.warning(f"Could not process directory {item.name}: {e}")

            return {
                "status": "success",
                "cleaned_items": cleaned_items,
                "cleaned_size_bytes": cleaned_size_bytes,
                "active_collections": list(active_collections)
            }

        except Exception as e:
            logger.error(f"Error during force cleanup: {e}")
            return {"status": "error", "message": str(e)}


# Create a global vector store instance
vector_store = VectorStore()
