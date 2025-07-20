"""
TextBOT Agent for Medical Data Analysis

This module implements the TextBOT agent that processes structured medical data
using multiple scikit-learn models to provide comprehensive health risk assessments.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..models.triage_case import StructuredData, StructuredDataType
from .medical_models import (
    DiabetesRiskModel,
    HeartDiseaseRiskModel,
    HypertensionRiskModel,
    KidneyDiseaseRiskModel,
    GeneralHealthRiskModel
)

logger = logging.getLogger(__name__)


class ModelSelectionResult:
    """Container for model selection results"""

    def __init__(self, selected_models: List[str], rationale: str, confidence: float):
        self.selected_models = selected_models
        self.rationale = rationale
        self.confidence = confidence


class TextBOTResult:
    """Container for TextBOT processing results"""

    def __init__(
        self,
        success: bool,
        overall_risk_score: float,
        risk_category: str,
        model_results: Dict[str, Any],
        recommendations: List[str],
        warnings: List[str],
        processing_time_ms: int,
        models_used: List[str],
        confidence_score: float,
        raw_output: Dict[str, Any]
    ):
        self.success = success
        self.overall_risk_score = overall_risk_score
        self.risk_category = risk_category
        self.model_results = model_results
        self.recommendations = recommendations
        self.warnings = warnings
        self.processing_time_ms = processing_time_ms
        self.models_used = models_used
        self.confidence_score = confidence_score
        self.raw_output = raw_output
        self.processed_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format"""
        return {
            "success": self.success,
            "overall_risk_score": self.overall_risk_score,
            "risk_category": self.risk_category,
            "model_results": self.model_results,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "processing_time_ms": self.processing_time_ms,
            "models_used": self.models_used,
            "confidence_score": self.confidence_score,
            "raw_output": self.raw_output,
            "processed_at": self.processed_at.isoformat()
        }


class TextBOT:
    """
    TextBOT agent for processing structured medical data.

    This agent analyzes structured medical data and routes it to appropriate
    medical prediction models (diabetes, heart disease, hypertension, etc.)
    to provide comprehensive health risk assessments.
    """

    def __init__(self):
        self.agent_name = "TextBOT Medical Data Analyzer"
        self.version = "1.0.0"

        # Initialize medical models
        self.models = {
            'diabetes': DiabetesRiskModel(),
            'heart_disease': HeartDiseaseRiskModel(),
            'hypertension': HypertensionRiskModel(),
            'kidney_disease': KidneyDiseaseRiskModel(),
            'general_health': GeneralHealthRiskModel()
        }

        # Model selection criteria based on available data
        self.model_selection_criteria = {
            'diabetes': {
                'required_indicators': ['fasting_glucose', 'glucose', 'hemoglobin_a1c', 'hba1c'],
                'data_types': [StructuredDataType.BLOOD_TEST, StructuredDataType.LAB_RESULTS],
                'priority': 1
            },
            'heart_disease': {
                'required_indicators': ['cholesterol', 'total_cholesterol', 'ldl_cholesterol', 'blood_pressure'],
                'data_types': [StructuredDataType.BLOOD_TEST, StructuredDataType.VITAL_SIGNS],
                'priority': 1
            },
            'hypertension': {
                'required_indicators': ['blood_pressure', 'systolic', 'diastolic', 'bp'],
                'data_types': [StructuredDataType.VITAL_SIGNS],
                'priority': 2
            },
            'kidney_disease': {
                'required_indicators': ['creatinine', 'bun', 'urea', 'protein', 'gfr'],
                'data_types': [StructuredDataType.BLOOD_TEST, StructuredDataType.LAB_RESULTS],
                'priority': 2
            },
            'general_health': {
                'required_indicators': ['age', 'bmi', 'weight', 'height'],
                'data_types': [StructuredDataType.VITAL_SIGNS, StructuredDataType.MEDICAL_HISTORY],
                'priority': 3
            }
        }

        logger.info(f"TextBOT initialized with {len(self.models)} medical models")

    async def process_structured_data(self, structured_data: List[StructuredData]) -> TextBOTResult:
        """
        Process structured medical data through appropriate models.

        Args:
            structured_data: List of StructuredData objects from TriageCase

        Returns:
            TextBOTResult containing comprehensive analysis results
        """
        start_time = time.time()

        try:
            # Convert StructuredData objects to dictionaries
            data_dicts = self._convert_structured_data(structured_data)

            # Select appropriate models
            model_selection = self._select_models(data_dicts)

            # Run selected models
            model_results = await self._run_models(model_selection.selected_models, data_dicts)

            # Synthesize results
            synthesis = self._synthesize_results(model_results)

            # Calculate processing time
            processing_time = int((time.time() - start_time) * 1000)

            # Create result object
            result = TextBOTResult(
                success=True,
                overall_risk_score=synthesis['overall_risk_score'],
                risk_category=synthesis['risk_category'],
                model_results=synthesis['model_results'],
                recommendations=synthesis['recommendations'],
                warnings=synthesis['warnings'],
                processing_time_ms=processing_time,
                models_used=model_selection.selected_models,
                confidence_score=synthesis['confidence_score'],
                raw_output={
                    'data_summary': self._get_data_summary(data_dicts),
                    'model_selection_rationale': model_selection.rationale,
                    'individual_predictions': model_results
                }
            )

            logger.info(f"TextBOT processing completed successfully in {processing_time}ms")
            return result

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"TextBOT processing failed: {str(e)}")

            return TextBOTResult(
                success=False,
                overall_risk_score=0.0,
                risk_category="error",
                model_results={},
                recommendations=["Error in medical data analysis - please consult healthcare provider"],
                warnings=[f"Processing error: {str(e)}"],
                processing_time_ms=processing_time,
                models_used=[],
                confidence_score=0.0,
                raw_output={"error": str(e)}
            )

    def _convert_structured_data(self, structured_data: List[StructuredData]) -> List[Dict[str, Any]]:
        """Convert StructuredData objects to dictionary format"""
        data_dicts = []

        for data_item in structured_data:
            # Handle both StructuredData objects and plain dictionaries
            if hasattr(data_item, 'data_type'):
                # StructuredData object
                data_dict = {
                    'data_type': data_item.data_type,
                    'data': data_item.data,
                    'units': data_item.units or {},
                    'reference_ranges': data_item.reference_ranges or {},
                    'test_date': data_item.test_date
                }
            else:
                # Plain dictionary (for backward compatibility)
                data_dict = data_item

            data_dicts.append(data_dict)

        return data_dicts

    def _select_models(self, data_dicts: List[Dict[str, Any]]) -> ModelSelectionResult:
        """
        Select appropriate medical models based on available data.

        Args:
            data_dicts: List of structured data dictionaries

        Returns:
            ModelSelectionResult with selected models and rationale
        """
        available_features = self._extract_available_features(data_dicts)
        available_data_types = self._extract_data_types(data_dicts)

        selected_models = []
        selection_scores = {}

        # Evaluate each model for selection
        for model_name, criteria in self.model_selection_criteria.items():
            score = 0

            # Check for required indicators
            indicator_matches = 0
            for indicator in criteria['required_indicators']:
                if any(indicator.lower() in feature.lower() for feature in available_features):
                    indicator_matches += 1

            if indicator_matches > 0:
                score += indicator_matches / len(criteria['required_indicators'])

                # Check data type compatibility
                for data_type in criteria['data_types']:
                    if data_type in available_data_types:
                        score += 0.5

                # Apply priority weighting
                score = score / criteria['priority']

                selection_scores[model_name] = score

        # Select models with score above threshold
        threshold = 0.3
        selected_models = [
            model for model, score in selection_scores.items()
            if score >= threshold
        ]

        # Always include general health if we have basic data
        if ('age' in available_features or 'bmi' in available_features) and 'general_health' not in selected_models:
            selected_models.append('general_health')

        # Ensure at least one model is selected
        if not selected_models:
            selected_models = ['general_health']

        # Generate rationale
        rationale = self._generate_selection_rationale(selected_models, selection_scores, available_features)

        return ModelSelectionResult(
            selected_models=selected_models,
            rationale=rationale,
            confidence=min(sum(selection_scores.values()) / len(selection_scores), 1.0) if selection_scores else 0.5
        )

    def _extract_available_features(self, data_dicts: List[Dict[str, Any]]) -> List[str]:
        """Extract list of available feature names from data"""
        features = set()

        for data_dict in data_dicts:
            data = data_dict.get('data', {})
            for key in data.keys():
                features.add(key.lower())

        return list(features)

    def _extract_data_types(self, data_dicts: List[Dict[str, Any]]) -> List[StructuredDataType]:
        """Extract list of available data types"""
        data_types = set()

        for data_dict in data_dicts:
            data_type = data_dict.get('data_type')
            if data_type:
                if isinstance(data_type, str):
                    # Convert string to enum if needed
                    try:
                        data_types.add(StructuredDataType(data_type))
                    except ValueError:
                        pass
                else:
                    data_types.add(data_type)

        return list(data_types)

    def _generate_selection_rationale(
        self,
        selected_models: List[str],
        selection_scores: Dict[str, float],
        available_features: List[str]
    ) -> str:
        """Generate human-readable rationale for model selection"""
        rationale_parts = []

        rationale_parts.append(f"Selected {len(selected_models)} models based on available data:")

        for model in selected_models:
            score = selection_scores.get(model, 0)
            rationale_parts.append(f"- {model.replace('_', ' ').title()}: relevance score {score:.2f}")

        rationale_parts.append(f"Available features: {', '.join(available_features[:10])}")
        if len(available_features) > 10:
            rationale_parts.append(f"... and {len(available_features) - 10} more")

        return " ".join(rationale_parts)

    async def _run_models(self, model_names: List[str], data_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run selected medical models on the data.

        Args:
            model_names: List of model names to run
            data_dicts: Structured data dictionaries

        Returns:
            Dictionary of model results
        """
        model_results = {}

        # Run models concurrently
        tasks = []
        for model_name in model_names:
            if model_name in self.models:
                task = self._run_single_model(model_name, self.models[model_name], data_dicts)
                tasks.append((model_name, task))

        # Wait for all models to complete
        for model_name, task in tasks:
            try:
                result = await task
                model_results[model_name] = result
            except Exception as e:
                logger.error(f"Error running {model_name} model: {str(e)}")
                model_results[model_name] = {
                    'error': str(e),
                    'success': False
                }

        return model_results

    async def _run_single_model(self, model_name: str, model, data_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run a single medical model asynchronously"""
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()

        def run_model():
            try:
                if model.can_predict(data_dicts):
                    result = model.predict(data_dicts)
                    return {
                        'success': True,
                        'result': result.to_dict(),
                        'model_name': model_name
                    }
                else:
                    return {
                        'success': False,
                        'error': 'Insufficient data for prediction',
                        'model_name': model_name
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'model_name': model_name
                }

        return await loop.run_in_executor(None, run_model)

    def _synthesize_results(self, model_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Synthesize results from multiple models into a unified assessment.

        Args:
            model_results: Dictionary of results from each model

        Returns:
            Dictionary with synthesized results
        """
        successful_results = {
            name: result for name, result in model_results.items()
            if result.get('success', False)
        }

        if not successful_results:
            return {
                'overall_risk_score': 0.0,
                'risk_category': 'insufficient_data',
                'model_results': model_results,
                'recommendations': ['Insufficient data for medical analysis'],
                'warnings': ['Unable to complete medical analysis'],
                'confidence_score': 0.0
            }

        # Calculate weighted overall risk score
        risk_scores = []
        confidence_scores = []
        all_recommendations = []
        all_warnings = []

        # Model importance weights
        model_weights = {
            'diabetes': 0.25,
            'heart_disease': 0.25,
            'hypertension': 0.20,
            'kidney_disease': 0.15,
            'general_health': 0.15
        }

        total_weight = 0
        weighted_risk = 0

        for model_name, result in successful_results.items():
            if 'result' in result:
                model_result = result['result']
                risk_score = model_result.get('risk_score', 0)
                confidence = model_result.get('confidence', 0)

                weight = model_weights.get(model_name, 0.1)
                weighted_risk += risk_score * weight
                total_weight += weight

                risk_scores.append(risk_score)
                confidence_scores.append(confidence)
                all_recommendations.extend(model_result.get('recommendations', []))
                all_warnings.extend(model_result.get('warnings', []))

        # Calculate final scores
        overall_risk = weighted_risk / total_weight if total_weight > 0 else 0
        overall_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0

        # Determine overall risk category
        overall_category = self._determine_overall_risk_category(overall_risk, successful_results)

        # Deduplicate and prioritize recommendations
        unique_recommendations = self._prioritize_recommendations(all_recommendations)
        unique_warnings = list(set(all_warnings))

        return {
            'overall_risk_score': round(overall_risk, 3),
            'risk_category': overall_category,
            'model_results': {name: result.get('result', {}) for name, result in successful_results.items()},
            'recommendations': unique_recommendations[:15],  # Limit to top 15
            'warnings': unique_warnings,
            'confidence_score': round(overall_confidence, 3)
        }

    def _determine_overall_risk_category(self, risk_score: float, results: Dict[str, Any]) -> str:
        """Determine overall risk category from score and individual results"""
        # Check for any very high risk findings
        for result in results.values():
            if 'result' in result:
                category = result['result'].get('risk_category', '').lower()
                if 'very_high' in category or 'crisis' in category:
                    return 'very_high'

        # Use standard thresholds
        if risk_score >= 0.75:
            return 'very_high'
        elif risk_score >= 0.5:
            return 'high'
        elif risk_score >= 0.3:
            return 'moderate'
        elif risk_score >= 0.15:
            return 'low_moderate'
        else:
            return 'low'

    def _prioritize_recommendations(self, recommendations: List[str]) -> List[str]:
        """Prioritize and deduplicate recommendations"""
        # Priority keywords for urgent recommendations
        urgent_keywords = [
            'immediate', 'urgent', 'emergency', 'crisis', 'consultation required',
            'medical attention', 'nephrology', 'cardiology', 'endocrinology'
        ]

        # Deduplicate while preserving order
        seen = set()
        unique_recs = []
        for rec in recommendations:
            if rec not in seen:
                seen.add(rec)
                unique_recs.append(rec)

        # Sort by priority (urgent first)
        def priority_score(rec):
            score = 0
            rec_lower = rec.lower()
            for keyword in urgent_keywords:
                if keyword in rec_lower:
                    score += 10
            return score

        return sorted(unique_recs, key=priority_score, reverse=True)

    def _get_data_summary(self, data_dicts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of processed data"""
        total_features = 0
        data_types = set()
        feature_categories = {}

        for data_dict in data_dicts:
            data = data_dict.get('data', {})
            total_features += len(data)

            data_type = data_dict.get('data_type', 'unknown')
            data_types.add(str(data_type))

            # Categorize features
            for feature in data.keys():
                category = self._categorize_feature(feature)
                if category not in feature_categories:
                    feature_categories[category] = 0
                feature_categories[category] += 1

        return {
            'total_data_items': len(data_dicts),
            'total_features': total_features,
            'data_types': list(data_types),
            'feature_categories': feature_categories
        }

    def _categorize_feature(self, feature_name: str) -> str:
        """Categorize a feature into a medical category"""
        feature_lower = feature_name.lower()

        if any(term in feature_lower for term in ['glucose', 'hba1c', 'diabetes']):
            return 'metabolic'
        elif any(term in feature_lower for term in ['cholesterol', 'ldl', 'hdl', 'triglycerides']):
            return 'lipid_profile'
        elif any(term in feature_lower for term in ['pressure', 'systolic', 'diastolic', 'heart_rate']):
            return 'cardiovascular'
        elif any(term in feature_lower for term in ['creatinine', 'bun', 'gfr', 'protein']):
            return 'kidney_function'
        elif any(term in feature_lower for term in ['age', 'bmi', 'weight', 'height']):
            return 'demographics'
        else:
            return 'other'

    def get_model_info(self) -> Dict[str, Any]:
        """Get information about available models and their capabilities"""
        model_info = {}

        for name, model in self.models.items():
            model_info[name] = {
                'model_name': model.model_name,
                'required_features': model.get_required_features(),
                'optional_features': model.get_optional_features(),
                'is_trained': model.is_trained
            }

        return {
            'agent_name': self.agent_name,
            'version': self.version,
            'available_models': model_info,
            'selection_criteria': self.model_selection_criteria
        }
