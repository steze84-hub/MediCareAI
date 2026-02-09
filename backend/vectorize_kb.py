import asyncio
import sys
sys.path.insert(0, '/app')

from app.db.database import AsyncSessionLocal
from app.services.kb_vectorization_service import KnowledgeBaseVectorizationService
from pathlib import Path
import uuid
from datetime import datetime

async def vectorize_pediatric_asthma():
    """向量化儿童支气管哮喘指南"""
    async with AsyncSessionLocal() as db:
        service = KnowledgeBaseVectorizationService(db)
        
        # 文档目录
        doc_dir = Path("/app/data/knowledge_bases/diseases/pediatric_bronchial_asthma")
        
        if not doc_dir.exists():
            print("❌ 文档目录不存在")
            return
        
        # 处理每个md文件
        md_files = list(doc_dir.glob("*.md"))
        print(f"📚 找到 {len(md_files)} 个文档文件")
        
        for file_path in md_files:
            try:
                print(f"\n📝 处理文档: {file_path.name}")
                
                # 读取内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 提取文档标题（去掉前缀）
                document_title = file_path.name.replace('MinerU_markdown_', '').replace('.md', '')
                
                # 向量化文档
                result = await service.vectorize_markdown_document(
                    document_content=content,
                    document_title=document_title,
                    disease_category='respiratory',  # 使用呼吸科分类
                    disease_id=uuid.uuid4(),  # 临时ID
                    source_type='disease_guideline',
                    created_by=None
                )
                
                print(f"✅ 完成: {result['new_chunks']} 个新块, {result['duplicates']} 个重复")
                
            except Exception as e:
                print(f"❌ 处理失败 {file_path.name}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n🎉 所有文档处理完成")

if __name__ == "__main__":
    asyncio.run(vectorize_pediatric_asthma())
