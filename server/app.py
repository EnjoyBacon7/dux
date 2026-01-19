"""
FastAPI application setup and configuration.

Provides core application initialization, middleware setup, error handling,
rate limiting, CORS configuration, and route registration.
"""

from fastapi import FastAPI, Request, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from starlette.middleware.sessions import SessionMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import logging
import os

from server.api import router as api_router
from server.auth_api import router as auth_router
from server.database import init_db
from server.config import settings
from server.thread_pool import shutdown_thread_pool

# ============================================================================
# Logging Configuration
# ============================================================================

# Create logs directory in working directory if it doesn't exist
log_dir = Path.cwd() / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / "app.log"

# Create file and stream handlers
file_handler = logging.FileHandler(log_file)
stream_handler = logging.StreamHandler()

# Configure format
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
stream_handler.setFormatter(formatter)

# Configure logging to write to both file and console
log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[file_handler, stream_handler]
)

# Configure FastAPI/Uvicorn access logging
access_logger = logging.getLogger("uvicorn.access")
access_logger.setLevel(log_level)
access_logger.addHandler(file_handler)
access_logger.addHandler(stream_handler)

logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file: {log_file}")

# ============================================================================
# Rate Limiting Setup
# ============================================================================

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

# ============================================================================
# FastAPI Application Initialization
# ============================================================================

app = FastAPI(docs_url="/apidoc", redoc_url=None)


# ============================================================================
# Exception Handlers
# ============================================================================


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unhandled exceptions.

    Catches all unhandled exceptions and returns a proper JSON response
    with error details (only if debug mode is enabled).
    """
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "message": str(exc) if settings.debug else "Internal server error"
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Handler for HTTPException to ensure consistent JSON responses.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


# ============================================================================
# Middleware Configuration
# ============================================================================

# Rate limiting middleware
if settings.rate_limit_enabled:
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS middleware (added before session middleware for proper ordering)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session middleware with secure settings
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    max_age=settings.session_max_age,
    same_site=settings.session_cookie_samesite,
    https_only=settings.session_cookie_secure,
)


# ============================================================================
# Startup Events
# ============================================================================


@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup.

    Currently initializes the database connection and schema.
    """
    init_db()


@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown.

    Gracefully shuts down the thread pool executor used for blocking operations.
    """
    shutdown_thread_pool()


# ============================================================================
# Route Registration
# ============================================================================

# Mount API routes
app.include_router(api_router, prefix="/api")
app.include_router(auth_router)


# ============================================================================
# Static File Serving and SPA Fallback
# ============================================================================

# Get project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Mount frontend static files (only if directory exists)
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Serve built docs without requiring the /static prefix
docs_dir = static_dir / "docs"
if docs_dir.exists():
    app.mount("/docs", StaticFiles(directory=str(docs_dir), html=True), name="docs")

    @app.get("/docs", include_in_schema=False)
    async def serve_docs_index():
        """Serve docs index without requiring a trailing slash."""
        index_path = docs_dir / "index.html"
        try:
            with open(index_path, "r", encoding="utf-8") as f:
                return HTMLResponse(f.read())
        except FileNotFoundError:
            logger.warning(f"Docs index not found at {index_path}")
            return JSONResponse(status_code=404, content={"detail": "Docs not built"})


@app.get("/{full_path:path}")
async def serve_spa(full_path: str):
    """
    Serve React SPA for all unmatched routes.

    This is a catch-all handler that serves index.html for any route
    not matched by other handlers, enabling client-side routing in the SPA.

    Args:
        full_path: The requested path

    Returns:
        HTML content of index.html for SPA, or error if not found
    """
    index_path = BASE_DIR / "static" / "index.html"

    try:
        with open(index_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        return HTMLResponse(content=html_content, status_code=200)
    except FileNotFoundError:
        logger.warning(f"index.html not found at {index_path}")
        return JSONResponse(
            status_code=404,
            content={"detail": "Frontend not built. Run 'npm run build' in dux-front directory."}
        )
    except Exception as e:
        logger.error(f"Failed to serve SPA: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Failed to serve application"}
        )
