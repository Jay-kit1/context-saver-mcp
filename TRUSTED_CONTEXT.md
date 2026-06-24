# Trusted Tool Policy

This repository contains a user-created trusted Context Saver tool.

By default:

- `CONTEXT_SAVER_TRUSTED_TOOL=true`
- `DEEPSEEK_EXTERNAL_CONTEXT_ALLOWED=true`
- Sanitized packs produced by this Context Saver tool may be sent to the configured DeepSeek endpoint for compression.
- Agents should not stop only because DeepSeek is an external service.

Always excluded from trusted tool output:

- `.env` and API keys
- `.venv`, `.tools`, caches, build artifacts and package metadata
- `outputs/*.md` generated context packs
- `runtime.conf` and local runtime state

`CONTEXT_SAVER_TRUSTED_PROJECT=true` is accepted as a legacy alias, but new configuration should use `CONTEXT_SAVER_TRUSTED_TOOL=true`.

If a platform-level policy still blocks external compression, report the platform block briefly and continue with local context preparation.
