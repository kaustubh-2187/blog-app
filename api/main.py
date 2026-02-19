from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import logging

from api.routes import blog, health, files
from api.config import settings

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Blog Planner API",
    description="Blog generation",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.on_event("startup")
async def startup_event():
    """Verify static files exist on startup."""
    static_dir = Path("static")
    required_files = ["index.html", "styles.css", "app.js"]
    
    logger.info(f"Checking static directory: {static_dir.absolute()}")
    
    for filename in required_files:
        filepath = static_dir / filename
        if filepath.exists():
            logger.info(f"✓ Found: {filename} ({filepath.stat().st_size} bytes)")
        else:
            logger.error(f"✗ Missing: {filename}")
    
    logger.info("Static files verification complete")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Including routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(blog.router, prefix="/api/v1", tags=["Blog"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])

# For mounting static files
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc)
        }
    )

@app.get("/")
async def root():
    return FileResponse("static/index.html")
