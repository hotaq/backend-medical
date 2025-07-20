"""
Chief-BOT Orchestrator for Medical Triage-BOTS System

This module implements the Chief-BOT, which serves as the main coordination engine
for the multi-agent medical triage system. It orchestrates VisionBOT and TextBOT
agents using async coordination and calculates final triage scores.

Features:
- Async agent coordination using asyncio.gather
- Decision-making logic for agent routing
- Final triage score calculation algorithm
- Integration with database logging
- Comprehensive error handling and monitoring
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from ..models.triage_case import (
    TriageCase as PydanticTriageCase,
    TriageCaseResponse,
    UrgencyLevel,
    DataType
)
from ..models.pydantic_compat import model_dump
from .text_bot import TextBOT
from .vision_bot import VisionBot, VisionBotConfig


logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Types of agents in the system"""
    VISION_BOT = "vision_bot"
    TEXT_BOT = "text_bot"
    STRUCTURED_BOT = "structured_bot"
    CHIEF_BOT = "chief_bot"


class ProcessingPhase(str, Enum):
    """Processing phases in the workflow"""
    ANALYSIS = "analysis"
    COORDINATION = "coordination"
    SYNTHESIS = "synthesis"
    FINALIZATION = "finalization"


@dataclass
class AgentResult:
    """Result from an agent processing step"""
    agent_type: AgentType
    success: bool
    raw_output: Optional[Dict[str, Any]] = None
    synthesized_output: Optional[str] = None
    confidence_score: Optional[float] = None
    processing_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    model_version: Optional[str] = None


@dataclass
class TriageDecision:
    """Final triage decision from Chief-BOT"""
    case_id: str
    final_triage_score: float
    urgency_level: UrgencyLevel
    confidence_score: float
    recommendations: List[str]
    reasoning: str
    agent_results: Dict[str, AgentResult]
    processing_summary: Dict[str, Any]


class ChiefBOT:
    """
    Chief-BOT Orchestrator - The main coordination engine for medical triage.

    Responsibilities:
    1. Analyze incoming TriageCase to determine processing requirements
    2. Coordinate VisionBOT and TextBOT agents using async execution
    3. Synthesize results from multiple agents
    4. Calculate final triage scores and urgency levels
    5. Generate clinical recommendations
    6. Log all processing steps for audit and analytics
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Chief-BOT orchestrator.

        Args:
            config: Configuration parameters for the orchestrator
        """
        self.config = config or {}
        self.version = "1.0.0"

        # Scoring algorithm parameters
        self.scoring_weights = {
            "vision_confidence": 0.35,      # Weight for vision analysis confidence
            "text_risk_score": 0.30,        # Weight for text analysis risk
            "structured_risk_score": 0.25,  # Weight for structured data risk
            "symptom_severity": 0.10        # Weight for symptom text analysis
        }

        # Urgency thresholds
        self.urgency_thresholds = {
            UrgencyLevel.CRITICAL: 0.80,
            UrgencyLevel.HIGH: 0.60,
            UrgencyLevel.MEDIUM: 0.40,
            UrgencyLevel.LOW: 0.00
        }

        # Processing timeout settings (in seconds)
        self.timeouts = {
            "vision_agent": 30,
            "text_agent": 20,
            "structured_agent": 15,
            "total_processing": 60
        }

        # Initialize agents
        self.text_bot = TextBOT()
        logger.info(f"TextBOT initialized in ChiefBOT: {self.text_bot.agent_name}")

        logger.info(f"Chief-BOT initialized with config: {self.config}")
    async def process_triage_case(
        self,
        triage_case: PydanticTriageCase,
        vision_agent=None,
        text_agent=None,
        structured_agent=None
    ) -> TriageDecision:
        """
        Main orchestration method for processing a triage case.

        Args:
            triage_case: The case to process
            vision_agent: VisionBOT agent instance (optional, for testing)
            text_agent: TextBOT agent instance (optional, for testing)
            structured_agent: Structured data agent instance (optional, for testing)

        Returns:
            TriageDecision: Complete triage decision with scores and recommendations
        """
        start_time = time.time()
        case_id = triage_case.case_id or f"CASE_{int(time.time())}"

        logger.info(f"Chief-BOT starting processing for case: {case_id}")

        try:
            # Phase 1: Analysis - Determine what processing is needed
            processing_requirements = await self._analyze_processing_requirements(triage_case)
            logger.info(f"Case {case_id} processing requirements: {processing_requirements}")

            # Phase 2: Coordination - Execute agents in parallel
            agent_results = await self._coordinate_agents(
                triage_case, processing_requirements, vision_agent, text_agent, structured_agent
            )

            # Phase 3: Synthesis - Combine results and calculate final score
            triage_decision = await self._synthesize_results(
                triage_case, agent_results, start_time
            )

            # Phase 4: Finalization - Generate final recommendations
            await self._finalize_decision(triage_decision)

            total_time = int((time.time() - start_time) * 1000)
            logger.info(f"Chief-BOT completed processing for case {case_id} in {total_time}ms")
            logger.info(f"Final triage score: {triage_decision.final_triage_score:.3f}, "
                       f"urgency: {triage_decision.urgency_level.value}")

            return triage_decision

        except Exception as e:
            error_msg = f"Chief-BOT processing failed for case {case_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)

            # Return error decision
            return TriageDecision(
                case_id=case_id,
                final_triage_score=0.5,  # Default moderate score for errors
                urgency_level=UrgencyLevel.MEDIUM,
                confidence_score=0.0,
                recommendations=["Manual review required due to processing error"],
                reasoning=f"Processing error: {str(e)}",
                agent_results={},
                processing_summary={"error": str(e), "processing_time_ms": int((time.time() - start_time) * 1000)}
            )

    async def _analyze_processing_requirements(
        self, triage_case: PydanticTriageCase
    ) -> Dict[str, bool]:
        """
        Analyze the triage case to determine which agents need to process it.

        Args:
            triage_case: Case to analyze

        Returns:
            Dict mapping agent types to whether they should process the case
        """
        requirements = triage_case.get_processing_requirements()

        # Add any additional logic here for determining processing needs
        # based on case content, patient history, etc.

        return {
            "vision_analysis": requirements["vision_analysis"],
            "text_analysis": requirements["text_analysis"],
            "structured_analysis": requirements["structured_analysis"]
        }

    async def _coordinate_agents(
        self,
        triage_case: PydanticTriageCase,
        requirements: Dict[str, bool],
        vision_agent=None,
        text_agent=None,
        structured_agent=None
    ) -> Dict[str, AgentResult]:
        """
        Coordinate multiple agents using async execution.

        Args:
            triage_case: Case to process
            requirements: Which agents should process the case
            vision_agent: VisionBOT agent instance
            text_agent: TextBOT agent instance
            structured_agent: Structured data agent instance

        Returns:
            Dict mapping agent types to their results
        """
        logger.info(f"Coordinating agents for case {triage_case.case_id}")

        # Prepare agent tasks
        tasks = []
        task_names = []

        if requirements["vision_analysis"] and triage_case.images:
            if vision_agent:
                task = asyncio.create_task(
                    self._run_agent_with_timeout(
                        vision_agent.process_images,
                        triage_case.images,
                        AgentType.VISION_BOT,
                        self.timeouts["vision_agent"]
                    )
                )
            else:
                # Use real VisionBot agent
                task = asyncio.create_task(
                    self._run_vision_agent(triage_case.images)
                )
            tasks.append(task)
            task_names.append("vision")

        if requirements["text_analysis"] and (triage_case.symptoms_text or triage_case.chief_complaint):
            if text_agent:
                task = asyncio.create_task(
                    self._run_agent_with_timeout(
                        text_agent.process_text,
                        triage_case.symptoms_text or triage_case.chief_complaint,
                        AgentType.TEXT_BOT,
                        self.timeouts["text_agent"]
                    )
                )
            else:
                # Use real TextBOT agent
                task = asyncio.create_task(
                    self._real_text_agent(triage_case)
                )
            tasks.append(task)
            task_names.append("text")

        if requirements["structured_analysis"] and triage_case.structured_data:
            if structured_agent:
                task = asyncio.create_task(
                    self._run_agent_with_timeout(
                        structured_agent.process_structured_data,
                        triage_case.structured_data,
                        AgentType.STRUCTURED_BOT,
                        self.timeouts["structured_agent"]
                    )
                )
            else:
                # Use real TextBOT for structured data analysis
                task = asyncio.create_task(
                    self._real_text_agent(triage_case)
                )
            tasks.append(task)
            task_names.append("structured")

        # Execute all agents in parallel using asyncio.gather
        logger.info(f"Executing {len(tasks)} agents in parallel: {task_names}")

        try:
            results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=self.timeouts["total_processing"]
            )

            # Process results
            agent_results = {}
            for i, result in enumerate(results):
                task_name = task_names[i]

                if isinstance(result, Exception):
                    logger.error(f"Agent {task_name} failed: {result}")
                    agent_results[task_name] = AgentResult(
                        agent_type=AgentType(f"{task_name}_bot"),
                        success=False,
                        error_message=str(result)
                    )
                else:
                    agent_results[task_name] = result

            return agent_results

        except asyncio.TimeoutError:
            logger.error(f"Agent coordination timeout for case {triage_case.case_id}")
            return {name: AgentResult(
                agent_type=AgentType(f"{name}_bot"),
                success=False,
                error_message="Processing timeout"
            ) for name in task_names}

    async def _run_agent_with_timeout(
        self, agent_method, data, agent_type: AgentType, timeout: int
    ) -> AgentResult:
        """
        Run an agent method with timeout protection.

        Args:
            agent_method: The agent method to call
            data: Data to pass to the agent
            agent_type: Type of agent
            timeout: Timeout in seconds

        Returns:
            AgentResult with processing results
        """
        start_time = time.time()

        try:
            result = await asyncio.wait_for(agent_method(data), timeout=timeout)
            processing_time = int((time.time() - start_time) * 1000)

            return AgentResult(
                agent_type=agent_type,
                success=True,
                raw_output=result.get("raw_output"),
                synthesized_output=result.get("synthesized_output"),
                confidence_score=result.get("confidence_score"),
                processing_time_ms=processing_time,
                model_version=result.get("model_version")
            )

        except asyncio.TimeoutError:
            return AgentResult(
                agent_type=agent_type,
                success=False,
                error_message=f"Agent timeout after {timeout}s"
            )
        except Exception as e:
            return AgentResult(
                agent_type=agent_type,
                success=False,
                error_message=str(e)
            )

    async def _synthesize_results(
        self,
        triage_case: PydanticTriageCase,
        agent_results: Dict[str, AgentResult],
        start_time: float
    ) -> TriageDecision:
        """
        Synthesize results from all agents into a final triage decision.

        Args:
            triage_case: Original case
            agent_results: Results from all agents
            start_time: Processing start time

        Returns:
            TriageDecision with final scores and recommendations
        """
        case_id = triage_case.case_id or f"CASE_{int(time.time())}"

        # Calculate final triage score using weighted algorithm
        final_score = await self._calculate_final_score(agent_results)

        # Determine urgency level based on score
        urgency_level = self._determine_urgency_level(final_score)

        # Calculate overall confidence
        confidence_score = self._calculate_confidence_score(agent_results)

        # Generate reasoning
        reasoning = self._generate_reasoning(agent_results, final_score)

        # Create processing summary
        processing_summary = {
            "total_processing_time_ms": int((time.time() - start_time) * 1000),
            "agents_executed": len([r for r in agent_results.values() if r.success]),
            "agents_failed": len([r for r in agent_results.values() if not r.success]),
            "algorithm_version": self.version,
            "scoring_weights": self.scoring_weights
        }

        return TriageDecision(
            case_id=case_id,
            final_triage_score=final_score,
            urgency_level=urgency_level,
            confidence_score=confidence_score,
            recommendations=[],  # Will be filled in finalization
            reasoning=reasoning,
            agent_results=agent_results,
            processing_summary=processing_summary
        )

    async def _calculate_final_score(self, agent_results: Dict[str, AgentResult]) -> float:
        """
        Calculate final triage score using weighted algorithm.

        Args:
            agent_results: Results from all agents

        Returns:
            Final triage score (0.0 to 1.0)
        """
        total_score = 0.0
        total_weight = 0.0

        # Vision analysis contribution
        if "vision" in agent_results and agent_results["vision"].success:
            vision_result = agent_results["vision"]
            if vision_result.confidence_score is not None:
                weight = self.scoring_weights["vision_confidence"]

                # Extract risk score from vision analysis if available
                risk_score = vision_result.confidence_score
                if vision_result.raw_output and "risk_score" in vision_result.raw_output:
                    risk_score = vision_result.raw_output["risk_score"]
                elif vision_result.raw_output and "overall_risk_score" in vision_result.raw_output:
                    risk_score = vision_result.raw_output["overall_risk_score"]

                total_score += risk_score * weight
                total_weight += weight

        # Text analysis contribution
        if "text" in agent_results and agent_results["text"].success:
            text_result = agent_results["text"]
            if text_result.raw_output and "risk_score" in text_result.raw_output:
                weight = self.scoring_weights["text_risk_score"]
                risk_score = text_result.raw_output["risk_score"]
                total_score += risk_score * weight
                total_weight += weight

        # Structured data contribution
        if "structured" in agent_results and agent_results["structured"].success:
            structured_result = agent_results["structured"]
            if structured_result.raw_output and "risk_score" in structured_result.raw_output:
                weight = self.scoring_weights["structured_risk_score"]
                risk_score = structured_result.raw_output["risk_score"]
                total_score += risk_score * weight
                total_weight += weight

        # If no agents provided useful scores, return moderate score
        if total_weight == 0:
            return 0.5

        # Normalize by total weight used
        final_score = total_score / total_weight

        # Ensure score is within bounds
        return max(0.0, min(1.0, final_score))

    def _determine_urgency_level(self, triage_score: float) -> UrgencyLevel:
        """
        Determine urgency level based on triage score.

        Args:
            triage_score: Final triage score

        Returns:
            UrgencyLevel enum value
        """
        if triage_score >= self.urgency_thresholds[UrgencyLevel.CRITICAL]:
            return UrgencyLevel.CRITICAL
        elif triage_score >= self.urgency_thresholds[UrgencyLevel.HIGH]:
            return UrgencyLevel.HIGH
        elif triage_score >= self.urgency_thresholds[UrgencyLevel.MEDIUM]:
            return UrgencyLevel.MEDIUM
        else:
            return UrgencyLevel.LOW

    def _calculate_confidence_score(self, agent_results: Dict[str, AgentResult]) -> float:
        """
        Calculate overall confidence in the triage decision.

        Args:
            agent_results: Results from all agents

        Returns:
            Confidence score (0.0 to 1.0)
        """
        confidence_scores = []

        for result in agent_results.values():
            if result.success and result.confidence_score is not None:
                confidence_scores.append(result.confidence_score)

        if not confidence_scores:
            return 0.5  # Moderate confidence if no agent provided confidence scores

        # Return average confidence
        return sum(confidence_scores) / len(confidence_scores)

    def _generate_reasoning(self, agent_results: Dict[str, AgentResult], final_score: float) -> str:
        """
        Generate human-readable reasoning for the triage decision.

        Args:
            agent_results: Results from all agents
            final_score: Final triage score

        Returns:
            Reasoning text
        """
        reasoning_parts = []

        # Add agent-specific reasoning
        for agent_name, result in agent_results.items():
            if result.success and result.synthesized_output:
                reasoning_parts.append(f"{agent_name.title()} analysis: {result.synthesized_output}")

        # Add overall assessment
        score_interpretation = {
            0.8: "critical priority requiring immediate attention",
            0.6: "high priority requiring prompt medical evaluation",
            0.4: "moderate priority for standard medical assessment",
            0.0: "low priority suitable for routine care"
        }

        for threshold, interpretation in score_interpretation.items():
            if final_score >= threshold:
                reasoning_parts.append(f"Overall assessment indicates {interpretation}.")
                break

        return " ".join(reasoning_parts) if reasoning_parts else "Assessment based on available clinical data."

    async def _run_vision_agent(self, images) -> AgentResult:
        """Run VisionBot agent for image analysis"""
        start_time = time.time()

        try:
            # Create VisionBot instance
            vision_bot = VisionBot()

            # Process images
            result = await vision_bot.process_images(images)
            processing_time = int((time.time() - start_time) * 1000)

            # Clean up resources
            await vision_bot.cleanup()

            # Convert to AgentResult format
            if result.get("success", False):
                return AgentResult(
                    agent_type=AgentType.VISION_BOT,
                    success=True,
                    raw_output=result.get("raw_output", {}),
                    synthesized_output=result.get("synthesized_output", ""),
                    confidence_score=result.get("overall_confidence", 0.5),
                    processing_time_ms=processing_time,
                    model_version=result.get("model_version", "vision_bot_v1")
                )
            else:
                return AgentResult(
                    agent_type=AgentType.VISION_BOT,
                    success=False,
                    error_message=result.get("error", "Vision analysis failed"),
                    processing_time_ms=processing_time
                )

        except Exception as e:
            processing_time = int((time.time() - start_time) * 1000)
            logger.error(f"VisionBot agent failed: {e}")
            return AgentResult(
                agent_type=AgentType.VISION_BOT,
                success=False,
                error_message=str(e),
                processing_time_ms=processing_time
            )

    async def _finalize_decision(self, decision: TriageDecision) -> None:
        """
        Finalize the triage decision by generating recommendations.

        Args:
            decision: TriageDecision to finalize
        """
        recommendations = []

        # Generate recommendations based on urgency level
        if decision.urgency_level == UrgencyLevel.CRITICAL:
            recommendations.extend([
                "Immediate medical attention required",
                "Monitor vital signs continuously",
                "Prepare for potential emergency intervention"
            ])
        elif decision.urgency_level == UrgencyLevel.HIGH:
            recommendations.extend([
                "Prompt medical evaluation recommended",
                "Monitor patient closely",
                "Consider specialist consultation"
            ])
        elif decision.urgency_level == UrgencyLevel.MEDIUM:
            recommendations.extend([
                "Standard medical assessment recommended",
                "Schedule follow-up as appropriate"
            ])
        else:
            recommendations.extend([
                "Routine medical care sufficient",
                "Schedule as convenient"
            ])

        # Add agent-specific recommendations
        for agent_name, result in decision.agent_results.items():
            if result.success and result.raw_output and "recommendations" in result.raw_output:
                agent_recommendations = result.raw_output["recommendations"]
                if isinstance(agent_recommendations, list):
                    # Limit recommendations per agent to avoid overwhelming output
                    recommendations.extend(agent_recommendations[:10])
                    logger.info(f"Added {len(agent_recommendations[:10])} recommendations from {agent_name} agent")

        decision.recommendations = recommendations

    # Mock agent methods for testing purposes
    async def _mock_vision_agent(self, images) -> AgentResult:
        """Mock VisionBOT agent for testing"""
        await asyncio.sleep(0.1)  # Simulate processing time

        return AgentResult(
            agent_type=AgentType.VISION_BOT,
            success=True,
            raw_output={
                "prediction_class": 3,
                "disease": "Severe Diabetic Retinopathy",
                "confidence": 0.92,
                "risk_score": 0.85
            },
            synthesized_output="Retinal analysis indicates severe diabetic retinopathy with high risk features requiring immediate ophthalmologic attention.",
            confidence_score=0.92,
            processing_time_ms=850,
            model_version="efficientnet_v2_mock"
        )

    async def _real_text_agent(self, triage_case: PydanticTriageCase) -> AgentResult:
        """Real TextBOT agent for structured data analysis"""
        try:
            logger.info(f"_real_text_agent called for case {triage_case.case_id}")
            logger.info(f"Structured data available: {triage_case.structured_data is not None}")
            if triage_case.structured_data:
                logger.info(f"Number of structured data items: {len(triage_case.structured_data)}")

            # Use structured data if available
            if triage_case.structured_data:
                logger.info("Processing structured data with TextBOT")
                result = await self.text_bot.process_structured_data(triage_case.structured_data)
                logger.info(f"TextBOT result: success={result.success}, score={result.overall_risk_score}, category={result.risk_category}")

                # Add recommendations to raw_output for ChiefBOT synthesis
                enhanced_raw_output = result.raw_output.copy()
                enhanced_raw_output["recommendations"] = result.recommendations
                enhanced_raw_output["risk_score"] = result.overall_risk_score
                enhanced_raw_output["risk_category"] = result.risk_category

                return AgentResult(
                    agent_type=AgentType.TEXT_BOT,
                    success=result.success,
                    raw_output=enhanced_raw_output,
                    synthesized_output=f"Medical data analysis indicates {result.risk_category} risk (score: {result.overall_risk_score:.3f}). Models used: {', '.join(result.models_used)}. {len(result.recommendations)} recommendations generated.",
                    confidence_score=result.confidence_score,
                    processing_time_ms=result.processing_time_ms,
                    model_version="TextBOT_v1.0.0"
                )
            else:
                logger.info("No structured data, using fallback text analysis")
                # Fallback to text analysis if no structured data
                return await self._mock_text_agent_fallback(triage_case.symptoms_text or triage_case.chief_complaint or "")

        except Exception as e:
            logger.error(f"TextBOT agent error: {str(e)}")
            import traceback
            logger.error(f"TextBOT traceback: {traceback.format_exc()}")
            return AgentResult(
                agent_type=AgentType.TEXT_BOT,
                success=False,
                error_message=f"TextBOT processing failed: {str(e)}",
                confidence_score=0.0,
                processing_time_ms=0,
                model_version="TextBOT_v1.0.0"
            )

    async def _mock_text_agent_fallback(self, symptoms_text: str) -> AgentResult:
        """Fallback text analysis for cases without structured data"""
        await asyncio.sleep(0.1)  # Simulate processing time

        # Simple risk assessment based on keywords
        high_risk_keywords = ["chest pain", "shortness of breath", "severe", "acute", "emergency"]
        risk_score = 0.3  # Base risk

        for keyword in high_risk_keywords:
            if keyword.lower() in symptoms_text.lower():
                risk_score += 0.15

        risk_score = min(risk_score, 1.0)

        return AgentResult(
            agent_type=AgentType.TEXT_BOT,
            success=True,
            raw_output={
                "risk_score": risk_score,
                "keywords_found": [kw for kw in high_risk_keywords if kw.lower() in symptoms_text.lower()],
                "recommendations": ["Clinical correlation recommended"]
            },
            synthesized_output=f"Text analysis of symptoms indicates {'high' if risk_score > 0.6 else 'moderate' if risk_score > 0.4 else 'low'} clinical risk requiring appropriate medical evaluation.",
            confidence_score=0.78,
            processing_time_ms=420,
            model_version="text_analyzer_fallback"
        )

    async def _mock_structured_agent(self, structured_data) -> AgentResult:
        """Mock structured data agent for testing"""
        await asyncio.sleep(0.1)  # Simulate processing time

        risk_score = 0.2  # Base risk
        abnormal_values = []

        # Analyze structured data for risk factors
        for data_item in structured_data:
            for key, value in data_item.data.items():
                if isinstance(value, (int, float)):
                    # Simple rules for common lab values
                    if "glucose" in key.lower() and value > 140:
                        risk_score += 0.2
                        abnormal_values.append(f"elevated_{key}")
                    elif "pressure" in key.lower() and value > 140:
                        risk_score += 0.15
                        abnormal_values.append(f"elevated_{key}")
                    elif "cholesterol" in key.lower() and value > 240:
                        risk_score += 0.1
                        abnormal_values.append(f"elevated_{key}")

        risk_score = min(risk_score, 1.0)

        return AgentResult(
            agent_type=AgentType.STRUCTURED_BOT,
            success=True,
            raw_output={
                "risk_score": risk_score,
                "abnormal_values": abnormal_values,
                "recommendations": ["Monitor lab values closely", "Consider additional testing"]
            },
            synthesized_output=f"Structured data analysis reveals {'significant' if risk_score > 0.6 else 'moderate' if risk_score > 0.4 else 'minimal'} risk factors requiring medical attention.",
            confidence_score=0.85,
            processing_time_ms=320,
            model_version="structured_analyzer_mock"
        )


# Utility functions for creating TriageCaseResponse
def create_triage_response(decision: TriageDecision) -> TriageCaseResponse:
    """
    Convert TriageDecision to TriageCaseResponse.

    Args:
        decision: TriageDecision from Chief-BOT

    Returns:
        TriageCaseResponse for API responses
    """
    # Calculate estimated wait time based on urgency
    wait_time_map = {
        UrgencyLevel.CRITICAL: 5,
        UrgencyLevel.HIGH: 15,
        UrgencyLevel.MEDIUM: 60,
        UrgencyLevel.LOW: 180
    }

    return TriageCaseResponse(
        case_id=decision.case_id,
        processing_status="completed",
        triage_score=decision.final_triage_score,
        urgency_level=decision.urgency_level,
        estimated_wait_time=wait_time_map.get(decision.urgency_level, 60),
        recommendations=decision.recommendations,
        vision_analysis_completed="vision" in decision.agent_results and decision.agent_results["vision"].success,
        text_analysis_completed="text" in decision.agent_results and decision.agent_results["text"].success,
        structured_analysis_completed="structured" in decision.agent_results and decision.agent_results["structured"].success,
        raw_vision_output=decision.agent_results.get("vision", {}).raw_output if "vision" in decision.agent_results else None,
        synthesized_vision_output=decision.agent_results.get("vision", {}).synthesized_output if "vision" in decision.agent_results else None,
        raw_text_output=decision.agent_results.get("text", {}).raw_output if "text" in decision.agent_results else None,
        synthesized_text_output=decision.agent_results.get("text", {}).synthesized_output if "text" in decision.agent_results else None
    )
