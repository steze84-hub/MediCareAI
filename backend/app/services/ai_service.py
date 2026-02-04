"""
AI Service - Integration with GLM-4.7-Flash (llama.cpp API)
Complete workflow: personal info + medical submission + knowledge base -> AI diagnosis
"""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from app.core.config import settings
from app.services.knowledge_base_service import get_knowledge_loader

logger = logging.getLogger(__name__)


class AIService:
    """AI Service class using llama.cpp API with streaming support."""
    
    async def chat_with_glm(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Chat with GLM-4.7-Flash using llama.cpp API format.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            API response result
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{settings.ai_api_url}chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.ai_api_key}"
                    },
                    json={
                        "model": settings.ai_model_id,
                        "messages": messages,
                        "max_tokens": 8192,
                        "temperature": 0.7,
                        "stream": False
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if 'choices' in result and result['choices']:
                        message = result['choices'][0]['message']
                        content = message.get('reasoning_content') or message.get('content', '')
                        return {
                            "success": True,
                            "content": content,
                            "model": result.get('model', ''),
                            "usage": result.get('usage', {})
                        }
                    return {
                        "success": False,
                        "error": "Invalid response format",
                        "data": result
                    }
                else:
                    logger.error(f"GLM API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "detail": response.text
                    }

        except httpx.TimeoutException:
            logger.error("GLM API timeout")
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"GLM API error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def chat_with_glm_stream(self, messages: List[Dict[str, str]]) -> AsyncGenerator[str, None]:
        """
        Stream chat with GLM-4.7-Flash using llama.cpp API format.
        
        Args:
            messages: List of conversation messages
            
        Yields:
            Streaming text chunks
        """
        try:
            async with httpx.AsyncClient(timeout=300.0) as client:
                async with client.stream(
                    "POST",
                    f"{settings.ai_api_url}chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.ai_api_key}"
                    },
                    json={
                        "model": settings.ai_model_id,
                        "messages": messages,
                        "max_tokens": 8192,
                        "temperature": 0.7,
                        "stream": True
                    }
                ) as response:
                    if response.status_code == 200:
                        async for line in response.aiter_lines():
                            if line.startswith("data: "):
                                data_str = line[6:]
                                if data_str.strip() == "[DONE]":
                                    break
                                try:
                                    data = json.loads(data_str)
                                    if 'choices' in data and data['choices']:
                                        delta = data['choices'][0].get('delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            yield content
                                except json.JSONDecodeError:
                                    continue
                    else:
                        error_text = await response.aread()
                        logger.error(f"Streaming API error: {response.status_code} - {error_text}")
                        yield f"[ERROR] API error: {response.status_code}"

        except httpx.TimeoutException:
            logger.error("Streaming API timeout")
            yield "[ERROR] Request timeout"
        except Exception as e:
            logger.error(f"Streaming API error: {str(e)}")
            yield f"[ERROR] {str(e)}"

    async def query_knowledge_base(self, symptoms: str, disease_category: str = "respiratory") -> Dict[str, Any]:
        """
        Query knowledge base for relevant disease information.
        
        Args:
            symptoms: Symptom description
            disease_category: Disease category, default respiratory
            
        Returns:
            Knowledge base information
        """
        try:
            loader = get_knowledge_loader()
            kb_data = loader.load_base(disease_category)
            
            diseases = kb_data.get('diseases', [])
            guidelines = kb_data.get('guidelines', [])
            
            knowledge_context = []
            
            for disease in diseases[:3]:
                disease_info = f"""
疾病名称: {disease.get('name', '未知')}
症状: {', '.join(disease.get('symptoms', [])[:5])}
诊断标准: {', '.join(disease.get('diagnosis_criteria', [])[:3])}
治疗方案: {', '.join(disease.get('treatment', [])[:3])}
"""
                knowledge_context.append(disease_info)
            
            guideline_context = []
            for guideline in guidelines[:2]:
                guide_info = f"""
指南: {guideline.get('name', '未知')}
来源: {guideline.get('source', '未知')}
关键点: {', '.join(guideline.get('key_points', [])[:3])}
"""
                guideline_context.append(guide_info)
            
            return {
                "success": True,
                "diseases_info": "\n".join(knowledge_context),
                "guidelines_info": "\n".join(guideline_context),
                "source": disease_category
            }
            
        except Exception as e:
            logger.error(f"Knowledge base query failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "diseases_info": "",
                "guidelines_info": ""
            }

    async def extract_document_with_mineru(self, file_url: str) -> Dict[str, Any]:
        """
        Extract document content using MinerU.
        
        Args:
            file_url: File URL or file path
            
        Returns:
            Extraction result
        """
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    settings.mineru_api_url,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {settings.mineru_token}"
                    },
                    json={
                        "extract_type": "parse",
                        "url": file_url
                    }
                )

                if response.status_code == 200:
                    result = response.json()
                    if result.get('code') == 0:
                        return {
                            "success": True,
                            "data": result.get('data', {}),
                            "text_content": result.get('data', {}).get('text', '')
                        }
                    else:
                        logger.error(f"MinerU API error: code={result.get('code')}, msg={result.get('msg')}")
                        return {
                            "success": False,
                            "error": result.get('msg', 'Unknown error'),
                            "code": result.get('code')
                        }
                else:
                    logger.error(f"MinerU API error: {response.status_code} - {response.text}")
                    return {
                        "success": False,
                        "error": f"API error: {response.status_code}",
                        "detail": response.text
                    }

        except httpx.TimeoutException:
            logger.error("MinerU API timeout")
            return {"success": False, "error": "Request timeout"}
        except Exception as e:
            logger.error(f"MinerU API error: {str(e)}")
            return {"success": False, "error": str(e)}

    async def comprehensive_diagnosis(
        self,
        symptoms: str,
        patient_info: Dict[str, Any],
        duration: Optional[str] = None,
        severity: Optional[str] = None,
        uploaded_files: Optional[List[str]] = None,
        disease_category: str = "respiratory",
        language: str = "zh"
    ) -> Dict[str, Any]:
        """
        Complete diagnosis workflow.
        
        Integrates: personal info + medical submission info + knowledge base -> AI diagnosis
        
        Args:
            language: Language preference - "zh" for Chinese, "en" for English
        """
        logger.info(f"Starting comprehensive diagnosis workflow (language: {language})...")
        
        # Process uploaded files with MinerU
        extracted_texts = []
        if uploaded_files:
            logger.info(f"Extracting {len(uploaded_files)} files...")
            for file_url in uploaded_files:
                extraction_result = await self.extract_document_with_mineru(file_url)
                if extraction_result.get('success'):
                    text_content = extraction_result.get('text_content', '')
                    if text_content:
                        extracted_texts.append(text_content[:2000])
                        logger.info(f"File extraction successful, content length: {len(text_content)}")
                else:
                    logger.warning(f"File extraction failed: {extraction_result.get('error')}")
        
        # Query knowledge base
        logger.info(f"Querying knowledge base: {disease_category}...")
        kb_result = await self.query_knowledge_base(symptoms, disease_category)
        
        # Build complete prompt
        prompt = self._build_diagnosis_prompt(
            patient_info=patient_info,
            symptoms=symptoms,
            duration=duration,
            severity=severity,
            extracted_texts=extracted_texts,
            knowledge_base=kb_result,
            language=language
        )
        
        logger.info("Calling AI model for diagnosis...")
        
        # 根据语言选择系统提示词
        if language == "zh":
            system_prompt = "你是一位经验丰富的全科医生。请根据患者信息、症状描述、相关检查数据和医疗知识库提供专业的中文诊断。请确保你的回答使用中文。"
        else:
            system_prompt = "You are a professional general practitioner with rich clinical experience. Please provide professional diagnosis in English based on the patient information, symptom description, relevant examination data and medical knowledge base. Please ensure your answer is in English."
        
        # Call AI for diagnosis
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        result = await self.chat_with_glm(messages)
        
        if result.get('success'):
            return {
                "success": True,
                "diagnosis": result['content'],
                "model_used": settings.ai_model_id,
                "tokens_used": result.get('usage', {}).get('total_tokens', 0),
                "workflow": {
                    "patient_info_included": bool(patient_info),
                    "files_processed": len(extracted_texts),
                    "knowledge_base_queried": kb_result.get('success', False),
                    "knowledge_source": kb_result.get('source', '')
                }
            }
        else:
            return {
                "success": False,
                "error": result.get('error'),
                "diagnosis": "AI analysis failed, please try again later"
            }

    async def comprehensive_diagnosis_stream(
        self,
        symptoms: str,
        patient_info: Dict[str, Any],
        duration: Optional[str] = None,
        severity: Optional[str] = None,
        uploaded_files: Optional[List[str]] = None,
        disease_category: str = "respiratory",
        language: str = "zh"
    ) -> AsyncGenerator[str, None]:
        """
        Complete diagnosis workflow (streaming).
        
        Integrates: personal info + medical submission info + knowledge base -> AI diagnosis (streaming)
        
        Args:
            language: Language preference - "zh" for Chinese, "en" for English
        """
        logger.info(f"Starting comprehensive diagnosis workflow (streaming, language: {language})...")
        
        # Process uploaded files with MinerU
        extracted_texts = []
        if uploaded_files:
            logger.info(f"Extracting {len(uploaded_files)} files...")
            for file_url in uploaded_files:
                extraction_result = await self.extract_document_with_mineru(file_url)
                if extraction_result.get('success'):
                    text_content = extraction_result.get('text_content', '')
                    if text_content:
                        extracted_texts.append(text_content[:2000])
                        logger.info(f"File extraction successful, content length: {len(text_content)}")
                else:
                    logger.warning(f"File extraction failed: {extraction_result.get('error')}")
        
        # Query knowledge base
        logger.info(f"Querying knowledge base: {disease_category}...")
        kb_result = await self.query_knowledge_base(symptoms, disease_category)
        
        # Build complete prompt
        prompt = self._build_diagnosis_prompt(
            patient_info=patient_info,
            symptoms=symptoms,
            duration=duration,
            severity=severity,
            extracted_texts=extracted_texts,
            knowledge_base=kb_result,
            language=language
        )
        
        logger.info("Calling AI model for streaming diagnosis...")
        
        # 根据语言选择系统提示词
        if language == "zh":
            system_prompt = """你是一位经验丰富的全科医生。请根据患者信息、症状描述、相关检查数据和医疗知识库提供专业的中文诊断。

请确保你的回答完整，包括：
1) 初步诊断（按可能性排序的表格）
2) 详细分析
3) 建议检查项目
4) 治疗方案
5) 注意事项

请使用中文回答。"""
        else:
            system_prompt = """You are a professional general practitioner with rich clinical experience. Please provide professional diagnosis in English based on the patient information, symptom description, relevant examination data and medical knowledge base.

Please ensure your answer is complete, including:
1) Preliminary diagnosis (table sorted by probability)
2) Detailed analysis
3) Recommended examinations
4) Treatment plan
5) Precautions

Please answer in English."""
        
        # Call AI for streaming diagnosis
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        chunk_count = 0
        total_chars = 0
        async for chunk in self.chat_with_glm_stream(messages):
            chunk_count += 1
            total_chars += len(chunk)
            yield chunk
        
        logger.info(f"Streaming diagnosis completed, {chunk_count} chunks, {total_chars} characters")

    def _build_diagnosis_prompt(
        self,
        patient_info: Dict[str, Any],
        symptoms: str,
        duration: Optional[str],
        severity: Optional[str],
        extracted_texts: List[str],
        knowledge_base: Dict[str, Any],
        language: str = "zh"
    ) -> str:
        """
        Build diagnosis prompt.
        
        Structure: personal info + medical submission info + knowledge base info
        
        Args:
            language: Language preference - "zh" for Chinese, "en" for English
        """
        prompt_parts = []
        
        # 根据语言选择文本
        if language == "zh":
            # 中文版本
            prompt_parts.append("=" * 50)
            prompt_parts.append("【第1部分：患者个人信息】")
            prompt_parts.append("=" * 50)
            
            if patient_info:
                prompt_parts.append(f"姓名: {patient_info.get('full_name', '未知')}")
                prompt_parts.append(f"性别: {patient_info.get('gender', '未知')}")
                prompt_parts.append(f"出生日期: {patient_info.get('date_of_birth', '未知')}")
                prompt_parts.append(f"电话: {patient_info.get('phone', '未知')}")
                prompt_parts.append(f"紧急联系人: {patient_info.get('emergency_contact', '未知')}")
                prompt_parts.append(f"地址: {patient_info.get('address', '未知')}")
                prompt_parts.append(f"备注: {patient_info.get('notes', '无')}")
            else:
                prompt_parts.append("无详细的个人信息")
            
            # Part 2: Medical Submission Information
            prompt_parts.append("\n" + "=" * 50)
            prompt_parts.append("【第2部分：诊疗提交信息】")
            prompt_parts.append("=" * 50)
            
            prompt_parts.append(f"\n症状描述:\n{symptoms}")
            
            if duration:
                prompt_parts.append(f"\n症状持续时间: {duration}")
            
            if severity:
                prompt_parts.append(f"\n严重程度: {severity}")
            
            # Add MinerU extracted file content
            if extracted_texts:
                prompt_parts.append("\n--- 上传的检查报告/材料 (通过MinerU提取) ---")
                for i, text in enumerate(extracted_texts, 1):
                    prompt_parts.append(f"\n[文件 {i} 内容]:")
                    prompt_parts.append(text[:1500])
            
            # Part 3: Knowledge Base Information
            prompt_parts.append("\n" + "=" * 50)
            prompt_parts.append("【第3部分：医疗知识库参考】")
            prompt_parts.append("=" * 50)
            
            if knowledge_base.get('success'):
                if knowledge_base.get('diseases_info'):
                    prompt_parts.append("\n[相关疾病信息]:")
                    prompt_parts.append(knowledge_base['diseases_info'])
                
                if knowledge_base.get('guidelines_info'):
                    prompt_parts.append("\n[治疗指南参考]:")
                    prompt_parts.append(knowledge_base['guidelines_info'])
            else:
                prompt_parts.append("\n(知识库暂时不可用，基于通用医疗知识进行分析)")
            
            # Diagnosis Requirements
            prompt_parts.append("\n" + "=" * 50)
            prompt_parts.append("【诊断要求】")
            prompt_parts.append("=" * 50)
            prompt_parts.append("""
请根据以上三部分内容提供以下中文诊断内容：

1. **初步诊断**：根据症状和检查数据提供可能的诊断（按可能性排序）
2. **诊断依据**：结合知识库解释诊断推理
3. **鉴别诊断**：列出需要排除的其他疾病
4. **建议检查**：列出推荐的进一步检查
5. **治疗方案**：基于知识库的治疗建议
6. **注意事项**：用药提醒、生活建议等
7. **就医建议**：是否需要立即就医，建议就诊科室

请注意：
- 诊断仅供参考，不能替代专业医生的诊疗
- 如有紧急情况，请立即就医
- 根据患者个人信息（如过敏史等）提供个性化建议
""")
        else:
            # English version
            prompt_parts.append("=" * 50)
            prompt_parts.append("【Part 1: Patient Personal Information】")
            prompt_parts.append("=" * 50)
            
            if patient_info:
                prompt_parts.append(f"Name: {patient_info.get('full_name', 'Unknown')}")
                prompt_parts.append(f"Gender: {patient_info.get('gender', 'Unknown')}")
                prompt_parts.append(f"Date of Birth: {patient_info.get('date_of_birth', 'Unknown')}")
                prompt_parts.append(f"Phone: {patient_info.get('phone', 'Unknown')}")
                prompt_parts.append(f"Emergency Contact: {patient_info.get('emergency_contact', 'Unknown')}")
                prompt_parts.append(f"Address: {patient_info.get('address', 'Unknown')}")
                prompt_parts.append(f"Notes: {patient_info.get('notes', 'None')}")
            else:
                prompt_parts.append("No detailed personal information available")
            
            # Part 2: Medical Submission Information
            prompt_parts.append("\n" + "=" * 50)
            prompt_parts.append("【Part 2: Medical Submission Information】")
            prompt_parts.append("=" * 50)
            
            prompt_parts.append(f"\nSymptom Description:\n{symptoms}")
            
            if duration:
                prompt_parts.append(f"\nSymptom Duration: {duration}")
            
            if severity:
                prompt_parts.append(f"\nSeverity: {severity}")
            
            # Add MinerU extracted file content
            if extracted_texts:
                prompt_parts.append("\n--- Uploaded examination reports/materials (extracted by MinerU) ---")
                for i, text in enumerate(extracted_texts, 1):
                    prompt_parts.append(f"\n[File {i} content]:")
                    prompt_parts.append(text[:1500])
            
            # Part 3: Knowledge Base Information
            prompt_parts.append("\n" + "=" * 50)
            prompt_parts.append("【Part 3: Medical Knowledge Base Reference】")
            prompt_parts.append("=" * 50)
            
            if knowledge_base.get('success'):
                if knowledge_base.get('diseases_info'):
                    prompt_parts.append("\n[Relevant Disease Information]:")
                    prompt_parts.append(knowledge_base['diseases_info'])
                
                if knowledge_base.get('guidelines_info'):
                    prompt_parts.append("\n[Treatment Guidelines Reference]:")
                    prompt_parts.append(knowledge_base['guidelines_info'])
            else:
                prompt_parts.append("\n(Knowledge base temporarily unavailable, analyzing based on general medical knowledge)")
            
            # Diagnosis Requirements
            prompt_parts.append("\n" + "=" * 50)
            prompt_parts.append("【Diagnosis Requirements】")
            prompt_parts.append("=" * 50)
            prompt_parts.append("""
Please provide the following diagnosis content based on the three parts above:

1. **Preliminary Diagnosis**: Possible diagnoses based on symptoms and examination data (sorted by probability)
2. **Diagnosis Basis**: Explain diagnosis reasoning combined with knowledge base
3. **Differential Diagnosis**: List other diseases to exclude
4. **Recommended Examinations**: List further examinations to recommend
5. **Treatment Plan**: Treatment recommendations based on knowledge base
6. **Precautions**: Medication reminders, lifestyle suggestions, etc.
7. **Medical Advice**: Whether immediate medical attention is needed, recommended departments

Please note:
- Diagnosis is for reference only and cannot replace professional doctor's consultation
- In case of emergency, seek medical attention immediately
- Provide personalized suggestions based on patient personal information (such as allergy history)
""")
        
        return "\n".join(prompt_parts)

    async def analyze_symptoms(self, symptoms: str, patient_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        AI analyze symptoms (simplified version, backward compatible)
        """
        # Call complete diagnosis workflow
        result = await self.comprehensive_diagnosis(
            symptoms=symptoms,
            patient_info=patient_info or {}
        )
        
        return {
            "diagnosis": result.get('diagnosis', ''),
            "model_used": result.get('model_used', ''),
            "tokens_used": result.get('tokens_used', 0),
            "error": result.get('error')
        }

    async def extract_medical_report(self, file_url: str) -> Dict[str, Any]:
        """
        Extract medical report content
        """
        result = await self.extract_document_with_mineru(file_url)

        if not result.get('success'):
            return result

        return {
            "success": True,
            "raw_data": result.get('data', {}),
            "extracted_text": result.get('text_content', ''),
            "extracted_fields": {}
        }


# Global instance
ai_service = AIService()