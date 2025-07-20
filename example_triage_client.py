#!/usr/bin/env python3
"""
Example Client for Medical Triage-BOTS API

This script demonstrates how to interact with the refactored /triage endpoint
using various types of medical data (text, structured data, images).

Features:
- Text-only triage cases
- Multi-modal cases with structured data
- Image upload examples
- Error handling and response processing
- Performance timing

Usage:
    python example_triage_client.py --example text
    python example_triage_client.py --example multimodal
    python example_triage_client.py --example image
    python example_triage_client.py --example all
"""

import argparse
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any, Optional
import sys
import os

try:
    import httpx
    import asyncio
except ImportError:
    print("Required packages not installed. Run: pip install httpx")
    sys.exit(1)


class TriageAPIClient:
    """Client for interacting with the Medical Triage-BOTS API"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def health_check(self) -> Dict[str, Any]:
        """Check API health status"""
        try:
            response = await self.client.get(f"{self.base_url}/health")
            return response.json()
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def submit_triage_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit a triage case for processing"""
        start_time = time.time()

        try:
            response = await self.client.post(
                f"{self.base_url}/triage",
                json=case_data,
                headers={"Content-Type": "application/json"}
            )

            processing_time = time.time() - start_time

            if response.status_code == 200:
                result = response.json()
                result["client_processing_time"] = round(processing_time * 1000, 2)
                return result
            else:
                return {
                    "error": True,
                    "status_code": response.status_code,
                    "message": response.text,
                    "processing_time": round(processing_time * 1000, 2)
                }

        except Exception as e:
            return {
                "error": True,
                "message": str(e),
                "processing_time": round((time.time() - start_time) * 1000, 2)
            }

    async def get_metrics(self) -> Dict[str, Any]:
        """Get API performance metrics"""
        try:
            response = await self.client.get(f"{self.base_url}/metrics")
            return response.json()
        except Exception as e:
            return {"error": str(e)}


def create_text_only_case() -> Dict[str, Any]:
    """Create a text-only triage case example"""
    return {
        "patient_info": {
            "patient_id": "P12345",
            "age": 45,
            "gender": "male"
        },
        "symptoms_text": "Experiencing severe chest pain that started 2 hours ago. Pain radiates to left arm and jaw. Also feeling nauseous and sweating profusely.",
        "chief_complaint": "Severe chest pain",
        "medical_history": "Hypertension, family history of heart disease"
    }


def create_multimodal_case() -> Dict[str, Any]:
    """Create a multi-modal case with structured data"""
    return {
        "patient_info": {
            "patient_id": "P67890",
            "age": 65,
            "gender": "female",
            "medical_record_number": "MRN-789456"
        },
        "symptoms_text": "Blurred vision and seeing dark spots for the past week. Also experiencing increased thirst and frequent urination.",
        "chief_complaint": "Vision problems",
        "medical_history": "Type 2 diabetes diagnosed 5 years ago, taking metformin",
        "structured_data": [
            {
                "data_type": "blood_test",
                "data": {
                    "fasting_glucose": 185,
                    "hba1c": 8.7,
                    "total_cholesterol": 240,
                    "ldl_cholesterol": 160,
                    "hdl_cholesterol": 35,
                    "triglycerides": 220
                },
                "units": {
                    "fasting_glucose": "mg/dL",
                    "hba1c": "%",
                    "total_cholesterol": "mg/dL",
                    "ldl_cholesterol": "mg/dL",
                    "hdl_cholesterol": "mg/dL",
                    "triglycerides": "mg/dL"
                },
                "reference_ranges": {
                    "fasting_glucose": {"min": 70, "max": 100},
                    "hba1c": {"min": 4.0, "max": 5.7},
                    "total_cholesterol": {"min": 0, "max": 200}
                },
                "test_date": "2024-12-19T10:30:00Z"
            },
            {
                "data_type": "vital_signs",
                "data": {
                    "blood_pressure_systolic": 145,
                    "blood_pressure_diastolic": 92,
                    "heart_rate": 88,
                    "temperature": 98.4,
                    "respiratory_rate": 18,
                    "oxygen_saturation": 97
                },
                "units": {
                    "blood_pressure_systolic": "mmHg",
                    "blood_pressure_diastolic": "mmHg",
                    "heart_rate": "bpm",
                    "temperature": "°F",
                    "respiratory_rate": "breaths/min",
                    "oxygen_saturation": "%"
                }
            }
        ],
        "images": [
            {
                "image_path": "/uploads/retinal_scan_67890.jpg",
                "image_type": "retinal",
                "file_size": 2048576
            }
        ]
    }


def create_emergency_case() -> Dict[str, Any]:
    """Create a high-priority emergency case"""
    return {
        "patient_info": {
            "patient_id": "P11111",
            "age": 72,
            "gender": "female"
        },
        "symptoms_text": "Sudden onset of severe headache, worst headache of my life. Accompanied by nausea, vomiting, and sensitivity to light. Confusion and difficulty speaking.",
        "chief_complaint": "Worst headache of life",
        "medical_history": "Hypertension, previous stroke 3 years ago",
        "structured_data": [
            {
                "data_type": "vital_signs",
                "data": {
                    "blood_pressure_systolic": 190,
                    "blood_pressure_diastolic": 110,
                    "heart_rate": 95,
                    "temperature": 99.2,
                    "glasgow_coma_scale": 13
                },
                "units": {
                    "blood_pressure_systolic": "mmHg",
                    "blood_pressure_diastolic": "mmHg",
                    "heart_rate": "bpm",
                    "temperature": "°F",
                    "glasgow_coma_scale": "points"
                }
            }
        ],
        "images": [
            {
                "image_path": "/uploads/ct_head_11111.dcm",
                "image_type": "ct_scan",
                "file_size": 15728640
            }
        ]
    }


def create_routine_case() -> Dict[str, Any]:
    """Create a routine, low-priority case"""
    return {
        "patient_info": {
            "patient_id": "P22222",
            "age": 28,
            "gender": "male"
        },
        "symptoms_text": "Mild sore throat for 3 days, slight runny nose, no fever. Able to work and function normally.",
        "chief_complaint": "Sore throat",
        "medical_history": "No significant medical history, seasonal allergies",
        "structured_data": [
            {
                "data_type": "vital_signs",
                "data": {
                    "blood_pressure_systolic": 120,
                    "blood_pressure_diastolic": 75,
                    "heart_rate": 68,
                    "temperature": 98.6,
                    "respiratory_rate": 16
                },
                "units": {
                    "blood_pressure_systolic": "mmHg",
                    "blood_pressure_diastolic": "mmHg",
                    "heart_rate": "bpm",
                    "temperature": "°F",
                    "respiratory_rate": "breaths/min"
                }
            }
        ]
    }


def print_response(response: Dict[str, Any], case_name: str):
    """Pretty print the API response"""
    print(f"\n{'='*60}")
    print(f"📋 {case_name.upper()} CASE RESULT")
    print(f"{'='*60}")

    if response.get("error"):
        print(f"❌ ERROR: {response.get('message', 'Unknown error')}")
        if "status_code" in response:
            print(f"   Status Code: {response['status_code']}")
        print(f"   Processing Time: {response.get('processing_time', 'N/A')}ms")
        return

    # Case information
    print(f"🆔 Case ID: {response.get('case_id', 'N/A')}")
    print(f"📊 Triage Score: {response.get('triage_score', 'N/A')}")
    print(f"🚨 Urgency Level: {response.get('urgency_level', 'N/A').upper()}")
    print(f"⏱️  Estimated Wait: {response.get('estimated_wait_time', 'N/A')} minutes")
    print(f"🕐 Processed At: {response.get('processed_at', 'N/A')}")

    # Processing details
    print(f"\n📈 PROCESSING DETAILS:")
    print(f"   Vision Analysis: {'✅' if response.get('vision_analysis_completed') else '❌'}")
    print(f"   Text Analysis: {'✅' if response.get('text_analysis_completed') else '❌'}")
    print(f"   Structured Analysis: {'✅' if response.get('structured_analysis_completed') else '❌'}")

    # Recommendations
    recommendations = response.get('recommendations', [])
    if recommendations:
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")

    # Timing
    if "client_processing_time" in response:
        print(f"\n⏱️  TIMING:")
        print(f"   Total Processing Time: {response['client_processing_time']}ms")

    # AI Analysis (if available)
    if response.get('synthesized_text_output'):
        print(f"\n🤖 TEXT ANALYSIS:")
        print(f"   {response['synthesized_text_output'][:200]}...")

    if response.get('synthesized_vision_output'):
        print(f"\n👁️  VISION ANALYSIS:")
        print(f"   {response['synthesized_vision_output'][:200]}...")


async def run_example(client: TriageAPIClient, example_type: str):
    """Run a specific example"""

    examples = {
        "text": ("Text-Only Case", create_text_only_case),
        "multimodal": ("Multi-Modal Case", create_multimodal_case),
        "emergency": ("Emergency Case", create_emergency_case),
        "routine": ("Routine Case", create_routine_case)
    }

    if example_type not in examples:
        print(f"❌ Unknown example type: {example_type}")
        return

    case_name, case_func = examples[example_type]
    print(f"\n🏥 Running {case_name} Example...")

    case_data = case_func()
    response = await client.submit_triage_case(case_data)
    print_response(response, case_name)


async def main():
    parser = argparse.ArgumentParser(description="Medical Triage-BOTS API Client Examples")
    parser.add_argument(
        "--example",
        choices=["text", "multimodal", "emergency", "routine", "all"],
        default="text",
        help="Type of example to run"
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="API base URL"
    )
    parser.add_argument(
        "--check-health",
        action="store_true",
        help="Check API health before running examples"
    )

    args = parser.parse_args()

    print("🏥 Medical Triage-BOTS API Client")
    print("="*50)

    async with TriageAPIClient(args.url) as client:

        # Health check
        if args.check_health:
            print("🔍 Checking API health...")
            health = await client.health_check()

            if health.get("status") == "healthy":
                print("✅ API is healthy and ready")
                components = health.get("components", {})
                for component, status in components.items():
                    print(f"   {component}: {status}")
            else:
                print(f"❌ API health check failed: {health}")
                return

        # Run examples
        if args.example == "all":
            examples = ["routine", "text", "multimodal", "emergency"]
            for example in examples:
                await run_example(client, example)
                await asyncio.sleep(1)  # Brief pause between examples
        else:
            await run_example(client, args.example)

        # Show metrics
        print(f"\n📊 API METRICS:")
        print("="*30)
        metrics = await client.get_metrics()
        if "metrics" in metrics:
            app_metrics = metrics["metrics"]
            print(f"Total Requests: {app_metrics.get('total_requests', 0)}")
            print(f"Successful: {app_metrics.get('successful_requests', 0)}")
            print(f"Failed: {app_metrics.get('failed_requests', 0)}")
            print(f"Avg Processing Time: {app_metrics.get('average_processing_time', 0):.1f}ms")
            print(f"Critical Cases: {app_metrics.get('critical_cases', 0)}")
            print(f"High Priority: {app_metrics.get('high_priority_cases', 0)}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Client interrupted by user")
    except Exception as e:
        print(f"\n❌ Client error: {e}")
        sys.exit(1)
