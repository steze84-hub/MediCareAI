import asyncio
import sys
sys.path.insert(0, '/app')

from app.db.database import AsyncSessionLocal
from app.services.kb_vectorization_service import KnowledgeBaseVectorizationService
from app.services.vector_embedding_service import VectorEmbeddingService
from app.models.models import KnowledgeBaseChunk
from pathlib import Path
import uuid
from datetime import datetime
import hashlib

class DocumentChunker:
    """简单的文档分块器"""
    def __init__(self, chunk_size=1000, chunk_overlap=100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def split_text(self, text):
        """将文本分块"""
        if not text or not text.strip():
            return []
        
        chunks = []
        start = 0
        text_len = len(text)
        
        while start < text_len:
            end = min(start + self.chunk_size, text_len)
            chunk = text[start:end].strip()
            if chunk:  # 只添加非空块
                chunks.append(chunk)
            start = end - self.chunk_overlap if end < text_len else end
        
        return chunks

async def vectorize_pediatric_asthma():
    """向量化儿童支气管哮喘指南"""
    async with AsyncSessionLocal() as db:
        service = KnowledgeBaseVectorizationService(db)
        vector_service = VectorEmbeddingService(db)
        chunker = DocumentChunker(chunk_size=800, chunk_overlap=100)
        
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
                
                # 简单的分块：按段落分割
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                
                all_chunks = []
                for i, para in enumerate(paragraphs):
                    # 跳过太短的段落
                    if len(para) < 50:
                        continue
                    
                    # 计算hash
                    text_hash = hashlib.sha256(para.encode()).hexdigest()
                    
                    # 检查是否已存在
                    from sqlalchemy import select
                    stmt = select(KnowledgeBaseChunk).where(
                        KnowledgeBaseChunk.chunk_text_hash == text_hash
                    )
                    result = await db.execute(stmt)
                    existing = result.scalar_one_or_none()
                    
                    if existing:
                        print(f"  跳过重复块 {i}")
                        continue
                    
                    # 创建chunk
                    chunk = KnowledgeBaseChunk(
                        id=uuid.uuid4(),
                        source_type='disease_guideline',
                        disease_id=uuid.uuid4(),
                        disease_category='respiratory',
                        document_title=document_title,
                        section_title=f"段落_{i}",
                        chunk_index=i,
                        chunk_text=para,
                        chunk_text_hash=text_hash,
                        is_active=True,
                        created_at=datetime.utcnow()
                    )
                    
                    all_chunks.append(chunk)
                    
                    # 每10个块处理一次
                    if len(all_chunks) >= 10:
                        await process_chunks(all_chunks, vector_service, db)
                        all_chunks = []
                
                # 处理剩余的块
                if all_chunks:
                    await process_chunks(all_chunks, vector_service, db)
                
                print(f"✅ 文档处理完成: {document_title}")
                
            except Exception as e:
                print(f"❌ 处理失败 {file_path.name}: {e}")
                import traceback
                traceback.print_exc()
        
        print("\n🎉 所有文档处理完成")

async def process_chunks(chunks, vector_service, db):
    """处理一批chunks"""
    if not chunks:
        return
    
    # 过滤空文本
    valid_chunks = [c for c in chunks if c.chunk_text and c.chunk_text.strip()]
    if not valid_chunks:
        print("  没有有效的文本块")
        return
    
    texts = [c.chunk_text for c in valid_chunks]
    
    try:
        print(f"  生成 {len(texts)} 个块的嵌入向量...")
        embeddings = await vector_service.generate_embeddings_batch(texts)
        
        # 更新chunks
        config = await vector_service.get_active_config()
        for chunk, embedding in zip(valid_chunks, embeddings):
            chunk.embedding = embedding
            chunk.embedding_model_id = config.model_id if config else 'unknown'
            db.add(chunk)
        
        await db.commit()
        print(f"  ✅ 已保存 {len(valid_chunks)} 个块")
        
    except Exception as e:
        print(f"  ❌ 生成嵌入失败: {e}")
        await db.rollback()
        raise

if __name__ == "__main__":
    asyncio.run(vectorize_pediatric_asthma())
