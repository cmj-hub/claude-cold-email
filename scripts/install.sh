#!/usr/bin/env bash
# Install cmj-hub/claude-cold-email into every detected agent harness.
# Primary path: npx skills add --all (Claude Code, Cursor, Codex, Grok, Copilot,
# Windsurf, Cline, OpenCode, Antigravity, Goose, Continue, Roo, and the rest of
# the skills CLI agent list). Fallback copies SKILL.md trees into well-known dirs.
set -euo pipefail

REPO="cmj-hub/claude-cold-email"
ORCH="cold-email"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Root installer lives at repo root; scripts/installer lives one level down.
if [[ "$(basename "$ROOT")" == "scripts" ]]; then
  PACK="$(cd "$ROOT/.." && pwd)"
else
  PACK="$ROOT"
fi

if command -v npx >/dev/null 2>&1; then
  echo "Installing $REPO via npx skills (all agents, global)..."
  npx -y skills add "$REPO" --all -g --copy --full-depth
  echo ""
  echo "Done. Restart the agent (Claude Code / Cursor / Codex / Grok / …)."
  echo "Project-local instead of global:"
  echo "  npx skills add $REPO --all --full-depth"
  exit 0
fi

echo "npx not found — falling back to copying skill folders."

if ! command -v git >/dev/null 2>&1; then
  echo "ERROR: git is required for the fallback installer." >&2
  exit 1
fi

SRC="$PACK"
if [[ ! -d "$SRC/skills" && ! -d "$SRC/$ORCH" ]]; then
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  git clone --depth 1 "https://github.com/$REPO.git" "$TMP/src" >/dev/null 2>&1
  SRC="$TMP/src"
fi

DESTS=(
  "$HOME/.claude/skills"
  "$HOME/.agents/skills"
  "$HOME/.cursor/skills"
  "$HOME/.codex/skills"
  "$HOME/.grok/skills"
  "$HOME/.github/skills"
  "$HOME/.copilot/skills"
  "$HOME/.windsurf/skills"
  "$HOME/.cline/skills"
  "$HOME/.opencode/skills"
  "$HOME/.goose/skills"
  "$HOME/.continue/skills"
  "$HOME/.gemini/antigravity/skills"
  "$HOME/.roo/skills"
  "$HOME/.crush/skills"
  "$HOME/.openclaw/skills"
  "$HOME/.hermes/skills"
)

copy_tree() {
  local from="$1" to="$2"
  [[ -e "$from" ]] || return 0
  mkdir -p "$(dirname "$to")"
  rm -rf "$to"
  cp -R "$from" "$to"
  echo "  → $to"
}

for dest in "${DESTS[@]}"; do
  mkdir -p "$dest"
  if [[ -d "$SRC/$ORCH" ]]; then
    copy_tree "$SRC/$ORCH" "$dest/$ORCH"
  fi
  if [[ -d "$SRC/skills" ]]; then
    for skill_dir in "$SRC/skills"/*; do
      [[ -d "$skill_dir" ]] || continue
      name="$(basename "$skill_dir")"
      copy_tree "$skill_dir" "$dest/$name"
    done
  fi
done

if [[ -d "$SRC/agents" ]]; then
  mkdir -p "$HOME/.claude/agents"
  cp -R "$SRC/agents/." "$HOME/.claude/agents/" 2>/dev/null || true
fi

echo ""
echo "Done (fallback copy). Restart the agent."
echo "Prefer installing Node so next time this can use: npx skills add $REPO --all -g --full-depth"
