import os
import time
import asyncio
from pathlib import Path
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from app.api.upload import router as upload_router
from app.api.dataset_profile import router as profile_router
from app.api.analyze import router as analyze_router
from app.api.chat import router as chat_router
from app.api.export import router as export_router
from app.core.logging import app_logger
from app.data.storage import cleanup_expired_datasets
from app.core.errors import (
    InsightForgeAPIException,
    custom_api_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    global_exception_handler
)

# Robust .env file discovery
for candidate_path in [
    Path.cwd() / ".env",
    Path(__file__).resolve().parent.parent / ".env",
    Path(__file__).resolve().parent.parent.parent / ".env"
]:
    if candidate_path.is_file():
        load_dotenv(candidate_path)
        break
else:
    load_dotenv()

async def background_dataset_cleaner():
    """Periodically purges temporary datasets older than 2 hours."""
    while True:
        try:
            await asyncio.sleep(1800)  # Every 30 minutes
            cleanup_expired_datasets(max_age_seconds=7200)
        except asyncio.CancelledError:
            break
        except Exception as e:
            app_logger.warning(f"Error during background dataset cleanup: {e}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    cleaner_task = asyncio.create_task(background_dataset_cleaner())
    yield
    # Shutdown
    cleaner_task.cancel()

app = FastAPI(
    title="InsightForge AI API",
    version="0.1.0",
    description="Production-hardened AI-powered data intelligence API with sandboxed Pandas execution.",
    lifespan=lifespan
)

# CORS Configuration from Environment Variables (Requirement 8)
default_origins = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000"
env_origins = os.environ.get("ALLOWED_ORIGINS", default_origins)
allowed_origins = [origin.strip() for origin in env_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Request Logging & Security Headers Middleware (Requirements 5, 7)
@app.middleware("http")
async def security_and_logging_middleware(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    duration_ms = round((time.time() - start_time) * 1000, 2)
    
    # Add defensive HTTP security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Structured access log (no sensitive credentials logged)
    if not request.url.path.startswith("/api/health"):
        app_logger.info(
            f"{request.method} {request.url.path} -> {response.status_code} ({duration_ms}ms)",
            extra={"extra_data": {
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms
            }}
        )
    
    return response

# Register Standardized Error Handlers (Requirement 9)
app.add_exception_handler(InsightForgeAPIException, custom_api_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)

# Register API Routers
app.include_router(upload_router)
app.include_router(profile_router)
app.include_router(analyze_router)
app.include_router(chat_router)
app.include_router(export_router)

@app.get("/api/health", status_code=status.HTTP_200_OK)
def health():
    return {
        "success": True,
        "status": "ok",
        "service": "InsightForge AI"
    }

@app.get("/api", status_code=status.HTTP_200_OK)
def root():
    return {
        "success": True,
        "name": "InsightForge AI",
        "version": "0.1.0",
        "security": "Sandboxed Pandas AST + Pydantic AI Validation"
    }

@app.get("/api/test-backend-failure", include_in_schema=False)
def test_backend_failure():
    """Diagnostic route to test unhandled exception formatting in production."""
    raise RuntimeError("Simulated unexpected internal engine failure")
