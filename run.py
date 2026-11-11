"""
Meridian Enterprise Application - Entrypoint CLI
Usage: python run.py [--port=8001] [--reload]
"""
import sys
import os
from pathlib import Path

# Add backend directory to sys.path so backend modules can be imported directly
BASE_DIR = Path(__file__).resolve().parent
BACKEND_DIR = BASE_DIR / "backend"
sys.path.insert(0, str(BACKEND_DIR))
sys.path.insert(0, str(BASE_DIR))

# Create compatibility alias so 'import app' or 'from app...' works seamlessly if invoked
import backend
sys.modules["app"] = backend

import uvicorn
from config import HOST, PORT

if __name__ == "__main__":
    port = PORT
    reload = "--reload" in sys.argv
    for arg in sys.argv:
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
    print(f"Starting Meridian Enterprise Application on http://{HOST}:{port} (Reload: {reload})...")
    uvicorn.run("main:app", host=HOST, port=port, reload=reload, app_dir=str(BACKEND_DIR))
