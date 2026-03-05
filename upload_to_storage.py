#!/usr/bin/env python3
"""Upload a file to Supabase Storage. Used when SUPABASE_* env vars are set instead of pushing to gh-pages."""

import os
import sys

def main():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
    bucket = os.getenv("SUPABASE_BUCKET", "rss")
    storage_path = os.getenv("SUPABASE_STORAGE_PATH", "gamefound_spotlight.xml")
    max_bytes = int(os.getenv("SUPABASE_MAX_FILE_BYTES", "1048576"))

    if not url or not key:
        print("SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY (or SUPABASE_KEY) are required.", file=sys.stderr)
        sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: upload_to_storage.py <local_file_path>", file=sys.stderr)
        sys.exit(1)
    local_path = sys.argv[1]
    if not os.path.isfile(local_path):
        print(f"File not found: {local_path}", file=sys.stderr)
        sys.exit(1)

    size = os.path.getsize(local_path)
    if size > max_bytes:
        print(f"File size {size} exceeds limit {max_bytes} (SUPABASE_MAX_FILE_BYTES).", file=sys.stderr)
        sys.exit(1)

    from supabase import create_client
    client = create_client(url, key)
    with open(local_path, "rb") as f:
        data = f.read()

    try:
        existing = client.storage.from_(bucket).download(storage_path)
        if existing == data:
            print("No RSS changes, skip upload.")
            return
    except Exception:
        pass

    client.storage.from_(bucket).upload(
        storage_path,
        data,
        file_options={"content-type": "application/rss+xml", "upsert": True},
    )
    print(f"Uploaded to {bucket}/{storage_path} ({size} bytes).")


if __name__ == "__main__":
    main()
