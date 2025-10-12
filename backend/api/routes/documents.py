"""
Documents API routes.

Endpoints:
- POST /api/projects/{project_id}/documents - Upload and process document
- GET /api/projects/{project_id}/documents - List documents for a project
- GET /api/documents/{document_id} - Get document details
- DELETE /api/documents/{document_id} - Delete a document
- GET /api/documents/{document_id}/download - Download document file
"""

import logging
from typing import List, Optional
from pathlib import Path
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
    UploadFile,
    File,
    BackgroundTasks
)
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from core.database import get_db
from core.config import settings
from core.embeddings import embedding_service
from core.vectorstore import vector_store
from core.chunking import chunk_text
from models.document import Document, DocumentType, DocumentStatus
from models.project import Project
from services.document_processor import DocumentProcessor, DocumentProcessingError
from services.file_storage import FileStorageService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["documents"])

# Initialize services
document_processor = DocumentProcessor()
file_storage = FileStorageService(settings.UPLOAD_DIR)


# Request/Response Models
class DocumentResponse(BaseModel):
    """Response model for document details."""
    id: int
    project_id: int
    filename: str
    file_type: str
    file_size: int
    status: str
    page_count: Optional[int] = None
    word_count: Optional[int] = None
    chunk_count: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str

    class Config:
        from_attributes = True


class UploadDocumentResponse(BaseModel):
    """Response model for document upload."""
    document: DocumentResponse
    message: str


# Helper functions
async def process_document_background(
    document_id: int,
    file_path: Path,
    project_id: int
):
    """
    Background task to process uploaded document.

    This function:
    1. Extracts text from the document
    2. Chunks the text
    3. Generates embeddings
    4. Stores embeddings in vector store
    5. Updates document status

    Args:
        document_id: Document ID
        file_path: Path to uploaded file
        project_id: Project ID
    """
    from core.database import SessionLocal

    try:
        logger.info(f"Starting background processing for document {document_id}")

        # Get database session
        async with SessionLocal() as db:
            # Get document
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            document = result.scalar_one_or_none()

            if not document:
                logger.error(f"Document {document_id} not found")
                return

            # Update status to processing
            document.status = DocumentStatus.PROCESSING
            await db.commit()

            try:
                # Extract text from document
                with open(file_path, 'rb') as f:
                    result = document_processor.process_file(f, file_path.name)

                # Update document metadata
                document.page_count = result.page_count
                document.word_count = result.word_count

                # Chunk the text
                chunks = chunk_text(
                    text=result.text,
                    chunk_size=1000,  # Default chunk size
                    chunk_overlap=200  # Default overlap
                )

                document.chunk_count = len(chunks)
                logger.info(f"Document {document_id} split into {len(chunks)} chunks")

                # Generate embeddings for chunks
                chunk_texts = [chunk['text'] for chunk in chunks]
                embeddings = embedding_service.generate_embeddings_batch(
                    texts=chunk_texts,
                    batch_size=10
                )

                # Filter out empty embeddings
                valid_data = [
                    (text, emb, meta)
                    for text, emb, meta in zip(chunk_texts, embeddings, chunks)
                    if emb  # Only include non-empty embeddings
                ]

                if not valid_data:
                    raise DocumentProcessingError("No valid embeddings generated")

                valid_texts, valid_embeddings, valid_chunks = zip(*valid_data)

                # Prepare metadata for vector store
                metadatas = [
                    {
                        'document_id': document_id,
                        'chunk_index': i,
                        'start_char': chunk.get('start', 0),
                        'end_char': chunk.get('end', 0),
                        'filename': document.filename
                    }
                    for i, chunk in enumerate(valid_chunks)
                ]

                # Generate unique IDs for chunks
                chunk_ids = [
                    f"{document_id}_chunk_{i}"
                    for i in range(len(valid_texts))
                ]

                # Store in vector database
                success = vector_store.add_documents(
                    project_id=project_id,
                    documents=list(valid_texts),
                    embeddings=list(valid_embeddings),
                    metadatas=metadatas,
                    ids=chunk_ids
                )

                if not success:
                    raise DocumentProcessingError("Failed to store embeddings in vector store")

                # Update document status to completed
                document.status = DocumentStatus.COMPLETED
                await db.commit()

                logger.info(
                    f"Successfully processed document {document_id}: "
                    f"{len(chunks)} chunks, {document.word_count} words"
                )

            except Exception as e:
                logger.error(f"Document processing failed for {document_id}: {str(e)}")

                # Update document status to failed
                document.status = DocumentStatus.FAILED
                document.error_message = str(e)
                await db.commit()

    except Exception as e:
        logger.error(f"Background processing error for document {document_id}: {str(e)}")


# Endpoints

@router.post(
    "/projects/{project_id}/documents",
    response_model=UploadDocumentResponse,
    status_code=status.HTTP_201_CREATED
)
async def upload_document(
    project_id: int,
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload and process a document.

    The document is uploaded immediately and processed in the background.
    Check the document status to see when processing is complete.

    Args:
        project_id: Project ID
        file: Uploaded file
        background_tasks: Background tasks manager
        db: Database session

    Returns:
        Document details and upload message

    Raises:
        HTTPException: If upload fails or file type not supported
    """
    try:
        # Verify project exists
        result = await db.execute(
            select(Project).where(Project.id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Project {project_id} not found"
            )

        # Validate file type
        try:
            doc_type = document_processor.get_document_type(file.filename)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file type: {file.filename}"
            )

        # Validate file size
        file_size = 0
        content = await file.read()
        file_size = len(content)

        if file_size > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"File size ({file_size} bytes) exceeds maximum allowed size ({settings.MAX_FILE_SIZE} bytes)"
            )

        # Generate unique filename to prevent collisions
        file_extension = Path(file.filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"

        # Save file to storage
        file_path = await file_storage.save_file(
            content=content,
            filename=unique_filename,
            project_id=project_id
        )

        # Create document record
        document = Document(
            project_id=project_id,
            filename=file.filename,  # Original filename
            file_path=str(file_path),  # Stored path
            file_type=doc_type,
            file_size=file_size,
            status=DocumentStatus.PENDING
        )

        db.add(document)
        await db.commit()
        await db.refresh(document)

        # Schedule background processing
        background_tasks.add_task(
            process_document_background,
            document_id=document.id,
            file_path=file_path,
            project_id=project_id
        )

        logger.info(
            f"Uploaded document {document.id} ({file.filename}) "
            f"to project {project_id}, scheduled for processing"
        )

        return UploadDocumentResponse(
            document=DocumentResponse(
                id=document.id,
                project_id=document.project_id,
                filename=document.filename,
                file_type=document.file_type.value,
                file_size=document.file_size,
                status=document.status.value,
                page_count=document.page_count,
                word_count=document.word_count,
                chunk_count=document.chunk_count,
                error_message=document.error_message,
                created_at=document.created_at.isoformat(),
                updated_at=document.updated_at.isoformat()
            ),
            message="Document uploaded successfully and queued for processing"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Document upload failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Document upload failed: {str(e)}"
        )


@router.get("/projects/{project_id}/documents", response_model=List[DocumentResponse])
async def list_documents(
    project_id: int,
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List documents for a project.

    Args:
        project_id: Project ID
        skip: Number of records to skip
        limit: Maximum number of records to return
        status_filter: Optional status filter (pending, processing, completed, failed)
        db: Database session

    Returns:
        List of documents
    """
    try:
        query = (
            select(Document)
            .where(Document.project_id == project_id)
            .order_by(Document.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        # Apply status filter if provided
        if status_filter:
            try:
                status_enum = DocumentStatus(status_filter.lower())
                query = query.where(Document.status == status_enum)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid status filter: {status_filter}"
                )

        result = await db.execute(query)
        documents = result.scalars().all()

        return [
            DocumentResponse(
                id=doc.id,
                project_id=doc.project_id,
                filename=doc.filename,
                file_type=doc.file_type.value,
                file_size=doc.file_size,
                status=doc.status.value,
                page_count=doc.page_count,
                word_count=doc.word_count,
                chunk_count=doc.chunk_count,
                error_message=doc.error_message,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat()
            )
            for doc in documents
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list documents: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list documents: {str(e)}"
        )


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get document details.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        Document details

    Raises:
        HTTPException: If document not found
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    return DocumentResponse(
        id=document.id,
        project_id=document.project_id,
        filename=document.filename,
        file_type=document.file_type.value,
        file_size=document.file_size,
        status=document.status.value,
        page_count=document.page_count,
        word_count=document.word_count,
        chunk_count=document.chunk_count,
        error_message=document.error_message,
        created_at=document.created_at.isoformat(),
        updated_at=document.updated_at.isoformat()
    )


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a document and its embeddings.

    Args:
        document_id: Document ID
        db: Database session

    Raises:
        HTTPException: If document not found or deletion fails
    """
    try:
        # Get document
        result = await db.execute(
            select(Document).where(Document.id == document_id)
        )
        document = result.scalar_one_or_none()

        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Document {document_id} not found"
            )

        # Delete embeddings from vector store
        vector_store.delete_documents(
            project_id=document.project_id,
            where={'document_id': document_id}
        )

        # Delete file from storage
        if document.file_path:
            file_path = Path(document.file_path)
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Deleted file: {file_path}")

        # Delete document record
        await db.delete(document)
        await db.commit()

        logger.info(f"Deleted document {document_id}")

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to delete document {document_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete document: {str(e)}"
        )


@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Download document file.

    Args:
        document_id: Document ID
        db: Database session

    Returns:
        File response with document content

    Raises:
        HTTPException: If document not found or file missing
    """
    result = await db.execute(
        select(Document).where(Document.id == document_id)
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document {document_id} not found"
        )

    file_path = Path(document.file_path)

    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document file not found on disk"
        )

    return FileResponse(
        path=file_path,
        filename=document.filename,
        media_type='application/octet-stream'
    )
