#!/usr/bin/env python3
"""Upload a file to Supabase Storage. Used when SUPABASE_* env vars are set instead of pushing to gh-pages."""

import os
import re
import sys
import logging

logging.basicConfig(format="%(asctime)s %(levelname)s %(message)s", level=logging.INFO)
log = logging.getLogger(__name__)


def normalize_rss_for_compare(xml_bytes: bytes) -> str:
    """Strip lastBuildDate so comparison ignores timestamp-only changes."""
    text = xml_bytes.decode("utf-8", errors="replace")
    return re.sub(r"<lastBuildDate>[^<]*</lastBuildDate>", "<lastBuildDate></lastBuildDate>", text)

def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    bucket = os.getenv("SUPABASE_BUCKET", "rss")
    storage_path = os.getenv("SUPABASE_STORAGE_PATH", "gamefound_spotlight.xml")
    max_bytes = int(os.getenv("SUPABASE_MAX_FILE_BYTES", "1048576"))

    if not url or not key:
        log.error("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) are required.")
        sys.exit(1)

    if len(sys.argv) < 2:
        log.error("Usage: upload_to_storage.py <local_file_path>")
        sys.exit(1)
    local_path = sys.argv[1]
    if not os.path.isfile(local_path):
        log.error("File not found: %s", local_path)
        sys.exit(1)

    size = os.path.getsize(local_path)
    if size > max_bytes:
        log.error("File size %d exceeds limit %d (SUPABASE_MAX_FILE_BYTES).", size, max_bytes)
        sys.exit(1)

    log.info("Preparing upload: %s (%d bytes) -> %s/%s", local_path, size, bucket, storage_path)

    from supabase import create_client
    client = create_client(url, key)
    with open(local_path, "rb") as f:
        data = f.read()

    try:
        existing = client.storage.from_(bucket).download(storage_path)
        if normalize_rss_for_compare(existing) == normalize_rss_for_compare(data):
            log.info("No RSS changes, skip upload.")
            return
        log.info("RSS content changed, will upload.")
    except Exception as e:
        log.warning("Could not download existing file for comparison: %s. Will upload new file.", e)

    client.storage.from_(bucket).upload(
        storage_path,
        data,
        file_options={"content-type": "application/rss+xml", "upsert": True},
    )
    log.info("Uploaded to %s/%s (%d bytes).", bucket, storage_path, size)


if __name__ == "__main__":
    main()
