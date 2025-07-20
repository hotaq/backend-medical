from typing import Optional, Dict, Any, List, Union
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class DataType(str, Enum):
    """Enum for different types of data that can be processed"""
    TEXT = "text"
    STRUCTURED = "structured"
    IMAGE = "image"
    MIXED = "mixed"


class UrgencyLevel(str, Enum):
    """Enum for urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class StructuredDataType(str, Enum):
    """Enum for types of structured medical data"""
    BLOOD_TEST = "blood_test"
    VITAL_SIGNS = "vital_signs"
    MEDICAL_HISTORY = "medical_history"
    LAB_RESULTS = "lab_results"
    OTHER = "other"


class ImageData(BaseModel):
    """Model for image data information"""
    image_path: str = Field(..., description="Path or ID of the image file")
    image_type: Optional[str] = Field(None, description="Type of medical image (e.g., 'retinal', 'xray', 'ct_scan')")
    uploaded_at: Optional[datetime] = Field(default_factory=datetime.now)
    file_size: Optional[int] = Field(None, description="File size in bytes")

    @validator('image_path')
    def validate_image_path(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Image path cannot be empty')
        return v.strip()


class StructuredData(BaseModel):
    """Model for structured medical data"""
    data_type: StructuredDataType = Field(..., description="Type of structured data")
    data: Dict[str, Any] = Field(..., description="The actual structured data as key-value pairs")
    units: Optional[Dict[str, str]] = Field(None, description="Units for numeric values")
    reference_ranges: Optional[Dict[str, Dict[str, float]]] = Field(None, description="Normal reference ranges")
    test_date: Optional[datetime] = Field(None, description="When the test was conducted")

    @validator('data')
    def validate_data_not_empty(cls, v):
        if not v:
            raise ValueError('Structured data cannot be empty')
        return v


class PatientInfo(BaseModel):
    """Basic patient information"""
    patient_id: Optional[str] = Field(None, description="Unique patient identifier")
    age: Optional[int] = Field(None, ge=0, le=150, description="Patient age")
    gender: Optional[str] = Field(None, description="Patient gender")
    medical_record_number: Optional[str] = Field(None, description="Medical record number")


class TriageCase(BaseModel):
    """
    Main model for handling triage cases with multi-modal data support.

    This model can handle:
    - Text symptoms and descriptions
    - Structured medical data (blood tests, vital signs, etc.)
    - Medical images (retinal photos, X-rays, etc.)
    - Mixed combinations of the above
    """

    # Case identification
    case_id: Optional[str] = Field(None, description="Unique case identifier")
    created_at: datetime = Field(default_factory=datetime.now, description="Case creation timestamp")
    priority_level: Optional[UrgencyLevel] = Field(None, description="Initial priority assessment")

    # Patient information
    patient_info: Optional[PatientInfo] = Field(None, description="Basic patient information")

    # Text data (symptoms, complaints, medical history)
    symptoms_text: Optional[str] = Field(None, description="Patient's symptoms described in text")
    chief_complaint: Optional[str] = Field(None, description="Main reason for visit")
    medical_history: Optional[str] = Field(None, description="Relevant medical history")
    additional_notes: Optional[str] = Field(None, description="Any additional clinical notes")

    # Structured data (lab results, vital signs, etc.)
    structured_data: Optional[List[StructuredData]] = Field(None, description="List of structured medical data")

    # Image data (medical images, photos, scans)
    images: Optional[List[ImageData]] = Field(None, description="List of medical images")

    # Data type classification
    primary_data_type: Optional[DataType] = Field(None, description="Primary type of data in this case")

    # Processing metadata
    requires_vision_analysis: bool = Field(False, description="Whether this case needs vision BOT analysis")
    requires_text_analysis: bool = Field(False, description="Whether this case needs text BOT analysis")
    requires_structured_analysis: bool = Field(False, description="Whether this case needs structured data analysis")

    # Department/specialty routing
    target_department: Optional[str] = Field(None, description="Target medical department")
    specialty_required: Optional[str] = Field(None, description="Required medical specialty")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        schema_extra = {
            "example": {
                "patient_info": {
                    "patient_id": "P12345",
                    "age": 65,
                    "gender": "female"
                },
                "symptoms_text": "Blurred vision and seeing dark spots for the past week",
                "chief_complaint": "Vision problems",
                "structured_data": [
                    {
                        "data_type": "blood_test",
                        "data": {
                            "fasting_glucose": 180,
                            "hba1c": 8.5,
                            "cholesterol": 220
                        },
                        "units": {
                            "fasting_glucose": "mg/dL",
                            "hba1c": "%",
                            "cholesterol": "mg/dL"
                        }
                    }
                ],
                "images": [
                    {
                        "image_path": "/uploads/retinal_12345.jpg",
                        "image_type": "retinal"
                    }
                ],
                "requires_vision_analysis": True,
                "requires_text_analysis": True,
                "requires_structured_analysis": True,
                "target_department": "ophthalmology"
            }
        }

    @validator('primary_data_type', always=True)
    def determine_primary_data_type(cls, v, values):
        """Automatically determine primary data type if not provided"""
        if v is not None:
            return v

        has_text = bool(values.get('symptoms_text') or values.get('chief_complaint'))
        has_structured = bool(values.get('structured_data'))
        has_images = bool(values.get('images'))

        data_types_present = sum([has_text, has_structured, has_images])

        if data_types_present > 1:
            return DataType.MIXED
        elif has_images:
            return DataType.IMAGE
        elif has_structured:
            return DataType.STRUCTURED
        elif has_text:
            return DataType.TEXT
        else:
            return DataType.TEXT  # Default

    @validator('requires_vision_analysis', always=True)
    def set_vision_analysis_requirement(cls, v, values):
        """Automatically set vision analysis requirement based on images"""
        if values.get('images'):
            return True
        return v

    @validator('requires_text_analysis', always=True)
    def set_text_analysis_requirement(cls, v, values):
        """Automatically set text analysis requirement based on text data"""
        has_text = bool(
            values.get('symptoms_text') or
            values.get('chief_complaint') or
            values.get('medical_history')
        )
        if has_text:
            return True
        return v

    @validator('requires_structured_analysis', always=True)
    def set_structured_analysis_requirement(cls, v, values):
        """Automatically set structured analysis requirement based on structured data"""
        if values.get('structured_data'):
            return True
        return v

    def has_any_data(self) -> bool:
        """Check if the case has any meaningful data to process"""
        return bool(
            self.symptoms_text or
            self.chief_complaint or
            self.structured_data or
            self.images
        )

    def get_data_summary(self) -> Dict[str, Any]:
        """Get a summary of what data types are present"""
        return {
            "has_text": bool(self.symptoms_text or self.chief_complaint or self.medical_history),
            "has_structured_data": bool(self.structured_data),
            "has_images": bool(self.images),
            "text_count": len([x for x in [self.symptoms_text, self.chief_complaint, self.medical_history] if x]),
            "structured_count": len(self.structured_data) if self.structured_data else 0,
            "image_count": len(self.images) if self.images else 0,
            "primary_data_type": self.primary_data_type
        }

    def get_processing_requirements(self) -> Dict[str, bool]:
        """Get what types of processing this case requires"""
        return {
            "vision_analysis": self.requires_vision_analysis,
            "text_analysis": self.requires_text_analysis,
            "structured_analysis": self.requires_structured_analysis
        }


class TriageCaseResponse(BaseModel):
    """Response model for triage case processing results"""
    case_id: str
    processing_status: str
    triage_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Final triage score (0-1)")
    urgency_level: Optional[UrgencyLevel] = None
    estimated_wait_time: Optional[int] = Field(None, description="Estimated wait time in minutes")
    recommendations: Optional[List[str]] = Field(None, description="Clinical recommendations")
    processed_at: datetime = Field(default_factory=datetime.now)

    # Processing details
    vision_analysis_completed: bool = False
    text_analysis_completed: bool = False
    structured_analysis_completed: bool = False

    # Raw results from different components
    raw_vision_output: Optional[Dict[str, Any]] = None
    synthesized_vision_output: Optional[str] = None
    raw_text_output: Optional[Dict[str, Any]] = None
    synthesized_text_output: Optional[str] = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
