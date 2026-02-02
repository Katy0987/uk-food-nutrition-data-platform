import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

# Get the project root directory (parent of src/)
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / '.env'

# Load environment variables with explicit path
load_dotenv(dotenv_path=ENV_PATH)

# Global variables for lazy initialization
_engine = None
_SessionLocal = None


def get_engine():
    """
    Create and return a SQLAlchemy PostgreSQL engine
    using environment variables.
    Uses lazy initialization to ensure .env is loaded.
    """
    global _engine
    
    if _engine is not None:
        return _engine
    
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")
    
    # Validate required environment variables
    if not all([user, password, host, port, database]):
        missing = []
        if not user: missing.append("POSTGRES_USER")
        if not password: missing.append("POSTGRES_PASSWORD")
        if not host: missing.append("POSTGRES_HOST")
        if not port: missing.append("POSTGRES_PORT")
        if not database: missing.append("POSTGRES_DB")
        
        # Print debug info
        print(f"Looking for .env at: {ENV_PATH}")
        print(f".env exists: {ENV_PATH.exists()}")
        
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    connection_string = (
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )
    
    _engine = create_engine(
        connection_string,
        pool_pre_ping=True,
        echo=False  # Set to True for SQL debugging
    )
    
    return _engine


def get_session_local():
    """
    Get or create the SessionLocal class.
    """
    global _SessionLocal
    
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    return _SessionLocal


def get_db_session() -> Session:
    """
    Create and return a new database session.
    """
    SessionLocal = get_session_local()
    return SessionLocal()


def get_db():
    """
    Dependency function for FastAPI to get database session.
    """
    SessionLocal = get_session_local()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()