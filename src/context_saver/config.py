from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_flash_model: str = "deepseek-v4-flash"
    deepseek_pro_model: str = "deepseek-v4-pro"
    deepseek_external_context_allowed: bool = True
    context_saver_trusted_tool: bool = True
    deepseek_timeout_seconds: float = 90.0
    deepseek_max_retries: int = 3
    deepseek_retry_backoff_seconds: float = 0.75
    anysearch_api_key: str = ""
    anysearch_base_url: str = "https://api.anysearch.com/mcp"
    anysearch_enabled: bool = False
    model_routing_mode: str = "auto"
    flash_context_tokens: int = 600000
    pro_context_tokens: int = 1000000
    flash_internal_input_tokens: int = 64000
    pro_internal_input_tokens: int = 160000
    careful_internal_input_tokens: int = 240000
    no_compress_internal_input_tokens: int = 320000
    default_output_tokens: int = 4096
    careful_output_tokens: int = 8192
    no_compress_output_tokens: int = 12000
    normal_pack_tokens: int = 3000
    normal_pack_max_tokens: int = 6000
    careful_pack_tokens: int = 12000
    careful_pack_max_tokens: int = 30000
    no_compress_pack_max_tokens: int = 60000
    archive_max_files: int = 500
    archive_max_total_size_mb: int = 300
    archive_max_single_file_mb: int = 20
    archive_max_text_files_read: int = 120
    archive_max_full_read_files: int = 40
    archive_max_depth: int = 5
    safety_margin_tokens: int = 2048


def _int_env(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return int(value)


def _float_env(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return float(value)


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None or value == "":
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(env_file: str | Path | None = None) -> Settings:
    load_dotenv(env_file)
    return Settings(
        deepseek_api_key=os.getenv("DEEPSEEK_API_KEY", ""),
        deepseek_base_url=os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        deepseek_flash_model=os.getenv("DEEPSEEK_FLASH_MODEL", "deepseek-v4-flash"),
        deepseek_pro_model=os.getenv("DEEPSEEK_PRO_MODEL", "deepseek-v4-pro"),
        deepseek_external_context_allowed=_bool_env("DEEPSEEK_EXTERNAL_CONTEXT_ALLOWED", True),
        context_saver_trusted_tool=_bool_env(
            "CONTEXT_SAVER_TRUSTED_TOOL",
            _bool_env("CONTEXT_SAVER_TRUSTED_PROJECT", True),
        ),
        deepseek_timeout_seconds=_float_env("DEEPSEEK_TIMEOUT_SECONDS", 90.0),
        deepseek_max_retries=_int_env("DEEPSEEK_MAX_RETRIES", 3),
        deepseek_retry_backoff_seconds=_float_env("DEEPSEEK_RETRY_BACKOFF_SECONDS", 0.75),
        anysearch_api_key=os.getenv("ANYSEARCH_API_KEY", ""),
        anysearch_base_url=os.getenv("ANYSEARCH_BASE_URL", "https://api.anysearch.com/mcp"),
        anysearch_enabled=_bool_env("ANYSEARCH_ENABLED", False),
        model_routing_mode=os.getenv("MODEL_ROUTING_MODE", "auto").lower(),
        flash_context_tokens=_int_env("FLASH_CONTEXT_TOKENS", 600000),
        pro_context_tokens=_int_env("PRO_CONTEXT_TOKENS", 1000000),
        flash_internal_input_tokens=_int_env("FLASH_INTERNAL_INPUT_TOKENS", 64000),
        pro_internal_input_tokens=_int_env("PRO_INTERNAL_INPUT_TOKENS", 160000),
        careful_internal_input_tokens=_int_env("CAREFUL_INTERNAL_INPUT_TOKENS", 240000),
        no_compress_internal_input_tokens=_int_env("NO_COMPRESS_INTERNAL_INPUT_TOKENS", 320000),
        default_output_tokens=_int_env("DEFAULT_OUTPUT_TOKENS", 4096),
        careful_output_tokens=_int_env("CAREFUL_OUTPUT_TOKENS", 8192),
        no_compress_output_tokens=_int_env("NO_COMPRESS_OUTPUT_TOKENS", 12000),
        normal_pack_tokens=_int_env("NORMAL_PACK_TOKENS", 3000),
        normal_pack_max_tokens=_int_env("NORMAL_PACK_MAX_TOKENS", 6000),
        careful_pack_tokens=_int_env("CAREFUL_PACK_TOKENS", 12000),
        careful_pack_max_tokens=_int_env("CAREFUL_PACK_MAX_TOKENS", 30000),
        no_compress_pack_max_tokens=_int_env("NO_COMPRESS_PACK_MAX_TOKENS", 60000),
        archive_max_files=_int_env("ARCHIVE_MAX_FILES", 500),
        archive_max_total_size_mb=_int_env("ARCHIVE_MAX_TOTAL_SIZE_MB", 300),
        archive_max_single_file_mb=_int_env("ARCHIVE_MAX_SINGLE_FILE_MB", 20),
        archive_max_text_files_read=_int_env("ARCHIVE_MAX_TEXT_FILES_READ", 120),
        archive_max_full_read_files=_int_env("ARCHIVE_MAX_FULL_READ_FILES", 40),
        archive_max_depth=_int_env("ARCHIVE_MAX_DEPTH", 5),
    )
