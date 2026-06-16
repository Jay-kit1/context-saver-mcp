#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILL_SOURCE="$ROOT_DIR/skills/context-saver-mcp"
SKILL_TARGET="$CODEX_HOME/skills/context-saver-mcp"

if [ ! -d "$SKILL_SOURCE" ]; then
  echo "Missing skill source: $SKILL_SOURCE" >&2
  exit 1
fi

mkdir -p "$CODEX_HOME/skills"
rm -rf "$SKILL_TARGET"
cp -R "$SKILL_SOURCE" "$SKILL_TARGET"

echo "Installed Context Saver MCP skill to: $SKILL_TARGET"
echo "Implicit invocation is enabled in agents/openai.yaml."
