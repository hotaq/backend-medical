"""
Tests package for the Medical Triage-BOTS system.

This package contains all test modules for validating the functionality,
performance, and reliability of the Medical Triage-BOTS application.
"""

__version__ = "1.0.0"
__author__ = "Medical Triage-BOTS Team"

# Test configuration
TEST_DATA_DIR = "test_data"
FIXTURES_DIR = "fixtures"

# Test categories
__all__ = [
    "test_triage_case_model",
    "test_agents",
    "test_api",
    "test_ml_models",
    "test_database"
]
