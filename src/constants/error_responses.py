from typing import Any

COMMON_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    400: {
        "description": "Bad Request",
        "content": {"application/json": {"example": {"detail": "Bad request"}}},
    },
    404: {
        "description": "Resource not found",
        "content": {"application/json": {"example": {"detail": "Resource not found"}}},
    },
    422: {
        "description": "Validation error",
        "content": {"application/json": {"example": {"detail": "Validation failed"}}},
    },
    500: {
        "description": "Internal server error",
        "content": {
            "application/json": {
                "example": {"detail": "Unexpected server error occurred"}
            }
        },
    },
}
