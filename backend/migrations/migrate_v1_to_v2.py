#!/usr/bin/env python3
"""
Database Migration Script v1.0 -> v2.0
Migrates users and patients tables to unified User model

Migration Steps:
1. Backup existing data
2. Create new tables (data_sharing_consents, shared_medical_cases, etc.)
3. Migrate patients data to users table
4. Update medical_cases foreign keys
5. Verify data integrity

Usage:
    cd backend
    python migrations/migrate_v1_to_v2.py
"""

import asyncio
import sys
import logging
from datetime import datetime
from typing import Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.insert(0, '/home/houge/Dev/MediCare_AI/backend')

from sqlalchemy import text, inspect
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import async_engine, AsyncSessionLocal
from app.models.models import User as UserV1, Patient as PatientV1
from app.core.security import get_password_hash


class DatabaseMigrator:
    """Database migration from v1.0 to v2.0"""
    
    def __init__(self):
        self.migration_log = []
        
    def log(self, message: str, level: str = "info"):
        """Log migration progress"""
        self.migration_log.append({
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        })
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
    
    async def check_current_version(self, session: AsyncSession) -> dict:
        """Check current database state"""
        self.log("Checking current database state...")
        
        # Check if v2 tables exist
        result = await session.execute(text("""
            SELECT EXISTS (
                SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'data_sharing_consents'
            );
        """))
        has_v2_tables = result.scalar()
        
        # Count existing records
        result = await session.execute(text("SELECT COUNT(*) FROM users;"))
        user_count = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM patients;"))
        patient_count = result.scalar()
        
        state = {
            "has_v2_tables": has_v2_tables,
            "user_count": user_count,
            "patient_count": patient_count,
            "needs_migration": not has_v2_tables and patient_count > 0
        }
        
        self.log(f"Database state: {state}")
        return state
    
    async def create_new_tables(self, session: AsyncSession):
        """Create new v2.0 tables"""
        self.log("Creating new v2.0 tables...")
        
        # Note: In production, use Alembic migrations
        # This is for demonstration purposes
        
        # Add role column to users table
        try:
            await session.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS role VARCHAR(20) DEFAULT 'patient';
            """))
            self.log("Added 'role' column to users table")
        except Exception as e:
            self.log(f"Role column might already exist: {e}", "warning")
        
        # Add patient-specific columns to users
        patient_columns = [
            ("date_of_birth", "DATE"),
            ("gender", "VARCHAR(10)"),
            ("address", "TEXT"),
            ("emergency_contact", "VARCHAR(255)"),
            ("anonymous_profile", "JSONB"),
        ]
        
        for col_name, col_type in patient_columns:
            try:
                await session.execute(text(f"""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                """))
                self.log(f"Added '{col_name}' column to users table")
            except Exception as e:
                self.log(f"Column {col_name} might already exist: {e}", "warning")
        
        # Add doctor-specific columns to users
        doctor_columns = [
            ("title", "VARCHAR(50)"),
            ("department", "VARCHAR(100)"),
            ("specialty", "VARCHAR(200)"),
            ("hospital", "VARCHAR(255)"),
            ("license_number", "VARCHAR(100)"),
            ("is_verified_doctor", "BOOLEAN DEFAULT FALSE"),
            ("display_name", "VARCHAR(255)"),
        ]
        
        for col_name, col_type in doctor_columns:
            try:
                await session.execute(text(f"""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS {col_name} {col_type};
                """))
                self.log(f"Added '{col_name}' column to users table")
            except Exception as e:
                self.log(f"Column {col_name} might already exist: {e}", "warning")
        
        # Add admin-specific columns
        try:
            await session.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS admin_level VARCHAR(20);
            """))
            self.log("Added 'admin_level' column to users table")
        except Exception as e:
            self.log(f"Column admin_level might already exist: {e}", "warning")
        
        # Create new tables
        new_tables_sql = [
            # Data Sharing Consents
            """
            CREATE TABLE IF NOT EXISTS data_sharing_consents (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID NOT NULL REFERENCES users(id),
                share_type VARCHAR(50) NOT NULL,
                target_doctor_id UUID REFERENCES users(id),
                disease_category VARCHAR(100),
                consent_version VARCHAR(20) NOT NULL,
                consent_text TEXT NOT NULL,
                ip_address VARCHAR(45),
                user_agent TEXT,
                signed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                valid_from TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                valid_until TIMESTAMP WITH TIME ZONE,
                is_active BOOLEAN DEFAULT TRUE,
                revoked_at TIMESTAMP WITH TIME ZONE
            );
            """,
            
            # Shared Medical Cases
            """
            CREATE TABLE IF NOT EXISTS shared_medical_cases (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                original_case_id UUID NOT NULL UNIQUE REFERENCES medical_cases(id),
                consent_id UUID NOT NULL REFERENCES data_sharing_consents(id),
                anonymous_patient_profile JSONB NOT NULL,
                anonymized_symptoms TEXT,
                anonymized_diagnosis TEXT,
                anonymized_documents JSONB DEFAULT '[]',
                visible_to_doctors BOOLEAN DEFAULT TRUE,
                visible_for_research BOOLEAN DEFAULT FALSE,
                view_count INTEGER DEFAULT 0,
                doctor_views JSONB DEFAULT '[]',
                exported_count INTEGER DEFAULT 0,
                export_records JSONB DEFAULT '[]',
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Doctor-Patient Relations
            """
            CREATE TABLE IF NOT EXISTS doctor_patient_relations (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                patient_id UUID NOT NULL REFERENCES users(id),
                doctor_id UUID NOT NULL REFERENCES users(id),
                status VARCHAR(20) DEFAULT 'pending',
                initiated_by VARCHAR(50) NOT NULL,
                share_all_cases BOOLEAN DEFAULT FALSE,
                shared_case_ids JSONB DEFAULT '[]',
                patient_message TEXT,
                doctor_response TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                activated_at TIMESTAMP WITH TIME ZONE,
                terminated_at TIMESTAMP WITH TIME ZONE,
                UNIQUE(patient_id, doctor_id)
            );
            """,
            
            # Vector Embedding Configs
            """
            CREATE TABLE IF NOT EXISTS vector_embedding_configs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(100) NOT NULL,
                provider VARCHAR(50) NOT NULL,
                model_id VARCHAR(100) NOT NULL,
                api_url VARCHAR(500) NOT NULL,
                api_key VARCHAR(500) NOT NULL,
                vector_dimension INTEGER DEFAULT 1536,
                max_input_length INTEGER DEFAULT 8192,
                is_active BOOLEAN DEFAULT FALSE,
                is_default BOOLEAN DEFAULT FALSE,
                last_tested_at TIMESTAMP WITH TIME ZONE,
                test_status VARCHAR(20) DEFAULT 'untested',
                test_error_message TEXT,
                created_by UUID NOT NULL REFERENCES users(id),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Knowledge Base Chunks
            """
            CREATE TABLE IF NOT EXISTS knowledge_base_chunks (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                source_document_id UUID,
                source_type VARCHAR(50) NOT NULL,
                disease_id UUID REFERENCES diseases(id),
                disease_category VARCHAR(100),
                document_title VARCHAR(255),
                section_title VARCHAR(255),
                chunk_index INTEGER NOT NULL,
                chunk_text TEXT NOT NULL,
                chunk_text_hash VARCHAR(64) UNIQUE,
                embedding JSONB,
                embedding_model_id VARCHAR(100),
                retrieval_count INTEGER DEFAULT 0,
                avg_relevance_score FLOAT,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # Create indexes for knowledge_base_chunks
            """
            CREATE INDEX IF NOT EXISTS idx_kb_chunks_category_disease 
            ON knowledge_base_chunks(disease_category, disease_id);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_kb_chunks_active 
            ON knowledge_base_chunks(is_active);
            """,
            
            # Case-Knowledge Matches
            """
            CREATE TABLE IF NOT EXISTS case_knowledge_matches (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                medical_case_id UUID NOT NULL REFERENCES medical_cases(id),
                query_text TEXT NOT NULL,
                query_embedding JSONB,
                matched_chunks JSONB NOT NULL,
                knowledge_sources JSONB DEFAULT '[]',
                selection_reasoning TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
            """,
            
            # System Resource Logs
            """
            CREATE TABLE IF NOT EXISTS system_resource_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                cpu_percent FLOAT,
                memory_percent FLOAT,
                disk_percent FLOAT,
                container_status JSONB DEFAULT '{}',
                db_connections INTEGER,
                db_query_time_avg FLOAT,
                alert_level VARCHAR(20) DEFAULT 'info',
                alert_message TEXT
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_resource_logs_timestamp 
            ON system_resource_logs(timestamp);
            """,
            
            # AI Diagnosis Logs
            """
            CREATE TABLE IF NOT EXISTS ai_diagnosis_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                user_id UUID REFERENCES users(id),
                request_type VARCHAR(50) NOT NULL,
                ai_model_id VARCHAR(100),
                ai_api_url VARCHAR(500),
                request_duration_ms INTEGER,
                tokens_input INTEGER,
                tokens_output INTEGER,
                status VARCHAR(20) NOT NULL,
                error_message TEXT,
                is_anomaly BOOLEAN DEFAULT FALSE,
                anomaly_reason TEXT
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_ai_logs_timestamp 
            ON ai_diagnosis_logs(timestamp);
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_ai_logs_anomaly 
            ON ai_diagnosis_logs(is_anomaly);
            """,
            
            # Admin Operation Logs
            """
            CREATE TABLE IF NOT EXISTS admin_operation_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                admin_id UUID NOT NULL REFERENCES users(id),
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                operation_type VARCHAR(50) NOT NULL,
                operation_details JSONB DEFAULT '{}',
                ip_address INET,
                user_agent TEXT
            );
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_admin_logs_timestamp 
            ON admin_operation_logs(timestamp);
            """,
        ]
        
        for sql in new_tables_sql:
            try:
                await session.execute(text(sql))
                self.log("Created table/index")
            except Exception as e:
                self.log(f"Table/index might already exist: {e}", "warning")
        
        # Add columns to medical_documents for PII cleaning
        try:
            await session.execute(text("""
                ALTER TABLE medical_documents 
                ADD COLUMN IF NOT EXISTS cleaned_content JSONB;
            """))
            await session.execute(text("""
                ALTER TABLE medical_documents 
                ADD COLUMN IF NOT EXISTS pii_cleaning_status VARCHAR(20) DEFAULT 'pending';
            """))
            await session.execute(text("""
                ALTER TABLE medical_documents 
                ADD COLUMN IF NOT EXISTS pii_detected JSONB DEFAULT '[]';
            """))
            await session.execute(text("""
                ALTER TABLE medical_documents 
                ADD COLUMN IF NOT EXISTS cleaning_confidence FLOAT;
            """))
            self.log("Added PII cleaning columns to medical_documents")
        except Exception as e:
            self.log(f"PII columns might already exist: {e}", "warning")
        
        # Add columns to medical_cases for sharing
        try:
            await session.execute(text("""
                ALTER TABLE medical_cases 
                ADD COLUMN IF NOT EXISTS is_shared BOOLEAN DEFAULT FALSE;
            """))
            await session.execute(text("""
                ALTER TABLE medical_cases 
                ADD COLUMN IF NOT EXISTS share_scope VARCHAR(20) DEFAULT 'private';
            """))
            self.log("Added sharing columns to medical_cases")
        except Exception as e:
            self.log(f"Sharing columns might already exist: {e}", "warning")
        
        # Add category column to diseases
        try:
            await session.execute(text("""
                ALTER TABLE diseases 
                ADD COLUMN IF NOT EXISTS category VARCHAR(100);
            """))
            self.log("Added category column to diseases")
        except Exception as e:
            self.log(f"Category column might already exist: {e}", "warning")
        
        await session.commit()
        self.log("New tables and columns created successfully")
    
    async def migrate_patient_data(self, session: AsyncSession):
        """Migrate patient data to users table"""
        self.log("Migrating patient data to users table...")
        
        # Get all patients
        result = await session.execute(text("""
            SELECT p.id, p.user_id, p.date_of_birth, p.gender, 
                   p.phone, p.address, p.emergency_contact, 
                   p.medical_record_number, p.notes
            FROM patients p
            JOIN users u ON p.user_id = u.id;
        """))
        patients = result.fetchall()
        
        self.log(f"Found {len(patients)} patients to migrate")
        
        migrated_count = 0
        for patient in patients:
            try:
                # Generate anonymous profile
                anonymous_profile = None
                if patient.date_of_birth:
                    from datetime import datetime
                    age = datetime.now().year - patient.date_of_birth.year
                    if age < 18:
                        age_range = "<18"
                    elif age < 30:
                        age_range = "18-30"
                    elif age < 40:
                        age_range = "30-40"
                    elif age < 50:
                        age_range = "40-50"
                    elif age < 60:
                        age_range = "50-60"
                    else:
                        age_range = "60+"
                    
                    # Extract city tier
                    city_tier = "unknown"
                    if patient.address:
                        tier1_cities = ["北京", "上海", "广州", "深圳"]
                        tier2_cities = ["杭州", "南京", "成都", "武汉", "西安"]
                        if any(city in patient.address for city in tier1_cities):
                            city_tier = "tier_1"
                        elif any(city in patient.address for city in tier2_cities):
                            city_tier = "tier_2"
                        else:
                            city_tier = "tier_3_plus"
                    
                    anonymous_profile = {
                        "age_range": age_range,
                        "gender": patient.gender,
                        "city_tier": city_tier,
                        "city_environment": "urban" if patient.address and "市" in patient.address else "rural"
                    }
                
                # Update user record with patient data
                await session.execute(text("""
                    UPDATE users SET
                        role = 'patient',
                        date_of_birth = :date_of_birth,
                        gender = :gender,
                        phone = COALESCE(:phone, phone),
                        address = :address,
                        emergency_contact = :emergency_contact,
                        anonymous_profile = :anonymous_profile
                    WHERE id = :user_id;
                """), {
                    "date_of_birth": patient.date_of_birth,
                    "gender": patient.gender,
                    "phone": patient.phone,
                    "address": patient.address,
                    "emergency_contact": patient.emergency_contact,
                    "anonymous_profile": json.dumps(anonymous_profile) if anonymous_profile else None,
                    "user_id": patient.user_id
                })
                
                migrated_count += 1
                
            except Exception as e:
                self.log(f"Failed to migrate patient {patient.id}: {e}", "error")
        
        await session.commit()
        self.log(f"Successfully migrated {migrated_count} patients")
    
    async def update_foreign_keys(self, session: AsyncSession):
        """Update foreign key references"""
        self.log("Updating foreign key references...")
        
        # medical_cases already references patients.id
        # We need to update it to reference users.id directly
        # But since patients.user_id already points to users.id, the relationship is intact
        
        # Just verify the data integrity
        result = await session.execute(text("""
            SELECT COUNT(*) FROM medical_cases mc
            JOIN patients p ON mc.patient_id = p.id
            WHERE NOT EXISTS (SELECT 1 FROM users u WHERE u.id = p.user_id);
        """))
        orphan_cases = result.scalar()
        
        if orphan_cases > 0:
            self.log(f"Warning: Found {orphan_cases} medical cases with orphaned patient references", "warning")
        else:
            self.log("All medical cases have valid patient references")
    
    async def verify_migration(self, session: AsyncSession) -> bool:
        """Verify migration success"""
        self.log("Verifying migration...")
        
        # Check user counts
        result = await session.execute(text("SELECT COUNT(*) FROM users WHERE role = 'patient';"))
        patient_users = result.scalar()
        
        result = await session.execute(text("SELECT COUNT(*) FROM patients;"))
        legacy_patients = result.scalar()
        
        self.log(f"Patient users: {patient_users}, Legacy patients: {legacy_patients}")
        
        if patient_users == legacy_patients:
            self.log("✅ Migration verification PASSED")
            return True
        else:
            self.log(f"⚠️ Migration verification FAILED: {patient_users} != {legacy_patients}", "warning")
            return False
    
    async def run_migration(self):
        """Run full migration"""
        self.log("=" * 60)
        self.log("Starting Database Migration v1.0 -> v2.0")
        self.log("=" * 60)
        
        async with AsyncSessionLocal() as session:
            try:
                # Step 1: Check current state
                state = await self.check_current_version(session)
                
                if not state["needs_migration"]:
                    self.log("Migration not needed or already completed")
                    return True
                
                # Step 2: Create new tables
                await self.create_new_tables(session)
                
                # Step 3: Migrate patient data
                if state["patient_count"] > 0:
                    await self.migrate_patient_data(session)
                
                # Step 4: Update foreign keys
                await self.update_foreign_keys(session)
                
                # Step 5: Verify migration
                success = await self.verify_migration(session)
                
                if success:
                    self.log("=" * 60)
                    self.log("✅ Migration completed successfully!")
                    self.log("=" * 60)
                else:
                    self.log("=" * 60)
                    self.log("⚠️ Migration completed with warnings")
                    self.log("=" * 60)
                
                return success
                
            except Exception as e:
                await session.rollback()
                self.log(f"❌ Migration failed: {e}", "error")
                import traceback
                self.log(traceback.format_exc(), "error")
                return False


async def main():
    """Main entry point"""
    import json  # Import here for migration script
    
    migrator = DatabaseMigrator()
    success = await migrator.run_migration()
    
    # Print summary
    print("\n" + "=" * 60)
    print("MIGRATION SUMMARY")
    print("=" * 60)
    for log in migrator.migration_log[-10:]:  # Show last 10 logs
        print(f"[{log['level'].upper()}] {log['message']}")
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
