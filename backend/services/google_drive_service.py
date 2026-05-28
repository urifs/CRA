"""
Google Drive integration service.
- Stores OAuth credentials for the workspace (single shared connection chosen by the admin).
- Provides primitives for uploading, listing, downloading and deleting files inside a single
  root folder `CRA-ERP` (created lazily on first upload) with per-entity subfolders.
"""
from __future__ import annotations

import io
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaIoBaseUpload

logger = logging.getLogger(__name__)

# Single workspace-wide connection id. The user reported in handoff that the
# admin will connect ONE Google account for the whole company.
WORKSPACE_KEY = "workspace"

SCOPES = ["https://www.googleapis.com/auth/drive"]

ROOT_FOLDER_NAME = "CRA-ERP"


def _client_config() -> dict:
    return {
        "web": {
            "client_id": os.environ["GOOGLE_CLIENT_ID"],
            "client_secret": os.environ["GOOGLE_CLIENT_SECRET"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [os.environ["GOOGLE_DRIVE_REDIRECT_URI"]],
        }
    }


def build_oauth_flow(redirect_uri: str, *, scopes: Optional[list[str]] = None) -> Flow:
    """Builds an OAuth Flow. Pass scopes=None on callback to accept whatever Google grants."""
    return Flow.from_client_config(
        _client_config(),
        scopes=scopes if scopes is not None else SCOPES,
        redirect_uri=redirect_uri,
    )


def _credentials_to_doc(creds: Credentials) -> dict:
    return {
        "access_token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": list(creds.scopes or []),
        "expiry": creds.expiry.replace(tzinfo=timezone.utc).isoformat()
        if creds.expiry
        else None,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def _doc_to_credentials(doc: dict) -> Credentials:
    return Credentials(
        token=doc["access_token"],
        refresh_token=doc.get("refresh_token"),
        token_uri=doc["token_uri"],
        client_id=doc["client_id"],
        client_secret=doc["client_secret"],
        scopes=doc.get("scopes") or SCOPES,
    )


async def save_credentials(db, creds: Credentials, *, user_email: str | None = None) -> None:
    doc = _credentials_to_doc(creds)
    doc["key"] = WORKSPACE_KEY
    if user_email:
        doc["connected_email"] = user_email
        doc["connected_at"] = datetime.now(timezone.utc).isoformat()
    await db.drive_credentials.update_one(
        {"key": WORKSPACE_KEY}, {"$set": doc}, upsert=True
    )


async def load_credentials(db) -> Optional[Credentials]:
    doc = await db.drive_credentials.find_one({"key": WORKSPACE_KEY})
    if not doc:
        return None
    creds = _doc_to_credentials(doc)
    # Refresh if needed
    if creds.expired and creds.refresh_token:
        try:
            creds.refresh(GoogleRequest())
            await db.drive_credentials.update_one(
                {"key": WORKSPACE_KEY},
                {
                    "$set": {
                        "access_token": creds.token,
                        "expiry": creds.expiry.replace(tzinfo=timezone.utc).isoformat()
                        if creds.expiry
                        else None,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    }
                },
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Failed to refresh Drive token: %s", e)
            return None
    return creds


async def get_service(db):
    creds = await load_credentials(db)
    if not creds:
        return None
    return build("drive", "v3", credentials=creds, cache_discovery=False)


async def disconnect(db) -> None:
    await db.drive_credentials.delete_one({"key": WORKSPACE_KEY})


async def get_status(db) -> dict:
    doc = await db.drive_credentials.find_one({"key": WORKSPACE_KEY})
    if not doc:
        return {"connected": False}
    return {
        "connected": True,
        "email": doc.get("connected_email"),
        "connected_at": doc.get("connected_at"),
        "updated_at": doc.get("updated_at"),
        "scopes": doc.get("scopes", []),
    }


async def fetch_userinfo(creds: Credentials) -> Optional[str]:
    """Best-effort: returns the email of the connected Google account."""
    try:
        oauth2 = build("oauth2", "v2", credentials=creds, cache_discovery=False)
        info = oauth2.userinfo().get().execute()
        return info.get("email")
    except Exception as e:  # noqa: BLE001
        logger.warning("Could not fetch userinfo: %s", e)
        return None


# ---------------- Folder helpers ----------------

async def _find_or_create_folder(service, name: str, parent_id: Optional[str] = None) -> str:
    safe_name = name.replace("'", "\\'")
    q = (
        f"name = '{safe_name}' and mimeType = 'application/vnd.google-apps.folder' "
        f"and trashed = false"
    )
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = service.files().list(q=q, fields="files(id, name)", pageSize=1).execute()
    files = res.get("files", [])
    if files:
        return files[0]["id"]
    metadata: dict[str, Any] = {
        "name": name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if parent_id:
        metadata["parents"] = [parent_id]
    created = service.files().create(body=metadata, fields="id").execute()
    return created["id"]


async def ensure_path(service, path_parts: list[str]) -> str:
    """Ensures a path like ['CRA-ERP','financeiro','contas_pagar'] exists, returns leaf folder id."""
    parent = None
    for part in path_parts:
        parent = await _find_or_create_folder(service, part, parent)
    return parent  # type: ignore[return-value]


# ---------------- File operations ----------------

async def upload_bytes(
    service,
    *,
    file_bytes: bytes,
    filename: str,
    mime_type: str,
    folder_path: list[str],
) -> dict:
    """Uploads a file into the given folder path (always prefixed with root CRA-ERP).
    Returns: {id, name, webViewLink, webContentLink, size, mimeType}
    """
    full_path = [ROOT_FOLDER_NAME, *folder_path]
    folder_id = await ensure_path(service, full_path)
    media = MediaIoBaseUpload(
        io.BytesIO(file_bytes), mimetype=mime_type or "application/octet-stream", resumable=False
    )
    metadata = {"name": filename, "parents": [folder_id]}
    file = (
        service.files()
        .create(
            body=metadata,
            media_body=media,
            fields="id, name, webViewLink, webContentLink, size, mimeType, createdTime",
        )
        .execute()
    )
    return file


async def download_bytes(service, file_id: str) -> tuple[bytes, dict]:
    meta = (
        service.files()
        .get(fileId=file_id, fields="id, name, mimeType, size")
        .execute()
    )
    request = service.files().get_media(fileId=file_id)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, request)
    done = False
    while not done:
        _status, done = downloader.next_chunk()
    buf.seek(0)
    return buf.read(), meta


async def delete_file(service, file_id: str) -> None:
    try:
        service.files().delete(fileId=file_id).execute()
    except HttpError as e:
        if e.resp.status == 404:
            return
        raise


async def list_folder(service, folder_path: list[str]) -> list[dict]:
    """Lists files & subfolders inside the given folder path under CRA-ERP."""
    full_path = [ROOT_FOLDER_NAME, *folder_path]
    folder_id = await ensure_path(service, full_path)
    q = f"'{folder_id}' in parents and trashed = false"
    res = (
        service.files()
        .list(
            q=q,
            fields="files(id, name, mimeType, size, modifiedTime, webViewLink, iconLink)",
            pageSize=1000,
            orderBy="folder,name",
        )
        .execute()
    )
    return res.get("files", [])
