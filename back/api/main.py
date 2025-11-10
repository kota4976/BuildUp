"""FastAPI application entry point"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import engine, Base
from app.core.middleware import RequestIDMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info(f"Starting {settings.app_name} API")
    logger.info(f"Environment: {settings.app_env}")
    yield
    # Shutdown
    logger.info("Shutting down API")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="BuildUp API for matching developers with projects",
    version="0.1.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add custom middleware
app.add_middleware(RequestIDMiddleware)


# Health check endpoint
@app.get("/healthz")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "app": settings.app_name}


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": settings.app_name,
        "version": "0.1.0",
        "docs": "/docs"
    }


# Include API routers
from app.api.v1 import api_router
from app.api import websocket

app.include_router(api_router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/ws")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production
    )

