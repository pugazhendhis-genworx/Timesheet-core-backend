"""
Google Cloud Storage service for uploading, downloading, and
generating signed URLs for email attachments.
"""

import datetime
import logging
import os

import google.auth
from google.auth import impersonated_credentials
from google.cloud import storage

from src.config.settings import settings

logger = logging.getLogger(__name__)

# ── Credentials ─────────────────────────────────────────

_source_credentials = None
_target_credentials = None
_storage_client = None


def _get_target_credentials():
    """
    Return impersonated credentials that can sign blobs for
    the target service account.  Cached at module level.
    """
    global _source_credentials, _target_credentials  # noqa: PLW0603

    if _target_credentials is not None:
        return _target_credentials

    _source_credentials, _ = google.auth.default()

    _target_credentials = impersonated_credentials.Credentials(
        source_credentials=_source_credentials,
        target_principal=settings.GCS_TARGET_SERVICE_ACCOUNT,
        target_scopes=[
            "https://www.googleapis.com/auth/devstorage.read_write",
            "https://www.googleapis.com/auth/iam",
        ],
        lifetime=3600,
    )

    logger.info(
        "Initialised impersonated credentials for %s",
        settings.GCS_TARGET_SERVICE_ACCOUNT,
    )
    return _target_credentials


def _get_storage_client() -> storage.Client:
    """Return a cached Storage client using impersonated credentials."""
    global _storage_client  # noqa: PLW0603

    if _storage_client is not None:
        return _storage_client

    creds = _get_target_credentials()
    _storage_client = storage.Client(
        project=settings.GCS_PROJECT_ID,
        credentials=creds,
    )
    return _storage_client


# ── Public helpers ──────────────────────────────────────


def _build_blob_name(file_name: str) -> str:
    """Build the full GCS object path: <prefix>/<filename>."""
    prefix = settings.GCS_BUCKET_PREFIX.strip("/")
    return f"{prefix}/{file_name}"


def upload_to_gcs(
    file_data: bytes,
    file_name: str,
    content_type: str = "application/octet-stream",
) -> str:
    """
    Upload raw bytes to GCS. Falls back to local attachments folder if GCS fails.

    Returns the ``gs://`` URI or the local path ``attachments/<file_name>``
    stored in the DB as ``file_path``.
    """
    try:
        client = _get_storage_client()
        bucket = client.bucket(settings.GCS_BUCKET_NAME)
        blob_name = _build_blob_name(file_name)
        blob = bucket.blob(blob_name)

        blob.upload_from_string(file_data, content_type=content_type)

        gcs_url = f"gs://{settings.GCS_BUCKET_NAME}/{blob_name}"
        logger.info("Uploaded %s → %s", file_name, gcs_url)
        return gcs_url
    except Exception as e:
        logger.warning(
            "GCS upload failed for %s: %s. Falling back to local storage.", file_name, e
        )
        os.makedirs("attachments", exist_ok=True)
        local_path = os.path.join("attachments", file_name)
        with open(local_path, "wb") as f:
            f.write(file_data)
        logger.info("Saved %s locally → %s", file_name, local_path)
        return local_path


def download_from_gcs(file_path: str) -> bytes:
    """
    Download file bytes from a ``gs://`` URI or local fallback path.
    If both GCS and local fallback fail, raises an error.
    """
    if file_path.startswith("gs://"):
        try:
            bucket_name, blob_name = _parse_gs_uri(file_path)
            client = _get_storage_client()
            bucket = client.bucket(bucket_name)
            blob = bucket.blob(blob_name)

            data = blob.download_as_bytes()
            logger.debug("Downloaded %d bytes from %s", len(data), file_path)
            return data
        except Exception as e:
            logger.warning(
                "Failed to download from GCS (%s): %s. Falling back to local storage.",
                file_path,
                e,
            )
            file_name = file_path.split("/")[-1]
            local_path = os.path.join("attachments", file_name)
    else:
        local_path = file_path

    try:
        with open(local_path, "rb") as f:
            data = f.read()
            logger.debug(
                "Downloaded %d bytes from local path %s", len(data), local_path
            )
            return data
    except Exception as e:
        logger.error("Failed to download from local storage (%s): %s", local_path, e)
        raise RuntimeError(f"Both GCS and local fallback failed for {file_path}") from e


def generate_signed_url(
    gcs_url: str,
    expiry_hours: int | None = None,
) -> str:
    """
    Generate a V4 signed URL for a GCS object.

    ``expiry_hours`` defaults to ``settings.GCS_SIGNED_URL_EXPIRY_HOURS``
    (configured via env, default 4 h).
    """
    if expiry_hours is None:
        expiry_hours = settings.GCS_SIGNED_URL_EXPIRY_HOURS

    bucket_name, blob_name = _parse_gs_uri(gcs_url)
    client = _get_storage_client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(blob_name)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(hours=expiry_hours),
        method="GET",
        credentials=_get_target_credentials(),
    )
    logger.debug("Signed URL generated for %s (expires in %dh)", gcs_url, expiry_hours)
    return url


# ── Internal helpers ────────────────────────────────────


def _parse_gs_uri(gcs_url: str) -> tuple[str, str]:
    """
    Parse ``gs://bucket/path/to/object`` into ``(bucket, path/to/object)``.
    """
    if not gcs_url.startswith("gs://"):
        raise ValueError(f"Invalid GCS URI (must start with gs://): {gcs_url}")

    without_scheme = gcs_url[len("gs://") :]
    parts = without_scheme.split("/", 1)
    if len(parts) != 2 or not parts[1]:
        raise ValueError(f"Invalid GCS URI (missing object path): {gcs_url}")

    return parts[0], parts[1]
