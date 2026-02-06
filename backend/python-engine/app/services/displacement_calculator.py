"""
Displacement Calculator Service
Implements force-directed displacement algorithm
"""
import numpy as np
from shapely.geometry import LineString, Point
from shapely import wkt as shapely_wkt
from typing import List, Tuple, Dict
from collections import defaultdict

from ..models.geometry_models import FeatureInput, FeaturePriority


class DisplacementCalculator:
    """Calculates force-directed displacement for overlapping features"""
    
    def __init__(self, repulsion_strength: float = 1.0):
        """
        Initialize displacement calculator
        
        Args:
            repulsion_strength: Strength of repulsion force (default: 1.0)
        """
        self.repulsion_strength = repulsion_strength
    
    def calculate_repulsion_vector(self,
                                   line1: LineString,
                                   line2: LineString) -> Tuple[float, float]:
        """
        Calculate repulsion vector between two lines using force-directed approach
        Treat features like magnets with same pole that repel each other
        
        Args:
            line1: First LineString (stays in place)
            line2: Second LineString (gets displaced)
            
        Returns:
            Tuple of (dx, dy) displacement vector
        """
        # Get centroids for initial direction
        centroid1 = line1.centroid
        centroid2 = line2.centroid
        
        # Calculate vector from line1 to line2
        dx = centroid2.x - centroid1.x
        dy = centroid2.y - centroid1.y
        
        # Calculate distance
        distance = np.sqrt(dx**2 + dy**2)
        
        if distance < 0.01:  # Avoid division by zero
            # If centroids are very close, use perpendicular direction
            dx, dy = 1.0, 0.0
            distance = 1.0
        
        # Normalize direction
        dx_norm = dx / distance
        dy_norm = dy / distance
        
        # Apply repulsion force (inverse square law)
        force_magnitude = self.repulsion_strength / (distance + 0.1)
        
        return (dx_norm * force_magnitude, dy_norm * force_magnitude)
    
    def apply_displacement(self,
                          wkt_string: str,
                          displacement_vector: Tuple[float, float]) -> str:
        """
        Apply displacement to a WKT LINESTRING
        
        Args:
            wkt_string: Original WKT LINESTRING
            displacement_vector: (dx, dy) displacement to apply
            
        Returns:
            Displaced WKT LINESTRING
        """
        line = shapely_wkt.loads(wkt_string)
        dx, dy = displacement_vector
        
        # Displace all coordinates
        new_coords = [(x + dx, y + dy) for x, y in line.coords]
        
        # Create new LineString
        new_line = LineString(new_coords)
        
        return new_line.wkt
    
    def calculate_displacement_for_pair(self,
                                       fixed_feature: FeatureInput,
                                       moving_feature: FeatureInput,
                                       displacement_distance: float) -> Tuple[float, float]:
        """
        Calculate displacement vector for a pair of conflicting features
        
        Args:
            fixed_feature: Feature that stays in place (higher priority)
            moving_feature: Feature that gets displaced (lower priority)
            displacement_distance: Required displacement distance
            
        Returns:
            Tuple of (dx, dy) displacement vector scaled to required distance
        """
        line_fixed = shapely_wkt.loads(fixed_feature.wkt)
        line_moving = shapely_wkt.loads(moving_feature.wkt)
        
        # Get base repulsion vector
        dx, dy = self.calculate_repulsion_vector(line_fixed, line_moving)
        
        # Scale to required displacement distance
        current_magnitude = np.sqrt(dx**2 + dy**2)
        if current_magnitude > 0:
            scale = displacement_distance / current_magnitude
            dx *= scale
            dy *= scale
        
        return (dx, dy)
    
    def accumulate_displacements(self,
                                 displacement_dict: Dict[str, List[Tuple[float, float]]]) -> Dict[str, Tuple[float, float]]:
        """
        Accumulate multiple displacement vectors for features with multiple conflicts
        
        Args:
            displacement_dict: Dictionary mapping feature_id to list of displacement vectors
            
        Returns:
            Dictionary mapping feature_id to final accumulated displacement vector
        """
        result = {}
        
        for feature_id, vectors in displacement_dict.items():
            if not vectors:
                result[feature_id] = (0.0, 0.0)
            else:
                # Sum all displacement vectors
                total_dx = sum(dx for dx, dy in vectors)
                total_dy = sum(dy for dx, dy in vectors)
                result[feature_id] = (total_dx, total_dy)
        
        return result
