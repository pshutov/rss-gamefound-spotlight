#!/usr/bin/env bash
set -e
vars=(REPO_SLUG CODE_BRANCH RSS_OUTPUT_PATH GIT_USER_NAME GIT_USER_EMAIL USE_DB GH_PAT CRON_TOKEN GF_API PORT
  SUPABASE_URL SUPABASE_SERVICE_ROLE_KEY SUPABASE_KEY SUPABASE_BUCKET SUPABASE_STORAGE_PATH SUPABASE_MAX_FILE_BYTES)
: > /app/.env.cron
for key in "${vars[@]}"; do
  val="${!key:-}"
  [[ -z "$val" ]] && continue
  escaped="${val//\'/\'\\\'\'}"
  echo "export $key='$escaped'" >> /app/.env.cron
done
exec "$@"
