"""
Geometry Engine Orchestrator
Main service that coordinates overlap detection, displacement, and topology validation
"""
from typing import List, Dict, Tuple
from collections import defaultdict

from ..models.geometry_models import (
    FeatureInput, GeometryRequest, GeometryResponse,
    DisplacementResult, ConflictMetadata, FeaturePriority
)
from .precision_overlap_detector import PrecisionOverlapDetector
from .displacement_calculator import DisplacementCalculator
from .topology_validator import TopologyValidator


class GeometryEngine:
    """Main geometry processing engine"""
    
    def __init__(self):
        """Initialize the geometry engine with all required services"""
        self.precision_overlap_detector = None
        self.displacement_calculator = DisplacementCalculator(repulsion_strength=1.5)
        self.topology_validator = TopologyValidator(snap_tolerance=0.1)
    
    def process_geometry(self, request: GeometryRequest) -> GeometryResponse:
        """
        Main processing pipeline for geometry conflict resolution
        
        Args:
            request: Geometry processing request
            
        Returns:
            Geometry response with corrected WKT and metadata
        """
        # Initialize overlap detector with min clearance from request
        self.precision_overlap_detector = PrecisionOverlapDetector(min_clearance=request.min_clearance, strict_mode=True)
        
        features = request.features
        
        # Step 1: Detect overlaps
        overlaps = self.precision_overlap_detector.detect_overlaps(features)
        
        if not overlaps:
            # No conflicts - return original features
            results = [
                DisplacementResult(
                    feature_id=f.id,
                    original_wkt=f.wkt,
                    corrected_wkt=f.wkt,
                    was_displaced=False,
                    metadata=None
                )
                for f in features
            ]
            
            return GeometryResponse(
                results=results,
                total_conflicts=0,
                total_displaced=0,
                processing_summary=self._create_summary(features, 0, 0)
            )
        
        # Step 2: Find junctions for topology preservation
        junctions = self.topology_validator.find_junctions(features)
        
        # Step 3: Process conflicts
        displacement_vectors = defaultdict(list)
        conflicts_metadata = {}
        
        for idx1, idx2, overlap_area in overlaps:
            feature1 = features[idx1]
            feature2 = features[idx2]
            
            # Determine which feature to displace (lower priority gets displaced)
            if self._get_priority_value(feature1.priority) < self._get_priority_value(feature2.priority):
                # feature1 has higher priority, displace feature2
                fixed_feature = feature1
                moving_feature = feature2
                moving_idx = idx2
            else:
                # feature2 has higher priority (or equal), displace feature1
                fixed_feature = feature2
                moving_feature = feature1
                moving_idx = idx1
            
            # Calculate required displacement
            displacement_distance = self.precision_overlap_detector.calculate_displacement_distance(
                fixed_feature, moving_feature, overlap_area
            )
            
            # Calculate displacement vector
            dx, dy = self.displacement_calculator.calculate_displacement_for_pair(
                fixed_feature, moving_feature, displacement_distance
            )
            
            # Store displacement vector
            displacement_vectors[moving_feature.id].append((dx, dy))
            
            # Store conflict metadata
            conflict_key = (moving_feature.id, fixed_feature.id)
            conflicts_metadata[conflict_key] = {
                'conflict_pair': [fixed_feature.id, moving_feature.id],
                'displacement_vector': [dx, dy],
                'overlap_amount': overlap_area,
                'z_index': self._assign_z_index(fixed_feature, moving_feature),
                'visual_depth_flag': True
            }
        
        # Step 4: Accumulate displacements for features with multiple conflicts
        final_displacements = self.displacement_calculator.accumulate_displacements(
            displacement_vectors
        )
        
        # Step 5: Apply displacements
        corrected_wkts = {}
        for feature_id, (dx, dy) in final_displacements.items():
            if abs(dx) > 0.001 or abs(dy) > 0.001:  # Only displace if significant
                feature = next(f for f in features if f.id == feature_id)
                corrected_wkt = self.displacement_calculator.apply_displacement(
                    feature.wkt, (dx, dy)
                )
                corrected_wkts[feature_id] = corrected_wkt
        
        # Step 6: Snap endpoints back to junctions (topology preservation)
        for feature_id, corrected_wkt in corrected_wkts.items():
            corrected_wkts[feature_id] = self.topology_validator.snap_endpoints_to_junctions(
                corrected_wkt, feature_id, junctions
            )
        
        # Step 7: Build results
        results = []
        for feature in features:
            was_displaced = feature.id in corrected_wkts
            corrected_wkt = corrected_wkts.get(feature.id, feature.wkt)
            
            # Find metadata for this feature
            metadata = None
            if was_displaced:
                for (moving_id, fixed_id), meta in conflicts_metadata.items():
                    if moving_id == feature.id:
                        metadata = ConflictMetadata(**meta)
                        break
            
            results.append(
                DisplacementResult(
                    feature_id=feature.id,
                    original_wkt=feature.wkt,
                    corrected_wkt=corrected_wkt,
                    was_displaced=was_displaced,
                    metadata=metadata
                )
            )
        
        total_conflicts = len(overlaps)
        total_displaced = len(corrected_wkts)
        
        return GeometryResponse(
            results=results,
            total_conflicts=total_conflicts,
            total_displaced=total_displaced,
            processing_summary=self._create_summary(features, total_conflicts, total_displaced)
        )
    
    def _get_priority_value(self, priority: FeaturePriority) -> int:
        """Get numeric priority value (lower = higher priority)"""
        return 1 if priority == FeaturePriority.P1_HIGHWAY else 2
    
    def _assign_z_index(self, fixed_feature: FeatureInput, moving_feature: FeatureInput) -> int:
        """Assign Z-index for 3D rendering (higher priority gets higher z-index)"""
        if fixed_feature.priority == FeaturePriority.P1_HIGHWAY:
            return 2  # Highway above
        else:
            return 1  # Road below
    
    def _create_summary(self, features: List[FeatureInput], 
                       total_conflicts: int, total_displaced: int) -> Dict:
        """Create processing summary statistics"""
        highways = sum(1 for f in features if f.priority == FeaturePriority.P1_HIGHWAY)
        roads = sum(1 for f in features if f.priority == FeaturePriority.P2_ROAD)
        
        return {
            'features_processed': len(features),
            'highways': highways,
            'roads': roads,
            'conflicts_detected': total_conflicts,
            'features_displaced': total_displaced
        }
