"""
Database Package for Medical Triage-BOTS System

This package provides comprehensive database management for the Medical Triage-BOTS
system, including models, CRUD operations, configuration, and utilities.

Features:
- SQLAlchemy async models for all entities
- CRUD operations for triage case management
- Database configuration and connection management
- Migration and initialization utilities
- Audit logging and analytics
- Performance monitoring

Usage:
    from app.database import init_database, get_db_session
    from app.database.crud import TriageCaseCRUD, PatientCRUD
    from app.database.models import TriageCase, Patient
"""

__version__ = "1.0.0"
__author__ = "Medical Triage-BOTS Team"

# Import core database components
from .config import (
    engine,
    AsyncSessionLocal,
    database,
    get_db_session,
    init_database,
    check_database_health,
    get_database_stats,
    cleanup_database,
    execute_raw_query,
    backup_database,
    config as db_config
)

from .models import (
    Base,
    Patient,
    TriageCase,
    CaseStructuredData,
    CaseImage,
    CaseProcessing,
    TriageResult,
    SystemAuditLog,
    ModelPerformanceMetrics,
    DataTypeEnum,
    UrgencyLevelEnum,
    ProcessingStatusEnum,
    StructuredDataTypeEnum
)

from .crud import (
    PatientCRUD,
    TriageCaseCRUD,
    CaseProcessingCRUD,
    TriageResultCRUD,
    AuditCRUD,
    BulkOperations
)

# Database initialization and management functions
async def initialize_database():
    """
    Initialize the database with all tables and initial data.

    This is a convenience wrapper around init_database() that can be
    called from application startup.
    """
    await init_database()

async def get_database_health():
    """
    Get database health status for monitoring.

    Returns:
        dict: Health status information
    """
    return await check_database_health()

async def get_database_statistics():
    """
    Get database statistics for analytics.

    Returns:
        dict: Database statistics
    """
    return await get_database_stats()

# Utility functions for common database operations
async def create_triage_case_with_session(pydantic_case):
    """
    Create a triage case with automatic session management.

    Args:
        pydantic_case: PydanticTriageCase instance

    Returns:
        TriageCase: Created database model instance
    """
    async with AsyncSessionLocal() as session:
        try:
            case = await TriageCaseCRUD.create_triage_case(session, pydantic_case)
            await session.commit()
            return case
        except Exception as e:
            await session.rollback()
            raise

async def get_case_with_session(case_id: str):
    """
    Get a triage case with automatic session management.

    Args:
        case_id: Case identifier

    Returns:
        TriageCase: Database model instance or None
    """
    async with AsyncSessionLocal() as session:
        return await TriageCaseCRUD.get_triage_case_by_id(session, case_id)

# Export all public APIs
__all__ = [
    # Core components
    "engine",
    "AsyncSessionLocal",
    "database",
    "get_db_session",
    "Base",

    # Initialization and management
    "init_database",
    "initialize_database",
    "cleanup_database",
    "check_database_health",
    "get_database_health",
    "get_database_stats",
    "get_database_statistics",
    "backup_database",
    "execute_raw_query",
    "db_config",

    # Models
    "Patient",
    "TriageCase",
    "CaseStructuredData",
    "CaseImage",
    "CaseProcessing",
    "TriageResult",
    "SystemAuditLog",
    "ModelPerformanceMetrics",

    # Enums
    "DataTypeEnum",
    "UrgencyLevelEnum",
    "ProcessingStatusEnum",
    "StructuredDataTypeEnum",

    # CRUD operations
    "PatientCRUD",
    "TriageCaseCRUD",
    "CaseProcessingCRUD",
    "TriageResultCRUD",
    "AuditCRUD",
    "BulkOperations",

    # Utility functions
    "create_triage_case_with_session",
    "get_case_with_session"
]

# Package metadata
PACKAGE_INFO = {
    "name": "Medical Triage-BOTS Database",
    "version": __version__,
    "description": "Comprehensive database management for medical triage system",
    "features": [
        "Async SQLAlchemy models",
        "Multi-agent workflow support",
        "Detailed audit logging",
        "Performance analytics",
        "Comprehensive CRUD operations",
        "Database health monitoring"
    ],
    "supported_databases": ["SQLite", "PostgreSQL (future)"],
    "python_requirements": ">=3.10"
}
