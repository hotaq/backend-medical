#!/usr/bin/env python3
"""
Database Integration Demo for Medical Triage-BOTS System

This script demonstrates the complete integration between Pydantic models
and the database schema, showing the full workflow from case creation
to final triage results and analytics.

Features demonstrated:
- Database initialization and schema creation
- Creating and storing TriageCase data
- Multi-agent processing workflow simulation
- Final triage result calculation
- Analytics and reporting
- Database health monitoring
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import json

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.triage_case import (
    TriageCase as PydanticTriageCase,
    PatientInfo,
    StructuredData,
    ImageData,
    UrgencyLevel,
    StructuredDataType
)
from app.models.pydantic_compat import model_dump_json, get_compatibility_info

from app.database import (
    initialize_database,
    get_database_health,
    get_database_statistics,
    cleanup_database,
    AsyncSessionLocal
)
from app.database.crud import (
    TriageCaseCRUD,
    PatientCRUD,
    CaseProcessingCRUD,
    TriageResultCRUD,
    AuditCRUD
)
from app.database.models import (
    ProcessingStatusEnum,
    UrgencyLevelEnum
)


class DatabaseDemo:
    """Demo class for database integration"""

    def __init__(self):
        self.demo_cases: List[PydanticTriageCase] = []
        self.created_case_ids: List[str] = []

    async def run_complete_demo(self):
        """Run the complete database integration demo"""
        print("🏥 MEDICAL TRIAGE-BOTS DATABASE INTEGRATION DEMO")
        print("=" * 60)

        try:
            # 1. Show compatibility info
            await self.show_compatibility_info()

            # 2. Initialize database
            await self.demo_database_initialization()

            # 3. Show database health
            await self.demo_database_health()

            # 4. Create sample cases
            await self.demo_case_creation()

            # 5. Simulate processing workflow
            await self.demo_processing_workflow()

            # 6. Create final triage results
            await self.demo_triage_results()

            # 7. Show analytics
            await self.demo_analytics()

            # 8. Show database statistics
            await self.demo_database_statistics()

            print("\n" + "=" * 60)
            print("✅ DATABASE INTEGRATION DEMO COMPLETED SUCCESSFULLY!")
            print("\nThe database schema successfully supports:")
            print("  • Multi-modal triage case storage")
            print("  • Detailed processing workflow logging")
            print("  • Final triage score calculation and storage")
            print("  • Comprehensive audit trails")
            print("  • Analytics and reporting capabilities")
            print("  • Performance monitoring and health checks")

        except Exception as e:
            print(f"\n❌ Demo failed with error: {e}")
            raise
        finally:
            # Cleanup
            await cleanup_database()

    async def show_compatibility_info(self):
        """Show system compatibility information"""
        print("\n=== SYSTEM COMPATIBILITY INFO ===")

        compat_info = get_compatibility_info()
        print(f"Python Version: {compat_info['python_version']}")
        print(f"Pydantic Version: {compat_info['pydantic_version']}")
        print(f"Using Pydantic V2: {compat_info['is_v2']}")

        # Show available features
        features = compat_info['available_features']
        print("Available Features:")
        for feature, available in features.items():
            status = "✅" if available else "❌"
            print(f"  {status} {feature}")

    async def demo_database_initialization(self):
        """Demo database initialization"""
        print("\n=== DATABASE INITIALIZATION ===")

        print("Initializing database schema...")
        success = await initialize_database()

        if success:
            print("✅ Database initialized successfully")
            print("   • All tables created")
            print("   • Indexes applied")
            print("   • Initial data setup completed")
        else:
            print("❌ Database initialization failed")
            raise Exception("Database initialization failed")

    async def demo_database_health(self):
        """Demo database health monitoring"""
        print("\n=== DATABASE HEALTH CHECK ===")

        health = await get_database_health()

        print(f"Database Status: {health['status']}")
        print(f"Connection: {'✅' if health['connection'] else '❌'}")
        print(f"Database Type: {health['database_url']}")

        if health['tables']:
            print(f"Tables Created: {len(health['tables'])}")
            for table in sorted(health['tables']):
                print(f"  • {table}")

        if health.get('error'):
            print(f"Error: {health['error']}")

    async def demo_case_creation(self):
        """Demo creating and storing triage cases"""
        print("\n=== TRIAGE CASE CREATION ===")

        # Create sample cases
        self.demo_cases = self.create_sample_cases()

        async with AsyncSessionLocal() as session:
            for i, pydantic_case in enumerate(self.demo_cases, 1):
                print(f"\nCreating Case {i}: {pydantic_case.case_id}")

                # Create in database
                db_case = await TriageCaseCRUD.create_triage_case(session, pydantic_case)
                self.created_case_ids.append(db_case.case_id)

                print(f"  ✅ Case stored with DB ID: {db_case.id}")
                print(f"  📊 Primary Data Type: {db_case.primary_data_type}")
                print(f"  🔍 Processing Required:")
                print(f"     Vision: {db_case.requires_vision_analysis}")
                print(f"     Text: {db_case.requires_text_analysis}")
                print(f"     Structured: {db_case.requires_structured_analysis}")

                # Show related data counts
                if hasattr(db_case, 'structured_data') and db_case.structured_data:
                    print(f"  📋 Structured Data Items: {len(db_case.structured_data)}")
                if hasattr(db_case, 'images') and db_case.images:
                    print(f"  📷 Images: {len(db_case.images)}")

            await session.commit()
            print(f"\n✅ Successfully created {len(self.demo_cases)} triage cases")

    async def demo_processing_workflow(self):
        """Demo the multi-agent processing workflow"""
        print("\n=== MULTI-AGENT PROCESSING WORKFLOW ===")

        async with AsyncSessionLocal() as session:
            for case_id in self.created_case_ids:
                print(f"\nProcessing Case: {case_id}")

                # Get case to check processing requirements
                case = await TriageCaseCRUD.get_triage_case_by_id(session, case_id)

                # Simulate VisionBOT processing
                if case.requires_vision_analysis:
                    await self.simulate_vision_processing(session, case_id)

                # Simulate TextBOT processing
                if case.requires_text_analysis:
                    await self.simulate_text_processing(session, case_id)

                # Simulate Structured Data processing
                if case.requires_structured_analysis:
                    await self.simulate_structured_processing(session, case_id)

                # Simulate Chief-BOT final processing
                await self.simulate_chief_bot_processing(session, case_id)

            await session.commit()
            print("\n✅ Processing workflow completed for all cases")

    async def simulate_vision_processing(self, session, case_id: str):
        """Simulate VisionBOT processing"""
        print("  🤖 VisionBOT Processing...")

        # Step 1: Tool processing (CNN)
        tool_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="vision_bot",
            processing_step="tool",
            status=ProcessingStatusEnum.IN_PROGRESS,
            model_version="efficientnet_v2"
        )

        # Simulate processing delay and result
        await asyncio.sleep(0.1)  # Simulate processing time

        # Update with results
        await CaseProcessingCRUD.update_processing_status(
            session,
            tool_record.id,
            ProcessingStatusEnum.COMPLETED,
            raw_output={
                "prediction_class": 3,
                "disease": "Severe Diabetic Retinopathy",
                "confidence": 0.92,
                "features": ["hemorrhages", "exudates", "neovascularization"]
            },
            processing_time_ms=1250
        )

        # Step 2: Synthesizer processing (LLM)
        synth_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="vision_bot",
            processing_step="synthesizer",
            status=ProcessingStatusEnum.IN_PROGRESS,
            llm_model_used="google/medgemma-4b-it"
        )

        await asyncio.sleep(0.1)

        await CaseProcessingCRUD.update_processing_status(
            session,
            synth_record.id,
            ProcessingStatusEnum.COMPLETED,
            synthesized_output="Retinal imaging shows severe diabetic retinopathy with significant hemorrhages, hard exudates, and evidence of neovascularization. Immediate ophthalmologic intervention is recommended.",
            processing_time_ms=890
        )

        print("    ✅ Vision analysis completed")

    async def simulate_text_processing(self, session, case_id: str):
        """Simulate TextBOT processing"""
        print("  📝 TextBOT Processing...")

        # Tool processing
        tool_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="text_bot",
            processing_step="tool",
            status=ProcessingStatusEnum.IN_PROGRESS,
            model_version="heart_disease_rf_v1.2"
        )

        await asyncio.sleep(0.1)

        await CaseProcessingCRUD.update_processing_status(
            session,
            tool_record.id,
            ProcessingStatusEnum.COMPLETED,
            raw_output={
                "risk_score": 0.78,
                "model_used": "RandomForestClassifier",
                "risk_factors": ["elevated_glucose", "high_bp", "family_history"],
                "recommendations": ["cardiology_consult", "diet_modification"]
            },
            processing_time_ms=450
        )

        # Synthesizer processing
        synth_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="text_bot",
            processing_step="synthesizer",
            status=ProcessingStatusEnum.IN_PROGRESS,
            llm_model_used="google/medgemma-4b-it"
        )

        await asyncio.sleep(0.1)

        await CaseProcessingCRUD.update_processing_status(
            session,
            synth_record.id,
            ProcessingStatusEnum.COMPLETED,
            synthesized_output="Analysis of patient symptoms and structured data indicates elevated cardiovascular risk. The combination of diabetes, hypertension, and current symptoms warrants immediate medical attention.",
            processing_time_ms=750
        )

        print("    ✅ Text analysis completed")

    async def simulate_structured_processing(self, session, case_id: str):
        """Simulate structured data processing"""
        print("  📊 Structured Data Processing...")

        tool_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="structured_bot",
            processing_step="tool",
            status=ProcessingStatusEnum.IN_PROGRESS,
            model_version="diabetes_risk_xgb_v2.1"
        )

        await asyncio.sleep(0.1)

        await CaseProcessingCRUD.update_processing_status(
            session,
            tool_record.id,
            ProcessingStatusEnum.COMPLETED,
            raw_output={
                "diabetes_risk": 0.85,
                "ckd_risk": 0.43,
                "abnormal_values": ["fasting_glucose", "hba1c", "creatinine"],
                "severity": "high"
            },
            processing_time_ms=320
        )

        print("    ✅ Structured data analysis completed")

    async def simulate_chief_bot_processing(self, session, case_id: str):
        """Simulate Chief-BOT final processing"""
        print("  🧠 Chief-BOT Final Processing...")

        final_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="chief_bot",
            processing_step="final",
            status=ProcessingStatusEnum.IN_PROGRESS,
            llm_model_used="google/medgemma-4b-it"
        )

        await asyncio.sleep(0.1)

        await CaseProcessingCRUD.update_processing_status(
            session,
            final_record.id,
            ProcessingStatusEnum.COMPLETED,
            raw_output={
                "final_score": 0.87,
                "confidence": 0.94,
                "reasoning": "High-risk case based on vision analysis and clinical data"
            },
            synthesized_output="Multi-modal analysis indicates high-priority case requiring immediate attention. Severe diabetic retinopathy combined with elevated cardiovascular risk factors necessitates urgent medical intervention.",
            processing_time_ms=680
        )

        print("    ✅ Chief-BOT processing completed")

    async def demo_triage_results(self):
        """Demo creating final triage results"""
        print("\n=== FINAL TRIAGE RESULTS ===")

        async with AsyncSessionLocal() as session:
            for i, case_id in enumerate(self.created_case_ids):
                print(f"\nFinalizing Case {i+1}: {case_id}")

                # Calculate final triage score based on processing results
                processing_history = await CaseProcessingCRUD.get_case_processing_history(session, case_id)

                # Extract scores from processing results
                scores = []
                for record in processing_history:
                    if record.raw_output and 'risk_score' in record.raw_output:
                        scores.append(record.raw_output['risk_score'])
                    elif record.raw_output and 'final_score' in record.raw_output:
                        scores.append(record.raw_output['final_score'])
                    elif record.raw_output and 'confidence' in record.raw_output:
                        scores.append(record.raw_output['confidence'])

                # Calculate weighted average
                final_score = sum(scores) / len(scores) if scores else 0.5

                # Determine urgency level
                if final_score >= 0.8:
                    urgency = UrgencyLevelEnum.CRITICAL
                    wait_time = 5
                elif final_score >= 0.6:
                    urgency = UrgencyLevelEnum.HIGH
                    wait_time = 15
                elif final_score >= 0.4:
                    urgency = UrgencyLevelEnum.MEDIUM
                    wait_time = 60
                else:
                    urgency = UrgencyLevelEnum.LOW
                    wait_time = 180

                # Create triage result
                result = await TriageResultCRUD.create_triage_result(
                    session,
                    case_id=case_id,
                    final_triage_score=final_score,
                    urgency_level=urgency,
                    estimated_wait_time=wait_time,
                    recommendations=[
                        "Immediate medical attention required",
                        "Monitor vital signs closely",
                        "Specialist consultation recommended"
                    ],
                    vision_analysis_completed=True,
                    text_analysis_completed=True,
                    structured_analysis_completed=True,
                    confidence_score=0.92,
                    scoring_algorithm_version="v1.0"
                )

                print(f"  ✅ Final Score: {final_score:.3f}")
                print(f"  🚨 Urgency Level: {urgency.value}")
                print(f"  ⏱️  Estimated Wait Time: {wait_time} minutes")
                print(f"  📋 Recommendations: {len(result.recommendations)} items")

            await session.commit()
            print(f"\n✅ Triage results created for all {len(self.created_case_ids)} cases")

    async def demo_analytics(self):
        """Demo analytics and reporting"""
        print("\n=== ANALYTICS AND REPORTING ===")

        async with AsyncSessionLocal() as session:
            # Get case analytics
            analytics = await AuditCRUD.get_case_analytics(session)

            print("📊 Case Analytics:")
            print(f"  Total Cases: {analytics['total_cases']}")
            print("  Priority Distribution:")
            for priority, count in analytics['priority_distribution'].items():
                print(f"    {priority}: {count}")

            print("  Average Processing Times (ms):")
            for agent, avg_time in analytics['avg_processing_times_ms'].items():
                print(f"    {agent}: {avg_time:.1f}ms")

            # Get high priority cases
            high_priority = await TriageResultCRUD.get_high_priority_cases(session)
            print(f"\n🚨 High Priority Cases: {len(high_priority)}")

            for result in high_priority:
                print(f"  Case {result.triage_case.case_id}: Score {result.final_triage_score:.3f} ({result.urgency_level.value})")

    async def demo_database_statistics(self):
        """Demo database statistics"""
        print("\n=== DATABASE STATISTICS ===")

        stats = await get_database_statistics()

        print("📈 Database Statistics:")
        for key, value in stats.items():
            if key != 'error':
                print(f"  {key.replace('_', ' ').title()}: {value}")

        if stats.get('error'):
            print(f"  Error: {stats['error']}")

    def create_sample_cases(self) -> List[PydanticTriageCase]:
        """Create sample triage cases for demonstration"""
        cases = []

        # Case 1: High-risk diabetic retinopathy case
        case1 = PydanticTriageCase(
            case_id="DEMO_001",
            patient_info=PatientInfo(
                patient_id="P001",
                age=58,
                gender="female"
            ),
            symptoms_text="Progressive vision loss, seeing dark spots and blurred vision for the past month",
            chief_complaint="Vision problems",
            medical_history="Type 2 diabetes for 15 years, hypertension, previous heart attack",
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.BLOOD_TEST,
                    data={
                        "fasting_glucose": 185,
                        "hba1c": 9.2,
                        "total_cholesterol": 280,
                        "creatinine": 1.8
                    },
                    units={
                        "fasting_glucose": "mg/dL",
                        "hba1c": "%",
                        "total_cholesterol": "mg/dL",
                        "creatinine": "mg/dL"
                    }
                )
            ],
            images=[
                ImageData(
                    image_path="/uploads/retinal_P001_left.jpg",
                    image_type="retinal"
                ),
                ImageData(
                    image_path="/uploads/retinal_P001_right.jpg",
                    image_type="retinal"
                )
            ],
            target_department="ophthalmology",
            priority_level=UrgencyLevel.HIGH
        )
        cases.append(case1)

        # Case 2: Chest pain with cardiac risk factors
        case2 = PydanticTriageCase(
            case_id="DEMO_002",
            patient_info=PatientInfo(
                patient_id="P002",
                age=67,
                gender="male"
            ),
            symptoms_text="Chest pain radiating to left arm, shortness of breath, nausea",
            chief_complaint="Chest pain",
            medical_history="Diabetes, hypertension, smoking history",
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.VITAL_SIGNS,
                    data={
                        "blood_pressure_systolic": 165,
                        "blood_pressure_diastolic": 98,
                        "heart_rate": 102,
                        "oxygen_saturation": 94
                    },
                    units={
                        "blood_pressure_systolic": "mmHg",
                        "blood_pressure_diastolic": "mmHg",
                        "heart_rate": "bpm",
                        "oxygen_saturation": "%"
                    }
                )
            ],
            target_department="cardiology",
            priority_level=UrgencyLevel.CRITICAL
        )
        cases.append(case2)

        # Case 3: Routine check with mild symptoms
        case3 = PydanticTriageCase(
            case_id="DEMO_003",
            patient_info=PatientInfo(
                patient_id="P003",
                age=34,
                gender="female"
            ),
            symptoms_text="Mild headache and fatigue for past few days",
            chief_complaint="Headache",
            target_department="general_medicine",
            priority_level=UrgencyLevel.LOW
        )
        cases.append(case3)

        return cases


async def main():
    """Main demo function"""
    demo = DatabaseDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Run the demo
    asyncio.run(main())
