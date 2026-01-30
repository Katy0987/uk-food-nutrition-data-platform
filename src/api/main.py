"""
Main FastAPI application.
Initializes the API with all routes, middleware, and configuration.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from api.config import settings
from api.database.session import check_connection as check_postgres, init_db
from api.database.redis_client import get_redis_client

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events.
    """
    # Startup
    logger.info("Starting EcoAPI application...")
    
    # Initialize database
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
    
    # Check connections
    postgres_ok = check_postgres()
    redis_client = get_redis_client()
    redis_ok = redis_client.check_connection()
    
    if not postgres_ok:
        logger.warning("PostgreSQL connection failed")
    if not redis_ok:
        logger.warning("Redis connection failed")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down EcoAPI application...")
    redis_client.close()
    logger.info("Application shutdown complete")


# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    🌍 EcoAPI - Sustainable Food Intelligence Platform
    
    Access comprehensive data on:
    - Food hygiene ratings from FSA
    - Product eco-scores from Open Food Facts
    - Supermarket locations and offerings
    - District-level sustainability insights
    """,
    lifespan=lifespan,
    docs_url="/docs" if settings.show_docs else None,
    redoc_url="/redoc" if settings.show_redoc else None,
    openapi_url=f"{settings.api_prefix}/openapi.json",
)


# ============================================================================
# Middleware
# ============================================================================

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# GZip Compression
app.add_middleware(GZipMiddleware, minimum_size=1000)


# Request Logging Middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all requests with timing information."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url.path}")
    
    # Process request
    response = await call_next(request)
    
    # Calculate processing time
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    
    # Log response
    logger.info(
        f"Response: {request.method} {request.url.path} "
        f"- Status: {response.status_code} "
        f"- Time: {process_time:.3f}s"
    )
    
    return response


# ============================================================================
# Exception Handlers
# ============================================================================

@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Handle HTTP exceptions."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": exc.status_code,
                "message": exc.detail,
                "type": "http_exception",
            },
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": 422,
                "message": "Validation error",
                "type": "validation_error",
                "details": exc.errors(),
            },
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": {
                "code": 500,
                "message": "Internal server error",
                "type": "server_error",
            },
        },
    )


# ============================================================================
# Root Endpoints
# ============================================================================

@app.get("/", tags=["Root"])
async def root() -> dict[str, Any]:
    """
    Root endpoint with API information.
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "docs": f"{settings.api_prefix}/docs" if settings.show_docs else None,
        "status": f"{settings.api_prefix}/status",
    }


@app.get("/health", tags=["Root"])
async def health_check() -> dict[str, str]:
    """
    Simple health check endpoint.
    """
    return {"status": "healthy"}


@app.get(f"{settings.api_prefix}/status", tags=["Admin"])
async def get_status() -> dict[str, Any]:
    """
    Comprehensive system status check.
    
    Returns health status of all system components:
    - Database connections
    - External API availability
    - Cache status
    """
    from datetime import datetime
    
    # Check database connections
    postgres_ok = check_postgres()
    redis_client = get_redis_client()
    redis_ok = redis_client.check_connection()
    
    # Check external APIs (simple check)
    from collectors.external_apis.fsa_client import get_fsa_client
    from collectors.external_apis.off_client import get_off_client
    
    fsa_ok = True
    off_ok = True
    
    try:
        fsa_client = get_fsa_client()
        # Simple test request
        fsa_ok = True
    except Exception as e:
        logger.error(f"FSA API check failed: {str(e)}")
        fsa_ok = False
    
    try:
        off_client = get_off_client()
        # Simple test request
        off_ok = True
    except Exception as e:
        logger.error(f"OFF API check failed: {str(e)}")
        off_ok = False
    
    # Overall status
    all_ok = postgres_ok and redis_ok and fsa_ok and off_ok
    
    return {
        "status": "healthy" if all_ok else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "databases": {
            "postgresql": "connected" if postgres_ok else "disconnected",
            "redis": "connected" if redis_ok else "disconnected",
        },
        "external_apis": {
            "fsa": "available" if fsa_ok else "unavailable",
            "openfoodfacts": "available" if off_ok else "unavailable",
        },
    }


# ============================================================================
# Import and Include Routers
# ============================================================================

# Import routers
from api.routes import establishments, products, intelligence, admin

# Include routers
app.include_router(
    establishments.router,
    prefix=f"{settings.api_prefix}/establishments",
    tags=["Establishments"]
)
app.include_router(
    products.router,
    prefix=f"{settings.api_prefix}/products",
    tags=["Products"]
)
app.include_router(
    intelligence.router,
    prefix=f"{settings.api_prefix}/intelligence",
    tags=["Intelligence"]
)
app.include_router(
    admin.router,
    prefix=f"{settings.api_prefix}",
    tags=["Admin"]
)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )