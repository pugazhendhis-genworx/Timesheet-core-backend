import os
import uuid

from google.cloud import storage

PROJECT_ID = os.getenv("GCS_PROJECT_ID")
BUCKET_NAME = os.getenv("GCS_BUCKET_NAME")
PREFIX = os.getenv("GCS_BUCKET_PREFIX", "default")

client = storage.Client(project=PROJECT_ID)
bucket = client.bucket(BUCKET_NAME)


def upload_file(file_bytes: bytes, filename: str, content_type: str):
    unique_id = str(uuid.uuid4())

    blob_name = f"{PREFIX}/emails/attachments/{unique_id}_{filename}"

    blob = bucket.blob(blob_name)

    blob.upload_from_string(file_bytes, content_type=content_type)
    blob.make_public()

    return blob.public_url, blob_name
