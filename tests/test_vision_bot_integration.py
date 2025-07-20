"""
VisionBot Integration Tests

Test suite for VisionBot agent functionality and integration with Chief-BOT.

Run with: python -m pytest tests/test_vision_bot_integration.py -v
"""

import asyncio
import pytest
import base64
import io
from PIL import Image
from unittest.mock import patch, MagicMock

from app.agents.vision_bot import (
    VisionBot,
    VisionBotConfig,
    MedicalImageType,
    ImageProcessor
)
from app.agents.chief_bot import ChiefBOT
from app.models.triage_case import (
    TriageCase,
    ImageData,
    StructuredData,
    StructuredDataType
)


class TestVisionBotBasic:
    """Basic VisionBot functionality tests"""

    @pytest.fixture
    def vision_bot_config(self):
        """Create test configuration"""
        config = VisionBotConfig()
        config.mock_mode = True  # Always use mock mode for tests
        return config

    @pytest.fixture
    def vision_bot(self, vision_bot_config):
        """Create VisionBot instance for testing"""
        return VisionBot(vision_bot_config)

    @pytest.fixture
    def mock_image_data(self):
        """Create mock base64 image data"""
        # Create simple test image
        image = Image.new('RGB', (100, 100), color='red')
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return ImageData(
            image_path=f"data:image/png;base64,{img_str}",
            image_type="retinal_scan",
            file_size=len(img_str)
        )

    @pytest.mark.asyncio
    async def test_vision_bot_initialization(self, vision_bot):
        """Test VisionBot initialization"""
        assert not vision_bot.is_initialized

        result = await vision_bot.initialize()

        assert result is True
        assert vision_bot.is_initialized
        assert vision_bot.config.mock_mode is True

    @pytest.mark.asyncio
    async def test_vision_bot_mock_analysis(self, vision_bot, mock_image_data):
        """Test mock image analysis"""
        await vision_bot.initialize()

        result = await vision_bot.process_images([mock_image_data])

        assert result['success'] is True
        assert 'overall_risk_score' in result
        assert 'overall_confidence' in result
        assert 'individual_results' in result
        assert len(result['individual_results']) == 1

        individual = result['individual_results'][0]
        assert individual['success'] is True
        assert 'image_type' in individual
        assert 'predicted_class' in individual
        assert 'confidence' in individual
        assert 'clinical_findings' in individual
        assert 'recommendations' in individual

    @pytest.mark.asyncio
    async def test_vision_bot_multiple_images(self, vision_bot):
        """Test processing multiple images"""
        await vision_bot.initialize()

        images = [
            ImageData(
                image_path="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                image_type="retinal_scan"
            ),
            ImageData(
                image_path="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                image_type="chest_xray"
            )
        ]

        result = await vision_bot.process_images(images)

        assert result['success'] is True
        assert result['images_analyzed'] == 2
        assert len(result['individual_results']) == 2

    @pytest.mark.asyncio
    async def test_vision_bot_error_handling(self, vision_bot):
        """Test error handling with invalid inputs"""
        await vision_bot.initialize()

        # Test empty image list
        result = await vision_bot.process_images([])
        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_vision_bot_cleanup(self, vision_bot):
        """Test VisionBot cleanup"""
        await vision_bot.initialize()
        await vision_bot.cleanup()

        assert vision_bot.is_initialized is False
        assert vision_bot.model is None
        assert vision_bot.processor is None


class TestImageProcessor:
    """Test image processing utilities"""

    @pytest.fixture
    def config(self):
        return VisionBotConfig()

    @pytest.fixture
    def processor(self, config):
        return ImageProcessor(config)

    def test_detect_image_type(self, processor):
        """Test image type detection"""
        # Test retinal scan detection
        retinal_data = ImageData(
            image_path="/path/to/retinal.jpg",
            image_type="retinal_scan"
        )
        assert processor.detect_image_type(retinal_data) == MedicalImageType.RETINAL_SCAN

        # Test chest X-ray detection
        chest_data = ImageData(
            image_path="/path/to/chest_xray.jpg",
            image_type="chest_xray"
        )
        assert processor.detect_image_type(chest_data) == MedicalImageType.CHEST_XRAY

        # Test generic fallback
        generic_data = ImageData(
            image_path="/path/to/unknown.jpg",
            image_type="unknown"
        )
        assert processor.detect_image_type(generic_data) == MedicalImageType.GENERIC

    def test_validate_image_path(self, processor):
        """Test image path validation"""
        # Valid paths would require actual files, so test invalid paths
        assert processor.validate_image_path("/nonexistent/path.jpg") is False
        assert processor.validate_image_path("invalid_path") is False

    def test_load_image_from_base64(self, processor):
        """Test loading image from base64"""
        # Create simple 1x1 PNG image in base64
        base64_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="

        image = processor.load_image_from_base64(base64_data)
        assert image is not None
        assert image.mode == 'RGB'
        assert image.size == (1, 1)

        # Test with data URL prefix
        data_url = f"data:image/png;base64,{base64_data}"
        image2 = processor.load_image_from_base64(data_url)
        assert image2 is not None


class TestChiefBotVisionIntegration:
    """Test VisionBot integration with Chief-BOT"""

    @pytest.fixture
    def chief_bot(self):
        """Create Chief-BOT instance"""
        return ChiefBOT()

    @pytest.fixture
    def vision_triage_case(self):
        """Create triage case with vision data"""
        return TriageCase(
            case_id="VISION_TEST_001",
            patient_id="P_TEST_001",
            chief_complaint="Vision problems and diabetes management",
            symptoms_text="Patient with diabetes reporting blurred vision and retinal changes",
            images=[
                ImageData(
                    image_path="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
                    image_type="retinal_scan",
                    file_size=1000
                )
            ],
            structured_data=[
                StructuredData(
                    data_type=StructuredDataType.VITAL_SIGNS,
                    data={
                        "blood_pressure_systolic": 140,
                        "blood_pressure_diastolic": 90,
                        "glucose": 180
                    }
                )
            ]
        )

    @pytest.mark.asyncio
    async def test_chief_bot_vision_integration(self, chief_bot, vision_triage_case):
        """Test Chief-BOT processing with vision data"""
        decision = await chief_bot.process_triage_case(vision_triage_case)

        # Verify decision structure
        assert decision.case_id == vision_triage_case.case_id
        assert 0.0 <= decision.final_triage_score <= 1.0
        assert decision.urgency_level is not None
        assert 0.0 <= decision.confidence_score <= 1.0
        assert isinstance(decision.recommendations, list)
        assert isinstance(decision.reasoning, str)

        # Verify vision agent was used
        assert 'vision' in decision.agent_results
        vision_result = decision.agent_results['vision']

        # Check if vision processing was attempted (success or graceful failure)
        assert hasattr(vision_result, 'agent_type')
        assert hasattr(vision_result, 'success')

    @pytest.mark.asyncio
    async def test_chief_bot_vision_scoring_contribution(self, chief_bot, vision_triage_case):
        """Test that vision analysis contributes to final scoring"""
        decision = await chief_bot.process_triage_case(vision_triage_case)

        # Vision should be included in processing requirements
        requirements = vision_triage_case.get_processing_requirements()
        assert requirements['vision_analysis'] is True

        # Final score should be calculated
        assert decision.final_triage_score > 0

        # Processing summary should include vision processing
        summary = decision.processing_summary
        assert 'agents_executed' in summary
        assert summary['agents_executed'] >= 1  # At least one agent should execute

    @pytest.mark.asyncio
    async def test_chief_bot_no_images(self, chief_bot):
        """Test Chief-BOT with case containing no images"""
        case_no_images = TriageCase(
            case_id="NO_VISION_001",
            patient_id="P_NO_VISION",
            chief_complaint="Headache",
            symptoms_text="Patient reports mild headache",
            images=[],  # No images
            structured_data=[]
        )

        decision = await chief_bot.process_triage_case(case_no_images)

        # Should still process successfully
        assert decision.case_id == case_no_images.case_id
        assert decision.final_triage_score >= 0

        # Vision agent should not be executed
        requirements = case_no_images.get_processing_requirements()
        assert requirements['vision_analysis'] is False

        # Vision should not be in agent results
        assert 'vision' not in decision.agent_results or not decision.agent_results['vision'].success


class TestVisionBotConfiguration:
    """Test VisionBot configuration options"""

    def test_default_config(self):
        """Test default configuration"""
        config = VisionBotConfig()

        assert config.model_id == "google/medgemma-4b-it"
        assert config.device in ["cuda", "cpu"]
        assert config.max_image_size == (512, 512)
        assert config.mock_mode is True  # Default for development

    def test_custom_config(self):
        """Test custom configuration"""
        config = VisionBotConfig()
        config.max_image_size = (256, 256)
        config.high_risk_threshold = 0.8
        config.cache_predictions = False

        assert config.max_image_size == (256, 256)
        assert config.high_risk_threshold == 0.8
        assert config.cache_predictions is False

    @pytest.mark.asyncio
    async def test_vision_bot_with_custom_config(self):
        """Test VisionBot with custom configuration"""
        custom_config = VisionBotConfig()
        custom_config.mock_mode = True
        custom_config.cache_predictions = False

        vision_bot = VisionBot(custom_config)
        await vision_bot.initialize()

        assert vision_bot.config.cache_predictions is False
        assert vision_bot.config.mock_mode is True

        await vision_bot.cleanup()


class TestVisionBotPerformance:
    """Test VisionBot performance characteristics"""

    @pytest.mark.asyncio
    async def test_processing_stats(self):
        """Test processing statistics tracking"""
        vision_bot = VisionBot()
        await vision_bot.initialize()

        # Initial stats
        stats = await vision_bot.get_processing_stats()
        initial_count = stats['total_images_processed']

        # Process some images
        test_image = ImageData(
            image_path="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            image_type="retinal_scan"
        )

        await vision_bot.process_images([test_image])

        # Check updated stats
        updated_stats = await vision_bot.get_processing_stats()
        assert updated_stats['total_images_processed'] > initial_count
        assert updated_stats['successful_predictions'] >= 0

        await vision_bot.cleanup()

    @pytest.mark.asyncio
    async def test_cache_functionality(self):
        """Test prediction caching"""
        config = VisionBotConfig()
        config.cache_predictions = True
        config.mock_mode = True

        vision_bot = VisionBot(config)
        await vision_bot.initialize()

        test_image = ImageData(
            image_path="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg==",
            image_type="retinal_scan"
        )

        # First processing
        result1 = await vision_bot.process_images([test_image])

        # Second processing (should use cache)
        result2 = await vision_bot.process_images([test_image])

        # Both should succeed
        assert result1['success'] is True
        assert result2['success'] is True

        # Check cache stats
        stats = await vision_bot.get_processing_stats()
        assert stats['cache_hits'] >= 0

        await vision_bot.cleanup()


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
