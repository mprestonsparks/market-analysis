"""
API Server Entry Point
"""
import uvicorn
import os
import sys
from pathlib import Path

# Add src directory to Python path
src_path = Path(__file__).parent.parent
sys.path.append(str(src_path))

from src.api.app import app

def main():
    """Run the FastAPI server"""
    port = int(os.getenv('API_PORT', 8000))
    host = os.getenv('API_HOST', '0.0.0.0')
    
    uvicorn.run(
        "src.api.app:app",
        host=host,
        port=port,
        reload=True,  # Enable auto-reload during development
        workers=1     # For development, increase in production
    )

if __name__ == "__main__":
    main()
