import logging
import time
import uuid

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("aitester.api.middleware")

class RequestTimingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # Generate or extract request ID
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))

        # We can put request_id in request.state if needed
        request.state.request_id = request_id

        response = await call_next(request)

        process_time = time.time() - start_time
        response.headers["X-Response-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id

        return response
