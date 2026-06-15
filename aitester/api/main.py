import logging

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from aitester.api.routes import projects
from aitester.core.config import settings
from aitester.core.exceptions import (
    AITesterError,
    RecordNotFoundError,
)

logger = logging.getLogger("aitester.api")

app = FastAPI(
    title="AITester API",
    description="AI-Powered Universal API Testing Platform",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# Include Routers
app.include_router(projects.router, prefix="/api/v1")


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
