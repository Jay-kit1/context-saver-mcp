---
name: context-saver-mcp
description: "Default context preparation layer for Codex. Use proactively before broad or expensive local work: coding in a repo, bug fixes, reviews, debugging, multi-file changes, project orientation, reading/searching many files, extracting a file, unpacking an archive, creating review packs, or preparing compact context. Also trigger for Context Saver MCP, csp, context pack, scan pack, archive pack, review pack, DeepSeek compression, token saving, or avoiding expensive coding-agent context use. Skip only for clearly tiny single-file or one-command tasks."
---

# Context Saver MCP

Use the local `context-saver-mcp` project as the default context-preparation layer before broad coding-agent work. Prefer the `context_saver_prepare` MCP tool when it is available, because that path actually calls DeepSeek and reports whether compression ran.

The installed project lives at `/Users/kukudejie/Desktop/inspiration/context-saver-mcp`. Prefer its virtualenv command:

```bash
/Users/kukudejie/Desktop/inspiration/context-saver-mcp/.venv/bin/csp --help
```

If that path is missing, run from the project root with `.venv/bin/python -m context_saver.cli --help` or reinstall locally with `pip install -e .` inside the existing virtualenv.

## Default Workflow

1. Before broad repo exploration, multi-file coding, debugging, reviewing, archive reading, or token-sensitive work, call `context_saver_prepare` if the MCP tool is available. Skip only for clearly tiny one-command or single-file tasks.
2. Use `csp doctor` first only when API-key or environment status matters.
3. If the MCP tool is unavailable, use the narrowest command that fits the task:
   - `csp codex "<task>"` for a Codex Context Pack.
   - `csp scan <project-path> --with-summary` for repository/project orientation.
   - `csp extract <file> --codex` for a single file.
   - `csp archive <archive> --codex` for zip/tar/7z archives.
   - `csp review <input> --goal "<review goal>"` for careful review packs.
   - `csp search "<query>"` for a search pack.
4. Save or point to generated `outputs/*.md` packs when useful, but do not upload generated output unless explicitly requested.
5. After generating a pack, use it as bounded context for the actual coding or review task.

## Safety Rules

- Never print, reveal, or commit `.env` or `DEEPSEEK_API_KEY`.
- Do not upload `.env`, `.venv`, `.tools`, caches, or generated `outputs/*.md` unless the user explicitly asks.
- For archive work, trust Context Saver MCP's safe extraction checks instead of hand-extracting unknown archives first.
- If DeepSeek is unavailable, continue with local fallback summaries and state that model compression was skipped.

## Useful Checks

Run these from `/Users/kukudejie/Desktop/inspiration/context-saver-mcp`:

```bash
.venv/bin/csp doctor
.venv/bin/python -m pytest
```

For GitHub publishing, use the repository at `https://github.com/Jay-kit1/context-saver-mcp` and keep `.gitignore` protections intact.
