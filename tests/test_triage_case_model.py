import pytest
import sys
import os
from datetime import datetime
from pydantic import ValidationError

# Add the backend directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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


class TestTriageCaseModel:
    """Test cases for TriageCase Pydantic model"""

    def test_empty_triage_case_creation(self):
        """Test creating an empty triage case"""
        case = TriageCase()
        assert case.case_id is None
        assert case.created_at is not None
        assert isinstance(case.created_at, datetime)
        assert not case.has_any_data()

    def test_text_only_case(self):
        """Test case with only text data"""
        case = TriageCase(
            symptoms_text="Patient complains of chest pain and shortness of breath",
            chief_complaint="Chest pain"
        )

        assert case.primary_data_type == DataType.TEXT
        assert case.requires_text_analysis is True
        assert case.requires_vision_analysis is False
        assert case.requires_structured_analysis is False
        assert case.has_any_data() is True

    def test_structured_data_only_case(self):
        """Test case with only structured data"""
        structured_data = [
            StructuredData(
                data_type=StructuredDataType.BLOOD_TEST,
                data={
                    "glucose": 180,
                    "cholesterol": 250,
                    "blood_pressure_systolic": 140
                },
                units={
                    "glucose": "mg/dL",
                    "cholesterol": "mg/dL",
                    "blood_pressure_systolic": "mmHg"
                }
            )
        ]

        case = TriageCase(structured_data=structured_data)

        assert case.primary_data_type == DataType.STRUCTURED
        assert case.requires_structured_analysis is True
        assert case.requires_text_analysis is False
        assert case.requires_vision_analysis is False
        assert case.has_any_data() is True

    def test_image_only_case(self):
        """Test case with only image data"""
        images = [
            ImageData(
                image_path="/uploads/retinal_scan_001.jpg",
                image_type="retinal"
            )
        ]

        case = TriageCase(images=images)

        assert case.primary_data_type == DataType.IMAGE
        assert case.requires_vision_analysis is True
        assert case.requires_text_analysis is False
        assert case.requires_structured_analysis is False
        assert case.has_any_data() is True

    def test_mixed_data_case(self):
        """Test case with mixed data types"""
        patient_info = PatientInfo(
            patient_id="P12345",
            age=65,
            gender="female"
        )

        structured_data = [
            StructuredData(
                data_type=StructuredDataType.BLOOD_TEST,
                data={"hba1c": 8.5, "fasting_glucose": 180},
                units={"hba1c": "%", "fasting_glucose": "mg/dL"}
            )
        ]

        images = [
            ImageData(
                image_path="/uploads/retinal_12345.jpg",
                image_type="retinal"
            )
        ]

        case = TriageCase(
            patient_info=patient_info,
            symptoms_text="Blurred vision and dark spots",
            chief_complaint="Vision problems",
            structured_data=structured_data,
            images=images,
            target_department="ophthalmology"
        )

        assert case.primary_data_type == DataType.MIXED
        assert case.requires_vision_analysis is True
        assert case.requires_text_analysis is True
        assert case.requires_structured_analysis is True
        assert case.has_any_data() is True

    def test_data_summary(self):
        """Test get_data_summary method"""
        case = TriageCase(
            symptoms_text="Chest pain",
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.VITAL_SIGNS,
                    data={"heart_rate": 100}
                )
            ]
        )

        summary = case.get_data_summary()

        assert summary["has_text"] is True
        assert summary["has_structured_data"] is True
        assert summary["has_images"] is False
        assert summary["text_count"] == 1
        assert summary["structured_count"] == 1
        assert summary["image_count"] == 0
        assert summary["primary_data_type"] == DataType.MIXED

    def test_processing_requirements(self):
        """Test get_processing_requirements method"""
        case = TriageCase(
            symptoms_text="Vision problems",
            images=[ImageData(image_path="/test.jpg")]
        )

        requirements = case.get_processing_requirements()

        assert requirements["vision_analysis"] is True
        assert requirements["text_analysis"] is True
        assert requirements["structured_analysis"] is False

    def test_patient_info_validation(self):
        """Test patient info validation"""
        patient_info = PatientInfo(
            patient_id="P123",
            age=45,
            gender="male"
        )

        case = TriageCase(patient_info=patient_info)
        assert case.patient_info.age == 45
        assert case.patient_info.gender == "male"

    def test_invalid_patient_age(self):
        """Test validation error for invalid patient age"""
        with pytest.raises(ValidationError):
            PatientInfo(age=-5)  # Negative age should fail

        with pytest.raises(ValidationError):
            PatientInfo(age=200)  # Age over 150 should fail

    def test_image_data_validation(self):
        """Test image data validation"""
        # Valid image data
        image = ImageData(image_path="/valid/path/image.jpg")
        assert image.image_path == "/valid/path/image.jpg"

        # Empty image path should fail
        with pytest.raises(ValidationError):
            ImageData(image_path="")

        with pytest.raises(ValidationError):
            ImageData(image_path="   ")  # Whitespace only

    def test_structured_data_validation(self):
        """Test structured data validation"""
        # Valid structured data
        data = StructuredData(
            data_type=StructuredDataType.LAB_RESULTS,
            data={"test1": 100, "test2": "normal"}
        )
        assert data.data_type == StructuredDataType.LAB_RESULTS

        # Empty data should fail
        with pytest.raises(ValidationError):
            StructuredData(
                data_type=StructuredDataType.BLOOD_TEST,
                data={}
            )


class TestTriageCaseResponse:
    """Test cases for TriageCaseResponse model"""

    def test_basic_response_creation(self):
        """Test creating a basic triage response"""
        response = TriageCaseResponse(
            case_id="CASE_001",
            processing_status="completed",
            triage_score=0.75,
            urgency_level=UrgencyLevel.HIGH
        )

        assert response.case_id == "CASE_001"
        assert response.triage_score == 0.75
        assert response.urgency_level == UrgencyLevel.HIGH
        assert response.processed_at is not None

    def test_triage_score_validation(self):
        """Test triage score validation (must be between 0 and 1)"""
        # Valid scores
        response1 = TriageCaseResponse(case_id="TEST", processing_status="done", triage_score=0.0)
        response2 = TriageCaseResponse(case_id="TEST", processing_status="done", triage_score=1.0)
        response3 = TriageCaseResponse(case_id="TEST", processing_status="done", triage_score=0.5)

        assert response1.triage_score == 0.0
        assert response2.triage_score == 1.0
        assert response3.triage_score == 0.5

        # Invalid scores should fail
        with pytest.raises(ValidationError):
            TriageCaseResponse(case_id="TEST", processing_status="done", triage_score=-0.1)

        with pytest.raises(ValidationError):
            TriageCaseResponse(case_id="TEST", processing_status="done", triage_score=1.1)

    def test_complete_response_with_all_fields(self):
        """Test response with all optional fields filled"""
        response = TriageCaseResponse(
            case_id="COMPLETE_001",
            processing_status="completed",
            triage_score=0.85,
            urgency_level=UrgencyLevel.CRITICAL,
            estimated_wait_time=15,
            recommendations=["Immediate attention required", "Monitor vital signs"],
            vision_analysis_completed=True,
            text_analysis_completed=True,
            structured_analysis_completed=True,
            raw_vision_output={"confidence": 0.92, "prediction": "severe_dr"},
            synthesized_vision_output="Severe diabetic retinopathy detected",
            raw_text_output={"risk_score": 0.8},
            synthesized_text_output="High cardiovascular risk identified"
        )

        assert response.urgency_level == UrgencyLevel.CRITICAL
        assert response.estimated_wait_time == 15
        assert len(response.recommendations) == 2
        assert response.vision_analysis_completed is True
        assert response.raw_vision_output["confidence"] == 0.92


class TestEnums:
    """Test enum definitions"""

    def test_data_type_enum(self):
        """Test DataType enum values"""
        assert DataType.TEXT == "text"
        assert DataType.STRUCTURED == "structured"
        assert DataType.IMAGE == "image"
        assert DataType.MIXED == "mixed"

    def test_urgency_level_enum(self):
        """Test UrgencyLevel enum values"""
        assert UrgencyLevel.LOW == "low"
        assert UrgencyLevel.MEDIUM == "medium"
        assert UrgencyLevel.HIGH == "high"
        assert UrgencyLevel.CRITICAL == "critical"

    def test_structured_data_type_enum(self):
        """Test StructuredDataType enum values"""
        assert StructuredDataType.BLOOD_TEST == "blood_test"
        assert StructuredDataType.VITAL_SIGNS == "vital_signs"
        assert StructuredDataType.MEDICAL_HISTORY == "medical_history"
        assert StructuredDataType.LAB_RESULTS == "lab_results"
        assert StructuredDataType.OTHER == "other"


if __name__ == "__main__":
    pytest.main([__file__])
