from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from app.db.database import get_db
from app.schemas.document import (
    MedicalDocumentResponse, 
    DocumentExtractionRequest,
    DocumentExtractionResponse
)
from app.services.document_service import DocumentService
from app.core.deps import get_current_active_user
from app.models.models import User
import uuid

router = APIRouter()


@router.post("/upload", response_model=MedicalDocumentResponse)
async def upload_document(
    medical_case_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> MedicalDocumentResponse:
    document_service = DocumentService(db)
    document = await document_service.upload_document(medical_case_id, file, current_user.id)
    return document


@router.get("/case/{medical_case_id}", response_model=List[MedicalDocumentResponse])
async def get_case_documents(
    medical_case_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    document_service = DocumentService(db)
    documents = await document_service.get_documents_by_case(medical_case_id, current_user.id)
    return documents


@router.get("/{document_id}", response_model=MedicalDocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> MedicalDocumentResponse:
    document_service = DocumentService(db)
    document = await document_service.get_document_by_id(document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    return document


@router.post("/{document_id}/extract", response_model=MedicalDocumentResponse)
async def extract_document_content(
    document_id: uuid.UUID,
    extraction_request: DocumentExtractionRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> MedicalDocumentResponse:
    document_service = DocumentService(db)
    document = await document_service.extract_document_content(
        document_id, extraction_request, current_user.id
    )
    return document


@router.get("/{document_id}/content")
async def get_document_content(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get document content including MinerU extraction and PII cleaning status"""
    from app.models.models import MedicalDocument, MedicalCase, SharedMedicalCase

    # Get document with case info
    result = await db.execute(
        select(MedicalDocument, MedicalCase)
        .join(MedicalCase, MedicalDocument.medical_case_id == MedicalCase.id)
        .where(MedicalDocument.id == document_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    document, case = row

    # Check permissions
    has_access = False
    if case.patient_id == current_user.id:
        has_access = True
    elif current_user.role == "admin":
        has_access = True
    elif current_user.role == "doctor":
        # Check if case is shared
        shared_result = await db.execute(
            select(SharedMedicalCase).where(
                SharedMedicalCase.original_case_id == case.id
            )
        )
        if shared_result.scalar_one_or_none():
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document"
        )
    
    if document.upload_status != "processed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document content not yet extracted"
        )
    
    # Build response with PII cleaning information
    response = {
        "document_id": str(document.id),
        "filename": document.original_filename,
        "extracted_content": document.extracted_content,
        "extraction_metadata": document.extraction_metadata,
        # PII cleaning information
        "pii_cleaning": {
            "status": document.pii_cleaning_status,
            "confidence_score": document.cleaning_confidence,
            "detected_count": len(document.pii_detected) if document.pii_detected else 0,
            "detected_types": list(set([pii.get("type") for pii in document.pii_detected])) if document.pii_detected else []
        }
    }
    
    # Add cleaned content if available
    if document.cleaned_content:
        response["cleaned_content"] = document.cleaned_content
    
    # Add detailed PII detection results if available
    if document.pii_detected:
        response["pii_cleaning"]["details"] = [
            {
                "type": pii.get("type"),
                "replacement": pii.get("replacement"),
                "confidence": pii.get("confidence")
            }
            for pii in document.pii_detected
        ]
    
    return response


@router.get("/{document_id}/pii-status")
async def get_document_pii_status(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """Get detailed PII cleaning status for a document"""
    document_service = DocumentService(db)
    
    try:
        result = await document_service.get_document_with_pii_status(document_id, current_user.id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving PII status: {str(e)}"
        )


@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    document_service = DocumentService(db)
    await document_service.delete_document(document_id, current_user.id)
    return {"message": "Document deleted successfully"}


# Static file serving for uploaded files (used by MinerU API)
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.core.config import settings

@router.get("/file/{filename}")
async def serve_uploaded_file(
    filename: str,
    current_user: User = Depends(get_current_active_user)
):
    """
    Serve uploaded file for MinerU API access.
    This endpoint provides public URL access to uploaded files.
    """
    file_path = os.path.join(settings.upload_path, filename)

    # Security check: ensure file is within upload directory
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.upload_path)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )

    return FileResponse(file_path)


@router.get("/{document_id}/download")
async def download_document(
    document_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Download document file.
    Returns the actual file with proper content-type for preview/download.
    """
    from app.models.models import MedicalDocument, MedicalCase
    from sqlalchemy import select

    # Get document with case info to check permissions
    result = await db.execute(
        select(MedicalDocument, MedicalCase)
        .join(MedicalCase, MedicalDocument.medical_case_id == MedicalCase.id)
        .where(MedicalDocument.id == document_id)
    )
    row = result.first()

    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    document, case = row

    # Check permissions:
    # 1. Document owner (patient who uploaded)
    # 2. Doctors can access if case is shared
    # 3. Admins have full access
    has_access = False

    if case.patient_id == current_user.id:
        # User owns the case
        has_access = True
    elif current_user.role == "admin":
        # Admins have full access
        has_access = True
    elif current_user.role == "doctor":
        # Doctors can access if case is shared
        from app.models.models import SharedMedicalCase
        shared_result = await db.execute(
            select(SharedMedicalCase).where(
                SharedMedicalCase.original_case_id == case.id
            )
        )
        if shared_result.scalar_one_or_none():
            has_access = True

    if not has_access:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this document"
        )

    # Build file path
    file_path = os.path.join(settings.upload_path, document.file_path)

    # Security check
    if not os.path.abspath(file_path).startswith(os.path.abspath(settings.upload_path)):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found on server"
        )

    # Determine content type based on file extension
    content_type = "application/octet-stream"
    filename_lower = document.original_filename.lower()
    if filename_lower.endswith('.pdf'):
        content_type = "application/pdf"
    elif filename_lower.endswith(('.jpg', '.jpeg')):
        content_type = "image/jpeg"
    elif filename_lower.endswith('.png'):
        content_type = "image/png"
    elif filename_lower.endswith('.gif'):
        content_type = "image/gif"
    elif filename_lower.endswith('.txt'):
        content_type = "text/plain"
    elif filename_lower.endswith('.doc'):
        content_type = "application/msword"
    elif filename_lower.endswith('.docx'):
        content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

    return FileResponse(
        file_path,
        media_type=content_type,
        filename=document.original_filename
    )