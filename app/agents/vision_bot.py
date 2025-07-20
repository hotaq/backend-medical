"""
VisionBot Agent for Medical Image Analysis

This module implements the VisionBot agent that processes medical images using
MedGemma multimodal models. It integrates with the Chief-BOT orchestrator to
provide comprehensive medical image analysis.

Features:
- MedGemma multimodal model integration
- Support for multiple medical image types
- Two-stage analysis: ML detection + clinical interpretation
- Structured output compatible with Chief-BOT scoring
- Comprehensive error handling and logging
- Performance monitoring and caching

Supported Image Types:
- Chest X-rays
- Retinal/Fundus images
- Dermatology images
- ECG images
- CT scans
- Histopathology slides
"""

import asyncio
import logging
import time
import json
import os
from typing import Dict, Any, List, Optional, Tuple, Union
from datetime import datetime
from pathlib import Path
import base64
import io

# Core dependencies
import numpy as np
from PIL import Image, ImageOps
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText

# App imports
from ..models.triage_case import ImageData
from ..models.pydantic_compat import model_dump

# Setup logging
logger = logging.getLogger(__name__)


class MedicalImageType:
    """Medical image type classifications"""
    CHEST_XRAY = "chest_xray"
    RETINAL_SCAN = "retinal_scan"
    FUNDUS = "fundus"
    DERMATOLOGY = "dermatology"
    ECG = "ecg"
    CT_SCAN = "ct_scan"
    HISTOPATHOLOGY = "histopathology"
    ULTRASOUND = "ultrasound"
    MRI = "mri"
    MAMMOGRAPHY = "mammography"
    GENERIC = "generic"


class VisionBotConfig:
    """Configuration for VisionBot agent"""

    def __init__(self):
        # Model configuration
        self.model_id = os.getenv("MEDGEMMA_MODEL_ID", "google/medgemma-4b-it")
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.torch_dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
        self.max_image_size = (512, 512)
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff']

        # Performance settings
        self.max_new_tokens = 500
        self.temperature = 0.7
        self.do_sample = True
        self.cache_predictions = True
        self.processing_timeout = 30  # seconds

        # Clinical thresholds
        self.high_risk_threshold = 0.7
        self.moderate_risk_threshold = 0.4

        # Mock mode for development/testing
        self.mock_mode = os.getenv("VISION_BOT_MOCK_MODE", "true").lower() == "true"


class ImageProcessor:
    """Utility class for image preprocessing and validation"""

    def __init__(self, config: VisionBotConfig):
        self.config = config

    def validate_image_path(self, image_path: str) -> bool:
        """Validate image file path and format"""
        try:
            path = Path(image_path)
            return path.exists() and path.suffix.lower() in self.config.supported_formats
        except Exception:
            return False

    def load_image_from_path(self, image_path: str) -> Optional[Image.Image]:
        """Load and preprocess image from file path"""
        try:
            if not self.validate_image_path(image_path):
                logger.warning(f"Invalid image path: {image_path}")
                return None

            # Load image
            image = Image.open(image_path)

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large
            if image.size[0] > self.config.max_image_size[0] or image.size[1] > self.config.max_image_size[1]:
                image = ImageOps.fit(image, self.config.max_image_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.error(f"Failed to load image {image_path}: {e}")
            return None

    def load_image_from_base64(self, base64_data: str) -> Optional[Image.Image]:
        """Load image from base64 encoded data"""
        try:
            # Remove data URL prefix if present
            if base64_data.startswith('data:image'):
                base64_data = base64_data.split(',')[1]

            # Decode base64
            image_bytes = base64.b64decode(base64_data)
            image = Image.open(io.BytesIO(image_bytes))

            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')

            # Resize if too large
            if image.size[0] > self.config.max_image_size[0] or image.size[1] > self.config.max_image_size[1]:
                image = ImageOps.fit(image, self.config.max_image_size, Image.Resampling.LANCZOS)

            return image

        except Exception as e:
            logger.error(f"Failed to load image from base64: {e}")
            return None

    def detect_image_type(self, image_data: ImageData) -> str:
        """Detect medical image type from metadata and filename"""
        image_type = image_data.image_type
        image_path = image_data.image_path.lower()

        # Use explicit image_type if provided
        if image_type:
            image_type_lower = image_type.lower()
            if any(keyword in image_type_lower for keyword in ['xray', 'x-ray', 'chest']):
                return MedicalImageType.CHEST_XRAY
            elif any(keyword in image_type_lower for keyword in ['retinal', 'fundus', 'ophthalmology']):
                return MedicalImageType.RETINAL_SCAN
            elif any(keyword in image_type_lower for keyword in ['skin', 'dermatology', 'dermoscopy']):
                return MedicalImageType.DERMATOLOGY
            elif 'ecg' in image_type_lower or 'ekg' in image_type_lower:
                return MedicalImageType.ECG
            elif 'ct' in image_type_lower or 'computed' in image_type_lower:
                return MedicalImageType.CT_SCAN
            elif any(keyword in image_type_lower for keyword in ['histology', 'pathology', 'biopsy']):
                return MedicalImageType.HISTOPATHOLOGY

        # Fallback to filename analysis
        if any(keyword in image_path for keyword in ['xray', 'x-ray', 'chest']):
            return MedicalImageType.CHEST_XRAY
        elif any(keyword in image_path for keyword in ['retinal', 'fundus', 'eye']):
            return MedicalImageType.RETINAL_SCAN
        elif any(keyword in image_path for keyword in ['skin', 'derma']):
            return MedicalImageType.DERMATOLOGY
        elif 'ecg' in image_path or 'ekg' in image_path:
            return MedicalImageType.ECG

        return MedicalImageType.GENERIC


class VisionBot:
    """
    VisionBot Agent for Medical Image Analysis

    Uses MedGemma multimodal models to analyze medical images and provide
    clinical interpretations, risk assessments, and recommendations.
    """

    def __init__(self, config: Optional[VisionBotConfig] = None):
        self.config = config or VisionBotConfig()
        self.image_processor = ImageProcessor(self.config)

        # Model components
        self.model = None
        self.processor = None
        self.is_initialized = False

        # Performance tracking
        self.prediction_cache = {}
        self.processing_stats = {
            "total_images_processed": 0,
            "successful_predictions": 0,
            "failed_predictions": 0,
            "average_processing_time": 0.0,
            "cache_hits": 0
        }

        logger.info(f"VisionBot initialized with device: {self.config.device}")

    async def initialize(self) -> bool:
        """Initialize MedGemma model and processor"""
        if self.is_initialized:
            return True

        if self.config.mock_mode:
            logger.info("🔧 VisionBot running in mock mode")
            self.model = "mock_model"
            self.processor = "mock_processor"
            self.is_initialized = True
            return True

        try:
            logger.info(f"🔄 Initializing VisionBot with {self.config.model_id}...")

            # Load processor
            self.processor = AutoProcessor.from_pretrained(self.config.model_id)

            # Load model
            self.model = AutoModelForImageTextToText.from_pretrained(
                self.config.model_id,
                torch_dtype=self.config.torch_dtype,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )

            self.is_initialized = True
            logger.info("✅ VisionBot initialized successfully")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize VisionBot: {e}")
            logger.info("🔄 Falling back to mock mode")
            self.config.mock_mode = True
            self.model = "mock_model"
            self.processor = "mock_processor"
            self.is_initialized = True
            return True

    async def process_images(self, images: List[ImageData]) -> Dict[str, Any]:
        """
        Process multiple medical images and return comprehensive analysis

        Args:
            images: List of ImageData objects to analyze

        Returns:
            Dict containing analysis results, confidence scores, and recommendations
        """
        start_time = time.time()

        try:
            if not await self.initialize():
                return self._create_error_response("Failed to initialize VisionBot")

            if not images:
                return self._create_error_response("No images provided for analysis")

            logger.info(f"🔍 Processing {len(images)} medical images")

            # Process each image
            image_results = []
            for i, image_data in enumerate(images):
                try:
                    result = await self._process_single_image(image_data, i)
                    image_results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process image {i}: {e}")
                    image_results.append({
                        "image_index": i,
                        "success": False,
                        "error": str(e)
                    })

            # Aggregate results
            aggregated_result = self._aggregate_image_results(image_results)

            # Update statistics
            processing_time = (time.time() - start_time) * 1000
            self._update_processing_stats(len(images), True, processing_time)

            # Add metadata
            aggregated_result.update({
                "processing_time_ms": int(processing_time),
                "images_processed": len(images),
                "model_version": self.config.model_id,
                "agent_type": "vision_bot"
            })

            logger.info(f"✅ VisionBot completed processing in {processing_time:.1f}ms")
            return aggregated_result

        except Exception as e:
            processing_time = (time.time() - start_time) * 1000
            self._update_processing_stats(len(images) if images else 0, False, processing_time)
            logger.error(f"❌ VisionBot processing failed: {e}")
            return self._create_error_response(str(e))

    async def _process_single_image(self, image_data: ImageData, index: int) -> Dict[str, Any]:
        """Process a single medical image"""
        try:
            # Detect image type
            detected_type = self.image_processor.detect_image_type(image_data)

            # Load image
            image = await self._load_image(image_data)
            if image is None:
                return {
                    "image_index": index,
                    "success": False,
                    "error": "Could not load image"
                }

            # Check cache
            cache_key = self._generate_cache_key(image_data, detected_type)
            if cache_key in self.prediction_cache:
                self.processing_stats["cache_hits"] += 1
                cached_result = self.prediction_cache[cache_key].copy()
                cached_result["image_index"] = index
                cached_result["from_cache"] = True
                return cached_result

            # Perform analysis
            if self.config.mock_mode:
                analysis_result = await self._mock_image_analysis(image_data, detected_type)
            else:
                analysis_result = await self._analyze_with_medgemma(image, image_data, detected_type)

            # Cache result
            if self.config.cache_predictions:
                self.prediction_cache[cache_key] = analysis_result.copy()

            analysis_result["image_index"] = index
            analysis_result["success"] = True

            return analysis_result

        except Exception as e:
            logger.error(f"Single image processing failed: {e}")
            return {
                "image_index": index,
                "success": False,
                "error": str(e)
            }

    async def _load_image(self, image_data: ImageData) -> Optional[Image.Image]:
        """Load image from ImageData object"""
        try:
            image_path = image_data.image_path

            # Handle different image path formats
            if image_path.startswith('data:image'):
                # Base64 encoded image
                return self.image_processor.load_image_from_base64(image_path)
            elif image_path.startswith('http'):
                # URL - would need additional handling
                logger.warning("URL-based images not yet supported")
                return None
            else:
                # File path
                return self.image_processor.load_image_from_path(image_path)

        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None

    async def _analyze_with_medgemma(self, image: Image.Image, image_data: ImageData, detected_type: str) -> Dict[str, Any]:
        """Analyze image using MedGemma multimodal model"""
        try:
            # Prepare prompt based on image type
            prompt = self._generate_medical_prompt(detected_type, image_data)

            # Prepare messages for MedGemma
            messages = [
                {
                    "role": "system",
                    "content": [{"type": "text", "text": "You are an expert medical specialist analyzing medical images. Provide accurate clinical interpretation, risk assessment, and recommendations based on the image findings."}]
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image", "image": image}
                    ]
                }
            ]

            # Apply chat template
            text_prompt = self.processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

            # Process inputs
            inputs = self.processor(
                text_prompt,
                images=image,
                return_tensors="pt"
            ).to(self.model.device)

            # Generate response
            with torch.no_grad():
                output = self.model.generate(
                    **inputs,
                    max_new_tokens=self.config.max_new_tokens,
                    do_sample=self.config.do_sample,
                    temperature=self.config.temperature,
                    pad_token_id=self.processor.tokenizer.eos_token_id
                )

            # Decode response
            response = self.processor.decode(output[0], skip_special_tokens=True)

            # Extract generated part (remove input prompt)
            generated_text = response[len(text_prompt):].strip()

            # Parse the medical response
            return self._parse_medical_response(generated_text, detected_type)

        except Exception as e:
            logger.error(f"MedGemma analysis failed: {e}")
            return self._fallback_analysis(detected_type)

    async def _mock_image_analysis(self, image_data: ImageData, detected_type: str) -> Dict[str, Any]:
        """Mock image analysis for development and testing"""
        await asyncio.sleep(0.1)  # Simulate processing time

        # Generate realistic mock results based on image type
        if detected_type == MedicalImageType.RETINAL_SCAN:
            return {
                "image_type": detected_type,
                "predicted_class": "moderate_diabetic_retinopathy",
                "confidence": 0.87,
                "risk_score": 0.65,
                "clinical_findings": [
                    "Microaneurysms present in multiple quadrants",
                    "Hard exudates near the macula",
                    "Mild cotton wool spots observed"
                ],
                "recommendations": [
                    "Ophthalmology referral recommended",
                    "Diabetic control optimization",
                    "Follow-up imaging in 3-6 months"
                ],
                "urgency_level": "high",
                "technical_quality": "good",
                "model_version": "mock_retinal_classifier_v1"
            }

        elif detected_type == MedicalImageType.CHEST_XRAY:
            return {
                "image_type": detected_type,
                "predicted_class": "normal",
                "confidence": 0.92,
                "risk_score": 0.15,
                "clinical_findings": [
                    "Clear lung fields bilaterally",
                    "Normal cardiac silhouette",
                    "No acute abnormalities"
                ],
                "recommendations": [
                    "No immediate action required",
                    "Routine follow-up as clinically indicated"
                ],
                "urgency_level": "routine",
                "technical_quality": "excellent",
                "model_version": "mock_chest_classifier_v1"
            }

        elif detected_type == MedicalImageType.DERMATOLOGY:
            return {
                "image_type": detected_type,
                "predicted_class": "benign_nevus",
                "confidence": 0.78,
                "risk_score": 0.25,
                "clinical_findings": [
                    "Symmetric pigmented lesion",
                    "Regular borders",
                    "Uniform coloration"
                ],
                "recommendations": [
                    "Routine dermatological monitoring",
                    "Patient education on self-examination"
                ],
                "urgency_level": "routine",
                "technical_quality": "good",
                "model_version": "mock_dermoscopy_classifier_v1"
            }

        else:
            return {
                "image_type": detected_type,
                "predicted_class": "normal_study",
                "confidence": 0.80,
                "risk_score": 0.20,
                "clinical_findings": [
                    "No acute abnormalities identified",
                    "Within normal limits for study type"
                ],
                "recommendations": [
                    "Clinical correlation recommended",
                    "Follow-up as clinically indicated"
                ],
                "urgency_level": "routine",
                "technical_quality": "adequate",
                "model_version": f"mock_{detected_type}_classifier_v1"
            }

    def _generate_medical_prompt(self, image_type: str, image_data: ImageData) -> str:
        """Generate specialized prompt based on medical image type"""
        base_prompt = f"""Please analyze this {image_type} medical image and provide a comprehensive clinical assessment.

Image Details:
- Type: {image_type}
- Source: {image_data.image_path}
- Upload time: {image_data.uploaded_at}

Please provide your analysis in the following JSON format:
{{
    "predicted_class": "primary diagnosis or finding",
    "confidence": 0.0-1.0,
    "risk_score": 0.0-1.0,
    "clinical_findings": ["finding1", "finding2", ...],
    "recommendations": ["recommendation1", "recommendation2", ...],
    "urgency_level": "routine|high|critical",
    "technical_quality": "poor|adequate|good|excellent"
}}

Specific analysis for {image_type}:"""

        if image_type == MedicalImageType.RETINAL_SCAN:
            base_prompt += """
- Assess for diabetic retinopathy (no DR, mild, moderate, severe, proliferative)
- Look for macular edema, hemorrhages, exudates
- Evaluate optic disc and vessel abnormalities
- Consider referral urgency based on findings"""

        elif image_type == MedicalImageType.CHEST_XRAY:
            base_prompt += """
- Evaluate lung fields for infiltrates, nodules, pneumothorax
- Assess cardiac silhouette and mediastinum
- Check for pleural effusions or other abnormalities
- Consider acute vs chronic findings"""

        elif image_type == MedicalImageType.DERMATOLOGY:
            base_prompt += """
- Apply ABCDE criteria for pigmented lesions
- Assess symmetry, borders, color, diameter, evolution
- Consider malignant vs benign characteristics
- Evaluate need for biopsy or specialist referral"""

        elif image_type == MedicalImageType.ECG:
            base_prompt += """
- Analyze rhythm, rate, and intervals
- Look for ST-segment changes, arrhythmias
- Assess for signs of ischemia or infarction
- Consider urgency based on findings"""

        return base_prompt

    def _parse_medical_response(self, response: str, image_type: str) -> Dict[str, Any]:
        """Parse MedGemma response into structured format"""
        try:
            # Try to parse as JSON first
            if '{' in response and '}' in response:
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                json_str = response[json_start:json_end]
                parsed = json.loads(json_str)

                # Validate and normalize required fields
                result = {
                    "image_type": image_type,
                    "predicted_class": parsed.get("predicted_class", "unknown"),
                    "confidence": float(parsed.get("confidence", 0.7)),
                    "risk_score": float(parsed.get("risk_score", 0.5)),
                    "clinical_findings": parsed.get("clinical_findings", []),
                    "recommendations": parsed.get("recommendations", []),
                    "urgency_level": parsed.get("urgency_level", "routine"),
                    "technical_quality": parsed.get("technical_quality", "adequate"),
                    "raw_response": response
                }

                return result

        except Exception as e:
            logger.warning(f"Failed to parse JSON response: {e}")

        # Fallback parsing for non-JSON responses
        return self._fallback_parse_response(response, image_type)

    def _fallback_parse_response(self, response: str, image_type: str) -> Dict[str, Any]:
        """Fallback response parsing when JSON parsing fails"""
        # Simple keyword-based risk assessment
        risk_keywords = ["abnormal", "pathological", "suspicious", "severe", "critical", "urgent"]
        risk_score = 0.3  # Base risk

        response_lower = response.lower()
        for keyword in risk_keywords:
            if keyword in response_lower:
                risk_score += 0.15

        risk_score = min(risk_score, 1.0)

        # Determine urgency
        urgency = "routine"
        if risk_score > 0.7:
            urgency = "critical"
        elif risk_score > 0.4:
            urgency = "high"

        return {
            "image_type": image_type,
            "predicted_class": "analysis_completed",
            "confidence": 0.7,
            "risk_score": risk_score,
            "clinical_findings": [response[:200] + "..." if len(response) > 200 else response],
            "recommendations": ["Clinical correlation recommended", "Consider specialist consultation if indicated"],
            "urgency_level": urgency,
            "technical_quality": "adequate",
            "raw_response": response
        }

    def _fallback_analysis(self, image_type: str) -> Dict[str, Any]:
        """Provide fallback analysis when main processing fails"""
        return {
            "image_type": image_type,
            "predicted_class": "analysis_unavailable",
            "confidence": 0.5,
            "risk_score": 0.5,
            "clinical_findings": ["Image analysis could not be completed"],
            "recommendations": ["Manual review recommended", "Consider re-imaging if clinically indicated"],
            "urgency_level": "routine",
            "technical_quality": "unknown",
            "error": "Primary analysis method failed"
        }

    def _aggregate_image_results(self, image_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Aggregate results from multiple images into a comprehensive assessment"""
        successful_results = [r for r in image_results if r.get("success", False)]

        if not successful_results:
            return self._create_error_response("No images could be processed successfully")

        # Calculate aggregate metrics
        total_risk_score = sum(r.get("risk_score", 0.5) for r in successful_results)
        total_confidence = sum(r.get("confidence", 0.5) for r in successful_results)
        avg_risk_score = total_risk_score / len(successful_results)
        avg_confidence = total_confidence / len(successful_results)

        # Determine overall urgency (take highest)
        urgency_levels = [r.get("urgency_level", "routine") for r in successful_results]
        urgency_priority = {"critical": 3, "high": 2, "moderate": 1, "routine": 0}
        max_urgency = max(urgency_levels, key=lambda x: urgency_priority.get(x, 0))

        # Collect all findings and recommendations
        all_findings = []
        all_recommendations = []

        for result in successful_results:
            findings = result.get("clinical_findings", [])
            recommendations = result.get("recommendations", [])

            if isinstance(findings, list):
                all_findings.extend(findings)
            elif isinstance(findings, str):
                all_findings.append(findings)

            if isinstance(recommendations, list):
                all_recommendations.extend(recommendations)
            elif isinstance(recommendations, str):
                all_recommendations.append(recommendations)

        # Remove duplicates while preserving order
        unique_findings = list(dict.fromkeys(all_findings))
        unique_recommendations = list(dict.fromkeys(all_recommendations))

        # Create aggregated result
        return {
            "success": True,
            "images_analyzed": len(successful_results),
            "images_failed": len(image_results) - len(successful_results),
            "overall_risk_score": round(avg_risk_score, 3),
            "overall_confidence": round(avg_confidence, 3),
            "highest_urgency": max_urgency,
            "clinical_findings": unique_findings,
            "recommendations": unique_recommendations,
            "individual_results": image_results,
            "raw_output": {
                "risk_score": avg_risk_score,
                "confidence": avg_confidence,
                "predictions": [r.get("predicted_class", "unknown") for r in successful_results],
                "image_types": [r.get("image_type", "unknown") for r in successful_results]
            },
            "synthesized_output": self._generate_synthesized_output(successful_results, avg_risk_score, max_urgency)
        }

    def _generate_synthesized_output(self, results: List[Dict[str, Any]], avg_risk: float, urgency: str) -> str:
        """Generate human-readable summary of image analysis"""
        if not results:
            return "No images could be analyzed successfully."

        num_images = len(results)
        image_types = [r.get("image_type", "unknown") for r in results]
        unique_types = list(set(image_types))

        # Risk assessment
        if avg_risk >= 0.7:
            risk_desc = "high-risk findings requiring immediate attention"
        elif avg_risk >= 0.4:
            risk_desc = "moderate-risk findings requiring clinical correlation"
        else:
            risk_desc = "low-risk findings with routine follow-up recommended"

        # Image type description
        if len(unique_types) == 1:
            type_desc = f"{unique_types[0]} image analysis"
        else:
            type_desc = f"multi-modal image analysis ({', '.join(unique_types)})"

        summary = f"Analysis of {num_images} medical image(s) shows {risk_desc}. "
        summary += f"The {type_desc} indicates {urgency} priority level. "

        # Add specific findings if available
        significant_findings = []
        for result in results:
            findings = result.get("clinical_findings", [])
            if findings and len(findings) > 0:
                # Take first finding as most significant
                if isinstance(findings, list) and findings:
                    significant_findings.append(findings[0])
                elif isinstance(findings, str):
                    significant_findings.append(findings)

        if significant_findings:
            summary += f"Key findings include: {', '.join(significant_findings[:3])}."

        return summary

    def _generate_cache_key(self, image_data: ImageData, image_type: str) -> str:
        """Generate cache key for image analysis results"""
        # Use image path and type as cache key (simplified)
        return f"{image_type}_{hash(image_data.image_path)}"

    def _create_error_response(self, error_message: str) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "success": False,
            "error": error_message,
            "raw_output": {"error": error_message},
            "synthesized_output": f"Vision analysis failed: {error_message}",
            "confidence_score": 0.0,
            "processing_time_ms": 0
        }

    def _update_processing_stats(self, num_images: int, success: bool, processing_time: float):
        """Update internal processing statistics"""
        self.processing_stats["total_images_processed"] += num_images

        if success:
            self.processing_stats["successful_predictions"] += 1
        else:
            self.processing_stats["failed_predictions"] += 1

        # Update average processing time
        total_predictions = self.processing_stats["successful_predictions"] + self.processing_stats["failed_predictions"]
        if total_predictions > 0:
            current_avg = self.processing_stats["average_processing_time"]
            self.processing_stats["average_processing_time"] = (
                (current_avg * (total_predictions - 1) + processing_time) / total_predictions
            )

    async def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        stats = self.processing_stats.copy()
        stats.update({
            "cache_size": len(self.prediction_cache),
            "is_initialized": self.is_initialized,
            "mock_mode": self.config.mock_mode,
            "device": self.config.device
        })
        return stats

    async def clear_cache(self):
        """Clear prediction cache"""
        self.prediction_cache.clear()
        logger.info("Vision prediction cache cleared")

    async def cleanup(self):
        """Cleanup model resources and cache"""
        try:
            if self.model and self.model != "mock_model":
                del self.model
                self.model = None

            if self.processor and self.processor != "mock_processor":
                del self.processor
                self.processor = None

            # Clear cache
            self.prediction_cache.clear()

            # Clear GPU memory if available
            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            self.is_initialized = False
            logger.info("VisionBot cleanup completed")

        except Exception as e:
            logger.error(f"VisionBot cleanup error: {e}")


# Utility functions for integration with Chief-BOT

def create_vision_bot(config: Optional[VisionBotConfig] = None) -> VisionBot:
    """Factory function to create VisionBot instance"""
    return VisionBot(config)


async def analyze_medical_images(images: List[ImageData], config: Optional[VisionBotConfig] = None) -> Dict[str, Any]:
    """
    Standalone function to analyze medical images

    Args:
        images: List of ImageData objects to analyze
        config: Optional VisionBot configuration

    Returns:
        Analysis results compatible with Chief-BOT orchestrator
    """
    vision_bot = VisionBot(config)
    try:
        result = await vision_bot.process_images(images)
        return result
    finally:
        await vision_bot.cleanup()


# Export main classes and functions
__all__ = [
    "VisionBot",
    "VisionBotConfig",
    "ImageProcessor",
    "MedicalImageType",
    "create_vision_bot",
    "analyze_medical_images"
]
