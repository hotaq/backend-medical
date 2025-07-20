# 🚀 Refactored `/triage` Endpoint - Medical Triage-BOTS System

## Overview

This document describes the refactored main `/triage` endpoint that uses the new TriageCase model, integrates with database operations, and handles multi-modal requests (text, images, structured data).

## 🏗️ Architecture

### Key Components

1. **FastAPI Application** (`main.py`)
   - Main application entry point
   - Endpoint definitions and routing
   - Middleware and CORS configuration

2. **TriageCase Model** (`app/models/triage_case.py`)
   - Pydantic models for request/response validation
   - Multi-modal data support
   - Automatic processing requirement detection

3. **Database Integration** (`app/database/`)
   - SQLAlchemy async models
   - CRUD operations
   - Transaction management

4. **ChiefBOT Orchestrator** (`app/agents/chief_bot.py`)
   - Multi-agent coordination
   - VisionBOT and TextBOT integration
   - Final triage score calculation

## 🎯 Endpoints

### Primary Endpoint: `POST /triage`

**Purpose**: Process medical triage cases with multi-modal data support

**Request Body**: `TriageCase` model

```json
{
  "case_id": "CASE_20241220_143022_ABC123EF",
  "patient_info": {
    "patient_id": "P12345",
    "age": 65,
    "gender": "female",
    "medical_record_number": "MRN-789456"
  },
  "symptoms_text": "Blurred vision and seeing dark spots for the past week",
  "chief_complaint": "Vision problems",
  "medical_history": "Diabetes Type 2, diagnosed 5 years ago",
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
      },
      "test_date": "2024-12-19T10:30:00Z"
    }
  ],
  "images": [
    {
      "image_path": "/uploads/retinal_12345.jpg",
      "image_type": "retinal",
      "file_size": 2048576
    }
  ]
}
```

**Response**: `TriageCaseResponse` model

```json
{
  "case_id": "CASE_20241220_143022_ABC123EF",
  "processing_status": "completed",
  "triage_score": 0.75,
  "urgency_level": "high",
  "estimated_wait_time": 15,
  "recommendations": [
    "Immediate ophthalmology consultation required",
    "Blood glucose management review needed",
    "Monitor for diabetic retinopathy progression"
  ],
  "processed_at": "2024-12-20T14:32:15Z",
  "vision_analysis_completed": true,
  "text_analysis_completed": true,
  "structured_analysis_completed": true,
  "synthesized_vision_output": "Retinal image shows signs of diabetic retinopathy...",
  "synthesized_text_output": "Patient presents with concerning vision symptoms..."
}
```

### Alternative Endpoint: `POST /triage/multipart`

**Purpose**: Handle form-based uploads with file attachments

**Form Fields**:
- `symptoms_text` (optional): Text description of symptoms
- `chief_complaint` (optional): Main complaint
- `medical_history` (optional): Medical history
- `patient_id` (optional): Patient identifier
- `age` (optional): Patient age
- `gender` (optional): Patient gender
- `structured_data` (optional): JSON string of structured data
- `images` (optional): File uploads for medical images

## 🔄 Processing Flow

### 1. Request Validation
- Validate TriageCase model structure
- Ensure at least one data type is present
- Auto-detect processing requirements

### 2. Database Operations
- Create/update patient record
- Store triage case with all related data
- Log processing start

### 3. Multi-Agent Processing
- Route to ChiefBOT orchestrator
- Coordinate VisionBOT and TextBOT agents
- Process text, images, and structured data

### 4. Response Generation
- Calculate final triage score
- Determine urgency level
- Generate clinical recommendations
- Estimate wait time

### 5. Audit and Metrics
- Log processing completion
- Update performance metrics
- Store audit trail

## 📊 Data Types Supported

### Text Data
- `symptoms_text`: Patient-described symptoms
- `chief_complaint`: Primary reason for visit
- `medical_history`: Relevant medical background
- `additional_notes`: Clinical observations

### Structured Data
- **Blood Tests**: Glucose, HbA1c, lipid panels
- **Vital Signs**: BP, heart rate, temperature
- **Lab Results**: Complete blood count, metabolic panels
- **Medical History**: Diagnoses, medications, allergies

### Image Data
- **Retinal Photos**: Fundus images for diabetic retinopathy
- **X-rays**: Chest, bone, joint imaging
- **CT Scans**: Cross-sectional imaging
- **MRI**: Magnetic resonance imaging
- **Ultrasound**: Echocardiograms, abdominal scans

## 🎛️ Configuration

### Environment Variables

```bash
# Database Configuration
DATABASE_URL=sqlite+aiosqlite:///./medical_triage_bots.db
DB_POOL_SIZE=5
DB_MAX_OVERFLOW=10
DB_ECHO=false

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1

# Logging
LOG_LEVEL=info
LOG_FILE=triage_api.log

# Security (for production)
SECRET_KEY=your-secret-key
ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
```

### Database Setup

```bash
# Initialize database tables
python -c "
import asyncio
from app.database.config import init_database
asyncio.run(init_database())
"
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r api_requirements.txt
```

### 2. Run Development Server

```bash
# Using the startup script
python run_api.py

# Or directly with uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 3. Test the Endpoint

```bash
# Simple text-only case
curl -X POST "http://localhost:8000/triage" \
  -H "Content-Type: application/json" \
  -d '{
    "symptoms_text": "Chest pain and shortness of breath",
    "chief_complaint": "Chest pain",
    "patient_info": {
      "age": 45,
      "gender": "male"
    }
  }'
```

### 4. Access Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 📈 Monitoring Endpoints

### Health Check: `GET /health`
Returns system health status including database connectivity and agent status.

### Metrics: `GET /metrics`
Returns application performance metrics:
- Total requests processed
- Success/failure rates
- Average processing time
- Case type distribution

## 🔧 Troubleshooting

### Common Issues

1. **Database Connection Errors**
   ```bash
   # Check database file permissions
   ls -la medical_triage_bots.db
   
   # Recreate database
   rm medical_triage_bots.db
   python -c "from app.database.config import init_database; import asyncio; asyncio.run(init_database())"
   ```

2. **Agent Initialization Failures**
   ```bash
   # Check if required models are available
   python -c "
   from app.agents.chief_bot import ChiefBOT
   import asyncio
   
   async def test():
       bot = ChiefBOT()
       await bot.initialize()
       print('✅ ChiefBOT initialized successfully')
   
   asyncio.run(test())
   "
   ```

3. **Memory Issues with Large Images**
   - Reduce image file sizes
   - Implement image compression
   - Use streaming for large files

### Debug Mode

```bash
# Run with debug logging
python run_api.py --log-level debug

# Check logs
tail -f triage_api.log
```

## 🧪 Testing

### Unit Tests

```bash
# Run all tests
pytest tests/

# Test specific endpoint
pytest tests/test_triage_endpoint.py -v

# Test with coverage
pytest --cov=app tests/
```

### Integration Tests

```bash
# Test database operations
python -m tests.test_database_integration

# Test agent coordination
python -m tests.test_agent_integration

# Test full pipeline
python -m tests.test_triage_pipeline
```

## 🔒 Security Considerations

### Production Deployment
- Enable HTTPS/TLS encryption
- Implement authentication/authorization
- Validate and sanitize all inputs
- Rate limiting and request throttling
- Secure file upload handling
- Database encryption at rest

### Data Privacy
- PHI/PII handling compliance
- Audit logging for all access
- Data retention policies
- Secure data transmission

## 📚 API Examples

### Multi-Modal Case Example

```python
import requests
import json

# Prepare case data
case_data = {
    "patient_info": {
        "patient_id": "P67890",
        "age": 72,
        "gender": "female"
    },
    "symptoms_text": "Sudden onset severe headache with vision changes",
    "chief_complaint": "Severe headache",
    "structured_data": [
        {
            "data_type": "vital_signs",
            "data": {
                "blood_pressure_systolic": 180,
                "blood_pressure_diastolic": 95,
                "heart_rate": 88,
                "temperature": 98.6
            },
            "units": {
                "blood_pressure_systolic": "mmHg",
                "blood_pressure_diastolic": "mmHg",
                "heart_rate": "bpm",
                "temperature": "°F"
            }
        }
    ],
    "images": [
        {
            "image_path": "/uploads/ct_head_67890.dcm",
            "image_type": "ct_scan"
        }
    ]
}

# Send request
response = requests.post(
    "http://localhost:8000/triage",
    json=case_data,
    headers={"Content-Type": "application/json"}
)

# Process response
if response.status_code == 200:
    result = response.json()
    print(f"Triage Score: {result['triage_score']}")
    print(f"Urgency Level: {result['urgency_level']}")
    print(f"Wait Time: {result['estimated_wait_time']} minutes")
    print("Recommendations:")
    for rec in result['recommendations']:
        print(f"  - {rec}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

## 🤝 Contributing

### Development Setup
1. Fork the repository
2. Create feature branch
3. Install development dependencies
4. Run tests before committing
5. Submit pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Document all functions
- Write comprehensive tests

## 📞 Support

For issues and questions:
- Check the troubleshooting section
- Review application logs
- Submit GitHub issues with detailed reproduction steps
- Include relevant log entries and system information

---

## 🎉 Features Delivered

✅ **Multi-modal triage processing** - Handles text, images, and structured data  
✅ **New TriageCase model integration** - Full Pydantic validation and serialization  
✅ **Database operations** - Complete CRUD with async SQLAlchemy  
✅ **ChiefBOT orchestration** - Coordinates VisionBOT and TextBOT agents  
✅ **Comprehensive error handling** - Robust error handling and logging  
✅ **Performance monitoring** - Built-in metrics and audit trails  
✅ **Production-ready** - CORS, health checks, and deployment scripts  
✅ **API documentation** - Auto-generated OpenAPI/Swagger docs  

The refactored `/triage` endpoint is now ready for production use with full multi-modal support and comprehensive database integration! 🏥🤖