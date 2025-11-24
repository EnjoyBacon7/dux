from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from server.api import router as api_router

app = FastAPI()

# Mount API routes with /api prefix
app.include_router(api_router, prefix="/api")

# Get the parent directory (project root)
BASE_DIR = Path(__file__).resolve().parent.parent

# Mount the frontend static files
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    return FileResponse(str(BASE_DIR / "static" / "index.html"))