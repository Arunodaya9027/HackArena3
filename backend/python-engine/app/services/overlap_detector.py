"""
Overlap Detection Service
Detects overlaps between feature buffers using Shapely
"""
from shapely.geometry import LineString
from shapely import wkt as shapely_wkt
from typing import List, Tuple, Dict
import numpy as np

from ..models.geometry_models import FeatureInput, FeaturePriority


# Feature width constants
FEATURE_WIDTHS = {
    FeaturePriority.P1_HIGHWAY: 5.0,  # Highway width in points
    FeaturePriority.P2_ROAD: 3.0       # Road width in points
}


class OverlapDetector:
    """Detects overlaps between feature buffers"""
    
    def __init__(self, min_clearance: float = 2.0):
        """
        Initialize overlap detector
        
        Args:
            min_clearance: Minimum clearance required between features (default: 2.0 points)
        """
        self.min_clearance = min_clearance
    
    def parse_wkt(self, wkt_string: str) -> LineString:
        """
        Parse WKT string to Shapely LineString
        
        Args:
            wkt_string: WKT LINESTRING representation
            
        Returns:
            Shapely LineString object
        """
        try:
            geom = shapely_wkt.loads(wkt_string)
            if not isinstance(geom, LineString):
                raise ValueError(f"Expected LINESTRING, got {type(geom).__name__}")
            return geom
        except Exception as e:
            raise ValueError(f"Invalid WKT: {e}")
    
    def get_feature_buffer(self, feature: FeatureInput) -> LineString:
        """
        Create buffer around feature based on its display width
        
        Args:
            feature: Input feature with WKT and priority
            
        Returns:
            Buffered LineString geometry
        """
        line = self.parse_wkt(feature.wkt)
        width = FEATURE_WIDTHS[feature.priority]
        # Buffer by half-width on each side
        buffer_distance = width / 2.0
        return line.buffer(buffer_distance)
    
    def detect_overlaps(self, features: List[FeatureInput]) -> List[Tuple[int, int, float]]:
        """
        Detect overlaps between feature buffers
        
        Args:
            features: List of input features
            
        Returns:
            List of tuples: (index1, index2, overlap_area)
        """
        overlaps = []
        n = len(features)
        
        # Create buffers for all features
        buffers = [self.get_feature_buffer(f) for f in features]
        
        # Check all pairs
        for i in range(n):
            for j in range(i + 1, n):
                buffer_i = buffers[i]
                buffer_j = buffers[j]
                
                # Check if buffers intersect
                if buffer_i.intersects(buffer_j):
                    intersection = buffer_i.intersection(buffer_j)
                    overlap_area = intersection.area
                    
                    # Only report if overlap exceeds minimum clearance
                    if overlap_area > self.min_clearance:
                        overlaps.append((i, j, overlap_area))
        
        return overlaps
    
    def calculate_displacement_distance(self, 
                                       feature1: FeatureInput, 
                                       feature2: FeatureInput,
                                       overlap_area: float) -> float:
        """
        Calculate required displacement distance based on overlap
        
        Args:
            feature1: First feature
            feature2: Second feature  
            overlap_area: Area of overlap
            
        Returns:
            Required displacement distance in points
        """
        # Get the widths of both features
        width1 = FEATURE_WIDTHS[feature1.priority]
        width2 = FEATURE_WIDTHS[feature2.priority]
        
        # Required separation is sum of half-widths plus min clearance
        required_separation = (width1 / 2.0) + (width2 / 2.0) + self.min_clearance
        
        # Estimate current separation from overlap
        # Simplified calculation - can be refined
        displacement_needed = np.sqrt(overlap_area) + self.min_clearance
        
        return displacement_needed
    
    def get_priority_order(self, features: List[FeatureInput]) -> List[int]:
        """
        Get indices sorted by priority (P1_HIGHWAY has higher priority than P2_ROAD)
        Higher priority features stay in place, lower priority features get displaced
        
        Args:
            features: List of input features
            
        Returns:
            List of indices sorted by priority (highest first)
        """
        priority_values = {
            FeaturePriority.P1_HIGHWAY: 1,
            FeaturePriority.P2_ROAD: 2
        }
        
        indexed_features = [(i, priority_values[f.priority]) for i, f in enumerate(features)]
        # Sort by priority value (lower value = higher priority)
        indexed_features.sort(key=lambda x: x[1])
        
        return [idx for idx, _ in indexed_features]
