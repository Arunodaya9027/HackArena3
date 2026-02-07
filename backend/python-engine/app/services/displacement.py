"""
Displacement algorithm service
Core logic for feature displacement processing
"""
import time
import math
from typing import List, Tuple
from app.models import Feature, ProcessingMetrics, Coordinate
from app.utils.geometry import haversine_distance, get_nearest_point

# Algorithm constants
MIN_CLEARANCE = 10.0  # meters
REPULSION_ITERATIONS = 5

def process_displacement(features: List[Feature]) -> Tuple[List[Feature], ProcessingMetrics]:
    """
    Core displacement algorithm - transferred from JavaScript
    
    Processes features to resolve overlaps by displacing lower-priority features
    away from higher-priority features using iterative repulsion.
    
    Args:
        features: List of features to process
    
    Returns:
        Tuple of (processed_features, processing_metrics)
    """
    start_time = time.time()
    
    overlaps_detected = 0
    overlaps_resolved = 0
    max_displacement = 0.0
    
    # Sort by priority (lower = higher priority, fixed first)
    sorted_features = sorted(features, key=lambda f: f.priority)
    
    # Split into fixed (priority <= 2) and moveable (priority > 2)
    fixed = [f for f in sorted_features if f.priority <= 2]
    moveable = [f for f in sorted_features if f.priority > 2]
    
    # Store original coordinates
    for feature in moveable:
        if feature.origCoords is None:
            feature.origCoords = [Coordinate(lat=c.lat, lng=c.lng) for c in feature.coords]
    
    # Iterative repulsion algorithm
    for iteration in range(REPULSION_ITERATIONS):
        for m_feature in moveable:
            if not m_feature.coords or len(m_feature.coords) < 2:
                continue
            
            feature_moved = False
            new_coords = []
            
            for vertex in m_feature.coords:
                total_dx = 0.0
                total_dy = 0.0
                count = 0
                
                # Check against all fixed features
                for f_feature in fixed:
                    nearest, dist_meters = get_nearest_point(vertex, f_feature.coords)
                    
                    required_dist = (f_feature.width / 2.0) + (m_feature.width / 2.0) + MIN_CLEARANCE
                    
                    if dist_meters < required_dist:
                        if iteration == 0:
                            overlaps_detected += 1
                        
                        push_dist = (required_dist - dist_meters) * 1.2
                        angle = math.atan2(vertex.lat - nearest.lat, vertex.lng - nearest.lng)
                        
                        push_deg = push_dist / 111111.0  # approx meters to degrees
                        
                        total_dx += math.sin(angle) * push_deg
                        total_dy += math.cos(angle) * push_deg
                        count += 1
                
                if count > 0:
                    feature_moved = True
                    overlaps_resolved += 1
                    
                    new_lat = vertex.lat + (total_dy / count)
                    new_lng = vertex.lng + (total_dx / count)
                    new_vertex = Coordinate(lat=new_lat, lng=new_lng)
                    
                    shift = haversine_distance(vertex, new_vertex)
                    if shift > max_displacement:
                        max_displacement = shift
                    
                    new_coords.append(new_vertex)
                else:
                    new_coords.append(vertex)
            
            if feature_moved:
                m_feature.coords = new_coords
                m_feature.displaced = True
    
    # Combine all features
    all_features = fixed + moveable
    
    processing_time = time.time() - start_time
    
    metrics = ProcessingMetrics(
        overlapsDetected=overlaps_detected,
        overlapsResolved=overlaps_resolved,
        maxDisplacementMeters=round(max_displacement, 2),
        processingTimeSeconds=round(processing_time, 3),
        totalFeatures=len(all_features)
    )
    
    return all_features, metrics
