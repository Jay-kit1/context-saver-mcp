#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CODEX_HOME="${CODEX_HOME:-$HOME/.codex}"
SKILL_SOURCE="$ROOT_DIR/skills/context-saver-mcp"
SKILL_TARGET="$CODEX_HOME/skills/context-saver-mcp"
AGENTS_FILE="$CODEX_HOME/AGENTS.md"
AGENTS_BACKUP="$CODEX_HOME/AGENTS.md.context-saver-mcp.bak"
AGENTS_START="<!-- context-saver-mcp:start -->"
AGENTS_END="<!-- context-saver-mcp:end -->"

if [ ! -d "$SKILL_SOURCE" ]; then
  echo "Missing skill source: $SKILL_SOURCE" >&2
  exit 1
fi

mkdir -p "$CODEX_HOME/skills"
rm -rf "$SKILL_TARGET"
cp -R "$SKILL_SOURCE" "$SKILL_TARGET"

mkdir -p "$CODEX_HOME"
touch "$AGENTS_FILE"
cp "$AGENTS_FILE" "$AGENTS_BACKUP"
python3 - "$AGENTS_FILE" "$AGENTS_START" "$AGENTS_END" <<'PY'
from __future__ import annotations

from pathlib import Path
import sys

path = Path(sys.argv[1])
start = sys.argv[2]
end = sys.argv[3]
block = f"""{start}
## Context Saver MCP default

- Use `$context-saver-mcp` proactively before broad or expensive local work: repo orientation, coding in a project, bug fixes, reviews, debugging, multi-file changes, reading/searching many files, extracting files, or unpacking archives.
- Treat it as the default context-preparation step when a task may otherwise require loading many files into Codex. Skip only for clearly tiny one-command or single-file tasks.
- Never include `.env`, API keys, `.venv`, `.tools`, caches, or generated `outputs/*.md` in uploaded or committed context.
{end}
"""
text = path.read_text(encoding="utf-8") if path.exists() else ""
if start in text and end in text:
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    text = before.rstrip() + "\n\n" + block + after.lstrip()
else:
    text = text.rstrip() + ("\n\n" if text.strip() else "") + block
path.write_text(text.rstrip() + "\n", encoding="utf-8")
PY

echo "Installed Context Saver MCP skill to: $SKILL_TARGET"
echo "Implicit invocation is enabled in agents/openai.yaml."
echo "Global default instruction installed in: $AGENTS_FILE"
echo "Previous AGENTS.md backup saved to: $AGENTS_BACKUP"
