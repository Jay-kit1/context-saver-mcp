from __future__ import annotations

from collections import Counter
from pathlib import Path

from .file_types import is_probably_binary, should_skip_path
from .models import ArchiveManifest, ArchiveMember, RankedFile


def should_skip_archive_file(path: Path, size: int, extension: str) -> str:
    if should_skip_path(path):
        return "ignored path"
    if is_probably_binary(path) or extension.lower() in {".png", ".jpg", ".jpeg", ".gif", ".mp4", ".mp3", ".wav", ".exe"}:
        return "binary or media file"
    return ""


def build_archive_manifest(extracted_dir: str | Path) -> ArchiveManifest:
    root = Path(extracted_dir)
    members: list[ArchiveMember] = []
    dirs: Counter[str] = Counter()
    types: Counter[str] = Counter()
    total_size = 0
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        size = path.stat().st_size if path.is_file() else 0
        total_size += size
        if rel.parts:
            dirs[rel.parts[0]] += 1
        ext = path.suffix.lower() or "[none]"
        if path.is_file():
            types[ext] += 1
        reason = should_skip_archive_file(rel, size, ext) if path.is_file() else ""
        members.append(ArchiveMember(path=str(rel), size=size, is_dir=path.is_dir(), extension=ext, skipped=bool(reason), reason=reason))
    files = [m for m in members if not m.is_dir]
    return ArchiveManifest(
        total_files=len(files),
        readable_files=len([m for m in files if not m.skipped]),
        skipped_files=len([m for m in files if m.skipped]),
        total_size=total_size,
        main_dirs=[name for name, _ in dirs.most_common(20)],
        main_file_types=dict(types.most_common(20)),
        members=members,
    )


def rank_archive_files(manifest: ArchiveManifest, user_goal: str = "") -> list[RankedFile]:
    important_names = {"README.md", "pyproject.toml", "package.json", "requirements.txt", "Dockerfile"}
    ranked: list[RankedFile] = []
    for member in manifest.members:
        if member.is_dir or member.skipped:
            continue
        score = 1
        path = Path(member.path)
        if path.name in important_names:
            score += 5
        if path.parts and path.parts[0] in {"src", "app", "lib", "tests", "docs"}:
            score += 3
        if user_goal and any(word.lower() in member.path.lower() for word in user_goal.split()):
            score += 2
        ranked.append(RankedFile(path=member.path, score=score, reason="ranked by path, type and user goal"))
    return sorted(ranked, key=lambda item: item.score, reverse=True)


def group_files_by_type_and_dir(manifest: ArchiveManifest) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {}
    for member in manifest.members:
        if member.is_dir:
            continue
        key = f"{Path(member.path).parts[0] if Path(member.path).parts else '.'}:{member.extension or '[none]'}"
        groups.setdefault(key, []).append(member.path)
    return groups


def summarize_archive_by_layers(manifest: ArchiveManifest, read_files: dict[str, str]) -> str:
    lines = [
        f"Files: {manifest.total_files}",
        f"Readable: {manifest.readable_files}",
        f"Skipped: {manifest.skipped_files}",
        "Top file types: " + ", ".join(f"{k}={v}" for k, v in manifest.main_file_types.items()),
    ]
    for path, text in list(read_files.items())[:20]:
        preview = text.replace("\n", " ")[:500]
        lines.append(f"- {path}: {preview}")
    return "\n".join(lines)
