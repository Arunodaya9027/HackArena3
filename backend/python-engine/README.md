# Python Geometry Engine

FastAPI microservice for geometry conflict resolution in GeoClear AI.

## Features

- **Overlap Detection**: Detects overlaps between feature buffers using Shapely
- **Force-Directed Displacement**: Calculates repulsion-based displacement vectors
- **Topology Preservation**: Maintains junction connectivity after displacement
- **3D Depth Metadata**: Assigns Z-index and visual depth flags

## Installation

```bash
cd python-geometry-engine
pip install -r requirements.txt
```

## Running the Service

```bash
python run.py
```

The service will start on `http://localhost:8001`

- API Docs: http://localhost:8001/docs
- Health Check: http://localhost:8001/health

## Architecture

```
app/
├── models/           # Pydantic data models
│   └── geometry_models.py
├── services/         # Core geometry processing
│   ├── precision_overlap_detector.py  # NO MERCY precision detection
│   ├── displacement_calculator.py
│   ├── topology_validator.py
│   └── geometry_engine.py
├── utils/            # Utilities
│   └── wkt_analyzer.py
└── main.py          # FastAPI application
```

## API Endpoints

### POST /api/geometry/process

Process geometry features and resolve conflicts.

**Request:**
```json
{
  "features": [
    {
      "id": "highway_001",
      "wkt": "LINESTRING(7071.42 8585.63, 7074.67 8588.81)",
      "priority": "P1_HIGHWAY"
    },
    {
      "id": "road_001",
      "wkt": "LINESTRING(7071.50 8585.70, 7074.70 8588.85)",
      "priority": "P2_ROAD"
    }
  ],
  "min_clearance": 2.0
}
```

**Response:**
```json
{
  "results": [...],
  "total_conflicts": 1,
  "total_displaced": 1,
  "processing_summary": {...}
}
```

## Analyzing WKT Data

```bash
python -m app.utils.wkt_analyzer path/to/file.wkt
```

## Constants

- **Highway (P1)**: Width 5pt
- **Road (P2)**: Width 3pt
- **Min Clearance**: 2pt (configurable)
