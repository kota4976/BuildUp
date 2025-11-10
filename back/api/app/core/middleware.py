"""Custom middleware for the application"""
import uuid
import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add request ID to all requests"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add request ID"""
        # Generate or get request ID
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # Add request ID to request state
        request.state.request_id = request_id
        
        # Log request
        start_time = time.time()
        logger.info(
            f"Request started: {request.method} {request.url.path} "
            f"[{request_id}]"
        )
        
        # Process request
        response = await call_next(request)
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log response
        duration = time.time() - start_time
        logger.info(
            f"Request completed: {request.method} {request.url.path} "
            f"[{request_id}] - {response.status_code} - {duration:.3f}s"
        )
        
        return response

