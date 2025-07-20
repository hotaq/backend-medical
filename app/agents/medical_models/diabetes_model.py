"""
Diabetes Risk Prediction Model

This module implements a scikit-learn based model for predicting diabetes risk
from structured medical data including glucose levels, HbA1c, BMI, and other factors.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import logging

from .base_medical_model import BaseMedicalModel

logger = logging.getLogger(__name__)


class DiabetesRiskModel(BaseMedicalModel):
    """
    Diabetes risk prediction model using structured medical data.

    This model predicts the risk of diabetes based on:
    - Fasting glucose levels
    - HbA1c (Hemoglobin A1c)
    - BMI (Body Mass Index)
    - Age
    - Family history (optional)
    - Blood pressure (optional)
    """

    def __init__(self):
        super().__init__("Diabetes Risk Predictor")

        # Define feature ranges for validation
        self.feature_ranges = {
            'fasting_glucose': (70, 400),      # mg/dL
            'hemoglobin_a1c': (4.0, 15.0),    # %
            'bmi': (15.0, 50.0),              # kg/m²
            'age': (18, 100),                 # years
            'systolic_blood_pressure': (80, 200),  # mmHg
            'diastolic_blood_pressure': (50, 120), # mmHg
        }

        # Define reference ranges for interpretation
        self.reference_ranges = {
            'fasting_glucose': {
                'normal': (70, 99),
                'prediabetes': (100, 125),
                'diabetes': (126, 400)
            },
            'hemoglobin_a1c': {
                'normal': (4.0, 5.6),
                'prediabetes': (5.7, 6.4),
                'diabetes': (6.5, 15.0)
            },
            'bmi': {
                'underweight': (0, 18.5),
                'normal': (18.5, 24.9),
                'overweight': (25.0, 29.9),
                'obese': (30.0, 50.0)
            }
        }

    def get_required_features(self) -> List[str]:
        """Return list of required features for diabetes prediction"""
        return [
            'fasting_glucose',
            'age'
        ]

    def get_optional_features(self) -> List[str]:
        """Return list of optional features that improve prediction accuracy"""
        return [
            'hemoglobin_a1c',
            'bmi',
            'systolic_blood_pressure',
            'diastolic_blood_pressure',
            'family_history_diabetes',
            'physical_activity_level'
        ]

    def _train_model(self, X: np.ndarray, y: np.ndarray):
        """Train the diabetes risk prediction model"""
        # Use Random Forest for better interpretability and performance
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'  # Handle imbalanced data
        )

        model.fit(X, y)
        return model

    def _interpret_risk_score(self, risk_score: float) -> str:
        """Convert numeric risk score to categorical diabetes risk level"""
        if risk_score >= 0.7:
            return "high"
        elif risk_score >= 0.4:
            return "moderate"
        elif risk_score >= 0.2:
            return "low_moderate"
        else:
            return "low"

    def _generate_recommendations(self, risk_score: float, features: Dict[str, Any]) -> List[str]:
        """Generate diabetes-specific recommendations based on prediction"""
        recommendations = []

        # Get feature values
        glucose = features.get('fasting_glucose', 0)
        hba1c = features.get('hemoglobin_a1c', 0)
        bmi = features.get('bmi', 0)
        age = features.get('age', 0)

        # Risk-based recommendations
        if risk_score >= 0.7:
            recommendations.extend([
                "High diabetes risk detected - immediate medical consultation recommended",
                "Consider comprehensive diabetes screening including OGTT",
                "Urgent lifestyle modifications required"
            ])
        elif risk_score >= 0.4:
            recommendations.extend([
                "Moderate diabetes risk - schedule follow-up with healthcare provider",
                "Consider diabetes prevention program",
                "Monitor blood glucose levels regularly"
            ])
        else:
            recommendations.extend([
                "Continue current preventive measures",
                "Annual diabetes screening recommended"
            ])

        # Glucose-specific recommendations
        if glucose >= 126:
            recommendations.append("Fasting glucose indicates diabetes - immediate medical attention required")
        elif glucose >= 100:
            recommendations.append("Elevated fasting glucose - prediabetes screening recommended")

        # HbA1c-specific recommendations
        if hba1c >= 6.5:
            recommendations.append("HbA1c indicates diabetes - endocrinology consultation recommended")
        elif hba1c >= 5.7:
            recommendations.append("Elevated HbA1c suggests prediabetes - lifestyle interventions recommended")

        # BMI-specific recommendations
        if bmi >= 30:
            recommendations.extend([
                "Obesity detected - weight management program recommended",
                "Consider nutrition counseling and structured exercise program"
            ])
        elif bmi >= 25:
            recommendations.append("Overweight - gradual weight reduction recommended")

        # Age-specific recommendations
        if age >= 45:
            recommendations.append("Age-related diabetes risk - annual screening recommended")

        # General lifestyle recommendations
        recommendations.extend([
            "Maintain healthy diet with controlled carbohydrate intake",
            "Regular physical activity (150 minutes/week moderate exercise)",
            "Monitor weight and blood pressure regularly"
        ])

        return recommendations

    def _initialize_default_model(self):
        """Initialize a trained diabetes model with realistic parameters"""
        # Create a more sophisticated default model
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )

        # Generate synthetic training data based on medical knowledge
        n_samples = 2000
        features = []
        labels = []

        for _ in range(n_samples):
            # Generate realistic medical data
            age = np.random.normal(50, 15)
            age = max(18, min(100, age))

            # Correlate glucose with diabetes risk
            base_glucose = np.random.normal(95, 20)

            # Generate BMI
            bmi = np.random.normal(27, 5)
            bmi = max(18, min(45, bmi))

            # Generate HbA1c
            base_hba1c = np.random.normal(5.5, 0.8)

            # Create risk factors
            age_risk = (age - 40) / 60  # Age risk factor
            bmi_risk = max(0, (bmi - 25) / 15)  # BMI risk factor

            # Determine diabetes status with realistic probabilities
            diabetes_risk = 0.1 + age_risk * 0.3 + bmi_risk * 0.4

            if np.random.random() < diabetes_risk:
                # Diabetic case
                glucose = base_glucose + np.random.normal(40, 20)
                hba1c = base_hba1c + np.random.normal(1.5, 0.5)
                label = 1
            else:
                # Non-diabetic case
                glucose = base_glucose + np.random.normal(0, 10)
                hba1c = base_hba1c + np.random.normal(0, 0.3)
                label = 0

            # Ensure realistic ranges
            glucose = max(70, min(400, glucose))
            hba1c = max(4.0, min(15.0, hba1c))

            # Optional features (with some missing values)
            systolic_bp = np.random.normal(125, 15) if np.random.random() > 0.2 else 120
            diastolic_bp = np.random.normal(80, 10) if np.random.random() > 0.2 else 80
            family_history = 1 if np.random.random() < 0.3 else 0
            activity_level = np.random.randint(1, 4)  # 1=low, 2=moderate, 3=high

            features.append([
                glucose,
                age,
                hba1c,
                bmi,
                systolic_bp,
                diastolic_bp,
                family_history,
                activity_level
            ])
            labels.append(label)

        X = np.array(features)
        y = np.array(labels)

        # Train the model
        self.model.fit(X, y)
        self.is_trained = True

        # Calculate and log feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_names = self.get_required_features() + self.get_optional_features()
            importance_dict = dict(zip(feature_names, self.model.feature_importances_))
            logger.info(f"Diabetes model feature importance: {importance_dict}")

        logger.info("Diabetes risk model initialized with synthetic training data")

    def get_risk_interpretation(self, features: Dict[str, Any]) -> Dict[str, str]:
        """
        Get detailed interpretation of risk factors for diabetes.

        Args:
            features: Dictionary of extracted features

        Returns:
            Dictionary with interpretations for each risk factor
        """
        interpretations = {}

        # Glucose interpretation
        glucose = features.get('fasting_glucose', 0)
        if glucose >= 126:
            interpretations['glucose'] = "Diabetic range (≥126 mg/dL)"
        elif glucose >= 100:
            interpretations['glucose'] = "Prediabetic range (100-125 mg/dL)"
        else:
            interpretations['glucose'] = "Normal range (<100 mg/dL)"

        # HbA1c interpretation
        hba1c = features.get('hemoglobin_a1c', 0)
        if hba1c >= 6.5:
            interpretations['hba1c'] = "Diabetic range (≥6.5%)"
        elif hba1c >= 5.7:
            interpretations['hba1c'] = "Prediabetic range (5.7-6.4%)"
        elif hba1c > 0:
            interpretations['hba1c'] = "Normal range (<5.7%)"

        # BMI interpretation
        bmi = features.get('bmi', 0)
        if bmi >= 30:
            interpretations['bmi'] = "Obese (≥30 kg/m²) - high diabetes risk"
        elif bmi >= 25:
            interpretations['bmi'] = "Overweight (25-29.9 kg/m²) - increased risk"
        elif bmi > 0:
            interpretations['bmi'] = "Normal weight (<25 kg/m²)"

        # Age interpretation
        age = features.get('age', 0)
        if age >= 45:
            interpretations['age'] = "Age ≥45 years - increased diabetes risk"
        else:
            interpretations['age'] = "Age <45 years - lower age-related risk"

        return interpretations

    def get_prevention_advice(self, risk_score: float, features: Dict[str, Any]) -> List[str]:
        """
        Generate personalized diabetes prevention advice.

        Args:
            risk_score: Predicted diabetes risk score
            features: Dictionary of extracted features

        Returns:
            List of personalized prevention recommendations
        """
        advice = []

        glucose = features.get('fasting_glucose', 0)
        bmi = features.get('bmi', 0)
        age = features.get('age', 0)

        # Weight management advice
        if bmi >= 30:
            advice.extend([
                "Target 7-10% weight loss through caloric restriction",
                "Consider medically supervised weight loss program",
                "Focus on sustainable dietary changes"
            ])
        elif bmi >= 25:
            advice.extend([
                "Target 5-7% weight loss through lifestyle modifications",
                "Reduce portion sizes and increase fiber intake"
            ])

        # Exercise recommendations
        if risk_score >= 0.4:
            advice.extend([
                "Aim for 150+ minutes of moderate aerobic activity per week",
                "Include resistance training 2-3 times per week",
                "Consider diabetes prevention program enrollment"
            ])
        else:
            advice.append("Maintain regular physical activity (150 minutes/week)")

        # Dietary advice
        advice.extend([
            "Follow a low-glycemic index diet",
            "Limit refined carbohydrates and added sugars",
            "Include plenty of vegetables, lean proteins, and whole grains",
            "Consider Mediterranean or DASH diet patterns"
        ])

        # Monitoring recommendations
        if risk_score >= 0.7:
            advice.append("Monitor blood glucose daily and keep a log")
        elif risk_score >= 0.4:
            advice.append("Check blood glucose weekly or as recommended")

        # Medical follow-up
        if glucose >= 100 or risk_score >= 0.4:
            advice.append("Schedule 3-6 month follow-up for diabetes screening")
        else:
            advice.append("Annual diabetes screening recommended")

        return advice
