# Context Saver MCP

Stop wasting expensive coding-agent tokens on web search, long files, archives and oversized project context.

Context Saver MCP is a local search, file-extraction, archive-reading, careful-review and context-compression proxy for Codex, Claude Code, Qwen Code, Cline and Aider. It uses low-cost models such as DeepSeek V4 Flash to extract and compress useful context, and switches to DeepSeek V4 Pro for important, high-risk or careful-review tasks. Optional AnySearch-style web search and URL extraction can feed external context into the same compression workflow without replacing the local-first core.

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
- Optional AnySearch-style web search, vertical search and URL extraction for external context.
- Real Codex MCP tool: `context_saver_prepare`. It stays as the single stable entry point and switches behavior with `kind="project"`, `kind="search"`, `kind="url"` or `kind="doctor"`.

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

## Install In Codex

This repository includes both:

- a Codex skill under `skills/context-saver-mcp`
- a real MCP server exposed by `context_saver.mcp_server`

Install or refresh both locally with:

```bash
bash scripts/install-codex-skill.sh
```

The installer:

- installs the skill to `${CODEX_HOME:-$HOME/.codex}/skills/context-saver-mcp`
- adds a `context_saver` MCP server block to `${CODEX_HOME:-$HOME/.codex}/config.toml`
- writes a global AGENTS.md rule telling Codex to call `context_saver_prepare` before broad local work
- backs up the previous files before editing them

After restarting Codex or opening a new Codex session, one MCP tool should be available:

- `context_saver_prepare` - the single integrated entry point. Use `kind="project"` for local project context, `kind="search"` for optional AnySearch-style search plus compression, `kind="url"` for URL extraction plus compression, and `kind="doctor"` for setup checks.

For matching tasks, context preparation is mandatory before the main work. If external DeepSeek compression is blocked by safety or secrets policy, the agent should fall back to safe local context preparation and continue instead of sending secrets outward.

Natural-language routing is intentional. The agent should infer one of four modes from intent:

- Default project mode: "帮我修这个项目", "review", "debug", "读这个仓库", "先了解项目", local file/archive extraction, or token-saving context work -> `kind="project"`
- Optional web search plus compression: "帮我搜索网页", "查一下", "找资料", "找最新文档", external research, docs lookup, or comparisons -> `kind="search"`
- Optional webpage extraction plus compression: pasted URLs, "抽取网页", "读取网页", "总结这个链接", or "把这个 URL 看一下" -> `kind="url"`
- Configuration/status check: "检查 API key", "DeepSeek 有没有调用", "MCP 为什么没启用", setup health, or default activation checks -> `kind="doctor"`

The installer also writes `runtime.conf` inside the installed skill directory. This records the selected runtime, command path, MCP server name and default tool so future agents do not need to rediscover the entry point.

## Environment

Create a private `.env` from the example:

```bash
cp .env.example .env
```

Set `DEEPSEEK_API_KEY` in `.env`. Never commit API keys. This repository ignores `.env`, `.env.*` except `.env.example`, and generated `outputs/*.md`.

DeepSeek compression is enabled for sanitized context by default:

```bash
DEEPSEEK_EXTERNAL_CONTEXT_ALLOWED=true
CONTEXT_SAVER_TRUSTED_PROJECT=true
```

Set either value to `false` only when you want all compression to stay local. Context Saver still excludes `.env`, API keys, caches, runtime files and generated outputs from context packs. See `TRUSTED_CONTEXT.md` for the project-level trust policy.

DeepSeek connection stability can be tuned without changing code:

```bash
DEEPSEEK_TIMEOUT_SECONDS=90
DEEPSEEK_MAX_RETRIES=3
DEEPSEEK_RETRY_BACKOFF_SECONDS=0.75
```

The DeepSeek client retries temporary timeouts, network disconnects, 429 rate limits and 5xx server errors. Authentication errors such as 401/403 fail fast so bad keys are not retried forever.

To verify the real API path without exposing your key, run `csp doctor --probe-deepseek`. It sends one tiny request and reports whether the configured base URL, model and API key work.

Optional web search and URL extraction can be enabled with:

```bash
ANYSEARCH_ENABLED=true
ANYSEARCH_API_KEY=
ANYSEARCH_BASE_URL=https://api.anysearch.com/mcp
```

`ANYSEARCH_API_KEY` is optional if the endpoint allows anonymous access, but a key may provide higher limits. Leave `ANYSEARCH_ENABLED=false` to keep search commands on local fallback unless a key is present.

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
csp search "AAPL latest earnings" --domain finance --sub-domain finance.us_stock --sdp ticker=AAPL
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

See `SECURITY.md` for the data-flow and secret-handling policy, and `TEST_PLAN.md` for install, MCP and provider verification steps.

## Roadmap

- v0.1 CLI and Codex MCP server
- v0.2 Cache
- v0.3 Source citations
- v0.4 VS Code extension

## License

MIT License.
