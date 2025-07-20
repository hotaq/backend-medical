"""
Base Medical Model Class

This module provides the base class for all medical prediction models.
It includes common functionality for data validation, preprocessing, and result formatting.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class MedicalModelResult:
    """Container for medical model prediction results"""

    def __init__(
        self,
        risk_score: float,
        risk_category: str,
        confidence: float,
        model_name: str,
        features_used: List[str],
        raw_predictions: Dict[str, Any],
        recommendations: List[str],
        warnings: List[str] = None
    ):
        self.risk_score = risk_score
        self.risk_category = risk_category
        self.confidence = confidence
        self.model_name = model_name
        self.features_used = features_used
        self.raw_predictions = raw_predictions
        self.recommendations = recommendations
        self.warnings = warnings or []
        self.prediction_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format"""
        return {
            "risk_score": self.risk_score,
            "risk_category": self.risk_category,
            "confidence": self.confidence,
            "model_name": self.model_name,
            "features_used": self.features_used,
            "raw_predictions": self.raw_predictions,
            "recommendations": self.recommendations,
            "warnings": self.warnings,
            "prediction_time": self.prediction_time.isoformat()
        }


class BaseMedicalModel(ABC):
    """
    Abstract base class for medical prediction models.

    All medical models should inherit from this class and implement
    the required abstract methods.
    """

    def __init__(self, model_name: str):
        self.model_name = model_name
        self.model: Optional[BaseEstimator] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.feature_ranges: Dict[str, Tuple[float, float]] = {}
        self.reference_ranges: Dict[str, Dict[str, float]] = {}
        self.is_trained = False

    @abstractmethod
    def get_required_features(self) -> List[str]:
        """Return list of required feature names for this model"""
        pass

    @abstractmethod
    def get_optional_features(self) -> List[str]:
        """Return list of optional feature names for this model"""
        pass

    @abstractmethod
    def _train_model(self, X: np.ndarray, y: np.ndarray) -> BaseEstimator:
        """Train the underlying ML model. Should return trained model."""
        pass

    @abstractmethod
    def _interpret_risk_score(self, risk_score: float) -> str:
        """Convert numeric risk score to categorical risk level"""
        pass

    @abstractmethod
    def _generate_recommendations(self, risk_score: float, features: Dict[str, Any]) -> List[str]:
        """Generate medical recommendations based on prediction"""
        pass

    def can_predict(self, structured_data: List[Dict[str, Any]]) -> bool:
        """
        Check if the model can make predictions with the given data.

        Args:
            structured_data: List of structured data dictionaries

        Returns:
            bool: True if model can predict, False otherwise
        """
        available_features = self._extract_available_features(structured_data)
        required_features = self.get_required_features()

        # Check if all required features are available
        for feature in required_features:
            if feature not in available_features:
                return False

        return True

    def extract_features(self, structured_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features from structured medical data.

        Args:
            structured_data: List of structured data from TriageCase

        Returns:
            Dict containing extracted features
        """
        features = {}

        for data_item in structured_data:
            data = data_item.get('data', {})
            data_type = data_item.get('data_type', '')

            # Extract relevant features based on data type and content
            for key, value in data.items():
                if self._is_relevant_feature(key, data_type):
                    # Normalize feature names
                    normalized_key = self._normalize_feature_name(key)
                    if normalized_key in (self.get_required_features() + self.get_optional_features()):
                        features[normalized_key] = self._normalize_value(normalized_key, value)

        return features

    def predict(self, structured_data: List[Dict[str, Any]]) -> MedicalModelResult:
        """
        Make prediction on structured medical data.

        Args:
            structured_data: List of structured data from TriageCase

        Returns:
            MedicalModelResult containing prediction results
        """
        try:
            # Extract features
            features = self.extract_features(structured_data)

            # Validate required features
            missing_features = self._validate_features(features)
            if missing_features:
                return self._create_error_result(
                    f"Missing required features: {missing_features}"
                )

            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)

            # Make prediction
            if not self.is_trained:
                self._initialize_default_model()

            risk_score = self._predict_risk_score(feature_vector)
            confidence = self._calculate_confidence(feature_vector, features)

            # Interpret results
            risk_category = self._interpret_risk_score(risk_score)
            recommendations = self._generate_recommendations(risk_score, features)
            warnings = self._generate_warnings(features)

            return MedicalModelResult(
                risk_score=risk_score,
                risk_category=risk_category,
                confidence=confidence,
                model_name=self.model_name,
                features_used=list(features.keys()),
                raw_predictions={
                    "probability": risk_score,
                    "features": features
                },
                recommendations=recommendations,
                warnings=warnings
            )

        except Exception as e:
            logger.error(f"Error in {self.model_name} prediction: {str(e)}")
            return self._create_error_result(str(e))

    def _extract_available_features(self, structured_data: List[Dict[str, Any]]) -> List[str]:
        """Extract list of available feature names from structured data"""
        available = []
        for data_item in structured_data:
            data = data_item.get('data', {})
            for key in data.keys():
                normalized_key = self._normalize_feature_name(key)
                if normalized_key not in available:
                    available.append(normalized_key)
        return available

    def _is_relevant_feature(self, feature_name: str, data_type: str) -> bool:
        """Check if a feature is relevant for this model"""
        normalized_name = self._normalize_feature_name(feature_name)
        all_features = self.get_required_features() + self.get_optional_features()
        return normalized_name in all_features

    def _normalize_feature_name(self, feature_name: str) -> str:
        """Normalize feature names to standard format"""
        # Convert to lowercase and replace common variations
        normalized = feature_name.lower().strip()

        # Common normalizations
        normalization_map = {
            'fbs': 'fasting_glucose',
            'glucose_fasting': 'fasting_glucose',
            'blood_glucose': 'fasting_glucose',
            'hba1c': 'hemoglobin_a1c',
            'hgba1c': 'hemoglobin_a1c',
            'cholesterol_total': 'total_cholesterol',
            'chol': 'total_cholesterol',
            'ldl': 'ldl_cholesterol',
            'hdl': 'hdl_cholesterol',
            'trig': 'triglycerides',
            'triglyceride': 'triglycerides',
            'systolic_bp': 'systolic_blood_pressure',
            'diastolic_bp': 'diastolic_blood_pressure',
            'bp_systolic': 'systolic_blood_pressure',
            'bp_diastolic': 'diastolic_blood_pressure',
            'creatinine_serum': 'creatinine',
            'bun': 'blood_urea_nitrogen',
            'urea': 'blood_urea_nitrogen'
        }

        return normalization_map.get(normalized, normalized)

    def _normalize_value(self, feature_name: str, value: Any) -> float:
        """Normalize feature values to standard units/ranges"""
        try:
            numeric_value = float(value)

            # Apply unit conversions if needed
            if feature_name == 'fasting_glucose':
                # Assume mg/dL, convert mmol/L if value is too small
                if numeric_value < 20:  # Likely mmol/L
                    numeric_value = numeric_value * 18.0

            return numeric_value
        except (ValueError, TypeError):
            logger.warning(f"Could not convert value {value} for feature {feature_name}")
            return 0.0

    def _validate_features(self, features: Dict[str, Any]) -> List[str]:
        """Validate that required features are present"""
        required = self.get_required_features()
        missing = [f for f in required if f not in features]
        return missing

    def _prepare_feature_vector(self, features: Dict[str, Any]) -> np.ndarray:
        """Prepare feature vector for model prediction"""
        all_features = self.get_required_features() + self.get_optional_features()

        # Create feature vector with default values for missing optional features
        feature_vector = []
        for feature in all_features:
            if feature in features:
                feature_vector.append(features[feature])
            else:
                # Use default value for missing optional features
                default_value = self._get_default_value(feature)
                feature_vector.append(default_value)

        return np.array(feature_vector).reshape(1, -1)

    def _get_default_value(self, feature_name: str) -> float:
        """Get default value for missing optional features"""
        # Common defaults for medical features
        defaults = {
            'age': 40.0,
            'bmi': 25.0,
            'systolic_blood_pressure': 120.0,
            'diastolic_blood_pressure': 80.0,
            'total_cholesterol': 200.0,
            'hdl_cholesterol': 50.0,
            'ldl_cholesterol': 100.0,
            'triglycerides': 150.0
        }
        return defaults.get(feature_name, 0.0)

    def _initialize_default_model(self):
        """Initialize a default model if none is trained"""
        # Create a simple default model for demonstration
        # In practice, this would load pre-trained weights
        self.model = RandomForestClassifier(n_estimators=50, random_state=42)

        # Generate synthetic training data for demonstration
        n_samples = 1000
        n_features = len(self.get_required_features() + self.get_optional_features())

        X = np.random.rand(n_samples, n_features)
        y = np.random.randint(0, 2, n_samples)  # Binary classification

        self.model.fit(X, y)
        self.is_trained = True

        logger.info(f"Initialized default model for {self.model_name}")

    def _predict_risk_score(self, feature_vector: np.ndarray) -> float:
        """Predict risk score using the trained model"""
        if hasattr(self.model, 'predict_proba'):
            # Get probability of positive class
            probabilities = self.model.predict_proba(feature_vector)
            return float(probabilities[0][1])  # Probability of risk class
        else:
            # For models without predict_proba, use decision function
            decision = self.model.decision_function(feature_vector)
            # Convert to probability-like score
            return float(1 / (1 + np.exp(-decision[0])))

    def _calculate_confidence(self, feature_vector: np.ndarray, features: Dict[str, Any]) -> float:
        """Calculate confidence score for the prediction"""
        base_confidence = 0.7

        # Increase confidence based on number of features available
        required_features = self.get_required_features()
        available_required = sum(1 for f in required_features if f in features)
        feature_completeness = available_required / len(required_features)

        # Adjust confidence based on feature quality
        confidence = base_confidence + (feature_completeness * 0.2)

        return min(confidence, 0.95)  # Cap at 95%

    def _generate_warnings(self, features: Dict[str, Any]) -> List[str]:
        """Generate warnings based on feature values"""
        warnings = []

        # Check for extreme values
        for feature, value in features.items():
            if feature in self.feature_ranges:
                min_val, max_val = self.feature_ranges[feature]
                if value < min_val or value > max_val:
                    warnings.append(f"Unusual {feature} value: {value}")

        return warnings

    def _create_error_result(self, error_message: str) -> MedicalModelResult:
        """Create an error result when prediction fails"""
        return MedicalModelResult(
            risk_score=0.0,
            risk_category="unknown",
            confidence=0.0,
            model_name=self.model_name,
            features_used=[],
            raw_predictions={"error": error_message},
            recommendations=["Unable to make prediction - please consult healthcare provider"],
            warnings=[f"Prediction error: {error_message}"]
        )
