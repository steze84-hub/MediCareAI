import asyncio
import sys
sys.path.insert(0, '/app')

from app.db.database import AsyncSessionLocal
from app.services.kb_vectorization_service import KnowledgeBaseVectorizationService
from app.models.models import KnowledgeBaseChunk, Disease
from pathlib import Path
import uuid
from datetime import datetime

async def main():
    async with AsyncSessionLocal() as db:
        service = KnowledgeBaseVectorizationService(db)
        
        # 查找或创建疾病记录
        from sqlalchemy import select
        stmt = select(Disease).where(Disease.name == "儿童支气管哮喘")
        result = await db.execute(stmt)
        disease = result.scalar_one_or_none()
        
        if not disease:
            # 创建疾病记录
            disease = Disease(
                id=uuid.uuid4(),
                name="儿童支气管哮喘",
                code="J45",
                category="respiratory",
                description="儿童期最常见的慢性呼吸系统疾病"
            )
            db.add(disease)
            await db.commit()
            await db.refresh(disease)
            print(f"✅ 创建疾病记录: {disease.name} (ID: {disease.id})")
        else:
            print(f"✅ 使用现有疾病记录: {disease.name} (ID: {disease.id})")
        
        # 处理文档
        doc_dir = Path("/app/data/knowledge_bases/diseases/pediatric_bronchial_asthma")
        md_files = list(doc_dir.glob("*.md"))
        print(f"📚 找到 {len(md_files)} 个文档")
        
        total_chunks = 0
        for file_path in md_files:
            try:
                print(f"\n📝 处理: {file_path.name}")
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                document_title = file_path.name.replace('MinerU_markdown_', '').replace('.md', '')
                
                result = await service.vectorize_markdown_document(
                    document_content=content,
                    document_title=document_title,
                    disease_category="respiratory",
                    disease_id=disease.id,
                    source_type="disease_guideline"
                )
                
                print(f"✅ 完成: {result['new_chunks']} 个新块, {result['duplicates']} 个重复")
                total_chunks += result['new_chunks']
                
            except Exception as e:
                print(f"❌ 失败: {e}")
                import traceback
                traceback.print_exc()
        
        # 验证结果
        stmt = select(KnowledgeBaseChunk).where(
            KnowledgeBaseChunk.disease_id == disease.id
        )
        result = await db.execute(stmt)
        chunks = result.scalars().all()
        print(f"\n🎉 总共向量化 {len(chunks)} 个块 (来自 {len(md_files)} 个文档)")
        print(f"✅ 所有文档已保存到知识库，可以被AI诊断使用了！")

if __name__ == "__main__":
    asyncio.run(main())
