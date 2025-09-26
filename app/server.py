"""
Datagen API Server Startup Script
"""

import uvicorn
import sys
import os
from pathlib import Path

# Add parent directory to Python path for imports
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

if __name__ == "__main__":
    print("🚀 Starting Datagen API Server...")
    print("📝 API Documentation: http://localhost:8000/docs")
    print("🔍 ReDoc Documentation: http://localhost:8000/redoc")
    print("💚 Health Check: http://localhost:8000/api/v1/health")
    print("📊 Statistics: http://localhost:8000/api/v1/stats")
    print("\n" + "="*60)
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )