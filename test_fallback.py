import os
import sys

sys.path.insert(0, os.path.abspath("."))

from src.core.services.gcs_service import download_from_gcs, upload_to_gcs

try:
    print("Testing upload_to_gcs fallback...")
    file_path = upload_to_gcs(b"hello world", "test_file.txt", "text/plain")
    print(f"Uploaded to: {file_path}")

    print("Testing download_from_gcs fallback...")
    data = download_from_gcs(file_path)
    print(f"Downloaded data: {data}")

    assert data == b"hello world"
    print("Fallback logic works perfectly!")
except Exception as e:
    print(f"Test failed: {e}")
