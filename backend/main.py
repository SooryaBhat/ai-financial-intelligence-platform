"""
Main application entry point for ALLADIN backend.
Re-exports the FastAPI app from app.main.

Supports:
  1. Render Root Directory = 'backend' with Start Command:
       uvicorn main:app --host 0.0.0.0 --port $PORT
     or:
       uvicorn app.main:app --host 0.0.0.0 --port $PORT

  2. Render Root Directory = '.' (repo root) with Start Command:
       uvicorn backend.main:app --host 0.0.0.0 --port $PORT
"""
import sys
from pathlib import Path

# Ensure backend directory is in sys.path so 'app' and its subpackages resolve cleanly
_backend_dir = Path(__file__).resolve().parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from app.main import app, create_app  # noqa: F401

__all__ = ["app", "create_app"]

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
