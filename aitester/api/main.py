import logging

from fastapi import Depends, FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from aitester.api.middleware import RequestTimingMiddleware
from aitester.api.routes import projects, test_runs
from aitester.api.v1 import reports
from aitester.core.config import settings
from aitester.core.exceptions import (
    AITesterError,
    RecordNotFoundError,
)
from aitester.core.security import verify_api_key

logger = logging.getLogger("aitester.api")

app = FastAPI(
    title="AITester API",
    description="AI-Powered Universal API Testing Platform",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    dependencies=[Depends(verify_api_key)],
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middleware
app.add_middleware(RequestTimingMiddleware)

# Include Routers
app.include_router(projects.router, prefix="/api/v1")
app.include_router(test_runs.router, prefix="/api/v1")
app.include_router(reports.router, prefix="/api/v1")


# Exception Handlers
@app.exception_handler(RecordNotFoundError)
async def not_found_exception_handler(request: Request, exc: RecordNotFoundError) -> JSONResponse:
    logger.warning(f"Record not found: {exc}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"error": "Not Found", "message": exc.message, "details": exc.details},
    )


@app.exception_handler(AITesterError)
async def generic_aitester_exception_handler(request: Request, exc: AITesterError) -> JSONResponse:
    logger.error(f"Internal error: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "message": exc.message},
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(f"Unhandled exception: {exc}", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error", "message": "An unexpected error occurred."},
    )


@app.get("/health", tags=["Health"])
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.
    """
    return {
        "status": "ok",
        "environment": "development" if settings.is_development else "production",
    }
