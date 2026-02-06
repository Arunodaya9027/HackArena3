"""
Test script for Precision Overlap Detection
Demonstrates NO MERCY conflict detection with real WKT data
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.models.geometry_models import FeatureInput, FeaturePriority
from app.services.precision_overlap_detector import PrecisionOverlapDetector


def test_precision_detection():
    """Test precision overlap detection with sample features"""
    
    print("\n" + "="*80)
    print("🧪 TESTING PRECISION OVERLAP DETECTION - NO MERCY MODE")
    print("="*80 + "\n")
    
    # Create test features with known overlaps
    features = [
        # Highway 1 - horizontal
        FeatureInput(
            id="highway_001",
            wkt="LINESTRING(0 0, 100 0)",
            priority=FeaturePriority.P1_HIGHWAY
        ),
        # Road 1 - nearly parallel to highway_001
        FeatureInput(
            id="road_001",
            wkt="LINESTRING(0 2, 100 2)",
            priority=FeaturePriority.P2_ROAD
        ),
        # Road 2 - crosses highway_001
        FeatureInput(
            id="road_002",
            wkt="LINESTRING(50 -10, 50 10)",
            priority=FeaturePriority.P2_ROAD
        ),
        # Highway 2 - nearly overlaps highway_001
        FeatureInput(
            id="highway_002",
            wkt="LINESTRING(10 1, 90 1)",
            priority=FeaturePriority.P1_HIGHWAY
        ),
        # Road 3 - diagonal, crosses multiple features
        FeatureInput(
            id="road_003",
            wkt="LINESTRING(0 -5, 100 5)",
            priority=FeaturePriority.P2_ROAD
        ),
    ]
    
    print(f"📊 Test Dataset:")
    print(f"   • Total features: {len(features)}")
    for feat in features:
        print(f"   • {feat.id}: {feat.priority.value} (width: {5.0 if feat.priority == FeaturePriority.P1_HIGHWAY else 3.0}pt)")
    print()
    
    # Initialize precision detector
    detector = PrecisionOverlapDetector(min_clearance=2.0, strict_mode=True)
    
    # Run detection
    conflicts = detector.detect_overlaps(features)
    
    # Detailed conflict report
    print("\n" + "="*80)
    print("📋 DETAILED CONFLICT REPORT")
    print("="*80 + "\n")
    
    if not conflicts:
        print("✅ NO CONFLICTS DETECTED (Unexpected!)")
        return
    
    for idx, conflict in enumerate(conflicts, 1):
        print(f"⚠️  CONFLICT #{idx}")
        print(f"{'─'*80}")
        print(f"   Feature Pair: {conflict['feature_pair'][0]} ↔ {conflict['feature_pair'][1]}")
        print(f"   Priorities: {conflict['feature_priorities'][0]} ({conflict['feature_widths'][0]}pt) vs "
              f"{conflict['feature_priorities'][1]} ({conflict['feature_widths'][1]}pt)")
        print(f"   Severity Score: {conflict['severity_score']:.2f}")
        print(f"   \n   Detected Conflicts:")
        
        for conf_detail in conflict["conflicts_detected"]:
            print(f"      🔸 {conf_detail['type']} ({conf_detail['severity']})")
            
            if conf_detail['type'] == 'BUFFER_OVERLAP':
                print(f"         • Overlap Area: {conf_detail['overlap_area']:.4f} sq units")
            
            elif conf_detail['type'] == 'CENTERLINE_PROXIMITY':
                print(f"         • Minimum Distance: {conf_detail['minimum_distance']:.4f} units")
                if conf_detail['closest_point']:
                    print(f"         • Closest Point: ({conf_detail['closest_point'][0]:.2f}, "
                          f"{conf_detail['closest_point'][1]:.2f})")
            
            elif conf_detail['type'] == 'CROSSING_CONFLICT':
                print(f"         • Number of Crossings: {conf_detail['num_crossings']}")
                for i, pt in enumerate(conf_detail['crossing_points'], 1):
                    print(f"         • Crossing Point {i}: ({pt[0]:.2f}, {pt[1]:.2f})")
            
            elif conf_detail['type'] == 'PARALLEL_CONFLICT':
                print(f"         • Angle Difference: {conf_detail['angle_difference']:.2f}°")
                print(f"         • Parallel Distance: {conf_detail['parallel_distance']:.4f} units")
            
            elif conf_detail['type'] == 'ENDPOINT_CONFLICT':
                print(f"         • Endpoint Conflicts: {conf_detail['num_endpoint_conflicts']}")
                print(f"         • Min Distance: {min(conf_detail['endpoint_distances']):.4f} units")
        
        print()
    
    # Summary statistics
    print("="*80)
    print("📊 CONFLICT STATISTICS")
    print("="*80)
    
    conflict_types = {}
    severity_counts = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    
    for conflict in conflicts:
        for conf_detail in conflict["conflicts_detected"]:
            conf_type = conf_detail['type']
            conflict_types[conf_type] = conflict_types.get(conf_type, 0) + 1
            severity_counts[conf_detail['severity']] += 1
    
    print(f"\n🔢 Conflict Type Distribution:")
    for conf_type, count in conflict_types.items():
        print(f"   • {conf_type}: {count}")
    
    print(f"\n⚠️  Severity Distribution:")
    for severity, count in severity_counts.items():
        print(f"   • {severity}: {count}")
    
    print(f"\n📈 Overall Metrics:")
    total_pairs = len(features) * (len(features) - 1) // 2
    print(f"   • Total pairs checked: {total_pairs}")
    print(f"   • Conflicting pairs: {len(conflicts)}")
    print(f"   • Conflict rate: {len(conflicts)/total_pairs*100:.1f}%")
    print(f"   • Total conflict instances: {sum(conflict_types.values())}")
    
    print("\n" + "="*80)
    print("✅ TESTING COMPLETE")
    print("="*80 + "\n")


def test_real_wkt_data():
    """Test with real WKT data from the problem file"""
    
    print("\n" + "="*80)
    print("🧪 TESTING WITH REAL WKT DATA")
    print("="*80 + "\n")
    
    # Sample from actual WKT file (Problem 3)
    real_features = [
        FeatureInput(
            id="street_001",
            wkt="LINESTRING(7071.42 8585.63, 7074.67 8588.81, 7092.86 8606.58)",
            priority=FeaturePriority.P1_HIGHWAY
        ),
        FeatureInput(
            id="street_002",
            wkt="LINESTRING(7074.67 8588.81, 7125.71 8589.01)",
            priority=FeaturePriority.P2_ROAD
        ),
        FeatureInput(
            id="street_003",
            wkt="LINESTRING(7092.86 8606.58, 7093.86 8656.58)",
            priority=FeaturePriority.P1_HIGHWAY
        ),
        FeatureInput(
            id="street_004",
            wkt="LINESTRING(7092.86 8606.58, 7138.1 8605.98)",
            priority=FeaturePriority.P2_ROAD
        ),
    ]
    
    print(f"📊 Real WKT Dataset:")
    print(f"   • Features: {len(real_features)}")
    print(f"   • Source: Problem 3 - streets_ugen.wkt")
    print()
    
    # Initialize detector
    detector = PrecisionOverlapDetector(min_clearance=2.0, strict_mode=True)
    
    # Run detection
    conflicts = detector.detect_overlaps(real_features)
    
    print(f"\n📋 Results: Found {len(conflicts)} conflicting pairs")
    
    if conflicts:
        print(f"\n⚠️  Conflict Summary:")
        for conflict in conflicts:
            print(f"   • {conflict['feature_pair'][0]} ↔ {conflict['feature_pair'][1]}: "
                  f"{len(conflict['conflicts_detected'])} conflict type(s), "
                  f"severity score: {conflict['severity_score']:.2f}")
    else:
        print("✅ No conflicts detected in this sample")
    
    print("\n" + "="*80 + "\n")


if __name__ == "__main__":
    print("\n🌍 GeoClear AI - Precision Overlap Detection Testing")
    print("="*80)
    
    try:
        # Run synthetic test
        test_precision_detection()
        
        # Run real data test
        test_real_wkt_data()
        
        print("\n✅ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
