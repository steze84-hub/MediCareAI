"""
Data Sharing Consent Service | 数据共享同意书服务
Manages patient consent for data sharing with legal compliance.

Features:
- Consent form generation
- Consent signing and storage
- Consent revocation
- Legal compliance tracking

支持：
- 同意书生成
- 同意书签署和存储
- 同意书撤销
- 法律合规追踪
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from app.models.models import DataSharingConsent, User
import uuid

logger = logging.getLogger(__name__)


# Legal consent template / 法律同意书模板
CONSENT_TEMPLATE_ZH = """
《医疗数据共享与使用知情同意书》

版本：v1.0
生效日期：2026年

尊敬的用户：

在您决定是否分享您的医疗数据之前，请仔细阅读以下内容：

一、数据共享目的
1. 医生诊疗参考：帮助医生了解类似病例，提供更好的诊疗建议
2. 医学研究：支持医学研究，促进疾病诊疗水平提升
3. AI模型训练：改进AI诊断系统的准确性

二、数据共享范围
您可以选择以下分享方式：
□ 分享给指定医生（您可以通过@功能指定医生）
□ 匿名分享给平台（所有医生可见，但您的个人信息会被匿名化）
□ 用于科研用途（严格遵循双盲原则）

三、隐私保护措施
我们采取以下措施保护您的隐私：
1. 自动PII清理：系统会自动删除姓名、身份证号、电话等个人身份信息
2. 匿名化处理：医生只能看到您的年龄段、性别、城市级别等统计信息
3. 医疗机构脱敏：医院名称会被替换为"[医疗机构]"
4. 访问控制：只有认证医生可以查看分享的病历

四、您的权利
1. 知情权：您有权知道数据的使用方式
2. 撤回权：您可以随时撤回分享授权
3. 删除权：您可以要求删除已分享的数据
4. 查询权：您可以查看哪些医生访问了您的数据

五、风险告知
尽管我们采取了严格的隐私保护措施，但数据共享仍可能存在以下风险：
1. 数据泄露风险：虽然概率极低，但无法完全排除
2. 再识别风险：恶意用户可能通过组合信息尝试识别您的身份

六、同意声明
我已阅读并理解上述内容，同意按照选择的方式分享我的医疗数据。

用户签名：___________
日期：___________
"""


class DataSharingConsentService:
    """
    Data Sharing Consent Service / 数据共享同意书服务
    
    Manages patient consent for medical data sharing.
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_consent(
        self,
        patient_id: uuid.UUID,
        share_type: str,  # 'to_specific_doctor', 'platform_anonymous', 'research'
        target_doctor_id: uuid.UUID = None,
        disease_category: str = None,
        valid_days: int = 365,
        ip_address: str = None,
        user_agent: str = None
    ) -> DataSharingConsent:
        """
        Create a new data sharing consent / 创建新的数据共享同意书
        """
        # Generate consent text
        consent_text = CONSENT_TEMPLATE_ZH
        
        # Calculate validity period
        valid_from = datetime.utcnow()
        valid_until = valid_from + timedelta(days=valid_days) if valid_days else None
        
        consent = DataSharingConsent(
            id=uuid.uuid4(),
            patient_id=patient_id,
            share_type=share_type,
            target_doctor_id=target_doctor_id,
            disease_category=disease_category,
            consent_version="v1.0",
            consent_text=consent_text,
            ip_address=ip_address,
            user_agent=user_agent,
            signed_at=datetime.utcnow(),
            valid_from=valid_from,
            valid_until=valid_until,
            is_active=True
        )
        
        self.db.add(consent)
        await self.db.commit()
        await self.db.refresh(consent)
        
        logger.info(f"Created data sharing consent: {consent.id} for patient {patient_id}")
        
        return consent
    
    async def get_active_consents(
        self,
        patient_id: uuid.UUID,
        share_type: str = None
    ) -> List[DataSharingConsent]:
        """
        Get active consents for a patient / 获取患者的有效同意书
        """
        stmt = select(DataSharingConsent).where(
            DataSharingConsent.patient_id == patient_id,
            DataSharingConsent.is_active == True
        )
        
        if share_type:
            stmt = stmt.where(DataSharingConsent.share_type == share_type)
        
        result = await self.db.execute(stmt)
        consents = result.scalars().all()
        
        # Filter out expired consents
        now = datetime.utcnow()
        active_consents = [
            c for c in consents 
            if c.valid_until is None or c.valid_until > now
        ]
        
        return active_consents
    
    async def check_consent_exists(
        self,
        patient_id: uuid.UUID,
        share_type: str,
        target_doctor_id: uuid.UUID = None
    ) -> bool:
        """
        Check if valid consent exists / 检查是否存在有效同意书
        """
        stmt = select(DataSharingConsent).where(
            DataSharingConsent.patient_id == patient_id,
            DataSharingConsent.share_type == share_type,
            DataSharingConsent.is_active == True
        )
        
        if target_doctor_id:
            stmt = stmt.where(DataSharingConsent.target_doctor_id == target_doctor_id)
        
        result = await self.db.execute(stmt)
        consents = result.scalars().all()
        
        # Check if any consent is still valid
        now = datetime.utcnow()
        for consent in consents:
            if consent.valid_until is None or consent.valid_until > now:
                return True
        
        return False
    
    async def revoke_consent(
        self,
        consent_id: uuid.UUID,
        patient_id: uuid.UUID
    ) -> bool:
        """
        Revoke a consent / 撤销同意书
        """
        stmt = select(DataSharingConsent).where(
            DataSharingConsent.id == consent_id,
            DataSharingConsent.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        consent = result.scalar_one_or_none()
        
        if not consent:
            return False
        
        consent.is_active = False
        consent.revoked_at = datetime.utcnow()
        
        await self.db.commit()
        
        logger.info(f"Revoked consent: {consent_id}")
        
        return True
    
    async def get_consent_details(
        self,
        consent_id: uuid.UUID,
        patient_id: uuid.UUID = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get consent details / 获取同意书详情
        """
        stmt = select(DataSharingConsent).where(DataSharingConsent.id == consent_id)
        
        if patient_id:
            stmt = stmt.where(DataSharingConsent.patient_id == patient_id)
        
        result = await self.db.execute(stmt)
        consent = result.scalar_one_or_none()
        
        if not consent:
            return None
        
        return {
            "id": str(consent.id),
            "share_type": consent.share_type,
            "target_doctor_id": str(consent.target_doctor_id) if consent.target_doctor_id else None,
            "disease_category": consent.disease_category,
            "consent_version": consent.consent_version,
            "signed_at": consent.signed_at.isoformat() if consent.signed_at else None,
            "valid_from": consent.valid_from.isoformat() if consent.valid_from else None,
            "valid_until": consent.valid_until.isoformat() if consent.valid_until else None,
            "is_active": consent.is_active,
            "revoked_at": consent.revoked_at.isoformat() if consent.revoked_at else None
        }
    
    async def get_patient_consent_summary(
        self,
        patient_id: uuid.UUID
    ) -> Dict[str, Any]:
        """
        Get summary of patient's consents / 获取患者同意书摘要
        """
        stmt = select(DataSharingConsent).where(
            DataSharingConsent.patient_id == patient_id
        )
        result = await self.db.execute(stmt)
        all_consents = result.scalars().all()
        
        now = datetime.utcnow()
        
        active_consents = [
            c for c in all_consents 
            if c.is_active and (c.valid_until is None or c.valid_until > now)
        ]
        
        expired_consents = [
            c for c in all_consents 
            if c.is_active and c.valid_until and c.valid_until <= now
        ]
        
        revoked_consents = [c for c in all_consents if not c.is_active]
        
        # Group by share type
        by_type = {}
        for consent in active_consents:
            share_type = consent.share_type
            if share_type not in by_type:
                by_type[share_type] = 0
            by_type[share_type] += 1
        
        return {
            "total_consents": len(all_consents),
            "active_consents": len(active_consents),
            "expired_consents": len(expired_consents),
            "revoked_consents": len(revoked_consents),
            "by_type": by_type,
            "consents": [
                {
                    "id": str(c.id),
                    "share_type": c.share_type,
                    "is_active": c.is_active,
                    "valid_until": c.valid_until.isoformat() if c.valid_until else None
                }
                for c in active_consents
            ]
        }


# Global service instance
def get_consent_service(db: AsyncSession) -> DataSharingConsentService:
    return DataSharingConsentService(db)
