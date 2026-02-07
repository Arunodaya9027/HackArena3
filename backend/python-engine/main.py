"""
GeoClear Python Backend - Entry Point
FastAPI application for geometric displacement processing
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from app.api import router

# Create FastAPI app
app = FastAPI(
    title="GeoClear Python Backend",
    description="High-performance geometric displacement processing API",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins in development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router)

if __name__ == "__main__":
    print("=" * 60)
    print("GeoClear Python Backend")
    print("=" * 60)
    print("Starting server on http://localhost:8002")
    print("API Documentation: http://localhost:8002/docs")
    print("Health Check: http://localhost:8002/api/health")
    print("=" * 60)
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8002,
        log_level="info"
    )

