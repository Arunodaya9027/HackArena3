"""API routes for geometry processing"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List

from app.models.geometry_models import GeometryRequest, GeometryResponse
from app.services.geometry_processor import GeometryProcessor
from app.services.precision_overlap_detector import PrecisionOverlapDetector

router = APIRouter()
geometry_processor = GeometryProcessor()
precision_detector = PrecisionOverlapDetector(strict_mode=True)


@router.post("/process", response_model=GeometryResponse)
async def process_geometries(request: GeometryRequest) -> GeometryResponse:
    """
    Process geometries to resolve overlaps and assign depth
    
    Args:
        request: Geometry processing request with features
        
    Returns:
        Processed geometries with displacement and depth metadata
    """
    try:
        response = geometry_processor.process_geometries(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "GeoClear AI - Python Geometry Engine",
        "version": "1.0.0"
    }


@router.get("/capabilities")
async def get_capabilities() -> Dict:
    """Return engine capabilities"""
    return {
        "features": [
            "overlap_detection",
            "precision_conflict_detection",
            "force_directed_displacement",
            "topology_preservation",
            "3d_depth_assignment",
            "junction_detection"
        ],
        "supported_geometries": ["LINESTRING"],
        "priorities": {
            "P1_HIGHWAY": "Highway (5pt width)",
            "P2_ROAD": "Road (3pt width)"
        },
        "conflict_types": [
            "BUFFER_OVERLAP",
            "CENTERLINE_PROXIMITY",
            "PARALLEL_CONFLICT",
            "CROSSING_CONFLICT",
            "ENDPOINT_CONFLICT"
        ],
        "default_min_clearance": 2.0
    }


@router.post("/detect-conflicts")
async def detect_conflicts(request: GeometryRequest) -> Dict:
    """
    Detect ALL conflicts between features with NO MERCY
    Reports every type of conflict found
    
    Args:
        request: Geometry processing request with features
        
    Returns:
        Comprehensive conflict report with detailed analysis
    """
    try:
        # Run precision conflict detection
        conflicts = precision_detector.detect_overlaps(request.features)
        
        # Organize conflicts by severity
        critical_conflicts = [c for c in conflicts 
                            if any(conf["severity"] == "CRITICAL" 
                                 for conf in c["conflicts_detected"])]
        high_conflicts = [c for c in conflicts 
                         if any(conf["severity"] == "HIGH" 
                              for conf in c["conflicts_detected"])]
        medium_conflicts = [c for c in conflicts 
                           if any(conf["severity"] == "MEDIUM" 
                                for conf in c["conflicts_detected"])]
        
        # Calculate statistics
        total_features = len(request.features)
        total_pairs = total_features * (total_features - 1) // 2
        conflict_pairs = len(conflicts)
        
        # Count conflict types
        conflict_type_counts = {}
        for conflict in conflicts:
            for conf in conflict["conflicts_detected"]:
                conflict_type = conf["type"]
                conflict_type_counts[conflict_type] = conflict_type_counts.get(conflict_type, 0) + 1
        
        return {
            "summary": {
                "total_features": total_features,
                "total_pairs_checked": total_pairs,
                "conflicting_pairs": conflict_pairs,
                "conflict_rate_percent": round((conflict_pairs / total_pairs * 100), 2) if total_pairs > 0 else 0,
                "min_clearance_used": request.min_clearance,
                "strict_mode": precision_detector.strict_mode
            },
            "severity_breakdown": {
                "critical": len(critical_conflicts),
                "high": len(high_conflicts),
                "medium": len(medium_conflicts)
            },
            "conflict_type_counts": conflict_type_counts,
            "conflicts": conflicts,
            "message": f"NO MERCY MODE: Found {conflict_pairs} conflicting pairs out of {total_pairs} total pairs"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Conflict detection error: {str(e)}")


@router.post("/analyze-pair")
async def analyze_pair(feature1_index: int, feature2_index: int, request: GeometryRequest) -> Dict:
    """
    Analyze specific pair of features in detail
    
    Args:
        feature1_index: Index of first feature
        feature2_index: Index of second feature
        request: Geometry request containing features
        
    Returns:
        Detailed conflict analysis for the specific pair
    """
    try:
        if feature1_index >= len(request.features) or feature2_index >= len(request.features):
            raise HTTPException(status_code=400, detail="Feature index out of range")
        
        feature1 = request.features[feature1_index]
        feature2 = request.features[feature2_index]
        
        conflict_result = precision_detector.detect_all_conflicts(feature1, feature2)
        
        return {
            "pair_analysis": conflict_result,
            "recommendation": "DISPLACEMENT REQUIRED" if conflict_result["has_any_conflict"] else "NO ACTION NEEDED"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pair analysis error: {str(e)}")
