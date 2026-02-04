"""
Medical Case Service - Manage medical records
"""

from __future__ import annotations

import uuid
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Disease, MedicalCase, Patient


class MedicalCaseService:
    """Medical case service class."""
    
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
    
    async def create_medical_case(
        self,
        patient_id: uuid.UUID,
        title: str,
        symptoms: str,
        diagnosis: str,
        severity: str = "moderate",
        description: Optional[str] = None,
        disease_id: Optional[uuid.UUID] = None
    ) -> MedicalCase:
        """
        Create medical case record
        
        Args:
            patient_id: Patient ID
            title: Medical case title
            symptoms: Symptom description
            diagnosis: Diagnosis result
            severity: Severity level
            description: Detailed description
            disease_id: Disease ID (optional)
            
        Returns:
            Created medical case record
        """
        # Query or create default disease if not provided
        if not disease_id:
            stmt = select(Disease).limit(1)
            result = await self.db.execute(stmt)
            disease = result.scalar_one_or_none()
            
            if disease:
                disease_id = disease.id
            else:
                # Create default disease record
                default_disease = Disease(
                    id=uuid.uuid4(),
                    name="Unclassified Disease",
                    code="UNC",
                    description="Default category for diseases without clear diagnosis"
                )
                self.db.add(default_disease)
                await self.db.flush()  # flush without commit to get ID
                disease_id = default_disease.id
        
        medical_case = MedicalCase(
            id=uuid.uuid4(),
            patient_id=patient_id,
            disease_id=disease_id,
            title=title,
            description=description or symptoms[:200],  # Use first 200 chars of symptoms if no description
            symptoms=symptoms,
            diagnosis=diagnosis,
            severity=severity,
            status='active'
        )
        
        self.db.add(medical_case)
        await self.db.commit()
        await self.db.refresh(medical_case)
        
        return medical_case
    
    async def get_medical_cases_by_patient(
        self,
        patient_id: uuid.UUID,
        skip: int = 0,
        limit: int = 20
    ) -> List[MedicalCase]:
        """
        Get all medical cases for a patient
        
        Args:
            patient_id: Patient ID
            skip: Number of records to skip
            limit: Number of records to return
            
        Returns:
            List of medical case records
        """
        stmt = (
            select(MedicalCase)
            .where(MedicalCase.patient_id == patient_id)
            .order_by(MedicalCase.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_medical_case_by_id(
        self,
        case_id: uuid.UUID,
        patient_id: uuid.UUID
    ) -> Optional[MedicalCase]:
        """
        Get medical case by ID
        
        Args:
            case_id: Medical case ID
            patient_id: Patient ID (for permission verification)
            
        Returns:
            Medical case record or None
        """
        stmt = (
            select(MedicalCase)
            .where(
                MedicalCase.id == case_id,
                MedicalCase.patient_id == patient_id
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def count_medical_cases_by_patient(
        self,
        patient_id: uuid.UUID
    ) -> int:
        """
        Count medical cases for a patient
        
        Args:
            patient_id: Patient ID
            
        Returns:
            Number of medical cases
        """
        stmt = (
            select(func.count(MedicalCase.id))
            .where(MedicalCase.patient_id == patient_id)
        )
        
        result = await self.db.execute(stmt)
        return result.scalar()
    
    async def update_medical_case_status(
        self,
        case_id: uuid.UUID,
        patient_id: uuid.UUID,
        status: str
    ) -> Optional[MedicalCase]:
        """
        Update medical case status
        
        Args:
            case_id: Medical case ID
            patient_id: Patient ID (for permission verification)
            status: New status ('active', 'completed', 'closed')
            
        Returns:
            Updated medical case record or None
        """
        medical_case = await self.get_medical_case_by_id(case_id, patient_id)
        
        if medical_case:
            medical_case.status = status
            await self.db.commit()
            await self.db.refresh(medical_case)
        
        return medical_case