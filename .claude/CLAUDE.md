# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python 3.12 microservice that fetches Gamefound Spotlight API data and generates an RSS 2.0 feed. Deployed as a Docker container on Dokploy with a scheduled cron job (every 30 minutes). Supports two storage backends: GitHub Pages (gh-pages branch) or Supabase Storage.

## Build & Run

```bash
# Docker
docker-compose build
docker-compose up

# Local development
pip install -r requirements.txt
python server.py

# Generate RSS manually
python fetch_to_rss.py --api "https://gamefound.com/api/platformEvents/getSpotlightPlatformEvents?eventCount=15&olderThanEventId=&excludeDemotedProjects=true" \
  --out "gamefound_spotlight.xml" --title "Gamefound Spotlight (unofficial)"
```

No test suite or linter configured.

## Architecture

**Execution flow:** Flask server (`server.py`) receives `POST /run?token=CRON_TOKEN` → shells out to `run_cron.sh` → clones repo, runs `fetch_to_rss.py` to generate RSS XML → uploads via `upload_to_storage.py` (Supabase) or commits to gh-pages branch (GitHub Pages).

- **server.py** — Flask app with health check (`GET /`) and cron trigger (`POST /run`) endpoints
- **fetch_to_rss.py** — Fetches Gamefound JSON API, transforms to RSS 2.0 XML with proper date conversion (ISO 8601 → RFC 2822)
- **upload_to_storage.py** — Supabase storage uploader; compares content to avoid redundant uploads, enforces max file size
- **run_cron.sh** — Orchestrator script; handles git clone, RSS generation, and conditional upload/push
- **entrypoint.sh** — Docker entrypoint; converts env vars into `/app/.env.cron` for shell script sourcing

## Environment Variables

Copy `.env.example` to `.env`. Key variables:

- `REPO_SLUG` (required) — GitHub repo slug
- `CRON_TOKEN` — Secret for `/run` endpoint auth
- `GH_PAT` — GitHub token (for gh-pages mode)
- `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` — Supabase credentials (for Supabase mode)
- `PORT` — Flask port (default: 10000)

## Deployment

Dokploy-based. See `docs/DEPLOY.md` for setup steps. The container connects to `dokploy-network` (defined in docker-compose.yml).
