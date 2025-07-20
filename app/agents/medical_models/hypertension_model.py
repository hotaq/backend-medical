"""
Hypertension Risk Prediction Model

This module implements a scikit-learn based model for predicting hypertension risk
from structured medical data including blood pressure readings, BMI, age, and other factors.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import logging

from .base_medical_model import BaseMedicalModel

logger = logging.getLogger(__name__)


class HypertensionRiskModel(BaseMedicalModel):
    """
    Hypertension risk prediction model using structured medical data.

    This model predicts hypertension risk based on:
    - Systolic and diastolic blood pressure
    - BMI (Body Mass Index)
    - Age
    - Family history (optional)
    - Sodium intake (optional)
    - Physical activity level (optional)
    """

    def __init__(self):
        super().__init__("Hypertension Risk Predictor")

        # Define feature ranges for validation
        self.feature_ranges = {
            'systolic_blood_pressure': (80, 220),  # mmHg
            'diastolic_blood_pressure': (50, 140), # mmHg
            'bmi': (15.0, 50.0),                   # kg/m²
            'age': (18, 100),                      # years
            'family_history_hypertension': (0, 1), # 0=no, 1=yes
            'sodium_intake': (1000, 8000),         # mg/day
            'physical_activity_level': (1, 4),     # 1=sedentary, 4=very active
            'alcohol_consumption': (0, 5),         # drinks per day
        }

        # Define reference ranges for interpretation
        self.reference_ranges = {
            'systolic_blood_pressure': {
                'normal': (90, 119),
                'elevated': (120, 129),
                'stage1_hypertension': (130, 139),
                'stage2_hypertension': (140, 179),
                'crisis': (180, 220)
            },
            'diastolic_blood_pressure': {
                'normal': (60, 79),
                'stage1_hypertension': (80, 89),
                'stage2_hypertension': (90, 119),
                'crisis': (120, 140)
            },
            'bmi': {
                'underweight': (0, 18.5),
                'normal': (18.5, 24.9),
                'overweight': (25.0, 29.9),
                'obese': (30.0, 50.0)
            }
        }

    def get_required_features(self) -> List[str]:
        """Return list of required features for hypertension prediction"""
        return [
            'systolic_blood_pressure',
            'diastolic_blood_pressure',
            'age'
        ]

    def get_optional_features(self) -> List[str]:
        """Return list of optional features that improve prediction accuracy"""
        return [
            'bmi',
            'family_history_hypertension',
            'sodium_intake',
            'physical_activity_level',
            'alcohol_consumption'
        ]

    def _train_model(self, X: np.ndarray, y: np.ndarray):
        """Train the hypertension risk prediction model"""
        model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )

        model.fit(X, y)
        return model

    def _interpret_risk_score(self, risk_score: float) -> str:
        """Convert numeric risk score to categorical hypertension risk level"""
        if risk_score >= 0.8:
            return "very_high"
        elif risk_score >= 0.6:
            return "high"
        elif risk_score >= 0.4:
            return "moderate"
        elif risk_score >= 0.2:
            return "low_moderate"
        else:
            return "low"

    def _generate_recommendations(self, risk_score: float, features: Dict[str, Any]) -> List[str]:
        """Generate hypertension-specific recommendations based on prediction"""
        recommendations = []

        # Get feature values
        systolic = features.get('systolic_blood_pressure', 0)
        diastolic = features.get('diastolic_blood_pressure', 0)
        bmi = features.get('bmi', 0)
        age = features.get('age', 0)
        family_history = features.get('family_history_hypertension', 0)

        # Risk-based recommendations
        if risk_score >= 0.8:
            recommendations.extend([
                "Very high hypertension risk - immediate medical evaluation required",
                "Consider 24-hour ambulatory blood pressure monitoring",
                "Aggressive lifestyle modifications essential"
            ])
        elif risk_score >= 0.6:
            recommendations.extend([
                "High hypertension risk - regular monitoring recommended",
                "Lifestyle modifications strongly advised",
                "Consider home blood pressure monitoring"
            ])
        elif risk_score >= 0.4:
            recommendations.extend([
                "Moderate hypertension risk - preventive measures beneficial",
                "Regular blood pressure checks recommended"
            ])
        else:
            recommendations.append("Continue healthy lifestyle practices")

        # Blood pressure-specific recommendations
        if systolic >= 180 or diastolic >= 120:
            recommendations.extend([
                "Hypertensive crisis - seek immediate emergency care",
                "Do not delay medical treatment"
            ])
        elif systolic >= 140 or diastolic >= 90:
            recommendations.extend([
                "Stage 2 hypertension detected - medication likely required",
                "Urgent medical consultation recommended"
            ])
        elif systolic >= 130 or diastolic >= 80:
            recommendations.extend([
                "Stage 1 hypertension - lifestyle changes and possible medication",
                "DASH diet implementation recommended"
            ])
        elif systolic >= 120:
            recommendations.append("Elevated blood pressure - lifestyle modifications recommended")

        # BMI-specific recommendations
        if bmi >= 30:
            recommendations.extend([
                "Obesity detected - weight loss critical for blood pressure control",
                "Target 5-10% weight reduction initially"
            ])
        elif bmi >= 25:
            recommendations.append("Weight reduction beneficial for blood pressure control")

        # Lifestyle recommendations
        recommendations.extend([
            "DASH diet: increase fruits, vegetables, low-fat dairy",
            "Reduce sodium intake to <2300mg/day (ideally <1500mg/day)",
            "Regular aerobic exercise 30+ minutes most days",
            "Limit alcohol consumption (≤1 drink/day women, ≤2 men)",
            "Stress management techniques beneficial"
        ])

        # Age-specific recommendations
        if age >= 65:
            recommendations.append("Age-related hypertension risk - regular monitoring important")

        # Family history considerations
        if family_history == 1:
            recommendations.append("Family history present - genetic predisposition requires vigilance")

        return recommendations

    def _initialize_default_model(self):
        """Initialize a trained hypertension model with realistic parameters"""
        self.model = RandomForestClassifier(
            n_estimators=100,
            max_depth=8,
            random_state=42,
            class_weight='balanced'
        )

        # Generate synthetic training data
        n_samples = 2500
        features = []
        labels = []

        for _ in range(n_samples):
            # Generate demographics
            age = np.random.normal(50, 15)
            age = max(18, min(100, age))

            # Generate BMI
            bmi = np.random.normal(26, 4)
            bmi = max(18, min(45, bmi))

            # Generate blood pressure with age correlation
            base_systolic = 110 + (age - 40) * 0.7
            base_diastolic = 70 + (age - 40) * 0.3

            # Add BMI effect
            bmi_effect_sys = max(0, (bmi - 25) * 1.5)
            bmi_effect_dia = max(0, (bmi - 25) * 0.8)

            systolic = base_systolic + bmi_effect_sys + np.random.normal(0, 10)
            diastolic = base_diastolic + bmi_effect_dia + np.random.normal(0, 8)

            # Ensure realistic ranges
            systolic = max(90, min(200, systolic))
            diastolic = max(60, min(120, diastolic))

            # Generate other features
            family_history = 1 if np.random.random() < 0.3 else 0
            sodium_intake = np.random.normal(3000, 800)
            activity_level = np.random.randint(1, 5)
            alcohol = np.random.exponential(0.5)

            # Calculate hypertension risk
            age_risk = max(0, (age - 40) / 60)
            bmi_risk = max(0, (bmi - 25) / 15)
            bp_risk = max(0, (systolic - 120) / 60) + max(0, (diastolic - 80) / 40)
            family_risk = family_history * 0.3
            lifestyle_risk = max(0, (sodium_intake - 2300) / 3000) + max(0, (4 - activity_level) / 3)

            total_risk = age_risk + bmi_risk + bp_risk + family_risk + lifestyle_risk
            hypertension_prob = 1 / (1 + np.exp(-2 * (total_risk - 1.2)))

            label = 1 if np.random.random() < hypertension_prob else 0

            features.append([
                systolic,
                diastolic,
                age,
                bmi,
                family_history,
                sodium_intake,
                activity_level,
                alcohol
            ])
            labels.append(label)

        X = np.array(features)
        y = np.array(labels)

        # Train the model
        self.model.fit(X, y)
        self.is_trained = True

        logger.info("Hypertension risk model initialized with synthetic training data")

    def get_blood_pressure_category(self, systolic: float, diastolic: float) -> str:
        """Categorize blood pressure reading according to AHA guidelines"""
        if systolic >= 180 or diastolic >= 120:
            return "Hypertensive Crisis"
        elif systolic >= 140 or diastolic >= 90:
            return "Stage 2 Hypertension"
        elif systolic >= 130 or diastolic >= 80:
            return "Stage 1 Hypertension"
        elif systolic >= 120 and diastolic < 80:
            return "Elevated"
        else:
            return "Normal"

    def calculate_dash_diet_score(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate adherence to DASH diet recommendations.
        This is a simplified version for demonstration.
        """
        sodium = features.get('sodium_intake', 3000)

        dash_score = {
            'sodium_status': 'excellent' if sodium < 1500 else
                           'good' if sodium < 2300 else
                           'needs_improvement',
            'recommended_sodium': min(1500, 2300),
            'current_sodium': sodium,
            'reduction_needed': max(0, sodium - 2300)
        }

        return dash_score
