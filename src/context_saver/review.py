from __future__ import annotations

from pathlib import Path
import shutil

from .archive_extract import extract_archive_texts
from .file_extract import extract_text_from_file
from .file_types import is_supported_archive


def review_input(path: Path) -> tuple[str, str, list[str]]:
    if is_supported_archive(path):
        result = extract_archive_texts(path)
        try:
            read = ", ".join(result.read_files.keys()) or "none"
            skipped = ", ".join(f"{k} ({v})" for k, v in result.skipped.items()) or "none"
            scope = f"Fully or partially read: {read}\nSkipped: {skipped}"
            content = "\n\n".join(f"## {name}\n{text[:4000]}" for name, text in result.read_files.items())
            evidence = [f"{name}: extracted text available" for name in result.read_files.keys()]
            return scope, content, evidence
        finally:
            shutil.rmtree(result.extracted_dir, ignore_errors=True)
    text = extract_text_from_file(path)
    lines = text.splitlines()
    scope = f"Read file text from {path}; {len(lines)} extracted lines."
    evidence = [f"{path}:1 extracted content begins here"] if lines else [f"{path}: no text extracted"]
    return scope, text, evidence
