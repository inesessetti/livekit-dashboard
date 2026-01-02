"""Authentication routes"""

from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse

from app.security.session_auth import SessionAuth, requires_admin_hybrid, get_current_user_hybrid
from app.security.csrf import get_csrf_token, validate_csrf_token as csrf_validate
from app.services.session import SessionManager


router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Display login page"""
    # If already authenticated, redirect to dashboard
    if SessionAuth.is_authenticated(request):
        return RedirectResponse(url="/", status_code=303)
    
    return request.app.state.templates.TemplateResponse(
        "login.html.j2",
        {
            "request": request,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.post("/login", response_class=HTMLResponse)
async def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    csrf_token: str = Form(...),
):
    """Handle login form submission"""
    # Validate CSRF token
    if not csrf_validate(csrf_token):
        return request.app.state.templates.TemplateResponse(
            "login.html.j2",
            {
                "request": request,
                "error": "Invalid security token. Please try again.",
                "csrf_token": get_csrf_token(request),
            },
            status_code=403
        )
    
    # Verify credentials
    if SessionAuth.verify_credentials(username, password):
        # Login successful
        SessionAuth.login_user(request, username)
        
        # Redirect to dashboard (which will redirect to server selection if needed)
        return RedirectResponse(url="/", status_code=303)
    else:
        # Login failed
        return request.app.state.templates.TemplateResponse(
            "login.html.j2",
            {
                "request": request,
                "error": "Invalid username or password.",
                "csrf_token": get_csrf_token(request),
            },
            status_code=401
        )


@router.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    """Logout - Clear session completely"""
    # Clear server selection and all session data
    SessionManager.clear_server_selection(request)
    SessionAuth.logout_user(request)
    
    return request.app.state.templates.TemplateResponse(
        "logout.html.j2",
        {
            "request": request,
        },
    )


# Backward compatibility route for HTTP Basic Auth
@router.get("/logout-clear-auth")
async def logout_clear_auth(request: Request):
    """Endpoint to help clear HTTP Basic Auth credentials (backward compatibility)"""
    from fastapi.responses import Response
    
    # Always return 401 to force browser to clear cached credentials
    return Response(
        content="Authentication cleared",
        status_code=401,
        headers={"WWW-Authenticate": 'Basic realm="LiveKit Dashboard"'}
    )
