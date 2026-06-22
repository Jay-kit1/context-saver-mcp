from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from .anysearch_client import AnySearchClient
from .codex_pack import build_context_pack, build_project_scan_pack, timestamped_output
from .config import load_settings
from .deepseek_client import DeepSeekClient
from .project_scan import scan_project
from .router import choose_model
from .summarizer import simple_summary
from .token_utils import count_tokens


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = PROJECT_ROOT / ".env"

mcp = FastMCP(
    "context-saver-mcp",
    instructions=(
        "Use the single context_saver_prepare tool before broad local coding, review, debugging, "
        "project orientation, multi-file work, archive/file extraction, optional web/search context, "
        "or token-sensitive work. It keeps one stable tool name and integrates project scan, "
        "search, URL extraction, diagnostics, and DeepSeek compression."
    ),
)


def _settings():
    return load_settings(ENV_FILE if ENV_FILE.exists() else None)


def _write_pack(prefix: str, content: str) -> str:
    output_path = timestamped_output(prefix, output_dir=PROJECT_ROOT / "outputs")
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def _resolve_path(path: str) -> Path:
    root = Path(path).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    return root


def _compress_text(
    task: str,
    text: str,
    instruction: str,
    use_deepseek: bool,
) -> tuple[str, bool, dict[str, Any] | None, str]:
    settings = _settings()
    decision = choose_model(task=task, mode="auto", careful=False, no_compress=False, settings=settings)
    if use_deepseek and settings.deepseek_api_key and text:
        try:
            result = DeepSeekClient(settings=settings).chat(
                [{"role": "user", "content": f"{instruction}\n\nTask: {task}\n\n{text}"}],
                model=decision.model_choice,
                max_tokens=min(decision.output_tokens, settings.normal_pack_max_tokens),
            )
            return result.content, True, result.usage, ""
        except RuntimeError as exc:
            return simple_summary(text, max_tokens=settings.normal_pack_tokens), False, None, str(exc)
    return simple_summary(text, max_tokens=settings.normal_pack_tokens), False, None, ""


def _project_pack(task: str, project_path: str, max_files: int, max_depth: int, use_deepseek: bool) -> dict[str, Any]:
    settings = _settings()
    root = _resolve_path(project_path)
    scan = scan_project(root, max_files=max_files, max_depth=max_depth, with_summary=True)
    scan_pack = build_project_scan_pack(root, scan)
    summary, deepseek_used, usage, error = _compress_text(
        task,
        scan_pack,
        "Compress this project scan into a compact Codex context pack. Preserve important file paths, likely implementation entry points, ignored paths, risks, and minimal next files to inspect.",
        use_deepseek,
    )
    decision = choose_model(task=task, mode="auto", careful=False, no_compress=False, settings=settings)
    pack = build_context_pack(
        task=task,
        decision=decision,
        verified_context=summary,
        recommended_implementation="Inspect only the suggested files first. Keep changes scoped and run minimal verification.",
        files_to_inspect=scan["suggested_codex_scope"],
    )
    output_path = _write_pack("mcp_context_pack", pack)
    return {
        "kind": "project",
        "deepseek_used": deepseek_used,
        "deepseek_usage": usage,
        "deepseek_error": error,
        "project_path": str(root),
        "output_path": output_path,
        "raw_scan_tokens": count_tokens(scan_pack),
        "pack_tokens": count_tokens(pack),
        "suggested_files": scan["suggested_codex_scope"],
        "ignored_paths": scan["ignored_paths"],
        "context_pack": pack,
    }


def _search_pack(
    task: str,
    query: str,
    max_results: int,
    domain: str,
    sub_domain: str,
    sub_domain_params: dict[str, Any] | None,
    use_deepseek: bool,
) -> dict[str, Any]:
    settings = _settings()
    anysearch_used = False
    anysearch_error = ""
    try:
        result = AnySearchClient(settings=settings).search(
            query=query,
            max_results=max_results,
            domain=domain,
            sub_domain=sub_domain,
            sub_domain_params=sub_domain_params,
        )
        text = result.text
        anysearch_used = True
    except RuntimeError as exc:
        anysearch_error = str(exc)
        text = f"Search query recorded locally because AnySearch was unavailable: {query}"

    summary, deepseek_used, usage, error = _compress_text(
        task or f"Search context for: {query}",
        text,
        "Compress these search results into a concise context pack section. Preserve URLs, dates, versions, direct facts, uncertainty and contradictions.",
        use_deepseek,
    )
    decision = choose_model(task=task or query, mode="auto", careful=False, no_compress=False, settings=settings)
    pack = build_context_pack(
        task=task or f"Search context for: {query}",
        decision=decision,
        verified_context=summary,
        recommended_implementation="Use this as external context only; verify before changing code.",
    )
    output_path = _write_pack("mcp_search_pack", pack)
    return {
        "kind": "search",
        "anysearch_used": anysearch_used,
        "anysearch_error": anysearch_error,
        "deepseek_used": deepseek_used,
        "deepseek_usage": usage,
        "deepseek_error": error,
        "output_path": output_path,
        "raw_tokens": count_tokens(text),
        "pack_tokens": count_tokens(pack),
        "context_pack": pack,
    }


def _url_pack(task: str, url: str, use_deepseek: bool) -> dict[str, Any]:
    settings = _settings()
    anysearch_used = False
    anysearch_error = ""
    try:
        result = AnySearchClient(settings=settings).extract(url)
        text = result.text
        anysearch_used = True
    except RuntimeError as exc:
        anysearch_error = str(exc)
        text = f"URL extraction failed for {url}: {anysearch_error}"

    summary, deepseek_used, usage, error = _compress_text(
        task or f"Extract URL context: {url}",
        text,
        "Compress this extracted web page for a coding agent. Preserve URL, headings, facts, versions, dates, code snippets and caveats.",
        use_deepseek,
    )
    decision = choose_model(task=task or url, mode="auto", careful=False, no_compress=False, settings=settings)
    pack = build_context_pack(
        task=task or f"Extract URL context: {url}",
        decision=decision,
        verified_context=summary,
        recommended_implementation="Use this as external context only; verify before changing code.",
    )
    output_path = _write_pack("mcp_url_extract_pack", pack)
    return {
        "kind": "url",
        "anysearch_used": anysearch_used,
        "anysearch_error": anysearch_error,
        "deepseek_used": deepseek_used,
        "deepseek_usage": usage,
        "deepseek_error": error,
        "output_path": output_path,
        "raw_tokens": count_tokens(text),
        "pack_tokens": count_tokens(pack),
        "context_pack": pack,
    }


def _doctor() -> dict[str, Any]:
    settings = _settings()
    return {
        "kind": "doctor",
        "project_root": str(PROJECT_ROOT),
        "env_file": str(ENV_FILE),
        "env_file_exists": ENV_FILE.exists(),
        "deepseek_api_key_configured": bool(settings.deepseek_api_key),
        "deepseek_base_url": settings.deepseek_base_url,
        "anysearch_enabled": settings.anysearch_enabled,
        "anysearch_api_key_configured": bool(settings.anysearch_api_key),
        "anysearch_base_url": settings.anysearch_base_url,
        "flash_model": settings.deepseek_flash_model,
        "pro_model": settings.deepseek_pro_model,
    }


@mcp.tool(
    name="context_saver_prepare",
    description=(
        "The single integrated Context Saver MCP tool. Default kind='project' scans a local project and "
        "uses DeepSeek to prepare a compact context pack. kind='search' uses optional AnySearch-style "
        "search then compression. kind='url' extracts a URL then compression. kind='doctor' reports setup. "
        "Use this one stable tool before broad coding, review, debugging, multi-file work, or token-sensitive work."
    ),
)
def context_saver_prepare(
    task: str = "Prepare compact context",
    kind: str = "project",
    project_path: str = ".",
    query: str = "",
    url: str = "",
    max_files: int = 300,
    max_depth: int = 5,
    max_results: int = 5,
    domain: str = "",
    sub_domain: str = "",
    sub_domain_params: dict[str, Any] | None = None,
    use_deepseek: bool = True,
) -> dict[str, Any]:
    normalized = kind.strip().lower()
    if normalized == "doctor":
        return _doctor()
    if normalized == "search":
        return _search_pack(task, query or task, max_results, domain, sub_domain, sub_domain_params, use_deepseek)
    if normalized == "url":
        if not url:
            return {"kind": "url", "error": "url is required when kind='url'"}
        return _url_pack(task, url, use_deepseek)
    return _project_pack(task, project_path, max_files, max_depth, use_deepseek)


def prepare_project_context(
    task: str,
    project_path: str = ".",
    max_files: int = 300,
    max_depth: int = 5,
    use_deepseek: bool = True,
) -> dict[str, Any]:
    return _project_pack(task, project_path, max_files, max_depth, use_deepseek)


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
