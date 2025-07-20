"""
Kidney Disease Risk Prediction Model

This module implements a scikit-learn based model for predicting chronic kidney disease (CKD) risk
from structured medical data including creatinine, BUN, protein levels, and other factors.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import logging

from .base_medical_model import BaseMedicalModel

logger = logging.getLogger(__name__)


class KidneyDiseaseRiskModel(BaseMedicalModel):
    """
    Kidney disease risk prediction model using structured medical data.

    This model predicts CKD risk based on:
    - Serum creatinine levels
    - Blood Urea Nitrogen (BUN)
    - Protein in urine (proteinuria)
    - Estimated GFR (Glomerular Filtration Rate)
    - Blood pressure
    - Diabetes status
    - Age
    """

    def __init__(self):
        super().__init__("Kidney Disease Risk Predictor")

        # Define feature ranges for validation
        self.feature_ranges = {
            'creatinine': (0.5, 10.0),             # mg/dL
            'blood_urea_nitrogen': (5, 100),        # mg/dL
            'protein_urine': (0, 5),               # g/day or qualitative scale
            'estimated_gfr': (5, 150),             # mL/min/1.73m²
            'systolic_blood_pressure': (80, 200),   # mmHg
            'diastolic_blood_pressure': (50, 120),  # mmHg
            'age': (18, 100),                       # years
            'diabetes_status': (0, 1),              # 0=no, 1=yes
            'hypertension_status': (0, 1),          # 0=no, 1=yes
            'hemoglobin': (8, 18),                  # g/dL
        }

        # Define reference ranges for interpretation
        self.reference_ranges = {
            'creatinine': {
                'normal_male': (0.7, 1.3),
                'normal_female': (0.6, 1.1),
                'mild_elevation': (1.4, 2.0),
                'moderate_elevation': (2.1, 4.0),
                'severe_elevation': (4.1, 10.0)
            },
            'blood_urea_nitrogen': {
                'normal': (7, 20),
                'mild_elevation': (21, 40),
                'moderate_elevation': (41, 60),
                'severe_elevation': (61, 100)
            },
            'estimated_gfr': {
                'normal': (90, 150),
                'mild_decrease': (60, 89),
                'moderate_decrease': (30, 59),
                'severe_decrease': (15, 29),
                'kidney_failure': (5, 14)
            },
            'protein_urine': {
                'normal': (0, 0.3),
                'mild_proteinuria': (0.3, 1.0),
                'moderate_proteinuria': (1.0, 3.0),
                'severe_proteinuria': (3.0, 5.0)
            }
        }

    def get_required_features(self) -> List[str]:
        """Return list of required features for kidney disease prediction"""
        return [
            'creatinine',
            'age'
        ]

    def get_optional_features(self) -> List[str]:
        """Return list of optional features that improve prediction accuracy"""
        return [
            'blood_urea_nitrogen',
            'protein_urine',
            'estimated_gfr',
            'systolic_blood_pressure',
            'diastolic_blood_pressure',
            'diabetes_status',
            'hypertension_status',
            'hemoglobin'
        ]

    def _train_model(self, X: np.ndarray, y: np.ndarray):
        """Train the kidney disease risk prediction model"""
        model = RandomForestClassifier(
            n_estimators=120,
            max_depth=10,
            min_samples_split=5,
            min_samples_leaf=3,
            random_state=42,
            class_weight='balanced'
        )

        model.fit(X, y)
        return model

    def _interpret_risk_score(self, risk_score: float) -> str:
        """Convert numeric risk score to categorical kidney disease risk level"""
        if risk_score >= 0.75:
            return "very_high"
        elif risk_score >= 0.5:
            return "high"
        elif risk_score >= 0.3:
            return "moderate"
        elif risk_score >= 0.15:
            return "low_moderate"
        else:
            return "low"

    def _generate_recommendations(self, risk_score: float, features: Dict[str, Any]) -> List[str]:
        """Generate kidney disease-specific recommendations based on prediction"""
        recommendations = []

        # Get feature values
        creatinine = features.get('creatinine', 0)
        bun = features.get('blood_urea_nitrogen', 0)
        protein_urine = features.get('protein_urine', 0)
        gfr = features.get('estimated_gfr', 0)
        systolic_bp = features.get('systolic_blood_pressure', 0)
        diabetes = features.get('diabetes_status', 0)
        age = features.get('age', 0)

        # Risk-based recommendations
        if risk_score >= 0.75:
            recommendations.extend([
                "Very high kidney disease risk - immediate nephrology consultation required",
                "Comprehensive kidney function evaluation needed",
                "Consider renal ultrasound and additional testing"
            ])
        elif risk_score >= 0.5:
            recommendations.extend([
                "High kidney disease risk - nephrology referral recommended",
                "Regular kidney function monitoring essential",
                "Aggressive blood pressure and diabetes control"
            ])
        elif risk_score >= 0.3:
            recommendations.extend([
                "Moderate kidney disease risk - enhanced monitoring recommended",
                "Annual comprehensive metabolic panel",
                "Focus on prevention strategies"
            ])
        else:
            recommendations.append("Continue kidney-healthy lifestyle practices")

        # Creatinine-specific recommendations
        if creatinine >= 2.0:
            recommendations.extend([
                "Significantly elevated creatinine - urgent medical evaluation",
                "Assess for acute kidney injury vs chronic disease",
                "Review all medications for nephrotoxic agents"
            ])
        elif creatinine >= 1.5:
            recommendations.extend([
                "Elevated creatinine - kidney function assessment recommended",
                "Calculate estimated GFR for staging"
            ])

        # BUN-specific recommendations
        if bun >= 40:
            recommendations.extend([
                "Elevated BUN - assess kidney function and hydration status",
                "Consider protein intake evaluation"
            ])

        # Proteinuria recommendations
        if protein_urine >= 1.0:
            recommendations.extend([
                "Significant proteinuria detected - nephrology consultation",
                "ACE inhibitor or ARB therapy consideration",
                "Diabetes screening if not already diagnosed"
            ])
        elif protein_urine >= 0.3:
            recommendations.append("Mild proteinuria - repeat testing and monitoring recommended")

        # GFR-specific recommendations
        if gfr > 0:
            if gfr < 30:
                recommendations.extend([
                    f"Severely reduced kidney function (GFR {gfr}) - nephrology care essential",
                    "Prepare for renal replacement therapy planning",
                    "Bone metabolism and anemia evaluation"
                ])
            elif gfr < 60:
                recommendations.extend([
                    f"Reduced kidney function (GFR {gfr}) - CKD management needed",
                    "Cardiovascular risk assessment important",
                    "Medication dose adjustments may be required"
                ])

        # Blood pressure management
        if systolic_bp >= 140:
            recommendations.extend([
                "Hypertension control critical for kidney protection",
                "Target blood pressure <130/80 mmHg for kidney disease",
                "ACE inhibitors or ARBs preferred for kidney protection"
            ])

        # Diabetes management
        if diabetes == 1:
            recommendations.extend([
                "Diabetes control essential for kidney protection",
                "Target HbA1c <7% to prevent diabetic nephropathy",
                "Annual microalbumin screening recommended"
            ])

        # General kidney health recommendations
        recommendations.extend([
            "Stay well hydrated (8+ glasses water daily)",
            "Limit NSAIDs and other nephrotoxic medications",
            "Maintain healthy weight and exercise regularly",
            "Limit sodium intake (<2300mg/day)",
            "Avoid excessive protein intake if kidney disease present"
        ])

        # Age-specific recommendations
        if age >= 60:
            recommendations.append("Age-related kidney function decline - regular monitoring important")

        return recommendations

    def _initialize_default_model(self):
        """Initialize a trained kidney disease model with realistic parameters"""
        self.model = RandomForestClassifier(
            n_estimators=120,
            max_depth=10,
            random_state=42,
            class_weight='balanced'
        )

        # Generate synthetic training data
        n_samples = 2000
        features = []
        labels = []

        for _ in range(n_samples):
            # Generate demographics
            age = np.random.normal(58, 15)
            age = max(18, min(100, age))

            # Generate baseline kidney function with age decline
            base_gfr = 120 - (age - 30) * 0.8 + np.random.normal(0, 15)
            base_gfr = max(10, min(150, base_gfr))

            # Generate creatinine inversely related to GFR
            # Using simplified inverse relationship
            creatinine = 1.2 + (120 - base_gfr) * 0.02 + np.random.normal(0, 0.2)
            creatinine = max(0.5, min(8.0, creatinine))

            # BUN somewhat correlated with creatinine
            bun = 15 + (creatinine - 1.0) * 8 + np.random.normal(0, 5)
            bun = max(5, min(80, bun))

            # Generate other features
            diabetes = 1 if np.random.random() < 0.25 else 0
            hypertension = 1 if np.random.random() < 0.35 else 0

            # Blood pressure (higher with kidney disease)
            systolic_bp = 125 + (2.0 - creatinine) * -10 + np.random.normal(0, 15)
            systolic_bp = max(90, min(180, systolic_bp))

            diastolic_bp = 80 + (2.0 - creatinine) * -5 + np.random.normal(0, 10)
            diastolic_bp = max(60, min(110, diastolic_bp))

            # Protein in urine (higher risk with diabetes/hypertension)
            protein_base = 0.1
            if diabetes: protein_base += 0.5
            if hypertension: protein_base += 0.3
            protein_urine = protein_base + np.random.exponential(0.3)
            protein_urine = min(protein_urine, 4.0)

            # Hemoglobin (lower with advanced CKD)
            hemoglobin = 13.5 - max(0, (2.0 - creatinine) * 2) + np.random.normal(0, 1)
            hemoglobin = max(8, min(17, hemoglobin))

            # Calculate CKD risk
            age_risk = max(0, (age - 50) / 50)
            creatinine_risk = max(0, (creatinine - 1.2) / 3.0)
            gfr_risk = max(0, (90 - base_gfr) / 80)
            diabetes_risk = diabetes * 0.4
            hypertension_risk = hypertension * 0.3
            protein_risk = min(protein_urine / 2.0, 1.0)

            total_risk = (age_risk + creatinine_risk + gfr_risk +
                         diabetes_risk + hypertension_risk + protein_risk)

            ckd_probability = 1 / (1 + np.exp(-2 * (total_risk - 1.5)))
            label = 1 if np.random.random() < ckd_probability else 0

            features.append([
                creatinine,
                age,
                bun,
                protein_urine,
                base_gfr,
                systolic_bp,
                diastolic_bp,
                diabetes,
                hypertension,
                hemoglobin
            ])
            labels.append(label)

        X = np.array(features)
        y = np.array(labels)

        # Train the model
        self.model.fit(X, y)
        self.is_trained = True

        logger.info("Kidney disease risk model initialized with synthetic training data")

    def calculate_estimated_gfr(self, creatinine: float, age: float, gender: int = 1) -> float:
        """
        Calculate estimated GFR using simplified CKD-EPI equation.

        Args:
            creatinine: Serum creatinine in mg/dL
            age: Age in years
            gender: 1 for male, 0 for female

        Returns:
            Estimated GFR in mL/min/1.73m²
        """
        # Simplified CKD-EPI calculation
        if gender == 0:  # Female
            if creatinine <= 0.7:
                gfr = 144 * (creatinine / 0.7) ** -0.329
            else:
                gfr = 144 * (creatinine / 0.7) ** -1.209
        else:  # Male
            if creatinine <= 0.9:
                gfr = 141 * (creatinine / 0.9) ** -0.411
            else:
                gfr = 141 * (creatinine / 0.9) ** -1.209

        gfr = gfr * (0.993 ** age)
        return max(5, min(150, gfr))

    def get_ckd_stage(self, gfr: float) -> str:
        """Determine CKD stage based on GFR"""
        if gfr >= 90:
            return "Normal or high (Stage 1 if kidney damage present)"
        elif gfr >= 60:
            return "Mildly decreased (Stage 2)"
        elif gfr >= 30:
            return "Moderately decreased (Stage 3)"
        elif gfr >= 15:
            return "Severely decreased (Stage 4)"
        else:
            return "Kidney failure (Stage 5)"

    def get_kidney_function_interpretation(self, features: Dict[str, Any]) -> Dict[str, str]:
        """Get detailed interpretation of kidney function tests"""
        interpretations = {}

        creatinine = features.get('creatinine', 0)
        bun = features.get('blood_urea_nitrogen', 0)
        gfr = features.get('estimated_gfr', 0)
        protein = features.get('protein_urine', 0)

        # Creatinine interpretation
        if creatinine >= 4.0:
            interpretations['creatinine'] = f"Severely elevated ({creatinine} mg/dL) - kidney failure likely"
        elif creatinine >= 2.0:
            interpretations['creatinine'] = f"Significantly elevated ({creatinine} mg/dL) - advanced kidney disease"
        elif creatinine >= 1.5:
            interpretations['creatinine'] = f"Elevated ({creatinine} mg/dL) - kidney function impaired"
        elif creatinine > 0:
            interpretations['creatinine'] = f"Normal range ({creatinine} mg/dL)"

        # BUN interpretation
        if bun >= 60:
            interpretations['bun'] = f"Severely elevated ({bun} mg/dL) - significant kidney impairment"
        elif bun >= 40:
            interpretations['bun'] = f"Elevated ({bun} mg/dL) - kidney function concern"
        elif bun >= 20:
            interpretations['bun'] = f"Mildly elevated ({bun} mg/dL) - monitor kidney function"
        elif bun > 0:
            interpretations['bun'] = f"Normal range ({bun} mg/dL)"

        # GFR interpretation
        if gfr > 0:
            interpretations['gfr'] = f"GFR {gfr} mL/min/1.73m² - {self.get_ckd_stage(gfr)}"

        # Protein interpretation
        if protein >= 3.0:
            interpretations['protein'] = f"Severe proteinuria ({protein} g/day) - nephrology urgent"
        elif protein >= 1.0:
            interpretations['protein'] = f"Moderate proteinuria ({protein} g/day) - kidney disease likely"
        elif protein >= 0.3:
            interpretations['protein'] = f"Mild proteinuria ({protein} g/day) - monitor closely"
        elif protein >= 0:
            interpretations['protein'] = f"Normal protein levels ({protein} g/day)"

        return interpretations
