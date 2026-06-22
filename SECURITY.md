# Security Policy

## Secrets

Never commit `.env`, API keys, local virtualenvs, tool downloads, caches, or generated context packs. This repository ignores:

- `.env` and `.env.*` except `.env.example`
- `.venv/`, `venv/`, `.tools/`
- `outputs/*.md`
- caches and build artifacts

Context Saver MCP reads `DEEPSEEK_API_KEY` from the project `.env` file or environment. Optional AnySearch-style search reads `ANYSEARCH_API_KEY` the same way.

## Data Flow

- Local project scans, file extraction, and archive inspection happen locally.
- DeepSeek compression sends selected context to the configured DeepSeek endpoint.
- Optional AnySearch-style search and URL extraction send search queries or URLs to the configured AnySearch endpoint.
- Generated context packs are written under `outputs/` and are not committed by default.

## Reporting

If you find a secret-handling bug, path traversal issue, unsafe archive behavior, or accidental upload path, open a private report or issue with:

- affected command or MCP tool
- minimal reproduction steps
- whether `.env`, API keys, or private files could be exposed
