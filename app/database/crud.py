"""
CRUD Operations for Medical Triage-BOTS Database

This module provides Create, Read, Update, Delete operations for all database models,
with a focus on triage case management and the multi-agent workflow.

Features:
- Async CRUD operations for all models
- Transaction management
- Error handling and logging
- Bulk operations for efficiency
- Search and filtering capabilities
- Data validation and consistency checks
"""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, and_, or_, desc, asc, func
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import logging
import uuid

from .models import (
    Patient, TriageCase, CaseStructuredData, CaseImage,
    CaseProcessing, TriageResult, SystemAuditLog, ModelPerformanceMetrics,
    DataTypeEnum, UrgencyLevelEnum, ProcessingStatusEnum, StructuredDataTypeEnum
)
from ..models.triage_case import TriageCase as PydanticTriageCase

logger = logging.getLogger(__name__)


# =============================================================================
# Patient CRUD Operations
# =============================================================================

class PatientCRUD:
    """CRUD operations for Patient model"""

    @staticmethod
    async def create_patient(
        db: AsyncSession,
        patient_id: str,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        medical_record_number: Optional[str] = None
    ) -> Patient:
        """Create a new patient record"""
        try:
            # Check if patient already exists
            existing = await PatientCRUD.get_patient_by_id(db, patient_id)
            if existing:
                logger.warning(f"Patient {patient_id} already exists")
                return existing

            patient = Patient(
                patient_id=patient_id,
                age=age,
                gender=gender,
                medical_record_number=medical_record_number
            )

            db.add(patient)
            await db.flush()  # Get the ID without committing

            logger.info(f"Created patient: {patient_id}")
            return patient

        except IntegrityError as e:
            await db.rollback()
            logger.error(f"Failed to create patient {patient_id}: {e}")
            raise
        except Exception as e:
            await db.rollback()
            logger.error(f"Unexpected error creating patient {patient_id}: {e}")
            raise

    @staticmethod
    async def get_patient_by_id(db: AsyncSession, patient_id: str) -> Optional[Patient]:
        """Get patient by patient_id"""
        try:
            stmt = select(Patient).where(Patient.patient_id == patient_id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting patient {patient_id}: {e}")
            raise

    @staticmethod
    async def get_patient_with_cases(db: AsyncSession, patient_id: str) -> Optional[Patient]:
        """Get patient with all their triage cases"""
        try:
            stmt = (
                select(Patient)
                .options(selectinload(Patient.triage_cases))
                .where(Patient.patient_id == patient_id)
            )
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting patient with cases {patient_id}: {e}")
            raise

    @staticmethod
    async def update_patient(
        db: AsyncSession,
        patient_id: str,
        **updates
    ) -> Optional[Patient]:
        """Update patient information"""
        try:
            stmt = (
                update(Patient)
                .where(Patient.patient_id == patient_id)
                .values(**updates)
                .returning(Patient)
            )
            result = await db.execute(stmt)
            patient = result.scalar_one_or_none()

            if patient:
                logger.info(f"Updated patient {patient_id}")

            return patient
        except Exception as e:
            logger.error(f"Error updating patient {patient_id}: {e}")
            raise


# =============================================================================
# Triage Case CRUD Operations
# =============================================================================

class TriageCaseCRUD:
    """CRUD operations for TriageCase model"""

    @staticmethod
    async def create_triage_case(
        db: AsyncSession,
        pydantic_case: PydanticTriageCase
    ) -> TriageCase:
        """Create a new triage case from Pydantic model"""
        try:
            # Generate case_id if not provided
            case_id = pydantic_case.case_id or f"CASE_{uuid.uuid4().hex[:8].upper()}"

            # Create or get patient if patient_info provided
            patient = None
            if pydantic_case.patient_info and pydantic_case.patient_info.patient_id:
                patient = await PatientCRUD.create_patient(
                    db,
                    patient_id=pydantic_case.patient_info.patient_id,
                    age=pydantic_case.patient_info.age,
                    gender=pydantic_case.patient_info.gender,
                    medical_record_number=pydantic_case.patient_info.medical_record_number
                )

            # Create main triage case
            db_case = TriageCase(
                case_id=case_id,
                patient_id=patient.id if patient else None,
                symptoms_text=pydantic_case.symptoms_text,
                chief_complaint=pydantic_case.chief_complaint,
                medical_history=pydantic_case.medical_history,
                additional_notes=pydantic_case.additional_notes,
                primary_data_type=DataTypeEnum(pydantic_case.primary_data_type.value) if pydantic_case.primary_data_type else None,
                priority_level=UrgencyLevelEnum(pydantic_case.priority_level.value) if pydantic_case.priority_level else None,
                target_department=pydantic_case.target_department,
                specialty_required=pydantic_case.specialty_required,
                requires_vision_analysis=pydantic_case.requires_vision_analysis,
                requires_text_analysis=pydantic_case.requires_text_analysis,
                requires_structured_analysis=pydantic_case.requires_structured_analysis
            )

            db.add(db_case)
            await db.flush()  # Get the ID

            # Add structured data
            if pydantic_case.structured_data:
                for struct_data in pydantic_case.structured_data:
                    db_struct = CaseStructuredData(
                        triage_case_id=db_case.id,
                        data_type=StructuredDataTypeEnum(struct_data.data_type.value),
                        data=struct_data.data,
                        units=struct_data.units,
                        reference_ranges=struct_data.reference_ranges,
                        test_date=struct_data.test_date
                    )
                    db.add(db_struct)

            # Add images
            if pydantic_case.images:
                for image_data in pydantic_case.images:
                    db_image = CaseImage(
                        triage_case_id=db_case.id,
                        image_path=image_data.image_path,
                        image_type=image_data.image_type,
                        file_size=image_data.file_size,
                        uploaded_at=image_data.uploaded_at
                    )
                    db.add(db_image)

            logger.info(f"Created triage case: {case_id}")
            return db_case

        except Exception as e:
            await db.rollback()
            logger.error(f"Error creating triage case: {e}")
            raise

    @staticmethod
    async def get_triage_case_by_id(
        db: AsyncSession,
        case_id: str,
        include_relations: bool = True
    ) -> Optional[TriageCase]:
        """Get triage case by case_id with optional relations"""
        try:
            stmt = select(TriageCase).where(TriageCase.case_id == case_id)

            if include_relations:
                stmt = stmt.options(
                    selectinload(TriageCase.patient),
                    selectinload(TriageCase.structured_data),
                    selectinload(TriageCase.images),
                    selectinload(TriageCase.processing_results),
                    selectinload(TriageCase.triage_result)
                )

            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting triage case {case_id}: {e}")
            raise

    @staticmethod
    async def get_cases_by_priority(
        db: AsyncSession,
        priority: UrgencyLevelEnum,
        limit: int = 50
    ) -> List[TriageCase]:
        """Get cases by priority level"""
        try:
            stmt = (
                select(TriageCase)
                .where(TriageCase.priority_level == priority)
                .order_by(desc(TriageCase.created_at))
                .limit(limit)
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting cases by priority {priority}: {e}")
            raise

    @staticmethod
    async def get_cases_requiring_processing(
        db: AsyncSession,
        processing_type: str,
        limit: int = 10
    ) -> List[TriageCase]:
        """Get cases that require specific type of processing"""
        try:
            conditions = {
                'vision': TriageCase.requires_vision_analysis == True,
                'text': TriageCase.requires_text_analysis == True,
                'structured': TriageCase.requires_structured_analysis == True
            }

            if processing_type not in conditions:
                raise ValueError(f"Invalid processing type: {processing_type}")

            stmt = (
                select(TriageCase)
                .where(conditions[processing_type])
                .order_by(desc(TriageCase.created_at))
                .limit(limit)
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting cases requiring {processing_type} processing: {e}")
            raise

    @staticmethod
    async def update_case_priority(
        db: AsyncSession,
        case_id: str,
        priority: UrgencyLevelEnum
    ) -> Optional[TriageCase]:
        """Update case priority level"""
        try:
            stmt = (
                update(TriageCase)
                .where(TriageCase.case_id == case_id)
                .values(priority_level=priority, updated_at=datetime.utcnow())
                .returning(TriageCase)
            )
            result = await db.execute(stmt)
            case = result.scalar_one_or_none()

            if case:
                logger.info(f"Updated case {case_id} priority to {priority}")

            return case
        except Exception as e:
            logger.error(f"Error updating case priority {case_id}: {e}")
            raise


# =============================================================================
# Case Processing CRUD Operations
# =============================================================================

class CaseProcessingCRUD:
    """CRUD operations for CaseProcessing model"""

    @staticmethod
    async def create_processing_record(
        db: AsyncSession,
        case_id: str,
        agent_type: str,
        processing_step: str,
        status: ProcessingStatusEnum = ProcessingStatusEnum.PENDING,
        raw_output: Optional[Dict[str, Any]] = None,
        synthesized_output: Optional[str] = None,
        **kwargs
    ) -> CaseProcessing:
        """Create a new processing record"""
        try:
            # Get case
            case = await TriageCaseCRUD.get_triage_case_by_id(db, case_id, include_relations=False)
            if not case:
                raise ValueError(f"Triage case not found: {case_id}")

            processing = CaseProcessing(
                triage_case_id=case.id,
                agent_type=agent_type,
                processing_step=processing_step,
                status=status,
                raw_output=raw_output,
                synthesized_output=synthesized_output,
                **kwargs
            )

            db.add(processing)
            await db.flush()

            logger.info(f"Created processing record for case {case_id}: {agent_type}/{processing_step}")
            return processing

        except Exception as e:
            logger.error(f"Error creating processing record: {e}")
            raise

    @staticmethod
    async def update_processing_status(
        db: AsyncSession,
        processing_id: int,
        status: ProcessingStatusEnum,
        raw_output: Optional[Dict[str, Any]] = None,
        synthesized_output: Optional[str] = None,
        error_message: Optional[str] = None,
        processing_time_ms: Optional[int] = None
    ) -> Optional[CaseProcessing]:
        """Update processing record status and results"""
        try:
            updates = {
                'status': status,
                'completed_at': datetime.utcnow() if status in [ProcessingStatusEnum.COMPLETED, ProcessingStatusEnum.FAILED] else None
            }

            if raw_output is not None:
                updates['raw_output'] = raw_output
            if synthesized_output is not None:
                updates['synthesized_output'] = synthesized_output
            if error_message is not None:
                updates['error_message'] = error_message
            if processing_time_ms is not None:
                updates['processing_time_ms'] = processing_time_ms

            stmt = (
                update(CaseProcessing)
                .where(CaseProcessing.id == processing_id)
                .values(**updates)
                .returning(CaseProcessing)
            )
            result = await db.execute(stmt)
            processing = result.scalar_one_or_none()

            if processing:
                logger.info(f"Updated processing record {processing_id} status to {status}")

            return processing
        except Exception as e:
            logger.error(f"Error updating processing status {processing_id}: {e}")
            raise

    @staticmethod
    async def get_case_processing_history(
        db: AsyncSession,
        case_id: str
    ) -> List[CaseProcessing]:
        """Get all processing records for a case"""
        try:
            case = await TriageCaseCRUD.get_triage_case_by_id(db, case_id, include_relations=False)
            if not case:
                return []

            stmt = (
                select(CaseProcessing)
                .where(CaseProcessing.triage_case_id == case.id)
                .order_by(asc(CaseProcessing.started_at))
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting processing history for case {case_id}: {e}")
            raise


# =============================================================================
# Triage Result CRUD Operations
# =============================================================================

class TriageResultCRUD:
    """CRUD operations for TriageResult model"""

    @staticmethod
    async def create_triage_result(
        db: AsyncSession,
        case_id: str,
        final_triage_score: float,
        urgency_level: UrgencyLevelEnum,
        recommendations: Optional[List[str]] = None,
        **kwargs
    ) -> TriageResult:
        """Create final triage result"""
        try:
            case = await TriageCaseCRUD.get_triage_case_by_id(db, case_id, include_relations=False)
            if not case:
                raise ValueError(f"Triage case not found: {case_id}")

            # Check if result already exists
            existing = await TriageResultCRUD.get_result_by_case_id(db, case_id)
            if existing:
                logger.warning(f"Triage result already exists for case {case_id}")
                return existing

            result = TriageResult(
                triage_case_id=case.id,
                final_triage_score=final_triage_score,
                urgency_level=urgency_level,
                recommendations=recommendations,
                **kwargs
            )

            db.add(result)
            await db.flush()

            # Update case priority based on triage result
            await TriageCaseCRUD.update_case_priority(db, case_id, urgency_level)

            logger.info(f"Created triage result for case {case_id}: score={final_triage_score}, urgency={urgency_level}")
            return result

        except Exception as e:
            logger.error(f"Error creating triage result: {e}")
            raise

    @staticmethod
    async def get_result_by_case_id(db: AsyncSession, case_id: str) -> Optional[TriageResult]:
        """Get triage result by case_id"""
        try:
            case = await TriageCaseCRUD.get_triage_case_by_id(db, case_id, include_relations=False)
            if not case:
                return None

            stmt = select(TriageResult).where(TriageResult.triage_case_id == case.id)
            result = await db.execute(stmt)
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting triage result for case {case_id}: {e}")
            raise

    @staticmethod
    async def get_high_priority_cases(
        db: AsyncSession,
        limit: int = 20
    ) -> List[TriageResult]:
        """Get cases with high triage scores for immediate attention"""
        try:
            stmt = (
                select(TriageResult)
                .options(joinedload(TriageResult.triage_case))
                .where(TriageResult.final_triage_score >= 0.7)
                .order_by(desc(TriageResult.final_triage_score))
                .limit(limit)
            )
            result = await db.execute(stmt)
            return result.scalars().all()
        except Exception as e:
            logger.error(f"Error getting high priority cases: {e}")
            raise


# =============================================================================
# Audit and Analytics CRUD Operations
# =============================================================================

class AuditCRUD:
    """CRUD operations for audit logging and analytics"""

    @staticmethod
    async def log_event(
        db: AsyncSession,
        event_type: str,
        entity_type: str,
        entity_id: Optional[int] = None,
        user_id: Optional[str] = None,
        event_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> SystemAuditLog:
        """Create audit log entry"""
        try:
            log_entry = SystemAuditLog(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                user_id=user_id,
                event_data=event_data,
                **kwargs
            )

            db.add(log_entry)
            await db.flush()

            return log_entry
        except Exception as e:
            logger.error(f"Error creating audit log: {e}")
            raise

    @staticmethod
    async def get_case_analytics(
        db: AsyncSession,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get analytics for triage cases"""
        try:
            # Build date filter
            date_filter = []
            if start_date:
                date_filter.append(TriageCase.created_at >= start_date)
            if end_date:
                date_filter.append(TriageCase.created_at <= end_date)

            # Total cases
            total_cases_stmt = select(func.count(TriageCase.id))
            if date_filter:
                total_cases_stmt = total_cases_stmt.where(and_(*date_filter))

            total_cases = await db.scalar(total_cases_stmt) or 0

            # Cases by priority
            priority_stmt = (
                select(TriageCase.priority_level, func.count(TriageCase.id))
                .group_by(TriageCase.priority_level)
            )
            if date_filter:
                priority_stmt = priority_stmt.where(and_(*date_filter))

            priority_result = await db.execute(priority_stmt)
            priority_distribution = {
                priority or "unknown": count
                for priority, count in priority_result.fetchall()
            }

            # Average processing times
            avg_processing_stmt = (
                select(
                    CaseProcessing.agent_type,
                    func.avg(CaseProcessing.processing_time_ms).label('avg_time')
                )
                .group_by(CaseProcessing.agent_type)
                .where(CaseProcessing.processing_time_ms.isnot(None))
            )

            avg_processing_result = await db.execute(avg_processing_stmt)
            avg_processing_times = {
                agent: round(avg_time, 2)
                for agent, avg_time in avg_processing_result.fetchall()
            }

            return {
                "total_cases": total_cases,
                "priority_distribution": priority_distribution,
                "avg_processing_times_ms": avg_processing_times,
                "date_range": {
                    "start": start_date.isoformat() if start_date else None,
                    "end": end_date.isoformat() if end_date else None
                }
            }
        except Exception as e:
            logger.error(f"Error getting case analytics: {e}")
            raise


# =============================================================================
# Bulk Operations
# =============================================================================

class BulkOperations:
    """Bulk database operations for efficiency"""

    @staticmethod
    async def bulk_create_cases(
        db: AsyncSession,
        pydantic_cases: List[PydanticTriageCase]
    ) -> List[TriageCase]:
        """Create multiple triage cases in a single transaction"""
        try:
            created_cases = []

            for pydantic_case in pydantic_cases:
                case = await TriageCaseCRUD.create_triage_case(db, pydantic_case)
                created_cases.append(case)

            logger.info(f"Bulk created {len(created_cases)} triage cases")
            return created_cases

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in bulk case creation: {e}")
            raise

    @staticmethod
    async def cleanup_old_records(
        db: AsyncSession,
        days_old: int = 365
    ) -> Dict[str, int]:
        """Clean up old records beyond retention period"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)

            # Count records to be deleted
            old_cases_count = await db.scalar(
                select(func.count(TriageCase.id))
                .where(TriageCase.created_at < cutoff_date)
            ) or 0

            old_audit_count = await db.scalar(
                select(func.count(SystemAuditLog.id))
                .where(SystemAuditLog.timestamp < cutoff_date)
            ) or 0

            # Delete old audit logs (cascading will handle related records)
            await db.execute(
                delete(SystemAuditLog)
                .where(SystemAuditLog.timestamp < cutoff_date)
            )

            # Note: Be careful with deleting triage cases as they may be needed for medical records
            # Only delete if explicitly allowed by data retention policies

            logger.info(f"Cleaned up {old_audit_count} old audit records")

            return {
                "old_cases_found": old_cases_count,
                "audit_records_deleted": old_audit_count
            }

        except Exception as e:
            await db.rollback()
            logger.error(f"Error in cleanup operation: {e}")
            raise


# Export CRUD classes
__all__ = [
    "PatientCRUD",
    "TriageCaseCRUD",
    "CaseProcessingCRUD",
    "TriageResultCRUD",
    "AuditCRUD",
    "BulkOperations"
]
