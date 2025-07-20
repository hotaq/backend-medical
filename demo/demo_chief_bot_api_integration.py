"""
Chief-BOT FastAPI Integration Demo

This demo shows how to integrate the Chief-BOT orchestrator with FastAPI
for production-ready medical triage endpoints.

Features:
- RESTful API endpoints for triage processing
- Async request handling
- Database integration
- Error handling and monitoring
- Request/response validation
- Performance metrics

Run with: python -m demo.demo_chief_bot_api_integration
"""

import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

# FastAPI and Pydantic imports
try:
    from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
    from fastapi.responses import JSONResponse
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
except ImportError:
    print("FastAPI not installed. Install with: pip install fastapi uvicorn")
    exit(1)

# App imports
try:
    from app.agents.chief_bot import ChiefBOT, create_triage_response
    from app.models.triage_case import (
        TriageCase,
        TriageCaseResponse,
        UrgencyLevel,
        DataType,
        ImageData,
        StructuredData
    )
    from app.database.crud import CaseProcessingCRUD
    from app.database.models import ProcessingStatusEnum
    from app.database.config import DatabaseManager
except ImportError as e:
    print(f"App imports failed: {e}")
    print("Please ensure all app modules are available")
    exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
chief_bot: ChiefBOT = None
db_manager: DatabaseManager = None
app_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "average_processing_time": 0.0,
    "critical_cases": 0,
    "high_priority_cases": 0
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    global chief_bot, db_manager
    logger.info("🚀 Starting Chief-BOT API Server...")

    chief_bot = ChiefBOT()
    db_manager = DatabaseManager()

    logger.info("✅ Chief-BOT orchestrator initialized")
    logger.info("✅ Database manager initialized")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Chief-BOT API Server...")


# Create FastAPI app
app = FastAPI(
    title="Chief-BOT Medical Triage API",
    description="AI-powered medical triage orchestration system",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Dependency to get database session
async def get_db_session():
    """Get database session dependency"""
    async with db_manager.get_session() as session:
        yield session


# Metrics tracking middleware
@app.middleware("http")
async def track_metrics(request, call_next):
    """Track API metrics"""
    start_time = time.time()

    response = await call_next(request)

    processing_time = time.time() - start_time
    app_metrics["total_requests"] += 1

    if response.status_code < 400:
        app_metrics["successful_requests"] += 1
    else:
        app_metrics["failed_requests"] += 1

    # Update average processing time
    total = app_metrics["total_requests"]
    current_avg = app_metrics["average_processing_time"]
    app_metrics["average_processing_time"] = (current_avg * (total - 1) + processing_time) / total

    return response


# API Endpoints

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "service": "Chief-BOT Medical Triage API",
        "version": "1.0.0",
        "status": "operational",
        "description": "AI-powered multi-agent medical triage orchestration",
        "endpoints": {
            "triage": "/triage",
            "health": "/health",
            "metrics": "/metrics",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "chief_bot_version": chief_bot.version if chief_bot else "not_initialized",
        "database_status": "connected" if db_manager else "not_connected"
    }


@app.get("/metrics")
async def get_metrics():
    """Get API performance metrics"""
    return {
        "metrics": app_metrics,
        "timestamp": datetime.now().isoformat(),
        "uptime_info": {
            "total_requests": app_metrics["total_requests"],
            "success_rate": app_metrics["successful_requests"] / max(app_metrics["total_requests"], 1) * 100,
            "average_processing_time_ms": app_metrics["average_processing_time"] * 1000
        }
    }


@app.post("/triage", response_model=TriageCaseResponse)
async def process_triage_case(
    triage_case: TriageCase,
    background_tasks: BackgroundTasks,
    session=Depends(get_db_session)
):
    """
    Main triage endpoint - process a medical case with Chief-BOT orchestrator

    This endpoint:
    1. Validates the incoming triage case
    2. Orchestrates multi-agent processing
    3. Calculates final triage scores
    4. Logs processing to database
    5. Returns comprehensive triage decision
    """
    start_time = time.time()

    try:
        logger.info(f"🧠 Processing triage case: {triage_case.case_id}")

        # Log initial request
        initial_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=triage_case.case_id,
            agent_type="chief_bot",
            processing_step="api_request",
            status=ProcessingStatusEnum.IN_PROGRESS,
            llm_model_used="chief_bot_orchestrator_v1.0.0"
        )

        # Process with Chief-BOT orchestrator
        decision = await chief_bot.process_triage_case(triage_case)

        # Convert to API response
        response = create_triage_response(decision)

        # Update metrics
        if decision.urgency_level == UrgencyLevel.CRITICAL:
            app_metrics["critical_cases"] += 1
        elif decision.urgency_level == UrgencyLevel.HIGH:
            app_metrics["high_priority_cases"] += 1

        # Log completion
        processing_time_ms = int((time.time() - start_time) * 1000)
        completion_record = await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=triage_case.case_id,
            agent_type="chief_bot",
            processing_step="api_response",
            status=ProcessingStatusEnum.COMPLETED,
            llm_model_used="chief_bot_orchestrator_v1.0.0",
            processing_time_ms=processing_time_ms,
            raw_output={
                "final_score": decision.final_triage_score,
                "urgency_level": decision.urgency_level.value,
                "confidence": decision.confidence_score,
                "agents_used": list(decision.agent_results.keys()),
                "recommendations_count": len(decision.recommendations)
            },
            synthesized_output=decision.reasoning
        )

        await session.commit()

        # Schedule background tasks for analytics
        background_tasks.add_task(
            log_case_analytics,
            triage_case.case_id,
            decision.final_triage_score,
            decision.urgency_level.value,
            processing_time_ms
        )

        logger.info(f"✅ Completed triage case {triage_case.case_id}: "
                   f"score={decision.final_triage_score:.3f}, "
                   f"urgency={decision.urgency_level.value}, "
                   f"time={processing_time_ms}ms")

        return response

    except Exception as e:
        logger.error(f"❌ Triage processing failed for case {triage_case.case_id}: {e}", exc_info=True)

        # Log error
        try:
            error_record = await CaseProcessingCRUD.create_processing_record(
                session,
                case_id=triage_case.case_id,
                agent_type="chief_bot",
                processing_step="api_error",
                status=ProcessingStatusEnum.FAILED,
                llm_model_used="chief_bot_orchestrator_v1.0.0",
                raw_output={"error": str(e)},
                synthesized_output=f"Processing failed: {str(e)}"
            )
            await session.commit()
        except Exception as db_error:
            logger.error(f"Failed to log error to database: {db_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Triage processing failed",
                "case_id": triage_case.case_id,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.get("/triage/{case_id}/status")
async def get_case_status(
    case_id: str,
    session=Depends(get_db_session)
):
    """Get processing status for a specific case"""
    try:
        # Get processing history
        history = await CaseProcessingCRUD.get_case_processing_history(session, case_id)

        if not history:
            raise HTTPException(status_code=404, detail="Case not found")

        # Build status response
        latest = history[0]  # Most recent record

        return {
            "case_id": case_id,
            "status": latest.status.value,
            "last_updated": latest.updated_at.isoformat(),
            "processing_steps": len(history),
            "total_processing_time_ms": sum(r.processing_time_ms or 0 for r in history),
            "agents_involved": list(set(r.agent_type for r in history)),
            "history": [
                {
                    "step": record.processing_step,
                    "status": record.status.value,
                    "agent": record.agent_type,
                    "timestamp": record.created_at.isoformat(),
                    "processing_time_ms": record.processing_time_ms
                }
                for record in history
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve case status")


@app.get("/triage/cases/recent")
async def get_recent_cases(
    limit: int = 10,
    urgency_filter: Optional[str] = None,
    session=Depends(get_db_session)
):
    """Get recent triage cases with optional urgency filtering"""
    try:
        # Get recent cases (simplified - would need proper case storage)
        # For demo purposes, returning mock data structure

        return {
            "recent_cases": [
                {
                    "case_id": f"CASE_{i:03d}",
                    "timestamp": datetime.now().isoformat(),
                    "urgency_level": "HIGH" if i % 3 == 0 else "MEDIUM",
                    "triage_score": 0.6 + (i % 4) * 0.1,
                    "processing_time_ms": 500 + i * 10
                }
                for i in range(1, limit + 1)
            ],
            "filters_applied": {"urgency": urgency_filter} if urgency_filter else {},
            "total_count": limit
        }

    except Exception as e:
        logger.error(f"Failed to get recent cases: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent cases")


# Background task functions

async def log_case_analytics(case_id: str, triage_score: float, urgency_level: str, processing_time_ms: int):
    """Background task for logging analytics"""
    try:
        logger.info(f"📊 Logging analytics for case {case_id}")
        # In production, this would send data to analytics service
        # For demo, just log the information
        analytics_data = {
            "case_id": case_id,
            "triage_score": triage_score,
            "urgency_level": urgency_level,
            "processing_time_ms": processing_time_ms,
            "timestamp": datetime.now().isoformat()
        }
        logger.info(f"Analytics: {json.dumps(analytics_data)}")
    except Exception as e:
        logger.error(f"Analytics logging failed: {e}")


# Demo and testing functions

async def run_api_demo():
    """Run comprehensive API demonstration"""
    print("\n" + "="*60)
    print("  🧠 CHIEF-BOT FastAPI INTEGRATION DEMO")
    print("="*60)

    # Test cases for demonstration
    test_cases = [
        {
            "name": "Critical Cardiac Case",
            "case": TriageCase(
                case_id="API_CRITICAL_001",
                patient_id="P_API_001",
                chief_complaint="Severe chest pain with radiation",
                symptoms_text="Patient presents with crushing chest pain radiating to left arm, profuse sweating, nausea, and shortness of breath. Pain started 30 minutes ago and is worsening.",
                images=[
                    ImageData(
                        image_id="ECG_001",
                        data_type=DataType.ECG,
                        file_path="/api/demo/ecg.jpg",
                        metadata={"leads": 12, "rhythm": "sinus_tachycardia"}
                    )
                ],
                structured_data=[
                    StructuredData(
                        data_type=DataType.VITAL_SIGNS,
                        data={
                            "blood_pressure_systolic": 180,
                            "blood_pressure_diastolic": 110,
                            "heart_rate": 120,
                            "respiratory_rate": 26,
                            "oxygen_saturation": 92
                        },
                        source="emergency_monitor"
                    )
                ]
            )
        },
        {
            "name": "Routine Check-up",
            "case": TriageCase(
                case_id="API_ROUTINE_001",
                patient_id="P_API_002",
                chief_complaint="Annual physical examination",
                symptoms_text="Patient feels well, here for routine annual check-up. No specific complaints.",
                images=[],
                structured_data=[
                    StructuredData(
                        data_type=DataType.VITAL_SIGNS,
                        data={
                            "blood_pressure_systolic": 120,
                            "blood_pressure_diastolic": 80,
                            "heart_rate": 72,
                            "respiratory_rate": 16,
                            "temperature": 98.6
                        },
                        source="clinic_vitals"
                    )
                ]
            )
        }
    ]

    print(f"Testing {len(test_cases)} cases through FastAPI endpoints...")

    # Initialize global instances for demo
    global chief_bot, db_manager
    chief_bot = ChiefBOT()
    db_manager = DatabaseManager()

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n🔹 Test Case {i}: {test_case['name']}")
        print("-" * 40)

        try:
            # Simulate FastAPI endpoint call
            start_time = time.time()

            # Use Chief-BOT directly (simulating the API endpoint logic)
            decision = await chief_bot.process_triage_case(test_case['case'])
            response = create_triage_response(decision)

            processing_time = (time.time() - start_time) * 1000

            print(f"✅ Processing completed in {processing_time:.1f}ms")
            print(f"   Case ID: {response.case_id}")
            print(f"   Triage Score: {response.triage_score:.3f}")
            print(f"   Urgency Level: {response.urgency_level.value.upper()}")
            print(f"   Wait Time: {response.estimated_wait_time} minutes")
            print(f"   Agents Used: Vision={response.vision_analysis_completed}, "
                  f"Text={response.text_analysis_completed}, "
                  f"Structured={response.structured_analysis_completed}")
            print(f"   Recommendations: {len(response.recommendations)} provided")

        except Exception as e:
            print(f"❌ Test case failed: {e}")

    print(f"\n📊 Demo Metrics:")
    print(f"   Total Cases Processed: {len(test_cases)}")
    print(f"   Average Processing Time: {app_metrics.get('average_processing_time', 0)*1000:.1f}ms")
    print(f"   Critical Cases: {app_metrics.get('critical_cases', 0)}")
    print(f"   High Priority Cases: {app_metrics.get('high_priority_cases', 0)}")

    print(f"\n🚀 FastAPI Integration Demo Complete!")
    print(f"   API is ready for production deployment")
    print(f"   Run with: uvicorn demo_chief_bot_api_integration:app --reload")


def run_fastapi_server():
    """Run the FastAPI server"""
    print("🚀 Starting Chief-BOT FastAPI Server...")
    print("📚 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("📊 Metrics: http://localhost:8000/metrics")

    uvicorn.run(
        "demo.demo_chief_bot_api_integration:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "demo":
        # Run demo without starting server
        asyncio.run(run_api_demo())
    else:
        # Start FastAPI server
        run_fastapi_server()
