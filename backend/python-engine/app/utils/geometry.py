"""
Geometric utility functions for coordinate calculations
"""
import math
from typing import Tuple, List
from app.models import Coordinate

# Constants
EARTH_RADIUS_M = 6371000.0  # meters

def haversine_distance(c1: Coordinate, c2: Coordinate) -> float:
    """
    Calculate distance between two coordinates using Haversine formula
    
    Args:
        c1: First coordinate
        c2: Second coordinate
    
    Returns:
        Distance in meters
    """
    lat1, lng1 = math.radians(c1.lat), math.radians(c1.lng)
    lat2, lng2 = math.radians(c2.lat), math.radians(c2.lng)
    
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    
    a = (math.sin(dlat / 2) ** 2 + 
         math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    
    return EARTH_RADIUS_M * c

def project_point_on_segment(p: Coordinate, a: Coordinate, b: Coordinate) -> Coordinate:
    """
    Project point p onto line segment ab
    
    Args:
        p: Point to project
        a: Start point of segment
        b: End point of segment
    
    Returns:
        Projected coordinate on segment
    """
    dx = b.lng - a.lng
    dy = b.lat - a.lat
    
    if dx == 0 and dy == 0:
        return a
    
    t = ((p.lng - a.lng) * dx + (p.lat - a.lat) * dy) / (dx * dx + dy * dy)
    t = max(0, min(1, t))
    
    return Coordinate(
        lat=a.lat + t * dy,
        lng=a.lng + t * dx
    )

def get_nearest_point(point: Coordinate, polyline: List[Coordinate]) -> Tuple[Coordinate, float]:
    """
    Find nearest point on polyline to given point
    
    Args:
        point: Point to find nearest from
        polyline: List of coordinates forming the polyline
    
    Returns:
        Tuple of (nearest_coordinate, distance_in_meters)
    """
    if not polyline or len(polyline) < 2:
        return point, 0.0
    
    nearest = polyline[0]
    min_dist = haversine_distance(point, nearest)
    
    for i in range(len(polyline) - 1):
        projected = project_point_on_segment(point, polyline[i], polyline[i + 1])
        dist = haversine_distance(point, projected)
        
        if dist < min_dist:
            min_dist = dist
            nearest = projected
    
    return nearest, min_dist
