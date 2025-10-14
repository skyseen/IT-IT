"""Database connection manager for Kanban module."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.pool import QueuePool

from kanban.models import Base

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Singleton database connection manager.
    Handles connection pooling, retries, and session management.
    """

    _instance: Optional[DatabaseManager] = None
    _initialized: bool = False

    def __new__(cls, *args, **kwargs) -> DatabaseManager:
        """Create singleton instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path: Optional[str] = None):
        """Initialize database manager."""
        # Check if this instance is already initialized
        if DatabaseManager._initialized:
            return

        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        self.engine: Optional[Engine] = None
        self.Session: Optional[scoped_session] = None

        self._initialize_connection()
        DatabaseManager._initialized = True

    def _get_default_config_path(self) -> str:
        """Get default config path relative to project root."""
        # Assume we're in IT-IT/kanban/database.py
        project_root = Path(__file__).resolve().parent.parent
        config_file = project_root / "config" / "kanban_config.json"

        # If config doesn't exist, try production config
        if not config_file.exists():
            config_file = project_root / "config" / "kanban_config_production.json"

        return str(config_file)

    def _load_config(self) -> dict:
        """Load database configuration from JSON file."""
        try:
            with open(self.config_path, encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            raise

    def _initialize_connection(self) -> None:
        """Create database engine with connection pooling."""
        db_config = self.config["database"]

        # Build connection string
        connection_string = (
            f"postgresql://{db_config['username']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

        # Create engine with connection pooling
        self.engine = create_engine(
            connection_string,
            poolclass=QueuePool,
            pool_size=db_config.get("pool_size", 5),
            max_overflow=db_config.get("max_overflow", 3),
            pool_timeout=30,
            pool_recycle=3600,  # Recycle connections after 1 hour
            pool_pre_ping=True,  # Verify connections before using
            echo=False,  # Set to True for SQL logging during development
        )

        # Set up event listeners
        @event.listens_for(self.engine, "connect")
        def receive_connect(dbapi_conn, connection_record):
            """Event handler for new connections."""
            logger.debug("Database connection established")

        @event.listens_for(self.engine, "checkout")
        def receive_checkout(dbapi_conn, connection_record, connection_proxy):
            """Event handler for connection checkout from pool."""
            logger.debug("Connection checked out from pool")

        # Thread-safe session factory
        session_factory = sessionmaker(
            bind=self.engine,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
        self.Session = scoped_session(session_factory)

        logger.info(
            f"Database connection initialized: {db_config['host']}:{db_config['port']}/{db_config['database']}"
        )

    def get_session(self):
        """
        Get a new database session.

        Returns:
            Session: SQLAlchemy session object

        Usage:
            session = db_manager.get_session()
            try:
                # Use session
                session.add(obj)
                session.commit()
            except Exception as e:
                session.rollback()
                raise
            finally:
                session.close()
        """
        if self.Session is None:
            raise RuntimeError("Database not initialized")
        return self.Session()

    def create_tables(self) -> None:
        """Create all tables in the database."""
        if self.engine is None:
            raise RuntimeError("Database not initialized")

        logger.info("Creating database tables...")
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")

    def drop_tables(self) -> None:
        """Drop all tables from the database (use with caution!)."""
        if self.engine is None:
            raise RuntimeError("Database not initialized")

        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(self.engine)
        logger.warning("All tables dropped")

    def close_all_sessions(self) -> None:
        """Close all active sessions (call on app shutdown)."""
        if self.Session:
            self.Session.remove()
        if self.engine:
            self.engine.dispose()
        logger.info("All database connections closed")

    def test_connection(self) -> bool:
        """
        Test database connection.

        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            session = self.get_session()
            session.execute(text("SELECT 1"))
            session.close()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False

    def get_pool_status(self) -> dict:
        """
        Get current connection pool status.

        Returns:
            dict: Pool statistics
        """
        if not self.engine:
            return {}

        pool = self.engine.pool
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow(),
        }


# Global database manager instance
_db_manager: Optional[DatabaseManager] = None


def get_db_manager(config_path: Optional[str] = None) -> DatabaseManager:
    """
    Get global database manager instance.

    Args:
        config_path: Optional path to config file

    Returns:
        DatabaseManager: Global database manager instance
    """
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(config_path)
    return _db_manager


def get_session():
    """
    Convenience function to get a database session.

    Returns:
        Session: SQLAlchemy session
    """
    return get_db_manager().get_session()

