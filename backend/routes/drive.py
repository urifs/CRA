"""Google Drive OAuth + admin endpoints."""
from __future__ import annotations

import logging
import os
import secrets
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse

from services import google_drive_service as drive
from utils.auth import get_current_user
from utils.database import db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/drive", tags=["drive"])


def _frontend_url(request: Request) -> str:
    """Returns the canonical frontend URL based on the incoming request, with env fallback."""
    forwarded = request.headers.get("origin") or request.headers.get("referer")
    if forwarded:
        # Strip path/query if a referer was sent
        from urllib.parse import urlparse
        parsed = urlparse(forwarded)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
    return os.environ.get("FRONTEND_URL", "")


def _redirect_uri(request: Request) -> str:
    """Builds the OAuth redirect URI from the current request host (so it works in preview and prod)."""
    # The OAuth redirect must be registered in Google Console for each host.
    base = _frontend_url(request)
    if base:
        return f"{base}/api/drive/callback"
    return os.environ["GOOGLE_DRIVE_REDIRECT_URI"]


@router.get("/status")
async def drive_status(current_user: dict = Depends(get_current_user)):
    return await drive.get_status(db)


@router.get("/connect")
async def drive_connect(request: Request, current_user: dict = Depends(get_current_user)):
    """Returns the Google authorization URL so the admin can connect Drive."""
    if (current_user or {}).get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Apenas administradores podem conectar o Drive.")

    redirect_uri = _redirect_uri(request)
    state = secrets.token_urlsafe(24)
    # Store state with the requesting frontend so callback can route back correctly
    await db.drive_oauth_states.insert_one(
        {"state": state, "frontend": _frontend_url(request), "redirect_uri": redirect_uri}
    )

    flow = drive.build_oauth_flow(redirect_uri)
    authorization_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state,
    )
    return {"authorization_url": authorization_url}


@router.get("/callback")
async def drive_callback(
    request: Request,
    code: str = Query(...),
    state: str = Query(...),
    error: str | None = Query(None),
):
    """Handles the OAuth redirect from Google and persists credentials."""
    state_doc = await db.drive_oauth_states.find_one({"state": state})
    if not state_doc:
        raise HTTPException(status_code=400, detail="State inválido ou expirado.")
    await db.drive_oauth_states.delete_one({"state": state})

    frontend = state_doc.get("frontend") or _frontend_url(request)
    redirect_uri = state_doc.get("redirect_uri") or _redirect_uri(request)

    if error:
        return RedirectResponse(
            url=f"{frontend}/admin/storage?drive={urlencode({'error': error})}"
        )

    try:
        # scopes=None on callback -> accept whatever Google granted (playbook recommendation)
        flow = drive.build_oauth_flow(redirect_uri, scopes=None)
        flow.fetch_token(code=code)
        creds = flow.credentials

        required = {"https://www.googleapis.com/auth/drive"}
        granted = set(creds.scopes or [])
        if not required.issubset(granted):
            missing = ", ".join(required - granted)
            return RedirectResponse(
                url=f"{frontend}/admin/storage?drive=error&detail=Escopos+ausentes:+{missing}"
            )

        email = await drive.fetch_userinfo(creds)
        await drive.save_credentials(db, creds, user_email=email)
        logger.info("Google Drive connected for workspace (account: %s)", email)
        return RedirectResponse(url=f"{frontend}/admin/storage?drive=connected")
    except Exception as e:  # noqa: BLE001
        logger.exception("Drive OAuth callback failed: %s", e)
        return RedirectResponse(url=f"{frontend}/admin/storage?drive=error&detail={str(e)[:120]}")


@router.post("/disconnect")
async def drive_disconnect(current_user: dict = Depends(get_current_user)):
    if (current_user or {}).get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Apenas administradores podem desconectar o Drive.")
    await drive.disconnect(db)
    return {"success": True, "message": "Google Drive desconectado."}


@router.get("/test")
async def drive_test(current_user: dict = Depends(get_current_user)):
    """Quick test endpoint: verifies the connection works by listing the root."""
    if (current_user or {}).get("role") not in ("admin", "superadmin"):
        raise HTTPException(status_code=403, detail="Apenas administradores.")
    service = await drive.get_service(db)
    if not service:
        raise HTTPException(status_code=400, detail="Drive não conectado.")
    files = await drive.list_folder(service, [])  # lists CRA-ERP root
    return {"success": True, "root_folder": drive.ROOT_FOLDER_NAME, "items": len(files), "files": files[:10]}
