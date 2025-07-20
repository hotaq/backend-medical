"""
Database Migration and Initialization Utilities for Medical Triage-BOTS

This module provides utilities for database schema migrations, data migrations,
and database initialization. It supports versioned schema changes and data
transformations for the Medical Triage-BOTS system.

Features:
- Schema version management
- Forward and backward migrations
- Data migration utilities
- Database backup before migrations
- Migration history tracking
- Rollback capabilities
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select, insert, update, delete
from sqlalchemy.exc import SQLAlchemyError
import json
import asyncio

from .config import AsyncSessionLocal, engine, backup_database
from .models import Base, SystemAuditLog

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Custom exception for migration errors"""
    pass


class DatabaseMigration:
    """
    Base class for database migrations.

    Each migration should inherit from this class and implement
    the up() and down() methods.
    """

    def __init__(self):
        self.version: str = "0.0.0"
        self.description: str = "Base migration"
        self.dependencies: List[str] = []

    async def up(self, session: AsyncSession) -> None:
        """
        Apply the migration (forward).

        Args:
            session: Database session
        """
        raise NotImplementedError("Subclasses must implement up() method")

    async def down(self, session: AsyncSession) -> None:
        """
        Reverse the migration (backward).

        Args:
            session: Database session
        """
        raise NotImplementedError("Subclasses must implement down() method")

    async def validate(self, session: AsyncSession) -> bool:
        """
        Validate that the migration was applied correctly.

        Args:
            session: Database session

        Returns:
            bool: True if validation passes
        """
        return True


class InitialSchemaMigration(DatabaseMigration):
    """Initial schema creation migration"""

    def __init__(self):
        super().__init__()
        self.version = "1.0.0"
        self.description = "Create initial schema for Medical Triage-BOTS"

    async def up(self, session: AsyncSession) -> None:
        """Create all tables"""
        try:
            logger.info("Creating initial database schema...")

            # Create all tables
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info("Initial schema created successfully")

        except Exception as e:
            logger.error(f"Failed to create initial schema: {e}")
            raise MigrationError(f"Initial schema creation failed: {e}")

    async def down(self, session: AsyncSession) -> None:
        """Drop all tables"""
        try:
            logger.info("Dropping all database tables...")

            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

            logger.info("All tables dropped successfully")

        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            raise MigrationError(f"Schema cleanup failed: {e}")

    async def validate(self, session: AsyncSession) -> bool:
        """Validate that all tables were created"""
        try:
            # Check if key tables exist
            tables_to_check = [
                'patients', 'triage_cases', 'case_structured_data',
                'case_images', 'case_processing', 'triage_results',
                'system_audit_log', 'model_performance_metrics'
            ]

            for table_name in tables_to_check:
                result = await session.execute(
                    text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                )
                if not result.scalar():
                    logger.error(f"Table {table_name} not found")
                    return False

            logger.info("Schema validation passed")
            return True

        except Exception as e:
            logger.error(f"Schema validation failed: {e}")
            return False


class AddIndexesMigration(DatabaseMigration):
    """Add performance indexes migration"""

    def __init__(self):
        super().__init__()
        self.version = "1.1.0"
        self.description = "Add performance indexes to key tables"
        self.dependencies = ["1.0.0"]

    async def up(self, session: AsyncSession) -> None:
        """Add performance indexes"""
        try:
            logger.info("Adding performance indexes...")

            indexes = [
                "CREATE INDEX IF NOT EXISTS idx_case_urgency_created ON triage_cases(urgency_level, created_at)",
                "CREATE INDEX IF NOT EXISTS idx_processing_agent_status ON case_processing(agent_type, status)",
                "CREATE INDEX IF NOT EXISTS idx_triage_score_processed ON triage_results(final_triage_score, processed_at)",
                "CREATE INDEX IF NOT EXISTS idx_audit_event_timestamp ON system_audit_log(event_type, timestamp)",
            ]

            for index_sql in indexes:
                await session.execute(text(index_sql))

            logger.info("Performance indexes added successfully")

        except Exception as e:
            logger.error(f"Failed to add indexes: {e}")
            raise MigrationError(f"Index creation failed: {e}")

    async def down(self, session: AsyncSession) -> None:
        """Remove performance indexes"""
        try:
            logger.info("Removing performance indexes...")

            indexes = [
                "DROP INDEX IF EXISTS idx_case_urgency_created",
                "DROP INDEX IF EXISTS idx_processing_agent_status",
                "DROP INDEX IF EXISTS idx_triage_score_processed",
                "DROP INDEX IF EXISTS idx_audit_event_timestamp",
            ]

            for index_sql in indexes:
                await session.execute(text(index_sql))

            logger.info("Performance indexes removed successfully")

        except Exception as e:
            logger.error(f"Failed to remove indexes: {e}")
            raise MigrationError(f"Index removal failed: {e}")


class MigrationManager:
    """
    Manages database migrations and schema versioning.
    """

    def __init__(self):
        self.migrations: Dict[str, DatabaseMigration] = {}
        self.migration_table = "schema_migrations"
        self._register_migrations()

    def _register_migrations(self):
        """Register all available migrations"""
        migrations = [
            InitialSchemaMigration(),
            AddIndexesMigration(),
        ]

        for migration in migrations:
            self.migrations[migration.version] = migration

    async def _ensure_migration_table(self, session: AsyncSession):
        """Ensure the migration tracking table exists"""
        try:
            await session.execute(text(f"""
                CREATE TABLE IF NOT EXISTS {self.migration_table} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT UNIQUE NOT NULL,
                    description TEXT,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    checksum TEXT
                )
            """))
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to create migration table: {e}")
            raise

    async def get_applied_migrations(self, session: AsyncSession) -> List[str]:
        """Get list of applied migration versions"""
        try:
            await self._ensure_migration_table(session)

            result = await session.execute(
                text(f"SELECT version FROM {self.migration_table} ORDER BY applied_at")
            )
            return [row[0] for row in result.fetchall()]
        except Exception as e:
            logger.error(f"Failed to get applied migrations: {e}")
            return []

    async def mark_migration_applied(
        self,
        session: AsyncSession,
        version: str,
        description: str,
        checksum: str = ""
    ):
        """Mark a migration as applied"""
        try:
            await session.execute(
                text(f"""
                    INSERT OR REPLACE INTO {self.migration_table}
                    (version, description, applied_at, checksum)
                    VALUES (?, ?, ?, ?)
                """),
                (version, description, datetime.utcnow(), checksum)
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to mark migration as applied: {e}")
            raise

    async def unmark_migration(self, session: AsyncSession, version: str):
        """Remove a migration from applied list"""
        try:
            await session.execute(
                text(f"DELETE FROM {self.migration_table} WHERE version = ?"),
                (version,)
            )
            await session.commit()
        except Exception as e:
            logger.error(f"Failed to unmark migration: {e}")
            raise

    def get_pending_migrations(self, applied_versions: List[str]) -> List[DatabaseMigration]:
        """Get list of pending migrations"""
        pending = []

        for version in sorted(self.migrations.keys()):
            if version not in applied_versions:
                migration = self.migrations[version]

                # Check if dependencies are satisfied
                if all(dep in applied_versions for dep in migration.dependencies):
                    pending.append(migration)
                else:
                    logger.warning(f"Migration {version} has unmet dependencies: {migration.dependencies}")

        return pending

    async def migrate_up(self, target_version: Optional[str] = None) -> bool:
        """
        Apply pending migrations.

        Args:
            target_version: Optional target version. If None, applies all pending.

        Returns:
            bool: True if all migrations succeeded
        """
        try:
            logger.info("Starting database migration...")

            async with AsyncSessionLocal() as session:
                applied_versions = await self.get_applied_migrations(session)
                pending = self.get_pending_migrations(applied_versions)

                if target_version:
                    # Filter to only migrations up to target
                    pending = [m for m in pending if m.version <= target_version]

                if not pending:
                    logger.info("No pending migrations")
                    return True

                # Backup database before migrations
                backup_path = f"backup_before_migration_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                if await backup_database(backup_path):
                    logger.info(f"Database backed up to {backup_path}")

                # Apply migrations
                for migration in pending:
                    logger.info(f"Applying migration {migration.version}: {migration.description}")

                    try:
                        await migration.up(session)
                        await session.commit()

                        # Validate migration
                        if not await migration.validate(session):
                            raise MigrationError(f"Migration {migration.version} validation failed")

                        # Mark as applied
                        await self.mark_migration_applied(
                            session,
                            migration.version,
                            migration.description
                        )

                        logger.info(f"Migration {migration.version} applied successfully")

                    except Exception as e:
                        await session.rollback()
                        logger.error(f"Migration {migration.version} failed: {e}")
                        raise MigrationError(f"Migration {migration.version} failed: {e}")

                logger.info("All migrations applied successfully")
                return True

        except Exception as e:
            logger.error(f"Migration process failed: {e}")
            return False

    async def migrate_down(self, target_version: str) -> bool:
        """
        Rollback migrations to target version.

        Args:
            target_version: Version to rollback to

        Returns:
            bool: True if rollback succeeded
        """
        try:
            logger.info(f"Rolling back to version {target_version}...")

            async with AsyncSessionLocal() as session:
                applied_versions = await self.get_applied_migrations(session)

                # Find migrations to rollback (in reverse order)
                to_rollback = []
                for version in sorted(applied_versions, reverse=True):
                    if version > target_version and version in self.migrations:
                        to_rollback.append(self.migrations[version])

                if not to_rollback:
                    logger.info("No migrations to rollback")
                    return True

                # Backup database before rollback
                backup_path = f"backup_before_rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                if await backup_database(backup_path):
                    logger.info(f"Database backed up to {backup_path}")

                # Rollback migrations
                for migration in to_rollback:
                    logger.info(f"Rolling back migration {migration.version}: {migration.description}")

                    try:
                        await migration.down(session)
                        await session.commit()

                        # Remove from applied list
                        await self.unmark_migration(session, migration.version)

                        logger.info(f"Migration {migration.version} rolled back successfully")

                    except Exception as e:
                        await session.rollback()
                        logger.error(f"Rollback of {migration.version} failed: {e}")
                        raise MigrationError(f"Rollback of {migration.version} failed: {e}")

                logger.info(f"Successfully rolled back to version {target_version}")
                return True

        except Exception as e:
            logger.error(f"Rollback process failed: {e}")
            return False

    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            async with AsyncSessionLocal() as session:
                applied_versions = await self.get_applied_migrations(session)
                pending = self.get_pending_migrations(applied_versions)

                return {
                    "current_version": applied_versions[-1] if applied_versions else None,
                    "applied_migrations": applied_versions,
                    "pending_migrations": [m.version for m in pending],
                    "total_migrations": len(self.migrations),
                    "applied_count": len(applied_versions),
                    "pending_count": len(pending)
                }
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {"error": str(e)}


# Global migration manager instance
migration_manager = MigrationManager()


# Convenience functions
async def initialize_database():
    """Initialize database with all migrations"""
    return await migration_manager.migrate_up()


async def migrate_database(target_version: Optional[str] = None):
    """Apply database migrations"""
    return await migration_manager.migrate_up(target_version)


async def rollback_database(target_version: str):
    """Rollback database migrations"""
    return await migration_manager.migrate_down(target_version)


async def get_migration_status():
    """Get migration status"""
    return await migration_manager.get_migration_status()


# Export public API
__all__ = [
    "DatabaseMigration",
    "MigrationManager",
    "MigrationError",
    "migration_manager",
    "initialize_database",
    "migrate_database",
    "rollback_database",
    "get_migration_status"
]
