"""
Frontend HTML Page Router - Meridian Enterprise Application
"""
import os
from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from config import TEMPLATES_DIR, BASE_DIR

router = APIRouter(tags=["Frontend Pages"])

def get_template_path(filename: str) -> str:
    tpl = TEMPLATES_DIR / filename
    if tpl.exists():
        return str(tpl)
    # Fallback to base directory
    root_tpl = BASE_DIR / filename
    return str(root_tpl)

@router.get("/")
@router.get("/portal")
@router.get("/employee_portal.html")
def employee_portal():
    return FileResponse(get_template_path("employee_portal.html"), media_type="text/html")

@router.get("/login")
@router.get("/login.html")
def login_page():
    return FileResponse(get_template_path("login.html"), media_type="text/html")

@router.get("/customer_store.html")
def customer_store_page():
    return FileResponse(get_template_path("customer_store.html"), media_type="text/html")

@router.get("/support/chat/{session_id}")
def support_chat_page(session_id: str):
    """
    Renders the live support chat window for Session ID.
    Accessed by both Employee (Maya) and Support Engineer (Alex).
    """
    return FileResponse(get_template_path("support_chat.html"), media_type="text/html")
