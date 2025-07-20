"""
Simple ChiefBOT + TextBOT Integration Debug Test

This script creates a minimal test to debug the integration between
ChiefBOT and TextBOT with detailed logging.
"""

import sys
import os
import asyncio
import logging
from datetime import datetime

# Add the backend app to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.chief_bot import ChiefBOT
from app.models.triage_case import (
    TriageCase,
    StructuredData,
    StructuredDataType,
    PatientInfo
)

# Configure logging to see detailed output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def simple_test():
    """Simple test with detailed logging"""
    print("🔍 Simple ChiefBOT + TextBOT Integration Test")
    print("=" * 60)

    # Create ChiefBOT
    logger.info("Creating ChiefBOT instance")
    chief_bot = ChiefBOT()

    # Create simple test case
    logger.info("Creating test case with structured data")
    case = TriageCase(
        case_id="SIMPLE_TEST_001",
        patient_info=PatientInfo(
            patient_id="P123456",
            age=45,
            gender="female"
        ),
        symptoms_text="Patient reports fatigue and thirst",
        chief_complaint="Fatigue and increased thirst",
        structured_data=[
            StructuredData(
                data_type=StructuredDataType.BLOOD_TEST,
                data={
                    "fasting_glucose": 150,  # Elevated
                    "hemoglobin_a1c": 6.8,   # Diabetic range
                },
                units={
                    "fasting_glucose": "mg/dL",
                    "hemoglobin_a1c": "%"
                }
            ),
            StructuredData(
                data_type=StructuredDataType.VITAL_SIGNS,
                data={
                    "age": 45,
                    "bmi": 28.5,
                    "systolic_blood_pressure": 135,
                    "diastolic_blood_pressure": 85
                }
            )
        ]
    )

    print(f"Test case created: {case.case_id}")
    print(f"Structured data items: {len(case.structured_data)}")
    print(f"First data item: {case.structured_data[0].data}")
    print(f"Second data item: {case.structured_data[1].data}")

    # Test direct TextBOT first
    logger.info("Testing TextBOT directly")
    print("\n--- Direct TextBOT Test ---")
    try:
        text_result = await chief_bot.text_bot.process_structured_data(case.structured_data)
        print(f"TextBOT Success: {text_result.success}")
        print(f"TextBOT Risk Score: {text_result.overall_risk_score:.3f}")
        print(f"TextBOT Risk Category: {text_result.risk_category}")
        print(f"TextBOT Models Used: {text_result.models_used}")
        print(f"TextBOT Recommendations: {len(text_result.recommendations)}")
    except Exception as e:
        print(f"TextBOT Error: {e}")
        import traceback
        traceback.print_exc()

    # Test through ChiefBOT
    logger.info("Testing through ChiefBOT")
    print("\n--- ChiefBOT Integration Test ---")
    try:
        result = await chief_bot.process_triage_case(case)
        print(f"ChiefBOT Success: {result.case_id is not None}")
        print(f"Final Triage Score: {result.final_triage_score:.3f}")
        print(f"Urgency Level: {result.urgency_level}")
        print(f"Confidence Score: {result.confidence_score:.3f}")
        print(f"Number of Recommendations: {len(result.recommendations)}")

        print("\nAgent Results:")
        for agent_name, agent_result in result.agent_results.items():
            print(f"  {agent_name}: success={agent_result.success}")
            if hasattr(agent_result, 'synthesized_output'):
                print(f"    Output: {agent_result.synthesized_output[:100]}...")

        print(f"\nReasoning: {result.reasoning[:200]}...")

        print("\nTop 3 Recommendations:")
        for i, rec in enumerate(result.recommendations[:3], 1):
            print(f"  {i}. {rec}")

    except Exception as e:
        print(f"ChiefBOT Error: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run the simple test"""
    await simple_test()
    print("\n✅ Simple test completed!")

if __name__ == "__main__":
    asyncio.run(main())
