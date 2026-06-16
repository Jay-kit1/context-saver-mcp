from __future__ import annotations

import shutil
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from .archive_extract import extract_archive_texts
from .archive_scan import rank_archive_files, summarize_archive_by_layers
from .codex_pack import (
    build_archive_pack,
    build_context_pack,
    build_extract_pack,
    build_project_scan_pack,
    build_review_pack,
    build_search_pack,
    timestamped_output,
)
from .config import load_settings
from .file_extract import extract_text_from_file
from .file_types import detect_file_type
from .project_scan import scan_project
from .review import review_input
from .router import choose_model
from .search import local_search_stub
from .summarizer import model_summary, simple_summary
from .token_utils import estimate_tokens

app = typer.Typer(help="Context Saver MCP: local context packs for coding agents.")
console = Console()


def _decision(task: str, flash: bool, pro: bool, auto: bool, careful: bool, no_compress: bool):
    mode = "auto"
    if flash:
        mode = "flash"
    elif pro:
        mode = "pro"
    elif auto:
        mode = "auto"
    return choose_model(task=task, mode=mode, careful=careful, no_compress=no_compress, settings=load_settings())


def _write_pack(prefix: str, content: str) -> Path:
    output_path = timestamped_output(prefix)
    output_path.write_text(content, encoding="utf-8")
    console.print(f"[green]Saved[/green] {output_path}")
    return output_path


def _summarize(text: str, decision, instruction: str, local_max_tokens: int) -> str:
    try:
        generated = model_summary(text, decision, instruction, settings=load_settings())
    except RuntimeError as exc:
        console.print(f"[yellow]DeepSeek unavailable: {exc}. Using local extraction fallback.[/yellow]")
        generated = None
    if generated:
        return generated
    console.print("[yellow]DeepSeek API key is not configured. Run `csp configure` when you want model-powered compression.[/yellow]")
    return simple_summary(text, max_tokens=local_max_tokens)


@app.command()
def configure(
    env_path: Path = typer.Option(Path(".env"), "--env-file", help="Where to save local settings."),
):
    """Save your DeepSeek API key into a local .env file."""
    api_key = typer.prompt("DeepSeek API key", hide_input=True, confirmation_prompt=True)
    base_url = typer.prompt("DeepSeek base URL", default="https://api.deepseek.com")
    flash_model = typer.prompt("Flash model", default="deepseek-v4-flash")
    pro_model = typer.prompt("Pro model", default="deepseek-v4-pro")

    existing: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8").splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                existing[key.strip()] = value.strip()

    existing.update(
        {
            "DEEPSEEK_API_KEY": api_key,
            "DEEPSEEK_BASE_URL": base_url,
            "DEEPSEEK_FLASH_MODEL": flash_model,
            "DEEPSEEK_PRO_MODEL": pro_model,
            "MODEL_ROUTING_MODE": existing.get("MODEL_ROUTING_MODE", "auto"),
        }
    )
    defaults = {
        "FLASH_CONTEXT_TOKENS": "600000",
        "PRO_CONTEXT_TOKENS": "1000000",
        "FLASH_INTERNAL_INPUT_TOKENS": "64000",
        "PRO_INTERNAL_INPUT_TOKENS": "160000",
        "CAREFUL_INTERNAL_INPUT_TOKENS": "240000",
        "NO_COMPRESS_INTERNAL_INPUT_TOKENS": "320000",
        "DEFAULT_OUTPUT_TOKENS": "4096",
        "CAREFUL_OUTPUT_TOKENS": "8192",
        "NO_COMPRESS_OUTPUT_TOKENS": "12000",
        "NORMAL_PACK_TOKENS": "3000",
        "NORMAL_PACK_MAX_TOKENS": "6000",
        "CAREFUL_PACK_TOKENS": "12000",
        "CAREFUL_PACK_MAX_TOKENS": "30000",
        "NO_COMPRESS_PACK_MAX_TOKENS": "60000",
        "ARCHIVE_MAX_FILES": "500",
        "ARCHIVE_MAX_TOTAL_SIZE_MB": "300",
        "ARCHIVE_MAX_SINGLE_FILE_MB": "20",
        "ARCHIVE_MAX_TEXT_FILES_READ": "120",
        "ARCHIVE_MAX_FULL_READ_FILES": "40",
        "ARCHIVE_MAX_DEPTH": "5",
    }
    for key, value in defaults.items():
        existing.setdefault(key, value)

    ordered_keys = [
        "DEEPSEEK_API_KEY",
        "DEEPSEEK_BASE_URL",
        "DEEPSEEK_FLASH_MODEL",
        "DEEPSEEK_PRO_MODEL",
        "MODEL_ROUTING_MODE",
        *defaults.keys(),
    ]
    lines = [f"{key}={existing[key]}" for key in ordered_keys]
    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    console.print(f"[green]Saved local settings to[/green] {env_path}")
    console.print("[yellow]Do not commit this file. It is ignored by .gitignore.[/yellow]")


@app.command()
def doctor():
    """Check local setup and API-key status."""
    settings = load_settings()
    console.print("[bold]Context Saver MCP Doctor[/bold]")
    console.print(f"Python package: [green]installed[/green]")
    console.print(f"Outputs directory: {'[green]ok[/green]' if Path('outputs').exists() else '[red]missing[/red]'}")
    console.print(f"DeepSeek base URL: {settings.deepseek_base_url}")
    if settings.deepseek_api_key:
        console.print("DeepSeek API key: [green]configured[/green]")
    else:
        console.print("DeepSeek API key: [yellow]not configured[/yellow]")
        console.print("Run `csp configure` before model-powered compression or API calls.")
    console.print("Git ignore check: `.env` and `outputs/*.md` should be ignored by this project.")


@app.command()
def codex(
    task: str,
    flash: bool = typer.Option(False, "--flash", help="Force Flash routing."),
    pro: bool = typer.Option(False, "--pro", help="Force Pro routing."),
    auto: bool = typer.Option(False, "--auto", help="Use automatic routing."),
    careful: bool = typer.Option(False, "--careful", help="Use Pro careful-review mode."),
    no_compress: bool = typer.Option(False, "--no-compress", help="Use Pro no-compress mode."),
):
    """Generate a Codex Context Pack."""
    decision = _decision(task, flash, pro, auto, careful, no_compress)
    pack = build_context_pack(
        task=task,
        decision=decision,
        verified_context="No local files were provided. This pack records task, budget and Codex constraints.",
        recommended_implementation="Let Codex inspect only relevant project files, then make the smallest safe change.",
    )
    _write_pack("context_pack", pack)
    console.print(pack)


@app.command()
def search(
    query: str,
    flash: bool = typer.Option(False, "--flash"),
    pro: bool = typer.Option(False, "--pro"),
    auto: bool = typer.Option(False, "--auto"),
    careful: bool = typer.Option(False, "--careful"),
    no_compress: bool = typer.Option(False, "--no-compress"),
):
    """Create a Search Pack. The first version records local structured results."""
    decision = _decision(query, flash, pro, auto, careful, no_compress)
    model_text = _summarize(
        query,
        decision,
        "Prepare a concise Search Pack draft. Preserve exact technologies, versions, commands and uncertainties.",
        local_max_tokens=1000,
    )
    findings = [model_text] if model_text else local_search_stub(query)
    pack = build_search_pack(query, decision, findings=findings)
    _write_pack("search_pack", pack)
    console.print(pack)


@app.command()
def extract(
    path: Path,
    codex: bool = typer.Option(False, "--codex"),
    search_pack: bool = typer.Option(False, "--search"),
    flash: bool = typer.Option(False, "--flash"),
    pro: bool = typer.Option(False, "--pro"),
    auto: bool = typer.Option(False, "--auto"),
    careful: bool = typer.Option(False, "--careful"),
    no_compress: bool = typer.Option(False, "--no-compress"),
):
    """Extract text from a supported file and create an Extract Pack."""
    decision = _decision(str(path), flash, pro, auto, careful, no_compress)
    text = extract_text_from_file(path)
    summary = _summarize(
        text,
        decision,
        "Extract and compress this file for a coding agent. Preserve paths, errors, code symbols, config values, facts and line-like evidence.",
        local_max_tokens=min(decision.internal_input_budget, 3000),
    )
    pack = build_extract_pack(path, detect_file_type(path), decision, summary)
    _write_pack("extract_pack", pack)
    console.print(pack)


@app.command()
def archive(
    path: Path,
    codex: bool = typer.Option(False, "--codex"),
    review: bool = typer.Option(False, "--review"),
    flash: bool = typer.Option(False, "--flash"),
    pro: bool = typer.Option(False, "--pro"),
    auto: bool = typer.Option(False, "--auto"),
    careful: bool = typer.Option(False, "--careful"),
    no_compress: bool = typer.Option(False, "--no-compress"),
    internal_input_tokens: Optional[int] = typer.Option(None, "--internal-input-tokens"),
):
    """Read a supported archive safely and create an Archive Pack."""
    decision = _decision(str(path), flash, pro, auto, careful or review, no_compress)
    result = extract_archive_texts(path)
    try:
        ranked = rank_archive_files(result.manifest, str(path))
        important = [item.path for item in ranked[:40]]
        ignored = [f"{k}: {v}" for k, v in result.skipped.items()]
        manifest_text = "\n".join(
            [
                f"- Total files: {result.manifest.total_files}",
                f"- Supported/readable files: {result.manifest.readable_files}",
                f"- Skipped files: {result.manifest.skipped_files}",
                f"- Total size: {result.manifest.total_size} bytes",
                f"- Main directories: {', '.join(result.manifest.main_dirs) or 'not available'}",
                f"- Main file types: {result.manifest.main_file_types}",
            ]
        )
        layered = summarize_archive_by_layers(result.manifest, result.read_files)
        summary = _summarize(
            layered,
            decision,
            "Summarize this archive for a coding agent. Preserve file paths, file roles, relationships, skipped reasons and risks.",
            local_max_tokens=min(decision.internal_input_budget, 6000),
        )
        checked_scope = (
            f"Fully/partially read files: {', '.join(result.read_files.keys()) or 'none'}\n"
            f"Skipped files and reasons: {', '.join(ignored) or 'none'}"
        )
        pack = build_archive_pack(path, decision, manifest_text, important, ignored, summary, checked_scope)
    finally:
        shutil.rmtree(result.extracted_dir, ignore_errors=True)
    _write_pack("archive_pack", pack)
    console.print(pack)


@app.command()
def review(
    path: Path,
    goal: str = typer.Option("", "--goal", help="Review goal."),
    no_compress: bool = typer.Option(False, "--no-compress"),
):
    """Carefully review a file or archive. Always uses Pro careful-review."""
    decision = choose_model(str(path), mode="pro", careful=True, no_compress=no_compress, settings=load_settings())
    scope, content, evidence = review_input(path)
    key_content = _summarize(
        content,
        decision,
        "Carefully review this input. Preserve evidence, checked scope, possible issues, uncertainty and exact file references.",
        local_max_tokens=min(decision.internal_input_budget, 12000),
    )
    pack = build_review_pack(path, decision, goal, scope, key_content, evidence=evidence)
    _write_pack("review_pack", pack)
    console.print(pack)


@app.command()
def scan(
    path: Path,
    with_summary: bool = typer.Option(False, "--with-summary"),
    max_files: int = typer.Option(300, "--max-files"),
    max_depth: int = typer.Option(5, "--max-depth"),
):
    """Scan a project tree without reading everything."""
    result = scan_project(path, max_files=max_files, max_depth=max_depth, with_summary=with_summary)
    pack = build_project_scan_pack(path, result)
    _write_pack("project_scan", pack)
    console.print(pack)


@app.command()
def summarize(
    path: Path,
    codex_pack: bool = typer.Option(False, "--codex"),
    search_pack: bool = typer.Option(False, "--search"),
    careful: bool = typer.Option(False, "--careful"),
    no_compress: bool = typer.Option(False, "--no-compress"),
):
    """Summarize a txt/md-like file into a Codex or Search Pack."""
    text = extract_text_from_file(path)
    decision = choose_model(str(path), careful=careful, no_compress=no_compress, settings=load_settings())
    summary = _summarize(
        text,
        decision,
        "Summarize this file without losing critical facts, paths, numbers, errors, configuration or user goals.",
        local_max_tokens=min(decision.internal_input_budget, 3000),
    )
    if search_pack:
        pack = build_search_pack(str(path), decision, findings=[summary])
        prefix = "search_pack"
    else:
        pack = build_context_pack(str(path), decision, verified_context=summary)
        prefix = "context_pack"
    _write_pack(prefix, pack)
    console.print(pack)


@app.command("pack")
def pack_command(
    task: str = typer.Argument("Manual context pack"),
    careful: bool = typer.Option(False, "--careful"),
    no_compress: bool = typer.Option(False, "--no-compress"),
):
    """Build a Context Pack from stdin."""
    raw = sys.stdin.read()
    decision = choose_model(task, careful=careful, no_compress=no_compress, settings=load_settings())
    pack = build_context_pack(task, decision, verified_context=raw)
    output_path = _write_pack("context_pack", pack)
    console.print(f"Estimated input tokens: {estimate_tokens(raw)}")
    console.print(pack)
