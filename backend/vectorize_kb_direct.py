import asyncio
import sys
sys.path.insert(0, '/app')

from app.db.database import AsyncSessionLocal
from app.services.kb_vectorization_service import KnowledgeBaseVectorizationService
from pathlib import Path
import uuid

async def main():
    async with AsyncSessionLocal() as db:
        service = KnowledgeBaseVectorizationService(db)
        
        # 读取文档
        doc_path = Path("/app/data/knowledge_bases/diseases/pediatric_bronchial_asthma/MinerU_markdown_儿童支气管哮喘规范化诊治建议（2020年版）_2017240024815718400.md")
        
        with open(doc_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📄 文档大小: {len(content)} 字符")
        print("🔄 开始向量化...")
        
        try:
            result = await service.vectorize_markdown_document(
                document_content=content,
                document_title="儿童支气管哮喘规范化诊治建议（2020年版）",
                disease_category="respiratory",
                disease_id=uuid.uuid4(),
                source_type="disease_guideline"
            )
            
            print(f"✅ 向量化完成!")
            print(f"   总块数: {result['total_chunks']}")
            print(f"   新块数: {result['new_chunks']}")
            print(f"   重复块: {result['duplicates']}")
            
        except Exception as e:
            print(f"❌ 失败: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
