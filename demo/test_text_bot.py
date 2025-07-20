"""
TextBOT Demo and Testing Script

This script demonstrates the TextBOT agent's capabilities for processing
structured medical data and generating health risk assessments.
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the backend app to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.text_bot import TextBOT
from app.models.triage_case import StructuredData, StructuredDataType


async def test_diabetes_prediction():
    """Test diabetes risk prediction with sample data"""
    print("\n🩺 Testing Diabetes Risk Prediction")
    print("=" * 50)

    text_bot = TextBOT()

    # Sample diabetes-related data
    diabetes_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "fasting_glucose": 145,  # Elevated
                "hemoglobin_a1c": 6.2,   # Prediabetic range
                "total_cholesterol": 220,
                "hdl_cholesterol": 35    # Low
            },
            units={
                "fasting_glucose": "mg/dL",
                "hemoglobin_a1c": "%",
                "total_cholesterol": "mg/dL",
                "hdl_cholesterol": "mg/dL"
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 52,
                "bmi": 31.5,  # Obese
                "systolic_blood_pressure": 138,
                "diastolic_blood_pressure": 88
            },
            units={
                "bmi": "kg/m²",
                "systolic_blood_pressure": "mmHg",
                "diastolic_blood_pressure": "mmHg"
            }
        )
    ]

    result = await text_bot.process_structured_data(diabetes_data)

    print(f"Success: {result.success}")
    print(f"Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"Risk Category: {result.risk_category}")
    print(f"Models Used: {', '.join(result.models_used)}")
    print(f"Processing Time: {result.processing_time_ms}ms")
    print(f"Confidence: {result.confidence_score:.3f}")

    print("\nTop Recommendations:")
    for i, rec in enumerate(result.recommendations[:5], 1):
        print(f"  {i}. {rec}")

    if result.warnings:
        print("\nWarnings:")
        for warning in result.warnings:
            print(f"  ⚠️ {warning}")


async def test_heart_disease_prediction():
    """Test cardiovascular risk prediction with sample data"""
    print("\n❤️ Testing Heart Disease Risk Prediction")
    print("=" * 50)

    text_bot = TextBOT()

    # Sample cardiovascular data
    cardio_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "total_cholesterol": 280,  # High
                "ldl_cholesterol": 180,    # Very high
                "hdl_cholesterol": 32,     # Low
                "triglycerides": 220       # High
            },
            units={
                "total_cholesterol": "mg/dL",
                "ldl_cholesterol": "mg/dL",
                "hdl_cholesterol": "mg/dL",
                "triglycerides": "mg/dL"
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 58,
                "gender": 1,  # Male
                "systolic_blood_pressure": 155,  # Stage 2 hypertension
                "diastolic_blood_pressure": 95,
                "smoking_status": 1,  # Smoker
                "family_history_cvd": 1  # Family history
            },
            units={
                "systolic_blood_pressure": "mmHg",
                "diastolic_blood_pressure": "mmHg"
            }
        )
    ]

    result = await text_bot.process_structured_data(cardio_data)

    print(f"Success: {result.success}")
    print(f"Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"Risk Category: {result.risk_category}")
    print(f"Models Used: {', '.join(result.models_used)}")

    print("\nTop Recommendations:")
    for i, rec in enumerate(result.recommendations[:5], 1):
        print(f"  {i}. {rec}")


async def test_kidney_disease_prediction():
    """Test kidney disease risk prediction with sample data"""
    print("\n🫘 Testing Kidney Disease Risk Prediction")
    print("=" * 50)

    text_bot = TextBOT()

    # Sample kidney function data
    kidney_data = [
        StructuredData(
            data_type=StructuredDataType.LAB_RESULTS,
            data={
                "creatinine": 2.1,        # Elevated
                "blood_urea_nitrogen": 45, # Elevated
                "estimated_gfr": 35,      # Stage 3 CKD
                "protein_urine": 1.2      # Moderate proteinuria
            },
            units={
                "creatinine": "mg/dL",
                "blood_urea_nitrogen": "mg/dL",
                "estimated_gfr": "mL/min/1.73m²",
                "protein_urine": "g/day"
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 65,
                "diabetes_status": 1,     # Has diabetes
                "systolic_blood_pressure": 145,
                "diastolic_blood_pressure": 90
            }
        )
    ]

    result = await text_bot.process_structured_data(kidney_data)

    print(f"Success: {result.success}")
    print(f"Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"Risk Category: {result.risk_category}")
    print(f"Models Used: {', '.join(result.models_used)}")

    print("\nTop Recommendations:")
    for i, rec in enumerate(result.recommendations[:5], 1):
        print(f"  {i}. {rec}")


async def test_comprehensive_health_assessment():
    """Test comprehensive health assessment with multiple data types"""
    print("\n🏥 Testing Comprehensive Health Assessment")
    print("=" * 50)

    text_bot = TextBOT()

    # Comprehensive medical data
    comprehensive_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "fasting_glucose": 118,    # Borderline
                "hemoglobin_a1c": 5.9,     # Prediabetic
                "total_cholesterol": 235,   # Borderline high
                "ldl_cholesterol": 155,     # High
                "hdl_cholesterol": 42,      # Low normal
                "triglycerides": 185,       # Borderline high
                "creatinine": 1.3          # Mildly elevated
            },
            units={
                "fasting_glucose": "mg/dL",
                "hemoglobin_a1c": "%",
                "total_cholesterol": "mg/dL",
                "ldl_cholesterol": "mg/dL",
                "hdl_cholesterol": "mg/dL",
                "triglycerides": "mg/dL",
                "creatinine": "mg/dL"
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 48,
                "bmi": 28.5,               # Overweight
                "systolic_blood_pressure": 132,  # Stage 1 hypertension
                "diastolic_blood_pressure": 84,
                "heart_rate": 78,
                "smoking_status": 0,        # Non-smoker
                "alcohol_consumption": 1,   # Moderate
                "physical_activity_level": 2  # Low-moderate
            },
            units={
                "bmi": "kg/m²",
                "systolic_blood_pressure": "mmHg",
                "diastolic_blood_pressure": "mmHg",
                "heart_rate": "bpm"
            }
        ),
        StructuredData(
            data_type=StructuredDataType.MEDICAL_HISTORY,
            data={
                "family_history_diabetes": 1,    # Yes
                "family_history_cvd": 1,         # Yes
                "family_history_hypertension": 1 # Yes
            }
        )
    ]

    result = await text_bot.process_structured_data(comprehensive_data)

    print(f"Success: {result.success}")
    print(f"Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"Risk Category: {result.risk_category}")
    print(f"Models Used: {', '.join(result.models_used)}")
    print(f"Confidence: {result.confidence_score:.3f}")

    print("\nModel-Specific Results:")
    for model_name, model_result in result.model_results.items():
        risk_score = model_result.get('risk_score', 0)
        risk_category = model_result.get('risk_category', 'unknown')
        print(f"  {model_name.replace('_', ' ').title()}: {risk_score:.3f} ({risk_category})")

    print("\nTop Recommendations:")
    for i, rec in enumerate(result.recommendations[:8], 1):
        print(f"  {i}. {rec}")

    # Show raw output for debugging
    print("\nData Summary:")
    data_summary = result.raw_output.get('data_summary', {})
    print(f"  Total Features: {data_summary.get('total_features', 0)}")
    print(f"  Data Types: {', '.join(data_summary.get('data_types', []))}")
    print(f"  Feature Categories: {data_summary.get('feature_categories', {})}")


async def test_insufficient_data():
    """Test behavior with insufficient data"""
    print("\n⚠️ Testing Insufficient Data Handling")
    print("=" * 50)

    text_bot = TextBOT()

    # Minimal data
    minimal_data = [
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "heart_rate": 72
            },
            units={
                "heart_rate": "bpm"
            }
        )
    ]

    result = await text_bot.process_structured_data(minimal_data)

    print(f"Success: {result.success}")
    print(f"Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"Risk Category: {result.risk_category}")
    print(f"Models Used: {', '.join(result.models_used)}")

    print("\nRecommendations:")
    for i, rec in enumerate(result.recommendations, 1):
        print(f"  {i}. {rec}")


async def test_model_info():
    """Test model information retrieval"""
    print("\n📋 Testing Model Information")
    print("=" * 50)

    text_bot = TextBOT()
    model_info = text_bot.get_model_info()

    print(f"Agent: {model_info['agent_name']}")
    print(f"Version: {model_info['version']}")
    print(f"Available Models: {len(model_info['available_models'])}")

    print("\nModel Details:")
    for model_name, info in model_info['available_models'].items():
        print(f"  {model_name.replace('_', ' ').title()}:")
        print(f"    Required features: {len(info['required_features'])}")
        print(f"    Optional features: {len(info['optional_features'])}")
        print(f"    Trained: {info['is_trained']}")


async def main():
    """Run all TextBOT tests"""
    print("🤖 TextBOT Medical Data Analysis Demo")
    print("=" * 60)

    try:
        # Test individual models
        await test_diabetes_prediction()
        await test_heart_disease_prediction()
        await test_kidney_disease_prediction()

        # Test comprehensive assessment
        await test_comprehensive_health_assessment()

        # Test edge cases
        await test_insufficient_data()

        # Test model info
        await test_model_info()

        print("\n✅ All TextBOT tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
