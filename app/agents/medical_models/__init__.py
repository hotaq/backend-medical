"""
Medical Prediction Models Package

This package contains scikit-learn based models for various medical condition predictions.
Each model is designed to work with structured medical data from TriageCase.
"""

from .base_medical_model import BaseMedicalModel
from .diabetes_model import DiabetesRiskModel
from .heart_disease_model import HeartDiseaseRiskModel
from .hypertension_model import HypertensionRiskModel
from .kidney_disease_model import KidneyDiseaseRiskModel
from .general_health_model import GeneralHealthRiskModel

__all__ = [
    "BaseMedicalModel",
    "DiabetesRiskModel",
    "HeartDiseaseRiskModel",
    "HypertensionRiskModel",
    "KidneyDiseaseRiskModel",
    "GeneralHealthRiskModel"
]
