from __future__ import annotations

import tarfile
import tempfile
import zipfile
from dataclasses import dataclass
from pathlib import Path

import py7zr
import rarfile

from .config import Settings, load_settings
from .file_extract import extract_text_from_file
from .file_types import is_supported_archive, is_supported_file, should_skip_path
from .models import ArchiveExtractionResult, ArchiveManifest, ArchiveMember


def prevent_path_traversal(member_path: str) -> bool:
    path = Path(member_path)
    return not path.is_absolute() and ".." not in path.parts


def _suffix(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".tar.gz"):
        return ".tar.gz"
    return path.suffix.lower()


def list_archive_members(path: str | Path) -> list[ArchiveMember]:
    path = Path(path)
    suffix = _suffix(path)
    members: list[ArchiveMember] = []
    if suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            for info in zf.infolist():
                members.append(ArchiveMember(path=info.filename, size=info.file_size, is_dir=info.is_dir(), extension=Path(info.filename).suffix.lower()))
    elif suffix in {".tar", ".tar.gz", ".tgz"}:
        with tarfile.open(path) as tf:
            for info in tf.getmembers():
                members.append(ArchiveMember(path=info.name, size=info.size, is_dir=info.isdir(), extension=Path(info.name).suffix.lower()))
    elif suffix == ".7z":
        with py7zr.SevenZipFile(path) as archive:
            for info in archive.list():
                members.append(ArchiveMember(path=info.filename, size=getattr(info, "uncompressed", 0) or 0, is_dir=info.is_directory, extension=Path(info.filename).suffix.lower()))
    elif suffix == ".rar":
        with rarfile.RarFile(path) as archive:
            for info in archive.infolist():
                members.append(ArchiveMember(path=info.filename, size=info.file_size, is_dir=info.isdir(), extension=Path(info.filename).suffix.lower()))
    else:
        raise ValueError(f"Unsupported archive: {path}")
    return members


def detect_archive_risk(path: str | Path, settings: Settings | None = None) -> list[str]:
    settings = settings or load_settings()
    risks = []
    members = list_archive_members(path)
    total_size = sum(m.size for m in members)
    if len([m for m in members if not m.is_dir]) > settings.archive_max_files:
        risks.append("archive file count exceeds configured max_files")
    if total_size > settings.archive_max_total_size_mb * 1024 * 1024:
        risks.append("archive total uncompressed size exceeds configured max_total_size")
    for member in members:
        if not prevent_path_traversal(member.path):
            risks.append(f"path traversal rejected: {member.path}")
    return risks


def safe_extract_archive(path: str | Path, target_dir: str | Path) -> Path:
    path = Path(path)
    target = Path(target_dir).resolve()
    if not is_supported_archive(path):
        raise ValueError(f"Unsupported archive: {path}")
    for member in list_archive_members(path):
        if not prevent_path_traversal(member.path):
            raise ValueError(f"Archive member would escape target directory: {member.path}")
    suffix = _suffix(path)
    if suffix == ".zip":
        with zipfile.ZipFile(path) as zf:
            zf.extractall(target)
    elif suffix in {".tar", ".tar.gz", ".tgz"}:
        with tarfile.open(path) as tf:
            try:
                tf.extractall(target, filter="data")
            except TypeError:
                tf.extractall(target)
    elif suffix == ".7z":
        with py7zr.SevenZipFile(path) as archive:
            archive.extractall(target)
    elif suffix == ".rar":
        with rarfile.RarFile(path) as archive:
            archive.extractall(target)
    return target


@dataclass
class ArchiveOptions:
    max_files: int | None = None
    max_single_file_mb: int | None = None
    max_text_files_read: int | None = None
    max_full_read_files: int | None = None


def extract_archive_texts(path: str | Path, options: ArchiveOptions | None = None, settings: Settings | None = None) -> ArchiveExtractionResult:
    settings = settings or load_settings()
    options = options or ArchiveOptions()
    max_files = options.max_files if options.max_files is not None else settings.archive_max_files
    max_single_mb = options.max_single_file_mb if options.max_single_file_mb is not None else settings.archive_max_single_file_mb
    max_single = max_single_mb * 1024 * 1024
    max_text = options.max_text_files_read if options.max_text_files_read is not None else settings.archive_max_text_files_read
    members = list_archive_members(path)
    file_members = [member for member in members if not member.is_dir]
    total_size = sum(member.size for member in file_members)
    if len(file_members) > max_files:
        raise ValueError(f"Archive has {len(file_members)} files, above max_files={max_files}.")
    if total_size > settings.archive_max_total_size_mb * 1024 * 1024:
        raise ValueError(
            f"Archive total size is {total_size} bytes, above max_total_size={settings.archive_max_total_size_mb}MB."
        )
    temp_dir = Path(tempfile.mkdtemp(prefix="csp_archive_"))
    safe_extract_archive(path, temp_dir)
    from .archive_scan import build_archive_manifest, should_skip_archive_file

    manifest = build_archive_manifest(temp_dir)
    read_files: dict[str, str] = {}
    skipped: dict[str, str] = {}
    count = 0
    for member in manifest.members:
        if member.is_dir:
            continue
        if count >= max_files:
            skipped[member.path] = "max_files limit reached"
            continue
        full_path = temp_dir / member.path
        reason = should_skip_archive_file(Path(member.path), member.size, member.extension)
        if member.size > max_single:
            reason = "file exceeds max single file size"
        if reason:
            member.skipped = True
            member.reason = reason
            skipped[member.path] = reason
            continue
        if len(read_files) >= max_text:
            skipped[member.path] = "max text files read limit reached"
            continue
        if is_supported_file(full_path) and not should_skip_path(Path(member.path)):
            try:
                read_files[member.path] = extract_text_from_file(full_path)
            except Exception as exc:
                skipped[member.path] = f"read error: {exc}"
        else:
            skipped[member.path] = "unsupported file type"
        count += 1
    manifest.skipped_files = len(skipped)
    manifest.readable_files = len(read_files)
    return ArchiveExtractionResult(extracted_dir=temp_dir, manifest=manifest, read_files=read_files, skipped=skipped)
