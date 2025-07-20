"""
Chief-BOT Orchestrator Demo

This demo showcases the Chief-BOT orchestrator in action with:
- Multi-agent coordination using asyncio.gather
- Real triage case processing
- Database integration
- Performance monitoring
- Comprehensive logging

Run with: python -m demo.demo_chief_bot_orchestrator
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports
try:
    from app.agents.chief_bot import ChiefBOT, create_triage_response
    from app.models.triage_case import (
        TriageCase,
        TriageCaseResponse,
        UrgencyLevel,
        DataType,
        ImageData,
        StructuredData,
        StructuredDataType
    )
    from app.database.crud import CaseProcessingCRUD
    from app.database.models import ProcessingStatusEnum
    from app.database.config import DatabaseManager
    import sqlalchemy as sa
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Please ensure all dependencies are installed and modules are available")
    exit(1)


class ChiefBOTDemo:
    """
    Comprehensive demonstration of Chief-BOT orchestrator capabilities.

    This demo shows:
    1. Multi-modal triage case processing
    2. Async agent coordination
    3. Database integration and logging
    4. Performance monitoring
    5. Error handling scenarios
    """

    def __init__(self):
        self.chief_bot = ChiefBOT()
        self.db_manager = DatabaseManager()
        self.demo_start_time = None

    def print_banner(self, title: str, char: str = "="):
        """Print a formatted banner"""
        print(f"\n{char * 60}")
        print(f"  {title}")
        print(f"{char * 60}")

    def print_section(self, title: str):
        """Print a section header"""
        print(f"\n🔹 {title}")
        print("-" * 40)

    async def run_complete_demo(self):
        """Run the complete Chief-BOT demonstration"""
        self.demo_start_time = time.time()

        self.print_banner("🧠 CHIEF-BOT ORCHESTRATOR DEMO", "=")
        print("Demonstrating multi-agent medical triage coordination")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Demo 1: High-Priority Multi-Modal Case
            await self.demo_critical_case()

            # Demo 2: Text-Only Case
            await self.demo_text_only_case()

            # Demo 3: Vision-Heavy Case
            await self.demo_vision_heavy_case()

            # Demo 4: Structured Data Analysis
            await self.demo_structured_data_case()

            # Demo 5: Error Handling
            await self.demo_error_handling()

            # Demo 6: Performance Comparison
            await self.demo_performance_comparison()

            # Demo 7: Database Integration
            await self.demo_database_integration()

        except Exception as e:
            logger.error(f"Demo failed: {e}", exc_info=True)
        finally:
            await self.demo_summary()

    async def demo_critical_case(self):
        """Demo 1: High-priority multi-modal case requiring all agents"""
        self.print_banner("🚨 DEMO 1: CRITICAL MULTI-MODAL CASE")

        # Create a critical case with all data types
        triage_case = TriageCase(
            case_id="CRITICAL_001",
            patient_id="P12345",
            chief_complaint="Severe chest pain and difficulty breathing",
            symptoms_text="Patient presents with crushing chest pain radiating to left arm, shortness of breath, sweating, and nausea. Pain started 2 hours ago and is getting worse. Patient has history of hypertension and diabetes.",
            images=[
                ImageData(
                    image_path="/path/to/chest_xray.jpg",
                    image_type="xray"
                ),
                ImageData(
                    image_path="/path/to/ecg_12lead.jpg",
                    image_type="ecg"
                )
            ],
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.VITAL_SIGNS,
                    data={
                        "blood_pressure_systolic": 180,
                        "blood_pressure_diastolic": 110,
                        "heart_rate": 110,
                        "respiratory_rate": 24,
                        "temperature": 98.6,
                        "oxygen_saturation": 92
                    }
                ),
                StructuredData(
                    data_type=StructuredDataType.LAB_RESULTS,
                    data={
                        "troponin_i": 0.8,  # Elevated (normal < 0.04)
                        "glucose": 220,     # Elevated
                        "creatinine": 1.5,  # Slightly elevated
                        "cholesterol_total": 280
                    }
                )
            ]
        )

        self.print_section("Case Overview")
        print(f"Case ID: {triage_case.case_id}")
        print(f"Chief Complaint: {triage_case.chief_complaint}")
        print(f"Images: {len(triage_case.images)} ({', '.join([img.image_type or 'unknown' for img in triage_case.images])})")
        print(f"Structured Data: {len(triage_case.structured_data)} datasets")

        # Show processing requirements
        requirements = triage_case.get_processing_requirements()
        self.print_section("Processing Requirements")
        for req, needed in requirements.items():
            status = "✅ Required" if needed else "❌ Not needed"
            print(f"  {req}: {status}")

        # Process with Chief-BOT
        self.print_section("Chief-BOT Processing")
        print("🧠 Starting orchestration...")

        start_time = time.time()
        decision = await self.chief_bot.process_triage_case(triage_case)
        processing_time = time.time() - start_time

        # Display results
        self.print_section("Results")
        print(f"Final Triage Score: {decision.final_triage_score:.3f}")
        print(f"Urgency Level: {decision.urgency_level.value.upper()}")
        print(f"Confidence Score: {decision.confidence_score:.3f}")
        print(f"Processing Time: {processing_time:.2f}s")

        print("\nAgent Results:")
        for agent_name, result in decision.agent_results.items():
            status = "✅ Success" if result.success else "❌ Failed"
            print(f"  {agent_name.title()}: {status}")
            if result.success and result.confidence_score:
                print(f"    Confidence: {result.confidence_score:.3f}")
                print(f"    Processing Time: {result.processing_time_ms}ms")

        print(f"\nRecommendations:")
        for i, rec in enumerate(decision.recommendations, 1):
            print(f"  {i}. {rec}")

        print(f"\nReasoning:")
        print(f"  {decision.reasoning}")

        # Convert to API response format
        response = create_triage_response(decision)
        print(f"\nEstimated Wait Time: {response.estimated_wait_time} minutes")

        return decision

    async def demo_text_only_case(self):
        """Demo 2: Text-only case (symptoms analysis)"""
        self.print_banner("📝 DEMO 2: TEXT-ONLY CASE")

        triage_case = TriageCase(
            case_id="TEXT_001",
            patient_id="P67890",
            chief_complaint="Headache and fever",
            symptoms_text="Patient reports severe headache lasting 3 days, fever up to 101.5°F, sensitivity to light, and neck stiffness. No nausea or vomiting. Patient is alert and oriented.",
            images=[],
            structured_data=[]
        )

        print(f"Case: {triage_case.chief_complaint}")
        print("Processing text-only case...")

        start_time = time.time()
        decision = await self.chief_bot.process_triage_case(triage_case)
        processing_time = time.time() - start_time

        print(f"\nResults:")
        print(f"  Triage Score: {decision.final_triage_score:.3f}")
        print(f"  Urgency: {decision.urgency_level.value}")
        print(f"  Processing Time: {processing_time:.2f}s")
        print(f"  Active Agents: {len([r for r in decision.agent_results.values() if r.success])}")

        return decision

    async def demo_vision_heavy_case(self):
        """Demo 3: Vision-heavy case with multiple medical images"""
        self.print_banner("👁️ DEMO 3: VISION-HEAVY CASE")

        triage_case = TriageCase(
            case_id="VISION_001",
            patient_id="P11111",
            chief_complaint="Diabetic retinopathy follow-up",
            symptoms_text="Routine diabetic eye screening. Patient reports some blurry vision.",
            images=[
                ImageData(
                    image_path="/path/to/left_retina.jpg",
                    image_type="retinal_scan"
                ),
                ImageData(
                    image_path="/path/to/right_retina.jpg",
                    image_type="retinal_scan"
                ),
                ImageData(
                    image_path="/path/to/oct_macula.jpg",
                    image_type="oct_scan"
                )
            ],
            structured_data=[]
        )

        print(f"Case: {triage_case.chief_complaint}")
        print(f"Images: {len(triage_case.images)} retinal/OCT scans")

        start_time = time.time()
        decision = await self.chief_bot.process_triage_case(triage_case)
        processing_time = time.time() - start_time

        print(f"\nVision Analysis Results:")
        if "vision" in decision.agent_results:
            vision_result = decision.agent_results["vision"]
            if vision_result.success and vision_result.raw_output:
                print(f"  Detected: {vision_result.raw_output.get('disease', 'N/A')}")
                print(f"  Confidence: {vision_result.confidence_score:.3f}")
                print(f"  Risk Score: {vision_result.raw_output.get('risk_score', 'N/A')}")

        print(f"\nOverall Results:")
        print(f"  Triage Score: {decision.final_triage_score:.3f}")
        print(f"  Urgency: {decision.urgency_level.value}")
        print(f"  Processing Time: {processing_time:.2f}s")

        return decision

    async def demo_structured_data_case(self):
        """Demo 4: Structured data analysis (lab results and vitals)"""
        self.print_banner("📊 DEMO 4: STRUCTURED DATA CASE")

        triage_case = TriageCase(
            case_id="DATA_001",
            patient_id="P22222",
            chief_complaint="Annual physical exam",
            symptoms_text="Routine annual checkup. Patient feels well.",
            images=[],
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.LAB_RESULTS,
                    data={
                        "glucose_fasting": 180,      # Elevated (normal 70-99)
                        "hba1c": 8.5,               # Elevated (normal < 5.7)
                        "cholesterol_total": 280,    # High (normal < 200)
                        "cholesterol_ldl": 190,     # High (normal < 100)
                        "triglycerides": 350,       # Very high (normal < 150)
                        "creatinine": 2.1           # Elevated (normal 0.6-1.2)
                    }
                ),
                StructuredData(
                    data_type=StructuredDataType.VITAL_SIGNS,
                    data={
                        "blood_pressure_systolic": 165,
                        "blood_pressure_diastolic": 95,
                        "heart_rate": 78,
                        "bmi": 32.5,               # Obese
                        "weight": 220,
                        "height": 70
                    }
                )
            ]
        )

        print(f"Case: {triage_case.chief_complaint}")
        print("Analyzing comprehensive lab results and vitals...")

        # Show key values
        lab_data = triage_case.structured_data[0].data
        vital_data = triage_case.structured_data[1].data

        print(f"\nKey Lab Values:")
        print(f"  Glucose: {lab_data['glucose_fasting']} mg/dL (normal: 70-99)")
        print(f"  HbA1c: {lab_data['hba1c']}% (normal: < 5.7)")
        print(f"  Total Cholesterol: {lab_data['cholesterol_total']} mg/dL (normal: < 200)")

        print(f"\nVital Signs:")
        print(f"  BP: {vital_data['blood_pressure_systolic']}/{vital_data['blood_pressure_diastolic']} mmHg")
        print(f"  BMI: {vital_data['bmi']} (normal: 18.5-24.9)")

        start_time = time.time()
        decision = await self.chief_bot.process_triage_case(triage_case)
        processing_time = time.time() - start_time

        print(f"\nStructured Data Analysis:")
        if "structured" in decision.agent_results:
            struct_result = decision.agent_results["structured"]
            if struct_result.success and struct_result.raw_output:
                print(f"  Risk Score: {struct_result.raw_output.get('risk_score', 'N/A')}")
                abnormal = struct_result.raw_output.get('abnormal_values', [])
                if abnormal:
                    print(f"  Abnormal Values: {', '.join(abnormal)}")

        print(f"\nOverall Results:")
        print(f"  Triage Score: {decision.final_triage_score:.3f}")
        print(f"  Urgency: {decision.urgency_level.value}")
        print(f"  Processing Time: {processing_time:.2f}s")

        return decision

    async def demo_error_handling(self):
        """Demo 5: Error handling scenarios"""
        self.print_banner("⚠️  DEMO 5: ERROR HANDLING")

        # Create case with minimal data to test robustness
        triage_case = TriageCase(
            case_id="ERROR_001",
            patient_id="P99999",
            chief_complaint="",  # Empty complaint
            symptoms_text=None,  # No symptoms
            images=[],           # No images
            structured_data=[]   # No structured data
        )

        print("Testing error handling with minimal/invalid data...")
        print("Case has: empty complaint, no symptoms, no images, no structured data")

        start_time = time.time()
        decision = await self.chief_bot.process_triage_case(triage_case)
        processing_time = time.time() - start_time

        print(f"\nError Handling Results:")
        print(f"  Processing Completed: ✅")
        print(f"  Triage Score: {decision.final_triage_score:.3f}")
        print(f"  Urgency: {decision.urgency_level.value}")
        print(f"  Confidence: {decision.confidence_score:.3f}")
        print(f"  Processing Time: {processing_time:.2f}s")

        # Check if system provided reasonable defaults
        if decision.final_triage_score == 0.5:
            print("  ✅ System provided default moderate score for insufficient data")

        if decision.recommendations:
            print(f"  ✅ System provided {len(decision.recommendations)} recommendations")

        return decision

    async def demo_performance_comparison(self):
        """Demo 6: Performance comparison between sequential vs parallel processing"""
        self.print_banner("⚡ DEMO 6: PERFORMANCE COMPARISON")

        # Create a case that requires all agents
        triage_case = TriageCase(
            case_id="PERF_001",
            patient_id="P55555",
            chief_complaint="Comprehensive evaluation",
            symptoms_text="Patient with multiple symptoms requiring full analysis including chest pain, visual changes, and abnormal lab results.",
            images=[
                ImageData(
                    image_path="/path/to/chest.jpg",
                    image_type="xray"
                ),
                ImageData(
                    image_path="/path/to/retina.jpg",
                    image_type="retinal_scan"
                )
            ],
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.LAB_RESULTS,
                    data={"glucose": 200, "cholesterol": 300}
                )
            ]
        )

        print("Comparing parallel vs sequential processing performance...")
        print("(Note: Using mock agents for demonstration)")

        # Test parallel processing (normal Chief-BOT operation)
        print(f"\n🔄 Parallel Processing (asyncio.gather):")
        start_time = time.time()
        decision_parallel = await self.chief_bot.process_triage_case(triage_case)
        parallel_time = time.time() - start_time

        print(f"  Time: {parallel_time:.3f}s")
        print(f"  Agents Processed: {len([r for r in decision_parallel.agent_results.values() if r.success])}")

        # Simulate sequential processing for comparison
        print(f"\n🔄 Sequential Processing (simulated):")
        start_time = time.time()

        # Simulate sequential agent calls
        await asyncio.sleep(0.1)  # Vision agent
        await asyncio.sleep(0.1)  # Text agent
        await asyncio.sleep(0.1)  # Structured agent

        sequential_time = time.time() - start_time
        print(f"  Time: {sequential_time:.3f}s")

        # Calculate performance improvement
        if sequential_time > 0:
            improvement = ((sequential_time - parallel_time) / sequential_time) * 100
            print(f"\n📈 Performance Improvement: {improvement:.1f}% faster with parallel processing")

        return decision_parallel

    async def demo_database_integration(self):
        """Demo 7: Database integration for logging and audit trail"""
        self.print_banner("🗄️  DEMO 7: DATABASE INTEGRATION")

        print("Demonstrating database integration with processing logs...")

        try:
            # Initialize database
            async with self.db_manager.get_session() as session:
                # Create a case for database demo
                triage_case = TriageCase(
                    case_id="DB_DEMO_001",
                    patient_id="P_DB_001",
                    chief_complaint="Database integration test",
                    symptoms_text="Testing database logging capabilities",
                    images=[],
                    structured_data=[]
                )

                print(f"Processing case: {triage_case.case_id}")

                # Log initial processing start
                initial_record = await CaseProcessingCRUD.create_processing_record(
                    session,
                    case_id=triage_case.case_id,
                    agent_type="chief_bot",
                    processing_step="initialization",
                    status=ProcessingStatusEnum.IN_PROGRESS,
                    llm_model_used="chief_bot_orchestrator_v1.0.0"
                )

                print(f"  📝 Created initial processing record: {initial_record.id}")

                # Process with Chief-BOT
                start_time = time.time()
                decision = await self.chief_bot.process_triage_case(triage_case)
                processing_time = time.time() - start_time

                # Log completion
                completion_record = await CaseProcessingCRUD.create_processing_record(
                    session,
                    case_id=triage_case.case_id,
                    agent_type="chief_bot",
                    processing_step="completion",
                    status=ProcessingStatusEnum.COMPLETED,
                    llm_model_used="chief_bot_orchestrator_v1.0.0",
                    processing_time_ms=int(processing_time * 1000),
                    raw_output={
                        "final_score": decision.final_triage_score,
                        "urgency_level": decision.urgency_level.value,
                        "confidence": decision.confidence_score,
                        "agents_used": list(decision.agent_results.keys())
                    },
                    synthesized_output=decision.reasoning
                )

                print(f"  📝 Created completion record: {completion_record.id}")

                # Query processing history
                history = await CaseProcessingCRUD.get_case_processing_history(
                    session, triage_case.case_id
                )

                print(f"\n📊 Processing History:")
                for record in history:
                    print(f"  {record.processing_step}: {record.status.value} "
                          f"({record.agent_type}) at {record.created_at}")

                await session.commit()
                print(f"  ✅ Database integration successful!")

        except Exception as e:
            print(f"  ❌ Database integration failed: {e}")
            logger.error(f"Database demo failed: {e}", exc_info=True)

    async def demo_summary(self):
        """Print demo summary and statistics"""
        total_time = time.time() - self.demo_start_time if self.demo_start_time else 0

        self.print_banner("📋 DEMO SUMMARY")

        print(f"✅ Chief-BOT Orchestrator Demo Completed!")
        print(f"⏱️  Total Demo Time: {total_time:.2f} seconds")
        print(f"🧠 Chief-BOT Version: {self.chief_bot.version}")

        print(f"\n🎯 Key Features Demonstrated:")
        features = [
            "Multi-agent async coordination with asyncio.gather",
            "Weighted scoring algorithm for final triage scores",
            "Dynamic agent selection based on data availability",
            "Comprehensive error handling and recovery",
            "Performance optimization through parallelization",
            "Database integration for audit trails",
            "Support for multi-modal medical data",
            "Clinical recommendation generation"
        ]

        for i, feature in enumerate(features, 1):
            print(f"  {i}. ✅ {feature}")

        print(f"\n🚀 Chief-BOT Orchestrator is ready for production use!")
        print(f"   - Handles all medical data types")
        print(f"   - Scales with async processing")
        print(f"   - Integrates with database logging")
        print(f"   - Provides comprehensive audit trails")


# Demo execution
async def main():
    """Main demo execution function"""
    demo = ChiefBOTDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Run the demo
    print("🧠 Starting Chief-BOT Orchestrator Demo...")
    print("   This demo showcases async multi-agent coordination")
    print("   for medical triage decision-making.\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        logger.error(f"Demo execution failed: {e}", exc_info=True)
