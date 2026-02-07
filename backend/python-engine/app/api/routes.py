"""
FastAPI route handlers
API endpoint definitions
"""
from fastapi import APIRouter
from app.models import DisplacementRequest, DisplacementResponse
from app.services import process_displacement

router = APIRouter()

@router.get("/")
async def root():
    """API information endpoint"""
    return {
        "service": "GeoClear Python Backend",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /api/health",
            "displacement": "POST /api/displacement"
        }
    }

@router.get("/api/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GeoClear Python Backend"
    }

@router.post("/api/displacement")
async def api_displacement(request: DisplacementRequest):
    """
    Process displacement algorithm on features
    
    Args:
        request: DisplacementRequest with list of features
    
    Returns:
        DisplacementResponse with processed features and metrics
    """
    try:
        processed_features, metrics = process_displacement(request.features)
        
        return DisplacementResponse(
            success=True,
            features=processed_features,
            metrics=metrics
        )
    except Exception as e:
        return DisplacementResponse(
            success=False,
            features=[],
            metrics=None
        )
