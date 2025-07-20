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


@app.get("/database/cases")
async def get_cases(
    page: int = 1,
    limit: int = 20,
    urgency_level: Optional[str] = None,
    department: Optional[str] = None,
    search: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    session: AsyncSession = Depends(get_db_session)
):
    """Get paginated list of triage cases"""
    try:
        # Calculate offset
        offset = (page - 1) * limit

        # Build query
        query = session.query(TriageCase)

        # Apply filters
        if urgency_level:
            query = query.filter(TriageCase.priority_level == urgency_level)
        if department:
            query = query.filter(TriageCase.target_department == department)
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    TriageCase.case_id.like(search_term),
                    TriageCase.chief_complaint.like(search_term),
                    TriageCase.symptoms_text.like(search_term)
                )
            )
        if date_from:
            query = query.filter(TriageCase.created_at >= date_from)
        if date_to:
            query = query.filter(TriageCase.created_at <= date_to)

        # Get total count
        total = await session.execute(
            select(func.count()).select_from(query.subquery())
        )
        total_count = total.scalar()

        # Get paginated results
        cases = await session.execute(
            query.offset(offset).limit(limit)
            .options(
                selectinload(TriageCase.patient),
                selectinload(TriageCase.triage_result)
            )
        )

        return {
            "data": cases.scalars().all(),
            "total": total_count,
            "page": page,
            "limit": limit,
            "has_next": (page * limit) < total_count,
            "has_prev": page > 1
        }

    except Exception as e:
        logger.error(f"Failed to get cases: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cases: {str(e)}")


@app.get("/database/cases/{case_id}")
async def get_case(
    case_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get specific triage case with full details"""
    try:
        case = await TriageCaseCRUD.get_triage_case_by_id(
            session,
            case_id,
            include_relations=True
        )
        if not case:
            raise HTTPException(status_code=404, detail="Case not found")

        return case

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get case {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get case: {str(e)}")


@app.get("/database/cases/{case_id}/processing")
async def get_case_processing_history(
    case_id: str,
    session: AsyncSession = Depends(get_db_session)
):
    """Get processing history for a specific case"""
    try:
        history = await CaseProcessingCRUD.get_case_processing_history(session, case_id)
        return history

    except Exception as e:
        logger.error(f"Failed to get processing history for {case_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get processing history: {str(e)}")


@app.post("/chat")
async def send_chat_message(
    message_data: dict,
    session: AsyncSession = Depends(get_db_session)
):
    """Send message to LLM and get response"""
    try:
        message = message_data.get("message", "")
        case_id = message_data.get("case_id")
        include_context = message_data.get("include_context", False)

        if not message.strip():
            raise HTTPException(status_code=400, detail="Message cannot be empty")

        # Prepare context if case_id is provided
        context = ""
        if case_id and include_context:
            try:
                case = await TriageCaseCRUD.get_triage_case_by_id(session, case_id)
                if case:
                    context = f"Case Context: {case.chief_complaint} - {case.symptoms_text}"
            except Exception as e:
                logger.warning(f"Failed to get case context: {e}")

        # Create enhanced prompt
        if context:
            enhanced_message = f"Medical Case Context: {context}\n\nUser Question: {message}"
        else:
            enhanced_message = f"Medical Question: {message}"

        # For now, return a simulated response
        # In production, integrate with actual LLM service
        response_content = await simulate_llm_response(enhanced_message)

        # Create response message
        response = {
            "id": f"msg_{int(time.time() * 1000)}",
            "role": "assistant",
            "content": response_content,
            "timestamp": datetime.now().isoformat(),
            "case_id": case_id,
            "metadata": {
                "processing_time": 1500,  # ms
                "model_used": "medical-llm-v1",
                "confidence": 0.85
            }
        }

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Chat processing failed: {str(e)}")


@app.get("/chat/history")
async def get_chat_history(
    case_id: Optional[str] = None,
    limit: int = 50
):
    """Get chat message history"""
    try:
        # For now, return empty history
        # In production, implement chat history storage
        return []

    except Exception as e:
        logger.error(f"Failed to get chat history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get chat history: {str(e)}")


@app.get("/analytics/dashboard")
async def get_dashboard_analytics(
    session: AsyncSession = Depends(get_db_session)
):
    """Get dashboard analytics data"""
    try:
        # Calculate analytics from database
        today = datetime.now().date()

        # Total cases today
        total_cases_query = select(func.count(TriageCase.id)).where(
            func.date(TriageCase.created_at) == today
        )
        total_cases = await session.execute(total_cases_query)
        total_cases_count = total_cases.scalar() or 0

        # Critical cases today
        critical_cases_query = select(func.count(TriageCase.id)).where(
            and_(
                func.date(TriageCase.created_at) == today,
                TriageCase.priority_level == UrgencyLevelEnum.CRITICAL
            )
        )
        critical_cases = await session.execute(critical_cases_query)
        critical_cases_count = critical_cases.scalar() or 0

        # Mock data for other metrics
        return {
            "total_cases": total_cases_count,
            "critical_cases": critical_cases_count,
            "avg_processing_time": 2.3,
            "success_rate": 94.5,
            "cases_by_urgency": {
                "critical": critical_cases_count,
                "high": max(0, total_cases_count - critical_cases_count),
                "medium": 0,
                "low": 0
            },
            "cases_by_hour": [
                {"hour": f"{i:02d}:00", "count": max(0, total_cases_count - i)}
                for i in range(24)
            ],
            "processing_times": [
                {"agent": "Vision Bot", "avg_time": 2.3},
                {"agent": "Text Bot", "avg_time": 1.8},
                {"agent": "Chief Bot", "avg_time": 3.1}
            ]
        }

    except Exception as e:
        logger.error(f"Failed to get dashboard analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


async def simulate_llm_response(message: str) -> str:
    """Simulate LLM response for medical questions"""
    # Add some delay to simulate processing
    await asyncio.sleep(1)

    message_lower = message.lower()

    if "diabetes" in message_lower:
        return """Diabetes symptoms typically include:
- Increased thirst and frequent urination
- Unexplained weight loss
- Fatigue and weakness
- Blurred vision
- Slow-healing wounds
- Frequent infections

For diagnosis, we typically look at fasting glucose levels (>126 mg/dL), HbA1c (>6.5%), or oral glucose tolerance test results. Early detection and management are crucial for preventing complications."""

    elif "system health" in message_lower or "health" in message_lower:
        return f"""Current system status:
- Overall health: Operational
- Database: Connected and responsive
- Vision Bot: Active and processing images
- Text Bot: Active and analyzing symptoms
- Chief Bot: Coordinating triage decisions

All systems are functioning normally. Average processing time is 2.3 seconds per case."""

    elif "critical" in message_lower or "cases" in message_lower:
        return f"""Current triage summary:
- Total cases processed today: {app_metrics['total_requests']}
- Critical cases: {app_metrics['critical_cases']}
- High priority cases: {app_metrics['high_priority_cases']}
- Average processing time: {app_metrics['average_processing_time']:.1f}ms

Critical cases require immediate attention and are automatically flagged for emergency department review."""

    elif "scoring" in message_lower or "triage" in message_lower:
        return """Our triage scoring system uses a multi-modal approach:

1. **Text Analysis**: Symptom severity, medical history, and risk factors
2. **Vision Analysis**: Medical image interpretation when provided
3. **Structured Data**: Lab results, vital signs, and clinical measurements

Scores range from 0-1, with urgency levels:
- 0.0-0.25: Low priority (Green)
- 0.25-0.5: Medium priority (Yellow)
- 0.5-0.75: High priority (Orange)
- 0.75-1.0: Critical priority (Red)

The system combines all available data sources to provide the most accurate triage decision."""

    else:
        return f"""I'm a medical AI assistant integrated with the Triage-BOTS system. I can help with:

- Medical symptom analysis and information
- System status and performance metrics
- Triage scoring explanations
- Case management guidance
- Clinical decision support

Your question: "{message[:100]}..."

Please feel free to ask specific medical questions or request information about the triage system."""


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
