from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid


class KnowledgeBaseChunkSource(BaseModel):
    """知识库分块溯源信息 / Knowledge Base Chunk Source Attribution"""
    chunk_id: Optional[str] = None
    section_title: str = Field(..., description="章节标题 / Section title")
    text_preview: str = Field(..., description="内容预览(前200字) / Content preview")
    similarity_score: float = Field(..., description="相似度得分(0-1) / Similarity score")
    source_file: Optional[str] = Field(None, description="源文件名 / Source filename")


class KnowledgeBaseSource(BaseModel):
    """知识库来源信息 / Knowledge Base Source Information"""
    category: str = Field(..., description="知识库分类 / Knowledge base category")
    category_name: Optional[str] = Field(None, description="分类中文名 / Category name in Chinese")
    relevance_score: float = Field(..., description="相关度得分 / Relevance score")
    selection_reason: str = Field(..., description="选择原因 / Selection reason")
    chunks_count: int = Field(..., description="引用分块数量 / Number of chunks referenced")
    chunks: List[KnowledgeBaseChunkSource] = Field(default=[], description="引用的具体内容分块 / Referenced content chunks")


class AIDiagnosisRequest(BaseModel):
    medical_case_id: uuid.UUID
    patient_info: Dict[str, Any]
    symptoms: Optional[str] = None
    clinical_findings: Optional[Dict[str, Any]] = None
    documents_content: Optional[List[Dict[str, Any]]] = None
    disease_guidelines: Optional[Dict[str, Any]] = None


class AITreatmentRequest(BaseModel):
    medical_case_id: uuid.UUID
    diagnosis: str
    severity: str
    patient_info: Dict[str, Any]
    current_medications: Optional[List[str]] = None
    allergies: Optional[List[str]] = None
    contraindications: Optional[List[str]] = None


class AIFollowUpRequest(BaseModel):
    medical_case_id: uuid.UUID
    current_status: str
    treatment_plan: str
    last_follow_up_notes: Optional[str] = None
    patient_compliance: Optional[str] = None


class AIResponse(BaseModel):
    response: str
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    reasoning: Optional[str] = None
    recommendations: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    references: Optional[List[str]] = None


class AIFeedbackCreate(BaseModel):
    medical_case_id: uuid.UUID
    feedback_type: str = Field(..., pattern="^(diagnosis|treatment|follow_up)$")
    input_data: Dict[str, Any]
    ai_response: Dict[str, Any]
    confidence_score: Optional[float] = Field(None, ge=0.0, le=1.0)
    recommendations: Optional[str] = None
    follow_up_plan: Optional[Dict[str, Any]] = None


class AIFeedbackResponse(AIFeedbackCreate):
    id: uuid.UUID
    is_reviewed: bool
    reviewed_by: Optional[uuid.UUID] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class AIFeedbackReview(BaseModel):
    is_approved: bool
    review_notes: Optional[str] = None


class AIFeedbackSummary(BaseModel):
    id: uuid.UUID
    feedback_type: str
    confidence_score: Optional[float]
    created_at: datetime
    is_reviewed: bool
    
    class Config:
        from_attributes = True