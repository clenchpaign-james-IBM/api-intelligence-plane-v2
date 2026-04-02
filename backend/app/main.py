"""
FastAPI Main Application

Entry point for the API Intelligence Plane backend service.
Configures FastAPI with middleware, error handlers, CORS, and routes.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logging import setup_logging
from app.middleware.error_handler import error_handler_middleware
from app.scheduler import setup_scheduler, start_scheduler, shutdown_scheduler
from app.db.client import get_opensearch_client

# Setup logging first
setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events:
    - Startup: Initialize database, start scheduler
    - Shutdown: Close connections, stop scheduler
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    
    # Initialize OpenSearch client
    try:
        os_client = get_opensearch_client()
        health = os_client.health_check()
        logger.info(f"OpenSearch connected: {health.get('status', 'unknown')}")
    except Exception as e:
        logger.error(f"Failed to connect to OpenSearch: {e}")
        if settings.is_production:
            raise
    
    # Setup and start scheduler
    try:
        setup_scheduler()
        start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
    
    logger.info("Application startup complete")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application...")
    
    # Stop scheduler
    try:
        shutdown_scheduler()
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
    
    # Close database connections
    try:
        os_client = get_opensearch_client()
        os_client.close()
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-driven API management platform with autonomous discovery, "
                "predictive health management, and intelligent optimization",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add audit logging middleware (before error handler)
from app.middleware.audit import AuditMiddleware
app.add_middleware(AuditMiddleware)

# Add error handling middleware
app.middleware("http")(error_handler_middleware)


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    
    Returns application and database health status.
    """
    try:
        os_client = get_opensearch_client()
        db_health = os_client.health_check()
        
        return {
            "status": "healthy",
            "app": {
                "name": settings.APP_NAME,
                "version": settings.APP_VERSION,
                "environment": settings.ENVIRONMENT,
            },
            "database": db_health,
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e),
            },
        )


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "description": "AI-driven API management platform",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
    }


# API v1 routes
from app.api.v1 import gateways, apis, metrics, predictions, optimization, rate_limits, query, security, compliance

app.include_router(gateways.router, prefix="/api/v1", tags=["Gateways"])
app.include_router(apis.router, prefix="/api/v1", tags=["APIs"])
app.include_router(metrics.router, prefix="/api/v1", tags=["Metrics"])
app.include_router(predictions.router, prefix="/api/v1", tags=["Predictions"])
app.include_router(optimization.router, prefix="/api/v1", tags=["Optimization"])
app.include_router(rate_limits.router, prefix="/api/v1", tags=["Rate Limiting"])
app.include_router(security.router, prefix="/api/v1", tags=["Security"])
app.include_router(compliance.router, prefix="/api/v1", tags=["Compliance"])
app.include_router(query.router, prefix="/api/v1", tags=["Query"])


if __name__ == "__main__":
    import uvicorn
    from app.utils.tls_config import get_uvicorn_ssl_config
    
    # Get SSL configuration if TLS is enabled
    ssl_config = get_uvicorn_ssl_config()
    
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.RELOAD,
        workers=settings.WORKERS if not settings.RELOAD else 1,
        log_level=settings.LOG_LEVEL.lower(),
        **ssl_config,
    )

# Made with Bob
