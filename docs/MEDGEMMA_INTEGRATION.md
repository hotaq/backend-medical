# MedGemma Integration for Medical Triage-BOTS

## Overview

This document describes the integration of Google's MedGemma models into the Medical Triage-BOTS system. MedGemma is a specialized medical AI model based on Gemma 3, designed specifically for healthcare applications and medical text understanding.

## What is MedGemma?

MedGemma is a collection of Gemma 3 variants trained for performance on medical text and image comprehension. It comes in three variants:
- **MedGemma 4B (multimodal)** - Recommended for most applications
- **MedGemma 27B (text-only)** - High performance text processing
- **MedGemma 27B (multimodal)** - Maximum performance with image support

## Integration Architecture

### Chief-BOT Orchestrator with MedGemma

The system uses MedGemma in two key areas:

1. **Orchestration**: ChiefBOT uses MedGemma to analyze patient data and decide which specialized ML tools to invoke
2. **Synthesis**: MedGemma combines results from multiple agents into comprehensive medical assessments

```
Patient Data → ChiefBOT (MedGemma) → Tool Selection → Agent Processing → Synthesis (MedGemma) → Final Assessment
```

### Multi-Agent Workflow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Patient Data  │───→│  ChiefBOT with   │───→│  Agent Results  │
│                 │    │    MedGemma      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Specialized Tools│
                       │                  │
                       │ • VisionBOT      │
                       │ • TextBOT        │
                       │ • ML Models      │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ MedGemma         │
                       │ Synthesis        │
                       └──────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │ Final Medical    │
                       │ Assessment       │
                       └──────────────────┘
```

## Configuration

### Environment Variables

```bash
# Hugging Face Token (Required)
HF_TOKEN=your_huggingface_token_here
HUGGINGFACE_HUB_TOKEN=your_huggingface_token_here

# Model Configuration
MEDGEMMA_MODEL_SIZE=medium          # small (2b), medium (4b), large (27b)
MEDGEMMA_DEPLOYMENT_MODE=production # development, testing, production, high_performance
MEDGEMMA_QUANTIZATION=true          # Enable for memory efficiency
MEDGEMMA_MAX_TOKENS=1024           # Maximum response length
MEDGEMMA_TEMPERATURE=0.1           # Low for medical accuracy

# Cache and Performance
HF_HOME=/app/models
TRANSFORMERS_CACHE=/app/models/transformers
TOKENIZERS_PARALLELISM=false
PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512
```

### Model Sizes and Requirements

| Model Size | Parameters | Memory Required | Use Case |
|------------|------------|-----------------|----------|
| Small | 2B | ~4GB | Development, Testing |
| Medium | 4B | ~8GB | Production (Recommended) |
| Large | 27B | ~32GB | High Performance |

## Docker Setup

### Quick Start

1. **Ensure you have the Hugging Face token in .env file**:
   ```bash
   HF_TOKEN=your_huggingface_token_here
   ```

2. **Start the development environment**:
   ```bash
   ./scripts/start-dev.sh
   ```

3. **Test the integration**:
   ```bash
   docker-compose -f docker-compose.dev.yml exec backend python scripts/test_medgemma_docker.py
   ```

### Production Deployment

```bash
# Build with production settings
docker-compose build --build-arg HF_TOKEN=${HF_TOKEN}

# Start production stack
docker-compose up -d

# Verify MedGemma is working
curl http://localhost:8000/health
```

## API Integration

### Health Check with MedGemma Status

```bash
GET /health
```

Response includes MedGemma status:
```json
{
  "status": "healthy",
  "timestamp": "2024-07-20T14:30:00Z",
  "components": {
    "chief_bot": "operational",
    "database": "operational",
    "medgemma": "loaded",
    "vision_bot": "operational",
    "text_bot": "operational"
  },
  "medgemma_info": {
    "model_name": "google/medgemma-4b-it",
    "quantization": true,
    "memory_usage": "4.2GB"
  }
}
```

### Triage Processing with MedGemma

```bash
POST /triage
```

Request:
```json
{
  "case_id": "CASE_001",
  "chief_complaint": "Chest pain and shortness of breath",
  "symptoms_text": "Sudden onset chest pain, radiating to left arm, shortness of breath, sweating",
  "structured_data": [
    {
      "data_type": "vital_signs",
      "values": {
        "blood_pressure": "140/90",
        "heart_rate": 110,
        "temperature": 98.6
      }
    }
  ]
}
```

Response with MedGemma Analysis:
```json
{
  "case_id": "CASE_001",
  "final_triage_score": 0.85,
  "urgency_level": "high",
  "confidence_score": 0.82,
  "recommendations": [
    "Immediate cardiac evaluation required",
    "Consider 12-lead ECG and cardiac enzymes",
    "Monitor vital signs continuously"
  ],
  "reasoning": "AI-Powered Medical Analysis:\nClinical Impression: The patient presents with classic symptoms suggestive of acute coronary syndrome...",
  "processing_summary": {
    "total_processing_time_ms": 2500,
    "synthesis_time_ms": 800,
    "medgemma_enabled": true,
    "agents_executed": 2
  }
}
```

## Code Examples

### ChiefBOT with MedGemma

```python
from app.agents.chief_bot import ChiefBOT
from app.models.triage_case import TriageCase

# Initialize ChiefBOT with MedGemma
config = {
    "deployment_mode": "production",
    "available_memory_gb": 8,
    "has_gpu": True
}

chief_bot = ChiefBOT(config=config)

# Process triage case
triage_case = TriageCase(
    case_id="TEST_001",
    chief_complaint="Severe headache with visual disturbances",
    symptoms_text="Sudden onset severe headache, nausea, blurred vision"
)

result = await chief_bot.process_triage_case(triage_case)
print(f"Urgency: {result.urgency_level}")
print(f"Score: {result.final_triage_score}")
print(f"AI Analysis: {result.reasoning}")
```

### Direct MedGemma Usage

```python
from app.agents.llm_text_bot import LLMTextBOT

# Initialize LLM TextBOT with MedGemma
llm_bot = LLMTextBOT(model_name="google/medgemma-4b-it")

# Analyze symptoms
symptoms = "Patient reports chest pain and difficulty breathing"
result = await llm_bot.analyze_symptoms(symptoms)

if result.success:
    analysis = result.symptom_analysis
    print(f"Risk Level: {analysis.risk_level}")
    print(f"Primary Symptoms: {analysis.primary_symptoms}")
    print(f"Recommendations: {analysis.recommendations}")
```

## Testing

### Quick Docker Test

```bash
# Run quick verification
docker-compose -f docker-compose.dev.yml exec backend python scripts/test_medgemma_docker.py
```

### Comprehensive Test

```bash
# Run full test suite
docker-compose -f docker-compose.dev.yml exec backend python scripts/test_medgemma.py
```

### Interactive Testing

```bash
# Start interactive shell
docker-compose -f docker-compose.dev.yml exec backend python scripts/docker-entrypoint.sh shell

# Test in Python shell
>>> from app.agents.chief_bot import ChiefBOT
>>> chief_bot = ChiefBOT()
>>> await chief_bot.load_medgemma()
>>> print("MedGemma loaded:", chief_bot.is_medgemma_loaded)
```

## Performance Optimization

### Memory Management

1. **Quantization**: Enable 4-bit quantization to reduce memory usage by ~60%
2. **Model Caching**: Models are cached in Docker volumes for faster startup
3. **Single Worker**: Use single worker process to avoid memory duplication

### Recommended Settings

```bash
# For systems with 8GB RAM
MEDGEMMA_MODEL_SIZE=medium
MEDGEMMA_QUANTIZATION=true
BACKEND_MEMORY_LIMIT=6G

# For systems with 16GB+ RAM
MEDGEMMA_MODEL_SIZE=medium
MEDGEMMA_QUANTIZATION=false
BACKEND_MEMORY_LIMIT=8G

# For high-performance systems (32GB+ RAM)
MEDGEMMA_MODEL_SIZE=large
MEDGEMMA_QUANTIZATION=false
BACKEND_MEMORY_LIMIT=16G
```

## Troubleshooting

### Common Issues

1. **Model Download Fails**
   ```bash
   # Check HF token
   echo $HF_TOKEN
   
   # Test authentication
   python -c "from huggingface_hub import whoami; print(whoami(token='$HF_TOKEN'))"
   ```

2. **Out of Memory**
   ```bash
   # Enable quantization
   MEDGEMMA_QUANTIZATION=true
   
   # Use smaller model
   MEDGEMMA_MODEL_SIZE=small
   
   # Increase Docker memory limit
   docker system info | grep "Total Memory"
   ```

3. **Slow Model Loading**
   ```bash
   # Check if model is cached
   docker-compose exec backend ls -la /app/models/transformers/
   
   # Pre-download model
   docker-compose exec backend python -c "
   from transformers import AutoProcessor
   AutoProcessor.from_pretrained('google/medgemma-4b-it')
   "
   ```

### Debug Commands

```bash
# Check container resources
docker stats medical-backend-dev

# View MedGemma logs
docker-compose logs backend | grep -i medgemma

# Monitor memory usage
docker-compose exec backend python -c "
import torch
print(f'GPU Memory: {torch.cuda.memory_allocated()/1024**3:.1f}GB')
"

# Test configuration
docker-compose exec backend python -c "
from config.medgemma_config import MedGemmaConfig
config = MedGemmaConfig.from_environment()
print(config)
"
```

## Security Considerations

1. **Token Management**: Store HF_TOKEN securely, never commit to version control
2. **Model Validation**: Verify model checksums and signatures
3. **Access Control**: Limit API access to authorized users
4. **Data Privacy**: Ensure patient data is not logged or cached

## Future Enhancements

1. **Model Fine-tuning**: Custom training on hospital-specific data
2. **Multi-GPU Support**: Scale to multiple GPUs for larger models
3. **Model Versioning**: A/B testing of different model versions
4. **Real-time Monitoring**: Performance and accuracy metrics
5. **Federated Learning**: Collaborative model improvement

## Support

For issues related to MedGemma integration:

1. Check the troubleshooting section above
2. Review container logs: `docker-compose logs backend`
3. Run diagnostic tests: `python scripts/test_medgemma_docker.py`
4. Verify environment configuration
5. Check Hugging Face model status and token permissions

## References

- [MedGemma Model Card](https://huggingface.co/google/medgemma-4b-it)
- [MedGemma Technical Report](https://arxiv.org/abs/2507.05201)
- [Transformers Documentation](https://huggingface.co/docs/transformers/)
- [Docker GPU Support](https://docs.docker.com/config/containers/resource_constraints/#gpu)