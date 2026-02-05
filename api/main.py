from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles  # ADD THIS
from fastapi.responses import FileResponse   # ADD THIS

from api.routes import blog, health, files
from api.config import settings

# Create FastAPI app
app = FastAPI(
    title="Blog Planner API",
    description="AI-powered blog generation with LangGraph",
    version="1.0.0",
    docs_url="/docs",  # Swagger will be at /docs
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ADD THIS: Mount static files
app.mount("/static", StaticFiles(directory="frontend"), name="static")

# Include routers
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(blog.router, prefix="/api/v1", tags=["Blog"])
app.include_router(files.router, prefix="/api/v1", tags=["Files"])

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

# CHANGE THIS: Serve HTML at root instead of JSON
@app.get("/")
async def root():
    """Serve the frontend HTML."""
    return FileResponse("frontend/index.html")