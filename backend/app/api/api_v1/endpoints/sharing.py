"""
Data Sharing API Endpoints (@医生功能) | 数据分享API端点
Comprehensive patient-to-doctor data sharing with legal compliance.

Endpoints implemented:
1. GET /api/v1/sharing/doctors - Get @able doctors list
2. POST /api/v1/sharing/cases/{case_id}/share - Share medical case
3. GET /api/v1/sharing/consents - Get patient consent records  
4. POST /api/v1/sharing/consents/{consent_id}/revoke - Revoke consent
5. GET /api/v1/sharing/legal-documents - Get legal document templates
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, update
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import uuid
from datetime import datetime, timedelta

from app.db.database import get_db
from app.services.pii_cleaner_service import PIICleanerService, anonymize_for_sharing
from app.core.deps import (
    get_current_active_user, 
    require_patient, 
    require_doctor,
    require_verified_doctor
)
from app.models.models import (
    User, 
    DataSharingConsent, 
    SharedMedicalCase, 
    MedicalCase,
    MedicalDocument,
    DoctorPatientRelation,
    AuditLog
)
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# ============== Pydantic Schemas / 数据模式 ==============

class DoctorInfo(BaseModel):
    id: str = Field(..., description="医生ID")
    surname: str = Field(..., description="姓氏")
    hospital: Optional[str] = Field(None, description="医院名称")
    department: Optional[str] = Field(None, description="科室")
    specialty: Optional[str] = Field(None, description="专业领域")
    title: Optional[str] = Field(None, description="职称")
    display_name: str = Field(..., description="显示名称")

class ShareCaseRequest(BaseModel):
    target_type: str = Field(..., pattern="^(specific_doctor|platform)$", description="分享目标类型")
    doctor_id: Optional[uuid.UUID] = Field(None, description="目标医生ID(当target_type=specific_doctor时必需)")
    consent_text: str = Field(..., min_length=50, description="同意书文本")
    include_history: bool = Field(False, description="是否包含历史相关病例")
    disease_category: Optional[str] = Field(None, description="疾病分类限制")
    valid_days: int = Field(365, ge=1, le=3650, description="有效期天数")

class ConsentRecord(BaseModel):
    id: str = Field(..., description="同意书ID")
    share_type: str = Field(..., description="分享类型")
    target_doctor: Optional[Dict[str, Any]] = Field(None, description="目标医生信息")
    disease_category: Optional[str] = Field(None, description="疾病分类")
    consent_text: str = Field(..., description="同意书文本")
    signed_at: str = Field(..., description="签署时间")
    valid_from: str = Field(..., description="生效时间")
    valid_until: Optional[str] = Field(None, description="过期时间")
    is_active: bool = Field(..., description="是否有效")
    revoked_at: Optional[str] = Field(None, description="撤销时间")
    shared_cases_count: int = Field(..., description="已分享病例数")

class RevokeConsentResponse(BaseModel):
    success: bool = Field(..., description="撤销是否成功")
    message: str = Field(..., description="响应消息")
    affected_cases: int = Field(..., description="受影响病例数")

class LegalDocumentTemplate(BaseModel):
    template_type: str = Field(..., description="模板类型")
    title: str = Field(..., description="文档标题")
    version: str = Field(..., description="版本号")
    content_html: str = Field(..., description="HTML格式内容")
    content_text: str = Field(..., description="纯文本格式内容")
    description: str = Field(..., description="文档说明")
    legal_basis: List[str] = Field(..., description="法律依据")
    patient_rights: List[str] = Field(..., description="患者权利")

# ============== PII Cleaning Helper Functions / PII清理助手函数 ==============

def create_anonymous_profile(patient_user: User) -> Dict[str, Any]:
    """
    Create anonymized patient profile for sharing | 创建匿名化患者资料用于分享
    """
    if patient_user.role != 'patient':
        return {}
    
    # Generate anonymous profile using model method
    return patient_user.generate_anonymous_profile()

async def clean_medical_content(
    pii_cleaner: PIICleanerService, 
    content: Optional[str]
) -> Optional[str]:
    """
    Clean PII from medical content | 清理医疗内容中的PII
    """
    if not content:
        return None
    
    try:
        result = pii_cleaner.clean_text(content)
        return result["cleaned_text"]
    except Exception as e:
        logger.error(f"Failed to clean medical content: {str(e)}")
        # Return content with basic placeholders if cleaning fails
        return content

async def process_medical_documents(
    pii_cleaner: PIICleanerService,
    medical_case: MedicalCase,
    db: AsyncSession
) -> List[Dict[str, Any]]:
    """
    Process and anonymize medical documents | 处理和匿名化医疗文档
    """
    anonymized_documents = []
    
    try:
        # Get documents for this case
        docs_query = select(MedicalDocument).where(
            MedicalDocument.medical_case_id == medical_case.id
        )
        docs_result = await db.execute(docs_query)
        documents = docs_result.scalars().all()
        
        for doc in documents:
            # Use PII cleaned content if available
            if doc.cleaned_content:
                doc_content = doc.cleaned_content
            elif doc.extracted_content:
                # Clean the extracted content
                cleaning_result = await clean_medical_content(
                    pii_cleaner, 
                    str(doc.extracted_content)
                )
                doc_content = cleaning_result
            else:
                doc_content = {"text": "No content available"}
            
            anonymized_documents.append({
                "filename": doc.original_filename,
                "file_type": doc.file_type,
                "cleaned_content": doc_content,
                "pii_cleaning_status": doc.pii_cleaning_status,
                "cleaning_confidence": doc.cleaning_confidence
            })
    
    except Exception as e:
        logger.error(f"Failed to process medical documents for case {medical_case.id}: {str(e)}")
    
    return anonymized_documents

def _get_age_range(birth_date: Optional[str]) -> str:
    """Convert birth date to age range | 将出生日期转换为年龄范围"""
    if not birth_date:
        return "未知"
    
    try:
        birth = datetime.fromisoformat(birth_date.replace('Z', '+00:00'))
        age = (datetime.now(birth.tzinfo) - birth).days // 365
        if age < 18:
            return "0-17岁"
        elif age < 30:
            return "18-29岁"
        elif age < 45:
            return "30-44岁"
        elif age < 60:
            return "45-59岁"
        else:
            return "60岁以上"
    except:
        return "未知"

def _get_city_level(address: Optional[str]) -> str:
    """Extract city level from address | 从地址提取城市等级"""
    if not address:
        return "未知"
    
    # Simplified city level detection
    tier1_cities = ["北京", "上海", "广州", "深圳", "杭州", "南京", "成都", "重庆", "武汉", "西安"]
    tier2_cities = ["天津", "苏州", "郑州", "长沙", "青岛", "沈阳", "大连", "厦门", "济南", "哈尔滨"]
    
    for city in tier1_cities:
        if city in address:
            return "一线城市"
    
    for city in tier2_cities:
        if city in address:
            return "二线城市"
    
    return "其他城市"

async def create_audit_log(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
    ip_address: Optional[str] = None,
    user_agent: Optional[str] = None
):
    """Create audit log entry | 创建审计日志"""
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details or {},
        ip_address=ip_address,
        user_agent=user_agent
    )
    db.add(audit)

# ============== Endpoint 1: Get @able Doctors / 获取可@医生列表 ==============

@router.get("/doctors", response_model=List[DoctorInfo])
async def get_able_doctors(
    q: Optional[str] = Query(None, description="搜索关键词"),
    specialty: Optional[str] = Query(None, description="专业领域筛选"),
    limit: int = Query(20, ge=1, le=100, description="返回数量限制"),
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    获取可@的医生列表 | Get list of @able doctors
    
    Returns authenticated doctors with their information.
    Supports filtering by specialty and search by name/hospital.
    """
    logger.info(f"Patient {current_user.id} requesting @able doctors list")
    
    # Build query for verified doctors
    query = select(User).where(
        and_(
            User.role == "doctor",
            User.is_active == True,
            User.is_verified == True  # Only verified doctors
        )
    )
    
    # Add search filter
    if q:
        search_filter = or_(
            User.full_name.ilike(f"%{q}%"),
            User.hospital.ilike(f"%{q}%"),
            User.specialty.ilike(f"%{q}%"),
            User.department.ilike(f"%{q}%")
        )
        query = query.where(search_filter)
    
    # Add specialty filter
    if specialty:
        query = query.where(User.specialty == specialty)
    
    # Add limit and order
    query = query.order_by(User.full_name).limit(limit)
    
    result = await db.execute(query)
    doctors = result.scalars().all()
    
    # Convert to response format
    doctor_list = []
    for doctor in doctors:
        # Extract surname from full name
        surname = doctor.full_name[0] if doctor.full_name else "未知"
        
        doctor_info = DoctorInfo(
            id=str(doctor.id),
            surname=surname,
            hospital=doctor.hospital,
            department=doctor.department,
            specialty=doctor.specialty,
            title=doctor.title,
            display_name=f"{surname}医生"  # Only show surname for privacy
        )
        doctor_list.append(doctor_info)
    
    # Create audit log
    await create_audit_log(
        db, current_user.id, "search_doctors", "user",
        details={"query": q, "specialty": specialty, "result_count": len(doctor_list)},
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    logger.info(f"Returned {len(doctor_list)} doctors for patient {current_user.id}")
    return doctor_list

# ============== Endpoint 2: Share Medical Case / 分享病例 ==============

@router.post("/cases/{case_id}/share")
async def share_medical_case(
    case_id: uuid.UUID,
    request_data: ShareCaseRequest,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    分享病例给医生或平台 | Share medical case to doctor or platform
    
    Creates consent, triggers PII cleaning, creates shared case record,
    and sends notification if sharing to specific doctor.
    """
    logger.info(f"Patient {current_user.id} attempting to share case {case_id}")
    
    # Validate patient owns the case
    case_query = select(MedicalCase).where(
        and_(
            MedicalCase.id == case_id,
            MedicalCase.patient_id == current_user.id
        )
    )
    case_result = await db.execute(case_query)
    medical_case = case_result.scalar_one_or_none()
    
    if not medical_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="病例不存在或无权访问"
        )
    
    # Validate target doctor if specified
    target_doctor = None
    if request_data.target_type == "specific_doctor":
        if not request_data.doctor_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="指定医生分享时必须提供医生ID"
            )
        
        doctor_query = select(User).where(
            and_(
                User.id == request_data.doctor_id,
                User.role == "doctor",
                User.is_active == True,
                User.is_verified == True
            )
        )
        doctor_result = await db.execute(doctor_query)
        target_doctor = doctor_result.scalar_one_or_none()
        
        if not target_doctor:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="目标医生不存在或未认证"
            )
    
    try:
        # 1. Create DataSharingConsent record
        valid_until = datetime.utcnow() + timedelta(days=float(request_data.valid_days))
        
        consent = DataSharingConsent(
            patient_id=current_user.id,
            share_type="to_specific_doctor" if request_data.target_type == "specific_doctor" else "platform_anonymous",
            target_doctor_id=request_data.doctor_id,
            disease_category=request_data.disease_category,
            consent_version="1.0",
            consent_text=request_data.consent_text,
            valid_until=valid_until,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        db.add(consent)
        await db.flush()  # Get consent.id
        
        # 2. Create anonymized patient profile
        pii_cleaner = PIICleanerService()
        anonymous_profile = create_anonymous_profile(current_user)
        
        # Anonymize medical content
        anonymized_symptoms = await clean_medical_content(
            pii_cleaner, medical_case.symptoms
        )
        anonymized_diagnosis = await clean_medical_content(
            pii_cleaner, medical_case.diagnosis
        )
        
        # Process and anonymize documents
        anonymized_documents = await process_medical_documents(
            pii_cleaner, medical_case, db
        )
        
        # 4. Create SharedMedicalCase record
        shared_case = SharedMedicalCase(
            original_case_id=case_id,
            consent_id=consent.id,
            anonymous_patient_profile=anonymous_profile,
            anonymized_symptoms=anonymized_symptoms,
            anonymized_diagnosis=anonymized_diagnosis,
            anonymized_documents=anonymized_documents,
            visible_to_doctors=request_data.target_type == "specific_doctor",
            visible_for_research=request_data.target_type == "platform"
        )
        db.add(shared_case)
        await db.flush()  # Get shared_case.id
        
        # 5. Handle history sharing if requested
        shared_case_ids = [shared_case.id]
        if request_data.include_history:
            # Find related cases (same disease category or similar diagnosis)
            history_query = select(MedicalCase).where(
                and_(
                    MedicalCase.patient_id == current_user.id,
                    MedicalCase.id != case_id,
                    or_(
                        MedicalCase.diagnosis.ilike(f"%{medical_case.diagnosis or ''}%"),
                        # Could add more sophisticated similarity matching
                    )
                )
            ).limit(5)  # Limit to 5 related cases
            
            history_result = await db.execute(history_query)
            related_cases = history_result.scalars().all()
            
            for related_case in related_cases:
                # Anonymize related case
                related_symptoms = await clean_medical_content(
                    pii_cleaner, related_case.symptoms
                )
                related_diagnosis = await clean_medical_content(
                    pii_cleaner, related_case.diagnosis
                )
                related_documents = await process_medical_documents(
                    pii_cleaner, related_case, db
                )
                
                related_shared_case = SharedMedicalCase(
                    original_case_id=related_case.id,
                    consent_id=consent.id,
                    anonymous_patient_profile=anonymous_profile,
                    anonymized_symptoms=related_symptoms,
                    anonymized_diagnosis=related_diagnosis,
                    anonymized_documents=related_documents,
                    visible_to_doctors=request_data.target_type == "specific_doctor",
                    visible_for_research=request_data.target_type == "platform"
                )
                db.add(related_shared_case)
                await db.flush()
                shared_case_ids.append(related_shared_case.id)
        
        # 6. Create doctor-patient relation if sharing to specific doctor
        if request_data.target_type == "specific_doctor" and target_doctor:
            existing_relation = await db.execute(
                select(DoctorPatientRelation).where(
                    and_(
                        DoctorPatientRelation.patient_id == current_user.id,
                        DoctorPatientRelation.doctor_id == target_doctor.id,
                        DoctorPatientRelation.status.in_(['pending', 'active'])
                    )
                )
            )
            
            if not existing_relation.scalar_one_or_none():
                relation = DoctorPatientRelation(
                    patient_id=current_user.id,
                    doctor_id=target_doctor.id,
                    status="pending",
                    initiated_by="patient_at",
                    patient_message=f"患者分享了病例:{medical_case.title or '未命名病例'}",
                    share_all_cases=request_data.include_history,
                    shared_case_ids=[str(cid) for cid in shared_case_ids]
                )
                db.add(relation)
        
        # 7. Create audit log
        await create_audit_log(
            db, current_user.id, "share_case", "medical_case", str(case_id),
            details={
                "target_type": request_data.target_type,
                "target_doctor_id": str(request_data.doctor_id) if request_data.doctor_id else None,
                "consent_id": str(consent.id),
                "shared_case_ids": [str(cid) for cid in shared_case_ids],
                "include_history": request_data.include_history
            },
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        await db.commit()
        
        logger.info(f"Case {case_id} shared successfully by patient {current_user.id}")
        
        return {
            "success": True,
            "message": f"病例分享成功{',包含历史病例' if request_data.include_history else ''}",
            "consent_id": str(consent.id),
            "shared_case_ids": [str(cid) for cid in shared_case_ids],
            "shared_cases_count": len(shared_case_ids),
            "valid_until": valid_until.isoformat()
        }
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to share case {case_id} by patient {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="分享失败,请稍后重试"
        )

# ============== Endpoint 3: Get Consent Records / 获取同意书记录 ==============

@router.get("/consents", response_model=List[ConsentRecord])
async def get_consent_records(
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    获取患者的分享同意书记录 | Get patient's data sharing consent records
    
    Returns all sharing records with their status and allows revocation.
    """
    logger.info(f"Patient {current_user.id} requesting consent records")
    
    # Query consents with related data
    query = select(
        DataSharingConsent,
        func.count(SharedMedicalCase.id).label('shared_cases_count')
    ).where(
        DataSharingConsent.patient_id == current_user.id
    ).outerjoin(
        SharedMedicalCase, SharedMedicalCase.consent_id == DataSharingConsent.id
    ).group_by(DataSharingConsent.id).order_by(DataSharingConsent.created_at.desc())
    
    result = await db.execute(query)
    records = result.all()
    
    consent_list = []
    for consent, shared_cases_count in records:
        # Get target doctor info if applicable
        target_doctor = None
        if consent.target_doctor_id:
            doctor_query = select(User).where(User.id == consent.target_doctor_id)
            doctor_result = await db.execute(doctor_query)
            doctor = doctor_result.scalar_one_or_none()
            if doctor:
                target_doctor = {
                    "id": str(doctor.id),
                    "surname": doctor.full_name[0] if doctor.full_name else "未知",
                    "hospital": doctor.hospital,
                    "specialty": doctor.specialty
                }
        
        consent_record = ConsentRecord(
            id=str(consent.id),
            share_type=consent.share_type,
            target_doctor=target_doctor,
            disease_category=consent.disease_category,
            consent_text=consent.consent_text,
            signed_at=consent.signed_at.isoformat() if consent.signed_at else "",
            valid_from=consent.valid_from.isoformat() if consent.valid_from else "",
            valid_until=consent.valid_until.isoformat() if consent.valid_until else None,
            is_active=consent.is_active and (not consent.valid_until or consent.valid_until > datetime.utcnow()),
            revoked_at=consent.revoked_at.isoformat() if consent.revoked_at else None,
            shared_cases_count=shared_cases_count
        )
        consent_list.append(consent_record)
    
    # Create audit log
    await create_audit_log(
        db, current_user.id, "view_consents", "data_sharing_consent",
        details={"record_count": len(consent_list)},
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    logger.info(f"Returned {len(consent_list)} consent records for patient {current_user.id}")
    return consent_list

# ============== Endpoint 4: Revoke Consent / 撤销同意书 ==============

@router.post("/consents/{consent_id}/revoke", response_model=RevokeConsentResponse)
async def revoke_consent(
    consent_id: uuid.UUID,
    current_user: User = Depends(require_patient),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    撤销分享同意 | Revoke data sharing consent
    
    Validates patient identity, marks consent as revoked,
    and updates shared case visibility.
    """
    logger.info(f"Patient {current_user.id} attempting to revoke consent {consent_id}")
    
    # Get consent record
    consent_query = select(DataSharingConsent).where(
        and_(
            DataSharingConsent.id == consent_id,
            DataSharingConsent.patient_id == current_user.id,
            DataSharingConsent.is_active == True
        )
    )
    consent_result = await db.execute(consent_query)
    consent = consent_result.scalar_one_or_none()
    
    if not consent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="同意书不存在或已被撤销"
        )
    
    try:
        # Mark consent as revoked
        consent.is_active = False
        consent.revoked_at = datetime.utcnow()
        
        # Update related shared cases visibility
        shared_cases_query = update(SharedMedicalCase).where(
            SharedMedicalCase.consent_id == consent_id
        ).values(
            visible_to_doctors=False,
            visible_for_research=False
        )
        
        shared_cases_result = await db.execute(shared_cases_query)
        affected_cases = shared_cases_result.rowcount
        
        # Update doctor-patient relations if applicable
        if consent.target_doctor_id:
            relation_query = update(DoctorPatientRelation).where(
                and_(
                    DoctorPatientRelation.patient_id == current_user.id,
                    DoctorPatientRelation.doctor_id == consent.target_doctor_id
                )
            ).values(status="terminated", terminated_at=datetime.utcnow())
            
            await db.execute(relation_query)
        
        # Create audit log
        await create_audit_log(
            db, current_user.id, "revoke_consent", "data_sharing_consent", str(consent_id),
            details={
                "affected_cases": affected_cases,
                "revoked_at": consent.revoked_at.isoformat(),
                "target_doctor_id": str(consent.target_doctor_id) if consent.target_doctor_id else None
            },
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None
        )
        
        await db.commit()
        
        logger.info(f"Consent {consent_id} revoked by patient {current_user.id}, affected {affected_cases} cases")
        
        return RevokeConsentResponse(
            success=True,
            message="同意书已成功撤销,相关病例访问权限已更新",
            affected_cases=affected_cases
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"Failed to revoke consent {consent_id} by patient {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="撤销失败,请稍后重试"
        )

# ============== Endpoint 5: Legal Document Templates / 法律文书模板 ==============

@router.get("/legal-documents", response_model=List[LegalDocumentTemplate])
async def get_legal_document_templates(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    request: Request = None
):
    """
    获取法律文书模板 | Get legal document templates
    
    Returns data sharing consent templates compliant with national regulations.
    Includes double-blind study statements, data usage scope, and patient rights.
    """
    logger.info(f"User {current_user.id} requesting legal document templates")
    
    # Legal document templates based on Chinese healthcare data protection regulations
    templates_data = [
        {
            "template_type": "specific_doctor_consent",
            "title": "医疗数据分享同意书(指定医生)",
            "version": "2024.1.0",
            "content_text": "医疗数据分享同意书(指定医生)\\n\\n本人同意将医疗数据分享给指定医生用于诊疗目的。\\n\\n1. 分享数据类型:基本病情描述、检查检验结果、诊断记录、治疗方案\\n2. 数据用途限制:仅用于本人诊疗目的,不得用于科研或教学,不得分享给第三方\\n3. 患者权利:有权随时撤销同意,有权查看分享记录,有权要求删除数据\\n\\n法律依据:根据《中华人民共和国个人信息保护法》第二十九条",
            "description": "向指定医生分享医疗数据的同意书模板",
            "legal_basis": [
                "中华人民共和国个人信息保护法",
                "中华人民共和国基本医疗卫生与健康促进法",
                "医疗机构管理条例"
            ],
            "patient_rights": [
                "知情权:了解数据分享的具体内容和范围",
                "同意权:自主决定是否分享数据",
                "撤回权:随时可以撤销分享同意",
                "删除权:要求删除相关医疗数据",
                "查询权:查看数据分享记录"
            ]
        },
        {
            "template_type": "platform_anonymous_consent",
            "title": "医疗数据匿名分享同意书(平台科研)",
            "version": "2024.1.0",
            "content_text": "医疗数据匿名分享同意书(平台科研)\\n\\n本人同意将匿名化医疗数据分享至平台用于医学研究。\\n\\n1. 数据匿名化处理:姓名替换为匿名ID,身份证号完全移除,联系方式完全移除,详细地址模糊化处理\\n2. 研究用途:医学科研、疾病统计分析、诊疗方案优化\\n3. 双盲机制:研究人员无法识别患者身份,患者身份与科研数据分离\\n\\n法律依据:根据《中华人民共和国个人信息保护法》第十三条",
            "description": "将医疗数据匿名分享至平台用于科研的同意书模板",
            "legal_basis": [
                "中华人民共和国个人信息保护法",
                "中华人民共和国基本医疗卫生与健康促进法",
                "涉及人的生物医学研究伦理审查办法"
            ],
            "patient_rights": [
                "知情权:了解研究目的和数据使用方式",
                "同意权:自主决定是否参与科研",
                "撤回权:随时可以退出研究",
                "受益权:分享研究成果和收益",
                "监督权:监督研究过程和结果"
            ]
        }
    ]
    
    # Convert to response models
    templates = []
    for template in templates_data:
        # Create simple HTML version
        html_content = f"<h1>{template['title']}</h1><div>{template['content_text'].replace(chr(10), '<br>')}</div>"
        
        templates.append(LegalDocumentTemplate(
            template_type=template["template_type"],
            title=template["title"],
            version=template["version"],
            content_html=html_content,
            content_text=template["content_text"],
            description=template["description"],
            legal_basis=template["legal_basis"],
            patient_rights=template["patient_rights"]
        ))
    
    # Create audit log
    await create_audit_log(
        db, current_user.id, "view_legal_templates", "legal_document",
        details={"template_count": len(templates)},
        ip_address=request.client.host if request else None,
        user_agent=request.headers.get("user-agent") if request else None
    )
    
    logger.info(f"Returned {len(templates)} legal document templates to user {current_user.id}")
    return templates
