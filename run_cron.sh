#!/usr/bin/env bash
set -euo pipefail

log() { echo "[$(date -u +'%Y-%m-%d %H:%M:%S UTC')] $*"; }
trap 'log "ERROR: script failed at line $LINENO (exit code $?)"' ERR

if [[ -f /app/.env.cron ]]; then
  set -a
  # shellcheck source=/dev/null
  . /app/.env.cron
  set +a
fi

log "Cron job started"

: "${REPO_SLUG:?REPO_SLUG is required, e.g. yourname/yourrepo}"
: "${CODE_BRANCH:=main}"
: "${RSS_OUTPUT_PATH:=gamefound_spotlight.xml}"
: "${GIT_USER_NAME:=Render Bot}"
: "${GIT_USER_EMAIL:=noreplay@renderbot.com}"
: "${USE_DB:=false}"

if [[ -z "${SUPABASE_URL:-}" ]]; then
  : "${GH_PAT:?GH_PAT (GitHub token) is required when not using Supabase Storage}"
fi
REPO_HTTPS="https://${GH_PAT:-x}@github.com/${REPO_SLUG}.git"

WORKDIR="$(mktemp -d)"
CODE_DIR="${WORKDIR}/code"
OUTPUT_DIR="${WORKDIR}/output"
DB_DIR="${WORKDIR}/db"

mkdir -p "$OUTPUT_DIR" "$DB_DIR"

log "Cloning repo ${REPO_SLUG} (branch: ${CODE_BRANCH})"
if [[ -n "${SUPABASE_URL:-}" ]]; then
  git clone --depth 1 --branch "$CODE_BRANCH" "https://github.com/${REPO_SLUG}.git" "$CODE_DIR"
else
  git config --global user.name "$GIT_USER_NAME"
  git config --global user.email "$GIT_USER_EMAIL"
  git clone --depth 1 --branch "$CODE_BRANCH" "$REPO_HTTPS" "$CODE_DIR"
fi
cd "$CODE_DIR"

API_ARG=()
if [[ -n "${GF_API:-}" ]]; then
  API_ARG=(--api "$GF_API")
fi

log "Generating RSS feed"
python3 fetch_to_rss.py "${API_ARG[@]}" --out "$OUTPUT_DIR/$(basename "$RSS_OUTPUT_PATH")"

if [[ -n "${SUPABASE_URL:-}" ]]; then
  log "Uploading to Supabase Storage"
  python3 upload_to_storage.py "$OUTPUT_DIR/$(basename "$RSS_OUTPUT_PATH")"
else
  GH_PAGES_DIR="${WORKDIR}/gh-pages"
  git init "$GH_PAGES_DIR"
  cd "$GH_PAGES_DIR"

  # Download current file to compare (skip if branch doesn't exist yet)
  CHANGED=true
  if git ls-remote --exit-code --heads "$REPO_HTTPS" gh-pages >/dev/null 2>&1; then
    if git fetch "$REPO_HTTPS" gh-pages && git show FETCH_HEAD:"$RSS_OUTPUT_PATH" > "${WORKDIR}/old_rss" 2>/dev/null; then
      if diff -q "${WORKDIR}/old_rss" "$OUTPUT_DIR/$(basename "$RSS_OUTPUT_PATH")" >/dev/null 2>&1; then
        CHANGED=false
      fi
    fi
  fi

  if [[ "$CHANGED" == "false" ]]; then
    log "No RSS changes to commit for gh-pages."
  else
    git checkout --orphan gh-pages
    mkdir -p "$(dirname "$RSS_OUTPUT_PATH")"
    cp -f "$OUTPUT_DIR/$(basename "$RSS_OUTPUT_PATH")" "$RSS_OUTPUT_PATH"
    git add "$RSS_OUTPUT_PATH"
    git commit -m "update RSS: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
    git push --force "$REPO_HTTPS" gh-pages
    log "Pushed RSS update to gh-pages (single-commit overwrite)"
  fi
fi

if [[ "$USE_DB" == "true" ]] && [[ -z "${SUPABASE_URL:-}" ]]; then
  DB_SOURCE="${CODE_DIR}/data/runtime.sqlite"
  if [[ -f "$DB_SOURCE" ]]; then
    RUNTIME_DB_DIR="${WORKDIR}/runtime-db"
    git clone --no-checkout "$REPO_HTTPS" "$RUNTIME_DB_DIR"
    cd "$RUNTIME_DB_DIR"

    if git ls-remote --exit-code --heads origin runtime-db >/dev/null 2>&1; then
      git fetch origin runtime-db:runtime-db
      git checkout runtime-db
    else
      git checkout --orphan runtime-db
      rm -rf .
    fi

    mkdir -p data
    cp -f "$DB_SOURCE" data/runtime.sqlite
    git add data/runtime.sqlite
    if git diff --cached --quiet; then
      log "No DB changes to commit for runtime-db."
    else
      git commit -m "update DB: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
      git push origin runtime-db
      log "Pushed DB update to runtime-db"
    fi
  else
    log "WARNING: USE_DB=true but DB file not found (${DB_SOURCE}). Skipping runtime-db push."
  fi
fi

log "Done."
