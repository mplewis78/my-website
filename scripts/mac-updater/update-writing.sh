#!/bin/bash
# Weekly refresh of writing.html from Substack, run on Mike's Mac by launchd.
# Substack blocks GitHub's servers and the free relays, but not home internet,
# so this runs here instead of in GitHub Actions.
#
# Works in its own clone (~/.website-updater) so it never touches the folder
# you edit in, and so macOS doesn't block it from ~/Documents.

export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
WORKDIR="$HOME/.website-updater"
REPO="https://github.com/mplewis78/my-website.git"

echo "=== $(date) ==="
set -e
if [ ! -d "$WORKDIR/.git" ]; then
  git clone --branch master "$REPO" "$WORKDIR"
fi
cd "$WORKDIR"
git fetch origin master
git reset --hard origin/master
set +e

python3 scripts/update_writing.py
status=$?

git add writing.html
if git diff --staged --quiet; then
  echo "No changes to commit."
else
  git commit -m "chore: auto-update writing page from Substack feeds" && git push origin master || status=1
fi
exit $status
