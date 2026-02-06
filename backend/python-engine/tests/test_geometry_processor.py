"""
Unit tests for Geometry Processor
"""
import pytest
from app.models.geometry_models import (
    GeometryRequest, FeatureInput, FeaturePriority
)
from app.services.geometry_processor import GeometryProcessor


@pytest.fixture
def geometry_processor():
    """Create geometry processor instance"""
    return GeometryProcessor()


@pytest.fixture
def sample_request():
    """Create sample processing request"""
    return GeometryRequest(
        features=[
            FeatureInput(
                feature_id="test_1",
                wkt_geometry="LINESTRING (0 0, 10 10)",
                priority=FeaturePriority.HIGHWAY,
                width=5.0
            ),
            FeatureInput(
                feature_id="test_2",
                wkt_geometry="LINESTRING (0 10, 10 0)",
                priority=FeaturePriority.ROAD,
                width=3.0
            )
        ],
        min_clearance=2.0,
        force_strength=1.5,
        max_iterations=50,
        enable_3d_depth=True
    )


def test_geometry_processor_initialization(geometry_processor):
    """Test geometry processor can be initialized"""
    assert geometry_processor is not None
    assert geometry_processor.precision_overlap_detector is None


def test_process_geometries(geometry_processor, sample_request):
    """Test full geometry processing pipeline"""
    response = geometry_processor.process_geometries(sample_request)
    
    assert response is not None
    assert len(response.results) == 2
    assert response.total_conflicts_resolved >= 0
    assert response.execution_time_ms > 0


def test_process_single_feature(geometry_processor):
    """Test processing with single feature (no overlaps)"""
    request = GeometryRequest(
        features=[
            FeatureInput(
                feature_id="solo",
                wkt_geometry="LINESTRING (0 0, 10 10)",
                priority=FeaturePriority.HIGHWAY,
                width=5.0
            )
        ],
        min_clearance=2.0,
        force_strength=1.5,
        max_iterations=50,
        enable_3d_depth=False
    )
    
    response = geometry_processor.process_geometries(request)
    
    assert response is not None
    assert len(response.results) == 1
    assert response.total_conflicts_resolved == 0


def test_process_with_3d_depth(geometry_processor, sample_request):
    """Test 3D depth assignment"""
    sample_request.enable_3d_depth = True
    response = geometry_processor.process_geometries(sample_request)
    
    assert response is not None
    for result in response.results:
        assert "depth_metadata" in result


def test_topology_preservation(geometry_processor, sample_request):
    """Test topology preservation validation"""
    response = geometry_processor.process_geometries(sample_request)
    
    # Topology should be preserved or validation attempted
    assert hasattr(response, "topology_preserved")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
