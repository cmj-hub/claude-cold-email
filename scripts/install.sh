#!/usr/bin/env bash
# Install cmj-hub/claude-cold-email into every detected agent harness.
# Path: npx skills add --all (Claude Code, Cursor, Codex, Grok, Copilot,
# Windsurf, Cline, OpenCode, Antigravity, Goose, Continue, Roo, and the rest of
# the skills CLI agent list).
set -euo pipefail

REPO="cmj-hub/claude-cold-email"

if command -v npx >/dev/null 2>&1; then
  echo "Installing $REPO via npx skills (all agents, global)..."
  npx -y skills add "$REPO" --all -g --copy --full-depth
  echo ""
  echo "Done. Restart the agent (Claude Code / Cursor / Codex / Grok / …)."
  echo "Project-local instead of global:"
  echo "  npx skills add $REPO --all --full-depth"
  exit 0
fi

echo "npx not found. Install Node 18+ and rerun, or use:"
echo "  npx skills add $REPO --all -g --full-depth"
exit 1
