from context_saver.config import load_settings
from context_saver.models import ModelChoice
from context_saver.token_utils import (
    estimate_tokens,
    get_internal_input_budget,
    get_model_context_limit,
    reserve_output_tokens,
    split_text_by_tokens,
)


def test_estimate_tokens_positive():
    assert estimate_tokens("hello 世界") > 0


def test_split_text_by_tokens_chunks():
    chunks = split_text_by_tokens("hello " * 1000, max_tokens=100, overlap_tokens=10)
    assert len(chunks) > 1


def test_default_context_and_internal_budgets():
    settings = load_settings()
    assert get_model_context_limit(ModelChoice.FLASH, settings) == 600000
    assert get_model_context_limit(ModelChoice.PRO, settings) == 1000000
    assert get_internal_input_budget(ModelChoice.FLASH, "normal-compression", settings) == 64000
    assert get_internal_input_budget(ModelChoice.PRO, "normal-compression", settings) == 160000
    assert get_internal_input_budget(ModelChoice.PRO, "careful-review", settings) == 240000
    assert get_internal_input_budget(ModelChoice.FLASH, "normal-compression", settings) < get_model_context_limit(ModelChoice.FLASH, settings)


def test_reserve_output_tokens():
    assert reserve_output_tokens(1000, 100, 50) == 850


def test_long_text_chunks():
    chunks = split_text_by_tokens("x" * 10000, max_tokens=200)
    assert len(chunks) > 1
