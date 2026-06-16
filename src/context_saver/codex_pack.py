from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .models import RoutingDecision

DEFAULT_FILES_TO_AVOID = [
    "node_modules", ".git", "dist", "build", "coverage", "logs", "large lock files",
]

DEFAULT_CODEX_CONSTRAINTS = [
    "Do not use web search.",
    "Do not refactor unrelated files.",
    "Only inspect files relevant to the task.",
    "If information is missing, stop and ask the user.",
    "Run minimal verification only.",
]


def build_model_budget_section(decision: RoutingDecision) -> str:
    return "\n".join(
        [
            f"- Model used: {decision.model_choice.value}",
            f"- Mode: {decision.mode}",
            f"- Context window: {decision.context_window} tokens",
            f"- Internal input budget: {decision.internal_input_budget} tokens",
            f"- Output tokens reserved: {decision.output_tokens}",
            f"- Routing reason: {decision.reason}",
        ]
    )


def _section(title: str, body: str | list[str]) -> str:
    if isinstance(body, list):
        content = "\n".join(f"- {item}" for item in body) if body else "- not available"
    else:
        content = body.strip() or "not available"
    return f"## {title}\n\n{content}"


def build_codex_prompt_from_pack(task: str, context: str, files_to_inspect: list[str] | None = None) -> str:
    files = "\n".join(f"- {path}" for path in (files_to_inspect or [])) or "- not available"
    return (
        f"Task: {task}\n\n"
        f"Use only this context. Do not use web search.\n\n"
        f"Relevant files:\n{files}\n\n"
        f"Context:\n{context}\n\n"
        "Make the smallest safe change and run minimal verification."
    )


def build_context_pack(
    task: str,
    decision: RoutingDecision,
    verified_context: str = "",
    recommended_implementation: str = "",
    files_to_inspect: list[str] | None = None,
    minimal_verification: list[str] | None = None,
) -> str:
    files_to_inspect = files_to_inspect or []
    constraints = DEFAULT_CODEX_CONSTRAINTS
    prompt = build_codex_prompt_from_pack(task, verified_context, files_to_inspect)
    sections = [
        "# Codex Context Pack",
        _section("Task", task),
        _section("Model And Budget", build_model_budget_section(decision)),
        _section("Verified Context", verified_context),
        _section("Recommended Implementation", recommended_implementation),
        _section("Files To Inspect", files_to_inspect),
        _section("Files To Avoid", DEFAULT_FILES_TO_AVOID),
        _section("Constraints For Codex", constraints),
        _section("Minimal Verification", minimal_verification or ["Run the smallest relevant test or syntax check."]),
        _section("Prompt To Paste Into Codex", f"```text\n{prompt}\n```"),
    ]
    return "\n\n".join(sections) + "\n"


def build_search_pack(query: str, decision: RoutingDecision, findings: list[str] | None = None, sources: list[str] | None = None, notes: str = "") -> str:
    sections = [
        "# Search Pack",
        _section("Query", query),
        _section("Model And Budget", build_model_budget_section(decision)),
        _section("Key Findings", findings or ["No live search results are available in this local first version."]),
        _section("Useful Sources", sources or ["not available"]),
        _section("Notes", notes or "This pack reserves source structure for future browser/API search integration."),
        _section("Suggested Next Step", "Paste this pack into Codex or run a more specific csp command with local files."),
    ]
    return "\n\n".join(sections) + "\n"


def build_extract_pack(
    file: Path,
    file_type: str,
    decision: RoutingDecision,
    extracted_summary: str,
    key_points: list[str] | None = None,
    possible_issues: list[str] | None = None,
) -> str:
    sections = [
        "# Extract Pack",
        _section("File", str(file)),
        _section("File Type", file_type),
        _section("Mode", decision.mode),
        _section("Model And Budget", build_model_budget_section(decision)),
        _section("Extracted Summary", extracted_summary),
        _section("Key Points", key_points or ["See extracted summary."]),
        _section("Important Details Preserved", ["Paths, error text, headings, code symbols and configuration-like lines were preserved when detected."]),
        _section("Possible Issues", possible_issues or ["not available"]),
        _section("Useful Context For Codex", extracted_summary),
        _section("Suggested Next Step", "Ask Codex to inspect only the relevant files and run minimal verification."),
    ]
    return "\n\n".join(sections) + "\n"


def build_archive_pack(
    archive: Path,
    decision: RoutingDecision,
    manifest_text: str,
    important_files: list[str],
    ignored_files: list[str],
    extracted_summary: str,
    checked_scope: str,
    missing: str = "",
) -> str:
    sections = [
        "# Archive Pack",
        _section("Archive", str(archive)),
        _section("Mode", decision.mode),
        _section("Model And Budget", build_model_budget_section(decision)),
        _section("Archive Manifest", manifest_text),
        _section("Important Files", important_files),
        _section("Ignored Files", ignored_files),
        _section("Extracted Summary", extracted_summary),
        _section("Cross-File Relationships", "Inferred from directory and filename grouping; deeper semantic relationships require user goal or Pro review."),
        _section("Key Findings", ["Important files are ranked by known project names, source directories and user goal overlap."]),
        _section("Possible Issues", ["Skipped files may contain relevant information if they were binary, oversized or under ignored directories."]),
        _section("Useful Context For Codex", extracted_summary),
        _section("Checked Scope", checked_scope),
        _section("Missing Or Unclear Information", missing or "not available"),
        _section("Suggested Next Step", "Paste this pack into Codex and inspect only the listed important files."),
    ]
    return "\n\n".join(sections) + "\n"


def build_review_pack(
    input_path: Path,
    decision: RoutingDecision,
    user_goal: str,
    checked_scope: str,
    key_content: str,
    findings: list[str] | None = None,
    evidence: list[str] | None = None,
) -> str:
    sections = [
        "# Review Pack",
        _section("Input", str(input_path)),
        _section("Model And Budget", build_model_budget_section(decision)),
        _section("Review Mode", "careful-review"),
        _section("User Goal", user_goal or "Review input carefully."),
        _section("Checked Scope", checked_scope),
        _section("Key Content", key_content),
        _section("Findings", findings or ["No concrete issue detected by local extraction only."]),
        _section("Potential Problems", ["Model-free local review cannot fully judge correctness without domain-specific goal details."]),
        _section("Evidence", evidence or ["Evidence not available; no line-specific issue was found."]),
        _section("Missing Or Unclear Information", "Any unread, skipped or binary content is listed in checked scope when applicable."),
        _section("Suggested Fixes Or Next Step", "Use Codex for targeted code changes after confirming these findings."),
        _section("Context For Codex", key_content),
    ]
    return "\n\n".join(sections) + "\n"


def build_project_scan_pack(root: Path, scan: dict) -> str:
    sections = [
        "# Project Scan Pack",
        _section("Project Root", str(root)),
        _section("File Tree Summary", scan["file_tree_summary"]),
        _section("Important Files", scan["important_files"]),
        _section("Ignored Paths", scan["ignored_paths"]),
        _section("Suggested Codex Scope", scan["suggested_codex_scope"]),
        _section("Prompt To Paste Into Codex", build_codex_prompt_from_pack("Inspect this project scope.", scan["file_tree_summary"], scan["suggested_codex_scope"])),
    ]
    return "\n\n".join(sections) + "\n"


def timestamped_output(prefix: str, output_dir: Path = Path("outputs")) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return output_dir / f"{prefix}_{stamp}.md"
