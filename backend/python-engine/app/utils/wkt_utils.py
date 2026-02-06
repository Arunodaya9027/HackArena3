"""
WKT Utility Functions
Helper functions for WKT parsing and validation
"""
from typing import Optional
from shapely import wkt
from shapely.geometry.base import BaseGeometry


def parse_wkt_safe(wkt_string: str) -> Optional[BaseGeometry]:
    """
    Safely parse WKT string to Shapely geometry
    
    Args:
        wkt_string: Well-Known Text geometry string
        
    Returns:
        Shapely geometry object or None if parsing fails
    """
    try:
        geometry = wkt.loads(wkt_string)
        if not geometry.is_valid:
            # Attempt to fix invalid geometries
            geometry = geometry.buffer(0)
        return geometry
    except Exception as e:
        print(f"⚠️ WKT parsing error: {str(e)}")
        return None


def validate_wkt(wkt_string: str) -> tuple[bool, str]:
    """
    Validate WKT string format
    
    Args:
        wkt_string: Well-Known Text string to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        geometry = wkt.loads(wkt_string)
        if not geometry.is_valid:
            return False, "Geometry is not valid (self-intersections or other issues)"
        return True, "Valid WKT"
    except Exception as e:
        return False, f"Parsing error: {str(e)}"


def get_geometry_info(geometry: BaseGeometry) -> dict:
    """
    Extract information from Shapely geometry
    
    Args:
        geometry: Shapely geometry object
        
    Returns:
        Dictionary with geometry metadata
    """
    return {
        "type": geometry.geom_type,
        "is_valid": geometry.is_valid,
        "is_empty": geometry.is_empty,
        "bounds": geometry.bounds,
        "length": geometry.length if hasattr(geometry, 'length') else 0,
        "area": geometry.area if hasattr(geometry, 'area') else 0,
    }


def simplify_geometry(geometry: BaseGeometry, tolerance: float = 0.1) -> BaseGeometry:
    """
    Simplify geometry while preserving topology
    
    Args:
        geometry: Shapely geometry to simplify
        tolerance: Simplification tolerance in coordinate units
        
    Returns:
        Simplified geometry
    """
    try:
        return geometry.simplify(tolerance, preserve_topology=True)
    except Exception:
        return geometry


def buffer_geometry(geometry: BaseGeometry, distance: float) -> BaseGeometry:
    """
    Create buffer around geometry
    
    Args:
        geometry: Shapely geometry
        distance: Buffer distance
        
    Returns:
        Buffered geometry
    """
    try:
        return geometry.buffer(distance)
    except Exception:
        return geometry
