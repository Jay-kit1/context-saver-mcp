from __future__ import annotations

from .models import ModelChoice, UsageReport
from .token_utils import estimate_tokens

PRICE_CNY_PER_1K = {
    ModelChoice.FLASH: {"input": 0.001, "output": 0.004},
    ModelChoice.PRO: {"input": 0.014, "output": 0.028},
}


def build_usage_report(input_text: str, output_text: str, model: ModelChoice, usage: dict | None = None) -> UsageReport:
    if usage:
        input_tokens = int(usage.get("prompt_tokens", 0))
        output_tokens = int(usage.get("completion_tokens", 0))
        approximate = False
    else:
        input_tokens = estimate_tokens(input_text)
        output_tokens = estimate_tokens(output_text)
        approximate = True
    price = PRICE_CNY_PER_1K[model]
    cost = input_tokens / 1000 * price["input"] + output_tokens / 1000 * price["output"]
    return UsageReport(
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        cost_cny=round(cost, 6),
        approximate=approximate,
    )
