"""
Depth Assigner Service
Assigns Z-order and visual depth cues for 3D representation
"""
from typing import List, Dict, Tuple, Optional
import numpy as np
from shapely.geometry import LineString, Point

from app.models.geometry_models import FeaturePriority


class DepthAssigner:
    """Assigns 3D depth and visual cues to features"""
    
    def __init__(self, shadow_offset_scale: float = 0.5):
        """
        Initialize depth assigner
        
        Args:
            shadow_offset_scale: Scale factor for shadow offset calculations
        """
        self.shadow_offset_scale = shadow_offset_scale
        self.base_z_index = 100  # Base Z-index for features
        
    def assign_z_order(self, 
                      overlaps: List[Dict],
                      features: List[Dict]) -> Dict[str, int]:
        """
        Assign Z-order to features based on priority and conflicts
        Higher priority features (highways) get higher Z-index
        
        Args:
            overlaps: List of overlap dictionaries
            features: List of all features
            
        Returns:
            Dictionary mapping feature_id to z_index
        """
        z_orders = {}
        
        # Initialize all features with base Z-index
        for feat_dict in features:
            feature_id = feat_dict['feature'].id
            priority = feat_dict['feature'].priority
            
            # Highways start with higher base Z
            if priority == FeaturePriority.HIGHWAY:
                z_orders[feature_id] = self.base_z_index + 10
            else:
                z_orders[feature_id] = self.base_z_index
        
        # Adjust Z-order based on conflicts
        for overlap in overlaps:
            feat_a_id = overlap['feature_a'].id
            feat_b_id = overlap['feature_b'].id
            
            # Higher priority feature gets higher Z
            if overlap['feature_a'].priority == FeaturePriority.HIGHWAY:
                z_orders[feat_a_id] = max(z_orders.get(feat_a_id, self.base_z_index), 
                                         z_orders.get(feat_b_id, self.base_z_index) + 1)
            elif overlap['feature_b'].priority == FeaturePriority.HIGHWAY:
                z_orders[feat_b_id] = max(z_orders.get(feat_b_id, self.base_z_index),
                                         z_orders.get(feat_a_id, self.base_z_index) + 1)
        
        return z_orders
    
    def calculate_shadow_offset(self,
                                z_index: int,
                                feature_priority: FeaturePriority) -> Tuple[float, float]:
        """
        Calculate shadow offset for visual depth effect
        
        Args:
            z_index: Z-order value
            feature_priority: Feature priority level
            
        Returns:
            (shadow_x, shadow_y) offset in points
        """
        # Higher Z-index = more elevated = larger shadow
        relative_height = (z_index - self.base_z_index) * self.shadow_offset_scale
        
        # Shadow direction (assumes light from top-left)
        shadow_angle = np.radians(45)  # 45 degrees
        shadow_x = relative_height * np.cos(shadow_angle)
        shadow_y = -relative_height * np.sin(shadow_angle)  # Negative for downward
        
        return (shadow_x, shadow_y)
    
    def determine_depth_flag(self,
                            feature_id: str,
                            overlaps: List[Dict],
                            z_orders: Dict[str, int]) -> bool:
        """
        Determine if a feature needs visual depth cues
        
        Args:
            feature_id: Feature identifier
            overlaps: List of overlaps
            z_orders: Z-order assignments
            
        Returns:
            True if feature needs depth visual cues, False otherwise
        """
        # Feature needs depth cues if:
        # 1. It's involved in a conflict
        # 2. It has different Z-order from conflicting features
        
        feature_z = z_orders.get(feature_id, self.base_z_index)
        
        for overlap in overlaps:
            # Extract feature IDs from feature_pair tuple
            id1, id2 = overlap['feature_pair']
            
            if id1 == feature_id or id2 == feature_id:
                other_id = id2 if id1 == feature_id else id1
                other_z = z_orders.get(other_id, self.base_z_index)
                
                # If Z-orders differ, needs depth cues
                if abs(feature_z - other_z) > 0:
                    return True
        
        return False
    
    def assign_virtual_depth(self,
                            feature_id: str,
                            z_index: int,
                            priority: FeaturePriority) -> float:
        """
        Calculate virtual depth value for rendering
        
        Args:
            feature_id: Feature identifier
            z_index: Z-order value
            priority: Feature priority
            
        Returns:
            Virtual depth value (0 = ground level, higher = elevated)
        """
        # Normalize Z-index to depth value
        depth = (z_index - self.base_z_index) / 10.0
        
        # Highways are generally elevated in complex junctions
        if priority == FeaturePriority.HIGHWAY:
            depth += 0.5
        
        return max(0.0, depth)
    
    def classify_junction_type(self, overlaps: List[Dict]) -> str:
        """
        Classify junction complexity
        
        Args:
            overlaps: List of overlaps at a junction
            
        Returns:
            Junction type: 'simple', 'complex', 'flyover', 'tunnel'
        """
        if len(overlaps) == 0:
            return 'simple'
        elif len(overlaps) == 1:
            return 'simple'
        elif len(overlaps) <= 3:
            return 'complex'
        else:
            # Check if there are significant Z-level differences
            z_levels = set()
            for overlap in overlaps:
                # This is a simplified heuristic
                if overlap['feature_a'].priority == FeaturePriority.HIGHWAY:
                    z_levels.add('high')
                else:
                    z_levels.add('low')
            
            if len(z_levels) > 1:
                return 'flyover'
            else:
                return 'complex'
    
    def assign_depth_metadata(self,
                             features: List[Dict],
                             overlaps: List[Dict]) -> Dict[str, Dict]:
        """
        Assign complete depth metadata to all features
        
        Args:
            features: List of features
            overlaps: List of overlaps
            
        Returns:
            Dictionary mapping feature_id to depth metadata
        """
        # Assign Z-orders
        z_orders = self.assign_z_order(overlaps, features)
        
        metadata = {}
        
        for feat_dict in features:
            feature = feat_dict['feature']
            feature_id = feature.id
            priority = feature.priority
            z_index = z_orders[feature_id]
            
            # Determine if depth cues needed
            needs_depth_cues = self.determine_depth_flag(feature_id, overlaps, z_orders)
            
            # Calculate shadow offset
            shadow_offset = self.calculate_shadow_offset(z_index, priority) if needs_depth_cues else None
            
            # Calculate virtual depth
            virtual_depth = self.assign_virtual_depth(feature_id, z_index, priority)
            
            metadata[feature_id] = {
                'z_index': z_index,
                'visual_depth_flag': needs_depth_cues,
                'shadow_offset': shadow_offset,
                'virtual_depth': virtual_depth,
                'priority': priority.value
            }
        
        return metadata
