#!/usr/bin/env bash
# Back up the revenue-engine data directory (lead history, config, outreach) to its
# private git remote. Safe to call on every run: no-ops cleanly if the data dir isn't a
# git repo or has no 'origin' remote, and skips the push when nothing changed.
#
# Usage: backup-data.sh [DATA_DIR] [commit message]
set -euo pipefail

DIR="${1:-$HOME/.revenue-engine-imparatta}"
MSG="${2:-revenue-engine run}"

cd "$DIR" 2>/dev/null || { echo "backup: data dir not found ($DIR)"; exit 0; }
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || { echo "backup: $DIR is not a git repo - skipping (run 'git init' + add a private remote to enable)"; exit 0; }
git remote get-url origin >/dev/null 2>&1 || { echo "backup: no 'origin' remote - skipping"; exit 0; }

git add -A
if git diff --cached --quiet; then
  echo "backup: no changes to push"
  exit 0
fi

git commit -q -m "$MSG"
git push -q origin HEAD
echo "backup: pushed to $(git remote get-url origin)"
