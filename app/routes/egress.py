"""Egress/Recording routes"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from typing import Optional
from datetime import datetime

from app.services.livekit import LiveKitClient
from app.security.session_auth import requires_admin_hybrid
from app.security.csrf import get_csrf_token, verify_csrf_token
from app.utils.route_helpers import get_livekit_client_for_request, get_base_template_context


router = APIRouter()


@router.get("/egress", response_class=HTMLResponse, )
async def egress_index(
    request: Request,
    partial: Optional[str] = None,
    current_user: str = Depends(requires_admin_hybrid),
):
    """List all egress jobs"""
    # Get LiveKit client for selected server
    lk = get_livekit_client_for_request(request)
    
    egress_jobs = await lk.list_egress(active=True)

    # Get base template context
    template_data = get_base_template_context(request)
    template_data.update({
        "request": request,
        "egress_jobs": egress_jobs,
    })

    # Return partial for HTMX polling
    if partial:
        return request.app.state.templates.TemplateResponse(
            "egress/index.html.j2",
            template_data,
        )

    return request.app.state.templates.TemplateResponse(
        "egress/index.html.j2",
        template_data,
    )


@router.post("/egress/start", )
async def start_egress(
    request: Request,
    csrf_token: str = Form(...),
    room_name: str = Form(...),
    output_filename: str = Form(...),
    layout: str = Form("grid"),
    audio_only: Optional[str] = Form(None),
    video_only: Optional[str] = Form(None),
    current_user: str = Depends(requires_admin_hybrid),
):
    """Start a room composite egress"""
    await verify_csrf_token(request)

    # Get LiveKit client for selected server
    lk = get_livekit_client_for_request(request)

    try:
        # Replace placeholders in filename
        filename = output_filename.replace("{room}", room_name)
        filename = filename.replace("{time}", datetime.now().strftime("%Y%m%d_%H%M%S"))
        
        await lk.start_room_composite_egress(
            room_name=room_name,
            output_filename=filename,
            layout=layout,
            audio_only=(audio_only == "on"),
            video_only=(video_only == "on"),
        )
    except Exception as e:
        print(f"Error starting egress: {e}")

    return RedirectResponse(url="/egress", status_code=303)


@router.post("/egress/{egress_id}/stop", )
async def stop_egress(
    request: Request,
    egress_id: str,
    csrf_token: str = Form(...),
    current_user: str = Depends(requires_admin_hybrid),
):
    """Stop an egress job"""
    await verify_csrf_token(request)
    
    # Get LiveKit client for selected server
    lk = get_livekit_client_for_request(request)
    
    try:
        await lk.stop_egress(egress_id)
    except Exception as e:
        print(f"Error stopping egress: {e}")

    return RedirectResponse(url="/egress", status_code=303)
