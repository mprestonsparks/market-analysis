"""
API Server Entry Point
"""
import uvicorn
import os
from pathlib import Path
import sys

def main():
    """Run the FastAPI server"""
    # Add the project root to Python path
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    
    # Import the FastAPI app
    from src.api.app import app  # Import here after path is set
    
    port = int(os.getenv('API_PORT', 8000))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    # Run the server
    uvicorn.run(
        app,  # Use the app instance directly
        host=host,
        port=port,
        reload=True,
        reload_dirs=[str(project_root / 'src')],
        workers=1
    )

if __name__ == "__main__":
    main()
