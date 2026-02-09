"""
Data Sharing Service - Patient @Doctor & Case Sharing | 数据分享服务
Manages patient-doctor relationships and medical case sharing.

Features:
- Patient @Doctor functionality (like GitHub @mentions)
- Medical case sharing with consent
- Anonymous sharing to platform
- PII cleaning for shared cases

支持：
- 患者@医生功能（类似GitHub @）
- 带同意的病例分享
- 匿名分享到平台
- PII清理用于分享病例
"""

import logging
import re
from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, or_
from sqlalchemy.orm import selectinload

from app.models.models import (
    User, MedicalCase, MedicalDocument, 
    DoctorPatientRelation, SharedMedicalCase,
    DataSharingConsent
)
from app.services.pii_cleaner_service import pii_cleaner
from app.services.data_sharing_consent_service import DataSharingConsentService

import uuid

logger = logging.getLogger(__name__)


class DataSharingService:
    """
    Data Sharing Service / 数据分享服务
    
    Manages medical data sharing between patients and doctors.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.consent_service = DataSharingConsentService(db)
    
    async def search_doctors(
        self,
        query: str,
        specialty: str = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Search doctors for @mention / 搜索医生用于@功能
        
        Returns doctors with display info (surname + hospital + specialty)
        """
        # Build query
        stmt = select(User).where(
            User.role == 'doctor',
            User.is_verified_doctor == True,
            User.is_active == True
        )
        
        # Add search filter
        if query:
            search_pattern = f"%{query}%"
            stmt = stmt.where(
                or_(
                    User.full_name.ilike(search_pattern),
                    User.hospital.ilike(search_pattern),
                    User.specialty.ilike(search_pattern),
                    User.department.ilike(search_pattern)
                )
            )
        
        if specialty:
            stmt = stmt.where(User.specialty.ilike(f"%{specialty}%"))
        
        stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        doctors = result.scalars().all()
        
        return [
            {
                "id": str(doctor.id),
                "display_name": doctor.display_name or f"{doctor.full_name[0]}医生",
                "hospital": doctor.hospital,
                "department": doctor.department,
                "specialty": doctor.specialty,
                "title": doctor.title,
                # Only show surname + initial
                "surname": doctor.full_name[0] if doctor.full_name else "医"
            }
            for doctor in doctors
        ]
    
    async def mention_doctor_in_case(
        self,
        patient_id: uuid.UUID,
        case_id: uuid.UUID,
        doctor_id: uuid.UUID,
        message: str = None,
        share_all_cases: bool = False
    ) -> Dict[str, Any]:
        """
        Patient @mentions doctor in a case / 患者在病例中@医生
        
        Creates a doctor-patient relationship and initiates sharing.
        """
        # Verify case belongs to patient
        stmt = select(MedicalCase).where(
            MedicalCase.id == case_id,
            MedicalCase.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        case = result.scalar_one_or_none()
        
        if not case:
            raise ValueError("病例不存在或不属于该患者")
        
        # Verify doctor exists and is verified
        stmt = select(User).where(
            User.id == doctor_id,
            User.role == 'doctor',
            User.is_verified_doctor == True
        )
        result = await self.db.execute(stmt)
        doctor = result.scalar_one_or_none()
        
        if not doctor:
            raise ValueError("医生不存在或未通过认证")
        
        # Check if relation already exists
        stmt = select(DoctorPatientRelation).where(
            DoctorPatientRelation.patient_id == patient_id,
            DoctorPatientRelation.doctor_id == doctor_id
        )
        result = await self.db.execute(stmt)
        existing_relation = result.scalar_one_or_none()
        
        if existing_relation:
            # Update existing relation
            if case_id not in (existing_relation.shared_case_ids or []):
                if existing_relation.shared_case_ids is None:
                    existing_relation.shared_case_ids = []
                existing_relation.shared_case_ids.append(str(case_id))
                
            existing_relation.share_all_cases = share_all_cases
            existing_relation.patient_message = message
            
            await self.db.commit()
            
            logger.info(f"Updated doctor-patient relation: {patient_id} -> {doctor_id}")
            
            return {
                "success": True,
                "relation_id": str(existing_relation.id),
                "status": existing_relation.status,
                "message": "已更新医生关系"
            }
        
        # Create new relation
        relation = DoctorPatientRelation(
            id=uuid.uuid4(),
            patient_id=patient_id,
            doctor_id=doctor_id,
            status='pending',
            initiated_by='patient_at',
            share_all_cases=share_all_cases,
            shared_case_ids=[str(case_id)],
            patient_message=message,
            created_at=datetime.utcnow()
        )
        
        self.db.add(relation)
        await self.db.commit()
        await self.db.refresh(relation)
        
        # Create consent if not exists
        has_consent = await self.consent_service.check_consent_exists(
            patient_id=patient_id,
            share_type='to_specific_doctor',
            target_doctor_id=doctor_id
        )
        
        if not has_consent:
            await self.consent_service.create_consent(
                patient_id=patient_id,
                share_type='to_specific_doctor',
                target_doctor_id=doctor_id,
                valid_days=365
            )
        
        logger.info(f"Created doctor-patient relation: {patient_id} -> {doctor_id}")
        
        return {
            "success": True,
            "relation_id": str(relation.id),
            "status": relation.status,
            "message": "已向医生发送分享请求"
        }
    
    async def share_case_anonymously(
        self,
        patient_id: uuid.UUID,
        case_id: uuid.UUID,
        visible_to_doctors: bool = True,
        visible_for_research: bool = False
    ) -> Dict[str, Any]:
        """
        Share case anonymously to platform / 匿名分享病例到平台
        """
        # Verify case belongs to patient
        stmt = select(MedicalCase).where(
            MedicalCase.id == case_id,
            MedicalCase.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        case = result.scalar_one_or_none()
        
        if not case:
            raise ValueError("病例不存在或不属于该患者")
        
        # Get patient info for anonymization
        stmt = select(User).where(User.id == patient_id)
        result = await self.db.execute(stmt)
        patient = result.scalar_one()
        
        # Check consent
        has_consent = await self.consent_service.check_consent_exists(
            patient_id=patient_id,
            share_type='platform_anonymous'
        )
        
        if not has_consent:
            # Create consent automatically
            await self.consent_service.create_consent(
                patient_id=patient_id,
                share_type='platform_anonymous',
                valid_days=365
            )
        
        # Anonymize patient info
        anonymous_profile = pii_cleaner.anonymize_patient_info({
            "date_of_birth": patient.date_of_birth.isoformat() if patient.date_of_birth else None,
            "gender": patient.gender,
            "address": patient.address,
            "notes": patient.emergency_contact or ""
        })
        
        # Anonymize case content
        anonymized_symptoms = pii_cleaner.clean_text(case.symptoms or "")['cleaned_text']
        anonymized_diagnosis = pii_cleaner.clean_text(case.diagnosis or "")['cleaned_text']
        
        # Get and anonymize documents
        stmt = select(MedicalDocument).where(
            MedicalDocument.medical_case_id == case_id
        )
        result = await self.db.execute(stmt)
        documents = result.scalars().all()
        
        anonymized_documents = []
        for doc in documents:
            if doc.cleaned_content:
                anonymized_documents.append({
                    "filename": doc.original_filename,
                    "content_preview": doc.cleaned_content.get('text', '')[:500] if isinstance(doc.cleaned_content, dict) else str(doc.cleaned_content)[:500]
                })
        
        # Create or update shared case
        stmt = select(SharedMedicalCase).where(
            SharedMedicalCase.original_case_id == case_id
        )
        result = await self.db.execute(stmt)
        existing_shared = result.scalar_one_or_none()
        
        if existing_shared:
            # Update existing
            existing_shared.anonymous_patient_profile = anonymous_profile
            existing_shared.anonymized_symptoms = anonymized_symptoms
            existing_shared.anonymized_diagnosis = anonymized_diagnosis
            existing_shared.anonymized_documents = anonymized_documents
            existing_shared.visible_to_doctors = visible_to_doctors
            existing_shared.visible_for_research = visible_for_research
            
            await self.db.commit()
            
            logger.info(f"Updated shared case: {case_id}")
            
            return {
                "success": True,
                "shared_case_id": str(existing_shared.id),
                "message": "已更新匿名分享"
            }
        
        # Get consent ID
        stmt = select(DataSharingConsent).where(
            DataSharingConsent.patient_id == patient_id,
            DataSharingConsent.share_type == 'platform_anonymous',
            DataSharingConsent.is_active == True
        )
        result = await self.db.execute(stmt)
        consent = result.scalar_one()
        
        # Create new shared case
        shared_case = SharedMedicalCase(
            id=uuid.uuid4(),
            original_case_id=case_id,
            consent_id=consent.id,
            anonymous_patient_profile=anonymous_profile,
            anonymized_symptoms=anonymized_symptoms,
            anonymized_diagnosis=anonymized_diagnosis,
            anonymized_documents=anonymized_documents,
            visible_to_doctors=visible_to_doctors,
            visible_for_research=visible_for_research,
            view_count=0,
            doctor_views=[],
            created_at=datetime.utcnow()
        )
        
        self.db.add(shared_case)
        
        # Update case sharing status
        case.is_shared = True
        case.share_scope = 'platform_anonymous'
        
        await self.db.commit()
        await self.db.refresh(shared_case)
        
        logger.info(f"Created shared case: {shared_case.id}")
        
        return {
            "success": True,
            "shared_case_id": str(shared_case.id),
            "message": "病例已匿名分享到平台"
        }
    
    async def get_shared_cases_for_doctor(
        self,
        doctor_id: uuid.UUID,
        disease_category: str = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """
        Get shared cases visible to doctor / 获取医生可见的分享病例
        """
        stmt = select(SharedMedicalCase).where(
            SharedMedicalCase.visible_to_doctors == True
        )
        
        if disease_category:
            # Join with MedicalCase to filter by category
            stmt = stmt.join(MedicalCase).where(
                MedicalCase.disease_id.in_(
                    select(Disease.id).where(Disease.category == disease_category)
                )
            )
        
        stmt = stmt.order_by(SharedMedicalCase.created_at.desc())
        stmt = stmt.limit(limit).offset(offset)
        
        result = await self.db.execute(stmt)
        shared_cases = result.scalars().all()
        
        cases = []
        for shared in shared_cases:
            # Check if doctor has viewed
            has_viewed = any(
                view.get('doctor_id') == str(doctor_id) 
                for view in (shared.doctor_views or [])
            )
            
            cases.append({
                "id": str(shared.id),
                "anonymous_profile": shared.anonymous_patient_profile,
                "anonymized_symptoms_preview": (shared.anonymized_symptoms or "")[:200] + "..." if shared.anonymized_symptoms and len(shared.anonymized_symptoms) > 200 else shared.anonymized_symptoms,
                "disease_category": shared.anonymous_patient_profile.get('disease_category') if shared.anonymous_patient_profile else None,
                "view_count": shared.view_count,
                "has_viewed": has_viewed,
                "created_at": shared.created_at.isoformat() if shared.created_at else None
            })
        
        return cases
    
    async def get_shared_case_detail(
        self,
        shared_case_id: uuid.UUID,
        doctor_id: uuid.UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get detailed shared case / 获取分享病例详情
        """
        stmt = select(SharedMedicalCase).where(
            SharedMedicalCase.id == shared_case_id,
            SharedMedicalCase.visible_to_doctors == True
        )
        result = await self.db.execute(stmt)
        shared = result.scalar_one_or_none()
        
        if not shared:
            return None
        
        # Record view
        if not shared.doctor_views:
            shared.doctor_views = []
        
        # Check if already viewed
        already_viewed = any(
            view.get('doctor_id') == str(doctor_id)
            for view in shared.doctor_views
        )
        
        if not already_viewed:
            shared.doctor_views.append({
                "doctor_id": str(doctor_id),
                "viewed_at": datetime.utcnow().isoformat()
            })
            shared.view_count += 1
            await self.db.commit()
        
        return {
            "id": str(shared.id),
            "anonymous_profile": shared.anonymous_patient_profile,
            "anonymized_symptoms": shared.anonymized_symptoms,
            "anonymized_diagnosis": shared.anonymized_diagnosis,
            "anonymized_documents": shared.anonymized_documents,
            "view_count": shared.view_count,
            "created_at": shared.created_at.isoformat() if shared.created_at else None
        }
    
    async def get_my_doctors(
        self,
        patient_id: uuid.UUID
    ) -> List[Dict[str, Any]]:
        """
        Get list of doctors connected to patient / 获取患者关联的医生列表
        """
        stmt = select(DoctorPatientRelation).where(
            DoctorPatientRelation.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        relations = result.scalars().all()
        
        doctors = []
        for relation in relations:
            stmt = select(User).where(User.id == relation.doctor_id)
            result = await self.db.execute(stmt)
            doctor = result.scalar_one()
            
            doctors.append({
                "relation_id": str(relation.id),
                "doctor_id": str(doctor.id),
                "display_name": doctor.display_name or f"{doctor.full_name[0]}医生",
                "hospital": doctor.hospital,
                "department": doctor.department,
                "specialty": doctor.specialty,
                "status": relation.status,
                "shared_cases_count": len(relation.shared_case_ids) if relation.shared_case_ids else 0,
                "created_at": relation.created_at.isoformat() if relation.created_at else None
            })
        
        return doctors


# Import Disease for category filtering
from app.models.models import Disease
