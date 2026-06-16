from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field


class ModelChoice(str, Enum):
    FLASH = "flash"
    PRO = "pro"


@dataclass(frozen=True)
class RoutingDecision:
    model_choice: ModelChoice
    mode: str
    context_window: int
    internal_input_budget: int
    output_tokens: int
    reason: str


class TokenBudget(BaseModel):
    model: str
    mode: str
    context_window: int
    internal_input_budget: int
    output_tokens: int
    safety_margin_tokens: int = 2048


class UsageReport(BaseModel):
    input_tokens: int
    output_tokens: int
    total_tokens: int
    cost_cny: float | None = None
    approximate: bool = True


class SearchPack(BaseModel):
    query: str
    key_findings: list[str] = Field(default_factory=list)
    useful_sources: list[str] = Field(default_factory=list)
    notes: str = ""


class CodexContextPack(BaseModel):
    task: str
    verified_context: str = ""
    recommended_implementation: str = ""
    files_to_inspect: list[str] = Field(default_factory=list)
    files_to_avoid: list[str] = Field(default_factory=list)
    constraints_for_codex: list[str] = Field(default_factory=list)
    minimal_verification: list[str] = Field(default_factory=list)


class ExtractPack(BaseModel):
    file: Path
    file_type: str
    extracted_summary: str
    key_points: list[str] = Field(default_factory=list)
    important_details_preserved: list[str] = Field(default_factory=list)
    possible_issues: list[str] = Field(default_factory=list)


class ArchiveMember(BaseModel):
    path: str
    size: int = 0
    is_dir: bool = False
    extension: str = ""
    skipped: bool = False
    reason: str = ""


class ArchiveManifest(BaseModel):
    total_files: int = 0
    readable_files: int = 0
    skipped_files: int = 0
    total_size: int = 0
    main_dirs: list[str] = Field(default_factory=list)
    main_file_types: dict[str, int] = Field(default_factory=dict)
    members: list[ArchiveMember] = Field(default_factory=list)


class ArchiveExtractionResult(BaseModel):
    extracted_dir: Path
    manifest: ArchiveManifest
    read_files: dict[str, str] = Field(default_factory=dict)
    skipped: dict[str, str] = Field(default_factory=dict)


class RankedFile(BaseModel):
    path: str
    score: int
    reason: str


class ArchivePack(BaseModel):
    archive: Path
    manifest: ArchiveManifest
    important_files: list[str] = Field(default_factory=list)
    ignored_files: list[str] = Field(default_factory=list)
    checked_scope: str = ""


class ProjectScanPack(BaseModel):
    project_root: Path
    file_tree_summary: str
    important_files: list[str] = Field(default_factory=list)
    ignored_paths: list[str] = Field(default_factory=list)
    suggested_codex_scope: list[str] = Field(default_factory=list)


class ReviewPack(BaseModel):
    input_path: Path
    user_goal: str = ""
    checked_scope: str = ""
    findings: list[str] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
