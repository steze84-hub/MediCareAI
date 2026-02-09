"""
PII Cleaner Service - Privacy Protection | PII清理服务 - 隐私保护
Automatically detects and removes personally identifiable information from medical documents.

Features:
- Rule-based PII detection (regex patterns)
- Medical institution name removal
- Address anonymization
- Name detection and replacement
- Confidence scoring

支持：
- 基于规则的PII检测（正则表达式）
- 医疗机构名称移除
- 地址匿名化
- 姓名检测和替换
- 置信度评分
"""

import re
import json
import logging
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class PIIType(Enum):
    """PII Types / PII类型"""
    NAME = "name"
    ID_NUMBER = "id_number"
    PHONE = "phone"
    EMAIL = "email"
    HOSPITAL = "hospital"
    DOCTOR_NAME = "doctor_name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    MEDICAL_RECORD_NUMBER = "medical_record_number"


@dataclass
class PIIDetection:
    """PII Detection Result / PII检测结果"""
    pii_type: PIIType
    original: str
    replacement: str
    position: Tuple[int, int]
    confidence: float


class PIICleanerService:
    """
    PII Cleaner Service / PII清理服务
    
    Automatically cleans sensitive information from medical documents
    to enable safe data sharing while preserving medical value.
    """
    
    # PII Detection Patterns / PII检测模式
    PII_PATTERNS = {
        PIIType.NAME: [
            # Chinese patterns
            r'患者姓名[：:]\s*([\u4e00-\u9fa5]{2,4})',
            r'姓名[：:]\s*([\u4e00-\u9fa5]{2,4})',
            r'病人[：:]\s*([\u4e00-\u9fa5]{2,4})',
            r'患者[：:]\s*([\u4e00-\u9fa5]{2,4})',
            r'姓名：\s*([A-Za-z\s]{2,30})',  # English names
            r'Name[：:]\s*([A-Za-z\s]{2,30})',
        ],
        PIIType.ID_NUMBER: [
            r'\b(\d{17}[\dXx])\b',  # Chinese ID
            r'身份证[号码]*[：:]\s*(\d{17}[\dXx])',
            r'身份证号[码]*[：:]\s*(\S+)',
            r'ID[ Number]*[：:]\s*(\S+)',
        ],
        PIIType.PHONE: [
            r'1[3-9]\d{9}',  # Chinese mobile
            r'电话[号码]*[：:]\s*(\d{7,11})',
            r'手机[号码]*[：:]\s*(\d{11})',
            r'Tel[：:]\s*(\+?[\d\-\s]{7,20})',
            r'Phone[：:]\s*(\+?[\d\-\s]{7,20})',
        ],
        PIIType.EMAIL: [
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            r'邮箱[：:]\s*(\S+@\S+)',
            r'Email[：:]\s*(\S+@\S+)',
        ],
        PIIType.HOSPITAL: [
            r'([\u4e00-\u9fa5]{2,10}(?:医院|诊所|卫生院|医疗中心|医务室))',
            r'就诊机构[：:]\s*([\u4e00-\u9fa5]+)',
            r'医疗机构[：:]\s*([\u4e00-\u9fa5]+)',
            r'Hospital[：:]\s*([A-Za-z\s]+)',
            r'Clinic[：:]\s*([A-Za-z\s]+)',
        ],
        PIIType.DOCTOR_NAME: [
            r'主治医生[：:]\s*([\u4e00-\u9fa5]{2,4}(?:医生|大夫|医师)?)',
            r'医师[：:]\s*([\u4e00-\u9fa5]{2,4})',
            r'医生[：:]\s*([\u4e00-\u9fa5]{2,4})',
            r'Attending[：:]\s*(Dr\.?\s*[A-Za-z\s]+)',
            r'Doctor[：:]\s*(Dr\.?\s*[A-Za-z\s]+)',
        ],
        PIIType.ADDRESS: [
            r'地址[：:]\s*([\u4e00-\u9fa5]{5,50})',
            r'住址[：:]\s*([\u4e00-\u9fa5]{5,50})',
            r'家庭地址[：:]\s*([\u4e00-\u9fa5]{5,50})',
            r'Address[：:]\s*([A-Za-z0-9\s,.-]{10,100})',
            r'住址[：:]\s*(.{5,50})(?=\n|$)',
        ],
        PIIType.DATE_OF_BIRTH: [
            r'出生日期[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)?',
            r'生日[：:]\s*(\d{4}[年/-]\d{1,2}[月/-]\d{1,2}[日]?)?',
            r'DOB[：:]\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
            r'Birth[ Date]*[：:]\s*(\d{4}[/-]\d{1,2}[/-]\d{1,2})',
        ],
        PIIType.MEDICAL_RECORD_NUMBER: [
            r'病历号[：:]\s*(\S+)',
            r'病案号[：:]\s*(\S+)',
            r'门诊号[：:]\s*(\S+)',
            r'住院号[：:]\s*(\S+)',
            r'MRN[：:]\s*(\S+)',
            r'Medical Record[ Number]*[：:]\s*(\S+)',
        ],
    }
    
    # Replacement placeholders / 替换占位符
    REPLACEMENTS = {
        PIIType.NAME: "[患者姓名]",
        PIIType.ID_NUMBER: "[身份证号]",
        PIIType.PHONE: "[联系电话]",
        PIIType.EMAIL: "[电子邮箱]",
        PIIType.HOSPITAL: "[医疗机构]",
        PIIType.DOCTOR_NAME: "[医生姓名]",
        PIIType.ADDRESS: "[家庭住址]",
        PIIType.DATE_OF_BIRTH: "[出生日期]",
        PIIType.MEDICAL_RECORD_NUMBER: "[病历号]",
    }
    
    def __init__(self):
        """Initialize PII cleaner / 初始化PII清理器"""
        self.compiled_patterns = self._compile_patterns()
    
    def _compile_patterns(self) -> Dict[PIIType, List[re.Pattern]]:
        """Compile regex patterns for performance / 编译正则表达式以提高性能"""
        compiled = {}
        for pii_type, patterns in self.PII_PATTERNS.items():
            compiled[pii_type] = [re.compile(p, re.IGNORECASE) for p in patterns]
        return compiled
    
    def detect_pii(self, text: str) -> List[PIIDetection]:
        """
        Detect PII in text / 检测文本中的PII
        
        Args:
            text: Input text to analyze / 要分析的输入文本
            
        Returns:
            List of detected PII items / 检测到的PII列表
        """
        detections = []
        
        for pii_type, patterns in self.compiled_patterns.items():
            for pattern in patterns:
                for match in pattern.finditer(text):
                    # Get the matched text (either full match or first group)
                    matched_text = match.group(0)
                    if match.lastindex and match.lastindex > 0:
                        # Use first capturing group if available
                        matched_text = match.group(1) if match.group(1) else matched_text
                    
                    # Skip if it's just a label without actual content
                    if matched_text and len(matched_text) > 5:  # Arbitrary minimum length
                        detection = PIIDetection(
                            pii_type=pii_type,
                            original=matched_text,
                            replacement=self.REPLACEMENTS[pii_type],
                            position=(match.start(), match.end()),
                            confidence=0.9 if pii_type in [PIIType.ID_NUMBER, PIIType.PHONE] else 0.8
                        )
                        detections.append(detection)
        
        # Sort by position to process from end to start (to maintain positions)
        detections.sort(key=lambda x: x.position[0], reverse=True)
        
        # Remove overlapping detections (keep longer matches)
        filtered_detections = []
        for detection in detections:
            # Check if this overlaps with any already kept detection
            overlaps = False
            for kept in filtered_detections:
                if (detection.position[0] < kept.position[1] and 
                    detection.position[1] > kept.position[0]):
                    overlaps = True
                    break
            if not overlaps:
                filtered_detections.append(detection)
        
        return filtered_detections
    
    def clean_text(self, text: str) -> Dict[str, Any]:
        """
        Clean PII from text / 清理文本中的PII
        
        Args:
            text: Input text / 输入文本
            
        Returns:
            Dictionary with cleaned text and metadata / 包含清理后文本和元数据的字典
            {
                "cleaned_text": str,
                "original_text": str,
                "pii_detected": List[Dict],
                "cleaning_stats": Dict,
                "confidence_score": float
            }
        """
        if not text or not isinstance(text, str):
            return {
                "cleaned_text": text,
                "original_text": text,
                "pii_detected": [],
                "cleaning_stats": {"total_pii": 0, "types_found": []},
                "confidence_score": 1.0
            }
        
        # Detect PII
        detections = self.detect_pii(text)
        
        # Create cleaned text by replacing PII
        cleaned_text = text
        for detection in detections:
            start, end = detection.position
            cleaned_text = cleaned_text[:start] + detection.replacement + cleaned_text[end:]
        
        # Calculate statistics
        pii_types_found = list(set([d.pii_type.value for d in detections]))
        avg_confidence = sum([d.confidence for d in detections]) / len(detections) if detections else 1.0
        
        return {
            "cleaned_text": cleaned_text,
            "original_text": text,
            "pii_detected": [
                {
                    "type": d.pii_type.value,
                    "original": d.original,
                    "replacement": d.replacement,
                    "confidence": d.confidence
                }
                for d in detections
            ],
            "cleaning_stats": {
                "total_pii": len(detections),
                "types_found": pii_types_found,
                "high_confidence": len([d for d in detections if d.confidence >= 0.9]),
                "medium_confidence": len([d for d in detections if 0.7 <= d.confidence < 0.9]),
            },
            "confidence_score": avg_confidence
        }
    
    def clean_medical_document(self, document_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean PII from medical document / 清理医疗文档中的PII
        
        Args:
            document_content: Document content from MinerU / MinerU的文档内容
            
        Returns:
            Cleaned document with PII removed / 清理后的文档
        """
        if not document_content:
            return document_content
        
        # Handle different input formats
        if isinstance(document_content, str):
            return self.clean_text(document_content)
        
        if isinstance(document_content, dict):
            cleaned_doc = {}
            
            # Clean text content
            if "text" in document_content:
                text_cleaning = self.clean_text(document_content["text"])
                cleaned_doc["text"] = text_cleaning["cleaned_text"]
                cleaned_doc["text_cleaning_metadata"] = {
                    "pii_detected": text_cleaning["pii_detected"],
                    "stats": text_cleaning["cleaning_stats"],
                    "confidence": text_cleaning["confidence_score"]
                }
            
            # Clean markdown content if present
            if "markdown" in document_content:
                md_cleaning = self.clean_text(document_content["markdown"])
                cleaned_doc["markdown"] = md_cleaning["cleaned_text"]
            
            # Preserve other fields
            for key in document_content:
                if key not in ["text", "markdown"]:
                    cleaned_doc[key] = document_content[key]
            
            return cleaned_doc
        
        return document_content
    
    def anonymize_patient_info(self, patient_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create anonymized patient profile / 创建匿名化患者资料
        
        Args:
            patient_info: Original patient info / 原始患者信息
            
        Returns:
            Anonymized profile for sharing / 用于分享的匿名化资料
        """
        from datetime import datetime
        
        anonymous_profile = {}
        
        # Age range / 年龄段
        if "date_of_birth" in patient_info and patient_info["date_of_birth"]:
            try:
                dob = patient_info["date_of_birth"]
                if isinstance(dob, str):
                    dob = datetime.strptime(dob, "%Y-%m-%d")
                age = datetime.now().year - dob.year
                
                if age < 18:
                    anonymous_profile["age_range"] = "<18"
                elif age < 30:
                    anonymous_profile["age_range"] = "18-30"
                elif age < 40:
                    anonymous_profile["age_range"] = "30-40"
                elif age < 50:
                    anonymous_profile["age_range"] = "40-50"
                elif age < 60:
                    anonymous_profile["age_range"] = "50-60"
                else:
                    anonymous_profile["age_range"] = "60+"
            except:
                anonymous_profile["age_range"] = "unknown"
        else:
            anonymous_profile["age_range"] = "unknown"
        
        # Gender / 性别
        anonymous_profile["gender"] = patient_info.get("gender", "unknown")
        
        # City tier / 城市级别
        address = patient_info.get("address", "")
        if address:
            tier1_cities = ["北京", "上海", "广州", "深圳"]
            tier2_cities = ["杭州", "南京", "成都", "武汉", "西安", "重庆", "天津"]
            
            if any(city in address for city in tier1_cities):
                anonymous_profile["city_tier"] = "tier_1"
            elif any(city in address for city in tier2_cities):
                anonymous_profile["city_tier"] = "tier_2"
            else:
                anonymous_profile["city_tier"] = "tier_3_plus"
            
            # City environment / 城市环境
            anonymous_profile["city_environment"] = "urban" if "市" in address else "rural"
        else:
            anonymous_profile["city_tier"] = "unknown"
            anonymous_profile["city_environment"] = "unknown"
        
        # Family history (if provided) / 家族史
        notes = patient_info.get("notes", "")
        anonymous_profile["has_family_history"] = any(keyword in notes for keyword in 
            ["家族史", "遗传", "父亲", "母亲", "家族病史", "family history"])
        
        return anonymous_profile


# Global service instance / 全局服务实例
pii_cleaner = PIICleanerService()


# Convenience functions / 便捷函数

def clean_text(text: str) -> str:
    """Clean PII from text and return cleaned text only / 清理PII并只返回清理后的文本"""
    result = pii_cleaner.clean_text(text)
    return result["cleaned_text"]


def detect_pii(text: str) -> List[Dict]:
    """Detect PII in text and return list / 检测PII并返回列表"""
    detections = pii_cleaner.detect_pii(text)
    return [
        {
            "type": d.pii_type.value,
            "original": d.original,
            "replacement": d.replacement,
            "confidence": d.confidence
        }
        for d in detections
    ]


def anonymize_for_sharing(text: str, patient_info: Dict = None) -> Dict[str, Any]:
    """
    Full anonymization pipeline / 完整匿名化流程
    
    Args:
        text: Document text / 文档文本
        patient_info: Optional patient info for profile generation / 可选的患者信息
        
    Returns:
        Complete anonymization result / 完整的匿名化结果
    """
    # Clean PII from text
    cleaning_result = pii_cleaner.clean_text(text)
    
    # Generate anonymous profile if patient info provided
    anonymous_profile = None
    if patient_info:
        anonymous_profile = pii_cleaner.anonymize_patient_info(patient_info)
    
    return {
        "anonymized_text": cleaning_result["cleaned_text"],
        "anonymous_profile": anonymous_profile,
        "pii_cleaning": {
            "detected": cleaning_result["pii_detected"],
            "stats": cleaning_result["cleaning_stats"],
            "confidence": cleaning_result["confidence_score"]
        },
        "safe_for_sharing": cleaning_result["confidence_score"] >= 0.7
    }


# Example usage / 示例用法
if __name__ == "__main__":
    # Test text with various PII
    test_text = """
    患者姓名：张三
    身份证号：110101199001011234
    电话：13800138000
    地址：北京市朝阳区某某街道123号
    就诊医院：北京协和医院
    主治医生：李医生
    病历号：M202401001
    
    患者主诉：咳嗽、发热3天
    现病史：患者于3天前无明显诱因出现咳嗽...
    """
    
    # Clean the text
    result = pii_cleaner.clean_text(test_text)
    
    print("Original text length:", len(test_text))
    print("Cleaned text length:", len(result["cleaned_text"]))
    print("\nPII detected:", len(result["pii_detected"]))
    for pii in result["pii_detected"]:
        print(f"  - {pii['type']}: {pii['original'][:20]}... -> {pii['replacement']}")
    print("\nConfidence score:", result["confidence_score"])
    print("\nCleaned text preview:")
    print(result["cleaned_text"][:500])
