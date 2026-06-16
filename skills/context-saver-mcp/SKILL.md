---
name: context-saver-mcp
description: "Use when Codex needs to prepare compact local context before coding or reviewing: search/query packaging, file extraction, archive reading, project scans, careful review packs, token-aware summaries, or prompts that mention Context Saver MCP, csp, context pack, archive pack, review pack, scan pack, DeepSeek-assisted compression, or avoiding expensive coding-agent context use."
---

# Context Saver MCP

Use the local `context-saver-mcp` project to prepare small, useful context packs before doing expensive coding-agent work.

The installed project lives at `/Users/kukudejie/Desktop/inspiration/context-saver-mcp`. Prefer its virtualenv command:

```bash
/Users/kukudejie/Desktop/inspiration/context-saver-mcp/.venv/bin/csp --help
```

If that path is missing, run from the project root with `.venv/bin/python -m context_saver.cli --help` or reinstall locally with `pip install -e .` inside the existing virtualenv.

## Default Workflow

1. Decide whether the user needs context preparation before coding, reviewing, reading large files, or unpacking archives.
2. Use `csp doctor` first only when API-key or environment status matters.
3. Use the narrowest command that fits the task:
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
