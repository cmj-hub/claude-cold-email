#!/usr/bin/env bash
# install.sh — Install claude-cold-email skill ecosystem
# Usage: curl -fsSL https://raw.githubusercontent.com/cmj-hub/claude-cold-email/main/install.sh | bash

set -euo pipefail

REPO_URL="https://github.com/cmj-hub/claude-cold-email"
SKILLS_DIR="${HOME}/.claude/skills"
AGENTS_DIR="${HOME}/.claude/agents"

check_prerequisites() {
    if ! command -v git >/dev/null 2>&1; then
        echo "ERROR: git is required but not installed." >&2
        exit 1
    fi
}

main() {
    echo "Installing claude-cold-email..."
    echo ""

    check_prerequisites

    mkdir -p "$SKILLS_DIR"
    mkdir -p "$AGENTS_DIR"

    TEMP_DIR=$(mktemp -d)
    trap 'rm -rf "$TEMP_DIR"' EXIT

    echo "Cloning repository..."
    git clone --depth 1 "$REPO_URL" "$TEMP_DIR" >/dev/null 2>&1

    echo "Installing main orchestrator skill (cold-email/)..."
    rm -rf "$SKILLS_DIR/cold-email"
    cp -r "$TEMP_DIR/cold-email" "$SKILLS_DIR/"
    echo "  ✓ cold-email"

    echo "Installing sub-skills..."
    for skill_dir in "$TEMP_DIR/skills"/cold-email-*; do
        if [[ -d "$skill_dir" ]]; then
            skill_name=$(basename "$skill_dir")
            rm -rf "${SKILLS_DIR:?}/$skill_name"
            cp -r "$skill_dir" "$SKILLS_DIR/"
            echo "  ✓ $skill_name"
        fi
    done

    echo "Installing agents..."
    for agent_file in "$TEMP_DIR/agents"/cold-email-*.md; do
        if [[ -f "$agent_file" ]]; then
            agent_name=$(basename "$agent_file" .md)
            cp "$agent_file" "$AGENTS_DIR/"
            echo "  ✓ $agent_name"
        fi
    done

    echo ""
    echo "Done. Restart Claude Code (or any open MCP-aware client) to pick up the new skill."
    echo ""
    echo "Try it:"
    echo "  > Write a cold email to <name>, <role> at <company>. They just <signal>."
    echo ""
    echo "Or:"
    echo "  > Audit our outbound program"
    echo ""
    echo "Course:  https://jaymountconsulting.com/learn/courses/cold-email-outreach-craft"
    echo "Source:  $REPO_URL"
}

main "$@"
