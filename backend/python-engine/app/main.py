"""
GeoClear AI - Python Geometry Engine

FastAPI microservice for geospatial conflict resolution
Handles overlap detection, displacement, and topology preservation
"""

import logging
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize FastAPI application
app = FastAPI(
    title="GeoClear AI - Python Geometry Engine",
    description="Advanced geospatial processing engine for overlap detection and resolution",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


# CORS middleware for Java API integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routes from routes.py with /api/geometry prefix
app.include_router(router, prefix="/api/geometry")


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint with service information"""
    return {
        "service": "GeoClear AI - Python Geometry Engine",
        "version": "1.0.0",
        "status": "operational",
        "documentation": "/docs",
        "capabilities": [
            "precision_overlap_detection",
            "force_directed_displacement",
            "topology_preservation",
            "3d_depth_assignment",
            "junction_detection"
        ]
    }


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc),
            "type": type(exc).__name__
        }
    )


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 GeoClear AI - Python Geometry Engine starting up...")
    logger.info("📍 API Documentation available at: http://localhost:8001/docs")
    logger.info("🔧 Service ready to process geometry conflicts")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛑 GeoClear AI - Python Geometry Engine shutting down...")


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
