#!/usr/bin/env python3
"""
Test database models and operations.

Usage:
    python scripts/test_db.py
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import select
from core.database import SessionLocal
from models import Project, Document, Chat, Message, UserSettings, DocumentStatus, MessageRole


async def test_models():
    """Test database models and operations."""
    print("Testing database models...\n")

    async with SessionLocal() as session:
        try:
            # Test 1: Query UserSettings
            print("1. Testing UserSettings...")
            result = await session.execute(
                select(UserSettings).where(UserSettings.user_id == "default_user")
            )
            settings = result.scalar_one_or_none()
            if settings:
                print(f"   ✓ Found user settings: {settings.default_llm_model}")
            else:
                print("   ✗ User settings not found")

            # Test 2: Create a Project
            print("\n2. Testing Project creation...")
            project = Project(
                name="Test Project",
                description="A test project for RAG chatbot",
                chroma_collection_name="test_project_collection"
            )
            session.add(project)
            await session.flush()  # Get the ID without committing
            print(f"   ✓ Created project with ID: {project.id}")

            # Test 3: Create a Document
            print("\n3. Testing Document creation...")
            document = Document(
                project_id=project.id,
                filename="test_doc.pdf",
                file_path="/storage/documents/test_doc.pdf",
                file_size=1024 * 50,  # 50 KB
                file_type="pdf",
                mime_type="application/pdf",
                status=DocumentStatus.COMPLETED,
                page_count=5,
                word_count=1000,
                chunk_count=10
            )
            session.add(document)
            await session.flush()
            print(f"   ✓ Created document with ID: {document.id}")
            print(f"   ✓ File size: {document.file_size_mb:.2f} MB")

            # Test 4: Create a Chat
            print("\n4. Testing Chat creation...")
            chat = Chat(
                project_id=project.id,
                title="Test Conversation"
            )
            session.add(chat)
            await session.flush()
            print(f"   ✓ Created chat with ID: {chat.id}")

            # Test 5: Create Messages
            print("\n5. Testing Message creation...")
            user_message = Message(
                chat_id=chat.id,
                role=MessageRole.USER,
                content="What is RAG?"
            )
            session.add(user_message)
            await session.flush()
            print(f"   ✓ Created user message with ID: {user_message.id}")

            assistant_message = Message(
                chat_id=chat.id,
                role=MessageRole.ASSISTANT,
                content="RAG stands for Retrieval-Augmented Generation...",
                model_name="llama3.2",
                token_count=50
            )
            session.add(assistant_message)
            await session.flush()
            print(f"   ✓ Created assistant message with ID: {assistant_message.id}")

            # Test 6: Query with Relationships
            print("\n6. Testing relationships...")
            result = await session.execute(
                select(Project).where(Project.id == project.id)
            )
            project_with_relations = result.scalar_one()
            print(f"   ✓ Project '{project_with_relations.name}' has:")
            print(f"     - {len(project_with_relations.documents)} document(s)")
            print(f"     - {len(project_with_relations.chats)} chat(s)")

            result = await session.execute(
                select(Chat).where(Chat.id == chat.id)
            )
            chat_with_messages = result.scalar_one()
            print(f"   ✓ Chat '{chat_with_messages.title}' has:")
            print(f"     - {len(chat_with_messages.messages)} message(s)")

            # Test 7: Update operations
            print("\n7. Testing update operations...")
            project.document_count = len(project_with_relations.documents)
            chat.message_count = len(chat_with_messages.messages)
            await session.flush()
            print(f"   ✓ Updated project document count: {project.document_count}")
            print(f"   ✓ Updated chat message count: {chat.message_count}")

            # Test 8: Soft delete
            print("\n8. Testing soft delete...")
            project.soft_delete()
            await session.flush()
            print(f"   ✓ Soft deleted project: {project.is_deleted}")

            # Don't commit - this is just a test
            await session.rollback()
            print("\n✓ All tests passed! (Changes rolled back)")

        except Exception as e:
            await session.rollback()
            print(f"\n✗ Test failed: {e}")
            import traceback
            traceback.print_exc()
            sys.exit(1)


async def main():
    """Run all tests."""
    print("=" * 60)
    print("Database Models Test Suite")
    print("=" * 60)
    print()
    await test_models()
    print()
    print("=" * 60)
    print("All database tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
