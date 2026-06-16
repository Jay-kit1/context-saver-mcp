from __future__ import annotations

import math
import re
from typing import Any

from .models import ModelChoice

try:
    import tiktoken
except Exception:  # pragma: no cover
    tiktoken = None


APPROXIMATE_TOKEN_COUNT = tiktoken is None
_ENCODING = None


def _get_encoding():
    global APPROXIMATE_TOKEN_COUNT, _ENCODING
    if tiktoken is None:
        return None
    if _ENCODING is not None:
        return _ENCODING
    try:
        _ENCODING = tiktoken.get_encoding("cl100k_base")
        return _ENCODING
    except Exception:
        APPROXIMATE_TOKEN_COUNT = True
        return None


def _fallback_count(text: str) -> int:
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    non_cjk = len(text) - cjk
    return max(1, cjk + math.ceil(non_cjk / 4))


def count_tokens(text: str) -> int:
    if not text:
        return 0
    encoding = _get_encoding()
    if encoding is None:
        return _fallback_count(text)
    return len(encoding.encode(text))


def estimate_tokens(text: str) -> int:
    return count_tokens(text)


def _slice_by_tokens(text: str, start: int, end: int) -> str:
    encoding = _get_encoding()
    if encoding is None:
        approx_chars = max(1, (end - start) * 3)
        approx_start = max(0, start * 3)
        return text[approx_start : approx_start + approx_chars]
    tokens = encoding.encode(text)
    return encoding.decode(tokens[start:end])


def split_text_by_tokens(text: str, max_tokens: int, overlap_tokens: int = 500) -> list[str]:
    if max_tokens <= 0:
        raise ValueError("max_tokens must be positive")
    total = count_tokens(text)
    if total <= max_tokens:
        return [text] if text else []
    chunks: list[str] = []
    start = 0
    overlap = min(overlap_tokens, max_tokens // 2)
    while start < total:
        end = min(total, start + max_tokens)
        chunks.append(_slice_by_tokens(text, start, end))
        if end == total:
            break
        start = max(0, end - overlap)
    return chunks


def get_model_context_limit(model_choice: ModelChoice | str, settings: Any) -> int:
    choice = ModelChoice(model_choice)
    return settings.flash_context_tokens if choice is ModelChoice.FLASH else settings.pro_context_tokens


def get_internal_input_budget(model_choice: ModelChoice | str, mode: str, settings: Any) -> int:
    choice = ModelChoice(model_choice)
    if mode == "no-compress":
        return settings.no_compress_internal_input_tokens
    if mode == "careful-review":
        return settings.careful_internal_input_tokens
    if choice is ModelChoice.FLASH:
        return settings.flash_internal_input_tokens
    return settings.pro_internal_input_tokens


def reserve_output_tokens(context_limit: int, output_tokens: int, safety_margin_tokens: int) -> int:
    return max(0, context_limit - output_tokens - safety_margin_tokens)


def clamp_input_budget(
    requested_budget: int,
    model_context_limit: int,
    output_tokens: int,
    safety_margin_tokens: int,
) -> int:
    available = reserve_output_tokens(model_context_limit, output_tokens, safety_margin_tokens)
    return min(requested_budget, available)
