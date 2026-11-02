import uvicorn
import sys
import os

if __name__ == "__main__":
    # Add backend directory to sys.path
    backend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "backend")
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    # Configurable port: CLI argument > BACKEND_PORT > PORT > default 8001
    # Port 8001 prevents WinError 10013 on Windows systems where port 8000 is reserved
    port = int(sys.argv[1]) if len(sys.argv) > 1 else int(os.getenv("BACKEND_PORT", os.getenv("PORT", "8001")))
    host = os.getenv("HOST", "127.0.0.1")

    print(f"Starting NexusIQ FastAPI Engine on http://{host}:{port}...")
    uvicorn.run("app.main:app", host=host, port=port, reload=True, app_dir=backend_dir)

