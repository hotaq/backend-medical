"""
Chief-BOT Orchestrator Test Suite

Comprehensive tests for the Chief-BOT orchestrator including:
- Multi-agent coordination
- Async processing
- Error handling
- Scoring algorithms
- Database integration
- Performance validation

Run with: python -m pytest tests/test_chief_bot_orchestrator.py -v
"""

import asyncio
import pytest
import time
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.agents.chief_bot import (
    ChiefBOT,
    AgentResult,
    TriageDecision,
    AgentType,
    create_triage_response
)
from app.models.triage_case import (
    TriageCase,
    UrgencyLevel,
    DataType,
    ImageData,
    StructuredData
)


class TestChiefBOTOrchestrator:
    """Test suite for Chief-BOT orchestrator functionality"""

    @pytest.fixture
    def chief_bot(self):
        """Create a Chief-BOT instance for testing"""
        return ChiefBOT()

    @pytest.fixture
    def sample_triage_case(self):
        """Create a sample triage case for testing"""
        return TriageCase(
            case_id="TEST_001",
            patient_id="P_TEST_001",
            chief_complaint="Test case for orchestrator",
            symptoms_text="Patient presents with test symptoms for validation",
            images=[
                ImageData(
                    image_id="TEST_IMG_001",
                    data_type=DataType.XRAY,
                    file_path="/test/path/xray.jpg",
                    metadata={"view": "PA"}
                )
            ],
            structured_data=[
                StructuredData(
                    data_type=DataType.VITAL_SIGNS,
                    data={
                        "blood_pressure_systolic": 120,
                        "blood_pressure_diastolic": 80,
                        "heart_rate": 72
                    },
                    source="test_monitor"
                )
            ]
        )

    @pytest.fixture
    def mock_agent_results(self):
        """Create mock agent results for testing"""
        return {
            "vision": AgentResult(
                agent_type=AgentType.VISION_BOT,
                success=True,
                raw_output={
                    "prediction_class": 2,
                    "disease": "Normal",
                    "confidence": 0.85,
                    "risk_score": 0.2
                },
                synthesized_output="Vision analysis shows normal findings",
                confidence_score=0.85,
                processing_time_ms=500,
                model_version="test_vision_v1"
            ),
            "text": AgentResult(
                agent_type=AgentType.TEXT_BOT,
                success=True,
                raw_output={
                    "risk_score": 0.3,
                    "keywords_found": ["test"],
                    "recommendations": ["Continue monitoring"]
                },
                synthesized_output="Text analysis indicates low risk",
                confidence_score=0.78,
                processing_time_ms=300,
                model_version="test_text_v1"
            ),
            "structured": AgentResult(
                agent_type=AgentType.STRUCTURED_BOT,
                success=True,
                raw_output={
                    "risk_score": 0.25,
                    "abnormal_values": [],
                    "recommendations": ["Normal values"]
                },
                synthesized_output="Structured data within normal limits",
                confidence_score=0.90,
                processing_time_ms=200,
                model_version="test_structured_v1"
            )
        }

    @pytest.mark.asyncio
    async def test_process_triage_case_success(self, chief_bot, sample_triage_case):
        """Test successful processing of a triage case"""
        # Process the case
        decision = await chief_bot.process_triage_case(sample_triage_case)

        # Validate decision structure
        assert isinstance(decision, TriageDecision)
        assert decision.case_id == sample_triage_case.case_id
        assert 0.0 <= decision.final_triage_score <= 1.0
        assert isinstance(decision.urgency_level, UrgencyLevel)
        assert 0.0 <= decision.confidence_score <= 1.0
        assert isinstance(decision.recommendations, list)
        assert isinstance(decision.reasoning, str)
        assert isinstance(decision.agent_results, dict)
        assert isinstance(decision.processing_summary, dict)

    @pytest.mark.asyncio
    async def test_analyze_processing_requirements(self, chief_bot, sample_triage_case):
        """Test processing requirements analysis"""
        requirements = await chief_bot._analyze_processing_requirements(sample_triage_case)

        assert isinstance(requirements, dict)
        assert "vision_analysis" in requirements
        assert "text_analysis" in requirements
        assert "structured_analysis" in requirements

        # Should require vision analysis (has images)
        assert requirements["vision_analysis"] is True
        # Should require text analysis (has symptoms)
        assert requirements["text_analysis"] is True
        # Should require structured analysis (has structured data)
        assert requirements["structured_analysis"] is True

    @pytest.mark.asyncio
    async def test_coordinate_agents_parallel(self, chief_bot, sample_triage_case):
        """Test parallel agent coordination"""
        requirements = {
            "vision_analysis": True,
            "text_analysis": True,
            "structured_analysis": True
        }

        # Test coordination without actual agents (uses mock agents)
        start_time = time.time()
        agent_results = await chief_bot._coordinate_agents(
            sample_triage_case, requirements
        )
        processing_time = time.time() - start_time

        # Should complete quickly due to parallel execution
        assert processing_time < 1.0  # Should be much faster than sequential

        # Validate results
        assert isinstance(agent_results, dict)
        assert len(agent_results) == 3  # vision, text, structured

        for agent_name, result in agent_results.items():
            assert isinstance(result, AgentResult)
            assert result.success is True  # Mock agents should succeed

    @pytest.mark.asyncio
    async def test_coordinate_agents_with_external_agents(self, chief_bot, sample_triage_case):
        """Test coordination with external agent implementations"""
        # Create mock external agents
        mock_vision_agent = MagicMock()
        mock_vision_agent.process_images = AsyncMock(return_value={
            "raw_output": {"prediction": "test"},
            "synthesized_output": "Test vision result",
            "confidence_score": 0.8
        })

        mock_text_agent = MagicMock()
        mock_text_agent.process_text = AsyncMock(return_value={
            "raw_output": {"risk_score": 0.3},
            "synthesized_output": "Test text result",
            "confidence_score": 0.7
        })

        requirements = {
            "vision_analysis": True,
            "text_analysis": True,
            "structured_analysis": False
        }

        agent_results = await chief_bot._coordinate_agents(
            sample_triage_case, requirements,
            vision_agent=mock_vision_agent,
            text_agent=mock_text_agent
        )

        # Verify external agents were called
        mock_vision_agent.process_images.assert_called_once()
        mock_text_agent.process_text.assert_called_once()

        # Verify results
        assert "vision" in agent_results
        assert "text" in agent_results
        assert "structured" not in agent_results  # Not required

    @pytest.mark.asyncio
    async def test_calculate_final_score(self, chief_bot, mock_agent_results):
        """Test final score calculation algorithm"""
        final_score = await chief_bot._calculate_final_score(mock_agent_results)

        assert isinstance(final_score, float)
        assert 0.0 <= final_score <= 1.0

        # Verify weighted calculation
        # With mock data: vision=0.85*0.35 + text=0.3*0.30 + structured=0.25*0.25
        expected_score = (0.85 * 0.35 + 0.3 * 0.30 + 0.25 * 0.25) / (0.35 + 0.30 + 0.25)
        assert abs(final_score - expected_score) < 0.001

    @pytest.mark.asyncio
    async def test_calculate_final_score_no_agents(self, chief_bot):
        """Test final score calculation with no successful agents"""
        empty_results = {}
        final_score = await chief_bot._calculate_final_score(empty_results)

        # Should return default moderate score
        assert final_score == 0.5

    def test_determine_urgency_level(self, chief_bot):
        """Test urgency level determination"""
        # Test critical level
        assert chief_bot._determine_urgency_level(0.9) == UrgencyLevel.CRITICAL
        assert chief_bot._determine_urgency_level(0.8) == UrgencyLevel.CRITICAL

        # Test high level
        assert chief_bot._determine_urgency_level(0.7) == UrgencyLevel.HIGH
        assert chief_bot._determine_urgency_level(0.6) == UrgencyLevel.HIGH

        # Test medium level
        assert chief_bot._determine_urgency_level(0.5) == UrgencyLevel.MEDIUM
        assert chief_bot._determine_urgency_level(0.4) == UrgencyLevel.MEDIUM

        # Test low level
        assert chief_bot._determine_urgency_level(0.3) == UrgencyLevel.LOW
        assert chief_bot._determine_urgency_level(0.1) == UrgencyLevel.LOW

    def test_calculate_confidence_score(self, chief_bot, mock_agent_results):
        """Test confidence score calculation"""
        confidence = chief_bot._calculate_confidence_score(mock_agent_results)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0

        # Should be average of agent confidences: (0.85 + 0.78 + 0.90) / 3
        expected_confidence = (0.85 + 0.78 + 0.90) / 3
        assert abs(confidence - expected_confidence) < 0.001

    def test_calculate_confidence_score_no_data(self, chief_bot):
        """Test confidence calculation with no agent data"""
        empty_results = {}
        confidence = chief_bot._calculate_confidence_score(empty_results)

        # Should return moderate confidence
        assert confidence == 0.5

    def test_generate_reasoning(self, chief_bot, mock_agent_results):
        """Test reasoning generation"""
        reasoning = chief_bot._generate_reasoning(mock_agent_results, 0.3)

        assert isinstance(reasoning, str)
        assert len(reasoning) > 0
        assert "Vision analysis" in reasoning
        assert "Text analysis" in reasoning
        assert "Structured data analysis" in reasoning

    @pytest.mark.asyncio
    async def test_finalize_decision(self, chief_bot):
        """Test decision finalization"""
        decision = TriageDecision(
            case_id="TEST_FINAL",
            final_triage_score=0.7,
            urgency_level=UrgencyLevel.HIGH,
            confidence_score=0.8,
            recommendations=[],
            reasoning="Test reasoning",
            agent_results={},
            processing_summary={}
        )

        await chief_bot._finalize_decision(decision)

        assert len(decision.recommendations) > 0
        assert any("prompt medical evaluation" in rec.lower() for rec in decision.recommendations)

    @pytest.mark.asyncio
    async def test_error_handling_empty_case(self, chief_bot):
        """Test error handling with minimal case data"""
        minimal_case = TriageCase(
            case_id="MINIMAL",
            patient_id="P_MIN",
            chief_complaint="",
            symptoms_text="",
            images=[],
            structured_data=[]
        )

        decision = await chief_bot.process_triage_case(minimal_case)

        # Should handle gracefully
        assert isinstance(decision, TriageDecision)
        assert decision.case_id == minimal_case.case_id
        # Should provide reasonable defaults
        assert decision.final_triage_score >= 0.0
        assert decision.urgency_level is not None

    @pytest.mark.asyncio
    async def test_timeout_handling(self, chief_bot, sample_triage_case):
        """Test timeout handling for slow agents"""
        # Create mock agent that times out
        slow_agent = MagicMock()
        slow_agent.process_images = AsyncMock()
        slow_agent.process_images.side_effect = asyncio.TimeoutError()

        requirements = {"vision_analysis": True, "text_analysis": False, "structured_analysis": False}

        agent_results = await chief_bot._coordinate_agents(
            sample_triage_case, requirements, vision_agent=slow_agent
        )

        # Should handle timeout gracefully
        assert "vision" in agent_results
        vision_result = agent_results["vision"]
        assert vision_result.success is False
        assert "timeout" in vision_result.error_message.lower()

    @pytest.mark.asyncio
    async def test_agent_exception_handling(self, chief_bot, sample_triage_case):
        """Test handling of agent exceptions"""
        # Create mock agent that raises exception
        failing_agent = MagicMock()
        failing_agent.process_text = AsyncMock()
        failing_agent.process_text.side_effect = ValueError("Test error")

        requirements = {"vision_analysis": False, "text_analysis": True, "structured_analysis": False}

        agent_results = await chief_bot._coordinate_agents(
            sample_triage_case, requirements, text_agent=failing_agent
        )

        # Should handle exception gracefully
        assert "text" in agent_results
        text_result = agent_results["text"]
        assert text_result.success is False
        assert "Test error" in text_result.error_message

    def test_create_triage_response(self, mock_agent_results):
        """Test creation of triage response from decision"""
        decision = TriageDecision(
            case_id="RESP_TEST",
            final_triage_score=0.6,
            urgency_level=UrgencyLevel.HIGH,
            confidence_score=0.8,
            recommendations=["Test recommendation"],
            reasoning="Test reasoning",
            agent_results=mock_agent_results,
            processing_summary={}
        )

        response = create_triage_response(decision)

        assert response.case_id == decision.case_id
        assert response.triage_score == decision.final_triage_score
        assert response.urgency_level == decision.urgency_level
        assert response.recommendations == decision.recommendations
        assert response.estimated_wait_time == 15  # High urgency wait time
        assert response.vision_analysis_completed is True
        assert response.text_analysis_completed is True
        assert response.structured_analysis_completed is True

    @pytest.mark.asyncio
    async def test_performance_parallel_vs_sequential(self, chief_bot, sample_triage_case):
        """Test that parallel processing is faster than sequential"""
        # Test parallel processing
        start_time = time.time()
        await chief_bot.process_triage_case(sample_triage_case)
        parallel_time = time.time() - start_time

        # Simulate sequential processing
        start_time = time.time()
        await chief_bot._mock_vision_agent(sample_triage_case.images)
        await chief_bot._mock_text_agent(sample_triage_case.symptoms_text)
        await chief_bot._mock_structured_agent(sample_triage_case.structured_data)
        sequential_time = time.time() - start_time

        # Parallel should be faster (or at least not significantly slower)
        # Allow for some variance in timing
        assert parallel_time <= sequential_time * 1.1

    @pytest.mark.asyncio
    async def test_scoring_weights_configuration(self):
        """Test custom scoring weights configuration"""
        custom_weights = {
            "vision_confidence": 0.5,
            "text_risk_score": 0.3,
            "structured_risk_score": 0.2,
            "symptom_severity": 0.0
        }

        custom_chief_bot = ChiefBOT(config={"scoring_weights": custom_weights})

        # Verify weights were set
        assert custom_chief_bot.scoring_weights["vision_confidence"] == 0.5

    @pytest.mark.asyncio
    async def test_urgency_threshold_configuration(self):
        """Test custom urgency threshold configuration"""
        custom_thresholds = {
            UrgencyLevel.CRITICAL: 0.9,
            UrgencyLevel.HIGH: 0.7,
            UrgencyLevel.MEDIUM: 0.5,
            UrgencyLevel.LOW: 0.0
        }

        custom_chief_bot = ChiefBOT(config={"urgency_thresholds": custom_thresholds})

        # Test with custom thresholds
        assert custom_chief_bot._determine_urgency_level(0.8) == UrgencyLevel.HIGH
        assert custom_chief_bot._determine_urgency_level(0.95) == UrgencyLevel.CRITICAL

    @pytest.mark.asyncio
    async def test_mock_agents_functionality(self, chief_bot):
        """Test that mock agents provide realistic outputs"""
        # Test vision mock
        vision_result = await chief_bot._mock_vision_agent([ImageData(
            image_id="test", data_type=DataType.RETINAL_SCAN,
            file_path="/test", metadata={}
        )])

        assert vision_result.success is True
        assert vision_result.confidence_score is not None
        assert vision_result.raw_output is not None

        # Test text mock
        text_result = await chief_bot._mock_text_agent("severe chest pain")

        assert text_result.success is True
        assert text_result.raw_output["risk_score"] > 0.5  # Should detect high risk

        # Test structured mock
        structured_result = await chief_bot._mock_structured_agent([
            StructuredData(
                data_type=DataType.LAB_RESULTS,
                data={"glucose": 200},  # High glucose
                source="test"
            )
        ])

        assert structured_result.success is True
        assert structured_result.raw_output["risk_score"] > 0.2  # Should detect elevated glucose


class TestChiefBOTIntegration:
    """Integration tests for Chief-BOT with other system components"""

    @pytest.mark.asyncio
    async def test_end_to_end_processing(self):
        """Test complete end-to-end processing flow"""
        # Create realistic case
        case = TriageCase(
            case_id="E2E_001",
            patient_id="P_E2E",
            chief_complaint="Chest pain and shortness of breath",
            symptoms_text="Patient presents with severe crushing chest pain radiating to left arm, accompanied by shortness of breath and sweating. Symptoms started 1 hour ago.",
            images=[
                ImageData(
                    image_id="ECG_001",
                    data_type=DataType.ECG,
                    file_path="/path/to/ecg.jpg",
                    metadata={"leads": 12}
                )
            ],
            structured_data=[
                StructuredData(
                    data_type=DataType.VITAL_SIGNS,
                    data={
                        "blood_pressure_systolic": 160,
                        "blood_pressure_diastolic": 100,
                        "heart_rate": 110,
                        "oxygen_saturation": 94
                    },
                    source="emergency_monitor"
                )
            ]
        )

        # Process with Chief-BOT
        chief_bot = ChiefBOT()
        decision = await chief_bot.process_triage_case(case)

        # Convert to response
        response = create_triage_response(decision)

        # Validate end-to-end flow
        assert response.case_id == case.case_id
        assert response.processing_status == "completed"

        # Should be high priority due to symptoms
        assert response.urgency_level in [UrgencyLevel.HIGH, UrgencyLevel.CRITICAL]
        assert response.estimated_wait_time <= 15  # Emergency priority

        # Should have processed multiple data types
        assert response.vision_analysis_completed is True
        assert response.text_analysis_completed is True
        assert response.structured_analysis_completed is True

        # Should provide clinical recommendations
        assert len(response.recommendations) > 0
        assert any("medical" in rec.lower() for rec in response.recommendations)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
