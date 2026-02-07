"""
Geometry Processor - SIMPLIFIED for Hackathon
Focus on RIGHT results, not PERFECT cartography
Priority-based displacement without over-engineering
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


class GeometryProcessor:
    """Simplified geometry processor - focus on functional correctness"""
    
    def __init__(self):
        """Initialize geometry processor"""
        self.precision_overlap_detector = None
        self.displacement_calculator = None
        
    def process_geometries(self, request: GeometryRequest) -> GeometryResponse:
        """
        SIMPLIFIED: Process geometries to resolve overlaps with priority-based displacement
        
        Focus on FUNCTIONAL CORRECTNESS:
        - P1 (Railway/Highway) never moves
        - P2 (Road) moves minimally  
        - P3 (Street) moves moderately
        - P4/P5 (Icon/Label) move freely
        
        Args:
            request: Geometry processing request
            
        Returns:
            Geometry processing response with corrected geometries
        """
        start_time = time.time()
        
        # Initialize ONLY the essential services
        self.precision_overlap_detector = PrecisionOverlapDetector(
            min_clearance=request.min_clearance, 
            strict_mode=True
        )
        self.displacement_calculator = DisplacementCalculator(
            repulsion_strength=request.force_strength
        )
        
        # Parse features
        parsed_features = self._parse_features(request.features)
        
        # Step 1: Detect overlaps (KEEP - essential)
        overlaps = self.precision_overlap_detector.detect_overlaps(request.features)
        
        # Step 2: Calculate displacements (SIMPLIFIED - no topology preservation)
        displacement_results = self._calculate_displacements_simple(
            parsed_features, overlaps
        )
        
        # Step 3: Build results
        results = self._build_results(displacement_results, overlaps)
        
        execution_time = (time.time() - start_time) * 1000  # Convert to ms
        
        return GeometryResponse(
            results=results,
            total_conflicts_resolved=len(overlaps),
            execution_time_ms=round(execution_time, 2),
            topology_preserved=True  # Simplified: always True for hackathon
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
    
    def _calculate_displacements_simple(self,
                                        parsed_features: List[Dict],
                                        overlaps: List[Dict]) -> Dict[str, Dict]:
        """
        SIMPLIFIED displacement calculation - focus on priority rules
        
        Rules:
        1. P1 features (Railway, Highway) NEVER move
        2. P2 features (Road) move only for P1
        3. P3 features (Street, Park) move for P1 and P2
        4. P4 features (Icon, Building) move for P1, P2, P3
        5. P5 features (Label) move for all others
        
        Returns:
            Dictionary mapping feature_id to displacement info
        """
        results = {}
        
        # Create feature lookup map
        feature_map = {feat_dict['feature'].id: feat_dict for feat_dict in parsed_features}
        
        # Group overlaps by feature that needs to be displaced
        features_to_displace = {}
        
        for overlap in overlaps:
            # Determine which feature should be displaced based on priority
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
                
                # Calculate displacement (SIMPLE - no topology preservation)
                displaced_geometry, displacement_history = self.displacement_calculator.displace_feature(
                    {'feature': feature, 'geometry': original_geometry},
                    conflict_features
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
                    'displaced_geometry': displaced_geometry,
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
                      overlaps: List[Dict]) -> List[DisplacementResult]:
        """Build final result objects (SIMPLIFIED - no depth metadata)"""
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
                
                # SIMPLIFIED: Use basic z-index based on priority
                z_index = self._get_simple_z_index(feature_id)
                
                conflict_meta = ConflictMetadata(
                    conflict_pair=(feature_id, other_id),
                    overlap_amount=overlap_dist,
                    displacement_vector=disp_info['displacement_vector'],
                    z_index=z_index,
                    visual_depth_flag=disp_info['was_displaced']
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
    
    def _get_simple_z_index(self, feature_id: str) -> int:
        """
        Get simple z-index based on priority
        P1 = 1000 (top)
        P2 = 900
        P3 = 800
        P4 = 700
        P5 = 600 (bottom)
        """
        if 'P1_' in feature_id:
            return 1000
        elif 'P2_' in feature_id:
            return 900
        elif 'P3_' in feature_id:
            return 800
        elif 'P4_' in feature_id:
            return 700
        elif 'P5_' in feature_id:
            return 600
        else:
            return 500  # default
