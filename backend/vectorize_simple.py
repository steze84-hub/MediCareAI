import asyncio
import sys
sys.path.insert(0, '/app')

from app.db.database import AsyncSessionLocal
from app.models.models import KnowledgeBaseChunk, VectorEmbeddingConfig
from pathlib import Path
import uuid
from datetime import datetime
import hashlib
import httpx

async def generate_embedding(text, config):
    """单个文本生成嵌入"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{config.api_url}embeddings",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {config.api_key}"
            },
            json={
                "model": config.model_id or "text-embedding-v3",
                "input": {
                    "texts": [text]
                },
                "parameters": {
                    "text_type": "document"
                }
            }
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'output' in result and 'embeddings' in result['output']:
                return result['output']['embeddings'][0]['embedding']
        else:
            print(f"  API错误: {response.status_code} - {response.text[:100]}")
            return None

async def vectorize_document(file_path, config, db):
    """向量化单个文档"""
    print(f"\n📝 处理: {file_path.name}")
    
    # 读取内容
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    document_title = file_path.name.replace('MinerU_markdown_', '').replace('.md', '')
    
    # 按行分割并合并成合理大小的块
    lines = content.split('\n')
    chunks = []
    current_chunk = ""
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # 如果当前块加上新行超过800字符，保存当前块
        if len(current_chunk) + len(line) > 800:
            if len(current_chunk) > 100:  # 只保存大于100字符的块
                chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += "\n" + line if current_chunk else line
    
    # 保存最后一个块
    if len(current_chunk) > 100:
        chunks.append(current_chunk)
    
    print(f"  创建 {len(chunks)} 个文本块")
    
    # 处理每个块
    success_count = 0
    for i, chunk_text in enumerate(chunks[:20]):  # 先处理前20个块测试
        try:
            # 检查长度
            if len(chunk_text.strip()) < 50:
                continue
            
            # 检查是否已存在
            from sqlalchemy import select
            text_hash = hashlib.sha256(chunk_text.encode()).hexdigest()
            stmt = select(KnowledgeBaseChunk).where(
                KnowledgeBaseChunk.chunk_text_hash == text_hash
            )
            result = await db.execute(stmt)
            if result.scalar_one_or_none():
                continue
            
            # 生成嵌入
            embedding = await generate_embedding(chunk_text, config)
            if not embedding:
                continue
            
            # 保存到数据库
            kb_chunk = KnowledgeBaseChunk(
                id=uuid.uuid4(),
                source_type='disease_guideline',
                disease_id=uuid.uuid4(),
                disease_category='respiratory',
                document_title=document_title,
                section_title=f"Section_{i}",
                chunk_index=i,
                chunk_text=chunk_text[:2000],  # 限制长度
                chunk_text_hash=text_hash,
                embedding=embedding,
                embedding_model_id=config.model_id,
                is_active=True,
                created_at=datetime.utcnow()
            )
            db.add(kb_chunk)
            await db.commit()
            
            success_count += 1
            if success_count % 5 == 0:
                print(f"  ✅ 已处理 {success_count} 个块")
                
        except Exception as e:
            print(f"  ❌ 块 {i} 处理失败: {e}")
            await db.rollback()
    
    print(f"  ✅ 完成: {success_count} 个块已保存")

async def main():
    async with AsyncSessionLocal() as db:
        # 获取配置
        from sqlalchemy import select
        stmt = select(VectorEmbeddingConfig).where(VectorEmbeddingConfig.is_active == True)
        result = await db.execute(stmt)
        config = result.scalar_one_or_none()
        
        if not config:
            print("❌ 没有找到活跃的Embedding配置")
            return
        
        print(f"✅ 使用配置: {config.provider} / {config.model_id}")
        
        # 文档目录
        doc_dir = Path("/app/data/knowledge_bases/diseases/pediatric_bronchial_asthma")
        if not doc_dir.exists():
            print("❌ 文档目录不存在")
            return
        
        # 处理文档
        md_files = list(doc_dir.glob("*.md"))
        print(f"📚 找到 {len(md_files)} 个文档")
        
        for file_path in md_files[:1]:  # 先处理第一个文档
            await vectorize_document(file_path, config, db)
        
        print("\n🎉 处理完成")

if __name__ == "__main__":
    asyncio.run(main())
