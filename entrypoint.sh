#!/usr/bin/env bash
set -e
env | grep -E '^(REPO_SLUG|CODE_BRANCH|RSS_OUTPUT_PATH|GIT_USER_NAME|GIT_USER_EMAIL|USE_DB|GH_PAT|CRON_TOKEN|GF_API|SUPABASE_|PORT)=' > /app/.env.cron 2>/dev/null || true
exec "$@"
