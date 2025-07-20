"""
Database Configuration for Medical Triage-BOTS System

This module provides database configuration, connection management, and
utilities for the Medical Triage-BOTS system using SQLAlchemy async.

Features:
- Async SQLAlchemy configuration
- Database connection pooling
- Health monitoring
- Migration support
- Error handling and logging

Usage:
    from app.database.config import engine, AsyncSessionLocal, init_database
"""

import asyncio
import logging
import os
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql import text

# Setup logging
logger = logging.getLogger(__name__)

# Database configuration
class DatabaseConfig:
    """Database configuration settings"""

    def __init__(self):
        # Default to SQLite for development
        self.database_url = os.getenv(
            "DATABASE_URL",
            "sqlite+aiosqlite:///./medical_triage_bots.db"
        )

        # Connection pool settings
        self.pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
        self.max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
        self.pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        self.pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "3600"))

        # SQLite specific settings
        self.echo = os.getenv("DB_ECHO", "false").lower() == "true"
        self.echo_pool = os.getenv("DB_ECHO_POOL", "false").lower() == "true"

        # Application settings
        self.auto_create_tables = os.getenv("DB_AUTO_CREATE_TABLES", "true").lower() == "true"
        self.enable_foreign_keys = os.getenv("DB_ENABLE_FOREIGN_KEYS", "true").lower() == "true"

# Global configuration instance
config = DatabaseConfig()

# Create async engine
def create_engine():
    """Create SQLAlchemy async engine with appropriate configuration"""

    if config.database_url.startswith("sqlite"):
        # SQLite specific configuration
        engine = create_async_engine(
            config.database_url,
            echo=config.echo,
            echo_pool=config.echo_pool,
            poolclass=StaticPool,
            connect_args={
                "check_same_thread": False,
                "timeout": 20
            },
            future=True
        )
    else:
        # PostgreSQL and other databases
        engine = create_async_engine(
            config.database_url,
            echo=config.echo,
            echo_pool=config.echo_pool,
            pool_size=config.pool_size,
            max_overflow=config.max_overflow,
            pool_timeout=config.pool_timeout,
            pool_recycle=config.pool_recycle,
            future=True
        )

    return engine

# Global engine instance
engine = create_engine()

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Database instance for compatibility
database = None


class DatabaseManager:
    """Database manager for handling connections and sessions"""

    def __init__(self):
        self.engine = engine
        self.session_factory = AsyncSessionLocal

    @asynccontextmanager
    async def get_session(self):
        """Get database session with automatic cleanup"""
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()


# Dependency function for FastAPI
async def get_db_session():
    """Database session dependency for FastAPI"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_database():
    """Initialize database tables"""
    try:
        from .models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


async def check_database_health() -> Dict[str, Any]:
    """Check database health"""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            test_value = result.scalar()
            return {
                "status": "healthy" if test_value == 1 else "unhealthy",
                "connection": True,
                "database_type": "sqlite"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "connection": False,
            "error": str(e)
        }


async def get_database_stats() -> Dict[str, Any]:
    """Get database statistics"""
    stats = {
        "total_tables": 0,
        "database_type": "sqlite",
        "status": "operational"
    }

    try:
        async with AsyncSessionLocal() as session:
            # Get table count
            result = await session.execute(
                text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")
            )
            stats["total_tables"] = result.scalar() or 0
    except Exception as e:
        stats["error"] = str(e)

    return stats


async def cleanup_database():
    """Cleanup database connections"""
    try:
        await engine.dispose()
        logger.info("Database cleanup completed")
    except Exception as e:
        logger.error(f"Database cleanup error: {e}")


async def execute_raw_query(query: str, values: Optional[Dict] = None):
    """Execute raw SQL query"""
    async with AsyncSessionLocal() as session:
        result = await session.execute(text(query), values or {})
        return result.fetchall()


async def backup_database(backup_path: str) -> bool:
    """Backup database (SQLite only)"""
    try:
        import shutil
        db_path = config.database_url.replace("sqlite+aiosqlite:///", "")
        if os.path.exists(db_path):
            shutil.copy2(db_path, backup_path)
            return True
        return False
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        return False
