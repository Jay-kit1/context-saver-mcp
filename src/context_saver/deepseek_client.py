from __future__ import annotations

from dataclasses import dataclass
import time
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
    RETRYABLE_STATUS_CODES = {408, 409, 425, 429, 500, 502, 503, 504}

    def __init__(
        self,
        settings: Settings | None = None,
        timeout: float | None = None,
        max_retries: int | None = None,
        retry_backoff_seconds: float | None = None,
    ):
        self.settings = settings or load_settings()
        self.timeout = timeout if timeout is not None else self.settings.deepseek_timeout_seconds
        self.max_retries = max(0, max_retries if max_retries is not None else self.settings.deepseek_max_retries)
        self.retry_backoff_seconds = max(
            0.0,
            retry_backoff_seconds
            if retry_backoff_seconds is not None
            else self.settings.deepseek_retry_backoff_seconds,
        )

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
        response = self._post_with_retries(payload, model_name)
        data = response.json()
        content = data["choices"][0]["message"].get("content") or ""
        usage = data.get("usage")
        if not content.strip():
            reasoning_tokens = (
                usage.get("completion_tokens_details", {}).get("reasoning_tokens")
                if isinstance(usage, dict)
                else None
            )
            if reasoning_tokens:
                raise RuntimeError(
                    "DeepSeek returned no visible content because the output budget was consumed by reasoning. "
                    "Increase DEFAULT_OUTPUT_TOKENS or the command's max_tokens."
                )
            raise RuntimeError("DeepSeek returned an empty response body.")
        return ChatResult(content=content, usage=usage)

    def _post_with_retries(self, payload: dict[str, Any], model_name: str) -> httpx.Response:
        attempts = self.max_retries + 1
        last_error: Exception | None = None
        headers = {"Authorization": f"Bearer {self.settings.deepseek_api_key}"}

        for attempt in range(1, attempts + 1):
            try:
                with httpx.Client(base_url=self.settings.deepseek_base_url, timeout=self.timeout) as client:
                    response = client.post("/chat/completions", json=payload, headers=headers)
                    response.raise_for_status()
                    return response
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code in {401, 403}:
                    raise RuntimeError("DeepSeek authentication failed. Check DEEPSEEK_API_KEY.") from exc
                if status_code not in self.RETRYABLE_STATUS_CODES or attempt == attempts:
                    body = exc.response.text[:200].replace("\n", " ")
                    detail = f": {body}" if body else ""
                    raise RuntimeError(
                        f"DeepSeek API HTTP error {status_code} after {attempt}/{attempts} attempt(s){detail}"
                    ) from exc
                last_error = exc
                self._sleep_before_retry(attempt, exc.response)
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt == attempts:
                    raise RuntimeError(
                        f"DeepSeek API request timed out after {attempts} attempt(s). "
                        f"base_url={self.settings.deepseek_base_url} model={model_name}"
                    ) from exc
                self._sleep_before_retry(attempt)
            except httpx.TransportError as exc:
                last_error = exc
                if attempt == attempts:
                    raise RuntimeError(
                        f"DeepSeek API network error after {attempts} attempt(s). "
                        f"base_url={self.settings.deepseek_base_url} model={model_name}"
                    ) from exc
                self._sleep_before_retry(attempt)

        raise RuntimeError(f"DeepSeek API request failed after {attempts} attempt(s): {last_error}")

    def _sleep_before_retry(self, attempt: int, response: httpx.Response | None = None) -> None:
        retry_after = response.headers.get("retry-after") if response is not None else None
        delay = self._parse_retry_after(retry_after)
        if delay is None:
            delay = self.retry_backoff_seconds * (2 ** (attempt - 1))
        if delay > 0:
            time.sleep(delay)

    @staticmethod
    def _parse_retry_after(value: str | None) -> float | None:
        if not value:
            return None
        try:
            return max(0.0, float(value))
        except ValueError:
            return None
