"""
Data models for GeoClear Python API
"""
from pydantic import BaseModel
from typing import List, Optional

class Coordinate(BaseModel):
    """Geographic coordinate"""
    lat: float
    lng: float

class Feature(BaseModel):
    """Geographic feature (road, building, etc.)"""
    id: int
    type: str
    priority: int
    width: float
    color: str
    coords: List[Coordinate]
    origCoords: Optional[List[Coordinate]] = None
    displaced: bool = False

class DisplacementRequest(BaseModel):
    """Request model for displacement processing"""
    features: List[Feature]

class ProcessingMetrics(BaseModel):
    """Metrics from displacement processing"""
    overlapsDetected: int
    overlapsResolved: int
    maxDisplacementMeters: float
    processingTimeSeconds: float
    totalFeatures: int

class DisplacementResponse(BaseModel):
    """Response model for displacement processing"""
    success: bool
    features: List[Feature]
    metrics: ProcessingMetrics
