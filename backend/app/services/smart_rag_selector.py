"""
Smart RAG Selector - Intelligent Knowledge Base Selection | 智能RAG选择器
Automatically selects relevant knowledge bases based on symptoms and context.

Features:
- Keyword-based disease category matching
- Vector similarity search
- Multi-source knowledge fusion
- Confidence scoring

支持：
- 基于关键词的疾病分类匹配
- 向量相似度搜索
- 多源知识融合
- 置信度评分
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.vector_embedding_service import VectorEmbeddingService
from app.services.kb_vectorization_service import KnowledgeBaseVectorizationService
import uuid

logger = logging.getLogger(__name__)


@dataclass
class KnowledgeSource:
    """Knowledge source with relevance info / 知识源及相关性信息"""
    category: str
    relevance_score: float
    chunks: List[Dict[str, Any]]
    selection_reason: str


class SmartRAGSelector:
    """
    Smart RAG Selector / 智能RAG选择器
    
    Intelligently selects relevant knowledge bases for diagnosis.
    """
    
    # Disease keywords mapping / 疾病关键词映射
    DISEASE_KEYWORDS = {
        'respiratory': {
            'keywords': [
                '咳嗽', '咳痰', '气喘', '呼吸困难', '呼吸', '喘息', '胸闷',
                '肺炎', '哮喘', '支气管炎', 'copd', '慢阻肺', '肺',
                'cough', 'sputum', 'wheeze', 'dyspnea', 'asthma',
                'pneumonia', 'bronchitis', 'breathing'
            ],
            'priority': 1
        },
        'cardiovascular': {
            'keywords': [
                '心悸', '胸闷', '胸痛', '心痛', '心绞痛', '心梗',
                '高血压', '心律失常', '心衰', '心力衰竭', '冠心病',
                'heart', 'chest pain', 'palpitation', 'hypertension',
                'arrhythmia', 'cardiac', 'cardiovascular'
            ],
            'priority': 1
        },
        'digestive': {
            'keywords': [
                '腹痛', '腹泻', '恶心', '呕吐', '消化不良', '胃炎',
                '肝炎', '便秘', '腹胀', '胃痛', '肠炎',
                'abdominal pain', 'diarrhea', 'nausea', 'vomiting',
                'indigestion', 'gastritis', 'hepatitis'
            ],
            'priority': 1
        },
        'pediatric': {
            'keywords': [
                '儿童', '婴儿', '小儿', '宝宝', '孩子', '发烧',
                '疫苗', '发育', '新生儿', '幼儿',
                'child', 'infant', 'baby', 'pediatric', 'vaccine',
                'growth', 'development'
            ],
            'priority': 2  # Secondary match
        },
        'dermatology': {
            'keywords': [
                '皮疹', '瘙痒', '皮肤', '湿疹', '荨麻疹', '皮炎',
                '痤疮', '痘痘', '红斑', '水泡',
                'rash', 'itch', 'skin', 'eczema', 'urticaria',
                'dermatitis', 'acne'
            ],
            'priority': 1
        },
        'neurological': {
            'keywords': [
                '头痛', '头晕', '眩晕', '抽搐', '癫痫', '中风',
                '偏瘫', '麻木', '神经痛', '失眠',
                'headache', 'dizziness', 'seizure', 'epilepsy',
                'stroke', 'paralysis', 'neuralgia', 'insomnia'
            ],
            'priority': 1
        }
    }
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vector_service = VectorEmbeddingService(db)
        self.kb_service = KnowledgeBaseVectorizationService(db)
    
    async def select_knowledge_bases(
        self,
        symptoms: str,
        patient_age: int = None,
        patient_gender: str = None,
        top_k: int = 3,
        use_vector_search: bool = True
    ) -> Dict[str, Any]:
        """
        Select relevant knowledge bases / 选择相关RAG知识库
        
        Strategy:
        1. Keyword matching for initial category filtering
        2. Vector similarity search for precise matching
        3. Multi-source fusion with relevance ranking
        
        Args:
            symptoms: Symptom description
            patient_age: Patient age (for pediatric filtering)
            patient_gender: Patient gender
            top_k: Number of top knowledge sources to return
            use_vector_search: Whether to use vector similarity
            
        Returns:
            {
                'sources': List[KnowledgeSource],
                'query_embedding': List[float],
                'selection_reasoning': str,
                'total_chunks': int
            }
        """
        logger.info(f"Selecting knowledge bases for symptoms: {symptoms[:100]}...")
        
        # Step 1: Keyword-based category matching
        keyword_matches = self._match_by_keywords(symptoms, patient_age)
        logger.info(f"Keyword matching found {len(keyword_matches)} categories: {list(keyword_matches.keys())}")
        
        # Step 2: Vector similarity search (if enabled)
        vector_matches = []
        if use_vector_search:
            try:
                vector_matches = await self._search_by_vector(symptoms, keyword_matches.keys())
                logger.info(f"Vector search found {len(vector_matches)} chunks")
            except Exception as e:
                logger.warning(f"Vector search failed: {e}, falling back to keyword only")
        
        # Step 3: Fuse and rank results
        ranked_sources = self._fuse_and_rank(keyword_matches, vector_matches)
        
        # Step 4: Select top-k sources
        selected_sources = ranked_sources[:top_k]
        
        # Generate reasoning
        reasoning = self._generate_reasoning(selected_sources, symptoms)
        
        # Calculate total chunks
        total_chunks = sum(len(source.chunks) for source in selected_sources)
        
        result = {
            'sources': [
                {
                    'category': source.category,
                    'relevance_score': source.relevance_score,
                    'chunks': source.chunks,
                    'selection_reason': source.selection_reason
                }
                for source in selected_sources
            ],
            'selection_reasoning': reasoning,
            'total_chunks': total_chunks,
            'all_matched_categories': list(keyword_matches.keys())
        }
        
        logger.info(f"Selected {len(selected_sources)} knowledge sources with {total_chunks} total chunks")
        
        return result
    
    def _match_by_keywords(
        self,
        symptoms: str,
        patient_age: int = None
    ) -> Dict[str, Dict[str, Any]]:
        """
        Match symptoms to disease categories by keywords / 基于关键词匹配
        """
        symptoms_lower = symptoms.lower()
        matches = {}
        
        for category, data in self.DISEASE_KEYWORDS.items():
            score = 0
            matched_keywords = []
            
            for keyword in data['keywords']:
                if keyword.lower() in symptoms_lower:
                    score += 1
                    matched_keywords.append(keyword)
            
            # Boost pediatric category for young patients
            if category == 'pediatric' and patient_age is not None:
                if patient_age < 18:
                    score += 2  # Significant boost for pediatric patients
            
            if score > 0:
                matches[category] = {
                    'score': score,
                    'priority': data['priority'],
                    'matched_keywords': matched_keywords,
                    'final_score': score * (2 - data['priority'] + 1)  # Higher priority = higher score
                }
        
        # Sort by final score
        return dict(sorted(matches.items(), key=lambda x: x[1]['final_score'], reverse=True))
    
    async def _search_by_vector(
        self,
        symptoms: str,
        categories: List[str]
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base using vector similarity / 基于向量相似度搜索
        """
        results = []
        
        for category in categories:
            try:
                chunks = await self.kb_service.search_similar_chunks(
                    query_text=symptoms,
                    disease_category=category,
                    top_k=5,
                    min_similarity=0.6
                )
                
                for chunk in chunks:
                    chunk['source_category'] = category
                
                results.extend(chunks)
                
            except Exception as e:
                logger.warning(f"Vector search failed for category {category}: {e}")
        
        # Sort by similarity score
        results.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
        
        return results
    
    def _fuse_and_rank(
        self,
        keyword_matches: Dict[str, Dict],
        vector_matches: List[Dict]
    ) -> List[KnowledgeSource]:
        """
        Fuse keyword and vector results and rank / 融合并排序结果
        """
        sources = {}
        
        # Process keyword matches
        for category, match_data in keyword_matches.items():
            sources[category] = {
                'keyword_score': match_data['final_score'],
                'vector_score': 0,
                'chunks': [],
                'reason': f"Keyword match: {', '.join(match_data['matched_keywords'][:3])}"
            }
        
        # Process vector matches
        for chunk in vector_matches:
            category = chunk.get('disease_category', 'unknown')
            similarity = chunk.get('similarity_score', 0)
            
            if category not in sources:
                sources[category] = {
                    'keyword_score': 0,
                    'vector_score': 0,
                    'chunks': [],
                    'reason': "Vector similarity match"
                }
            
            sources[category]['vector_score'] = max(sources[category]['vector_score'], similarity)
            sources[category]['chunks'].append(chunk)
            
            if 'keyword match' not in sources[category]['reason'].lower():
                sources[category]['reason'] = f"Vector similarity: {similarity:.2f}"
        
        # Convert to KnowledgeSource objects and sort
        knowledge_sources = []
        for category, data in sources.items():
            # Combined score: 60% keyword + 40% vector
            combined_score = (data['keyword_score'] * 0.6) + (data['vector_score'] * 0.4)
            
            # Boost if both keyword and vector match
            if data['keyword_score'] > 0 and data['vector_score'] > 0:
                combined_score *= 1.2
            
            knowledge_sources.append(KnowledgeSource(
                category=category,
                relevance_score=combined_score,
                chunks=data['chunks'],
                selection_reason=data['reason']
            ))
        
        # Sort by relevance score
        knowledge_sources.sort(key=lambda x: x.relevance_score, reverse=True)
        
        return knowledge_sources
    
    def _generate_reasoning(
        self,
        selected_sources: List[KnowledgeSource],
        symptoms: str
    ) -> str:
        """
        Generate explanation for knowledge base selection / 生成选择说明
        """
        if not selected_sources:
            return "No specific knowledge base matched. Using general medical knowledge."
        
        reasons = []
        for source in selected_sources:
            reasons.append(f"{source.category} (score: {source.relevance_score:.2f}): {source.selection_reason}")
        
        return "Based on symptom analysis, the following knowledge bases were selected:\n" + "\n".join(reasons)
    
    def get_category_statistics(self) -> Dict[str, int]:
        """Get available disease categories and their statistics"""
        return {
            category: len(data['keywords'])
            for category, data in self.DISEASE_KEYWORDS.items()
        }


# Global service instance
smart_rag_selector = SmartRAGSelector
