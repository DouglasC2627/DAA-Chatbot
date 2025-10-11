#!/usr/bin/env python3
"""
Test script for Vector Store functionality.

This script tests the ChromaDB integration including:
- Collection creation and management
- Document insertion and retrieval
- Similarity search
- Metadata filtering
- Collection per project isolation
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from core.vectorstore import vector_store


def test_basic_operations():
    """Test basic vector store operations."""
    print("=" * 60)
    print("TEST 1: Basic Operations")
    print("=" * 60)

    # Test data
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

    # Test 1: Add documents
    print("\n1. Adding documents to project 1...")
    success = vector_store.add_documents(
        project_id=project_id,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print(f"   ✓ Documents added: {success}")

    # Test 2: Get collection count
    count = vector_store.get_collection_count(project_id)
    print(f"   ✓ Collection count: {count}")

    # Test 3: Search
    print("\n2. Searching for similar documents...")
    query_embedding = [0.15, 0.25, 0.35, 0.45, 0.55]
    results = vector_store.search(
        project_id=project_id,
        query_embedding=query_embedding,
        n_results=2
    )
    print(f"   ✓ Found {len(results['documents'])} results:")
    for i, doc in enumerate(results['documents']):
        print(f"      {i+1}. {doc[:50]}... (distance: {results['distances'][i]:.4f})")


def test_metadata_filtering():
    """Test metadata filtering."""
    print("\n" + "=" * 60)
    print("TEST 2: Metadata Filtering")
    print("=" * 60)

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

    # Add documents
    print("\n1. Adding documents with metadata...")
    vector_store.add_documents(
        project_id=project_id,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas
    )
    print("   ✓ Documents added")

    # Search with metadata filter
    print("\n2. Searching with metadata filter (page=1)...")
    results = vector_store.search(
        project_id=project_id,
        query_embedding=[0.15, 0.15, 0.15],
        n_results=5,
        where={"page": 1}
    )
    print(f"   ✓ Found {len(results['documents'])} results from page 1:")
    for i, doc in enumerate(results['documents']):
        print(f"      {i+1}. {doc} (page: {results['metadatas'][i]['page']})")


def test_project_isolation():
    """Test project-based collection isolation."""
    print("\n" + "=" * 60)
    print("TEST 3: Project Isolation")
    print("=" * 60)

    # Add documents to project 3
    print("\n1. Adding documents to project 3...")
    vector_store.add_documents(
        project_id=3,
        documents=["Project 3 document 1", "Project 3 document 2"],
        embeddings=[[0.1, 0.2], [0.3, 0.4]],
        metadatas=[{"project": 3}, {"project": 3}]
    )

    # Add documents to project 4
    print("2. Adding documents to project 4...")
    vector_store.add_documents(
        project_id=4,
        documents=["Project 4 document 1", "Project 4 document 2"],
        embeddings=[[0.5, 0.6], [0.7, 0.8]],
        metadatas=[{"project": 4}, {"project": 4}]
    )

    # Check isolation
    count_p3 = vector_store.get_collection_count(3)
    count_p4 = vector_store.get_collection_count(4)

    print(f"\n   ✓ Project 3 has {count_p3} documents")
    print(f"   ✓ Project 4 has {count_p4} documents")

    # Search in project 3
    results_p3 = vector_store.search(
        project_id=3,
        query_embedding=[0.2, 0.3],
        n_results=5
    )
    print(f"\n   ✓ Searching in project 3: found {len(results_p3['documents'])} documents")
    for doc in results_p3['documents']:
        print(f"      - {doc}")


def test_delete_operations():
    """Test delete operations."""
    print("\n" + "=" * 60)
    print("TEST 4: Delete Operations")
    print("=" * 60)

    project_id = 5

    # Add documents with IDs
    print("\n1. Adding documents with specific IDs...")
    vector_store.add_documents(
        project_id=project_id,
        documents=["Doc to keep", "Doc to delete", "Another doc to keep"],
        embeddings=[[0.1, 0.2], [0.3, 0.4], [0.5, 0.6]],
        ids=["keep1", "delete1", "keep2"],
        metadatas=[{"status": "keep"}, {"status": "delete"}, {"status": "keep"}]
    )

    initial_count = vector_store.get_collection_count(project_id)
    print(f"   ✓ Initial count: {initial_count}")

    # Delete by ID
    print("\n2. Deleting document by ID...")
    vector_store.delete_documents(project_id=project_id, ids=["delete1"])

    after_delete_count = vector_store.get_collection_count(project_id)
    print(f"   ✓ Count after delete: {after_delete_count}")

    # Verify remaining documents
    results = vector_store.search(
        project_id=project_id,
        query_embedding=[0.3, 0.4],
        n_results=5
    )
    print(f"\n   ✓ Remaining documents:")
    for doc in results['documents']:
        print(f"      - {doc}")


def test_list_collections():
    """Test listing all collections."""
    print("\n" + "=" * 60)
    print("TEST 5: List All Collections")
    print("=" * 60)

    collections = vector_store.list_collections()
    print(f"\n✓ Total collections: {len(collections)}")
    for col in collections:
        print(f"   - {col['name']}: {col['count']} documents")


def cleanup():
    """Clean up test data."""
    print("\n" + "=" * 60)
    print("CLEANUP: Removing test collections")
    print("=" * 60)

    for project_id in [1, 2, 3, 4, 5]:
        success = vector_store.delete_collection(project_id)
        if success:
            print(f"   ✓ Deleted collection for project {project_id}")

    print("\n✓ Cleanup complete")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("CHROMADB VECTOR STORE TEST SUITE")
    print("=" * 60)

    try:
        test_basic_operations()
        test_metadata_filtering()
        test_project_isolation()
        test_delete_operations()
        test_list_collections()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED!")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Ask user if they want to cleanup
        print("\n")
        response = input("Do you want to clean up test collections? (y/n): ").strip().lower()
        if response == 'y':
            cleanup()
        else:
            print("\n✓ Test collections preserved for inspection")

    print("\n✓ Test suite complete!\n")


if __name__ == "__main__":
    main()
