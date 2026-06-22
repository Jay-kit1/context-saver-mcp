from __future__ import annotations

from .config import Settings, load_settings
from .deepseek_client import DeepSeekClient
from .models import RoutingDecision
from .token_utils import split_text_by_tokens


def simple_summary(text: str, max_tokens: int = 3000) -> str:
    chunks = split_text_by_tokens(text, max_tokens=max_tokens)
    if not chunks:
        return ""
    if len(chunks) == 1:
        return chunks[0]
    previews = []
    for index, chunk in enumerate(chunks[:20], start=1):
        previews.append(f"[Chunk {index}]\n{chunk[:2500]}")
    if len(chunks) > 20:
        previews.append(f"[Skipped] {len(chunks) - 20} additional chunks need layered review.")
    return "\n\n".join(previews)


def model_summary(
    text: str,
    decision: RoutingDecision,
    instruction: str,
    settings: Settings | None = None,
) -> str | None:
    settings = settings or load_settings()
    if not settings.deepseek_external_context_allowed:
        return None
    if not settings.deepseek_api_key:
        return None
    chunks = split_text_by_tokens(text, max_tokens=max(1000, decision.internal_input_budget // 4))
    client = DeepSeekClient(settings=settings)
    partials = []
    for index, chunk in enumerate(chunks[:8], start=1):
        result = client.chat(
            [
                {
                    "role": "user",
                    "content": (
                        f"{instruction}\n\n"
                        f"Mode: {decision.mode}\n"
                        f"Chunk {index}/{len(chunks)}:\n{chunk}"
                    ),
                }
            ],
            model=decision.model_choice,
            max_tokens=min(decision.output_tokens, 4096),
        )
        partials.append(result.content)
    if len(partials) == 1:
        return partials[0]
    merged = "\n\n".join(f"[Partial {index}]\n{part}" for index, part in enumerate(partials, start=1))
    result = client.chat(
        [
            {
                "role": "user",
                "content": (
                    f"Merge these partial summaries into one accurate Context Pack section. {instruction}\n\n{merged}"
                ),
            }
        ],
        model=decision.model_choice,
        max_tokens=decision.output_tokens,
    )
    return result.content
