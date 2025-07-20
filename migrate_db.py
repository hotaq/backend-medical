#!/usr/bin/env python3
"""
Database Migration Script for Medical Triage-BOTS System

This script handles database initialization, schema creation, and data migrations
for the Medical Triage-BOTS system. It supports both SQLite and PostgreSQL.

Usage:
    python migrate_db.py                    # Run all migrations
    python migrate_db.py --init             # Initialize database only
    python migrate_db.py --seed             # Add sample data
    python migrate_db.py --reset            # Reset database (DANGER!)
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict, Any

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database.config import DatabaseManager, engine
    from app.database.models import (
        Base, Patient, TriageCase, CaseStructuredData, CaseImage,
        CaseProcessing, TriageResult, SystemAuditLog, ModelPerformanceMetrics,
        DataTypeEnum, UrgencyLevelEnum, ProcessingStatusEnum, StructuredDataTypeEnum
    )
except ImportError as e:
    print(f"Error importing required modules: {e}")
    print("Please ensure you're running from the correct directory and all dependencies are installed.")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migration.log')
    ]
)
logger = logging.getLogger(__name__)


class DatabaseMigrator:
    """Handles database migrations and initialization"""

    def __init__(self):
        self.db_manager = DatabaseManager()

    async def check_database_connection(self) -> bool:
        """Check if database connection is working"""
        try:
            async with self.db_manager.get_session() as session:
                result = await session.execute(text("SELECT 1"))
                test_value = result.scalar()
                if test_value == 1:
                    logger.info("✅ Database connection successful")
                    return True
                else:
                    logger.error("❌ Database connection test failed")
                    return False
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False

    async def init_database(self) -> bool:
        """Initialize database schema"""
        try:
            logger.info("🚀 Initializing database schema...")

            async with engine.begin() as conn:
                # Create all tables
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables created successfully")

            # Log the initialization
            await self.log_migration_event("database_initialized", {
                "timestamp": datetime.now().isoformat(),
                "tables_created": len(Base.metadata.tables),
                "table_names": list(Base.metadata.tables.keys())
            })

            return True

        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}")
            return False

    async def check_existing_data(self) -> Dict[str, int]:
        """Check existing data in the database"""
        try:
            async with self.db_manager.get_session() as session:
                # Count existing records
                counts = {}

                # Count patients
                result = await session.execute(text("SELECT COUNT(*) FROM patients"))
                counts['patients'] = result.scalar() or 0

                # Count triage cases
                result = await session.execute(text("SELECT COUNT(*) FROM triage_cases"))
                counts['triage_cases'] = result.scalar() or 0

                # Count processing records
                result = await session.execute(text("SELECT COUNT(*) FROM case_processing"))
                counts['processing_records'] = result.scalar() or 0

                # Count triage results
                result = await session.execute(text("SELECT COUNT(*) FROM triage_results"))
                counts['triage_results'] = result.scalar() or 0

                logger.info(f"📊 Existing data counts: {counts}")
                return counts

        except Exception as e:
            logger.warning(f"⚠️ Could not check existing data: {e}")
            return {}

    async def seed_sample_data(self) -> bool:
        """Add sample data for testing and demonstration"""
        try:
            logger.info("🌱 Seeding sample data...")

            async with self.db_manager.get_session() as session:
                # Create sample patients
                sample_patients = [
                    Patient(
                        patient_id="P12345",
                        age=65,
                        gender="female",
                        medical_record_number="MRN-789456"
                    ),
                    Patient(
                        patient_id="P67890",
                        age=45,
                        gender="male",
                        medical_record_number="MRN-123789"
                    ),
                    Patient(
                        patient_id="P11111",
                        age=72,
                        gender="female",
                        medical_record_number="MRN-456123"
                    ),
                    Patient(
                        patient_id="P22222",
                        age=28,
                        gender="male",
                        medical_record_number="MRN-789012"
                    )
                ]

                for patient in sample_patients:
                    session.add(patient)

                await session.flush()  # Get patient IDs

                # Create sample triage cases
                sample_cases = [
                    TriageCase(
                        case_id="CASE_20241220_001",
                        patient_id=sample_patients[0].id,
                        symptoms_text="Blurred vision and seeing dark spots for the past week",
                        chief_complaint="Vision problems",
                        medical_history="Type 2 diabetes diagnosed 5 years ago",
                        primary_data_type=DataTypeEnum.MIXED,
                        priority_level=UrgencyLevelEnum.HIGH,
                        target_department="ophthalmology",
                        requires_vision_analysis=True,
                        requires_text_analysis=True,
                        requires_structured_analysis=True
                    ),
                    TriageCase(
                        case_id="CASE_20241220_002",
                        patient_id=sample_patients[1].id,
                        symptoms_text="Severe chest pain radiating to left arm",
                        chief_complaint="Chest pain",
                        medical_history="Hypertension, family history of heart disease",
                        primary_data_type=DataTypeEnum.TEXT,
                        priority_level=UrgencyLevelEnum.CRITICAL,
                        target_department="emergency",
                        requires_text_analysis=True
                    ),
                    TriageCase(
                        case_id="CASE_20241220_003",
                        patient_id=sample_patients[2].id,
                        symptoms_text="Sudden onset severe headache with nausea",
                        chief_complaint="Worst headache of life",
                        medical_history="Previous stroke 3 years ago",
                        primary_data_type=DataTypeEnum.MIXED,
                        priority_level=UrgencyLevelEnum.CRITICAL,
                        target_department="emergency",
                        requires_text_analysis=True,
                        requires_structured_analysis=True
                    ),
                    TriageCase(
                        case_id="CASE_20241220_004",
                        patient_id=sample_patients[3].id,
                        symptoms_text="Mild sore throat for 3 days, no fever",
                        chief_complaint="Sore throat",
                        medical_history="No significant medical history",
                        primary_data_type=DataTypeEnum.TEXT,
                        priority_level=UrgencyLevelEnum.LOW,
                        target_department="general_medicine",
                        requires_text_analysis=True
                    )
                ]

                for case in sample_cases:
                    session.add(case)

                await session.flush()  # Get case IDs

                # Add sample structured data
                sample_structured_data = [
                    CaseStructuredData(
                        triage_case_id=sample_cases[0].id,
                        data_type=StructuredDataTypeEnum.BLOOD_TEST,
                        data={
                            "fasting_glucose": 185,
                            "hba1c": 8.7,
                            "total_cholesterol": 240
                        },
                        units={
                            "fasting_glucose": "mg/dL",
                            "hba1c": "%",
                            "total_cholesterol": "mg/dL"
                        }
                    ),
                    CaseStructuredData(
                        triage_case_id=sample_cases[2].id,
                        data_type=StructuredDataTypeEnum.VITAL_SIGNS,
                        data={
                            "blood_pressure_systolic": 190,
                            "blood_pressure_diastolic": 110,
                            "heart_rate": 95,
                            "temperature": 99.2
                        },
                        units={
                            "blood_pressure_systolic": "mmHg",
                            "blood_pressure_diastolic": "mmHg",
                            "heart_rate": "bpm",
                            "temperature": "°F"
                        }
                    )
                ]

                for data in sample_structured_data:
                    session.add(data)

                # Add sample images
                sample_images = [
                    CaseImage(
                        triage_case_id=sample_cases[0].id,
                        image_path="/uploads/sample_retinal_scan.jpg",
                        image_type="retinal",
                        file_size=2048576,
                        processed=True
                    )
                ]

                for image in sample_images:
                    session.add(image)

                # Add sample processing records
                base_time = datetime.now() - timedelta(minutes=30)
                sample_processing = [
                    CaseProcessing(
                        triage_case_id=sample_cases[0].id,
                        agent_type="text_bot",
                        processing_step="analysis",
                        status=ProcessingStatusEnum.COMPLETED,
                        raw_output={"risk_score": 0.75, "confidence": 0.85},
                        synthesized_output="Patient presents with diabetic retinopathy symptoms requiring urgent ophthalmology consultation.",
                        llm_model_used="medical-llm-v1",
                        processing_time_ms=2300,
                        started_at=base_time,
                        completed_at=base_time + timedelta(seconds=2.3)
                    ),
                    CaseProcessing(
                        triage_case_id=sample_cases[0].id,
                        agent_type="vision_bot",
                        processing_step="analysis",
                        status=ProcessingStatusEnum.COMPLETED,
                        raw_output={"severity": "moderate", "confidence": 0.78},
                        synthesized_output="Retinal image shows signs of diabetic retinopathy with microaneurysms.",
                        llm_model_used="vision-model-v1",
                        processing_time_ms=3100,
                        started_at=base_time + timedelta(seconds=3),
                        completed_at=base_time + timedelta(seconds=6.1)
                    )
                ]

                for processing in sample_processing:
                    session.add(processing)

                # Add sample triage results
                sample_results = [
                    TriageResult(
                        triage_case_id=sample_cases[0].id,
                        final_triage_score=0.75,
                        urgency_level=UrgencyLevelEnum.HIGH,
                        estimated_wait_time=15,
                        recommendations=[
                            "Immediate ophthalmology consultation required",
                            "Blood glucose management review needed",
                            "Monitor for diabetic retinopathy progression"
                        ],
                        clinical_notes="Patient with diabetes showing signs of retinopathy progression",
                        vision_analysis_completed=True,
                        text_analysis_completed=True,
                        structured_analysis_completed=True,
                        confidence_score=0.82
                    ),
                    TriageResult(
                        triage_case_id=sample_cases[1].id,
                        final_triage_score=0.92,
                        urgency_level=UrgencyLevelEnum.CRITICAL,
                        estimated_wait_time=0,
                        recommendations=[
                            "IMMEDIATE emergency department evaluation",
                            "Cardiac monitoring required",
                            "Consider acute coronary syndrome"
                        ],
                        clinical_notes="High-risk presentation for acute coronary syndrome",
                        text_analysis_completed=True,
                        confidence_score=0.95
                    )
                ]

                for result in sample_results:
                    session.add(result)

                # Add sample audit logs
                sample_audit = [
                    SystemAuditLog(
                        event_type="case_created",
                        entity_type="triage_case",
                        entity_id=sample_cases[0].id,
                        event_data={
                            "case_id": "CASE_20241220_001",
                            "priority": "high",
                            "department": "ophthalmology"
                        }
                    ),
                    SystemAuditLog(
                        event_type="processing_completed",
                        entity_type="triage_case",
                        entity_id=sample_cases[0].id,
                        event_data={
                            "processing_time_ms": 5400,
                            "agents_used": ["text_bot", "vision_bot"],
                            "final_score": 0.75
                        }
                    )
                ]

                for audit in sample_audit:
                    session.add(audit)

                # Add sample performance metrics
                sample_metrics = ModelPerformanceMetrics(
                    model_type="vision_cnn",
                    model_version="v1.0.0",
                    accuracy=0.87,
                    precision=0.84,
                    recall=0.89,
                    f1_score=0.86,
                    avg_processing_time_ms=2800.0,
                    total_predictions=150,
                    successful_predictions=142,
                    measurement_period_start=datetime.now() - timedelta(days=7),
                    measurement_period_end=datetime.now(),
                    notes="Weekly performance measurement"
                )
                session.add(sample_metrics)

                await session.commit()
                logger.info("✅ Sample data seeded successfully")

                # Log the seeding
                await self.log_migration_event("sample_data_seeded", {
                    "patients": len(sample_patients),
                    "cases": len(sample_cases),
                    "structured_data": len(sample_structured_data),
                    "images": len(sample_images),
                    "processing_records": len(sample_processing),
                    "results": len(sample_results)
                })

                return True

        except Exception as e:
            logger.error(f"❌ Sample data seeding failed: {e}")
            return False

    async def reset_database(self) -> bool:
        """Reset database by dropping and recreating all tables"""
        try:
            logger.warning("⚠️ RESETTING DATABASE - ALL DATA WILL BE LOST!")

            async with engine.begin() as conn:
                # Drop all tables
                await conn.run_sync(Base.metadata.drop_all)
                logger.info("🗑️ All tables dropped")

                # Recreate all tables
                await conn.run_sync(Base.metadata.create_all)
                logger.info("✅ Database tables recreated")

            # Log the reset
            await self.log_migration_event("database_reset", {
                "timestamp": datetime.now().isoformat(),
                "action": "complete_reset"
            })

            return True

        except Exception as e:
            logger.error(f"❌ Database reset failed: {e}")
            return False

    async def log_migration_event(self, event_type: str, event_data: Dict[str, Any]):
        """Log migration events to audit log"""
        try:
            async with self.db_manager.get_session() as session:
                audit_log = SystemAuditLog(
                    event_type=f"migration_{event_type}",
                    entity_type="database",
                    event_data=event_data,
                    user_id="system_migrator"
                )
                session.add(audit_log)
                await session.commit()
        except Exception as e:
            logger.warning(f"Could not log migration event: {e}")

    async def run_migrations(self, init_only: bool = False, seed_data: bool = False, reset: bool = False) -> bool:
        """Run the complete migration process"""
        try:
            logger.info("🏥 Medical Triage-BOTS Database Migration")
            logger.info("=" * 50)

            # Check database connection
            if not await self.check_database_connection():
                return False

            # Reset database if requested
            if reset:
                logger.warning("🚨 Database reset requested!")
                confirm = input("Are you sure you want to reset the database? This will DELETE ALL DATA! (yes/no): ")
                if confirm.lower() != 'yes':
                    logger.info("Database reset cancelled")
                    return False

                if not await self.reset_database():
                    return False

            # Initialize database schema
            if not await self.init_database():
                return False

            if init_only:
                logger.info("✅ Database initialization complete")
                return True

            # Check existing data
            existing_counts = await self.check_existing_data()

            # Seed sample data if requested or if database is empty
            if seed_data or all(count == 0 for count in existing_counts.values()):
                if not await self.seed_sample_data():
                    logger.warning("⚠️ Sample data seeding failed, but migration continues")

            logger.info("🎉 Database migration completed successfully!")
            logger.info("📊 Final database status:")

            final_counts = await self.check_existing_data()
            for table, count in final_counts.items():
                logger.info(f"   {table}: {count} records")

            return True

        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Medical Triage-BOTS Database Migration")
    parser.add_argument("--init", action="store_true", help="Initialize database only")
    parser.add_argument("--seed", action="store_true", help="Add sample data")
    parser.add_argument("--reset", action="store_true", help="Reset database (DANGER!)")
    parser.add_argument("--check", action="store_true", help="Check database connection only")

    args = parser.parse_args()

    migrator = DatabaseMigrator()

    if args.check:
        success = await migrator.check_database_connection()
        sys.exit(0 if success else 1)

    success = await migrator.run_migrations(
        init_only=args.init,
        seed_data=args.seed,
        reset=args.reset
    )

    if success:
        logger.info("✅ Migration completed successfully")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
