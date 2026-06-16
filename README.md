# Context Saver MCP

Stop wasting expensive coding-agent tokens on web search, long files, archives and oversized project context.

Context Saver MCP is a local search, file-extraction, archive-reading, careful-review and context-compression proxy for Codex, Claude Code, Qwen Code, Cline and Aider. It uses low-cost models such as DeepSeek V4 Flash to search, extract and compress useful context, and switches to DeepSeek V4 Pro for important, high-risk or careful-review tasks.

Flash may support a 600,000-token context window and Pro may support a 1,000,000-token context window, but these are maximum limits, not default targets. Context Saver uses smaller internal budgets by default, such as 64k for Flash normal tasks and 240k for careful review, then applies layered summarization to keep both DeepSeek and coding-agent token usage under control.

The goal is simple: keep expensive coding-agent tokens for coding, not searching, reading huge files or unpacking noisy archives. Compression should remove noise, not important details.

## Pain Points

Coding agents often burn premium tokens and search quota on repetitive web search, long files, logs, source files, archives and full repository scans. Context Saver MCP prepares short, clean Context Packs first so the coding agent can focus on code changes, execution and verification.

## Core Design

- Default Flash low-cost routing for ordinary work.
- Important, high-risk or careful-review tasks automatically use Pro.
- Flash context window: 600k tokens. Pro context window: 1000k tokens.
- Context windows are upper limits, not a reason to fill the prompt.
- Default internal budgets: Flash 64k, Pro 160k, careful-review 240k, no-compress 320k.
- Chunking and budget decisions are token-based, not character-based.
- Supports search, file extraction, archive reading, project scan and careful review.
- Outputs Codex Context Pack, Search Pack, Extract Pack, Archive Pack, Review Pack and Project Scan Pack.

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then confirm the CLI:

```bash
csp --help
```

## Install As A Codex Skill

This repository includes the Codex skill definition under `skills/context-saver-mcp`.
Install or refresh it locally with:

```bash
bash scripts/install-codex-skill.sh
```

The skill is installed to `${CODEX_HOME:-$HOME/.codex}/skills/context-saver-mcp` and has implicit invocation enabled, so Codex can automatically use it for context packs, archive packs, review packs, file extraction and project scans.

## Environment

Create a private `.env` from the example:

```bash
cp .env.example .env
```

Set `DEEPSEEK_API_KEY` in `.env`. Never commit API keys. This repository ignores `.env`, `.env.*` except `.env.example`, and generated `outputs/*.md`.

You can also use the interactive setup command:

```bash
csp configure
```

It asks for your DeepSeek API key with hidden input and saves it to local `.env`.

Check whether the key is configured:

```bash
csp doctor
```

Most local commands still run without an API key by using deterministic extraction and token-aware fallback summaries. Model-powered compression, careful DeepSeek review and any real API call require `DEEPSEEK_API_KEY`.

## Examples

```bash
csp search "Python pypdf extract text best practices"
csp codex "Fix the login redirect bug using local project context"
csp extract README.md --codex
csp extract error.log --careful
csp archive project.zip --codex
csp archive homework_files.zip --careful
csp review contract.docx --goal "认真复查，不要漏"
csp scan ./src --with-summary
```

## Output Example

Every Codex Context Pack includes stable sections such as:

- Task
- Model And Budget
- Verified Context
- Recommended Implementation
- Files To Inspect
- Files To Avoid
- Constraints For Codex
- Minimal Verification
- Prompt To Paste Into Codex

The Codex constraints always include `Do not use web search.`

## Archive Safety

Archives are extracted into temporary directories and cleaned after use. The archive reader checks for path traversal, file-count limits, total-size limits, single-file limits and unsupported binary/media files. It skips `.git`, `node_modules`, `dist`, `build`, `coverage`, `.next`, `.nuxt`, `target`, virtualenv folders, caches, logs and generated outputs by default.

RAR support depends on the local environment. If RAR extraction is unavailable, Context Saver MCP reports that clearly instead of failing silently.

## API Key Safety

Do not write API keys into source code. Do not commit `.env`. Confirm ignore behavior with:

```bash
git check-ignore .env
git check-ignore outputs/example.md
```

## Roadmap

- v0.1 CLI
- v0.2 Cache
- v0.3 Source citations
- v0.4 MCP server
- v0.5 VS Code extension

## License

MIT License.
