from __future__ import annotations

from .config import Settings, load_settings
from .models import ModelChoice, RoutingDecision
from .token_utils import clamp_input_budget, get_internal_input_budget, get_model_context_limit

HIGH_RISK_TERMS = {
    "important", "critical", "production", "security", "payment", "database",
    "deployment", "auth", "privacy", "legal", "medical", "financial",
    "必须准确", "不能错", "生产环境", "线上环境", "数据库", "鉴权", "支付",
    "安全漏洞", "隐私", "法律", "医疗", "金融",
}

CAREFUL_TERMS = {
    "认真读", "仔细读", "完整读", "不要漏", "逐项检查", "认真复查", "帮我复查",
    "核对文件", "对照检查", "审一遍", "不要过度压缩", "每个文件都认真看",
    "检查压缩包全部内容", "复查",
}

FLASH_TERMS = {"low-cost", "cheap", "flash", "省钱"}


def _contains_any(task: str, terms: set[str]) -> str | None:
    lowered = task.lower()
    for term in terms:
        if term.lower() in lowered:
            return term
    return None


def choose_model(
    task: str,
    mode: str = "auto",
    careful: bool = False,
    no_compress: bool = False,
    settings: Settings | None = None,
) -> RoutingDecision:
    settings = settings or load_settings()
    routing_mode = mode if mode in {"flash", "pro", "auto"} else settings.model_routing_mode
    compression_mode = "normal-compression"
    reason = "ordinary task uses low-cost Flash"

    if no_compress:
        model_choice = ModelChoice.PRO
        compression_mode = "no-compress"
        reason = "no-compress requires Pro"
    elif careful or _contains_any(task, CAREFUL_TERMS):
        model_choice = ModelChoice.PRO
        compression_mode = "careful-review"
        reason = "careful review wording requires Pro"
    elif routing_mode == "flash":
        model_choice = ModelChoice.FLASH
        reason = "forced Flash routing"
    elif routing_mode == "pro":
        model_choice = ModelChoice.PRO
        reason = "forced Pro routing"
    elif _contains_any(task, HIGH_RISK_TERMS):
        model_choice = ModelChoice.PRO
        reason = "important or high-risk task requires Pro"
    elif _contains_any(task, FLASH_TERMS):
        model_choice = ModelChoice.FLASH
        reason = "user requested low-cost Flash"
    else:
        model_choice = ModelChoice.FLASH

    output_tokens = settings.default_output_tokens
    if compression_mode == "careful-review":
        output_tokens = settings.careful_output_tokens
    elif compression_mode == "no-compress":
        output_tokens = settings.no_compress_output_tokens

    context_window = get_model_context_limit(model_choice, settings)
    raw_budget = get_internal_input_budget(model_choice, compression_mode, settings)
    internal_input_budget = clamp_input_budget(
        raw_budget,
        context_window,
        output_tokens,
        settings.safety_margin_tokens,
    )
    return RoutingDecision(
        model_choice=model_choice,
        mode=compression_mode,
        context_window=context_window,
        internal_input_budget=internal_input_budget,
        output_tokens=output_tokens,
        reason=reason,
    )
