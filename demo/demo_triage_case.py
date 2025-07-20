#!/usr/bin/env python3
"""
Demo script for TriageCase Pydantic model usage.

This script demonstrates how to create and use TriageCase models
for different types of medical data scenarios.
"""

import json
import sys
import os
from datetime import datetime

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.triage_case import (
    TriageCase,
    TriageCaseResponse,
    ImageData,
    StructuredData,
    PatientInfo,
    DataType,
    UrgencyLevel,
    StructuredDataType
)
from app.models.pydantic_compat import model_dump_json, get_compatibility_info


def demo_text_only_case():
    """Demo: Text-only triage case"""
    print("\n=== TEXT-ONLY CASE DEMO ===")

    case = TriageCase(
        case_id="CASE_001",
        patient_info=PatientInfo(
            patient_id="P001",
            age=45,
            gender="male"
        ),
        symptoms_text="Patient reports severe chest pain radiating to left arm, shortness of breath, and nausea for the past 30 minutes",
        chief_complaint="Chest pain",
        medical_history="Previous heart attack in 2020, diabetes, hypertension",
        target_department="cardiology"
    )

    print(f"Case ID: {case.case_id}")
    print(f"Primary Data Type: {case.primary_data_type}")
    print(f"Data Summary: {case.get_data_summary()}")
    print(f"Processing Requirements: {case.get_processing_requirements()}")
    print(f"Has Any Data: {case.has_any_data()}")


def demo_vision_case():
    """Demo: Vision/Image-based triage case"""
    print("\n=== VISION CASE DEMO ===")

    images = [
        ImageData(
            image_path="/uploads/retinal_scans/patient_002_left_eye.jpg",
            image_type="retinal",
            file_size=2048576
        ),
        ImageData(
            image_path="/uploads/retinal_scans/patient_002_right_eye.jpg",
            image_type="retinal",
            file_size=1987234
        )
    ]

    case = TriageCase(
        case_id="CASE_002",
        patient_info=PatientInfo(
            patient_id="P002",
            age=58,
            gender="female"
        ),
        symptoms_text="Gradual vision loss and seeing floating dark spots",
        chief_complaint="Vision problems",
        images=images,
        target_department="ophthalmology",
        specialty_required="retinal_specialist"
    )

    print(f"Case ID: {case.case_id}")
    print(f"Primary Data Type: {case.primary_data_type}")
    print(f"Number of Images: {len(case.images)}")
    print(f"Image Types: {[img.image_type for img in case.images]}")
    print(f"Processing Requirements: {case.get_processing_requirements()}")


def demo_structured_data_case():
    """Demo: Structured data triage case"""
    print("\n=== STRUCTURED DATA CASE DEMO ===")

    structured_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "fasting_glucose": 185,
                "hba1c": 9.2,
                "total_cholesterol": 280,
                "ldl_cholesterol": 180,
                "triglycerides": 300
            },
            units={
                "fasting_glucose": "mg/dL",
                "hba1c": "%",
                "total_cholesterol": "mg/dL",
                "ldl_cholesterol": "mg/dL",
                "triglycerides": "mg/dL"
            },
            reference_ranges={
                "fasting_glucose": {"min": 70, "max": 100},
                "hba1c": {"min": 4.0, "max": 5.6},
                "total_cholesterol": {"min": 0, "max": 200}
            },
            test_date=datetime(2024, 1, 15)
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "blood_pressure_systolic": 160,
                "blood_pressure_diastolic": 95,
                "heart_rate": 88,
                "temperature": 98.6,
                "oxygen_saturation": 97
            },
            units={
                "blood_pressure_systolic": "mmHg",
                "blood_pressure_diastolic": "mmHg",
                "heart_rate": "bpm",
                "temperature": "°F",
                "oxygen_saturation": "%"
            }
        )
    ]

    case = TriageCase(
        case_id="CASE_003",
        patient_info=PatientInfo(
            patient_id="P003",
            age=62,
            gender="male"
        ),
        symptoms_text="Fatigue, frequent urination, increased thirst",
        chief_complaint="Diabetes complications screening",
        structured_data=structured_data,
        target_department="endocrinology"
    )

    print(f"Case ID: {case.case_id}")
    print(f"Primary Data Type: {case.primary_data_type}")
    print(f"Number of Structured Data Items: {len(case.structured_data)}")
    print(f"Data Types: {[data.data_type for data in case.structured_data]}")
    print(f"Processing Requirements: {case.get_processing_requirements()}")


def demo_complex_mixed_case():
    """Demo: Complex case with all data types"""
    print("\n=== COMPLEX MIXED CASE DEMO ===")

    patient_info = PatientInfo(
        patient_id="P004",
        age=67,
        gender="female",
        medical_record_number="MRN789456"
    )

    structured_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "creatinine": 2.1,
                "bun": 45,
                "gfr": 35,
                "albumin": 2.8,
                "hemoglobin": 9.2
            },
            units={
                "creatinine": "mg/dL",
                "bun": "mg/dL",
                "gfr": "mL/min/1.73m²",
                "albumin": "g/dL",
                "hemoglobin": "g/dL"
            }
        )
    ]

    images = [
        ImageData(
            image_path="/uploads/xrays/chest_004.dcm",
            image_type="chest_xray"
        )
    ]

    case = TriageCase(
        case_id="CASE_004",
        patient_info=patient_info,
        symptoms_text="Shortness of breath, swelling in legs and feet, decreased urination",
        chief_complaint="Kidney disease progression",
        medical_history="Stage 3 CKD, diabetes mellitus type 2, hypertension, previous heart failure",
        additional_notes="Patient missed last two nephrology appointments",
        structured_data=structured_data,
        images=images,
        priority_level=UrgencyLevel.HIGH,
        target_department="nephrology",
        specialty_required="nephrology"
    )

    print(f"Case ID: {case.case_id}")
    print(f"Primary Data Type: {case.primary_data_type}")
    print(f"Initial Priority: {case.priority_level}")
    print(f"Data Summary: {case.get_data_summary()}")
    print(f"Processing Requirements: {case.get_processing_requirements()}")

    # Show JSON representation
    print(f"\nJSON Representation (first 500 chars):")
    json_str = model_dump_json(case, indent=2)
    print(json_str[:500] + "..." if len(json_str) > 500 else json_str)


def demo_triage_response():
    """Demo: Triage response after processing"""
    print("\n=== TRIAGE RESPONSE DEMO ===")

    response = TriageCaseResponse(
        case_id="CASE_004",
        processing_status="completed",
        triage_score=0.87,
        urgency_level=UrgencyLevel.CRITICAL,
        estimated_wait_time=10,
        recommendations=[
            "Immediate nephrology consultation required",
            "Monitor fluid balance closely",
            "Consider dialysis preparation",
            "Cardiology evaluation for heart failure management"
        ],
        vision_analysis_completed=True,
        text_analysis_completed=True,
        structured_analysis_completed=True,
        raw_vision_output={
            "chest_xray_analysis": "cardiomegaly_detected",
            "confidence": 0.84,
            "findings": ["enlarged_heart", "pulmonary_congestion"]
        },
        synthesized_vision_output="Chest X-ray shows cardiomegaly with signs of pulmonary congestion, consistent with heart failure",
        raw_text_output={
            "ckd_risk_score": 0.92,
            "heart_failure_risk": 0.78,
            "emergency_indicators": ["decreased_urination", "leg_swelling"]
        },
        synthesized_text_output="High-risk CKD patient with acute decompensation. Symptoms suggest fluid overload and possible acute kidney injury progression."
    )

    print(f"Case ID: {response.case_id}")
    print(f"Final Triage Score: {response.triage_score}")
    print(f"Urgency Level: {response.urgency_level}")
    print(f"Estimated Wait Time: {response.estimated_wait_time} minutes")
    print(f"Number of Recommendations: {len(response.recommendations)}")
    print("Recommendations:")
    for i, rec in enumerate(response.recommendations, 1):
        print(f"  {i}. {rec}")

    print(f"\nAnalysis Completion Status:")
    print(f"  Vision: {response.vision_analysis_completed}")
    print(f"  Text: {response.text_analysis_completed}")
    print(f"  Structured: {response.structured_analysis_completed}")


def demo_model_validation():
    """Demo: Model validation and error handling"""
    print("\n=== MODEL VALIDATION DEMO ===")

    try:
        # Valid case
        case = TriageCase(symptoms_text="Valid symptoms")
        print("✓ Valid case created successfully")

        # Invalid image path
        try:
            invalid_image = ImageData(image_path="")
            print("✗ This should have failed!")
        except Exception as e:
            print(f"✓ Image validation works: {type(e).__name__}")

        # Invalid triage score
        try:
            invalid_response = TriageCaseResponse(
                case_id="TEST",
                processing_status="done",
                triage_score=1.5  # Should be between 0-1
            )
            print("✗ This should have failed!")
        except Exception as e:
            print(f"✓ Triage score validation works: {type(e).__name__}")

        # Invalid patient age
        try:
            invalid_patient = PatientInfo(age=-5)
            print("✗ This should have failed!")
        except Exception as e:
            print(f"✓ Patient age validation works: {type(e).__name__}")

    except Exception as e:
        print(f"Unexpected error: {e}")


def main():
    """Run all demos"""
    print("🏥 TRIAGE-BOTS Pydantic Model Demo")
    print("=" * 50)

    # Show compatibility info
    compat_info = get_compatibility_info()
    print(f"Pydantic Version: {compat_info['pydantic_version']}")
    print(f"Python Version: {compat_info['python_version']}")
    print(f"Using Pydantic V2: {compat_info['is_v2']}")
    print("=" * 50)

    demo_text_only_case()
    demo_vision_case()
    demo_structured_data_case()
    demo_complex_mixed_case()
    demo_triage_response()
    demo_model_validation()

    print("\n" + "=" * 50)
    print("✅ All demos completed successfully!")
    print("\nThe TriageCase model is ready to handle:")
    print("  • Text-based symptoms and medical history")
    print("  • Structured medical data (blood tests, vital signs)")
    print("  • Medical images (retinal scans, X-rays, etc.)")
    print("  • Mixed combinations of all data types")
    print("  • Automatic processing requirement detection")
    print("  • Comprehensive validation and error handling")


if __name__ == "__main__":
    main()
