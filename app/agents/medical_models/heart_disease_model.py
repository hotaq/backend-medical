"""
Heart Disease Risk Prediction Model

This module implements a scikit-learn based model for predicting cardiovascular disease risk
from structured medical data including cholesterol levels, blood pressure, age, and other factors.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import logging

from .base_medical_model import BaseMedicalModel

logger = logging.getLogger(__name__)


class HeartDiseaseRiskModel(BaseMedicalModel):
    """
    Heart disease risk prediction model using structured medical data.

    This model predicts cardiovascular disease risk based on:
    - Total cholesterol levels
    - LDL and HDL cholesterol
    - Blood pressure (systolic/diastolic)
    - Age and gender
    - Smoking status (optional)
    - Family history (optional)
    - Diabetes status (optional)
    """

    def __init__(self):
        super().__init__("Heart Disease Risk Predictor")

        # Define feature ranges for validation
        self.feature_ranges = {
            'total_cholesterol': (100, 400),       # mg/dL
            'ldl_cholesterol': (50, 300),          # mg/dL
            'hdl_cholesterol': (20, 100),          # mg/dL
            'triglycerides': (50, 500),            # mg/dL
            'systolic_blood_pressure': (80, 200),  # mmHg
            'diastolic_blood_pressure': (50, 120), # mmHg
            'age': (18, 100),                      # years
            'gender': (0, 1),                      # 0=female, 1=male
            'smoking_status': (0, 1),              # 0=non-smoker, 1=smoker
            'diabetes_status': (0, 1),             # 0=no diabetes, 1=diabetes
            'family_history_cvd': (0, 1),          # 0=no history, 1=family history
        }

        # Define reference ranges for interpretation
        self.reference_ranges = {
            'total_cholesterol': {
                'desirable': (0, 199),
                'borderline': (200, 239),
                'high': (240, 400)
            },
            'ldl_cholesterol': {
                'optimal': (0, 99),
                'near_optimal': (100, 129),
                'borderline': (130, 159),
                'high': (160, 189),
                'very_high': (190, 300)
            },
            'hdl_cholesterol': {
                'low': (0, 39),
                'normal': (40, 59),
                'high': (60, 100)
            },
            'triglycerides': {
                'normal': (0, 149),
                'borderline': (150, 199),
                'high': (200, 499),
                'very_high': (500, 999)
            },
            'systolic_blood_pressure': {
                'normal': (0, 119),
                'elevated': (120, 129),
                'stage1_hypertension': (130, 139),
                'stage2_hypertension': (140, 200)
            },
            'diastolic_blood_pressure': {
                'normal': (0, 79),
                'stage1_hypertension': (80, 89),
                'stage2_hypertension': (90, 120)
            }
        }

    def get_required_features(self) -> List[str]:
        """Return list of required features for heart disease prediction"""
        return [
            'age',
            'gender',
            'systolic_blood_pressure',
            'total_cholesterol'
        ]

    def get_optional_features(self) -> List[str]:
        """Return list of optional features that improve prediction accuracy"""
        return [
            'ldl_cholesterol',
            'hdl_cholesterol',
            'triglycerides',
            'diastolic_blood_pressure',
            'smoking_status',
            'diabetes_status',
            'family_history_cvd',
            'bmi',
            'physical_activity_level'
        ]

    def _train_model(self, X: np.ndarray, y: np.ndarray):
        """Train the heart disease risk prediction model"""
        # Use Random Forest for cardiovascular risk prediction
        model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            min_samples_split=5,
            min_samples_leaf=3,
            random_state=42,
            class_weight='balanced'
        )

        model.fit(X, y)
        return model

    def _interpret_risk_score(self, risk_score: float) -> str:
        """Convert numeric risk score to categorical cardiovascular risk level"""
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
        """Generate heart disease-specific recommendations based on prediction"""
        recommendations = []

        # Get feature values
        total_chol = features.get('total_cholesterol', 0)
        ldl_chol = features.get('ldl_cholesterol', 0)
        hdl_chol = features.get('hdl_cholesterol', 0)
        systolic_bp = features.get('systolic_blood_pressure', 0)
        diastolic_bp = features.get('diastolic_blood_pressure', 0)
        age = features.get('age', 0)
        gender = features.get('gender', 0)
        smoking = features.get('smoking_status', 0)
        diabetes = features.get('diabetes_status', 0)

        # Risk-based recommendations
        if risk_score >= 0.75:
            recommendations.extend([
                "Very high cardiovascular risk - immediate cardiology consultation required",
                "Consider comprehensive cardiac evaluation including stress testing",
                "Aggressive risk factor modification essential",
                "Discuss preventive cardiac medications with physician"
            ])
        elif risk_score >= 0.5:
            recommendations.extend([
                "High cardiovascular risk - cardiology evaluation recommended",
                "Intensive lifestyle modifications required",
                "Consider cardiac risk assessment tools (coronary calcium scoring)"
            ])
        elif risk_score >= 0.3:
            recommendations.extend([
                "Moderate cardiovascular risk - regular monitoring recommended",
                "Lifestyle modifications beneficial",
                "Annual cardiovascular risk assessment"
            ])
        else:
            recommendations.extend([
                "Continue current heart-healthy practices",
                "Maintain regular preventive care"
            ])

        # Cholesterol-specific recommendations
        if total_chol >= 240:
            recommendations.extend([
                "High cholesterol detected - lipid management required",
                "Consider statin therapy evaluation",
                "Dietary cholesterol reduction essential"
            ])
        elif total_chol >= 200:
            recommendations.append("Borderline high cholesterol - dietary modifications recommended")

        if ldl_chol >= 160:
            recommendations.append("LDL cholesterol very high - aggressive treatment indicated")
        elif ldl_chol >= 130:
            recommendations.append("LDL cholesterol elevated - lifestyle and possible medication therapy")

        if hdl_chol < 40:
            recommendations.extend([
                "Low HDL cholesterol - increase aerobic exercise",
                "Consider niacin or fibrate therapy evaluation"
            ])

        # Blood pressure recommendations
        if systolic_bp >= 140 or diastolic_bp >= 90:
            recommendations.extend([
                "Hypertension detected - blood pressure management essential",
                "DASH diet and sodium restriction recommended",
                "Consider antihypertensive medication evaluation"
            ])
        elif systolic_bp >= 130 or diastolic_bp >= 80:
            recommendations.append("Elevated blood pressure - lifestyle modifications recommended")

        # Smoking cessation
        if smoking == 1:
            recommendations.extend([
                "Smoking cessation critical for cardiovascular health",
                "Consider nicotine replacement therapy or counseling",
                "Risk reduction benefits begin immediately after quitting"
            ])

        # Diabetes management
        if diabetes == 1:
            recommendations.extend([
                "Diabetes increases cardiovascular risk - optimal glucose control essential",
                "Target HbA1c <7% for most patients",
                "Regular cardiovascular screening recommended"
            ])

        # Age and gender-specific recommendations
        if gender == 1 and age >= 45:  # Male ≥45
            recommendations.append("Age and gender increase cardiovascular risk - regular screening important")
        elif gender == 0 and age >= 55:  # Female ≥55
            recommendations.append("Post-menopausal cardiovascular risk - hormone therapy discussion may be beneficial")

        # General lifestyle recommendations
        recommendations.extend([
            "Mediterranean diet pattern recommended",
            "Regular aerobic exercise (150 minutes/week minimum)",
            "Weight management if BMI >25",
            "Stress reduction techniques beneficial",
            "Limit alcohol consumption (≤1 drink/day for women, ≤2 for men)"
        ])

        return recommendations

    def _initialize_default_model(self):
        """Initialize a trained heart disease model with realistic parameters"""
        self.model = RandomForestClassifier(
            n_estimators=150,
            max_depth=12,
            random_state=42,
            class_weight='balanced'
        )

        # Generate synthetic training data based on Framingham Risk Score factors
        n_samples = 3000
        features = []
        labels = []

        for _ in range(n_samples):
            # Generate demographics
            age = np.random.normal(55, 15)
            age = max(18, min(100, age))
            gender = np.random.choice([0, 1])  # 0=female, 1=male

            # Generate cardiovascular risk factors
            # Age-related cholesterol increase
            base_chol = 180 + (age - 40) * 1.5 + np.random.normal(0, 30)
            total_chol = max(120, min(400, base_chol))

            # LDL typically 60-70% of total cholesterol
            ldl_chol = total_chol * (0.6 + np.random.normal(0, 0.1))
            ldl_chol = max(50, min(300, ldl_chol))

            # HDL - typically higher in women
            base_hdl = 50 if gender == 0 else 40
            hdl_chol = base_hdl + np.random.normal(0, 10)
            hdl_chol = max(20, min(100, hdl_chol))

            # Triglycerides
            triglycerides = np.random.normal(150, 50)
            triglycerides = max(50, min(500, triglycerides))

            # Blood pressure (age-related increase)
            systolic_bp = 110 + (age - 40) * 0.8 + np.random.normal(0, 15)
            systolic_bp = max(90, min(200, systolic_bp))

            diastolic_bp = 70 + (age - 40) * 0.3 + np.random.normal(0, 10)
            diastolic_bp = max(60, min(120, diastolic_bp))

            # Risk factors
            smoking = 1 if np.random.random() < 0.15 else 0
            diabetes = 1 if np.random.random() < 0.08 else 0
            family_history = 1 if np.random.random() < 0.25 else 0
            bmi = np.random.normal(26, 4)
            activity_level = np.random.randint(1, 4)

            # Calculate cardiovascular risk based on established factors
            age_risk = max(0, (age - 40) / 60)
            gender_risk = 0.2 if gender == 1 else 0  # Male higher risk
            chol_risk = max(0, (total_chol - 200) / 200)
            ldl_risk = max(0, (ldl_chol - 100) / 150)
            hdl_risk = max(0, (50 - hdl_chol) / 30)  # Lower HDL = higher risk
            bp_risk = max(0, (systolic_bp - 120) / 80)
            smoking_risk = smoking * 0.4
            diabetes_risk = diabetes * 0.3
            family_risk = family_history * 0.2

            total_risk = (age_risk + gender_risk + chol_risk + ldl_risk +
                         hdl_risk + bp_risk + smoking_risk + diabetes_risk + family_risk)

            # Convert to probability
            cvd_probability = 1 / (1 + np.exp(-2 * (total_risk - 1.5)))

            # Determine label
            label = 1 if np.random.random() < cvd_probability else 0

            features.append([
                age,
                gender,
                systolic_bp,
                total_chol,
                ldl_chol,
                hdl_chol,
                triglycerides,
                diastolic_bp,
                smoking,
                diabetes,
                family_history,
                bmi,
                activity_level
            ])
            labels.append(label)

        X = np.array(features)
        y = np.array(labels)

        # Train the model
        self.model.fit(X, y)
        self.is_trained = True

        # Log feature importance
        if hasattr(self.model, 'feature_importances_'):
            feature_names = self.get_required_features() + self.get_optional_features()
            importance_dict = dict(zip(feature_names, self.model.feature_importances_))
            logger.info(f"Heart disease model feature importance: {importance_dict}")

        logger.info("Heart disease risk model initialized with synthetic training data")

    def calculate_framingham_risk(self, features: Dict[str, Any]) -> float:
        """
        Calculate Framingham Risk Score for cardiovascular disease.

        This is a simplified version of the established Framingham Risk Score.
        """
        age = features.get('age', 40)
        gender = features.get('gender', 0)
        total_chol = features.get('total_cholesterol', 200)
        hdl_chol = features.get('hdl_cholesterol', 50)
        systolic_bp = features.get('systolic_blood_pressure', 120)
        smoking = features.get('smoking_status', 0)
        diabetes = features.get('diabetes_status', 0)

        # Simplified Framingham calculation
        points = 0

        # Age points
        if gender == 1:  # Male
            if age >= 70: points += 11
            elif age >= 60: points += 8
            elif age >= 50: points += 5
            elif age >= 40: points += 2
        else:  # Female
            if age >= 70: points += 12
            elif age >= 60: points += 9
            elif age >= 50: points += 6
            elif age >= 40: points += 3

        # Cholesterol points
        if total_chol >= 280: points += 3
        elif total_chol >= 240: points += 2
        elif total_chol >= 200: points += 1

        # HDL points (protective)
        if hdl_chol >= 60: points -= 1
        elif hdl_chol < 35: points += 2
        elif hdl_chol < 45: points += 1

        # Blood pressure points
        if systolic_bp >= 160: points += 3
        elif systolic_bp >= 140: points += 2
        elif systolic_bp >= 130: points += 1

        # Risk factors
        if smoking: points += 3
        if diabetes: points += 3

        # Convert points to risk percentage (simplified)
        if points <= 0: risk = 0.02
        elif points <= 4: risk = 0.05
        elif points <= 8: risk = 0.10
        elif points <= 12: risk = 0.20
        elif points <= 16: risk = 0.30
        else: risk = 0.40

        return min(risk, 0.80)  # Cap at 80%

    def get_lipid_profile_interpretation(self, features: Dict[str, Any]) -> Dict[str, str]:
        """Get detailed interpretation of lipid profile"""
        interpretations = {}

        total_chol = features.get('total_cholesterol', 0)
        ldl_chol = features.get('ldl_cholesterol', 0)
        hdl_chol = features.get('hdl_cholesterol', 0)
        triglycerides = features.get('triglycerides', 0)

        # Total cholesterol
        if total_chol >= 240:
            interpretations['total_cholesterol'] = "High (≥240 mg/dL) - treatment indicated"
        elif total_chol >= 200:
            interpretations['total_cholesterol'] = "Borderline high (200-239 mg/dL)"
        elif total_chol > 0:
            interpretations['total_cholesterol'] = "Desirable (<200 mg/dL)"

        # LDL cholesterol
        if ldl_chol >= 190:
            interpretations['ldl_cholesterol'] = "Very high (≥190 mg/dL) - immediate treatment"
        elif ldl_chol >= 160:
            interpretations['ldl_cholesterol'] = "High (160-189 mg/dL)"
        elif ldl_chol >= 130:
            interpretations['ldl_cholesterol'] = "Borderline high (130-159 mg/dL)"
        elif ldl_chol >= 100:
            interpretations['ldl_cholesterol'] = "Near optimal (100-129 mg/dL)"
        elif ldl_chol > 0:
            interpretations['ldl_cholesterol'] = "Optimal (<100 mg/dL)"

        # HDL cholesterol
        if hdl_chol >= 60:
            interpretations['hdl_cholesterol'] = "High (≥60 mg/dL) - protective factor"
        elif hdl_chol >= 40:
            interpretations['hdl_cholesterol'] = "Normal (40-59 mg/dL)"
        elif hdl_chol > 0:
            interpretations['hdl_cholesterol'] = "Low (<40 mg/dL) - risk factor"

        # Triglycerides
        if triglycerides >= 500:
            interpretations['triglycerides'] = "Very high (≥500 mg/dL) - pancreatitis risk"
        elif triglycerides >= 200:
            interpretations['triglycerides'] = "High (200-499 mg/dL)"
        elif triglycerides >= 150:
            interpretations['triglycerides'] = "Borderline high (150-199 mg/dL)"
        elif triglycerides > 0:
            interpretations['triglycerides'] = "Normal (<150 mg/dL)"

        return interpretations

    def get_blood_pressure_interpretation(self, features: Dict[str, Any]) -> str:
        """Get blood pressure category interpretation"""
        systolic = features.get('systolic_blood_pressure', 0)
        diastolic = features.get('diastolic_blood_pressure', 0)

        if systolic >= 180 or diastolic >= 120:
            return "Hypertensive crisis - immediate medical attention required"
        elif systolic >= 140 or diastolic >= 90:
            return "Stage 2 hypertension - medication typically required"
        elif systolic >= 130 or diastolic >= 80:
            return "Stage 1 hypertension - lifestyle changes and possible medication"
        elif systolic >= 120 and diastolic < 80:
            return "Elevated blood pressure - lifestyle modifications recommended"
        else:
            return "Normal blood pressure (<120/80 mmHg)"
