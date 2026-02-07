#!/usr/bin/env python3"""

"""Startup script for Python Geometry Engine

GeoClear AI - Python Geometry Engine Launcher"""

Quick start script for developmentimport sys

"""from pathlib import Path

import sys

import os# Add app to path

import subprocesssys.path.insert(0, str(Path(__file__).parent))



# Add app directory to Python pathif __name__ == "__main__":

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))    import uvicorn

    from app.main import app

def check_dependencies():    

    """Check if required dependencies are installed"""    print("🚀 Starting GeoClear AI - Python Geometry Engine")

    try:    print("📍 API Documentation: http://localhost:8010/docs")

        import fastapi    print("📍 Health Check: http://localhost:8010/health")

        import shapely    

        import geopandas    uvicorn.run(

        import numpy        app,

        print("✅ All dependencies installed")        host="0.0.0.0",

        return True        port=8010,

    except ImportError as e:        log_level="info",

        print(f"❌ Missing dependency: {e.name}")        reload=True  # Enable auto-reload for development

        print("\nPlease install dependencies:")    )

        print("  pip install -r requirements.txt")
        return False

def main():
    """Main entry point"""
    print("🌍 GeoClear AI - Python Geometry Engine")
    print("=" * 50)
    
    if not check_dependencies():
        sys.exit(1)
    
    print("\n🚀 Starting FastAPI server...")
    print("📡 Server will be available at: http://localhost:8010")
    print("📚 API documentation: http://localhost:8010/docs")
    print("\nPress Ctrl+C to stop\n")
    
    # Start the FastAPI server
    try:
        from app.main import app
        import uvicorn
        uvicorn.run(app, host="0.0.0.0", port=8010, reload=True)
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
