import os
from sqlalchemy import create_engine
from dotenv import load_dotenv # type: ignore

def get_engine():
    """
    Create and return a SQLAlchemy PostgreSQL engine
    using environment variables.
    """
    load_dotenv()

    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")
    host = os.getenv("POSTGRES_HOST")
    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")

    connection_string = (
        f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"
    )

    engine = create_engine(connection_string)
    return engine
