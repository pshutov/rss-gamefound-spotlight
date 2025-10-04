#!/usr/bin/env bash
set -euo pipefail

: "${REPO_SLUG:?REPO_SLUG is required, e.g. yourname/yourrepo}"
: "${CODE_BRANCH:=main}"
: "${RSS_OUTPUT_PATH:=gamefound_spotlight.xml}"
: "${GIT_USER_NAME:=Render Bot}"
: "${GIT_USER_EMAIL:=noreplay@renderbot.com}"
: "${USE_DB:=false}"
: "${GH_PAT:?GH_PAT (GitHub token) is required}"

REPO_HTTPS="https://${GH_PAT}@github.com/${REPO_SLUG}.git"

WORKDIR="$(mktemp -d)"
CODE_DIR="${WORKDIR}/code"
OUTPUT_DIR="${WORKDIR}/output"
DB_DIR="${WORKDIR}/db"

mkdir -p "$OUTPUT_DIR" "$DB_DIR"

git config --global user.name "$GIT_USER_NAME"
git config --global user.email "$GIT_USER_EMAIL"

git clone --depth 1 --branch "$CODE_BRANCH" "https://github.com/${REPO_SLUG}.git" "$CODE_DIR"
cd "$CODE_DIR"

API_ARG=()
if [[ -n "${GF_API:-}" ]]; then
  API_ARG=(--api "$GF_API")
fi

python3 -V
python3 fetch_to_rss.py "${API_ARG[@]}" --out "$OUTPUT_DIR/$(basename "$RSS_OUTPUT_PATH")"

GH_PAGES_DIR="${WORKDIR}/gh-pages"
git clone --no-checkout "$REPO_HTTPS" "$GH_PAGES_DIR"
cd "$GH_PAGES_DIR"

if git ls-remote --exit-code --heads origin gh-pages >/dev/null 2>&1; then
  git fetch origin gh-pages:gh-pages
  git checkout gh-pages
else
  git checkout --orphan gh-pages
  rm -rf .
fi

mkdir -p "$(dirname "$RSS_OUTPUT_PATH")"
cp -f "$OUTPUT_DIR/$(basename "$RSS_OUTPUT_PATH")" "$RSS_OUTPUT_PATH"

git add "$RSS_OUTPUT_PATH"
if git diff --cached --quiet; then
  echo "No RSS changes to commit for gh-pages."
else
  git commit -m "update RSS: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
  git push origin gh-pages
fi

if [[ "$USE_DB" == "true" ]]; then
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
      echo "No DB changes to commit for runtime-db."
    else
      git commit -m "update DB: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
      git push origin runtime-db
    fi
  else
    echo "USE_DB=true but DB file not found (${DB_SOURCE}). Skipping runtime-db push."
  fi
fi

echo "Done."
