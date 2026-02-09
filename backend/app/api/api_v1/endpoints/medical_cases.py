"""
病历记录 API 端点
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
from typing import List, Optional
import uuid
from app.db.database import get_db
from app.core.deps import get_current_active_user
from app.models.models import User, SharedMedicalCase, DoctorCaseComment, CaseCommentReply
from app.services.medical_case_service import MedicalCaseService
from app.services.patient_service import PatientService
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class MedicalCaseResponse(BaseModel):
    """病历响应模型"""
    id: uuid.UUID
    patient_id: uuid.UUID
    title: str
    description: str
    symptoms: str
    diagnosis: str
    severity: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class MedicalCaseCreate(BaseModel):
    """创建病历请求模型"""
    title: str
    symptoms: str
    severity: str = "moderate"
    description: str = ""


class DoctorCommentResponse(BaseModel):
    """医生评论响应模型"""
    id: uuid.UUID
    doctor_name: str
    doctor_specialty: Optional[str]
    doctor_hospital: Optional[str]
    comment_type: str
    content: str
    created_at: datetime
    patient_replies: Optional[List[dict]] = None

    class Config:
        from_attributes = True


class PatientReplyCreate(BaseModel):
    """患者回复请求模型"""
    content: str


class PatientReplyResponse(BaseModel):
    """患者回复响应模型"""
    id: uuid.UUID
    content: str
    created_at: datetime
    status: str

    class Config:
        from_attributes = True


@router.post("/", response_model=MedicalCaseResponse)
async def create_medical_case(
    case_data: MedicalCaseCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    创建新的病历记录
    """
    try:
        case_service = MedicalCaseService(db)

        # 直接使用 current_user.id 作为 patient_id
        medical_case = await case_service.create_medical_case(
            patient_id=current_user.id,
            title=case_data.title,
            symptoms=case_data.symptoms,
            severity=case_data.severity,
            description=case_data.description,
            diagnosis=""  # 初始为空，等待AI诊断
        )

        return medical_case

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建病历记录失败: {str(e)}"
        )


@router.get("/", response_model=List[MedicalCaseResponse])
async def get_my_medical_cases(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取当前用户的所有病历记录
    """
    try:
        # 获取病历记录 - 直接使用current_user.id查询
        # 因为medical_cases.patient_id存储的是user.id（统一用户模型）
        case_service = MedicalCaseService(db)
        cases = await case_service.get_medical_cases_by_patient(current_user.id, skip, limit)
        
        return cases
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取病历记录失败: {str(e)}"
        )


@router.get("/count")
async def get_medical_case_count(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    获取病历记录数量统计
    """
    try:
        # 获取病历数量 - 直接使用current_user.id
        case_service = MedicalCaseService(db)
        total = await case_service.count_medical_cases_by_patient(current_user.id)
        
        return {
            "total": total,
            "active": total,  # 简化处理，后续可按状态统计
            "completed": 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取病历统计失败: {str(e)}"
        )


@router.get("/{case_id}", response_model=MedicalCaseResponse)
async def get_medical_case_detail(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取单个病历详情
    """
    try:
        # 获取病历详情 - 直接使用current_user.id
        case_service = MedicalCaseService(db)
        case = await case_service.get_medical_case_by_id(case_id, current_user.id)
        
        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="病历记录不存在"
            )
        
        return case
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取病历详情失败: {str(e)}"
        )


@router.get("/{case_id}/doctor-comments", response_model=List[DoctorCommentResponse])
async def get_doctor_comments_for_case(
    case_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    获取患者病历的医生评论
    Get doctor comments for patient's medical case
    """
    try:
        # Verify the case belongs to current user
        case_service = MedicalCaseService(db)
        case = await case_service.get_medical_case_by_id(case_id, current_user.id)

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="病历记录不存在"
            )

        # Find shared case associated with this medical case
        stmt = select(SharedMedicalCase).where(
            SharedMedicalCase.original_case_id == case_id
        )
        result = await db.execute(stmt)
        shared_case = result.scalar_one_or_none()

        if not shared_case:
            return []

        # Get doctor comments for this shared case with eager loading of doctor and patient replies
        comments_stmt = select(DoctorCaseComment).options(
            joinedload(DoctorCaseComment.doctor),
            joinedload(DoctorCaseComment.patient_replies)
        ).where(
            DoctorCaseComment.shared_case_id == shared_case.id,
            DoctorCaseComment.status.in_(['active', 'edited']),
            DoctorCaseComment.is_public == True
        ).order_by(desc(DoctorCaseComment.created_at))

        result = await db.execute(comments_stmt)
        comments = result.unique().scalars().all()

        # Format response
        response = []
        for comment in comments:
            doctor_name = "未知医生"
            if comment.doctor:
                # Use surname + doctor title for privacy
                surname = comment.doctor.full_name[0] if comment.doctor.full_name else "医"
                doctor_name = f"{surname}医生"

            # Get patient replies for this comment
            patient_replies = []
            if hasattr(comment, 'patient_replies') and comment.patient_replies:
                for reply in comment.patient_replies:
                    if reply.status == 'active':
                        patient_replies.append({
                            "id": str(reply.id),
                            "content": reply.content,
                            "created_at": reply.created_at.isoformat() if reply.created_at else None
                        })

            response.append(DoctorCommentResponse(
                id=comment.id,
                doctor_name=doctor_name,
                doctor_specialty=comment.doctor_specialty or "未填写",
                doctor_hospital=comment.doctor_hospital or "未填写",
                comment_type=comment.comment_type or "general",
                content=comment.content,
                created_at=comment.created_at,
                patient_replies=patient_replies if patient_replies else None
            ))

        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取医生评论失败: {str(e)}"
        )


@router.post("/{case_id}/doctor-comments/{comment_id}/reply", response_model=PatientReplyResponse)
async def reply_to_doctor_comment(
    case_id: uuid.UUID,
    comment_id: uuid.UUID,
    reply_data: PatientReplyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    患者回复医生评论
    Patient replies to a doctor's comment
    """
    try:
        # Verify the case belongs to current user
        case_service = MedicalCaseService(db)
        case = await case_service.get_medical_case_by_id(case_id, current_user.id)

        if not case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="病历记录不存在"
            )

        # Find shared case
        stmt = select(SharedMedicalCase).where(
            SharedMedicalCase.original_case_id == case_id
        )
        result = await db.execute(stmt)
        shared_case = result.scalar_one_or_none()

        if not shared_case:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="分享病例不存在"
            )

        # Verify the doctor comment exists and belongs to this shared case
        comment_stmt = select(DoctorCaseComment).where(
            DoctorCaseComment.id == comment_id,
            DoctorCaseComment.shared_case_id == shared_case.id,
            DoctorCaseComment.status.in_(['active', 'edited'])
        )
        comment_result = await db.execute(comment_stmt)
        doctor_comment = comment_result.scalar_one_or_none()

        if not doctor_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="医生评论不存在"
            )

        # Create patient reply
        reply = CaseCommentReply(
            doctor_comment_id=comment_id,
            patient_id=current_user.id,
            shared_case_id=shared_case.id,
            content=reply_data.content,
            status='active'
        )

        db.add(reply)
        await db.commit()
        await db.refresh(reply)

        return PatientReplyResponse(
            id=reply.id,
            content=reply.content,
            created_at=reply.created_at,
            status=reply.status
        )

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"回复医生评论失败: {str(e)}"
        )
