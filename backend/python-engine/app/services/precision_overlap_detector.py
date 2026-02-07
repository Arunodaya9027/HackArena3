"""
Enhanced Precision Overlap Detection Service
Implements strict conflict detection with multiple detection strategies
NO MERCY - Reports ALL conflicts regardless of type
"""
from shapely.geometry import LineString, Point, MultiPoint
from shapely import wkt as shapely_wkt
from shapely.ops import nearest_points
from typing import List, Tuple, Dict, Optional
import numpy as np

from ..models.geometry_models import FeatureInput, FeaturePriority


# Feature width constants (display width in points)
FEATURE_WIDTHS = {
    # P1: Critical Infrastructure (Highest Priority)
    FeaturePriority.P1_HIGHWAY: 5.0,       # Highways/Expressways
    FeaturePriority.P1_RAILWAY: 4.5,       # Railway Lines
    FeaturePriority.P1_RIVER: 4.0,         # Rivers/Water Bodies
    
    # P2: Major Roads
    FeaturePriority.P2_MAIN_ROAD: 3.5,     # Main Roads/Avenues
    
    # P3: Local Roads
    FeaturePriority.P3_LOCAL_ROAD: 3.0,    # Local Roads/Streets
    FeaturePriority.P3_STREET: 2.8,        # Streets/Lanes
    
    # P4: Structures
    FeaturePriority.P4_BUILDING: 2.5,      # Buildings/Structures
    FeaturePriority.P4_PARK: 2.5,          # Parks/Green Spaces
    
    # P5: Decorative Elements (Lowest Priority)
    FeaturePriority.P5_LABEL: 2.0,         # Text Labels
    FeaturePriority.P5_ICON: 2.0,          # Map Icons
    FeaturePriority.P5_OVERLAP_AREA: 1.5,  # Overlap Areas
    
    # Backward compatibility (deprecated)
    FeaturePriority.P2_ROAD: 3.0           # Generic Road (Legacy)
}


class ConflictType:
    """Types of conflicts detected"""
    BUFFER_OVERLAP = "BUFFER_OVERLAP"           # Buffers intersect
    CENTERLINE_PROXIMITY = "CENTERLINE_PROXIMITY"  # Centerlines too close
    PARALLEL_CONFLICT = "PARALLEL_CONFLICT"     # Parallel segments overlap
    CROSSING_CONFLICT = "CROSSING_CONFLICT"     # Lines cross each other
    ENDPOINT_CONFLICT = "ENDPOINT_CONFLICT"     # Endpoints too close
    SEGMENT_OVERLAP = "SEGMENT_OVERLAP"         # Actual segment overlap


class PrecisionOverlapDetector:
    """
    Enhanced overlap detector with multiple conflict detection strategies
    NO MERCY MODE: Reports ALL conflicts regardless of severity
    """
    
    def __init__(self, min_clearance: float = 2.0, strict_mode: bool = True):
        """
        Initialize precision overlap detector
        
        Args:
            min_clearance: Minimum clearance required between features (default: 2.0 points)
            strict_mode: If True, reports ALL conflicts without threshold filtering
        """
        self.min_clearance = min_clearance
        self.strict_mode = strict_mode
        self.epsilon = 1e-6  # Numerical precision threshold
        
    def parse_wkt(self, wkt_string: str) -> LineString:
        """
        Parse WKT string to Shapely LineString
        
        Args:
            wkt_string: WKT LINESTRING representation
            
        Returns:
            Shapely LineString object
            
        Raises:
            ValueError: If WKT is invalid or not a LINESTRING
        """
        try:
            geom = shapely_wkt.loads(wkt_string)
            if not isinstance(geom, LineString):
                raise ValueError(f"Expected LINESTRING, got {type(geom).__name__}")
            return geom
        except Exception as e:
            raise ValueError(f"Invalid WKT: {e}")
    
    def get_feature_width(self, feature: FeatureInput) -> float:
        """Get display width for feature based on priority"""
        return FEATURE_WIDTHS[feature.priority]
    
    def get_feature_buffer(self, feature: FeatureInput, buffer_scale: float = 1.0) -> LineString:
        """
        Create buffer around feature based on its display width
        
        Args:
            feature: Input feature with WKT and priority
            buffer_scale: Scale factor for buffer (default: 1.0)
            
        Returns:
            Buffered polygon geometry
        """
        line = self.parse_wkt(feature.wkt)
        width = self.get_feature_width(feature)
        # Buffer by half-width on each side
        buffer_distance = (width / 2.0) * buffer_scale
        return line.buffer(buffer_distance, cap_style=2, join_style=2)  # Flat caps, mitered joins
    
    def calculate_minimum_distance(self, geom1: LineString, geom2: LineString) -> float:
        """
        Calculate minimum distance between two geometries
        
        Args:
            geom1: First geometry
            geom2: Second geometry
            
        Returns:
            Minimum distance in points
        """
        return geom1.distance(geom2)
    
    def check_buffer_overlap(self, 
                            feature1: FeatureInput, 
                            feature2: FeatureInput) -> Tuple[bool, float, Optional[object]]:
        """
        Check if feature buffers overlap (PRIMARY DETECTION METHOD)
        
        Args:
            feature1: First feature
            feature2: Second feature
            
        Returns:
            Tuple of (has_conflict, overlap_area, intersection_geometry)
        """
        buffer1 = self.get_feature_buffer(feature1)
        buffer2 = self.get_feature_buffer(feature2)
        
        if buffer1.intersects(buffer2):
            intersection = buffer1.intersection(buffer2)
            overlap_area = intersection.area
            
            # In strict mode, report ANY overlap
            if self.strict_mode:
                return (True, overlap_area, intersection)
            # Otherwise, check against minimum clearance
            elif overlap_area > self.epsilon:
                return (True, overlap_area, intersection)
        
        return (False, 0.0, None)
    
    def check_centerline_proximity(self, 
                                   feature1: FeatureInput, 
                                   feature2: FeatureInput) -> Tuple[bool, float, Point]:
        """
        Check if centerlines are too close to each other
        
        Args:
            feature1: First feature
            feature2: Second feature
            
        Returns:
            Tuple of (has_conflict, min_distance, closest_point)
        """
        line1 = self.parse_wkt(feature1.wkt)
        line2 = self.parse_wkt(feature2.wkt)
        
        min_distance = self.calculate_minimum_distance(line1, line2)
        
        # Calculate required clearance (sum of half-widths + min_clearance)
        width1 = self.get_feature_width(feature1)
        width2 = self.get_feature_width(feature2)
        required_clearance = (width1 / 2.0) + (width2 / 2.0) + self.min_clearance
        
        # Get closest points
        p1, p2 = nearest_points(line1, line2)
        
        if min_distance < required_clearance:
            return (True, min_distance, p1)
        
        return (False, min_distance, None)
    
    def check_crossing_conflict(self, 
                               feature1: FeatureInput, 
                               feature2: FeatureInput) -> Tuple[bool, List[Point]]:
        """
        Check if lines cross each other
        
        Args:
            feature1: First feature
            feature2: Second feature
            
        Returns:
            Tuple of (has_conflict, list_of_crossing_points)
        """
        line1 = self.parse_wkt(feature1.wkt)
        line2 = self.parse_wkt(feature2.wkt)
        
        if line1.crosses(line2):
            intersection = line1.intersection(line2)
            crossing_points = []
            
            if isinstance(intersection, Point):
                crossing_points = [intersection]
            elif isinstance(intersection, MultiPoint):
                crossing_points = list(intersection.geoms)
            
            return (True, crossing_points)
        
        return (False, [])
    
    def check_parallel_conflict(self, 
                               feature1: FeatureInput, 
                               feature2: FeatureInput,
                               angle_threshold: float = 15.0) -> Tuple[bool, float, float]:
        """
        Check if lines are parallel and too close
        
        Args:
            feature1: First feature
            feature2: Second feature
            angle_threshold: Maximum angle difference to consider parallel (degrees)
            
        Returns:
            Tuple of (has_conflict, angle_difference, parallel_distance)
        """
        line1 = self.parse_wkt(feature1.wkt)
        line2 = self.parse_wkt(feature2.wkt)
        
        # Get line orientations
        coords1 = list(line1.coords)
        coords2 = list(line2.coords)
        
        if len(coords1) < 2 or len(coords2) < 2:
            return (False, 0.0, 0.0)
        
        # Calculate average orientation for each line
        def get_orientation(coords):
            dx = coords[-1][0] - coords[0][0]
            dy = coords[-1][1] - coords[0][1]
            return np.degrees(np.arctan2(dy, dx))
        
        angle1 = get_orientation(coords1)
        angle2 = get_orientation(coords2)
        
        # Calculate angle difference (normalized to 0-90 degrees)
        angle_diff = abs(angle1 - angle2)
        angle_diff = min(angle_diff, 180 - angle_diff)  # Handle reflex angles
        
        # Check if parallel
        if angle_diff <= angle_threshold:
            # Calculate perpendicular distance between parallel lines
            min_distance = self.calculate_minimum_distance(line1, line2)
            
            # Check against required clearance
            width1 = self.get_feature_width(feature1)
            width2 = self.get_feature_width(feature2)
            required_clearance = (width1 / 2.0) + (width2 / 2.0) + self.min_clearance
            
            if min_distance < required_clearance:
                return (True, angle_diff, min_distance)
        
        return (False, angle_diff, 0.0)
    
    def check_endpoint_conflict(self, 
                               feature1: FeatureInput, 
                               feature2: FeatureInput) -> Tuple[bool, List[Tuple[Point, Point, float]]]:
        """
        Check if endpoints are too close to each other or to opposite lines
        
        Args:
            feature1: First feature
            feature2: Second feature
            
        Returns:
            Tuple of (has_conflict, list_of_close_endpoint_pairs)
        """
        line1 = self.parse_wkt(feature1.wkt)
        line2 = self.parse_wkt(feature2.wkt)
        
        conflicts = []
        
        # Get endpoints
        endpoints1 = [Point(line1.coords[0]), Point(line1.coords[-1])]
        endpoints2 = [Point(line2.coords[0]), Point(line2.coords[-1])]
        
        # Calculate required clearance
        width1 = self.get_feature_width(feature1)
        width2 = self.get_feature_width(feature2)
        required_clearance = max(width1, width2) / 2.0 + self.min_clearance
        
        # Check endpoint-to-endpoint distances
        for ep1 in endpoints1:
            for ep2 in endpoints2:
                dist = ep1.distance(ep2)
                if dist < required_clearance:
                    conflicts.append((ep1, ep2, dist))
            
            # Check endpoint-to-line distances
            dist_to_line = ep1.distance(line2)
            if dist_to_line < required_clearance:
                nearest_pt = nearest_points(ep1, line2)[1]
                conflicts.append((ep1, nearest_pt, dist_to_line))
        
        # Check feature2 endpoints to feature1 line
        for ep2 in endpoints2:
            dist_to_line = ep2.distance(line1)
            if dist_to_line < required_clearance:
                nearest_pt = nearest_points(ep2, line1)[1]
                conflicts.append((ep2, nearest_pt, dist_to_line))
        
        has_conflict = len(conflicts) > 0
        return (has_conflict, conflicts)
    
    def detect_all_conflicts(self, 
                           feature1: FeatureInput, 
                           feature2: FeatureInput) -> Dict:
        """
        Run ALL conflict detection methods on a feature pair
        NO MERCY: Reports everything
        
        Args:
            feature1: First feature
            feature2: Second feature
            
        Returns:
            Dictionary with all conflict information
        """
        conflicts = {
            "feature_pair": (feature1.id, feature2.id),
            "feature_priorities": (feature1.priority.value, feature2.priority.value),
            "feature_widths": (self.get_feature_width(feature1), self.get_feature_width(feature2)),
            "conflicts_detected": [],
            "has_any_conflict": False,
            "severity_score": 0.0
        }
        
        # 1. Buffer Overlap Check (PRIMARY)
        buffer_conflict, overlap_area, intersection = self.check_buffer_overlap(feature1, feature2)
        if buffer_conflict:
            conflicts["conflicts_detected"].append({
                "type": ConflictType.BUFFER_OVERLAP,
                "overlap_area": overlap_area,
                "intersection_area": overlap_area,
                "severity": "HIGH"
            })
            conflicts["has_any_conflict"] = True
            conflicts["severity_score"] += overlap_area
        
        # 2. Centerline Proximity Check
        proximity_conflict, min_dist, closest_pt = self.check_centerline_proximity(feature1, feature2)
        if proximity_conflict:
            conflicts["conflicts_detected"].append({
                "type": ConflictType.CENTERLINE_PROXIMITY,
                "minimum_distance": min_dist,
                "closest_point": (closest_pt.x, closest_pt.y) if closest_pt else None,
                "severity": "MEDIUM"
            })
            conflicts["has_any_conflict"] = True
            conflicts["severity_score"] += (10.0 / (min_dist + self.epsilon))
        
        # 3. Crossing Check
        crossing_conflict, crossing_points = self.check_crossing_conflict(feature1, feature2)
        if crossing_conflict:
            conflicts["conflicts_detected"].append({
                "type": ConflictType.CROSSING_CONFLICT,
                "crossing_points": [(pt.x, pt.y) for pt in crossing_points],
                "num_crossings": len(crossing_points),
                "severity": "CRITICAL"
            })
            conflicts["has_any_conflict"] = True
            conflicts["severity_score"] += len(crossing_points) * 20.0
        
        # 4. Parallel Conflict Check
        parallel_conflict, angle_diff, parallel_dist = self.check_parallel_conflict(feature1, feature2)
        if parallel_conflict:
            conflicts["conflicts_detected"].append({
                "type": ConflictType.PARALLEL_CONFLICT,
                "angle_difference": angle_diff,
                "parallel_distance": parallel_dist,
                "severity": "HIGH"
            })
            conflicts["has_any_conflict"] = True
            conflicts["severity_score"] += (5.0 / (parallel_dist + self.epsilon))
        
        # 5. Endpoint Conflict Check
        endpoint_conflict, endpoint_pairs = self.check_endpoint_conflict(feature1, feature2)
        if endpoint_conflict:
            conflicts["conflicts_detected"].append({
                "type": ConflictType.ENDPOINT_CONFLICT,
                "num_endpoint_conflicts": len(endpoint_pairs),
                "endpoint_distances": [dist for _, _, dist in endpoint_pairs],
                "severity": "MEDIUM"
            })
            conflicts["has_any_conflict"] = True
            conflicts["severity_score"] += len(endpoint_pairs) * 5.0
        
        return conflicts
    
    def detect_overlaps(self, features: List[FeatureInput]) -> List[Dict]:
        """
        Detect ALL overlaps between ALL feature pairs
        NO MERCY MODE: Reports everything
        
        Args:
            features: List of input features
            
        Returns:
            List of conflict dictionaries for ALL conflicting pairs
        """
        all_conflicts = []
        n = len(features)
        
        print(f"\n{'='*80}")
        print(f"🔍 PRECISION OVERLAP DETECTION - NO MERCY MODE")
        print(f"{'='*80}")
        print(f"📊 Total features to analyze: {n}")
        print(f"🔢 Total pairs to check: {n * (n - 1) // 2}")
        print(f"⚙️  Minimum clearance: {self.min_clearance} points")
        print(f"🎯 Strict mode: {self.strict_mode}")
        print(f"{'='*80}\n")
        
        pair_count = 0
        conflict_count = 0
        
        # Check all pairs - NO EXCEPTIONS
        for i in range(n):
            for j in range(i + 1, n):
                pair_count += 1
                feature1 = features[i]
                feature2 = features[j]
                
                # Run full conflict analysis
                conflict_result = self.detect_all_conflicts(feature1, feature2)
                
                if conflict_result["has_any_conflict"]:
                    conflict_count += 1
                    all_conflicts.append(conflict_result)
                    
                    # Print conflict report
                    print(f"⚠️  CONFLICT #{conflict_count} (Pair {pair_count}/{n*(n-1)//2})")
                    print(f"   Features: {feature1.id} vs {feature2.id}")
                    print(f"   Priorities: {feature1.priority.value} vs {feature2.priority.value}")
                    print(f"   Severity Score: {conflict_result['severity_score']:.2f}")
                    print(f"   Conflict Types:")
                    for conflict in conflict_result["conflicts_detected"]:
                        print(f"      • {conflict['type']} - {conflict['severity']}")
                    print()
        
        print(f"{'='*80}")
        print(f"📈 DETECTION SUMMARY")
        print(f"{'='*80}")
        print(f"✅ Pairs analyzed: {pair_count}")
        print(f"⚠️  Conflicts found: {conflict_count}")
        print(f"📊 Conflict rate: {(conflict_count/pair_count*100):.1f}%")
        print(f"{'='*80}\n")
        
        return all_conflicts

    def calculate_displacement_distance(self, feature1, feature2, overlap_area):
        """
        Calculate the displacement distance needed to resolve overlap.
        
        Args:
            feature1: First feature in conflict
            feature2: Second feature in conflict
            overlap_area: Area of overlap between features
            
        Returns:
            float: Displacement distance in points
        """
        # Get feature widths from FEATURE_WIDTHS constant
        width1 = FEATURE_WIDTHS.get(feature1.priority, 4.0)
        width2 = FEATURE_WIDTHS.get(feature2.priority, 4.0)
        
        # Calculate required separation distance
        required_separation = (width1/2.0) + (width2/2.0) + self.min_clearance
        
        # Calculate displacement needed based on overlap area
        displacement_needed = np.sqrt(overlap_area) + self.min_clearance
        
        return displacement_needed
    
    def get_priority_order(self, features):
        """
        Get list of feature indices sorted by priority order.
        Higher priority features (P1_HIGHWAY) come first.
        
        Args:
            features: List of Feature objects
            
        Returns:
            list: Indices of features sorted by priority
        """
        # Priority values: P1_HIGHWAY = 1 (highest), P2_ROAD = 2
        priority_values = {
            FeaturePriority.P1_HIGHWAY: 1,
            FeaturePriority.P2_ROAD: 2
        }
        
        # Create list of (index, priority_value) tuples
        indexed_features = [
            (i, priority_values.get(f.priority, 999)) 
            for i, f in enumerate(features)
        ]
        
        # Sort by priority value (lower number = higher priority)
        indexed_features.sort(key=lambda x: x[1])
        
        # Return just the indices
        return [i for i, _ in indexed_features]

    def get_conflict_priority(self, overlap: Dict) -> str:
        """
        Determine which feature should be displaced in a conflict.
        Lower priority features (P2_ROAD) should move, higher priority (P1_HIGHWAY) stays.
        
        Args:
            overlap: Conflict dictionary with feature_pair and feature_priorities
            
        Returns:
            str: ID of the feature that should be displaced
        """
        feature_ids = overlap["feature_pair"]
        priorities = overlap["feature_priorities"]
        
        # Priority format: "P1_HIGHWAY" or "P2_ROAD"
        # P1 (highway) has higher priority, P2 (road) has lower priority
        # Lower priority feature should be displaced
        
        # Extract priority numbers (P1 -> 1, P2 -> 2)
        priority1 = int(priorities[0].split('_')[0][1])  # "P1_HIGHWAY" -> 1
        priority2 = int(priorities[1].split('_')[0][1])  # "P2_ROAD" -> 2
        
        # Lower priority number means HIGHER importance
        # So feature with HIGHER priority number should be displaced
        if priority1 < priority2:
            # Feature 1 has higher priority, displace feature 2
            return feature_ids[1]
        elif priority2 < priority1:
            # Feature 2 has higher priority, displace feature 1
            return feature_ids[0]
        else:
            # Same priority - displace the second feature by default
            return feature_ids[1]

