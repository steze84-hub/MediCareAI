"""
Migration: Add 'comprehensive_diagnosis' to request_type enum

This migration adds the new 'comprehensive_diagnosis' value to the request_type enum
used in the ai_diagnosis_logs table.

Run this migration:
    docker-compose exec postgres psql -U medicare_user -d medicare_ai -f /app/migrations/add_comprehensive_diagnosis_enum.sql
"""

# PostgreSQL SQL to add enum value
ADD_ENUM_VALUE_SQL = """
-- Add new value to request_type enum
ALTER TYPE request_type ADD VALUE IF NOT EXISTS 'comprehensive_diagnosis';
"""

# Alternative: If using Alembic or SQLAlchemy migrations
# This can be run as a Python script

import asyncio
import asyncpg
from app.core.config import settings


async def migrate():
    """Execute the migration"""
    conn = await asyncpg.connect(settings.database_url)
    
    try:
        # Add the new enum value
        await conn.execute("""
            ALTER TYPE request_type ADD VALUE IF NOT EXISTS 'comprehensive_diagnosis';
        """)
        print("✅ Successfully added 'comprehensive_diagnosis' to request_type enum")
        
        # Verify the change
        result = await conn.fetch("""
            SELECT enumlabel FROM pg_enum WHERE enumtypid = 'request_type'::regtype;
        """)
        values = [row['enumlabel'] for row in result]
        print(f"Current enum values: {values}")
        
        if 'comprehensive_diagnosis' in values:
            print("✅ Verification successful: comprehensive_diagnosis is in the enum")
        else:
            print("❌ Verification failed: comprehensive_diagnosis not found")
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise
    finally:
        await conn.close()


if __name__ == "__main__":
    import sys
    sys.path.insert(0, '/app')
    
    # Run the migration
    asyncio.run(migrate())
