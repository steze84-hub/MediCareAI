"""
Data Sharing API Endpoints | 数据分享API端点
Patient @Doctor and case sharing functionality.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel, Field
import uuid

from app.db.database import get_db
from app.services.data_sharing_service import DataSharingService
from app.services.data_sharing_consent_service import DataSharingConsentService
from app.core.deps import (
    get_current_active_user, 
    require_patient, 
    require_doctor,
    require_verified_doctor
)
from app.models.models import User

import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Schemas / 数据模式 ==============

class DoctorSearchResponse(BaseModel):
    id: str
    display_name: str
    hospital: Optional[str]
    department: Optional[str]
    specialty: Optional[str]
    title: Optional[str]
    surname: str


class MentionDoctorRequest(BaseModel):
    case_id: uuid.UUID
    doctor_id: uuid.UUID
    message: Optional[str] = None
    share_all_cases: bool = False


class MentionDoctorResponse(BaseModel):
    success: bool
    relation_id: str
    status: str
    message: str


class ShareCaseRequest(BaseModel):
    case_id: uuid.UUID
    visible_to_doctors: bool = True
    visible_for_research: bool = False


class SharedCaseResponse(BaseModel):
    success: bool
    shared_case_id: Optional[str]
    message: str


class SharedCaseListItem(BaseModel):
    id: str
    anonymous_profile: dict
    anonymized_symptoms_preview: Optional[str]
    disease_category: Optional[str]
    view_count: int
    has_viewed: bool
    created_at: str


class SharedCaseDetail(BaseModel):
    id: str
    anonymous_profile: dict
    anonymized_symptoms: Optional[str]
    anonymized_diagnosis: Optional[str]
    anonymized_documents: List[dict]
    view_count: int
    created_at: str


class MyDoctorItem(BaseModel):
    relation_id: str
    doctor_id: str
    display_name: str
    hospital: Optional[str]
    department: Optional[str]
    specialty: Optional[str]
    status: str
    shared_cases_count: int
    created_at: str


# ============== Patient Endpoints / 患者端点 ==============

@router.get("/doctors/search", response_model=List[DoctorSearchResponse])
async def search_doctors(
    q: str = "",
    specialty: Optional[str] = None,
    limit: int = 10,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """
    搜索医生（用于@功能）
    Search doctors (for @mention functionality)
    """
    service = DataSharingService(db)
    doctors = await service.search_doctors(
        query=q,
        specialty=specialty,
        limit=limit
    )
    return doctors


@router.post("/mention-doctor", response_model=MentionDoctorResponse)
async def mention_doctor(
    request: MentionDoctorRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """
    患者在病例中@医生
    Patient @mentions doctor in a case
    """
    service = DataSharingService(db)
    
    try:
        result = await service.mention_doctor_in_case(
            patient_id=current_user.id,
            case_id=request.case_id,
            doctor_id=request.doctor_id,
            message=request.message,
            share_all_cases=request.share_all_cases
        )
        return MentionDoctorResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/share-case", response_model=SharedCaseResponse)
async def share_case_anonymously(
    request: ShareCaseRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """
    匿名分享病例到平台
    Share case anonymously to platform
    """
    service = DataSharingService(db)
    
    try:
        result = await service.share_case_anonymously(
            patient_id=current_user.id,
            case_id=request.case_id,
            visible_to_doctors=request.visible_to_doctors,
            visible_for_research=request.visible_for_research
        )
        return SharedCaseResponse(**result)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/my-doctors", response_model=List[MyDoctorItem])
async def get_my_doctors(
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """
    获取我关联的医生列表
    Get list of doctors connected to me
    """
    service = DataSharingService(db)
    doctors = await service.get_my_doctors(patient_id=current_user.id)
    return doctors


# ============== Doctor Endpoints / 医生端点 ==============

@router.get("/public-cases", response_model=List[SharedCaseListItem])
async def get_public_cases(
    disease_category: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(require_verified_doctor),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开病例列表（医生可见）
    Get list of public cases (visible to doctors)
    """
    service = DataSharingService(db)
    cases = await service.get_shared_cases_for_doctor(
        doctor_id=current_user.id,
        disease_category=disease_category,
        limit=limit,
        offset=offset
    )
    return cases


@router.get("/public-cases/{case_id}", response_model=SharedCaseDetail)
async def get_public_case_detail(
    case_id: uuid.UUID,
    current_user: User = Depends(require_verified_doctor),
    db: AsyncSession = Depends(get_db)
):
    """
    获取公开病例详情
    Get public case detail
    """
    service = DataSharingService(db)
    case = await service.get_shared_case_detail(
        shared_case_id=case_id,
        doctor_id=current_user.id
    )
    
    if not case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="病例不存在或不可见"
        )
    
    return case


# ============== Consent Endpoints / 同意书端点 ==============

@router.post("/consent/create")
async def create_sharing_consent(
    share_type: str,  # 'to_specific_doctor', 'platform_anonymous', 'research'
    target_doctor_id: Optional[uuid.UUID] = None,
    disease_category: Optional[str] = None,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """
    创建数据共享同意书
    Create data sharing consent
    """
    service = DataSharingConsentService(db)
    
    consent = await service.create_consent(
        patient_id=current_user.id,
        share_type=share_type,
        target_doctor_id=target_doctor_id,
        disease_category=disease_category,
        valid_days=365,
        ip_address=None,  # Should get from request
        user_agent=None   # Should get from request
    )
    
    return {
        "consent_id": str(consent.id),
        "share_type": consent.share_type,
        "valid_from": consent.valid_from.isoformat() if consent.valid_from else None,
        "valid_until": consent.valid_until.isoformat() if consent.valid_until else None,
        "message": "同意书创建成功"
    }


@router.get("/consent/my-consents")
async def get_my_consents(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取我的数据共享同意书列表
    Get my data sharing consents
    """
    service = DataSharingConsentService(db)
    summary = await service.get_patient_consent_summary(
        patient_id=current_user.id
    )
    return summary


@router.post("/consent/revoke/{consent_id}")
async def revoke_consent(
    consent_id: uuid.UUID,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db)
):
    """
    撤销数据共享同意书
    Revoke data sharing consent
    """
    service = DataSharingConsentService(db)
    success = await service.revoke_consent(
        consent_id=consent_id,
        patient_id=current_user.id
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="同意书不存在"
        )
    
    return {"message": "同意书已撤销"}


# ============== Doctor: Accept Patient / 医生接受患者 ==============

@router.post("/accept-patient/{relation_id}")
async def accept_patient_relation(
    relation_id: uuid.UUID,
    current_user: User = Depends(require_verified_doctor),
    db: AsyncSession = Depends(get_db)
):
    """
    医生接受患者分享请求
    Doctor accepts patient sharing request
    """
    from sqlalchemy import select
    from app.models.models import DoctorPatientRelation
    
    stmt = select(DoctorPatientRelation).where(
        DoctorPatientRelation.id == relation_id,
        DoctorPatientRelation.doctor_id == current_user.id
    )
    result = await db.execute(stmt)
    relation = result.scalar_one_or_none()
    
    if not relation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="关系不存在"
        )
    
    if relation.status != 'pending':
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"关系状态为 {relation.status}，无法接受"
        )
    
    relation.status = 'active'
    relation.activated_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "已接受患者分享请求", "relation_id": str(relation_id)}


from datetime import datetime
