"""
Topology Validator Service
Ensures topology preservation - intersections remain connected
"""
from shapely.geometry import LineString, Point
from shapely import wkt as shapely_wkt
from typing import List, Dict, Tuple, Set
import numpy as np

from ..models.geometry_models import FeatureInput


class TopologyValidator:
    """Validates and preserves topology during displacement"""
    
    def __init__(self, snap_tolerance: float = 0.01):
        """
        Initialize topology validator
        
        Args:
            snap_tolerance: Distance threshold for considering points as junctions
        """
        self.snap_tolerance = snap_tolerance
    
    def find_junctions(self, features: List[FeatureInput]) -> Dict[Tuple[float, float], List[str]]:
        """
        Find junction points where multiple features connect
        
        Args:
            features: List of input features
            
        Returns:
            Dictionary mapping junction coordinates to list of feature IDs that share it
        """
        junctions = {}
        
        # Extract all endpoints
        endpoints = []
        for feature in features:
            line = shapely_wkt.loads(feature.wkt)
            coords = list(line.coords)
            
            # Add start and end points
            start_point = coords[0]
            end_point = coords[-1]
            
            endpoints.append((start_point, feature.id, 'start'))
            endpoints.append((end_point, feature.id, 'end'))
        
        # Group endpoints that are within snap tolerance
        used = set()
        for i, (point1, feature_id1, pos1) in enumerate(endpoints):
            if i in used:
                continue
                
            # Find all points within snap tolerance
            junction_point = point1
            connected_features = [(feature_id1, pos1)]
            
            for j, (point2, feature_id2, pos2) in enumerate(endpoints):
                if i != j and j not in used:
                    dist = np.sqrt((point1[0] - point2[0])**2 + (point1[1] - point2[1])**2)
                    if dist <= self.snap_tolerance:
                        connected_features.append((feature_id2, pos2))
                        used.add(j)
            
            # Only consider as junction if 2 or more features connect
            if len(connected_features) >= 2:
                junctions[junction_point] = connected_features
                used.add(i)
        
        return junctions
    
    def snap_endpoints_to_junctions(self,
                                    wkt_string: str,
                                    feature_id: str,
                                    junctions: Dict[Tuple[float, float], List[Tuple[str, str]]]) -> str:
        """
        Snap endpoints back to original junction coordinates
        Ensures topology preservation after displacement
        
        Args:
            wkt_string: Displaced WKT LINESTRING
            feature_id: Feature identifier
            junctions: Dictionary of junction points
            
        Returns:
            WKT LINESTRING with endpoints snapped to junctions
        """
        line = shapely_wkt.loads(wkt_string)
        coords = list(line.coords)
        
        # Check if start or end points should be snapped
        for junction_point, connected_features in junctions.items():
            feature_positions = {fid: pos for fid, pos in connected_features}
            
            if feature_id in feature_positions:
                position = feature_positions[feature_id]
                
                if position == 'start':
                    # Snap start point to junction
                    coords[0] = junction_point
                elif position == 'end':
                    # Snap end point to junction
                    coords[-1] = junction_point
        
        # Create new LineString with snapped endpoints
        new_line = LineString(coords)
        return new_line.wkt
    
    def validate_connectivity(self,
                             original_features: List[FeatureInput],
                             corrected_wkts: Dict[str, str]) -> Dict[str, bool]:
        """
        Validate that connectivity is preserved after displacement
        
        Args:
            original_features: Original input features
            corrected_wkts: Dictionary mapping feature_id to corrected WKT
            
        Returns:
            Dictionary mapping feature_id to connectivity status (True if preserved)
        """
        # Find junctions in original features
        original_junctions = self.find_junctions(original_features)
        
        # Create modified features list
        modified_features = []
        for feature in original_features:
            if feature.id in corrected_wkts:
                modified_feature = FeatureInput(
                    id=feature.id,
                    wkt=corrected_wkts[feature.id],
                    priority=feature.priority
                )
                modified_features.append(modified_feature)
            else:
                modified_features.append(feature)
        
        # Find junctions in modified features
        modified_junctions = self.find_junctions(modified_features)
        
        # Compare junction counts
        connectivity_status = {}
        for feature in original_features:
            # Count junctions for this feature
            original_count = sum(1 for conn_features in original_junctions.values() 
                               if any(fid == feature.id for fid, _ in conn_features))
            modified_count = sum(1 for conn_features in modified_junctions.values() 
                               if any(fid == feature.id for fid, _ in conn_features))
            
            connectivity_status[feature.id] = (original_count == modified_count)
        
        return connectivity_status
