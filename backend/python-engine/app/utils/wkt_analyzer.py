"""
WKT Data Analyzer
Analyzes the street network WKT data
"""
import sys
from pathlib import Path
from typing import List, Dict, Tuple
from shapely.geometry import LineString
from shapely import wkt as shapely_wkt
import json


class WKTAnalyzer:
    """Analyzes WKT LINESTRING data"""
    
    def __init__(self, wkt_file_path: str):
        """Initialize with WKT file path"""
        self.wkt_file_path = Path(wkt_file_path)
        self.linestrings: List[LineString] = []
        self.raw_lines: List[str] = []
    
    def load_wkt_file(self):
        """Load and parse WKT file"""
        with open(self.wkt_file_path, 'r') as f:
            self.raw_lines = [line.strip() for line in f.readlines() if line.strip()]
        
        print(f"Loaded {len(self.raw_lines)} lines from {self.wkt_file_path}")
        
        # Parse WKT strings
        for i, line in enumerate(self.raw_lines):
            try:
                geom = shapely_wkt.loads(line)
                if isinstance(geom, LineString):
                    self.linestrings.append(geom)
            except Exception as e:
                print(f"Warning: Could not parse line {i+1}: {e}")
    
    def analyze_network(self) -> Dict:
        """Comprehensive network analysis"""
        if not self.linestrings:
            return {}
        
        # Basic statistics
        total_features = len(self.linestrings)
        
        # Coordinate analysis
        all_x, all_y = [], []
        total_length = 0
        segment_counts = []
        
        for line in self.linestrings:
            coords = list(line.coords)
            segment_counts.append(len(coords))
            total_length += line.length
            
            for x, y in coords:
                all_x.append(x)
                all_y.append(y)
        
        # Bounding box
        min_x, max_x = min(all_x), max(all_x)
        min_y, max_y = min(all_y), max(all_y)
        
        # Junction detection (endpoints)
        endpoints = []
        for line in self.linestrings:
            coords = list(line.coords)
            endpoints.append(coords[0])
            endpoints.append(coords[-1])
        
        # Count unique endpoints vs total (junction detection)
        unique_endpoints = len(set(endpoints))
        total_endpoints = len(endpoints)
        potential_junctions = total_endpoints - unique_endpoints
        
        analysis = {
            "file": str(self.wkt_file_path),
            "total_features": total_features,
            "total_coordinate_points": len(all_x),
            "bounding_box": {
                "min_x": round(min_x, 2),
                "max_x": round(max_x, 2),
                "min_y": round(min_y, 2),
                "max_y": round(max_y, 2),
                "width": round(max_x - min_x, 2),
                "height": round(max_y - min_y, 2)
            },
            "network_statistics": {
                "total_network_length": round(total_length, 2),
                "average_feature_length": round(total_length / total_features, 2),
                "min_segments_per_feature": min(segment_counts),
                "max_segments_per_feature": max(segment_counts),
                "avg_segments_per_feature": round(sum(segment_counts) / len(segment_counts), 2)
            },
            "topology": {
                "total_endpoints": total_endpoints,
                "unique_endpoints": unique_endpoints,
                "potential_junctions": potential_junctions,
                "connectivity_ratio": round(potential_junctions / total_endpoints, 2)
            }
        }
        
        return analysis
    
    def detect_potential_overlaps(self, buffer_distance: float = 2.5) -> List[Tuple[int, int]]:
        """
        Detect potential overlaps using simple buffer analysis
        
        Args:
            buffer_distance: Buffer distance for overlap detection
            
        Returns:
            List of tuples (index1, index2) of potentially overlapping features
        """
        potential_overlaps = []
        n = len(self.linestrings)
        
        print(f"\nChecking for potential overlaps (buffer={buffer_distance})...")
        
        for i in range(n):
            buffer_i = self.linestrings[i].buffer(buffer_distance)
            for j in range(i + 1, n):
                if buffer_i.intersects(self.linestrings[j]):
                    potential_overlaps.append((i, j))
        
        return potential_overlaps
    
    def print_analysis(self):
        """Print formatted analysis"""
        analysis = self.analyze_network()
        
        print("\n" + "="*70)
        print("WKT STREET NETWORK ANALYSIS")
        print("="*70)
        
        print(f"\n📁 File: {analysis['file']}")
        print(f"📊 Total Features: {analysis['total_features']}")
        print(f"📍 Total Coordinate Points: {analysis['total_coordinate_points']}")
        
        print("\n🗺️  BOUNDING BOX:")
        bb = analysis['bounding_box']
        print(f"   X Range: {bb['min_x']} to {bb['max_x']} (width: {bb['width']})")
        print(f"   Y Range: {bb['min_y']} to {bb['max_y']} (height: {bb['height']})")
        
        print("\n📏 NETWORK STATISTICS:")
        ns = analysis['network_statistics']
        print(f"   Total Network Length: {ns['total_network_length']}")
        print(f"   Average Feature Length: {ns['average_feature_length']}")
        print(f"   Segments per Feature: {ns['min_segments_per_feature']} to {ns['max_segments_per_feature']} (avg: {ns['avg_segments_per_feature']})")
        
        print("\n🔗 TOPOLOGY:")
        topo = analysis['topology']
        print(f"   Total Endpoints: {topo['total_endpoints']}")
        print(f"   Unique Endpoints: {topo['unique_endpoints']}")
        print(f"   Potential Junctions: {topo['potential_junctions']}")
        print(f"   Connectivity Ratio: {topo['connectivity_ratio']}")
        
        # Detect overlaps
        overlaps = self.detect_potential_overlaps(buffer_distance=2.5)
        print(f"\n⚠️  POTENTIAL OVERLAPS (buffer=2.5): {len(overlaps)}")
        
        if overlaps:
            print(f"   First 10 overlap pairs:")
            for i, (idx1, idx2) in enumerate(overlaps[:10]):
                print(f"      {i+1}. Feature {idx1} overlaps with Feature {idx2}")
        
        print("\n" + "="*70)
        
        return analysis


def main():
    """Main analysis function"""
    # Default WKT file path
    wkt_file = Path(__file__).parent.parent.parent.parent / "docs" / "Problem 3 - streets_ugen.wkt"
    
    if len(sys.argv) > 1:
        wkt_file = Path(sys.argv[1])
    
    if not wkt_file.exists():
        print(f"Error: WKT file not found: {wkt_file}")
        return
    
    # Analyze
    analyzer = WKTAnalyzer(str(wkt_file))
    analyzer.load_wkt_file()
    analysis = analyzer.print_analysis()
    
    # Save to JSON
    output_file = wkt_file.parent / "wkt_analysis.json"
    with open(output_file, 'w') as f:
        json.dump(analysis, f, indent=2)
    
    print(f"\n✅ Analysis saved to: {output_file}")


if __name__ == "__main__":
    main()
