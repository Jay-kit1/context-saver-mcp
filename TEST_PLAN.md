# Context Saver MCP Test Plan

## Goals

Verify that Context Saver MCP works as:

- a local project/file/archive context packer
- a real Codex MCP server
- a DeepSeek-powered compression layer
- an optional AnySearch-style web search and URL extraction layer

## Local Tests

```bash
.venv/bin/python -m pytest
.venv/bin/python /Users/kukudejie/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/context-saver-mcp
```

Expected:

- all tests pass
- skill validation prints `Skill is valid!`

## MCP Server Smoke Test

```bash
.venv/bin/python - <<'PY'
import anyio
from pathlib import Path
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    params = StdioServerParameters(
        command=str(Path(".venv/bin/context-saver-mcp").resolve()),
        args=[],
    )
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print([tool.name for tool in tools.tools])

anyio.run(main)
PY
```

Expected tool:

- `context_saver_prepare`

Expected modes through the same tool:

- `kind="project"`
- `kind="search"`
- `kind="url"`
- `kind="doctor"`

## DeepSeek Verification

Run a tiny `context_saver_prepare` call with `use_deepseek=true`.

Expected:

- `deepseek_used` is `true`
- `deepseek_usage.total_tokens` is present
- DeepSeek platform usage increases after the provider delay

## Optional AnySearch Verification

Set either:

```bash
ANYSEARCH_ENABLED=true
```

or:

```bash
ANYSEARCH_API_KEY=<your_key>
```

Then run:

```bash
csp search "capital of France" --max-results 2
```

Expected:

- search pack is generated
- AnySearch results are included when the endpoint is reachable
- local fallback appears clearly if the endpoint is unavailable

## Install Verification

```bash
bash scripts/install-codex-skill.sh
```

Expected:

- skill installed under `${CODEX_HOME:-$HOME/.codex}/skills/context-saver-mcp`
- `runtime.conf` is written in the installed skill directory
- `${CODEX_HOME:-$HOME/.codex}/config.toml` contains `[mcp_servers.context_saver]`
- backups are created before modifying `AGENTS.md` or `config.toml`
