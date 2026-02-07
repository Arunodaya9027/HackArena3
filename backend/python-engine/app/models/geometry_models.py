"""
Data models for GeoClear AI Geometry Engine
Handles request/response structures for geometry processing
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class FeaturePriority(str, Enum):
    """
    Enhanced Feature Priority System - Multi-category Classification
    
    Priority Hierarchy (Lower number = Higher importance):
    P1: Critical Infrastructure (Highways, Railways, Rivers)
    P2: Major Roads (Main Roads)
    P3: Local Streets (Local Roads, Streets)
    P4: Structures (Buildings, Parks)
    P5: Decorative (Icons, Labels, Overlap Areas)
    """
    # P1: Critical Infrastructure (Highest Priority)
    P1_HIGHWAY = "P1_HIGHWAY"              # Width 5.0pt - Highways/Expressways
    P1_RAILWAY = "P1_RAILWAY"              # Width 4.5pt - Railway Lines
    P1_RIVER = "P1_RIVER"                  # Width 4.0pt - Rivers/Water Bodies
    
    # P2: Major Roads
    P2_MAIN_ROAD = "P2_MAIN_ROAD"          # Width 3.5pt - Main Roads/Avenues
    
    # P3: Local Roads
    P3_LOCAL_ROAD = "P3_LOCAL_ROAD"        # Width 3.0pt - Local Roads/Streets
    P3_STREET = "P3_STREET"                # Width 2.8pt - Streets/Lanes
    
    # P4: Structures
    P4_BUILDING = "P4_BUILDING"            # Width 2.5pt - Buildings/Structures
    P4_PARK = "P4_PARK"                    # Width 2.5pt - Parks/Green Spaces
    
    # P5: Decorative Elements (Lowest Priority)
    P5_LABEL = "P5_LABEL"                  # Width 2.0pt - Text Labels
    P5_ICON = "P5_ICON"                    # Width 2.0pt - Map Icons
    P5_OVERLAP_AREA = "P5_OVERLAP_AREA"    # Width 1.5pt - Overlap Areas
    
    # Backward compatibility (deprecated)
    P2_ROAD = "P2_ROAD"                    # Width 3.0pt - Generic Road (Legacy)


class FeatureInput(BaseModel):
    """Input feature with WKT geometry"""
    id: str = Field(..., description="Unique identifier for the feature")
    wkt: str = Field(..., description="WKT LINESTRING geometry")
    priority: FeaturePriority = Field(..., description="Feature priority level")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "highway_001",
                "wkt": "LINESTRING(7071.42 8585.63, 7074.67 8588.81)",
                "priority": "P1_HIGHWAY"
            }
        }


class GeometryRequest(BaseModel):
    """Request for geometry processing"""
    features: List[FeatureInput] = Field(..., description="List of input features")
    min_clearance: float = Field(default=2.0, description="Minimum clearance in points")
    force_strength: float = Field(default=1.0, description="Force strength for displacement (0.0-2.0)")
    max_iterations: int = Field(default=100, description="Maximum iterations for force-directed layout")
    enable_3d_depth: bool = Field(default=False, description="Enable 3D depth features (z-index, shadows)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "features": [
                    {
                        "id": "highway_001",
                        "wkt": "LINESTRING(7071.42 8585.63, 7074.67 8588.81)",
                        "priority": "P1_HIGHWAY"
                    },
                    {
                        "id": "road_001",
                        "wkt": "LINESTRING(7071.50 8585.70, 7074.70 8588.85)",
                        "priority": "P2_ROAD"
                    }
                ],
                "min_clearance": 2.0,
                "force_strength": 1.0,
                "max_iterations": 100,
                "enable_3d_depth": False
            }
        }


class ConflictMetadata(BaseModel):
    """Metadata about a detected conflict"""
    conflict_pair: List[str] = Field(..., description="IDs of conflicting features")
    displacement_vector: List[float] = Field(..., description="[dx, dy] displacement applied")
    overlap_amount: float = Field(..., description="Amount of overlap detected in points")
    z_index: Optional[int] = Field(None, description="Z-order for 3D depth rendering")
    visual_depth_flag: bool = Field(default=False, description="Flag for shadow/depth rendering")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conflict_pair": ["highway_001", "road_001"],
                "displacement_vector": [1.5, 0.8],
                "overlap_amount": 2.3,
                "z_index": 1,
                "visual_depth_flag": True
            }
        }


class DisplacementResult(BaseModel):
    """Result of displacement processing for a single feature"""
    feature_id: str = Field(..., description="Feature identifier")
    original_wkt: str = Field(..., description="Original WKT geometry")
    corrected_wkt: str = Field(..., description="Corrected WKT geometry after displacement")
    was_displaced: bool = Field(..., description="Whether this feature was displaced")
    metadata: Optional[ConflictMetadata] = Field(None, description="Conflict metadata if displaced")
    
    class Config:
        json_schema_extra = {
            "example": {
                "feature_id": "road_001",
                "original_wkt": "LINESTRING(7071.50 8585.70, 7074.70 8588.85)",
                "corrected_wkt": "LINESTRING(7073.00 8586.50, 7076.20 8589.65)",
                "was_displaced": True,
                "metadata": {
                    "conflict_pair": ["highway_001", "road_001"],
                    "displacement_vector": [1.5, 0.8],
                    "overlap_amount": 2.3,
                    "z_index": 1,
                    "visual_depth_flag": True
                }
            }
        }


class GeometryResponse(BaseModel):
    """Response containing processed geometry results"""
    results: List[DisplacementResult] = Field(..., description="List of processing results")
    total_conflicts: int = Field(default=0, description="Total number of conflicts detected")
    total_displaced: int = Field(default=0, description="Total number of features displaced")
    total_conflicts_resolved: int = Field(default=0, description="Total conflicts resolved")
    execution_time_ms: float = Field(default=0.0, description="Processing time in milliseconds")
    topology_preserved: bool = Field(default=True, description="Whether topology was preserved")
    processing_summary: Dict[str, Any] = Field(default_factory=dict, description="Processing statistics")
    
    class Config:
        json_schema_extra = {
            "example": {
                "results": [
                    {
                        "feature_id": "highway_001",
                        "original_wkt": "LINESTRING(7071.42 8585.63, 7074.67 8588.81)",
                        "corrected_wkt": "LINESTRING(7071.42 8585.63, 7074.67 8588.81)",
                        "was_displaced": False,
                        "metadata": None
                    },
                    {
                        "feature_id": "road_001",
                        "original_wkt": "LINESTRING(7071.50 8585.70, 7074.70 8588.85)",
                        "corrected_wkt": "LINESTRING(7073.00 8586.50, 7076.20 8589.65)",
                        "was_displaced": True,
                        "metadata": {
                            "conflict_pair": ["highway_001", "road_001"],
                            "displacement_vector": [1.5, 0.8],
                            "overlap_amount": 2.3,
                            "z_index": 1,
                            "visual_depth_flag": True
                        }
                    }
                ],
                "total_conflicts": 1,
                "total_displaced": 1,
                "total_conflicts_resolved": 1,
                "execution_time_ms": 45.23,
                "topology_preserved": True,
                "processing_summary": {
                    "features_processed": 2,
                    "highways": 1,
                    "roads": 1
                }
            }
        }
