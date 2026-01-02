"""Route helper functions for common operations"""

from typing import Optional
from fastapi import Request
from fastapi.responses import RedirectResponse

from app.services.livekit import create_livekit_client, LiveKitClient
from app.services.session import get_current_server_id
from app.services.server_config import get_server_config_manager
from app.security.session_auth import get_current_user_hybrid
from app.security.csrf import get_csrf_token


def get_livekit_client_for_request(request: Request) -> LiveKitClient:
    """Get LiveKit client for the currently selected server"""
    current_server_id = get_current_server_id(request)
    if not current_server_id:
        raise RedirectResponse(url="/select-server", status_code=303)
    
    return create_livekit_client(current_server_id)


def get_base_template_context(request: Request) -> dict:
    """Get common template context data"""
    # Get current user
    current_user = get_current_user_hybrid(request)
    
    # Get server configuration data
    server_manager = get_server_config_manager()
    servers = server_manager.list_servers()
    current_server_id = get_current_server_id(request)
    current_server_config = None
    
    if current_server_id:
        current_server_config = server_manager.get_server(current_server_id)
    
    # Get LiveKit client for SIP status
    sip_enabled = False
    if current_server_id:
        try:
            lk = create_livekit_client(current_server_id)
            sip_enabled = lk.sip_enabled
        except Exception:
            pass
    
    return {
        "current_user": current_user,
        "sip_enabled": sip_enabled,
        "csrf_token": get_csrf_token(request),
        "servers": servers,
        "current_server_id": current_server_id,
        "current_server_config": current_server_config,
    }
