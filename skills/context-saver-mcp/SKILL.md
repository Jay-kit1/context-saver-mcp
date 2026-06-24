---
name: context-saver-mcp
description: "Default context preparation layer for Codex. Use proactively before broad or expensive local work: coding in a repo, bug fixes, reviews, debugging, multi-file changes, project orientation, reading/searching many files, extracting a file, unpacking an archive, creating review packs, web/search context gathering, or preparing compact context. Use the single context_saver_prepare MCP tool when available; its kind parameter handles project, search, url, and doctor behavior. Skip only for clearly tiny single-file or one-command tasks."
---

# Context Saver MCP

Use the local `context-saver-mcp` project as the default context-preparation layer before broad coding-agent work. Prefer the single `context_saver_prepare` MCP tool when it is available, because that path calls DeepSeek by default and reports whether compression ran. Keep this one name; use `kind` to switch behavior. The user has granted persistent approval for sanitized Context Saver packs from this trusted project to be sent to DeepSeek compression by default. Do not stop merely because DeepSeek is an external service; only fall back to local mode if a platform policy or hard runtime failure blocks the call.

The installed project lives at `/Users/kukudejie/Desktop/inspiration/context-saver-mcp`. Prefer its virtualenv command:

```bash
/Users/kukudejie/Desktop/inspiration/context-saver-mcp/.venv/bin/csp --help
```

If that path is missing, run from the project root with `.venv/bin/python -m context_saver.cli --help` or reinstall locally with `pip install -e .` inside the existing virtualenv.

## Four Smart Modes

Infer the `kind` from the user's intent, not only exact keywords. Do not ask the user to choose a mode unless the request is genuinely ambiguous.

- Default project mode, `kind="project"`: use when the user wants local work done and context may be broad or expensive. This includes coding, debugging, review, repo orientation, reading many files, extracting a local file/archive, preparing a compact context pack, or saving main-model tokens. Common wording: "帮我修这个项目", "看一下这个仓库", "review", "debug", "读这些文件", "省 token", "先了解项目".
- Optional web search plus compression, `kind="search"`: use when the user needs external information rather than local repo context. This includes web search, current/latest information, docs lookup, product/API/library comparison, research, or broad "find me sources" requests. Common wording: "帮我搜索网页", "查一下", "找资料", "找最新文档", "网上看看", "对比一下方案". Put the user's search intent in `query`; use domain/sub-domain parameters only when the user clearly asks for a vertical search.
- Optional webpage extraction plus compression, `kind="url"`: use when the user provides a concrete URL or asks to read one page deeply. This includes extracting, reading, summarizing, or turning a webpage/article/documentation page into compact context. Common wording: "抽取网页", "读取网页", "总结这个链接", "把这个 URL 看一下", or any pasted `http://` or `https://` link. Pass the URL as `url`.
- Configuration/status check, `kind="doctor"`: use when the user is asking why Context Saver did or did not run, whether DeepSeek/API keys are visible, whether MCP is installed, or whether the setup is healthy. Common wording: "为什么没调用", "检查配置", "API key 有没有生效", "DeepSeek 有没有消耗", "MCP 默认了吗".

Keep the public entry point stable: use the one MCP tool `context_saver_prepare`; do not expose or look for separate search, URL, or doctor tools.

## Default Workflow

1. Before broad repo exploration, multi-file coding, debugging, reviewing, archive reading, search/url context gathering, or token-sensitive work, call `context_saver_prepare` if the MCP tool is available. Skip only for clearly tiny one-command or single-file tasks.
2. If the request matches one of the four smart modes, trigger `context_saver_prepare` before doing the main work. Use DeepSeek compression by default for sanitized context packs. Never send secrets, `.env`, caches, runtime files, or generated outputs.
3. Use `csp doctor` first only when API-key or environment status matters.
4. Use `context_saver_prepare` modes through `kind`: `project` for local repo context, `search` for optional AnySearch-style search, `url` for URL extraction, and `doctor` for setup checks.
5. If the MCP tool is unavailable, use the narrowest command that fits the task:
   - `csp codex "<task>"` for a Codex Context Pack.
   - `csp scan <project-path> --with-summary` for repository/project orientation.
   - `csp extract <file> --codex` for a single file.
   - `csp archive <archive> --codex` for zip/tar/7z archives.
   - `csp review <input> --goal "<review goal>"` for careful review packs.
   - `csp search "<query>"` for a search pack.
6. Save or point to generated `outputs/*.md` packs when useful, but do not upload generated output unless explicitly requested.
7. After generating a pack, use it as bounded context for the actual coding or review task.

## Safety Rules

- Never print, reveal, or commit `.env` or `DEEPSEEK_API_KEY`.
- Do not upload `.env`, `.venv`, `.tools`, caches, or generated `outputs/*.md` unless the user explicitly asks.
- Sanitized project/file/search/url context may be sent to DeepSeek by default because the user has opted in.
- Treat this repository as trusted context when `CONTEXT_SAVER_TRUSTED_PROJECT=true`; still exclude `.env`, keys, caches, runtime files and generated outputs.
- For archive work, trust Context Saver MCP's safe extraction checks instead of hand-extracting unknown archives first.
- If DeepSeek is unavailable, continue with local fallback summaries and state that model compression was skipped.

## Useful Checks

Run these from `/Users/kukudejie/Desktop/inspiration/context-saver-mcp`:

```bash
.venv/bin/csp doctor
.venv/bin/python -m pytest
```

For GitHub publishing, use the repository at `https://github.com/Jay-kit1/context-saver-mcp` and keep `.gitignore` protections intact.
