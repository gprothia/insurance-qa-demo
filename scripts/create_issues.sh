#!/usr/bin/env bash
# Creates the demo user stories as GitHub issues from specs/*.md.
# Requires: gh auth login (once). Safe to re-run: skips issues whose title already exists.
#
#   ./scripts/create_issues.sh [owner/repo]
set -euo pipefail
REPO="${1:-gprothia/insurance-qa-demo}"
cd "$(dirname "$0")/.."

gh label create story --repo "$REPO" --color 1D76DB --description "User story with acceptance criteria" --force >/dev/null
gh label create spec-driven-tests --repo "$REPO" --color 0E8A16 --description "Generate acceptance tests from this story" --force >/dev/null

for spec in specs/INS-*.md; do
  # Title comes from the spec's first heading, e.g. "INS-101: Online auto insurance quote".
  title="$(head -1 "$spec" | sed 's/^# //')"
  if gh issue list --repo "$REPO" --state all --search "\"$title\" in:title" --json title -q '.[].title' | grep -Fxq "$title"; then
    echo "exists: $title"
    continue
  fi
  # Drop the heading line; GitHub shows the title separately.
  tail -n +2 "$spec" | gh issue create --repo "$REPO" --title "$title" --body-file - \
    --label story --label spec-driven-tests
done

gh issue list --repo "$REPO" --label story
