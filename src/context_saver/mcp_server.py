from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

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
        "Use context_saver_prepare before broad local coding, review, debugging, "
        "project orientation, multi-file work, archive/file extraction, or token-sensitive work. "
        "It compresses local project context with DeepSeek when configured."
    ),
)


def _settings():
    return load_settings(ENV_FILE if ENV_FILE.exists() else None)


def _write_pack(prefix: str, content: str) -> str:
    output_path = timestamped_output(prefix, output_dir=PROJECT_ROOT / "outputs")
    output_path.write_text(content, encoding="utf-8")
    return str(output_path)


def prepare_project_context(
    task: str,
    project_path: str = ".",
    max_files: int = 300,
    max_depth: int = 5,
    use_deepseek: bool = True,
) -> dict[str, Any]:
    settings = _settings()
    root = Path(project_path).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    scan = scan_project(root, max_files=max_files, max_depth=max_depth, with_summary=True)
    scan_pack = build_project_scan_pack(root, scan)
    decision = choose_model(task=task, mode="auto", careful=False, no_compress=False, settings=settings)

    deepseek_used = False
    usage: dict[str, Any] | None = None
    summary = ""
    error = ""
    if use_deepseek and settings.deepseek_api_key:
        try:
            result = DeepSeekClient(settings=settings).chat(
                [
                    {
                        "role": "user",
                        "content": (
                            "Compress this project scan into a compact Codex context pack. "
                            "Preserve important file paths, likely implementation entry points, "
                            "ignored paths, risks, and minimal next files to inspect.\n\n"
                            f"Task: {task}\n\n{scan_pack}"
                        ),
                    }
                ],
                model=decision.model_choice,
                max_tokens=min(decision.output_tokens, settings.normal_pack_max_tokens),
            )
            summary = result.content
            usage = result.usage
            deepseek_used = True
        except RuntimeError as exc:
            error = str(exc)

    if not summary:
        summary = simple_summary(scan_pack, max_tokens=settings.normal_pack_tokens)

    pack = build_context_pack(
        task=task,
        decision=decision,
        verified_context=summary,
        recommended_implementation=(
            "Inspect only the suggested files first. Keep changes scoped and run minimal verification."
        ),
        files_to_inspect=scan["suggested_codex_scope"],
    )
    output_path = _write_pack("mcp_context_pack", pack)

    return {
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


@mcp.tool(
    name="context_saver_prepare",
    description=(
        "Default first step before broad local Codex work. Scan a project and use DeepSeek "
        "to prepare a compact context pack. Use before coding in repos, bug fixing, review, "
        "debugging, multi-file changes, or reading/searching many files."
    ),
)
def context_saver_prepare(
    task: str,
    project_path: str = ".",
    max_files: int = 300,
    max_depth: int = 5,
    use_deepseek: bool = True,
) -> dict[str, Any]:
    return prepare_project_context(task, project_path, max_files, max_depth, use_deepseek)


@mcp.tool(
    name="context_saver_scan",
    description="Fast local project scan without DeepSeek. Use only when model-powered compression is not needed.",
)
def context_saver_scan(project_path: str = ".", max_files: int = 300, max_depth: int = 5) -> dict[str, Any]:
    root = Path(project_path).expanduser()
    if not root.is_absolute():
        root = Path.cwd() / root
    scan = scan_project(root, max_files=max_files, max_depth=max_depth, with_summary=True)
    pack = build_project_scan_pack(root, scan)
    output_path = _write_pack("mcp_project_scan", pack)
    return {
        "deepseek_used": False,
        "project_path": str(root),
        "output_path": output_path,
        "pack_tokens": count_tokens(pack),
        "suggested_files": scan["suggested_codex_scope"],
        "ignored_paths": scan["ignored_paths"],
        "scan_pack": pack,
    }


@mcp.tool(name="context_saver_doctor", description="Check whether Context Saver MCP can see the DeepSeek API key.")
def context_saver_doctor() -> dict[str, Any]:
    settings = _settings()
    return {
        "project_root": str(PROJECT_ROOT),
        "env_file": str(ENV_FILE),
        "env_file_exists": ENV_FILE.exists(),
        "deepseek_api_key_configured": bool(settings.deepseek_api_key),
        "deepseek_base_url": settings.deepseek_base_url,
        "flash_model": settings.deepseek_flash_model,
        "pro_model": settings.deepseek_pro_model,
    }


def main() -> None:
    mcp.run("stdio")


if __name__ == "__main__":
    main()
