from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .config import Settings, load_settings
from .models import ModelChoice
from .token_utils import count_tokens, get_model_context_limit

SYSTEM_PROMPT = """You are a low-cost search, file extraction, archive reading, careful-review and context compression proxy. Your task is to reduce Codex and coding-agent search, file-reading, archive-reading and context token usage. Saving tokens must not remove key facts, numbers, paths, errors, configuration, code logic, versions, user goals, file relationships or executable information. In careful-review or no-compress mode, prioritize accuracy, completeness and auditability. Large context is a fallback, not the default path. All budgets are counted in tokens."""


@dataclass
class ChatResult:
    content: str
    usage: dict[str, Any] | None = None


class DeepSeekClient:
    def __init__(self, settings: Settings | None = None, timeout: float = 60.0):
        self.settings = settings or load_settings()
        self.timeout = timeout

    def _model_name(self, model: str | ModelChoice | None) -> str:
        choice = ModelChoice(model or ModelChoice.FLASH)
        return self.settings.deepseek_flash_model if choice is ModelChoice.FLASH else self.settings.deepseek_pro_model

    def chat(self, messages: list[dict[str, str]], model: str | ModelChoice | None = None, max_tokens: int = 4096, temperature: float = 0.2) -> ChatResult:
        if not self.settings.deepseek_api_key:
            raise RuntimeError("DEEPSEEK_API_KEY is not configured. Create .env from .env.example.")
        if not self.settings.deepseek_api_key.isascii():
            raise RuntimeError("DEEPSEEK_API_KEY contains non-ASCII characters. Run `csp configure` again.")
        choice = ModelChoice(model or ModelChoice.FLASH)
        model_name = self._model_name(choice)
        total_input_tokens = sum(count_tokens(message.get("content", "")) for message in messages)
        context_limit = get_model_context_limit(choice, self.settings)
        if total_input_tokens + max_tokens + self.settings.safety_margin_tokens > context_limit:
            raise ValueError("Request exceeds model context limit. Split the input into chunks first.")
        payload = {
            "model": model_name,
            "messages": [{"role": "system", "content": SYSTEM_PROMPT}, *messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        try:
            with httpx.Client(base_url=self.settings.deepseek_base_url, timeout=self.timeout) as client:
                response = client.post(
                    "/chat/completions",
                    json=payload,
                    headers={"Authorization": f"Bearer {self.settings.deepseek_api_key}"},
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in {401, 403}:
                raise RuntimeError("DeepSeek authentication failed. Check DEEPSEEK_API_KEY.") from exc
            raise RuntimeError(f"DeepSeek API HTTP error: {exc.response.status_code}") from exc
        except httpx.TimeoutException as exc:
            raise RuntimeError("DeepSeek API request timed out.") from exc
        except httpx.NetworkError as exc:
            raise RuntimeError("DeepSeek API network error.") from exc
        data = response.json()
        return ChatResult(content=data["choices"][0]["message"]["content"], usage=data.get("usage"))
