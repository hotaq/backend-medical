"""
Debug Script for TextBOT Data Conversion

This script helps debug the data flow between ChiefBOT and TextBOT
to understand why models are returning "insufficient_data".
"""

import sys
import os
import asyncio
import json
from datetime import datetime

# Add the backend app to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.agents.text_bot import TextBOT
from app.models.triage_case import StructuredData, StructuredDataType


async def debug_data_conversion():
    """Debug the data conversion process step by step"""
    print("🔍 Debugging TextBOT Data Conversion")
    print("=" * 60)

    # Create sample structured data
    sample_data = [
        StructuredData(
            data_type=StructuredDataType.BLOOD_TEST,
            data={
                "fasting_glucose": 145,
                "hemoglobin_a1c": 6.2,
                "total_cholesterol": 220,
                "hdl_cholesterol": 35
            },
            units={
                "fasting_glucose": "mg/dL",
                "hemoglobin_a1c": "%",
                "total_cholesterol": "mg/dL",
                "hdl_cholesterol": "mg/dL"
            }
        ),
        StructuredData(
            data_type=StructuredDataType.VITAL_SIGNS,
            data={
                "age": 52,
                "bmi": 31.5,
                "systolic_blood_pressure": 138,
                "diastolic_blood_pressure": 88
            }
        )
    ]

    text_bot = TextBOT()

    print("Step 1: Original StructuredData objects")
    for i, data in enumerate(sample_data):
        print(f"  Data {i+1}:")
        print(f"    Type: {data.data_type}")
        print(f"    Data: {data.data}")
        print(f"    Units: {data.units}")

    # Test data conversion
    print("\nStep 2: Converting to dictionaries")
    data_dicts = text_bot._convert_structured_data(sample_data)
    for i, data_dict in enumerate(data_dicts):
        print(f"  Dict {i+1}:")
        print(f"    Type: {data_dict.get('data_type')}")
        print(f"    Data: {data_dict.get('data')}")

    # Test feature extraction
    print("\nStep 3: Extracting available features")
    available_features = text_bot._extract_available_features(data_dicts)
    print(f"  Available features: {available_features}")

    # Test model selection
    print("\nStep 4: Model selection process")
    model_selection = text_bot._select_models(data_dicts)
    print(f"  Selected models: {model_selection.selected_models}")
    print(f"  Rationale: {model_selection.rationale}")
    print(f"  Confidence: {model_selection.confidence}")

    # Test individual model capability
    print("\nStep 5: Testing individual model capabilities")
    for model_name, model in text_bot.models.items():
        can_predict = model.can_predict(data_dicts)
        required_features = model.get_required_features()
        optional_features = model.get_optional_features()

        print(f"  {model_name}:")
        print(f"    Can predict: {can_predict}")
        print(f"    Required features: {required_features}")
        print(f"    Optional features: {optional_features[:5]}{'...' if len(optional_features) > 5 else ''}")

        if can_predict:
            # Test feature extraction
            try:
                features = model.extract_features(data_dicts)
                print(f"    Extracted features: {features}")
            except Exception as e:
                print(f"    Feature extraction error: {e}")

    # Test full processing
    print("\nStep 6: Full processing test")
    try:
        result = await text_bot.process_structured_data(sample_data)
        print(f"  Success: {result.success}")
        print(f"  Risk score: {result.overall_risk_score}")
        print(f"  Risk category: {result.risk_category}")
        print(f"  Models used: {result.models_used}")
        print(f"  Processing time: {result.processing_time_ms}ms")

        if result.success and result.model_results:
            print("\n  Individual model results:")
            for model_name, model_result in result.model_results.items():
                risk_score = model_result.get('risk_score', 0)
                risk_category = model_result.get('risk_category', 'unknown')
                print(f"    {model_name}: {risk_score:.3f} ({risk_category})")

    except Exception as e:
        print(f"  Processing error: {e}")
        import traceback
        traceback.print_exc()


async def debug_diabetes_model_specifically():
    """Debug diabetes model specifically with known good data"""
    print("\n🩺 Debugging Diabetes Model Specifically")
    print("=" * 60)

    text_bot = TextBOT()
    diabetes_model = text_bot.models['diabetes']

    # Create data that should definitely work for diabetes
    data_dicts = [
        {
            'data_type': 'blood_test',
            'data': {
                'fasting_glucose': 145,  # This should trigger diabetes model
                'age': 52
            },
            'units': {'fasting_glucose': 'mg/dL'},
            'reference_ranges': {},
            'test_date': None
        }
    ]

    print("Data for diabetes model:")
    print(f"  Data: {data_dicts[0]['data']}")

    print("\nDiabetes model analysis:")
    print(f"  Required features: {diabetes_model.get_required_features()}")
    print(f"  Can predict: {diabetes_model.can_predict(data_dicts)}")

    # Test feature extraction
    available_features = []
    for data_dict in data_dicts:
        for key in data_dict.get('data', {}).keys():
            available_features.append(key.lower())

    print(f"  Available features: {available_features}")

    # Check feature normalization
    print("\nFeature normalization test:")
    for feature in available_features:
        normalized = diabetes_model._normalize_feature_name(feature)
        print(f"  '{feature}' -> '{normalized}'")

        is_relevant = diabetes_model._is_relevant_feature(feature, 'blood_test')
        print(f"    Relevant: {is_relevant}")

    # Test manual prediction
    try:
        print("\nTesting manual prediction:")
        result = diabetes_model.predict(data_dicts)
        print(f"  Success: {result is not None}")
        if result:
            print(f"  Risk score: {result.risk_score}")
            print(f"  Risk category: {result.risk_category}")
            print(f"  Features used: {result.features_used}")
            print(f"  Warnings: {result.warnings}")
    except Exception as e:
        print(f"  Prediction error: {e}")
        import traceback
        traceback.print_exc()


async def debug_feature_name_mapping():
    """Debug feature name normalization mapping"""
    print("\n🔍 Debugging Feature Name Mapping")
    print("=" * 60)

    text_bot = TextBOT()
    diabetes_model = text_bot.models['diabetes']

    # Test various feature name variations
    test_features = [
        'fasting_glucose', 'glucose', 'FBS', 'glucose_fasting', 'blood_glucose',
        'hemoglobin_a1c', 'hba1c', 'HbA1c', 'hgba1c',
        'age', 'Age', 'patient_age',
        'bmi', 'BMI', 'body_mass_index',
        'systolic_blood_pressure', 'systolic_bp', 'bp_systolic', 'systolic'
    ]

    print("Feature name normalization test:")
    for feature in test_features:
        normalized = diabetes_model._normalize_feature_name(feature)
        is_required = normalized in diabetes_model.get_required_features()
        is_optional = normalized in diabetes_model.get_optional_features()

        status = "REQUIRED" if is_required else "OPTIONAL" if is_optional else "IGNORED"
        print(f"  '{feature}' -> '{normalized}' [{status}]")


async def main():
    """Run all debug tests"""
    await debug_data_conversion()
    await debug_diabetes_model_specifically()
    await debug_feature_name_mapping()

    print("\n" + "=" * 60)
    print("🎯 Debug Analysis Complete!")
    print("\nNext steps based on findings:")
    print("1. Check if feature normalization is working correctly")
    print("2. Verify required features are being found")
    print("3. Ensure data conversion preserves feature names")
    print("4. Test individual model predictions")


if __name__ == "__main__":
    asyncio.run(main())
