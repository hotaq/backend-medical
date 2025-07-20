"""
Database Models for Medical Triage-BOTS System

This module defines SQLAlchemy models for storing triage cases, patient data,
processing results, and detailed logging for the multi-agent workflow.

Designed to support:
- Multi-modal triage cases (text, structured data, images)
- Detailed logging of each processing step
- VisionBOT and TextBOT agent results
- Final triage scores and decisions
- Audit trails and analytics
"""

from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import (
    Boolean, Column, DateTime, Float, Integer, String, Text, JSON,
    ForeignKey, Index, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class DataTypeEnum(str, enum.Enum):
    """Enum for different types of data that can be processed"""
    TEXT = "text"
    STRUCTURED = "structured"
    IMAGE = "image"
    MIXED = "mixed"


class UrgencyLevelEnum(str, enum.Enum):
    """Enum for urgency levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ProcessingStatusEnum(str, enum.Enum):
    """Enum for processing status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StructuredDataTypeEnum(str, enum.Enum):
    """Enum for types of structured medical data"""
    BLOOD_TEST = "blood_test"
    VITAL_SIGNS = "vital_signs"
    MEDICAL_HISTORY = "medical_history"
    LAB_RESULTS = "lab_results"
    OTHER = "other"


class Patient(Base):
    """Patient information table"""
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(String(50), unique=True, index=True, nullable=False)
    age = Column(Integer, nullable=True)
    gender = Column(String(20), nullable=True)
    medical_record_number = Column(String(50), nullable=True, index=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    triage_cases = relationship("TriageCase", back_populates="patient")

    def __repr__(self):
        return f"<Patient(id={self.id}, patient_id='{self.patient_id}', age={self.age})>"


class TriageCase(Base):
    """Main triage case table storing core case information"""
    __tablename__ = "triage_cases"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(50), unique=True, index=True, nullable=False)

    # Patient reference
    patient_id = Column(Integer, ForeignKey("patients.id"), nullable=True)

    # Text data
    symptoms_text = Column(Text, nullable=True)
    chief_complaint = Column(Text, nullable=True)
    medical_history = Column(Text, nullable=True)
    additional_notes = Column(Text, nullable=True)

    # Case metadata
    primary_data_type = Column(SQLEnum(DataTypeEnum), nullable=True)
    priority_level = Column(SQLEnum(UrgencyLevelEnum), nullable=True)
    target_department = Column(String(100), nullable=True)
    specialty_required = Column(String(100), nullable=True)

    # Processing flags
    requires_vision_analysis = Column(Boolean, default=False)
    requires_text_analysis = Column(Boolean, default=False)
    requires_structured_analysis = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    patient = relationship("Patient", back_populates="triage_cases")
    structured_data = relationship("CaseStructuredData", back_populates="triage_case")
    images = relationship("CaseImage", back_populates="triage_case")
    processing_results = relationship("CaseProcessing", back_populates="triage_case")
    triage_result = relationship("TriageResult", back_populates="triage_case", uselist=False)

    # Indexes
    __table_args__ = (
        Index('idx_case_created_at', 'created_at'),
        Index('idx_case_priority', 'priority_level'),
        Index('idx_case_department', 'target_department'),
    )

    def __repr__(self):
        return f"<TriageCase(id={self.id}, case_id='{self.case_id}', priority='{self.priority_level}')>"


class CaseStructuredData(Base):
    """Structured medical data associated with triage cases"""
    __tablename__ = "case_structured_data"

    id = Column(Integer, primary_key=True, index=True)
    triage_case_id = Column(Integer, ForeignKey("triage_cases.id"), nullable=False)

    # Data information
    data_type = Column(SQLEnum(StructuredDataTypeEnum), nullable=False)
    data = Column(JSON, nullable=False)  # The actual structured data
    units = Column(JSON, nullable=True)  # Units for numeric values
    reference_ranges = Column(JSON, nullable=True)  # Normal reference ranges
    test_date = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    triage_case = relationship("TriageCase", back_populates="structured_data")

    # Indexes
    __table_args__ = (
        Index('idx_structured_data_type', 'data_type'),
        Index('idx_structured_data_case', 'triage_case_id'),
    )

    def __repr__(self):
        return f"<CaseStructuredData(id={self.id}, type='{self.data_type}', case_id={self.triage_case_id})>"


class CaseImage(Base):
    """Medical images associated with triage cases"""
    __tablename__ = "case_images"

    id = Column(Integer, primary_key=True, index=True)
    triage_case_id = Column(Integer, ForeignKey("triage_cases.id"), nullable=False)

    # Image information
    image_path = Column(String(500), nullable=False)
    image_type = Column(String(50), nullable=True)  # 'retinal', 'xray', 'ct_scan', etc.
    file_size = Column(Integer, nullable=True)

    # Processing status for this image
    processed = Column(Boolean, default=False)
    processing_error = Column(Text, nullable=True)

    # Timestamps
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    triage_case = relationship("TriageCase", back_populates="images")

    # Indexes
    __table_args__ = (
        Index('idx_image_type', 'image_type'),
        Index('idx_image_case', 'triage_case_id'),
        Index('idx_image_processed', 'processed'),
    )

    def __repr__(self):
        return f"<CaseImage(id={self.id}, type='{self.image_type}', case_id={self.triage_case_id})>"


class CaseProcessing(Base):
    """Detailed processing results from each agent/step"""
    __tablename__ = "case_processing"

    id = Column(Integer, primary_key=True, index=True)
    triage_case_id = Column(Integer, ForeignKey("triage_cases.id"), nullable=False)

    # Processing information
    agent_type = Column(String(50), nullable=False)  # 'vision_bot', 'text_bot', 'chief_bot'
    processing_step = Column(String(50), nullable=False)  # 'tool', 'synthesizer', 'final'
    status = Column(SQLEnum(ProcessingStatusEnum), nullable=False)

    # Raw outputs from ML models/tools
    raw_output = Column(JSON, nullable=True)
    confidence_score = Column(Float, nullable=True)
    model_version = Column(String(50), nullable=True)

    # Synthesized outputs from LLM
    synthesized_output = Column(Text, nullable=True)
    llm_model_used = Column(String(100), nullable=True)

    # Processing metadata
    processing_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)

    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    triage_case = relationship("TriageCase", back_populates="processing_results")

    # Indexes
    __table_args__ = (
        Index('idx_processing_agent', 'agent_type'),
        Index('idx_processing_status', 'status'),
        Index('idx_processing_case', 'triage_case_id'),
        Index('idx_processing_step', 'processing_step'),
    )

    def __repr__(self):
        return f"<CaseProcessing(id={self.id}, agent='{self.agent_type}', step='{self.processing_step}', status='{self.status}')>"


class TriageResult(Base):
    """Final triage results and decisions"""
    __tablename__ = "triage_results"

    id = Column(Integer, primary_key=True, index=True)
    triage_case_id = Column(Integer, ForeignKey("triage_cases.id"), nullable=False, unique=True)

    # Final results
    final_triage_score = Column(Float, nullable=False)  # 0.0 to 1.0
    urgency_level = Column(SQLEnum(UrgencyLevelEnum), nullable=False)
    estimated_wait_time = Column(Integer, nullable=True)  # minutes

    # Recommendations and decisions
    recommendations = Column(JSON, nullable=True)  # List of recommendations
    clinical_notes = Column(Text, nullable=True)

    # Processing summary
    vision_analysis_completed = Column(Boolean, default=False)
    text_analysis_completed = Column(Boolean, default=False)
    structured_analysis_completed = Column(Boolean, default=False)

    # Algorithm details
    scoring_algorithm_version = Column(String(50), nullable=True)
    feature_weights = Column(JSON, nullable=True)  # Weights used in final scoring

    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    review_required = Column(Boolean, default=False)
    reviewed_by = Column(String(100), nullable=True)
    review_notes = Column(Text, nullable=True)

    # Timestamps
    processed_at = Column(DateTime(timezone=True), server_default=func.now())
    reviewed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    triage_case = relationship("TriageCase", back_populates="triage_result")

    # Indexes
    __table_args__ = (
        Index('idx_triage_score', 'final_triage_score'),
        Index('idx_triage_urgency', 'urgency_level'),
        Index('idx_triage_processed', 'processed_at'),
        Index('idx_triage_review', 'review_required'),
    )

    def __repr__(self):
        return f"<TriageResult(id={self.id}, case_id={self.triage_case_id}, score={self.final_triage_score}, urgency='{self.urgency_level}')>"


class SystemAuditLog(Base):
    """System-wide audit log for tracking all activities"""
    __tablename__ = "system_audit_log"

    id = Column(Integer, primary_key=True, index=True)

    # What happened
    event_type = Column(String(100), nullable=False)  # 'case_created', 'processing_started', etc.
    entity_type = Column(String(50), nullable=False)  # 'triage_case', 'patient', etc.
    entity_id = Column(Integer, nullable=True)

    # Who did it
    user_id = Column(String(100), nullable=True)
    user_role = Column(String(50), nullable=True)

    # Details
    event_data = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)

    # Timestamp
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_audit_event_type', 'event_type'),
        Index('idx_audit_entity', 'entity_type', 'entity_id'),
        Index('idx_audit_timestamp', 'timestamp'),
        Index('idx_audit_user', 'user_id'),
    )

    def __repr__(self):
        return f"<SystemAuditLog(id={self.id}, event='{self.event_type}', entity='{self.entity_type}')>"


class ModelPerformanceMetrics(Base):
    """Track ML model performance over time"""
    __tablename__ = "model_performance_metrics"

    id = Column(Integer, primary_key=True, index=True)

    # Model information
    model_type = Column(String(50), nullable=False)  # 'vision_cnn', 'heart_disease_rf', etc.
    model_version = Column(String(50), nullable=False)

    # Performance metrics
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    auc_roc = Column(Float, nullable=True)

    # Processing metrics
    avg_processing_time_ms = Column(Float, nullable=True)
    total_predictions = Column(Integer, nullable=False, default=0)
    successful_predictions = Column(Integer, nullable=False, default=0)

    # Period information
    measurement_period_start = Column(DateTime(timezone=True), nullable=False)
    measurement_period_end = Column(DateTime(timezone=True), nullable=False)

    # Metadata
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Indexes
    __table_args__ = (
        Index('idx_metrics_model', 'model_type', 'model_version'),
        Index('idx_metrics_period', 'measurement_period_start', 'measurement_period_end'),
    )

    def __repr__(self):
        return f"<ModelPerformanceMetrics(id={self.id}, model='{self.model_type}', accuracy={self.accuracy})>"
