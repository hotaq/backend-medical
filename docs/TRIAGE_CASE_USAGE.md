# TriageCase Model Usage Guide

## Overview

The `TriageCase` Pydantic model is the core data structure for handling multi-modal medical triage cases in the Triage-BOTS system. It supports text symptoms, structured medical data (lab results, vital signs), and medical images.

## Quick Start

```python
from app.models.triage_case import TriageCase, PatientInfo, StructuredData, ImageData

# Simple text-only case
case = TriageCase(
    symptoms_text="Patient reports chest pain and shortness of breath",
    chief_complaint="Chest pain"
)
```

## Model Structure

### Core Components

1. **TriageCase** - Main model for input data
2. **TriageCaseResponse** - Model for processing results
3. **PatientInfo** - Patient demographics
4. **StructuredData** - Lab results, vital signs, etc.
5. **ImageData** - Medical images metadata

### Data Types Supported

- **TEXT**: Symptoms, medical history, notes
- **STRUCTURED**: Blood tests, vital signs, lab results
- **IMAGE**: Retinal scans, X-rays, CT scans
- **MIXED**: Combination of above types

## Usage Examples

### 1. Text-Only Case

```python
from app.models.triage_case import TriageCase, PatientInfo

case = TriageCase(
    patient_info=PatientInfo(
        patient_id="P001",
        age=45,
        gender="male"
    ),
    symptoms_text="Severe chest pain radiating to left arm",
    chief_complaint="Chest pain",
    medical_history="Previous MI in 2020, diabetes, hypertension",
    target_department="cardiology"
)

# Check what processing is needed
print(case.get_processing_requirements())
# Output: {'vision_analysis': False, 'text_analysis': True, 'structured_analysis': False}
```

### 2. Vision/Image Case

```python
from app.models.triage_case import TriageCase, ImageData

images = [
    ImageData(
        image_path="/uploads/retinal_scans/patient_002_left.jpg",
        image_type="retinal"
    ),
    ImageData(
        image_path="/uploads/retinal_scans/patient_002_right.jpg", 
        image_type="retinal"
    )
]

case = TriageCase(
    symptoms_text="Blurred vision and dark spots",
    images=images,
    target_department="ophthalmology"
)

print(f"Requires vision analysis: {case.requires_vision_analysis}")  # True
print(f"Number of images: {len(case.images)}")  # 2
```

### 3. Structured Data Case

```python
from app.models.triage_case import TriageCase, StructuredData, StructuredDataType

structured_data = [
    StructuredData(
        data_type=StructuredDataType.BLOOD_TEST,
        data={
            "fasting_glucose": 185,
            "hba1c": 9.2,
            "total_cholesterol": 280
        },
        units={
            "fasting_glucose": "mg/dL",
            "hba1c": "%",
            "total_cholesterol": "mg/dL"
        },
        reference_ranges={
            "fasting_glucose": {"min": 70, "max": 100},
            "hba1c": {"min": 4.0, "max": 5.6}
        }
    )
]

case = TriageCase(
    symptoms_text="Fatigue and frequent urination",
    structured_data=structured_data,
    target_department="endocrinology"
)
```

### 4. Complex Mixed Case

```python
from app.models.triage_case import *

# Complete case with all data types
case = TriageCase(
    case_id="CASE_001",
    patient_info=PatientInfo(
        patient_id="P123",
        age=67,
        gender="female"
    ),
    symptoms_text="Shortness of breath, leg swelling",
    chief_complaint="Heart failure symptoms",
    medical_history="Stage 3 CKD, diabetes, hypertension",
    structured_data=[
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={"creatinine": 2.1, "bun": 45, "gfr": 35}
        )
    ],
    images=[
        ImageData(
            image_path="/uploads/chest_xray_123.jpg",
            image_type="chest_xray"
        )
    ],
    priority_level=UrgencyLevel.HIGH,
    target_department="nephrology"
)

# Get comprehensive data summary
summary = case.get_data_summary()
print(summary)
# Output: {
#   'has_text': True,
#   'has_structured_data': True, 
#   'has_images': True,
#   'text_count': 3,
#   'structured_count': 1,
#   'image_count': 1,
#   'primary_data_type': DataType.MIXED
# }
```

## Working with Responses

```python
from app.models.triage_case import TriageCaseResponse, UrgencyLevel

# Create response after processing
response = TriageCaseResponse(
    case_id="CASE_001",
    processing_status="completed",
    triage_score=0.87,  # 0.0 to 1.0
    urgency_level=UrgencyLevel.CRITICAL,
    estimated_wait_time=10,  # minutes
    recommendations=[
        "Immediate nephrology consultation required",
        "Monitor fluid balance closely"
    ],
    vision_analysis_completed=True,
    text_analysis_completed=True,
    structured_analysis_completed=True
)
```

## Validation Features

### Automatic Validation

```python
# Age validation
try:
    PatientInfo(age=-5)  # Fails: age must be 0-150
except ValidationError as e:
    print("Invalid age")

# Triage score validation  
try:
    TriageCaseResponse(
        case_id="TEST",
        processing_status="done", 
        triage_score=1.5  # Fails: must be 0.0-1.0
    )
except ValidationError as e:
    print("Invalid triage score")

# Empty image path fails
try:
    ImageData(image_path="")  # Fails: cannot be empty
except ValidationError as e:
    print("Invalid image path")
```

### Automatic Processing Detection

```python
case = TriageCase(
    symptoms_text="Vision problems",
    images=[ImageData(image_path="/test.jpg")]
)

# Automatically detects what processing is needed
print(case.requires_vision_analysis)    # True (has images)
print(case.requires_text_analysis)      # True (has text)
print(case.requires_structured_analysis) # False (no structured data)
print(case.primary_data_type)           # DataType.MIXED
```

## JSON Serialization

```python
# Export to JSON
case = TriageCase(symptoms_text="Test symptoms")
json_data = case.json(indent=2)

# Import from JSON
case_dict = {"symptoms_text": "Test symptoms"}
case = TriageCase(**case_dict)

# Check if case has meaningful data
if case.has_any_data():
    print("Case ready for processing")
```

## Integration with Chief-BOT

```python
# Example of how Chief-BOT will use this model
async def process_triage_case(case: TriageCase) -> TriageCaseResponse:
    requirements = case.get_processing_requirements()
    
    results = {}
    
    if requirements["vision_analysis"]:
        results["vision"] = await run_vision_agent(case.images)
    
    if requirements["text_analysis"]:
        results["text"] = await run_text_agent(case.symptoms_text)
        
    if requirements["structured_analysis"]:
        results["structured"] = await run_structured_agent(case.structured_data)
    
    # Calculate final triage score
    triage_score = calculate_final_score(results)
    
    return TriageCaseResponse(
        case_id=case.case_id,
        processing_status="completed",
        triage_score=triage_score,
        urgency_level=determine_urgency(triage_score)
    )
```

## Enums Reference

### DataType
- `TEXT`: Text-based data only
- `STRUCTURED`: Lab results, vital signs  
- `IMAGE`: Medical images
- `MIXED`: Multiple data types

### UrgencyLevel
- `LOW`: Non-urgent, routine care
- `MEDIUM`: Standard priority
- `HIGH`: Elevated priority
- `CRITICAL`: Immediate attention needed

### StructuredDataType
- `BLOOD_TEST`: Blood lab results
- `VITAL_SIGNS`: BP, HR, temp, etc.
- `MEDICAL_HISTORY`: Past medical history
- `LAB_RESULTS`: General lab results
- `OTHER`: Other structured data

## Best Practices

1. **Always validate input**: Use try/catch for ValidationError
2. **Check data availability**: Use `has_any_data()` before processing
3. **Use processing requirements**: Check what analysis types are needed
4. **Provide complete patient info**: Include age, gender when available
5. **Set appropriate target department**: Helps with routing
6. **Include units for structured data**: Essential for interpretation
7. **Use descriptive image types**: "retinal", "chest_xray", "ct_scan", etc.

## Testing

Run the test suite:

```bash
python -m pytest tests/test_triage_case_model.py -v
```

Run the demo:

```bash
python demo_triage_case.py
```

## Next Steps

This model is ready for integration with:
- **A2**: Database schema updates
- **B1**: Chief-BOT orchestrator  
- **C1-C3**: VisionBOT Agent
- **D1-D3**: TextBOT Agent
- **E1**: API endpoint refactoring