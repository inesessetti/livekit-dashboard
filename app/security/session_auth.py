"""Session-based Authentication System"""

import os
import secrets
from typing import Optional
from fastapi import Request, HTTPException, status, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials


class SessionAuth:
    """Session-based authentication manager"""
    
    SESSION_USER_KEY = "authenticated_user"
    SESSION_AUTH_KEY = "is_authenticated"
    
    @staticmethod
    def verify_credentials(username: str, password: str) -> bool:
        """Verify username and password against environment variables"""
        correct_username = os.environ.get("ADMIN_USERNAME", "admin")
        correct_password = os.environ.get("ADMIN_PASSWORD", "changeme")

        # Use constant-time comparison to prevent timing attacks
        username_correct = secrets.compare_digest(
            username.encode("utf8"), correct_username.encode("utf8")
        )
        password_correct = secrets.compare_digest(
            password.encode("utf8"), correct_password.encode("utf8")
        )

        return username_correct and password_correct
    
    @staticmethod
    def login_user(request: Request, username: str) -> bool:
        """Log in a user by setting session data"""
        request.session[SessionAuth.SESSION_AUTH_KEY] = True
        request.session[SessionAuth.SESSION_USER_KEY] = username
        return True
    
    @staticmethod
    def logout_user(request: Request):
        """Log out a user by clearing session data"""
        request.session.clear()
    
    @staticmethod
    def is_authenticated(request: Request) -> bool:
        """Check if user is authenticated"""
        return request.session.get(SessionAuth.SESSION_AUTH_KEY, False)
    
    @staticmethod
    def get_current_user(request: Request) -> Optional[str]:
        """Get current authenticated user"""
        if SessionAuth.is_authenticated(request):
            return request.session.get(SessionAuth.SESSION_USER_KEY)
        return None


def requires_auth(request: Request) -> str:
    """Dependency that requires authentication"""
    if not SessionAuth.is_authenticated(request):
        # Check if this is an API request or browser request
        accept_header = request.headers.get("accept", "")
        if "text/html" in accept_header:
            # Browser request - redirect to login
            raise HTTPException(
                status_code=status.HTTP_303_SEE_OTHER,
                detail="Authentication required",
                headers={"Location": "/login"}
            )
        else:
            # API request - return 401
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Session"}
            )
    
    return SessionAuth.get_current_user(request)


def get_current_user_optional(request: Request) -> Optional[str]:
    """Get current user without requiring authentication"""
    return SessionAuth.get_current_user(request)


# Backward compatibility - try HTTP Basic Auth first, then session
def requires_admin_hybrid(request: Request) -> str:
    """Hybrid authentication - supports both HTTP Basic and Session"""
    # First try session auth
    if SessionAuth.is_authenticated(request):
        return SessionAuth.get_current_user(request)
    
    # Fallback to HTTP Basic Auth for backward compatibility
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Basic "):
        try:
            import base64
            encoded = auth_header.replace("Basic ", "")
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, password = decoded.split(":", 1)
            
            if SessionAuth.verify_credentials(username, password):
                # Auto-login to session for future requests
                SessionAuth.login_user(request, username)
                return username
        except Exception:
            pass
    
    # No valid authentication found
    accept_header = request.headers.get("accept", "")
    if "text/html" in accept_header:
        # Browser request - redirect to login
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Authentication required",
            headers={"Location": "/login"}
        )
    else:
        # API request - return 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Basic, Session"}
        )


def get_current_user_hybrid(request: Request) -> Optional[str]:
    """Get current user with hybrid auth support"""
    # Try session first
    user = SessionAuth.get_current_user(request)
    if user:
        return user
    
    # Try HTTP Basic Auth
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Basic "):
        try:
            import base64
            encoded = auth_header.replace("Basic ", "")
            decoded = base64.b64decode(encoded).decode("utf-8")
            username, _ = decoded.split(":", 1)
            return username
        except Exception:
            pass
    
    return None
