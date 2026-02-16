"""IAudit - Google Drive storage service for PDF certificates."""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime

import httpx
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from app.config import settings

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive.file"]


class GoogleDriveService:
    """Manages PDF uploads to Google Drive with structured folder hierarchy."""

    def __init__(self):
        self._service = None
        self._folder_cache: dict[str, str] = {}

    def _get_service(self):
        """Build or return cached Drive service."""
        if self._service is None:
            creds_path = settings.google_drive_credentials_path
            if not os.path.exists(creds_path):
                logger.warning(
                    f"Google Drive credentials not found at {creds_path}. "
                    "PDF upload will be skipped."
                )
                return None

            credentials = service_account.Credentials.from_service_account_file(
                creds_path, scopes=SCOPES
            )
            self._service = build("drive", "v3", credentials=credentials)
        return self._service

    def _find_or_create_folder(
        self, name: str, parent_id: str | None = None
    ) -> str | None:
        """Find or create a folder by name under parent_id."""
        service = self._get_service()
        if not service:
            return None

        cache_key = f"{parent_id}:{name}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]

        # Search for existing folder
        query = f"name = '{name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
        if parent_id:
            query += f" and '{parent_id}' in parents"

        results = (
            service.files()
            .list(q=query, spaces="drive", fields="files(id, name)")
            .execute()
        )
        files = results.get("files", [])

        if files:
            folder_id = files[0]["id"]
        else:
            # Create folder
            metadata = {
                "name": name,
                "mimeType": "application/vnd.google-apps.folder",
            }
            if parent_id:
                metadata["parents"] = [parent_id]

            folder = (
                service.files()
                .create(body=metadata, fields="id")
                .execute()
            )
            folder_id = folder["id"]

        self._folder_cache[cache_key] = folder_id
        return folder_id

    def _build_folder_path(self, tipo: str, cnpj: str) -> str | None:
        """
        Create folder structure: IAudit/{tipo}/{CNPJ}/
        Returns the CNPJ folder ID.
        """
        root_id = settings.google_drive_root_folder_id or None

        # IAudit root
        iaudit_id = self._find_or_create_folder("IAudit", root_id)
        if not iaudit_id:
            return None

        # Tipo subfolder
        tipo_labels = {
            "cnd_federal": "CND_Federal",
            "cnd_pr": "CND_Parana",
            "fgts_regularidade": "FGTS_Regularidade",
        }
        tipo_label = tipo_labels.get(tipo, tipo)
        tipo_id = self._find_or_create_folder(tipo_label, iaudit_id)
        if not tipo_id:
            return None

        # CNPJ subfolder
        cnpj_id = self._find_or_create_folder(cnpj, tipo_id)
        return cnpj_id

    async def upload_pdf(
        self,
        pdf_url: str,
        tipo: str,
        cnpj: str,
        data: datetime | None = None,
    ) -> str | None:
        """
        Download PDF from URL and upload to Google Drive.

        Structure: IAudit/{tipo}/{CNPJ}/{data}_certidao.pdf

        Args:
            pdf_url: URL to download the PDF.
            tipo: Consultation type (cnd_federal, cnd_pr, fgts_regularidade).
            cnpj: CNPJ (digits only).
            data: Date for filename (defaults to now).

        Returns:
            Shareable Drive link or None if upload failed.
        """
        service = self._get_service()
        if not service:
            logger.warning("Google Drive not configured. Skipping PDF upload.")
            return None

        try:
            # Download PDF
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(pdf_url)
                response.raise_for_status()
                pdf_bytes = response.content

            # Build folder structure
            folder_id = self._build_folder_path(tipo, cnpj)
            if not folder_id:
                logger.error("Failed to create Drive folder structure.")
                return None

            # Build filename
            date_str = (data or datetime.now()).strftime("%Y-%m-%d_%H%M%S")
            filename = f"{date_str}_certidao.pdf"

            # Upload file
            file_metadata = {
                "name": filename,
                "parents": [folder_id],
            }
            media = MediaIoBaseUpload(
                io.BytesIO(pdf_bytes),
                mimetype="application/pdf",
                resumable=True,
            )
            file = (
                service.files()
                .create(body=file_metadata, media_body=media, fields="id,webViewLink")
                .execute()
            )

            # Make shareable
            service.permissions().create(
                fileId=file["id"],
                body={"type": "anyone", "role": "reader"},
            ).execute()

            link = file.get("webViewLink", "")
            logger.info(f"PDF uploaded to Drive: {filename} -> {link}")
            return link

        except Exception as e:
            logger.error(f"Google Drive upload failed: {e}")
            return None


# Module-level singleton
drive_service = GoogleDriveService()
