#!/usr/bin/env python3
"""
Run Datagen API server
"""

import uvicorn
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    print("🚀 Starting Datagen API Server...")
    print("📝 API Documentation will be available at: http://localhost:8000/docs")
    print("🔍 Alternative docs at: http://localhost:8000/redoc")
    print("💚 Health check: http://localhost:8000/health")
    print("📊 Statistics: http://localhost:8000/stats")
    print("\n" + "="*50)
    
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        access_log=True
    )