import asyncio
import sys
sys.path.insert(0, '/app')

from app.db.database import AsyncSessionLocal
from app.models.models import VectorEmbeddingConfig
import uuid
from datetime import datetime

ADMIN_ID = 'b0771813-f5cf-4b90-83be-ed3cda0e2dac'

async def create_embedding_config():
    """创建向量嵌入配置"""
    async with AsyncSessionLocal() as db:
        # 检查是否已有配置
        from sqlalchemy import select
        stmt = select(VectorEmbeddingConfig).where(VectorEmbeddingConfig.is_active == True)
        result = await db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            print(f"✅ 已有活跃配置: {existing.provider} / {existing.model_id}")
            return
        
        # 创建新配置
        config = VectorEmbeddingConfig(
            id=uuid.uuid4(),
            name='DashScope Text Embedding V3',
            provider='dashscope',
            model_id='text-embedding-v3',
            api_url='https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings',
            api_key='sk-placeholder',
            vector_dimension=1024,
            max_input_length=8192,
            is_active=True,
            is_default=True,
            created_by=uuid.UUID(ADMIN_ID),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(config)
        await db.commit()
        
        print(f"✅ 已创建向量嵌入配置: {config.provider} / {config.model_id}")
        print(f"   维度: {config.vector_dimension}")
        print(f"   API: {config.api_url}")

if __name__ == "__main__":
    asyncio.run(create_embedding_config())
