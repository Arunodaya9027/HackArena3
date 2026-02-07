"""
Topology Preserver Service
Ensures intersections remain connected after displacement
"""
from typing import List, Dict, Set, Tuple
from shapely.geometry import LineString, Point
from shapely.ops import nearest_points
import numpy as np


class TopologyPreserver:
    """Preserves topological relationships between features during displacement"""
    
    def __init__(self, snap_tolerance: float = 0.1):
        """
        Initialize topology preserver
        
        Args:
            snap_tolerance: Distance threshold for snapping endpoints to junctions
        """
        self.snap_tolerance = snap_tolerance
        
    def find_junctions(self, features: List[Dict]) -> Dict[str, Point]:
        """
        Identify junction points where multiple features meet
        
        Args:
            features: List of feature dictionaries with 'feature' and 'geometry'
            
        Returns:
            Dictionary mapping junction coordinates to Point geometries
        """
        junctions = {}
        endpoint_registry = {}  # Maps coordinate tuples to list of feature IDs
        
        for feat_dict in features:
            feature = feat_dict['feature']
            geometry = feat_dict['geometry']
            
            # Get start and end points
            start_point = Point(geometry.coords[0])
            end_point = Point(geometry.coords[-1])
            
            # Register endpoints
            start_key = self._point_to_key(start_point)
            end_key = self._point_to_key(end_point)
            
            if start_key not in endpoint_registry:
                endpoint_registry[start_key] = []
            endpoint_registry[start_key].append(feature.id)
            
            if end_key not in endpoint_registry:
                endpoint_registry[end_key] = []
            endpoint_registry[end_key].append(feature.id)
        
        # Junctions are points where 3+ features meet
        for coord_key, feature_ids in endpoint_registry.items():
            if len(feature_ids) >= 2:  # 2+ features share this endpoint
                junctions[coord_key] = Point(coord_key)
        
        return junctions
    
    def _point_to_key(self, point: Point, precision: int = 2) -> Tuple[float, float]:
        """Convert Point to hashable coordinate tuple with precision"""
        return (round(point.x, precision), round(point.y, precision))
    
    def _key_to_point(self, key: Tuple[float, float]) -> Point:
        """Convert coordinate tuple back to Point"""
        return Point(key[0], key[1])
    
    def snap_endpoints_to_junctions(self, 
                                    displaced_geometry: LineString,
                                    original_geometry: LineString,
                                    junctions: Dict[str, Point]) -> LineString:
        """
        Snap displaced geometry endpoints back to original junction points
        Preserves topology while allowing interior points to move
        
        Args:
            displaced_geometry: Geometry after displacement
            original_geometry: Original geometry before displacement
            junctions: Dictionary of junction points
            
        Returns:
            Geometry with endpoints snapped to junctions
        """
        # Get original endpoints
        orig_start = Point(original_geometry.coords[0])
        orig_end = Point(original_geometry.coords[-1])
        
        # Check if original endpoints were at junctions
        start_junction = None
        end_junction = None
        
        for junction_key, junction_point in junctions.items():
            if orig_start.distance(junction_point) < self.snap_tolerance:
                start_junction = junction_point
            if orig_end.distance(junction_point) < self.snap_tolerance:
                end_junction = junction_point
        
        # Build new coordinate list
        new_coords = list(displaced_geometry.coords)
        
        # Snap start point if it was at a junction
        if start_junction:
            new_coords[0] = (start_junction.x, start_junction.y)
        
        # Snap end point if it was at a junction
        if end_junction:
            new_coords[-1] = (end_junction.x, end_junction.y)
        
        return LineString(new_coords)
    
    def preserve_connectivity(self,
                             feature_id: str,
                             displaced_geometry: LineString,
                             original_geometry: LineString,
                             all_features: List[Dict],
                             junctions: Dict[str, Point]) -> LineString:
        """
        Ensure feature remains connected to adjacent features after displacement
        
        Args:
            feature_id: ID of the feature being displaced
            displaced_geometry: Displaced geometry
            original_geometry: Original geometry
            all_features: All features in the dataset
            junctions: Junction points
            
        Returns:
            Topology-preserved geometry
        """
        # Snap to junctions first
        preserved_geometry = self.snap_endpoints_to_junctions(
            displaced_geometry,
            original_geometry,
            junctions
        )
        
        return preserved_geometry
    
    def validate_topology(self, 
                         original_features: List[Dict],
                         displaced_features: List[Dict]) -> bool:
        """
        Validate that topology is preserved after displacement
        
        Args:
            original_features: Original feature list
            displaced_features: Displaced feature list
            
        Returns:
            True if topology is preserved, False otherwise
        """
        # Find junctions in original
        orig_junctions = self.find_junctions(original_features)
        
        # Check if displaced features still connect at those junctions
        for junction_key, junction_point in orig_junctions.items():
            # Count how many displaced features connect at this junction
            connection_count = 0
            
            for feat_dict in displaced_features:
                geometry = feat_dict['geometry']
                start_point = Point(geometry.coords[0])
                end_point = Point(geometry.coords[-1])
                
                if (start_point.distance(junction_point) < self.snap_tolerance or
                    end_point.distance(junction_point) < self.snap_tolerance):
                    connection_count += 1
            
            # Should have at least 2 connections at each junction
            if connection_count < 2:
                return False
        
        return True
    
    def get_connected_features(self, 
                               feature_id: str,
                               all_features: List[Dict]) -> List[str]:
        """
        Find all features connected to a given feature
        
        Args:
            feature_id: Feature ID to find connections for
            all_features: All features in dataset
            
        Returns:
            List of connected feature IDs
        """
        target_feature = None
        for feat_dict in all_features:
            if feat_dict['feature'].id == feature_id:
                target_feature = feat_dict
                break
        
        if not target_feature:
            return []
        
        target_geom = target_feature['geometry']
        target_start = Point(target_geom.coords[0])
        target_end = Point(target_geom.coords[-1])
        
        connected = []
        
        for feat_dict in all_features:
            if feat_dict['feature'].id == feature_id:
                continue  # Skip self
            
            other_geom = feat_dict['geometry']
            other_start = Point(other_geom.coords[0])
            other_end = Point(other_geom.coords[-1])
            
            # Check if any endpoints touch
            if (target_start.distance(other_start) < self.snap_tolerance or
                target_start.distance(other_end) < self.snap_tolerance or
                target_end.distance(other_start) < self.snap_tolerance or
                target_end.distance(other_end) < self.snap_tolerance):
                connected.append(feat_dict['feature'].id)
        
        return connected
