import asyncio
import sys
sys.path.insert(0, '/opt/medicare-ai/backend')

from app.db.database import Base, engine
from app.models import models

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("OK")

if __name__ == "__main__":
    asyncio.run(init_db())
