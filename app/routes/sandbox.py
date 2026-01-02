"""Token generator sandbox routes"""

from fastapi import APIRouter, Depends, Request, Form
from fastapi.responses import HTMLResponse
from typing import Optional
from urllib.parse import urlencode

from app.services.livekit import LiveKitClient
from app.security.session_auth import requires_admin_hybrid
from app.security.csrf import get_csrf_token, verify_csrf_token
from app.utils.route_helpers import get_livekit_client_for_request, get_base_template_context


router = APIRouter()


@router.get("/sandbox", response_class=HTMLResponse)
async def sandbox_index(
    request: Request,
    current_user: str = Depends(requires_admin_hybrid),
):
    """Display token generator sandbox"""
    # Get base template context
    template_data = get_base_template_context(request)
    template_data.update({
        "request": request,
        "form_data": {},
        "token": None,
        "test_url": None,
    })

    return request.app.state.templates.TemplateResponse(
        "sandbox.html.j2",
        template_data,
    )


@router.post("/sandbox/generate", response_class=HTMLResponse)
async def generate_sandbox_token(
    request: Request,
    csrf_token: str = Form(...),
    room: str = Form(...),
    identity: str = Form(...),
    name: Optional[str] = Form(None),
    ttl: int = Form(3600),
    metadata: str = Form(""),
    can_publish: Optional[str] = Form(None),
    can_subscribe: Optional[str] = Form(None),
    can_publish_data: Optional[str] = Form(None),
    current_user: str = Depends(requires_admin_hybrid),
):
    """Generate a test token"""
    await verify_csrf_token(request)

    # Get LiveKit client for selected server
    lk = get_livekit_client_for_request(request)

    # Generate token
    token = lk.generate_token(
        room=room,
        identity=identity,
        name=name,
        ttl=ttl,
        metadata=metadata,
        can_publish=(can_publish == "on"),
        can_subscribe=(can_subscribe == "on"),
        can_publish_data=(can_publish_data == "on"),
    )

    # Generate test URL for LiveKit Meet (example)
    # Note: Update this URL based on your actual LiveKit Meet deployment
    test_params = {
        "url": lk.url,
        "token": token,
    }
    test_url = f"https://meet.livekit.io/custom?{urlencode(test_params)}"

    # Store form data to pre-fill
    form_data = {
        "room": room,
        "identity": identity,
        "name": name,
        "ttl": ttl,
        "metadata": metadata,
        "can_publish": (can_publish == "on"),
        "can_subscribe": (can_subscribe == "on"),
        "can_publish_data": (can_publish_data == "on"),
    }

    # Get base template context
    template_data = get_base_template_context(request)
    template_data.update({
        "request": request,
        "form_data": form_data,
        "token": token,
        "test_url": test_url,
    })

    return request.app.state.templates.TemplateResponse(
        "sandbox.html.j2",
        template_data,
    )
