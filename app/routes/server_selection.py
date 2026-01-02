"""Server selection routes"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse

from app.services.session import set_selected_server_id, has_server_selection
from app.services.server_config import get_server_config_manager
from app.security.session_auth import requires_admin_hybrid
from app.security.csrf import validate_csrf_token as csrf_validate, get_csrf_token


router = APIRouter()


@router.get("/select-server", response_class=HTMLResponse)
async def server_selection_page(request: Request, current_user: str = Depends(requires_admin_hybrid)):
    """Display server selection page"""
    manager = get_server_config_manager()
    servers = manager.list_servers()
    
    # If only one server, set it automatically and redirect
    if len(servers) == 1:
        set_selected_server_id(request, servers[0].id)
        return RedirectResponse(url="/", status_code=303)
    
    return request.app.state.templates.TemplateResponse(
        "server_select.html.j2",
        {
            "request": request,
            "servers": servers,
            "csrf_token": get_csrf_token(request),
        },
    )


@router.post("/select-server", response_class=HTMLResponse)
async def handle_server_selection(
    request: Request,
    server_id: str = Form(...),
    csrf_token: str = Form(...),
    current_user: str = Depends(requires_admin_hybrid),
):
    """Handle server selection from the selection page"""
    # Validate CSRF token
    if not csrf_validate(csrf_token):
        manager = get_server_config_manager()
        servers = manager.list_servers()
        return request.app.state.templates.TemplateResponse(
            "server_select.html.j2",
            {
                "request": request,
                "servers": servers,
                "error": "Invalid security token. Please try again.",
                "csrf_token": get_csrf_token(request),
            },
            status_code=403
        )
    
    # Validate server exists
    manager = get_server_config_manager()
    if not manager.get_server(server_id):
        servers = manager.list_servers()
        return request.app.state.templates.TemplateResponse(
            "server_select.html.j2",
            {
                "request": request,
                "servers": servers,
                "error": "Invalid server selection. Please choose a valid server.",
                "csrf_token": get_csrf_token(request),
            },
            status_code=400
        )
    
    # Set selected server in session
    success = set_selected_server_id(request, server_id)
    
    if success:
        # Redirect to dashboard
        return RedirectResponse(url="/", status_code=303)
    else:
        servers = manager.list_servers()
        return request.app.state.templates.TemplateResponse(
            "server_select.html.j2",
            {
                "request": request,
                "servers": servers,
                "error": "Failed to save server selection. Please try again.",
                "csrf_token": get_csrf_token(request),
            },
            status_code=500
        )
