"""Settings and configuration routes"""

import os
from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse

from app.services.livekit import LiveKitClient
from app.security.session_auth import requires_admin_hybrid
from app.utils.route_helpers import get_livekit_client_for_request, get_base_template_context


router = APIRouter()


@router.get("/settings", response_class=HTMLResponse)
async def settings_index(
    request: Request,
    current_user: str = Depends(requires_admin_hybrid),
):
    """Display settings and configuration"""
    # Get LiveKit client for selected server
    lk = get_livekit_client_for_request(request)
    
    # Get server info
    server_info = await lk.get_server_info()

    config = {
        "livekit_url": lk.url,
        "status": server_info.get("status", "unknown"),
        "sip_enabled": lk.sip_enabled,
        "debug": os.environ.get("DEBUG", "false").lower() == "true",
    }

    # Get base template context
    template_data = get_base_template_context(request)
    template_data.update({
        "request": request,
        "config": config,
    })

    return request.app.state.templates.TemplateResponse(
        "settings.html.j2",
        template_data,
    )
