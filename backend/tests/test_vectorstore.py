"""
Tests for Vector Store functionality.

This test suite tests the ChromaDB integration including:
- Collection creation and management
- Document insertion and retrieval
- Similarity search
- Metadata filtering
- Collection per project isolation
"""

import pytest
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.vectorstore import vector_store


class TestBasicOperations:
    """Test basic vector store operations."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        # Setup
        yield
        # Teardown - cleanup test collections
        try:
            vector_store.delete_collection(1)
        except:
            pass

    def test_add_documents(self):
        """Test adding documents to vector store."""
        project_id = 1
        documents = [
            "This is a test document about machine learning.",
            "Python is a great programming language.",
            "Vector databases store embeddings efficiently."
        ]

        # Simple embeddings (normally these would come from an embedding model)
        embeddings = [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.2, 0.3, 0.4, 0.5, 0.6],
            [0.3, 0.4, 0.5, 0.6, 0.7]
        ]

        metadatas = [
            {"document_id": "doc1", "page": 1, "source": "test.pdf"},
            {"document_id": "doc2", "page": 1, "source": "test.pdf"},
            {"document_id": "doc3", "page": 2, "source": "test.pdf"}
        ]

        success = vector_store.add_documents(
            project_id=project_id,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        assert success is True

    def test_get_collection_count(self):
        """Test getting collection count."""
        project_id = 1
        documents = ["Test document"]
        embeddings = [[0.1, 0.2]]
        metadatas = [{"id": 1}]

        vector_store.add_documents(
            project_id=project_id,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        count = vector_store.get_collection_count(project_id)
        assert count == 1

    def test_search(self):
        """Test similarity search."""
        project_id = 1
        documents = [
            "Machine learning is fascinating",
            "Python programming is fun"
        ]
        embeddings = [
            [0.1, 0.2, 0.3],
            [0.4, 0.5, 0.6]
        ]
        metadatas = [{"doc": 1}, {"doc": 2}]

        vector_store.add_documents(
            project_id=project_id,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # Search with similar embedding to first document
        query_embedding = [0.15, 0.25, 0.35]
        results = vector_store.search(
            project_id=project_id,
            query_embedding=query_embedding,
            n_results=2
        )

        assert len(results['documents']) == 2
        assert 'distances' in results
        assert 'metadatas' in results


class TestMetadataFiltering:
    """Test metadata filtering functionality."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        yield
        try:
            vector_store.delete_collection(2)
        except:
            pass

    def test_filter_by_page(self):
        """Test filtering documents by page metadata."""
        project_id = 2
        documents = [
            "Document from page 1",
            "Another document from page 1",
            "Document from page 2"
        ]

        embeddings = [
            [0.1, 0.1, 0.1],
            [0.2, 0.2, 0.2],
            [0.3, 0.3, 0.3]
        ]

        metadatas = [
            {"page": 1, "type": "text"},
            {"page": 1, "type": "code"},
            {"page": 2, "type": "text"}
        ]

        vector_store.add_documents(
            project_id=project_id,
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas
        )

        # Search with metadata filter for page 1
        results = vector_store.search(
            project_id=project_id,
            query_embedding=[0.15, 0.15, 0.15],
            n_results=5,
            where={"page": 1}
        )

        assert len(results['documents']) == 2
        # Verify all results are from page 1
        for metadata in results['metadatas']:
            assert metadata['page'] == 1


class TestProjectIsolation:
    """Test project-based collection isolation."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        yield
        for project_id in [3, 4]:
            try:
                vector_store.delete_collection(project_id)
            except:
                pass

    def test_separate_collections(self):
        """Test that projects have separate collections."""
        # Add documents to project 3
        vector_store.add_documents(
            project_id=3,
            documents=["Project 3 document 1", "Project 3 document 2"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            metadatas=[{"project": 3}, {"project": 3}]
        )

        # Add documents to project 4
        vector_store.add_documents(
            project_id=4,
            documents=["Project 4 document 1", "Project 4 document 2"],
            embeddings=[[0.5, 0.6], [0.7, 0.8]],
            metadatas=[{"project": 4}, {"project": 4}]
        )

        # Check isolation
        count_p3 = vector_store.get_collection_count(3)
        count_p4 = vector_store.get_collection_count(4)

        assert count_p3 == 2
        assert count_p4 == 2

        # Search in project 3 should only return project 3 documents
        results_p3 = vector_store.search(
            project_id=3,
            query_embedding=[0.2, 0.3],
            n_results=5
        )

        assert len(results_p3['documents']) == 2
        assert "Project 3" in results_p3['documents'][0]


class TestDeleteOperations:
    """Test delete operations."""

    @pytest.fixture(autouse=True)
    def setup_and_teardown(self):
        """Setup and teardown for each test."""
        yield
        try:
            vector_store.delete_collection(5)
        except:
            pass

    def test_delete_by_id(self):
        """Test deleting documents by ID."""
        project_id = 5

        # Add documents with specific IDs
        vector_store.add_documents(
            project_id=project_id,
            documents=["Doc to keep", "Doc to delete", "Another doc to keep"],
            embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
            ids=["keep1", "delete1", "keep2"],
            metadatas=[{"status": "keep"}, {"status": "delete"}, {"status": "keep"}]
        )

        initial_count = vector_store.get_collection_count(project_id)
        assert initial_count == 3

        # Delete by ID
        vector_store.delete_documents(project_id=project_id, ids=["delete1"])

        after_delete_count = vector_store.get_collection_count(project_id)
        assert after_delete_count == 2

    def test_delete_by_metadata(self):
        """Test deleting documents by metadata filter."""
        project_id = 5

        vector_store.add_documents(
            project_id=project_id,
            documents=["Keep doc", "Delete doc"],
            embeddings=[[0.1, 0.2], [0.3, 0.4]],
            metadatas=[{"status": "keep"}, {"status": "delete"}]
        )

        # Delete by metadata
        vector_store.delete_documents(
            project_id=project_id,
            where={"status": "delete"}
        )

        # Verify only one document remains
        count = vector_store.get_collection_count(project_id)
        assert count == 1


class TestCollectionManagement:
    """Test collection management operations."""

    def test_list_collections(self):
        """Test listing all collections."""
        # Create a test collection
        test_project_id = 99
        vector_store.add_documents(
            project_id=test_project_id,
            documents=["Test"],
            embeddings=[[0.1]],
            metadatas=[{}]
        )

        collections = vector_store.list_collections()
        assert isinstance(collections, list)
        assert len(collections) > 0

        # Check that our test collection is in the list
        collection_names = [col['name'] for col in collections]
        assert f"project_{test_project_id}" in collection_names

        # Cleanup
        vector_store.delete_collection(test_project_id)

    def test_delete_collection(self):
        """Test deleting a collection."""
        project_id = 100

        # Create collection
        vector_store.add_documents(
            project_id=project_id,
            documents=["Test"],
            embeddings=[[0.1]],
            metadatas=[{}]
        )

        # Verify it exists
        count_before = vector_store.get_collection_count(project_id)
        assert count_before == 1

        # Delete collection
        success = vector_store.delete_collection(project_id)
        assert success is True

        # Verify it's gone
        count_after = vector_store.get_collection_count(project_id)
        assert count_after == 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
