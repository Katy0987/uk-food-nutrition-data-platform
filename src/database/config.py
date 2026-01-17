import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parents[2] / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Centralized database configuration for both PostgreSQL and MongoDB."""

    # PostgreSQL Configuration
    POSTGRES_HOST: str = os.getenv('PS_DB_HOST', 'localhost')
    POSTGRES_PORT: int = int(os.getenv('PS_DB_PORT', '5432'))
    POSTGRES_USER: str = os.getenv('PS_DB_USER', 'postgres')
    POSTGRES_PASSWORD: str = os.getenv('PS_DB_PASSWORD', 'postgres')
    POSTGRES_DB: str = os.getenv('PS_DB_NAME', 'urban_data_hub')

    # MongoDB Configuration
    MONGODB_URL: str = os.getenv('MONGODB_URL', 'mongodb://localhost:27017')
    MONGODB_NAME: str = os.getenv('MONGODB_NAME', 'urban_data_hub')

    # Cache Configuration
    CACHE_URL: str = os.getenv('CACHE_URL', 'redis://localhost:6379/0')
    CACHE_TTL: str = 300

    @classmethod
    def get_sql_url(cls) -> str:
        return (
            f"postgresql://{cls.POSTGRES_USER}:{cls.POSTGRES_PASSWORD}"
            f"@{cls.POSTGRES_HOST}:{cls.POSTGRES_PORT}/{cls.POSTGRES_DB}"
        )

    @classmethod
    def get_mongodb_url(cls) -> str:
        return cls.MONGODB_URL