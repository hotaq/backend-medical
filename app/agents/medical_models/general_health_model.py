"""
General Health Risk Assessment Model

This module implements a comprehensive health risk assessment model that combines
multiple medical factors to provide an overall health risk score and recommendations.
"""

from typing import Dict, Any, List
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
import logging

from .base_medical_model import BaseMedicalModel

logger = logging.getLogger(__name__)


class GeneralHealthRiskModel(BaseMedicalModel):
    """
    General health risk assessment model using comprehensive medical data.

    This model provides an overall health risk assessment based on:
    - Vital signs (blood pressure, heart rate)
    - Laboratory values (glucose, cholesterol, kidney function)
    - Anthropometric measures (BMI, age)
    - Risk factors (smoking, family history, medications)
    - Lifestyle factors (physical activity, diet)
    """

    def __init__(self):
        super().__init__("General Health Risk Assessor")

        # Define feature ranges for validation
        self.feature_ranges = {
            'age': (18, 100),                       # years
            'bmi': (15.0, 50.0),                   # kg/m²
            'systolic_blood_pressure': (80, 220),   # mmHg
            'diastolic_blood_pressure': (50, 140),  # mmHg
            'heart_rate': (40, 150),                # bpm
            'fasting_glucose': (60, 400),           # mg/dL
            'total_cholesterol': (100, 400),        # mg/dL
            'hdl_cholesterol': (20, 100),           # mg/dL
            'ldl_cholesterol': (50, 300),           # mg/dL
            'triglycerides': (50, 500),             # mg/dL
            'creatinine': (0.5, 8.0),              # mg/dL
            'hemoglobin_a1c': (4.0, 15.0),         # %
            'smoking_status': (0, 1),               # 0=non-smoker, 1=smoker
            'alcohol_consumption': (0, 5),          # drinks per day
            'physical_activity_level': (1, 4),      # 1=sedentary, 4=very active
            'family_history_score': (0, 5),         # composite family history score
        }

        # Define health risk categories
        self.health_categories = {
            'cardiovascular': {
                'weight': 0.25,
                'features': ['systolic_blood_pressure', 'diastolic_blood_pressure',
                           'total_cholesterol', 'ldl_cholesterol', 'hdl_cholesterol']
            },
            'metabolic': {
                'weight': 0.25,
                'features': ['fasting_glucose', 'hemoglobin_a1c', 'bmi', 'triglycerides']
            },
            'kidney': {
                'weight': 0.15,
                'features': ['creatinine', 'systolic_blood_pressure']
            },
            'lifestyle': {
                'weight': 0.20,
                'features': ['smoking_status', 'alcohol_consumption', 'physical_activity_level', 'bmi']
            },
            'genetic': {
                'weight': 0.15,
                'features': ['family_history_score', 'age']
            }
        }

    def get_required_features(self) -> List[str]:
        """Return list of required features for general health assessment"""
        return [
            'age',
            'bmi',
            'systolic_blood_pressure'
        ]

    def get_optional_features(self) -> List[str]:
        """Return list of optional features that improve assessment accuracy"""
        return [
            'diastolic_blood_pressure',
            'heart_rate',
            'fasting_glucose',
            'total_cholesterol',
            'hdl_cholesterol',
            'ldl_cholesterol',
            'triglycerides',
            'creatinine',
            'hemoglobin_a1c',
            'smoking_status',
            'alcohol_consumption',
            'physical_activity_level',
            'family_history_score'
        ]

    def _train_model(self, X: np.ndarray, y: np.ndarray):
        """Train the general health risk assessment model"""
        model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=5,
            min_samples_leaf=2,
            random_state=42,
            class_weight='balanced'
        )

        model.fit(X, y)
        return model

    def _interpret_risk_score(self, risk_score: float) -> str:
        """Convert numeric risk score to categorical health risk level"""
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
        """Generate comprehensive health recommendations based on assessment"""
        recommendations = []

        # Get feature values
        age = features.get('age', 0)
        bmi = features.get('bmi', 0)
        systolic_bp = features.get('systolic_blood_pressure', 0)
        diastolic_bp = features.get('diastolic_blood_pressure', 0)
        glucose = features.get('fasting_glucose', 0)
        total_chol = features.get('total_cholesterol', 0)
        smoking = features.get('smoking_status', 0)
        activity = features.get('physical_activity_level', 2)

        # Overall risk-based recommendations
        if risk_score >= 0.8:
            recommendations.extend([
                "Very high health risk detected - comprehensive medical evaluation urgent",
                "Multiple risk factors require immediate attention",
                "Consider specialist referrals as appropriate",
                "Aggressive lifestyle modifications essential"
            ])
        elif risk_score >= 0.6:
            recommendations.extend([
                "High health risk - medical consultation recommended",
                "Multiple preventive interventions beneficial",
                "Regular monitoring of health metrics important"
            ])
        elif risk_score >= 0.4:
            recommendations.extend([
                "Moderate health risk - preventive measures recommended",
                "Focus on modifiable risk factors",
                "Annual comprehensive health screening"
            ])
        else:
            recommendations.extend([
                "Good overall health status",
                "Continue current healthy practices",
                "Regular preventive care recommended"
            ])

        # Category-specific recommendations
        recommendations.extend(self._get_cardiovascular_recommendations(features))
        recommendations.extend(self._get_metabolic_recommendations(features))
        recommendations.extend(self._get_lifestyle_recommendations(features))
        recommendations.extend(self._get_preventive_recommendations(features))

        return recommendations

    def _get_cardiovascular_recommendations(self, features: Dict[str, Any]) -> List[str]:
        """Generate cardiovascular-specific recommendations"""
        recommendations = []

        systolic_bp = features.get('systolic_blood_pressure', 0)
        diastolic_bp = features.get('diastolic_blood_pressure', 0)
        total_chol = features.get('total_cholesterol', 0)
        hdl_chol = features.get('hdl_cholesterol', 0)

        if systolic_bp >= 140 or diastolic_bp >= 90:
            recommendations.extend([
                "Blood pressure elevation detected - cardiovascular risk management needed",
                "DASH diet and sodium restriction recommended"
            ])

        if total_chol >= 240:
            recommendations.append("High cholesterol - lipid management strategies needed")

        if hdl_chol > 0 and hdl_chol < 40:
            recommendations.append("Low HDL cholesterol - aerobic exercise beneficial")

        return recommendations

    def _get_metabolic_recommendations(self, features: Dict[str, Any]) -> List[str]:
        """Generate metabolic health recommendations"""
        recommendations = []

        glucose = features.get('fasting_glucose', 0)
        hba1c = features.get('hemoglobin_a1c', 0)
        bmi = features.get('bmi', 0)
        triglycerides = features.get('triglycerides', 0)

        if glucose >= 126:
            recommendations.append("Elevated glucose - diabetes evaluation recommended")
        elif glucose >= 100:
            recommendations.append("Prediabetic glucose range - diabetes prevention important")

        if hba1c >= 6.5:
            recommendations.append("HbA1c indicates diabetes - endocrine consultation beneficial")
        elif hba1c >= 5.7:
            recommendations.append("Prediabetic HbA1c - lifestyle interventions recommended")

        if bmi >= 30:
            recommendations.extend([
                "Obesity detected - structured weight management program beneficial",
                "Target 5-10% initial weight loss"
            ])
        elif bmi >= 25:
            recommendations.append("Overweight - gradual weight reduction beneficial")

        if triglycerides >= 200:
            recommendations.append("Elevated triglycerides - dietary modification and exercise recommended")

        return recommendations

    def _get_lifestyle_recommendations(self, features: Dict[str, Any]) -> List[str]:
        """Generate lifestyle modification recommendations"""
        recommendations = []

        smoking = features.get('smoking_status', 0)
        alcohol = features.get('alcohol_consumption', 0)
        activity = features.get('physical_activity_level', 2)

        if smoking == 1:
            recommendations.extend([
                "Smoking cessation critical for health improvement",
                "Consider nicotine replacement therapy or counseling support",
                "Benefits begin immediately after quitting"
            ])

        if alcohol > 2:  # Excessive drinking
            recommendations.extend([
                "Alcohol consumption above recommended limits",
                "Consider reduction to ≤1 drink/day (women) or ≤2 drinks/day (men)"
            ])

        if activity <= 2:  # Low activity level
            recommendations.extend([
                "Physical activity level below optimal",
                "Target 150+ minutes moderate aerobic activity per week",
                "Include resistance training 2-3 times per week"
            ])

        return recommendations

    def _get_preventive_recommendations(self, features: Dict[str, Any]) -> List[str]:
        """Generate preventive care recommendations"""
        recommendations = []

        age = features.get('age', 0)

        # Age-based screening recommendations
        if age >= 50:
            recommendations.extend([
                "Age-appropriate cancer screening recommended",
                "Annual comprehensive physical examination",
                "Bone density assessment consideration"
            ])

        if age >= 40:
            recommendations.extend([
                "Cardiovascular risk assessment annually",
                "Diabetes screening every 3 years"
            ])

        # General preventive care
        recommendations.extend([
            "Maintain up-to-date vaccinations",
            "Regular dental and vision care",
            "Stress management techniques beneficial",
            "Adequate sleep (7-9 hours nightly) important"
        ])

        return recommendations

    def _initialize_default_model(self):
        """Initialize a trained general health model with realistic parameters"""
        self.model = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            random_state=42,
            class_weight='balanced'
        )

        # Generate comprehensive synthetic training data
        n_samples = 5000
        features = []
        labels = []

        for _ in range(n_samples):
            # Generate demographics
            age = np.random.normal(50, 18)
            age = max(18, min(100, age))

            # Generate anthropometrics
            bmi = np.random.normal(26, 5)
            bmi = max(18, min(45, bmi))

            # Generate vital signs with age/BMI correlations
            systolic_bp = 110 + (age - 40) * 0.7 + (bmi - 25) * 1.2 + np.random.normal(0, 12)
            systolic_bp = max(90, min(200, systolic_bp))

            diastolic_bp = 70 + (age - 40) * 0.3 + (bmi - 25) * 0.6 + np.random.normal(0, 8)
            diastolic_bp = max(60, min(120, diastolic_bp))

            heart_rate = 70 + np.random.normal(0, 12)
            heart_rate = max(50, min(120, heart_rate))

            # Generate lab values
            glucose = 90 + (age - 40) * 0.5 + (bmi - 25) * 1.5 + np.random.normal(0, 15)
            glucose = max(70, min(300, glucose))

            total_chol = 180 + (age - 40) * 1.2 + np.random.normal(0, 30)
            total_chol = max(120, min(350, total_chol))

            hdl_chol = 50 - (bmi - 25) * 0.8 + np.random.normal(0, 10)
            hdl_chol = max(25, min(80, hdl_chol))

            ldl_chol = total_chol * 0.65 + np.random.normal(0, 20)
            ldl_chol = max(50, min(250, ldl_chol))

            triglycerides = 120 + (bmi - 25) * 3 + np.random.normal(0, 40)
            triglycerides = max(60, min(400, triglycerides))

            creatinine = 1.0 + (age - 40) * 0.005 + np.random.normal(0, 0.2)
            creatinine = max(0.6, min(3.0, creatinine))

            hba1c = 5.2 + (glucose - 90) * 0.02 + np.random.normal(0, 0.3)
            hba1c = max(4.5, min(12.0, hba1c))

            # Generate lifestyle factors
            smoking = 1 if np.random.random() < 0.15 else 0
            alcohol = np.random.exponential(0.5)
            alcohol = min(alcohol, 4)
            activity = np.random.randint(1, 5)
            family_history = np.random.randint(0, 6)

            # Calculate comprehensive health risk
            age_risk = max(0, (age - 40) / 60)
            bmi_risk = max(0, (bmi - 25) / 15)
            bp_risk = max(0, (systolic_bp - 120) / 60) + max(0, (diastolic_bp - 80) / 40)
            glucose_risk = max(0, (glucose - 100) / 100)
            chol_risk = max(0, (total_chol - 200) / 150)
            hdl_risk = max(0, (50 - hdl_chol) / 30)
            smoking_risk = smoking * 0.4
            lifestyle_risk = max(0, (4 - activity) / 3) + min(alcohol / 3, 0.3)
            family_risk = family_history / 10

            total_risk = (age_risk + bmi_risk + bp_risk + glucose_risk +
                         chol_risk + hdl_risk + smoking_risk + lifestyle_risk + family_risk)

            # Convert to probability with more nuanced scaling
            health_risk_prob = 1 / (1 + np.exp(-1.5 * (total_risk - 2.0)))
            label = 1 if np.random.random() < health_risk_prob else 0

            features.append([
                age,
                bmi,
                systolic_bp,
                diastolic_bp,
                heart_rate,
                glucose,
                total_chol,
                hdl_chol,
                ldl_chol,
                triglycerides,
                creatinine,
                hba1c,
                smoking,
                alcohol,
                activity,
                family_history
            ])
            labels.append(label)

        X = np.array(features)
        y = np.array(labels)

        # Train the model
        self.model.fit(X, y)
        self.is_trained = True

        logger.info("General health risk model initialized with comprehensive synthetic training data")

    def calculate_category_risks(self, features: Dict[str, Any]) -> Dict[str, float]:
        """Calculate risk scores for each health category"""
        category_risks = {}

        for category, config in self.health_categories.items():
            category_score = 0
            feature_count = 0

            for feature in config['features']:
                if feature in features:
                    value = features[feature]
                    normalized_risk = self._calculate_feature_risk(feature, value)
                    category_score += normalized_risk
                    feature_count += 1

            if feature_count > 0:
                category_risks[category] = category_score / feature_count
            else:
                category_risks[category] = 0.0

        return category_risks

    def _calculate_feature_risk(self, feature_name: str, value: float) -> float:
        """Calculate normalized risk score for individual feature"""
        # Simplified risk calculation for each feature type
        risk_mappings = {
            'systolic_blood_pressure': lambda x: max(0, (x - 120) / 80),
            'diastolic_blood_pressure': lambda x: max(0, (x - 80) / 40),
            'fasting_glucose': lambda x: max(0, (x - 100) / 100),
            'total_cholesterol': lambda x: max(0, (x - 200) / 150),
            'ldl_cholesterol': lambda x: max(0, (x - 100) / 150),
            'hdl_cholesterol': lambda x: max(0, (50 - x) / 30),
            'bmi': lambda x: max(0, (x - 25) / 15),
            'creatinine': lambda x: max(0, (x - 1.2) / 2.0),
            'hemoglobin_a1c': lambda x: max(0, (x - 5.7) / 3.0),
            'smoking_status': lambda x: x * 1.0,
            'age': lambda x: max(0, (x - 40) / 60),
            'alcohol_consumption': lambda x: max(0, (x - 1) / 3),
            'physical_activity_level': lambda x: max(0, (4 - x) / 3),
            'family_history_score': lambda x: x / 5.0
        }

        if feature_name in risk_mappings:
            risk = risk_mappings[feature_name](value)
            return min(risk, 1.0)  # Cap at 1.0

        return 0.0

    def get_health_summary(self, features: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive health summary"""
        category_risks = self.calculate_category_risks(features)

        # Calculate weighted overall risk
        overall_risk = sum(
            category_risks[cat] * config['weight']
            for cat, config in self.health_categories.items()
        )

        return {
            'overall_health_score': 1 - overall_risk,  # Convert risk to health score
            'category_risks': category_risks,
            'risk_level': self._interpret_risk_score(overall_risk),
            'top_risk_categories': sorted(
                category_risks.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        }
