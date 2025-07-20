import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
import os
from transformers import AutoProcessor, AutoModelForImageTextToText
import torch
from PIL import Image
import io
import base64
import numpy as np

from models.schemas import VitalSigns, LabResults, MedicalImageData, PriorityLevel

logger = logging.getLogger(__name__)

class MedGemmaAgent:
    """Base class for MedGemma-powered medical agents"""

    def __init__(self, agent_name: str, model_id: str = "google/medgemma-4b-it"):
        self.agent_name = agent_name
        self.model_id = model_id
        self.model = None
        self.processor = None
        self.is_initialized = False

    async def initialize(self):
        """Initialize the MedGemma model"""
        try:
            logger.info(f"🔄 Initializing {self.agent_name} with {self.model_id}...")

            self.model = AutoModelForImageTextToText.from_pretrained(
                self.model_id,
                torch_dtype=torch.bfloat16,
                device_map="auto",
            )
            self.processor = AutoProcessor.from_pretrained(self.model_id)

            self.is_initialized = True
            logger.info(f"✅ {self.agent_name} initialized successfully")

        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.agent_name}: {str(e)}")
            # For demo/testing, create a mock model
            self.model = "mock_model"
            self.processor = "mock_processor"
            self.is_initialized = True
            logger.warning(f"⚠️ {self.agent_name} running in demo mode")

    async def cleanup(self):
        """Cleanup model resources"""
        if self.model and self.model != "mock_model":
            del self.model
            self.model = None
        if self.processor and self.processor != "mock_processor":
            del self.processor
            self.processor = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        self.is_initialized = False

class VisionBot(MedGemmaAgent):
    """
    Vision-BOT: Two-stage medical image analysis agent
    Stage 1: Traditional ML model for specific image analysis
    Stage 2: MedGemma LLM for interpretation and clinical reasoning
    """

    def __init__(self):
        super().__init__("VisionBot")
        self.vision_models = {}

    async def initialize(self):
        """Initialize both vision models and MedGemma"""
        await super().initialize()
        await self._load_vision_models()

    async def _load_vision_models(self):
        """Load traditional ML models for specific vision tasks"""
        try:
            logger.info("📦 Loading vision processing models...")

            # Simulate loading DR model
            self.vision_models['diabetic_retinopathy'] = {
                'loaded': True,
                'classes': ['no_dr', 'mild', 'moderate', 'severe', 'proliferative'],
                'model_type': 'cnn_classifier'
            }

            self.vision_models['glaucoma'] = {
                'loaded': True,
                'classes': ['normal', 'suspect', 'glaucoma'],
                'model_type': 'cnn_classifier'
            }

            logger.info("✅ Vision processing models loaded")

        except Exception as e:
            logger.warning(f"⚠️ Could not load all vision models: {str(e)}")

    async def analyze_image(
        self,
        image_data: Dict[str, Any],
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Two-stage image analysis:
        1. Traditional ML model for specific detection
        2. MedGemma for clinical interpretation
        """
        try:
            # Stage 1: Traditional ML Analysis
            ml_results = await self._stage1_ml_analysis(image_data)

            # Stage 2: MedGemma Clinical Interpretation
            clinical_analysis = await self._stage2_clinical_interpretation(
                image_data, ml_results, patient_context
            )

            # Combine results
            return {
                'success': True,
                'stage1_ml_results': ml_results,
                'stage2_clinical_analysis': clinical_analysis,
                'risk_score': clinical_analysis.get('risk_score', 0.0),
                'confidence': clinical_analysis.get('confidence', 0.0),
                'findings': clinical_analysis.get('findings', []),
                'recommendations': clinical_analysis.get('recommendations', [])
            }

        except Exception as e:
            logger.error(f"Error in vision analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'risk_score': 0.0,
                'confidence': 0.0
            }

    async def _stage1_ml_analysis(self, image_data: Dict[str, Any]) -> Dict[str, Any]:
        """Stage 1: Traditional ML model analysis"""
        try:
            image_type = image_data.get('image_type', '').lower()

            # Load image
            image = await self._load_image(image_data)
            if image is None:
                return {'error': 'Could not load image'}

            # Simulate ML model prediction based on image type
            if 'fundus' in image_type or 'retinal' in image_type:
                return await self._analyze_fundus_image(image)
            elif 'skin' in image_type or 'dermatology' in image_type:
                return await self._analyze_skin_image(image)
            else:
                return await self._analyze_generic_medical_image(image)

        except Exception as e:
            logger.error(f"Error in Stage 1 ML analysis: {str(e)}")
            return {'error': str(e)}

    async def _analyze_fundus_image(self, image) -> Dict[str, Any]:
        """Analyze fundus image for diabetic retinopathy"""
        # Simulate CNN model prediction
        np.random.seed(42)

        # Simulate model probabilities
        dr_probabilities = np.random.dirichlet([2, 1, 1, 1, 1])  # Bias towards no DR
        predicted_class_idx = np.argmax(dr_probabilities)

        classes = ['no_dr', 'mild', 'moderate', 'severe', 'proliferative']
        predicted_class = classes[predicted_class_idx]
        confidence = float(dr_probabilities[predicted_class_idx])

        return {
            'analysis_type': 'diabetic_retinopathy',
            'predicted_class': predicted_class,
            'confidence': confidence,
            'class_probabilities': dr_probabilities.tolist(),
            'ml_model': 'cnn_diabetic_retinopathy_v1',
            'technical_findings': {
                'microaneurysms': predicted_class_idx > 0,
                'hemorrhages': predicted_class_idx > 1,
                'exudates': predicted_class_idx > 2,
                'neovascularization': predicted_class_idx > 3
            }
        }

    async def _analyze_skin_image(self, image) -> Dict[str, Any]:
        """Analyze skin image for dermatological conditions"""
        np.random.seed(43)

        skin_probabilities = np.random.dirichlet([3, 1, 1, 1])  # Bias towards normal
        classes = ['normal', 'benign_lesion', 'suspicious_lesion', 'malignant']

        predicted_class_idx = np.argmax(skin_probabilities)
        predicted_class = classes[predicted_class_idx]
        confidence = float(skin_probabilities[predicted_class_idx])

        return {
            'analysis_type': 'skin_lesion',
            'predicted_class': predicted_class,
            'confidence': confidence,
            'class_probabilities': skin_probabilities.tolist(),
            'ml_model': 'cnn_skin_lesion_v1',
            'technical_findings': {
                'asymmetry': predicted_class_idx > 1,
                'border_irregularity': predicted_class_idx > 1,
                'color_variation': predicted_class_idx > 0,
                'diameter_large': predicted_class_idx > 2
            }
        }

    async def _analyze_generic_medical_image(self, image) -> Dict[str, Any]:
        """Generic medical image analysis"""
        return {
            'analysis_type': 'generic_medical',
            'predicted_class': 'normal',
            'confidence': 0.7,
            'ml_model': 'generic_medical_classifier_v1',
            'technical_findings': {
                'abnormalities_detected': False
            }
        }

    async def _stage2_clinical_interpretation(
        self,
        image_data: Dict[str, Any],
        ml_results: Dict[str, Any],
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Stage 2: MedGemma clinical interpretation"""
        try:
            if self.model == "mock_model":
                return self._mock_clinical_interpretation(ml_results, patient_context)

            # Load image for MedGemma
            image = await self._load_image(image_data)
            if image is None:
                return {'error': 'Could not load image for clinical interpretation'}

            # Prepare context for MedGemma
            context = self._prepare_clinical_context(ml_results, patient_context)

            # Create messages for MedGemma
            messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are an expert medical specialist analyzing medical images. Provide clinical interpretation, risk assessment, and recommendations."}]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": f"""Please analyze this medical image and provide clinical interpretation.

Context:
- Image type: {image_data.get('image_type', 'unknown')}
- ML Analysis Results: {json.dumps(ml_results, indent=2)}
- Patient Context: {context}

Please provide:
1. Clinical interpretation of the findings
2. Risk assessment (score 0.0-1.0)
3. Key clinical findings
4. Specific recommendations
5. Urgency level

Format your response as JSON with fields: clinical_interpretation, risk_score, confidence, findings, recommendations, urgency_level"""},
                        {"type": "image", "image": image}
                    ]
                }
            ]

            # Get MedGemma response
            response = await self._query_medgemma(messages)

            # Parse response
            return self._parse_clinical_response(response)

        except Exception as e:
            logger.error(f"Error in Stage 2 clinical interpretation: {str(e)}")
            return self._fallback_clinical_interpretation(ml_results)

    def _mock_clinical_interpretation(
        self,
        ml_results: Dict[str, Any],
        patient_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Mock clinical interpretation for demo mode"""
        analysis_type = ml_results.get('analysis_type', 'unknown')
        predicted_class = ml_results.get('predicted_class', 'normal')
        confidence = ml_results.get('confidence', 0.5)

        if analysis_type == 'diabetic_retinopathy':
            if predicted_class == 'no_dr':
                risk_score = 0.1
                findings = ['No diabetic retinopathy detected on fundus examination']
                recommendations = ['Continue routine diabetic eye screening annually']
            elif predicted_class in ['severe', 'proliferative']:
                risk_score = 0.9
                findings = [f'Severe diabetic retinopathy detected: {predicted_class}']
                recommendations = ['URGENT: Immediate ophthalmology referral required within 24-48 hours']
            else:
                risk_score = 0.5
                findings = [f'Diabetic retinopathy detected: {predicted_class} stage']
                recommendations = ['Ophthalmology referral recommended within 2-4 weeks']
        else:
            risk_score = confidence * 0.5
            findings = [f'{analysis_type} analysis: {predicted_class}']
            recommendations = ['Clinical correlation recommended']

        return {
            'clinical_interpretation': f'AI-assisted analysis shows {predicted_class} with {confidence:.2f} confidence. Patient context considered.',
            'risk_score': risk_score,
            'confidence': confidence,
            'findings': findings,
            'recommendations': recommendations,
            'urgency_level': 'urgent' if risk_score > 0.7 else 'routine'
        }

    async def _query_medgemma(self, messages: List[Dict]) -> str:
        """Query MedGemma model"""
        try:
            # Process the input
            prompt = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
            inputs = self.processor(prompt, messages[1]["content"][1]["image"], return_tensors="pt").to(self.model.device)

            # Generate response
            with torch.no_grad():
                output = self.model.generate(**inputs, max_new_tokens=500, do_sample=True, temperature=0.7)

            # Decode response
            response = self.processor.decode(output[0], skip_special_tokens=True)

            # Extract the generated part
            generated_text = response.split("assistant\n")[-1] if "assistant\n" in response else response

            return generated_text

        except Exception as e:
            logger.error(f"Error querying MedGemma: {str(e)}")
            raise

    def _prepare_clinical_context(self, ml_results: Dict[str, Any], patient_context: Dict[str, Any]) -> str:
        """Prepare clinical context for MedGemma"""
        context_parts = []

        if 'age' in patient_context:
            context_parts.append(f"Age: {patient_context['age']} years")
        if 'gender' in patient_context:
            context_parts.append(f"Gender: {patient_context['gender']}")
        if 'chronic_conditions' in patient_context:
            context_parts.append(f"Medical history: {patient_context['chronic_conditions']}")
        if 'chief_complaint' in patient_context:
            context_parts.append(f"Chief complaint: {patient_context['chief_complaint']}")

        return "; ".join(context_parts)

    def _parse_clinical_response(self, response: str) -> Dict[str, Any]:
        """Parse MedGemma clinical response"""
        try:
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)

            if json_match:
                json_str = json_match.group()
                parsed = json.loads(json_str)

                return {
                    'clinical_interpretation': parsed.get('clinical_interpretation', ''),
                    'risk_score': float(parsed.get('risk_score', 0.0)),
                    'confidence': float(parsed.get('confidence', 0.7)),
                    'findings': parsed.get('findings', []),
                    'recommendations': parsed.get('recommendations', []),
                    'urgency_level': parsed.get('urgency_level', 'routine')
                }
            else:
                return self._fallback_parse_response(response)

        except Exception as e:
            logger.warning(f"Error parsing clinical response: {str(e)}")
            return self._fallback_parse_response(response)

    def _fallback_parse_response(self, response: str) -> Dict[str, Any]:
        """Fallback response parsing"""
        import re
        risk_match = re.search(r'risk[:\s]+(\d*\.?\d+)', response.lower())
        risk_score = float(risk_match.group(1)) if risk_match else 0.3

        return {
            'clinical_interpretation': response,
            'risk_score': min(risk_score, 1.0),
            'confidence': 0.7,
            'findings': [response[:200] + "..." if len(response) > 200 else response],
            'recommendations': ['Clinical review recommended based on image findings'],
            'urgency_level': 'routine'
        }

    def _fallback_clinical_interpretation(self, ml_results: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback interpretation when MedGemma fails"""
        analysis_type = ml_results.get('analysis_type', 'unknown')
        predicted_class = ml_results.get('predicted_class', 'normal')
        confidence = ml_results.get('confidence', 0.5)

        if analysis_type == 'diabetic_retinopathy':
            if predicted_class == 'no_dr':
                risk_score = 0.1
                findings = ['No diabetic retinopathy detected']
                recommendations = ['Continue routine diabetic eye screening']
            elif predicted_class in ['severe', 'proliferative']:
                risk_score = 0.9
                findings = [f'Severe diabetic retinopathy detected: {predicted_class}']
                recommendations = ['URGENT: Immediate ophthalmology referral required']
            else:
                risk_score = 0.5
                findings = [f'Diabetic retinopathy detected: {predicted_class}']
                recommendations = ['Ophthalmology referral recommended']
        else:
            risk_score = confidence * 0.5
            findings = [f'{analysis_type} analysis: {predicted_class}']
            recommendations = ['Clinical correlation recommended']

        return {
            'clinical_interpretation': f'ML model detected {predicted_class} with {confidence:.2f} confidence',
            'risk_score': risk_score,
            'confidence': confidence,
            'findings': findings,
            'recommendations': recommendations,
            'urgency_level': 'routine' if risk_score < 0.7 else 'urgent'
        }

    async def _load_image(self, image_data: Dict[str, Any]) -> Optional[Image.Image]:
        """Load image from base64 or file path"""
        try:
            if 'image_base64' in image_data and image_data['image_base64']:
                image_bytes = base64.b64decode(image_data['image_base64'])
                return Image.open(io.BytesIO(image_bytes)).convert('RGB')
            elif 'image_url' in image_data and image_data['image_url']:
                return Image.open(image_data['image_url']).convert('RGB')
            else:
                logger.warning("No valid image data found")
                return None
        except Exception as e:
            logger.error(f"Error loading image: {str(e)}")
            return None

class TextBot(MedGemmaAgent):
    """
    Text-BOT: Medical text analysis using MedGemma for symptoms, lab results, and clinical reasoning
    """

    def __init__(self):
        super().__init__("TextBot")

    async def analyze_clinical_data(
        self,
        patient_data: Dict[str, Any],
        examination_data: Dict[str, Any],
        focus_area: str = "general"
    ) -> Dict[str, Any]:
        """Analyze clinical text data using MedGemma"""
        try:
            if self.model == "mock_model":
                return self._mock_text_analysis(patient_data, examination_data, focus_area)

            # Prepare clinical prompt
            clinical_context = self._prepare_text_context(patient_data, examination_data, focus_area)

            messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": f"You are an expert {focus_area} physician. Analyze the clinical data and provide comprehensive assessment."}]
                },
                {
                    "role": "user",
                    "content": [{"type": "text", "text": clinical_context}]
                }
            ]

            # Get MedGemma analysis
            response = await self._query_medgemma_text(messages)

            # Parse response
            return self._parse_text_response(response, focus_area)

        except Exception as e:
            logger.error(f"Error in text analysis: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'risk_score': 0.0,
                'confidence': 0.0
            }

    def _mock_text_analysis(
        self,
        patient_data: Dict[str, Any],
        examination_data: Dict[str, Any],
        focus_area: str
    ) -> Dict[str, Any]:
        """Mock text analysis for demo mode"""
        age = self._calculate_age(patient_data.get('date_of_birth', ''))
        chronic_conditions = patient_data.get('chronic_conditions', '').lower()
        chief_complaint = examination_data.get('chief_complaint', '').lower()

        # Simple risk assessment based on keywords
        risk_score = 0.3  # Base risk
        findings = []
        recommendations = []

        # Age factor
        if age > 65:
            risk_score += 0.1
            findings.append(f"Advanced age ({age} years) increases overall health risk")

        # Chronic conditions
        if 'diabetes' in chronic_conditions:
            risk_score += 0.2
            findings.append("Diabetes mellitus requires ongoing management")
            recommendations.append("Monitor blood glucose and HbA1c regularly")

        if 'hypertension' in chronic_conditions:
            risk_score += 0.15
            findings.append("Hypertension noted in medical history")
            recommendations.append("Blood pressure monitoring and management")

        # Chief complaint analysis
        if 'chest pain' in chief_complaint:
            risk_score += 0.3
            findings.append("Chest pain requires cardiovascular evaluation")
            recommendations.append("Consider ECG and cardiac biomarkers")

        if 'shortness of breath' in chief_complaint:
            risk_score += 0.2
            findings.append("Dyspnea may indicate cardiopulmonary pathology")
            recommendations.append("Evaluate respiratory and cardiac function")

        risk_score = min(risk_score, 1.0)

        return {
            'success': True,
            'clinical_assessment': f'Clinical assessment focused on {focus_area}. Patient presents with relevant findings requiring evaluation.',
            'risk_score': risk_score,
            'confidence': 0.8,
            'findings': findings if findings else ['Routine presentation'],
            'recommendations': recommendations if recommendations else ['Continue routine care'],
            'follow_up_plan': 'Follow up as clinically indicated',
            'differential_diagnosis': [],
            'focus_area': focus_area
        }

    def _prepare_text_context(
        self,
        patient_data: Dict[str, Any],
        examination_data: Dict[str, Any],
        focus_area: str
    ) -> str:
        """Prepare clinical context for text analysis"""

        context = f"""Please analyze this clinical case with focus on {focus_area}:

PATIENT INFORMATION:
- Age: {self._calculate_age(patient_data.get('date_of_birth', ''))} years
- Gender: {patient_data.get('gender', 'unknown')}
- Medical History: {patient_data.get('chronic_conditions', 'None reported')}
- Current Medications: {patient_data.get('current_medications', 'None reported')}
- Allergies: {patient_data.get('allergies', 'None reported')}

CURRENT PRESENTATION:
- Chief Complaint: {examination_data.get('chief_complaint', 'Not specified')}
- Symptoms: {examination_data.get('symptoms', 'Not specified')}

VITAL SIGNS:
{self._format_vital_signs(examination_data.get('vital_signs', {}))}

LABORATORY RESULTS:
{self._format_lab_results(examination_data.get('lab_results', {}))}

Please provide a comprehensive analysis including:
1. Clinical assessment and differential diagnosis
2. Risk stratification (score 0.0-1.0)
3. Key clinical findings
4. Specific recommendations for {focus_area}
5. Follow-up plan

Format your response as JSON with fields: clinical_assessment, risk_score, confidence, findings, recommendations, follow_up_plan, differential_diagnosis"""

        return context

    def _format_vital_signs(self, vital_signs: Dict[str, Any]) -> str:
        """Format vital signs for display"""
        if not vital_signs:
            return "- Not recorded"

        formatted = []
        if 'systolic_bp' in vital_signs and 'diastolic_bp' in vital_signs:
            formatted.append(f"- Blood Pressure: {vital_signs['systolic_bp']}/{vital_signs['diastolic_bp']} mmHg")
        if 'heart_rate' in vital_signs:
            formatted.append(f"- Heart Rate: {vital_signs['heart_rate']} bpm")
        if 'temperature' in vital_signs:
            formatted.append(f"- Temperature: {vital_signs['temperature']}°C")
        if 'oxygen_saturation' in vital_signs:
            formatted.append(f"- O2 Saturation: {vital_signs['oxygen_saturation']}%")
        if 'bmi' in vital_signs:
            formatted.append(f"- BMI: {vital_signs['bmi']}")

        return "\n".join(formatted) if formatted else "- Not recorded"

    def _format_lab_results(self, lab_results: Dict[str, Any]) -> str:
        """Format lab results for display"""
        if not lab_results:
            return "- Not available"

        formatted = []
        lab_mappings = {
            'glucose': 'Glucose',
            'hba1c': 'HbA1c',
            'creatinine': 'Creatinine',
            'egfr': 'eGFR',
            'cholesterol_total': 'Total Cholesterol',
            'cholesterol_ldl': 'LDL Cholesterol',
            'cholesterol_hdl': 'HDL Cholesterol',
            'triglycerides': 'Triglycerides',
            'hemoglobin': 'Hemoglobin',
            'tsh': 'TSH'
        }

        for key, label in lab_mappings.items():
            if key in lab_results:
                formatted.append(f"- {label}: {lab_results[key]}")

        return "\n".join(formatted) if formatted else "- Not available"

    async def _query_medgemma_text(self, messages: List[Dict]) -> str:
        """Query MedGemma for text analysis"""
        try:
            #
