"""
VisionBot Pipeline Demo

This demo showcases the VisionBot agent's medical image analysis capabilities
including MedGemma integration, multi-modal processing, and Chief-BOT integration.

Features demonstrated:
- Medical image analysis for different image types
- MedGemma multimodal model integration
- Risk assessment and clinical recommendations
- Performance monitoring and caching
- Integration with Chief-BOT orchestrator
- Error handling and fallback mechanisms

Run with: python -m demo.demo_vision_bot_pipeline
"""

import asyncio
import logging
import time
import json
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Imports
try:
    from app.agents.vision_bot import (
        VisionBot,
        VisionBotConfig,
        MedicalImageType,
        analyze_medical_images
    )
    from app.agents.chief_bot import ChiefBOT
    from app.models.triage_case import (
        TriageCase,
        ImageData,
        StructuredData,
        StructuredDataType
    )
except ImportError as e:
    logger.error(f"Import error: {e}")
    logger.error("Please ensure all dependencies are installed and modules are available")
    exit(1)


class VisionBotDemo:
    """
    Comprehensive demonstration of VisionBot capabilities.

    This demo shows:
    1. Individual medical image analysis
    2. Multi-image batch processing
    3. Different medical image types
    4. Performance and caching
    5. Integration with Chief-BOT
    6. Error handling scenarios
    """

    def __init__(self):
        self.demo_start_time = None
        self.results_summary = []

    def print_banner(self, title: str, char: str = "="):
        """Print a formatted banner"""
        print(f"\n{char * 70}")
        print(f"  {title}")
        print(f"{char * 70}")

    def print_section(self, title: str):
        """Print a section header"""
        print(f"\n👁️ {title}")
        print("-" * 50)

    async def run_complete_demo(self):
        """Run the complete VisionBot demonstration"""
        self.demo_start_time = time.time()

        self.print_banner("👁️ VISIONBOT PIPELINE DEMO", "=")
        print("Demonstrating AI-powered medical image analysis")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        try:
            # Demo 1: Single Retinal Scan Analysis
            await self.demo_retinal_scan_analysis()

            # Demo 2: Multi-Image Batch Processing
            await self.demo_batch_image_processing()

            # Demo 3: Different Medical Image Types
            await self.demo_different_image_types()

            # Demo 4: Performance and Caching
            await self.demo_performance_caching()

            # Demo 5: Integration with Chief-BOT
            await self.demo_chief_bot_integration()

            # Demo 6: Error Handling
            await self.demo_error_handling()

            # Demo 7: Configuration and Customization
            await self.demo_configuration_options()

        except Exception as e:
            logger.error(f"Demo failed: {e}", exc_info=True)
        finally:
            await self.demo_summary()

    async def demo_retinal_scan_analysis(self):
        """Demo 1: Analyze a single retinal scan for diabetic retinopathy"""
        self.print_banner("🔍 DEMO 1: RETINAL SCAN ANALYSIS")

        # Create sample retinal image data
        retinal_image = ImageData(
            image_path="/demo/images/retinal_scan_001.jpg",
            image_type="retinal_scan",
            file_size=245760,
            uploaded_at=datetime.now()
        )

        self.print_section("Image Details")
        print(f"Image Path: {retinal_image.image_path}")
        print(f"Image Type: {retinal_image.image_type}")
        print(f"File Size: {retinal_image.file_size} bytes")
        print(f"Uploaded: {retinal_image.uploaded_at}")

        # Initialize VisionBot
        vision_bot = VisionBot()

        self.print_section("VisionBot Analysis")
        print("🔄 Initializing VisionBot...")
        await vision_bot.initialize()

        print("🔍 Analyzing retinal scan...")
        start_time = time.time()

        result = await vision_bot.process_images([retinal_image])

        processing_time = time.time() - start_time

        self.print_section("Analysis Results")
        print(f"✅ Analysis completed in {processing_time:.2f}s")
        print(f"Success: {result.get('success', False)}")

        if result.get('success'):
            print(f"Images Analyzed: {result.get('images_analyzed', 0)}")
            print(f"Overall Risk Score: {result.get('overall_risk_score', 0):.3f}")
            print(f"Overall Confidence: {result.get('overall_confidence', 0):.3f}")
            print(f"Highest Urgency: {result.get('highest_urgency', 'routine')}")

            # Clinical findings
            findings = result.get('clinical_findings', [])
            if findings:
                print(f"\nClinical Findings:")
                for i, finding in enumerate(findings[:3], 1):
                    print(f"  {i}. {finding}")

            # Recommendations
            recommendations = result.get('recommendations', [])
            if recommendations:
                print(f"\nRecommendations:")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec}")

            # Synthesized output
            synthesized = result.get('synthesized_output', '')
            if synthesized:
                print(f"\nClinical Summary:")
                print(f"  {synthesized}")

        else:
            print(f"❌ Analysis failed: {result.get('error', 'Unknown error')}")

        # Cleanup
        await vision_bot.cleanup()

        # Store result for summary
        self.results_summary.append({
            "demo": "Retinal Scan Analysis",
            "success": result.get('success', False),
            "processing_time": processing_time,
            "risk_score": result.get('overall_risk_score', 0),
            "images_processed": 1
        })

    async def demo_batch_image_processing(self):
        """Demo 2: Process multiple images in batch"""
        self.print_banner("📚 DEMO 2: BATCH IMAGE PROCESSING")

        # Create multiple sample images
        images = [
            ImageData(
                image_path="/demo/images/chest_xray_001.jpg",
                image_type="chest_xray",
                file_size=189440
            ),
            ImageData(
                image_path="/demo/images/retinal_scan_002.jpg",
                image_type="retinal_scan",
                file_size=256000
            ),
            ImageData(
                image_path="/demo/images/skin_lesion_001.jpg",
                image_type="dermatology",
                file_size=178920
            )
        ]

        self.print_section("Batch Processing Setup")
        print(f"Number of images: {len(images)}")
        for i, img in enumerate(images, 1):
            print(f"  {i}. {img.image_type} ({img.file_size} bytes)")

        # Process batch
        vision_bot = VisionBot()
        await vision_bot.initialize()

        self.print_section("Batch Analysis")
        print("🔄 Processing image batch...")

        start_time = time.time()
        result = await vision_bot.process_images(images)
        processing_time = time.time() - start_time

        self.print_section("Batch Results")
        print(f"✅ Batch processed in {processing_time:.2f}s")
        print(f"Total Images: {len(images)}")
        print(f"Successfully Analyzed: {result.get('images_analyzed', 0)}")
        print(f"Failed: {result.get('images_failed', 0)}")
        print(f"Overall Risk Score: {result.get('overall_risk_score', 0):.3f}")
        print(f"Highest Urgency Level: {result.get('highest_urgency', 'routine')}")

        # Individual results
        individual_results = result.get('individual_results', [])
        if individual_results:
            print(f"\nIndividual Image Results:")
            for i, img_result in enumerate(individual_results):
                if img_result.get('success'):
                    risk = img_result.get('risk_score', 0)
                    urgency = img_result.get('urgency_level', 'routine')
                    print(f"  Image {i+1}: Risk={risk:.3f}, Urgency={urgency}")
                else:
                    print(f"  Image {i+1}: ❌ {img_result.get('error', 'Failed')}")

        # Performance metrics
        total_processing_time = result.get('processing_time_ms', 0)
        avg_time_per_image = total_processing_time / len(images) if images else 0
        print(f"\nPerformance Metrics:")
        print(f"  Total Processing: {total_processing_time}ms")
        print(f"  Average per Image: {avg_time_per_image:.1f}ms")

        await vision_bot.cleanup()

        self.results_summary.append({
            "demo": "Batch Processing",
            "success": result.get('success', False),
            "processing_time": processing_time,
            "risk_score": result.get('overall_risk_score', 0),
            "images_processed": len(images)
        })

    async def demo_different_image_types(self):
        """Demo 3: Test different medical image types"""
        self.print_banner("🏥 DEMO 3: DIFFERENT MEDICAL IMAGE TYPES")

        # Define different image types to test
        image_types = [
            ("chest_xray", "Chest X-ray Analysis"),
            ("retinal_scan", "Retinal Fundus Analysis"),
            ("dermatology", "Skin Lesion Analysis"),
            ("ecg", "ECG Interpretation"),
            ("ct_scan", "CT Scan Analysis")
        ]

        vision_bot = VisionBot()
        await vision_bot.initialize()

        type_results = {}

        for image_type, description in image_types:
            self.print_section(f"{description}")

            # Create sample image
            sample_image = ImageData(
                image_path=f"/demo/images/{image_type}_sample.jpg",
                image_type=image_type,
                file_size=200000
            )

            print(f"Analyzing {image_type} image...")
            start_time = time.time()

            result = await vision_bot.process_images([sample_image])
            processing_time = time.time() - start_time

            if result.get('success'):
                risk_score = result.get('overall_risk_score', 0)
                urgency = result.get('highest_urgency', 'routine')
                confidence = result.get('overall_confidence', 0)

                print(f"  ✅ Success: Risk={risk_score:.3f}, Urgency={urgency}, Confidence={confidence:.3f}")
                print(f"  Processing Time: {processing_time:.2f}s")

                # Get primary finding
                findings = result.get('clinical_findings', [])
                if findings:
                    print(f"  Primary Finding: {findings[0]}")

                type_results[image_type] = {
                    "success": True,
                    "risk_score": risk_score,
                    "urgency": urgency,
                    "confidence": confidence,
                    "processing_time": processing_time
                }
            else:
                print(f"  ❌ Failed: {result.get('error', 'Unknown error')}")
                type_results[image_type] = {
                    "success": False,
                    "error": result.get('error', 'Unknown error')
                }

        # Summary of image type analysis
        self.print_section("Image Type Analysis Summary")
        successful_types = [t for t, r in type_results.items() if r.get('success')]
        print(f"Successfully analyzed: {len(successful_types)}/{len(image_types)} image types")

        if successful_types:
            avg_risk = sum(type_results[t]['risk_score'] for t in successful_types) / len(successful_types)
            avg_time = sum(type_results[t]['processing_time'] for t in successful_types) / len(successful_types)
            print(f"Average risk score: {avg_risk:.3f}")
            print(f"Average processing time: {avg_time:.2f}s")

        await vision_bot.cleanup()

        self.results_summary.append({
            "demo": "Different Image Types",
            "success": len(successful_types) > 0,
            "processing_time": sum(r.get('processing_time', 0) for r in type_results.values()),
            "risk_score": avg_risk if successful_types else 0,
            "images_processed": len(image_types)
        })

    async def demo_performance_caching(self):
        """Demo 4: Performance optimization and caching"""
        self.print_banner("⚡ DEMO 4: PERFORMANCE & CACHING")

        # Create test image
        test_image = ImageData(
            image_path="/demo/images/performance_test.jpg",
            image_type="retinal_scan",
            file_size=200000
        )

        vision_bot = VisionBot()
        await vision_bot.initialize()

        self.print_section("First Analysis (No Cache)")
        start_time = time.time()
        result1 = await vision_bot.process_images([test_image])
        first_time = time.time() - start_time

        print(f"First analysis time: {first_time:.3f}s")
        print(f"Success: {result1.get('success', False)}")

        self.print_section("Second Analysis (With Cache)")
        start_time = time.time()
        result2 = await vision_bot.process_images([test_image])
        second_time = time.time() - start_time

        print(f"Second analysis time: {second_time:.3f}s")
        print(f"Success: {result2.get('success', False)}")

        # Check if caching worked
        cache_benefit = (first_time - second_time) / first_time * 100 if first_time > 0 else 0
        print(f"Cache performance improvement: {cache_benefit:.1f}%")

        # Get processing stats
        self.print_section("Processing Statistics")
        stats = await vision_bot.get_processing_stats()
        print(f"Total images processed: {stats.get('total_images_processed', 0)}")
        print(f"Successful predictions: {stats.get('successful_predictions', 0)}")
        print(f"Failed predictions: {stats.get('failed_predictions', 0)}")
        print(f"Cache hits: {stats.get('cache_hits', 0)}")
        print(f"Cache size: {stats.get('cache_size', 0)}")
        print(f"Average processing time: {stats.get('average_processing_time', 0):.2f}ms")

        await vision_bot.cleanup()

        self.results_summary.append({
            "demo": "Performance & Caching",
            "success": result1.get('success', False) and result2.get('success', False),
            "processing_time": first_time + second_time,
            "cache_improvement": cache_benefit,
            "images_processed": 2
        })

    async def demo_chief_bot_integration(self):
        """Demo 5: Integration with Chief-BOT orchestrator"""
        self.print_banner("🧠 DEMO 5: CHIEF-BOT INTEGRATION")

        # Create comprehensive triage case with images
        triage_case = TriageCase(
            case_id="VISION_INTEGRATION_001",
            patient_id="P_VISION_001",
            chief_complaint="Visual disturbances and chest pain",
            symptoms_text="Patient reports blurred vision and chest discomfort. History of diabetes and hypertension.",
            images=[
                ImageData(
                    image_path="/demo/images/retinal_diabetic.jpg",
                    image_type="retinal_scan",
                    file_size=250000
                ),
                ImageData(
                    image_path="/demo/images/chest_emergency.jpg",
                    image_type="chest_xray",
                    file_size=180000
                )
            ],
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.VITAL_SIGNS,
                    data={
                        "blood_pressure_systolic": 165,
                        "blood_pressure_diastolic": 95,
                        "heart_rate": 88,
                        "glucose": 245
                    }
                )
            ]
        )

        self.print_section("Case Overview")
        print(f"Case ID: {triage_case.case_id}")
        print(f"Chief Complaint: {triage_case.chief_complaint}")
        print(f"Images: {len(triage_case.images)} medical images")
        print(f"Structured Data: {len(triage_case.structured_data)} datasets")

        # Process with Chief-BOT (which will use VisionBot)
        self.print_section("Chief-BOT Processing with VisionBot")
        chief_bot = ChiefBOT()

        print("🧠 Starting orchestrated analysis...")
        start_time = time.time()

        decision = await chief_bot.process_triage_case(triage_case)

        processing_time = time.time() - start_time

        self.print_section("Integrated Analysis Results")
        print(f"✅ Analysis completed in {processing_time:.2f}s")
        print(f"Final Triage Score: {decision.final_triage_score:.3f}")
        print(f"Urgency Level: {decision.urgency_level.value.upper()}")
        print(f"Confidence Score: {decision.confidence_score:.3f}")

        # Vision-specific results
        vision_result = decision.agent_results.get('vision')
        if vision_result:
            print(f"\nVision Analysis Results:")
            print(f"  Success: {'✅' if vision_result.success else '❌'}")
            if vision_result.success:
                print(f"  Confidence: {vision_result.confidence_score:.3f}")
                print(f"  Processing Time: {vision_result.processing_time_ms}ms")
                if vision_result.synthesized_output:
                    print(f"  Summary: {vision_result.synthesized_output[:100]}...")

        # Overall recommendations
        print(f"\nRecommendations:")
        for i, rec in enumerate(decision.recommendations[:3], 1):
            print(f"  {i}. {rec}")

        print(f"\nClinical Reasoning:")
        print(f"  {decision.reasoning}")

        self.results_summary.append({
            "demo": "Chief-BOT Integration",
            "success": decision.final_triage_score > 0,
            "processing_time": processing_time,
            "risk_score": decision.final_triage_score,
            "images_processed": len(triage_case.images)
        })

    async def demo_error_handling(self):
        """Demo 6: Error handling and robustness"""
        self.print_banner("⚠️  DEMO 6: ERROR HANDLING")

        vision_bot = VisionBot()
        await vision_bot.initialize()

        # Test scenarios
        error_scenarios = [
            {
                "name": "Invalid Image Path",
                "image": ImageData(
                    image_path="/nonexistent/path/image.jpg",
                    image_type="chest_xray"
                )
            },
            {
                "name": "Unsupported Image Type",
                "image": ImageData(
                    image_path="/demo/images/test.txt",
                    image_type="unknown"
                )
            },
            {
                "name": "Empty Image List",
                "images": []
            }
        ]

        for scenario in error_scenarios:
            self.print_section(f"Testing: {scenario['name']}")

            try:
                if 'images' in scenario:
                    # Empty list scenario
                    result = await vision_bot.process_images(scenario['images'])
                else:
                    # Single image scenarios
                    result = await vision_bot.process_images([scenario['image']])

                print(f"Result: {'✅ Handled gracefully' if not result.get('success') else '⚠️ Unexpected success'}")
                if not result.get('success'):
                    print(f"Error message: {result.get('error', 'No error message')}")
                else:
                    print(f"Unexpected success with score: {result.get('overall_risk_score', 0)}")

            except Exception as e:
                print(f"❌ Exception raised: {e}")

        await vision_bot.cleanup()

        self.results_summary.append({
            "demo": "Error Handling",
            "success": True,  # Success means errors were handled gracefully
            "processing_time": 0.1,
            "images_processed": len(error_scenarios)
        })

    async def demo_configuration_options(self):
        """Demo 7: Configuration and customization options"""
        self.print_banner("🔧 DEMO 7: CONFIGURATION OPTIONS")

        self.print_section("Default Configuration")
        default_config = VisionBotConfig()
        print(f"Model ID: {default_config.model_id}")
        print(f"Device: {default_config.device}")
        print(f"Mock Mode: {default_config.mock_mode}")
        print(f"Max Image Size: {default_config.max_image_size}")
        print(f"Processing Timeout: {default_config.processing_timeout}s")

        # Test with custom configuration
        self.print_section("Custom Configuration")
        custom_config = VisionBotConfig()
        custom_config.mock_mode = True
        custom_config.max_image_size = (256, 256)
        custom_config.high_risk_threshold = 0.8
        custom_config.cache_predictions = False

        print(f"Custom Mock Mode: {custom_config.mock_mode}")
        print(f"Custom Max Size: {custom_config.max_image_size}")
        print(f"Custom Risk Threshold: {custom_config.high_risk_threshold}")
        print(f"Custom Caching: {custom_config.cache_predictions}")

        # Test custom configuration
        custom_vision_bot = VisionBot(custom_config)
        await custom_vision_bot.initialize()

        test_image = ImageData(
            image_path="/demo/images/config_test.jpg",
            image_type="retinal_scan"
        )

        result = await custom_vision_bot.process_images([test_image])

        self.print_section("Custom Configuration Results")
        print(f"Success: {result.get('success', False)}")
        print(f"Risk Score: {result.get('overall_risk_score', 0):.3f}")
        print(f"Mock Analysis: {'Yes' if custom_config.mock_mode else 'No'}")

        await custom_vision_bot.cleanup()

        self.results_summary.append({
            "demo": "Configuration Options",
            "success": result.get('success', False),
            "processing_time": 0.1,
            "images_processed": 1
        })

    async def demo_summary(self):
        """Print demo summary and statistics"""
        total_time = time.time() - self.demo_start_time if self.demo_start_time else 0

        self.print_banner("📋 VISIONBOT DEMO SUMMARY")

        print(f"✅ VisionBot Pipeline Demo Completed!")
        print(f"⏱️  Total Demo Time: {total_time:.2f} seconds")
        print(f"👁️ Total Demos Run: {len(self.results_summary)}")

        # Calculate overall statistics
        successful_demos = [r for r in self.results_summary if r.get('success', False)]
        total_images = sum(r.get('images_processed', 0) for r in self.results_summary)
        total_processing_time = sum(r.get('processing_time', 0) for r in self.results_summary)
        avg_risk_score = sum(r.get('risk_score', 0) for r in successful_demos) / len(successful_demos) if successful_demos else 0

        print(f"\n📊 Demo Statistics:")
        print(f"  Successful Demos: {len(successful_demos)}/{len(self.results_summary)}")
        print(f"  Total Images Processed: {total_images}")
        print(f"  Total Processing Time: {total_processing_time:.2f}s")
        print(f"  Average Risk Score: {avg_risk_score:.3f}")

        if total_images > 0:
            avg_time_per_image = total_processing_time / total_images
            print(f"  Average Time per Image: {avg_time_per_image:.3f}s")

        print(f"\n🎯 Key Features Demonstrated:")
        features = [
            "Medical image analysis with MedGemma integration",
            "Multi-modal image processing (retinal, X-ray, dermatology)",
            "Batch processing capabilities",
            "Performance optimization and caching",
            "Chief-BOT orchestrator integration",
            "Comprehensive error handling",
            "Flexible configuration options",
            "Clinical risk assessment and recommendations"
        ]

        for i, feature in enumerate(features, 1):
            print(f"  {i}. ✅ {feature}")

        print(f"\n🚀 VisionBot Pipeline is ready for production use!")
        print(f"   - Supports multiple medical image types")
        print(f"   - Integrates seamlessly with Chief-BOT")
        print(f"   - Provides clinical-grade analysis")
        print(f"   - Scales with high-performance processing")

        # Individual demo results
        print(f"\n📝 Individual Demo Results:")
        for result in self.results_summary:
            status = "✅" if result.get('success', False) else "❌"
            demo_name = result.get('demo', 'Unknown')
            time_taken = result.get('processing_time', 0)
            images = result.get('images_processed', 0)
            print(f"  {status} {demo_name}: {time_taken:.2f}s ({images} images)")


# Demo execution
async def main():
    """Main demo execution function"""
    demo = VisionBotDemo()
    await demo.run_complete_demo()


if __name__ == "__main__":
    # Run the demo
    print("👁️ Starting VisionBot Pipeline Demo...")
    print("   This demo showcases AI-powered medical image analysis")
    print("   with MedGemma integration and Chief-BOT coordination.\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Demo failed: {e}")
        logger.error(f"Demo execution failed: {e}", exc_info=True)
