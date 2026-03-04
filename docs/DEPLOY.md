# Deploy to Dokploy

## 1. Deploy the app

1. In Dokploy, create a new project and add a **Docker Compose** application.
2. Set Compose path to `./docker-compose.yml`, connect your repo and branch (e.g. `main`).
3. Configure environment variables from [../.env.example](../.env.example). Set them in Dokploy UI (or on the server in `.env`).
   - **Required:** `REPO_SLUG`. `CRON_TOKEN` only if you trigger `/run` manually or via webhook (not needed when Schedule Job runs the script directly).
   - **When using Supabase Storage (recommended, no git push):** `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY` (or `SUPABASE_KEY`), and optionally `SUPABASE_BUCKET`, `SUPABASE_STORAGE_PATH`, `SUPABASE_MAX_FILE_BYTES`. You do **not** need `GH_PAT`.
   - **When using gh-pages:** `GH_PAT` (secret), `GIT_USER_NAME`, `GIT_USER_EMAIL`.
4. Optional: `RSS_OUTPUT_PATH`, `USE_DB`, `GF_API`, `PORT` (default `10000`).
5. Deploy. Ensure the service is on the `dokploy-network` (the compose file attaches it).
6. If you need a public URL for the app, add a domain in Dokploy (Traefik) for this service and point it at the app port (e.g. `10000`).

## 2. Supabase Storage (optional — store RSS in bucket instead of gh-pages)

1. In [Supabase](https://supabase.com) → **Storage** → **New bucket** (e.g. name `rss`).
2. Make the bucket **Public** so the RSS feed URL is readable without auth.
3. Optionally set a **file size limit** for the bucket (Dashboard → Storage → bucket → Settings) to cap storage use; 1–5 MB is enough for an RSS file.
4. Set env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `SUPABASE_BUCKET` (e.g. `rss`). The app will upload the generated XML to this bucket and skip pushing to GitHub.
5. Public feed URL: `https://<project-ref>.supabase.co/storage/v1/object/public/<bucket>/<SUPABASE_STORAGE_PATH>` (e.g. `.../rss/gamefound_spotlight.xml`).

## 3. Schedule Job (replace GitHub Actions cron)

1. In Dokploy, open **Schedule** and create a new job.
2. Type: **Application** (runs inside the app container).
3. Select the application (the service from step 1).
4. **Cron expression:** `*/30 * * * *` (every 30 minutes).
5. **Command** — run the script directly (no URL, no token):
   ```bash
   bash /app/run_cron.sh
   ```
   Required env vars (e.g. `REPO_SLUG`, Supabase or `GH_PAT`) must be set in the application's Environment in Dokploy so the container has them at startup; the entrypoint saves them for the Schedule Job. If you see "REPO_SLUG is required", add `REPO_SLUG=yourname/rss-gamefound-spotlight` (and other vars) in the app's Environment.

   Alternatively, to trigger via HTTP (e.g. from another service):  
   `curl -sS -X POST "http://localhost:${PORT:-10000}/run?token=$CRON_TOKEN" --max-time 300`

## 4. Verify

- Call `GET https://your-app-url/` — should return `OK`.
- Call `POST https://your-app-url/run?token=YOUR_CRON_TOKEN` — should return `{"status":"ok"}`.
- If using Supabase: open the bucket’s public URL and confirm the RSS XML is updated.
- If using gh-pages: confirm the branch and RSS file are updated.
