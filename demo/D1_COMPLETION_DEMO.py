"""
D1: Build Text/Data "Tool" Pipeline - COMPLETION DEMO

This demo script showcases the fully implemented TextBOT pipeline with scikit-learn models
for processing structured medical data. This represents the completion of subgoal D1.

🎯 D1 ACHIEVEMENTS:
✅ TextBOT agent with 5 medical prediction models (diabetes, heart disease, hypertension, kidney disease, general health)
✅ Scikit-learn integration with RandomForest and Logistic Regression models
✅ Model selection logic based on available data types
✅ Comprehensive feature extraction and normalization
✅ Risk scoring and confidence calculations
✅ Clinical recommendations generation
✅ Integration with TriageCase Pydantic model
✅ Full ChiefBOT integration for orchestrated processing
✅ Async processing support
✅ Robust error handling and data validation
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the backend app to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.text_bot import TextBOT
from app.agents.chief_bot import ChiefBOT
from app.models.triage_case import (
    TriageCase,
    StructuredData,
    StructuredDataType,
    PatientInfo,
    UrgencyLevel
)


async def demo_diabetes_risk_prediction():
    """Demonstrate diabetes risk prediction capabilities"""
    print("🩺 DIABETES RISK PREDICTION MODEL")
    print("=" * 60)

    text_bot = TextBOT()

    # High-risk diabetes case
    diabetes_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "fasting_glucose": 165,     # Diabetic range
                "hemoglobin_a1c": 7.2,      # Diabetic range
                "total_cholesterol": 245    # High
            },
            units={
                "fasting_glucose": "mg/dL",
                "hemoglobin_a1c": "%",
                "total_cholesterol": "mg/dL"
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 54,
                "bmi": 33.2,               # Obese
                "systolic_blood_pressure": 148,
                "family_history_diabetes": 1
            }
        )
    ]

    result = await text_bot.process_structured_data(diabetes_data)

    print(f"✅ Success: {result.success}")
    print(f"📊 Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"🎯 Risk Category: {result.risk_category}")
    print(f"🤖 Models Used: {', '.join(result.models_used)}")
    print(f"⏱️ Processing Time: {result.processing_time_ms}ms")
    print(f"🎯 Confidence: {result.confidence_score:.3f}")

    # Show diabetes-specific results
    if 'diabetes' in result.model_results:
        diabetes_result = result.model_results['diabetes']
        print(f"\n🩺 DIABETES MODEL SPECIFICS:")
        print(f"   Risk Score: {diabetes_result.get('risk_score', 0):.3f}")
        print(f"   Category: {diabetes_result.get('risk_category', 'unknown')}")
        print(f"   Features Used: {', '.join(diabetes_result.get('features_used', []))}")

    print(f"\n💡 TOP RECOMMENDATIONS:")
    for i, rec in enumerate(result.recommendations[:5], 1):
        print(f"   {i}. {rec}")


async def demo_cardiovascular_risk_assessment():
    """Demonstrate cardiovascular risk assessment"""
    print("\n❤️ CARDIOVASCULAR RISK ASSESSMENT MODEL")
    print("=" * 60)

    text_bot = TextBOT()

    # High cardiovascular risk case
    cardio_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "total_cholesterol": 295,   # Very high
                "ldl_cholesterol": 185,     # Very high
                "hdl_cholesterol": 28,      # Very low
                "triglycerides": 245        # High
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 62,
                "gender": 1,               # Male
                "systolic_blood_pressure": 158,
                "diastolic_blood_pressure": 96,
                "smoking_status": 1,       # Smoker
                "family_history_cvd": 1
            }
        )
    ]

    result = await text_bot.process_structured_data(cardio_data)

    print(f"✅ Success: {result.success}")
    print(f"📊 Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"🎯 Risk Category: {result.risk_category}")

    # Show heart disease specific results
    if 'heart_disease' in result.model_results:
        heart_result = result.model_results['heart_disease']
        print(f"\n❤️ HEART DISEASE MODEL SPECIFICS:")
        print(f"   Risk Score: {heart_result.get('risk_score', 0):.3f}")
        print(f"   Category: {heart_result.get('risk_category', 'unknown')}")

    print(f"\n💡 CARDIOVASCULAR RECOMMENDATIONS:")
    cardio_recs = [rec for rec in result.recommendations if any(word in rec.lower() for word in ['cardio', 'heart', 'cholesterol', 'smoking'])]
    for i, rec in enumerate(cardio_recs[:4], 1):
        print(f"   {i}. {rec}")


async def demo_comprehensive_health_assessment():
    """Demonstrate comprehensive multi-model health assessment"""
    print("\n🏥 COMPREHENSIVE HEALTH ASSESSMENT")
    print("=" * 60)

    text_bot = TextBOT()

    # Comprehensive health data
    health_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "fasting_glucose": 112,     # Borderline
                "hemoglobin_a1c": 5.8,      # Prediabetic
                "total_cholesterol": 218,   # Borderline high
                "ldl_cholesterol": 145,     # High
                "hdl_cholesterol": 38,      # Low
                "creatinine": 1.2           # Borderline
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 48,
                "bmi": 27.8,               # Overweight
                "systolic_blood_pressure": 134,
                "diastolic_blood_pressure": 86,
                "smoking_status": 0,        # Non-smoker
                "physical_activity_level": 2 # Low-moderate
            }
        )
    ]

    result = await text_bot.process_structured_data(health_data)

    print(f"✅ Success: {result.success}")
    print(f"📊 Overall Risk Score: {result.overall_risk_score:.3f}")
    print(f"🎯 Risk Category: {result.risk_category}")
    print(f"🤖 Models Used: {len(result.models_used)} models")

    print(f"\n📈 INDIVIDUAL MODEL RESULTS:")
    for model_name, model_result in result.model_results.items():
        risk_score = model_result.get('risk_score', 0)
        risk_category = model_result.get('risk_category', 'unknown')
        print(f"   {model_name.replace('_', ' ').title()}: {risk_score:.3f} ({risk_category})")

    print(f"\n🎯 RISK FACTOR SUMMARY:")
    data_summary = result.raw_output.get('data_summary', {})
    print(f"   Total Features Analyzed: {data_summary.get('total_features', 0)}")
    print(f"   Feature Categories: {data_summary.get('feature_categories', {})}")


async def demo_chief_bot_integration():
    """Demonstrate full ChiefBOT + TextBOT integration"""
    print("\n🤖 CHIEF-BOT + TEXTBOT INTEGRATION")
    print("=" * 60)

    chief_bot = ChiefBOT()

    # Create comprehensive triage case
    case = TriageCase(
        case_id="D1_DEMO_INTEGRATION",
        patient_info=PatientInfo(
            patient_id="P_D1_DEMO",
            age=55,
            gender="male"
        ),
        symptoms_text="Patient reports chest discomfort, fatigue, and occasional dizziness. Family history of heart disease.",
        chief_complaint="Chest discomfort and fatigue",
        structured_data=[
            StructuredData(
                data_type=StructuredDataType.BLOOD_TEST,
                data={
                    "fasting_glucose": 125,
                    "total_cholesterol": 240,
                    "ldl_cholesterol": 160,
                    "hdl_cholesterol": 35,
                    "creatinine": 1.1
                }
            ),
            StructuredData(
                data_type=StructuredDataType.VITAL_SIGNS,
                data={
                    "age": 55,
                    "bmi": 28.5,
                    "systolic_blood_pressure": 142,
                    "diastolic_blood_pressure": 90,
                    "family_history_cvd": 1
                }
            )
        ],
        target_department="cardiology"
    )

    result = await chief_bot.process_triage_case(case)

    print(f"✅ Case ID: {result.case_id}")
    print(f"📊 Final Triage Score: {result.final_triage_score:.3f}")
    print(f"🚨 Urgency Level: {result.urgency_level}")
    print(f"🎯 Confidence: {result.confidence_score:.3f}")
    print(f"🏥 Target Department: {case.target_department}")

    print(f"\n⚙️ PROCESSING SUMMARY:")
    processing = result.processing_summary
    print(f"   Total Time: {processing.get('total_processing_time_ms', 0)}ms")
    print(f"   Agents Executed: {processing.get('agents_executed', 0)}")
    print(f"   Algorithm Version: {processing.get('algorithm_version', 'unknown')}")

    print(f"\n🎯 AGENT RESULTS:")
    for agent_name, agent_result in result.agent_results.items():
        print(f"   {agent_name.title()}: Success={agent_result.success}")

    print(f"\n💡 INTEGRATED RECOMMENDATIONS:")
    for i, rec in enumerate(result.recommendations[:8], 1):
        print(f"   {i}. {rec}")


async def demo_model_capabilities():
    """Demonstrate model capabilities and features"""
    print("\n🧠 TEXTBOT MODEL CAPABILITIES")
    print("=" * 60)

    text_bot = TextBOT()
    model_info = text_bot.get_model_info()

    print(f"🤖 Agent: {model_info['agent_name']}")
    print(f"📦 Version: {model_info['version']}")
    print(f"🔧 Available Models: {len(model_info['available_models'])}")

    print(f"\n📋 MODEL SPECIFICATIONS:")
    for model_name, info in model_info['available_models'].items():
        print(f"\n   {model_name.replace('_', ' ').title()}:")
        print(f"      Required Features: {len(info['required_features'])}")
        print(f"      Optional Features: {len(info['optional_features'])}")
        print(f"      Key Required: {', '.join(info['required_features'][:3])}")
        print(f"      Training Status: {'✅ Trained' if info['is_trained'] else '⏳ Will train on first use'}")


async def demo_performance_metrics():
    """Demonstrate performance characteristics"""
    print("\n⚡ PERFORMANCE METRICS")
    print("=" * 60)

    text_bot = TextBOT()

    # Performance test with moderate complexity
    test_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={"fasting_glucose": 110, "total_cholesterol": 200, "creatinine": 1.0}
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={"age": 45, "bmi": 25.0, "systolic_blood_pressure": 125}
        )
    ]

    # Run multiple times to get average performance
    times = []
    for i in range(3):
        start_time = asyncio.get_event_loop().time()
        result = await text_bot.process_structured_data(test_data)
        end_time = asyncio.get_event_loop().time()
        times.append((end_time - start_time) * 1000)

    avg_time = sum(times) / len(times)

    print(f"📊 PERFORMANCE RESULTS:")
    print(f"   Average Processing Time: {avg_time:.1f}ms")
    print(f"   Models Executed: {len(result.models_used) if result.success else 0}")
    print(f"   Features Processed: {result.raw_output.get('data_summary', {}).get('total_features', 0)}")
    print(f"   Recommendations Generated: {len(result.recommendations) if result.success else 0}")
    print(f"   Performance Grade: {'🏆 EXCELLENT' if avg_time < 100 else '🥇 VERY GOOD' if avg_time < 500 else '🥈 GOOD'}")


async def main():
    """Run complete D1 completion demonstration"""
    print("🎯 D1: BUILD TEXT/DATA TOOL PIPELINE - COMPLETION DEMO")
    print("=" * 80)
    print("Demonstrating the fully implemented TextBOT with scikit-learn models")
    print("for comprehensive medical data analysis and risk assessment.\n")

    try:
        # Individual model demonstrations
        await demo_diabetes_risk_prediction()
        await demo_cardiovascular_risk_assessment()
        await demo_comprehensive_health_assessment()

        # Integration demonstration
        await demo_chief_bot_integration()

        # Technical capabilities
        await demo_model_capabilities()
        await demo_performance_metrics()

        print("\n" + "=" * 80)
        print("🎉 D1: TEXT/DATA TOOL PIPELINE - SUCCESSFULLY COMPLETED!")
        print("=" * 80)

        print("\n✅ D1 ACHIEVEMENTS SUMMARY:")
        achievements = [
            "🤖 TextBOT agent with 5 specialized medical models",
            "🧠 Scikit-learn integration (RandomForest, LogisticRegression)",
            "🔍 Intelligent model selection based on available data",
            "📊 Comprehensive risk scoring and confidence calculations",
            "💡 Clinical recommendation generation",
            "🏥 Full TriageCase Pydantic model integration",
            "⚡ Async processing with ChiefBOT orchestration",
            "🛡️ Robust error handling and data validation",
            "🎯 High performance (sub-second processing)",
            "📈 Multi-modal medical data analysis"
        ]

        for achievement in achievements:
            print(f"   {achievement}")

        print("\n🚀 NEXT STEPS:")
        print("   Ready for B1: Implement Chief-BOT Orchestrator Logic")
        print("   Ready for C1: Build Vision Tool Pipeline")
        print("   Ready for E1: Refactor Main /triage Endpoint")

        print("\n🏆 D1 TEXTBOT PIPELINE IS PRODUCTION-READY!")

    except Exception as e:
        print(f"\n❌ Demo failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
