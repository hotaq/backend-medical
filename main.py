"""
Main FastAPI Application for Medical Triage-BOTS System

This is the main application file that provides a production-ready FastAPI server
with the refactored /triage endpoint using the new TriageCase model and database integration.

Features:
- Multi-modal triage processing (text, images, structured data)
- Integration with ChiefBOT orchestrator
- Database operations with SQLAlchemy
- Comprehensive error handling and logging
- Performance metrics and monitoring
- Background task processing
- CORS support for web clients

Run with: uvicorn main:app --reload
"""

import asyncio
import logging
import time
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
from contextlib import asynccontextmanager

# FastAPI and related imports
from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks, File, UploadFile, Form
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession

# App imports
from app.agents.chief_bot import ChiefBOT
from app.models.triage_case import (
    TriageCase,
    TriageCaseResponse,
    UrgencyLevel,
    DataType,
    ImageData,
    StructuredData,
    PatientInfo,
    StructuredDataType
)
from app.database.config import DatabaseManager, init_database
from app.database.crud import (
    TriageCaseCRUD,
    CaseProcessingCRUD,
    TriageResultCRUD,
    AuditCRUD,
    PatientCRUD
)
from app.database.models import ProcessingStatusEnum, UrgencyLevelEnum

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global instances
chief_bot: ChiefBOT = None
db_manager: DatabaseManager = None

# Application metrics
app_metrics = {
    "total_requests": 0,
    "successful_requests": 0,
    "failed_requests": 0,
    "average_processing_time": 0.0,
    "critical_cases": 0,
    "high_priority_cases": 0,
    "text_only_cases": 0,
    "image_cases": 0,
    "multimodal_cases": 0
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown"""
    # Startup
    global chief_bot, db_manager
    logger.info("🚀 Starting Medical Triage-BOTS System...")

    try:
        # Initialize database
        db_manager = DatabaseManager()
        await init_database()
        logger.info("✅ Database manager initialized")

        # Initialize ChiefBOT orchestrator
        chief_bot = ChiefBOT()
        await chief_bot.initialize()
        logger.info("✅ ChiefBOT orchestrator initialized")

        logger.info("🏥 Medical Triage-BOTS System ready for service")

    except Exception as e:
        logger.error(f"❌ Failed to initialize system: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Medical Triage-BOTS System...")
    if db_manager:
        from app.database.config import cleanup_database
        await cleanup_database()


# Create FastAPI application
app = FastAPI(
    title="Medical Triage-BOTS System",
    description="AI-powered multi-modal medical triage system with VisionBOT and TextBOT agents",
    version="2.0.0",
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


async def get_db_session() -> AsyncSession:
    """Dependency to get database session"""
    async with db_manager.get_session() as session:
        yield session


def generate_case_id() -> str:
    """Generate unique case ID"""
    return f"CASE_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8].upper()}"


async def log_processing_metrics(
    case_id: str,
    processing_time_ms: int,
    triage_score: float,
    urgency_level: str,
    data_types_used: List[str]
):
    """Background task to log processing metrics"""
    try:
        # Update application metrics
        app_metrics["total_requests"] += 1
        app_metrics["successful_requests"] += 1

        # Update average processing time
        current_avg = app_metrics["average_processing_time"]
        total_requests = app_metrics["total_requests"]
        app_metrics["average_processing_time"] = (
            (current_avg * (total_requests - 1) + processing_time_ms) / total_requests
        )

        # Update case type metrics
        if urgency_level == UrgencyLevel.CRITICAL.value:
            app_metrics["critical_cases"] += 1
        elif urgency_level == UrgencyLevel.HIGH.value:
            app_metrics["high_priority_cases"] += 1

        # Update data type metrics
        if len(data_types_used) > 1:
            app_metrics["multimodal_cases"] += 1
        elif "image" in data_types_used:
            app_metrics["image_cases"] += 1
        elif "text" in data_types_used:
            app_metrics["text_only_cases"] += 1

        logger.info(f"📊 Metrics updated for case {case_id}")

    except Exception as e:
        logger.error(f"Failed to log metrics for case {case_id}: {e}")


@app.get("/")
async def root():
    """Root endpoint with system status"""
    return {
        "message": "Medical Triage-BOTS System",
        "version": "2.0.0",
        "status": "operational",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "triage": "/triage",
            "health": "/health",
            "metrics": "/metrics"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if ChiefBOT is initialized
        if not chief_bot or not chief_bot.is_initialized:
            raise HTTPException(status_code=503, detail="ChiefBOT not initialized")

        # Check database connection
        async with db_manager.get_session() as session:
            await session.execute("SELECT 1")

        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {
                "chief_bot": "operational",
                "database": "operational",
                "vision_bot": "operational" if chief_bot.vision_bot else "not_initialized",
                "text_bot": "operational" if chief_bot.text_bot else "not_initialized"
            }
        }

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail=f"System unhealthy: {str(e)}")


@app.get("/metrics")
async def get_metrics():
    """Get application metrics"""
    return {
        "metrics": app_metrics,
        "timestamp": datetime.now().isoformat()
    }


@app.post("/triage", response_model=TriageCaseResponse)
async def process_triage_case(
    triage_case: TriageCase,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session)
):
    """
    Main triage endpoint - process a medical case with multi-modal support

    This endpoint handles:
    - Text-based symptoms and medical history
    - Structured medical data (lab results, vital signs)
    - Medical images (retinal photos, X-rays, CT scans)
    - Mixed multi-modal cases

    Processing flow:
    1. Validate and enrich the triage case
    2. Store case in database
    3. Route to appropriate agents via ChiefBOT
    4. Calculate final triage score
    5. Generate recommendations
    6. Log results and metrics
    """
    start_time = time.time()
    case_id = triage_case.case_id or generate_case_id()
    triage_case.case_id = case_id

    try:
        logger.info(f"🧠 Processing triage case: {case_id}")
        logger.info(f"📊 Data summary: {triage_case.get_data_summary()}")

        # Validate that case has meaningful data
        if not triage_case.has_any_data():
            raise HTTPException(
                status_code=400,
                detail="Triage case must contain at least one of: symptoms_text, chief_complaint, structured_data, or images"
            )

        # Store triage case in database (includes patient creation if needed)
        try:
            db_case = await TriageCaseCRUD.create_triage_case(session, triage_case)
            logger.info(f"💾 Stored case in database with ID: {db_case.id}")
            if triage_case.patient_info:
                logger.info(f"👤 Patient data processed: {triage_case.patient_info.patient_id}")
        except Exception as e:
            logger.error(f"Failed to store case in database: {e}")
            # Continue processing even if database storage fails
            db_case = None

        # Log initial processing record
        await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="chief_bot",
            processing_step="api_request",
            status=ProcessingStatusEnum.IN_PROGRESS,
            llm_model_used="chief_bot_orchestrator_v2.0.0"
        )

        # Process with ChiefBOT orchestrator
        logger.info(f"🤖 Routing case to ChiefBOT orchestrator...")
        processing_requirements = triage_case.get_processing_requirements()
        logger.info(f"📋 Processing requirements: {processing_requirements}")

        # Process the case through ChiefBOT
        triage_decision = await chief_bot.process_triage_case(triage_case)

        # Calculate processing time
        processing_time_ms = int((time.time() - start_time) * 1000)

        # Create response object
        response = TriageCaseResponse(
            case_id=case_id,
            processing_status="completed",
            triage_score=triage_decision.final_triage_score,
            urgency_level=triage_decision.urgency_level,
            estimated_wait_time=calculate_wait_time(triage_decision.urgency_level),
            recommendations=triage_decision.recommendations,
            vision_analysis_completed=triage_case.requires_vision_analysis,
            text_analysis_completed=triage_case.requires_text_analysis,
            structured_analysis_completed=triage_case.requires_structured_analysis,
            raw_vision_output=triage_decision.agent_results.get("vision_bot"),
            raw_text_output=triage_decision.agent_results.get("text_bot"),
            synthesized_vision_output=triage_decision.vision_synthesis,
            synthesized_text_output=triage_decision.text_synthesis
        )

        # Store final triage result in database
        if db_case:
            try:
                await TriageResultCRUD.create_triage_result(
                    session,
                    case_id=case_id,
                    final_triage_score=triage_decision.final_triage_score,
                    urgency_level=UrgencyLevelEnum(triage_decision.urgency_level.value),
                    recommendations=triage_decision.recommendations,
                    confidence_score=triage_decision.confidence_score,
                    clinical_notes=triage_decision.reasoning,
                    vision_analysis_completed=triage_case.requires_vision_analysis,
                    text_analysis_completed=triage_case.requires_text_analysis,
                    structured_analysis_completed=triage_case.requires_structured_analysis,
                    scoring_algorithm_version="chief_bot_v2.0.0"
                )
                logger.info(f"💾 Stored triage result in database")
            except Exception as e:
                logger.error(f"Failed to store triage result: {e}")

        # Log completion
        await CaseProcessingCRUD.create_processing_record(
            session,
            case_id=case_id,
            agent_type="chief_bot",
            processing_step="api_response",
            status=ProcessingStatusEnum.COMPLETED,
            llm_model_used="chief_bot_orchestrator_v2.0.0",
            processing_time_ms=processing_time_ms,
            raw_output={
                "final_score": triage_decision.final_triage_score,
                "urgency_level": triage_decision.urgency_level.value,
                "confidence": triage_decision.confidence_score,
                "agents_used": list(triage_decision.agent_results.keys()),
                "recommendations_count": len(triage_decision.recommendations)
            },
            synthesized_output=triage_decision.reasoning
        )

        # Commit all database changes
        await session.commit()

        # Schedule background tasks for metrics
        data_types_used = []
        if triage_case.requires_text_analysis:
            data_types_used.append("text")
        if triage_case.requires_vision_analysis:
            data_types_used.append("image")
        if triage_case.requires_structured_analysis:
            data_types_used.append("structured")

        background_tasks.add_task(
            log_processing_metrics,
            case_id,
            processing_time_ms,
            triage_decision.final_triage_score,
            triage_decision.urgency_level.value,
            data_types_used
        )

        # Log audit event
        background_tasks.add_task(
            log_audit_event,
            session,
            "triage_case_processed",
            "triage_case",
            case_id,
            {
                "urgency_level": triage_decision.urgency_level.value,
                "processing_time_ms": processing_time_ms,
                "agents_used": list(triage_decision.agent_results.keys())
            }
        )

        logger.info(f"✅ Completed triage case {case_id}: "
                   f"score={triage_decision.final_triage_score:.3f}, "
                   f"urgency={triage_decision.urgency_level.value}, "
                   f"time={processing_time_ms}ms")

        return response

    except HTTPException:
        # Re-raise HTTP exceptions
        app_metrics["failed_requests"] += 1
        raise

    except Exception as e:
        logger.error(f"❌ Triage processing failed for case {case_id}: {e}", exc_info=True)
        app_metrics["failed_requests"] += 1

        # Log error to database
        try:
            await CaseProcessingCRUD.create_processing_record(
                session,
                case_id=case_id,
                agent_type="chief_bot",
                processing_step="api_error",
                status=ProcessingStatusEnum.FAILED,
                llm_model_used="chief_bot_orchestrator_v2.0.0",
                error_message=str(e),
                raw_output={"error": str(e), "error_type": type(e).__name__}
            )
            await session.commit()
        except Exception as db_error:
            logger.error(f"Failed to log error to database: {db_error}")

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Triage processing failed",
                "case_id": case_id,
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )


@app.post("/triage/multipart")
async def process_triage_case_multipart(
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db_session),
    # Form fields
    symptoms_text: Optional[str] = Form(None),
    chief_complaint: Optional[str] = Form(None),
    medical_history: Optional[str] = Form(None),
    patient_id: Optional[str] = Form(None),
    age: Optional[int] = Form(None),
    gender: Optional[str] = Form(None),
    structured_data: Optional[str] = Form(None),  # JSON string
    # File uploads
    images: List[UploadFile] = File(None)
):
    """
    Alternative triage endpoint that accepts multipart form data

    This endpoint is useful for web forms and clients that need to upload
    files along with form data.
    """
    try:
        # Build patient info
        patient_info = None
        if patient_id or age or gender:
            patient_info = PatientInfo(
                patient_id=patient_id,
                age=age,
                gender=gender
            )

        # Process structured data if provided
        structured_data_list = None
        if structured_data:
            try:
                import json
                structured_json = json.loads(structured_data)
                structured_data_list = [
                    StructuredData(**item) for item in structured_json
                ]
            except (json.JSONDecodeError, TypeError, ValueError) as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid structured_data JSON: {str(e)}"
                )

        # Process uploaded images
        image_data_list = None
        if images and images[0].filename:  # Check if actual files were uploaded
            image_data_list = []
            for i, image_file in enumerate(images):
                if image_file.filename:
                    # In a production system, you would save the file and store the path
                    # For now, we'll create a placeholder path
                    image_path = f"/uploads/{generate_case_id()}_{i}_{image_file.filename}"

                    image_data = ImageData(
                        image_path=image_path,
                        image_type=detect_image_type(image_file.filename),
                        file_size=len(await image_file.read()) if hasattr(image_file, 'read') else None
                    )
                    image_data_list.append(image_data)

                    # Reset file pointer if needed
                    if hasattr(image_file, 'seek'):
                        await image_file.seek(0)

        # Create TriageCase object
        triage_case = TriageCase(
            patient_info=patient_info,
            symptoms_text=symptoms_text,
            chief_complaint=chief_complaint,
            medical_history=medical_history,
            structured_data=structured_data_list,
            images=image_data_list
        )

        # Process through the main triage endpoint
        return await process_triage_case(triage_case, background_tasks, session)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Multipart triage processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Multipart triage processing failed: {str(e)}"
        )


def calculate_wait_time(urgency_level: UrgencyLevel) -> int:
    """Calculate estimated wait time based on urgency level"""
    wait_times = {
        UrgencyLevel.CRITICAL: 0,      # Immediate
        UrgencyLevel.HIGH: 15,         # 15 minutes
        UrgencyLevel.MEDIUM: 60,       # 1 hour
        UrgencyLevel.LOW: 180          # 3 hours
    }
    return wait_times.get(urgency_level, 120)


def detect_image_type(filename: str) -> str:
    """Detect image type from filename"""
    filename_lower = filename.lower()

    if any(keyword in filename_lower for keyword in ['retinal', 'fundus', 'eye']):
        return 'retinal'
    elif any(keyword in filename_lower for keyword in ['xray', 'x-ray', 'radiograph']):
        return 'xray'
    elif any(keyword in filename_lower for keyword in ['ct', 'scan', 'computed']):
        return 'ct_scan'
    elif any(keyword in filename_lower for keyword in ['mri', 'magnetic']):
        return 'mri'
    elif any(keyword in filename_lower for keyword in ['ultrasound', 'echo']):
        return 'ultrasound'
    else:
        return 'general'


async def log_audit_event(
    session: AsyncSession,
    event_type: str,
    entity_type: str,
    entity_id: str,
    event_data: Dict[str, Any]
):
    """Background task to log audit events"""
    try:
        await AuditCRUD.log_event(
            session,
            event_type=event_type,
            entity_type=entity_type,
            entity_id=entity_id,
            event_data=event_data
        )
        await session.commit()
    except Exception as e:
        logger.error(f"Failed to log audit event: {e}")


if __name__ == "__main__":
    import uvicorn

    logger.info("🚀 Starting Medical Triage-BOTS FastAPI server...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
