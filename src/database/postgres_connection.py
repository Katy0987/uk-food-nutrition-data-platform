import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv  # type: ignore

# Load environment variables at module level
load_dotenv()


def get_engine():
    """
    Create and return a SQLAlchemy PostgreSQL engine
    using environment variables.
    """
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")
    
    # Debug: Print loaded values (remove in production)
    print(f"Debug - POSTGRES_USER: {user}")
    print(f"Debug - POSTGRES_HOST: {host}")
    print(f"Debug - POSTGRES_PORT: {port}")
    print(f"Debug - POSTGRES_DB: {database}")
    
    # Validate required environment variables
    if not all([user, password, host, port, database]):
        missing = []
        if not user: missing.append("POSTGRES_USER")
        if not password: missing.append("POSTGRES_PASSWORD")
        if not host: missing.append("POSTGRES_HOST")
        if not port: missing.append("POSTGRES_PORT")
        if not database: missing.append("POSTGRES_DB")
        
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    connection_string = (
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )
    
    engine = create_engine(
        connection_string,
        pool_pre_ping=True,  # Verify connections before using them
        echo=False  # Set to True for SQL query logging during development
    )
    
    return engine


# Create engine instance
engine = get_engine()

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db_session() -> Session:
    """
    Create and return a new database session.
    This function creates a new session that should be closed after use.
    """
    return SessionLocal()


def get_db():
    """
    Dependency function for FastAPI to get database session.
    Yields a database session and ensures it's closed after use.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()