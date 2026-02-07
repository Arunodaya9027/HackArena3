"""
Metrics Tracker - Comprehensive reporting for hackathon requirements
Tracks: Total Overlaps Detected vs. Total Overlaps Resolved
"""
from typing import Dict, List
from dataclasses import dataclass, field
import time


@dataclass
class ProcessingMetrics:
    """Comprehensive metrics for displacement processing"""
    
    # Core hackathon metrics
    total_overlaps_detected: int = 0
    total_overlaps_resolved: int = 0
    success_rate_percent: float = 0.0
    
    # Feature statistics
    total_features: int = 0
    features_displaced: int = 0
    features_unchanged: int = 0
    
    # Displacement statistics
    total_displacement_distance: float = 0.0
    average_displacement: float = 0.0
    max_displacement: float = 0.0
    min_displacement: float = float('inf')
    
    # Topology metrics
    junctions_detected: int = 0
    junctions_preserved: int = 0
    topology_breaks: int = 0
    connectivity_intact: bool = True
    
    # 3D/Depth metrics
    features_with_z_index: int = 0
    shadows_cast: int = 0
    leader_lines_generated: int = 0
    
    # Performance metrics
    processing_time_ms: float = 0.0
    detection_time_ms: float = 0.0
    displacement_time_ms: float = 0.0
    validation_time_ms: float = 0.0
    
    # Detailed breakdowns
    conflicts_by_severity: Dict[str, int] = field(default_factory=dict)
    conflicts_by_type: Dict[str, int] = field(default_factory=dict)
    displacement_by_priority: Dict[str, float] = field(default_factory=dict)


class MetricsTracker:
    """Track and calculate processing metrics"""
    
    def __init__(self):
        self.metrics = ProcessingMetrics()
        self.start_time = None
        self.phase_timings = {}
        
    def start_tracking(self):
        """Start overall tracking"""
        self.start_time = time.time()
        
    def start_phase(self, phase_name: str):
        """Start tracking a specific phase"""
        self.phase_timings[phase_name] = {'start': time.time()}
        
    def end_phase(self, phase_name: str):
        """End tracking a specific phase"""
        if phase_name in self.phase_timings:
            elapsed = (time.time() - self.phase_timings[phase_name]['start']) * 1000
            self.phase_timings[phase_name]['duration_ms'] = elapsed
            return elapsed
        return 0.0
    
    def record_overlaps_detected(self, overlap_count: int, overlaps: List[Dict]):
        """Record detected overlaps"""
        self.metrics.total_overlaps_detected = overlap_count
        
        # Break down by severity
        for overlap in overlaps:
            for conflict in overlap.get('conflicts_detected', []):
                severity = conflict.get('severity', 'UNKNOWN')
                self.metrics.conflicts_by_severity[severity] = \
                    self.metrics.conflicts_by_severity.get(severity, 0) + 1
                
                conflict_type = conflict.get('type', 'UNKNOWN')
                self.metrics.conflicts_by_type[conflict_type] = \
                    self.metrics.conflicts_by_type.get(conflict_type, 0) + 1
    
    def record_displacement(self, feature_id: str, priority: str, 
                          displacement_distance: float, was_displaced: bool):
        """Record displacement for a feature"""
        if was_displaced:
            self.metrics.features_displaced += 1
            self.metrics.total_displacement_distance += displacement_distance
            self.metrics.max_displacement = max(
                self.metrics.max_displacement, displacement_distance
            )
            self.metrics.min_displacement = min(
                self.metrics.min_displacement, displacement_distance
            )
            
            # Track by priority
            if priority not in self.metrics.displacement_by_priority:
                self.metrics.displacement_by_priority[priority] = 0.0
            self.metrics.displacement_by_priority[priority] += displacement_distance
        else:
            self.metrics.features_unchanged += 1
    
    def record_overlaps_resolved(self, resolved_count: int):
        """Record successfully resolved overlaps"""
        self.metrics.total_overlaps_resolved = resolved_count
        
        # Calculate success rate
        if self.metrics.total_overlaps_detected > 0:
            self.metrics.success_rate_percent = round(
                (resolved_count / self.metrics.total_overlaps_detected) * 100.0, 2
            )
    
    def record_topology_metrics(self, junctions_detected: int, 
                                junctions_preserved: int, topology_breaks: int):
        """Record topology preservation metrics"""
        self.metrics.junctions_detected = junctions_detected
        self.metrics.junctions_preserved = junctions_preserved
        self.metrics.topology_breaks = topology_breaks
        self.metrics.connectivity_intact = (topology_breaks == 0)
    
    def record_3d_features(self, z_index_count: int, shadows_count: int, 
                          leader_lines_count: int):
        """Record 3D/depth feature metrics"""
        self.metrics.features_with_z_index = z_index_count
        self.metrics.shadows_cast = shadows_count
        self.metrics.leader_lines_generated = leader_lines_count
    
    def finalize_metrics(self, total_features: int):
        """Calculate final metrics"""
        self.metrics.total_features = total_features
        
        # Calculate average displacement
        if self.metrics.features_displaced > 0:
            self.metrics.average_displacement = round(
                self.metrics.total_displacement_distance / self.metrics.features_displaced, 2
            )
        
        # Record timing
        if self.start_time:
            self.metrics.processing_time_ms = round(
                (time.time() - self.start_time) * 1000, 2
            )
        
        # Record phase timings
        self.metrics.detection_time_ms = self.phase_timings.get(
            'detection', {}
        ).get('duration_ms', 0.0)
        self.metrics.displacement_time_ms = self.phase_timings.get(
            'displacement', {}
        ).get('duration_ms', 0.0)
        self.metrics.validation_time_ms = self.phase_timings.get(
            'validation', {}
        ).get('duration_ms', 0.0)
        
        # Fix min_displacement if no displacements occurred
        if self.metrics.features_displaced == 0:
            self.metrics.min_displacement = 0.0
        
        return self.metrics
    
    def get_summary_dict(self) -> Dict:
        """Get metrics as dictionary for JSON response"""
        return {
            "core_metrics": {
                "total_overlaps_detected": self.metrics.total_overlaps_detected,
                "total_overlaps_resolved": self.metrics.total_overlaps_resolved,
                "success_rate_percent": self.metrics.success_rate_percent,
                "processing_time_ms": self.metrics.processing_time_ms
            },
            "feature_statistics": {
                "total_features": self.metrics.total_features,
                "features_displaced": self.metrics.features_displaced,
                "features_unchanged": self.metrics.features_unchanged
            },
            "displacement_statistics": {
                "total_displacement_distance": round(
                    self.metrics.total_displacement_distance, 2
                ),
                "average_displacement": self.metrics.average_displacement,
                "max_displacement": round(self.metrics.max_displacement, 2),
                "min_displacement": round(self.metrics.min_displacement, 2),
                "displacement_by_priority": {
                    k: round(v, 2) 
                    for k, v in self.metrics.displacement_by_priority.items()
                }
            },
            "topology_metrics": {
                "junctions_detected": self.metrics.junctions_detected,
                "junctions_preserved": self.metrics.junctions_preserved,
                "topology_breaks": self.metrics.topology_breaks,
                "connectivity_intact": self.metrics.connectivity_intact
            },
            "3d_features": {
                "features_with_z_index": self.metrics.features_with_z_index,
                "shadows_cast": self.metrics.shadows_cast,
                "leader_lines_generated": self.metrics.leader_lines_generated
            },
            "performance_breakdown": {
                "detection_time_ms": round(self.metrics.detection_time_ms, 2),
                "displacement_time_ms": round(self.metrics.displacement_time_ms, 2),
                "validation_time_ms": round(self.metrics.validation_time_ms, 2)
            },
            "conflict_breakdown": {
                "by_severity": self.metrics.conflicts_by_severity,
                "by_type": self.metrics.conflicts_by_type
            }
        }
    
    def get_hackathon_report(self) -> str:
        """Generate hackathon-friendly text report"""
        report = []
        report.append("=" * 60)
        report.append("GEOCLEAR AI - HACKATHON METRICS REPORT")
        report.append("=" * 60)
        report.append("")
        
        report.append("📊 CORE METRICS (Hackathon Requirements):")
        report.append("-" * 60)
        report.append(f"Total Overlaps Detected:  {self.metrics.total_overlaps_detected}")
        report.append(f"Total Overlaps Resolved:  {self.metrics.total_overlaps_resolved}")
        report.append(f"Success Rate:             {self.metrics.success_rate_percent}%")
        report.append(f"Processing Time:          {self.metrics.processing_time_ms:.2f}ms")
        report.append("")
        
        report.append("📍 FEATURE STATISTICS:")
        report.append("-" * 60)
        report.append(f"Total Features Processed: {self.metrics.total_features}")
        report.append(f"Features Displaced:       {self.metrics.features_displaced}")
        report.append(f"Features Unchanged:       {self.metrics.features_unchanged}")
        report.append("")
        
        report.append("📏 DISPLACEMENT STATISTICS:")
        report.append("-" * 60)
        report.append(f"Average Displacement:     {self.metrics.average_displacement:.2f}pt")
        report.append(f"Maximum Displacement:     {self.metrics.max_displacement:.2f}pt")
        report.append(f"Minimum Displacement:     {self.metrics.min_displacement:.2f}pt")
        report.append(f"Total Distance Moved:     {self.metrics.total_displacement_distance:.2f}pt")
        report.append("")
        
        report.append("🔗 TOPOLOGY PRESERVATION:")
        report.append("-" * 60)
        report.append(f"Junctions Detected:       {self.metrics.junctions_detected}")
        report.append(f"Junctions Preserved:      {self.metrics.junctions_preserved}")
        report.append(f"Topology Breaks:          {self.metrics.topology_breaks}")
        report.append(f"Network Connectivity:     {'✅ INTACT' if self.metrics.connectivity_intact else '❌ BROKEN'}")
        report.append("")
        
        if self.metrics.features_with_z_index > 0:
            report.append("🎮 3D FEATURES:")
            report.append("-" * 60)
            report.append(f"Features with Z-Index:    {self.metrics.features_with_z_index}")
            report.append(f"Shadows Cast:             {self.metrics.shadows_cast}")
            report.append(f"Leader Lines:             {self.metrics.leader_lines_generated}")
            report.append("")
        
        report.append("=" * 60)
        report.append("✅ Processing Complete")
        report.append("=" * 60)
        
        return "\n".join(report)
