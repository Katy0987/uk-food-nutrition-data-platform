"""
Configuration management using Pydantic Settings.
Loads configuration from environment variables with validation.
"""

from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    """Application settings with environment variable support."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Application
    app_name: str = Field(default="EcoAPI", description="Application name")
    app_version: str = Field(default="1.0.0", description="API version")
    environment: str = Field(default="development", description="Environment (development/staging/production)")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    api_prefix: str = Field(default="/api/v1", description="API route prefix")

    # Server
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8000, description="Server port")
    workers: int = Field(default=4, description="Number of workers")

    # PostgreSQL
    database_url: str = Field(
        default="postgresql://ecouser:ecopass@localhost:5432/ecodb",
        description="PostgreSQL connection URL"
    )
    db_pool_size: int = Field(default=20, description="Database pool size")
    db_max_overflow: int = Field(default=40, description="Max pool overflow")
    db_pool_timeout: int = Field(default=30, description="Pool timeout in seconds")

    # MongoDB
    mongodb_url: str = Field(
        default="mongodb://localhost:27017",
        description="MongoDB connection URL"
    )
    mongodb_db_name: str = Field(default="ecodb", description="MongoDB database name")
    mongodb_max_pool_size: int = Field(default=50, description="MongoDB max pool size")
    mongodb_min_pool_size: int = Field(default=10, description="MongoDB min pool size")

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection URL"
    )
    redis_max_connections: int = Field(default=50, description="Redis max connections")
    redis_socket_timeout: int = Field(default=5, description="Redis socket timeout")
    redis_socket_connect_timeout: int = Field(default=5, description="Redis connect timeout")

    # FSA API
    fsa_api_base_url: str = Field(
        default="https://api.ratings.food.gov.uk",
        description="FSA API base URL"
    )
    fsa_api_version: str = Field(default="v2", description="FSA API version")
    fsa_api_timeout: int = Field(default=10, description="FSA API timeout")
    fsa_api_max_retries: int = Field(default=3, description="FSA API max retries")
    fsa_api_retry_delay: int = Field(default=1, description="FSA API retry delay")

    # Open Food Facts API
    off_api_base_url: str = Field(
        default="https://world.openfoodfacts.org",
        description="OFF API base URL"
    )
    off_api_timeout: int = Field(default=10, description="OFF API timeout")
    off_api_max_retries: int = Field(default=3, description="OFF API max retries")
    off_api_user_agent: str = Field(
        default="EcoAPI/1.0.0",
        description="User agent for OFF API"
    )

    # Cache Configuration (TTL in seconds)
    cache_ttl_establishment: int = Field(default=86400, description="Establishment cache TTL")
    cache_ttl_product: int = Field(default=86400, description="Product cache TTL")
    cache_ttl_search: int = Field(default=3600, description="Search cache TTL")
    cache_ttl_intelligence: int = Field(default=21600, description="Intelligence cache TTL")
    cache_max_size_mb: int = Field(default=500, description="Max cache size in MB")

    # Security
    secret_key: str = Field(
        default="change-this-secret-key-in-production",
        description="Secret key for JWT"
    )
    algorithm: str = Field(default="HS256", description="JWT algorithm")
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiry in minutes"
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiry in days"
    )

    # CORS
    cors_origins: List[str] = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        description="Allowed CORS origins"
    )
    cors_allow_credentials: bool = Field(default=True, description="Allow credentials")
    cors_allow_methods: List[str] = Field(default=["*"], description="Allowed methods")
    cors_allow_headers: List[str] = Field(default=["*"], description="Allowed headers")

    # Rate Limiting
    rate_limit_per_minute: int = Field(default=60, description="Requests per minute")
    rate_limit_per_hour: int = Field(default=1000, description="Requests per hour")

    # Performance
    max_concurrent_requests: int = Field(default=50, description="Max concurrent requests")
    request_timeout: int = Field(default=30, description="Request timeout in seconds")
    query_timeout: int = Field(default=5, description="Query timeout in seconds")

    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    enable_request_logging: bool = Field(default=True, description="Enable request logging")
    log_file_path: str = Field(default="logs/api.log", description="Log file path")
    log_rotation_size_mb: int = Field(default=100, description="Log rotation size")
    log_retention_days: int = Field(default=30, description="Log retention days")

    # Feature Flags
    enable_caching: bool = Field(default=True, description="Enable caching")
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_authentication: bool = Field(default=True, description="Enable authentication")
    enable_web_search: bool = Field(default=False, description="Enable web search")

    # Development
    reload: bool = Field(default=False, description="Auto-reload on code changes")
    show_docs: bool = Field(default=True, description="Show OpenAPI docs")
    show_redoc: bool = Field(default=True, description="Show ReDoc")

    # Testing
    test_database_url: Optional[str] = Field(
        default=None,
        description="Test database URL"
    )
    test_mongodb_url: Optional[str] = Field(
        default=None,
        description="Test MongoDB URL"
    )
    test_redis_url: Optional[str] = Field(
        default=None,
        description="Test Redis URL"
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v):
        """Validate environment value."""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"environment must be one of {allowed}")
        return v

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def fsa_api_url(self) -> str:
        """Get full FSA API URL."""
        return f"{self.fsa_api_base_url}/{self.fsa_api_version}"

    @property
    def database_url_async(self) -> str:
        """Get async database URL for SQLAlchemy."""
        return self.database_url.replace("postgresql://", "postgresql+asyncpg://")


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    Uses lru_cache to ensure settings are loaded only once.
    """
    return Settings()


# Export settings instance
settings = get_settings()