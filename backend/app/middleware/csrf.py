"""CSRF protection middleware."""

import secrets

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from loguru import logger

from app.utils.security import generate_csrf_token, CSRF_HEADER_NAME


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add CSRF protection to the application.
    
    This middleware:
    1. Generates and sets CSRF token in cookie for safe requests
    2. Validates CSRF token for state-changing requests (POST, PUT, DELETE, PATCH)
    """

    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.csrf_cookie_name = "csrf_token"
        self.csrf_header_name = CSRF_HEADER_NAME
        self.safe_methods = {"GET", "HEAD", "OPTIONS", "TRACE"}
        
    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and add CSRF protection.
        
        Args:
            request: Incoming request
            call_next: Next middleware/route handler
            
        Returns:
            Response with CSRF protection
        """
        # Skip CSRF for safe methods
        if request.method in self.safe_methods:
            response = await call_next(request)
            await self._set_csrf_cookie(request, response)
            return response
        
        # For state-changing methods, validate CSRF token
        if request.method in {"POST", "PUT", "DELETE", "PATCH"}:
            csrf_error = await self._validate_csrf_token(request)
            if csrf_error:
                return csrf_error
        
        # Process request
        response = await call_next(request)
        return response
    
    async def _set_csrf_cookie(self, request: Request, response: Response) -> None:
        """
        Set CSRF token in cookie if not already present.
        
        Args:
            request: Incoming request
            response: Outgoing response
        """
        existing_token = request.cookies.get(self.csrf_cookie_name)
        
        if not existing_token:
            # Generate new CSRF token
            csrf_token = generate_csrf_token()
            
            # Set cookie with security attributes
            response.set_cookie(
                key=self.csrf_cookie_name,
                value=csrf_token,
                httponly=False,  # JavaScript needs to read this
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",  # Protect against CSRF
                max_age=3600,  # 1 hour
                path="/"
            )
            logger.debug(f"Set CSRF cookie for {request.url}")
    
    async def _validate_csrf_token(self, request: Request) -> JSONResponse | None:
        """
        Validate CSRF token from request header.
        
        Args:
            request: Incoming request
            
        Returns:
            JSONResponse if validation fails, None otherwise
        """
        # Get token from cookie
        cookie_token = request.cookies.get(self.csrf_cookie_name)
        
        # Get token from header
        header_token = request.headers.get(self.csrf_header_name)
        
        # Validate tokens
        if not cookie_token:
            logger.warning(f"CSRF cookie missing for {request.url}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token missing. Please refresh the page."}
            )
        
        if not header_token:
            logger.warning(f"CSRF header missing for {request.url}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "CSRF token required in headers."}
            )
        
        # Use constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(cookie_token, header_token):
            logger.warning(f"CSRF token mismatch for {request.url}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={"detail": "Invalid CSRF token. Please refresh the page."}
            )
        
        return None

