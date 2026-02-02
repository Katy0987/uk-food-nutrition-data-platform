"""
PostgreSQL database session management using SQLAlchemy.
Provides database connection, session creation, and dependency injection.
"""

import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

from api.config import settings
from core.models.establishment import Base as EstablishmentBase
from core.models.product_eco import Base as ProductEcoBase

logger = logging.getLogger(__name__)


# Create database engine with connection pooling
engine = create_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_timeout=settings.db_pool_timeout,
    pool_pre_ping=True,  # Test connections before using
    echo=settings.debug,  # Log SQL in debug mode
)

# Create session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Event listeners for connection management
@event.listens_for(engine, "connect")
def set_postgres_pragma(dbapi_connection, connection_record):
    """Set PostgreSQL session parameters on connection."""
    cursor = dbapi_connection.cursor()
    cursor.execute("SET timezone='UTC'")
    cursor.close()


def init_db():
    """
    Initialize database schema.
    Creates all tables if they don't exist.
    """
    try:
        logger.info("Initializing database schema...")
        
        # Import all models to ensure they're registered
        from core.models.establishment import Establishment
        from core.models.product_eco import ProductEco
        
        # Create all tables
        EstablishmentBase.metadata.create_all(bind=engine)
        ProductEcoBase.metadata.create_all(bind=engine)
        
        logger.info("Database schema initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise


def drop_db():
    """
    Drop all database tables.
    WARNING: This will delete all data!
    """
    logger.warning("Dropping all database tables...")
    EstablishmentBase.metadata.drop_all(bind=engine)
    ProductEcoBase.metadata.drop_all(bind=engine)
    logger.info("All database tables dropped")


def get_db() -> Generator[Session, None, None]:
    """
    Dependency injection for database sessions.
    
    Yields:
        Database session
        
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for database sessions.
    
    Yields:
        Database session
        
    Usage:
        with get_db_context() as db:
            db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def check_connection() -> bool:
    """Check if database connection is alive."""
    try:
        from sqlalchemy import text
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))  # ✅ Fixed!
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return False


def get_db_stats() -> dict:
    """
    Get database connection pool statistics.
    
    Returns:
        Dictionary with pool stats
    """
    pool = engine.pool
    return {
        "pool_size": pool.size(),
        "checked_in": pool.checkedin(),
        "checked_out": pool.checkedout(),
        "overflow": pool.overflow(),
        "total_connections": pool.size() + pool.overflow(),
    }
