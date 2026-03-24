import logging
import time
import traceback
import uuid

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("app")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 🔹 Generate correlation ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        start_time = time.time()

        # Attach to request state (accessible everywhere)
        request.state.request_id = request_id

        try:
            # 🔹 Log incoming request
            logger.info(
                "request_started",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                },
            )

            response = await call_next(request)

            # 🔹 Calculate duration
            duration = round((time.time() - start_time) * 1000, 2)

            # 🔹 Log success
            logger.info(
                "request_completed",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "duration_ms": duration,
                },
            )

            # 🔹 Attach correlation ID to response
            response.headers["X-Request-ID"] = request_id

            return response

        except Exception as exc:
            duration = round((time.time() - start_time) * 1000, 2)

            # Full error logging
            logger.error(
                "request_failed",
                extra={
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "duration_ms": duration,
                    "error": str(exc),
                    "trace": traceback.format_exc(),
                },
            )

            return JSONResponse(
                status_code=500,
                content={
                    "success": False,
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "Something went wrong",
                        "request_id": request_id,
                    },
                },
            )
