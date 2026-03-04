# Deploy to Dokploy

## 1. Deploy the app

1. In Dokploy, create a new project and add a **Docker Compose** application.
2. Set Compose path to `./docker-compose.yml`, connect your repo and branch (e.g. `main`).
3. Configure environment variables from [../.env.example](../.env.example). Set them in Dokploy UI (or on the server in `.env`). Required:
   - `REPO_SLUG` — e.g. `yourname/rss-gamefound-spotlight`
   - `GH_PAT` — GitHub token with push access to the repo (secret)
   - `CRON_TOKEN` — random secret used to protect the `/run` endpoint (secret)
   - `GIT_USER_NAME`, `GIT_USER_EMAIL` — git identity for gh-pages commits
4. Optional: `RSS_OUTPUT_PATH`, `USE_DB`, `GF_API`, `PORT` (default `10000`).
5. Deploy. Ensure the service is on the `dokploy-network` (the compose file attaches it).
6. If you need a public URL, add a domain in Dokploy (Traefik) for this service and point it at the app port (e.g. `10000`).

## 2. Schedule Job (replace GitHub Actions cron)

1. In Dokploy, open **Schedule** and create a new job.
2. Type: **Application** (runs inside the app container).
3. Select the application (the service from step 1).
4. **Cron expression:** `*/30 * * * *` (every 30 minutes).
5. **Command:**
   ```bash
   curl -sS -X POST "http://localhost:${PORT:-10000}/run?token=$CRON_TOKEN" --max-time 300
   ```
   The container has `PORT` and `CRON_TOKEN` in its environment, so this will trigger the RSS generation and push to gh-pages.

## 3. Verify

- Call `GET https://your-app-url/` — should return `OK`.
- Call `POST https://your-app-url/run?token=YOUR_CRON_TOKEN` — should return `{"status":"ok"}` and update the gh-pages branch.
- After the first scheduled run, check that the RSS file on gh-pages is updated.
