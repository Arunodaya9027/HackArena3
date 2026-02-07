"""
Geometry Processor - Main orchestration service
Coordinates overlap detection, displacement, topology preservation, and depth assignment
"""
from typing import List, Dict
import time
from shapely.geometry import LineString

from app.models.geometry_models import (
    GeometryRequest, GeometryResponse, DisplacementResult,
    ConflictMetadata, FeatureInput
)
from app.services.precision_overlap_detector import PrecisionOverlapDetector
from app.services.displacement_calculator import DisplacementCalculator
from app.services.topology_preserver import TopologyPreserver
from app.services.depth_assigner import DepthAssigner


class GeometryProcessor:
    """Main geometry processing orchestrator"""
    
    def __init__(self):
        """Initialize geometry processor with all services"""
        self.precision_overlap_detector = None
        self.displacement_calculator = None
        self.topology_preserver = None
        self.depth_assigner = None
        
    def process_geometries(self, request: GeometryRequest) -> GeometryResponse:
        """
        Process geometries to resolve overlaps and assign depth
        
        Args:
            request: Geometry processing request
            
        Returns:
            Geometry processing response with corrected geometries
        """
        start_time = time.time()
        
        # Initialize services with request parameters
        self.precision_overlap_detector = PrecisionOverlapDetector(min_clearance=request.min_clearance, strict_mode=True)
        self.displacement_calculator = DisplacementCalculator(
            repulsion_strength=request.force_strength
        )
        self.topology_preserver = TopologyPreserver(snap_tolerance=0.1)
        self.depth_assigner = DepthAssigner(shadow_offset_scale=0.5)
        
        # Parse features
        parsed_features = self._parse_features(request.features)
        
        # Step 1: Detect overlaps
        overlaps = self.precision_overlap_detector.detect_overlaps(request.features)
        
        # Step 2: Identify junctions for topology preservation
        junctions = self.topology_preserver.find_junctions(parsed_features)
        
        # Step 3: Calculate displacements
        displacement_results = self._calculate_displacements(
            parsed_features, overlaps, junctions
        )
        
        # Step 4: Assign depth metadata if enabled
        if request.enable_3d_depth:
            depth_metadata = self.depth_assigner.assign_depth_metadata(
                parsed_features, overlaps
            )
        else:
            depth_metadata = {}
        
        # Step 5: Build results
        results = self._build_results(
            displacement_results, depth_metadata, overlaps
        )
        
        # Step 6: Validate topology
        displaced_features = [
            {'feature': r['feature'], 'geometry': r['displaced_geometry']}
            for r in displacement_results.values()
        ]
        topology_preserved = self.topology_preserver.validate_topology(
            parsed_features, displaced_features
        )
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return GeometryResponse(
            results=results,
            total_conflicts_resolved=len(overlaps),
            execution_time_ms=round(execution_time, 2),
            topology_preserved=topology_preserved
        )
    
    def _parse_features(self, features: List[FeatureInput]) -> List[Dict]:
        """Parse WKT features into Shapely geometries"""
        parsed = []
        for feature in features:
            geometry = self.precision_overlap_detector.parse_wkt(feature.wkt)
            parsed.append({
                'feature': feature,
                'geometry': geometry
            })
        return parsed
    
    def _calculate_displacements(self,
                                parsed_features: List[Dict],
                                overlaps: List[Dict],
                                junctions: Dict) -> Dict[str, Dict]:
        """
        Calculate and apply displacements for all features
        
        Returns:
            Dictionary mapping feature_id to displacement info
        """
        results = {}
        
        # Create a map from feature_id to feature dict for quick lookup
        feature_map = {feat_dict['feature'].id: feat_dict for feat_dict in parsed_features}
        
        # Group overlaps by feature that needs to be displaced
        features_to_displace = {}
        
        for overlap in overlaps:
            # Determine which feature should be displaced
            displaced_id = self.precision_overlap_detector.get_conflict_priority(overlap)
            
            if displaced_id not in features_to_displace:
                features_to_displace[displaced_id] = []
            
            features_to_displace[displaced_id].append(overlap)
        
        # Apply displacements
        for feat_dict in parsed_features:
            feature = feat_dict['feature']
            feature_id = feature.id
            original_geometry = feat_dict['geometry']
            
            if feature_id in features_to_displace:
                # Feature needs displacement
                conflicts = features_to_displace[feature_id]
                
                # Prepare conflict features for displacement calculation
                conflict_features = []
                for conflict in conflicts:
                    # Extract feature IDs from feature_pair tuple
                    id1, id2 = conflict['feature_pair']
                    
                    # Get the other feature (not the one being displaced)
                    other_id = id2 if id1 == feature_id else id1
                    other_feat_dict = feature_map[other_id]
                    
                    conflict_features.append({
                        'geometry': other_feat_dict['geometry'],
                        'feature': other_feat_dict['feature'],
                        'clearance_violation': self.precision_overlap_detector.min_clearance
                    })
                
                # Calculate displacement
                displaced_geometry, displacement_history = self.displacement_calculator.displace_feature(
                    {'feature': feature, 'geometry': original_geometry},
                    conflict_features
                )
                
                # Preserve topology
                final_geometry = self.topology_preserver.preserve_connectivity(
                    feature_id, displaced_geometry, original_geometry,
                    parsed_features, junctions
                )
                
                # Calculate total displacement
                total_dx = sum(d[0] for d in displacement_history)
                total_dy = sum(d[1] for d in displacement_history)
                total_displacement = (total_dx, total_dy)
                displacement_magnitude = self.displacement_calculator.calculate_displacement_magnitude(
                    total_displacement
                )
                
                results[feature_id] = {
                    'feature': feature,
                    'original_geometry': original_geometry,
                    'displaced_geometry': final_geometry,
                    'was_displaced': True,
                    'displacement_vector': total_displacement,
                    'displacement_magnitude': displacement_magnitude,
                    'conflicts': conflicts
                }
            else:
                # Feature was not displaced
                results[feature_id] = {
                    'feature': feature,
                    'original_geometry': original_geometry,
                    'displaced_geometry': original_geometry,
                    'was_displaced': False,
                    'displacement_vector': (0.0, 0.0),
                    'displacement_magnitude': 0.0,
                    'conflicts': []
                }
        
        return results
    
    def _build_results(self,
                      displacement_results: Dict[str, Dict],
                      depth_metadata: Dict[str, Dict],
                      overlaps: List[Dict]) -> List[DisplacementResult]:
        """Build final result objects"""
        results = []
        
        for feature_id, disp_info in displacement_results.items():
            feature = disp_info['feature']
            original_wkt = feature.wkt
            displaced_wkt = disp_info['displaced_geometry'].wkt
            
            # Build conflict metadata
            conflict_metadata_list = []
            for conflict in disp_info['conflicts']:
                # Extract feature IDs from feature_pair tuple
                id1, id2 = conflict['feature_pair']
                other_id = id2 if id1 == feature_id else id1
                
                # Calculate overlap distance from conflict data
                overlap_dist = conflict.get('severity_score', 0.0)
                
                depth_meta = depth_metadata.get(feature_id, {})
                
                conflict_meta = ConflictMetadata(
                    conflict_pair=(feature_id, other_id),
                    overlap_amount=overlap_dist,
                    displacement_vector=disp_info['displacement_vector'],
                    z_index=depth_meta.get('z_index', 100),
                    visual_depth_flag=depth_meta.get('visual_depth_flag', False)
                )
                conflict_metadata_list.append(conflict_meta)
            
            result = DisplacementResult(
                feature_id=feature_id,
                original_wkt=original_wkt,
                corrected_wkt=displaced_wkt,
                was_displaced=disp_info['was_displaced'],
                displacement_magnitude=round(disp_info['displacement_magnitude'], 3),
                conflicts=conflict_metadata_list
            )
            results.append(result)
        
        return results
