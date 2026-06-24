# Trusted Context Policy

This repository is intended to be a trusted Context Saver project.

By default:

- `CONTEXT_SAVER_TRUSTED_PROJECT=true`
- `DEEPSEEK_EXTERNAL_CONTEXT_ALLOWED=true`
- Sanitized Context Saver packs may be sent to the configured DeepSeek endpoint for compression.
- Agents should not stop only because DeepSeek is an external service.

Always excluded from trusted context:

- `.env` and API keys
- `.venv`, `.tools`, caches, build artifacts and package metadata
- `outputs/*.md` generated context packs
- `runtime.conf` and local runtime state

If a platform-level policy still blocks external compression, report the platform block briefly and continue with local context preparation.
