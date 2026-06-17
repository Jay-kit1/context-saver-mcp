from __future__ import annotations

from collections import Counter
from pathlib import Path

from .file_types import should_skip_path


IMPORTANT_NAMES = {
    "README.md", "pyproject.toml", "package.json", "requirements.txt", "Cargo.toml",
    "go.mod", "Dockerfile", "docker-compose.yml", ".env.example", "AGENTS.md",
}


def scan_project(
    root: str | Path,
    max_files: int = 300,
    max_depth: int = 5,
    with_summary: bool = False,
    max_single_file_summary_size: int = 200_000,
) -> dict:
    root_path = Path(root).resolve()
    files: list[Path] = []
    ignored: list[str] = []
    extensions: Counter[str] = Counter()

    def walk_dir(directory: Path) -> None:
        if len(files) >= max_files:
            return
        try:
            children = sorted(directory.iterdir(), key=lambda item: (item.is_file(), item.name.lower()))
        except OSError:
            return
        for path in children:
            rel = path.relative_to(root_path)
            if len(rel.parts) > max_depth:
                ignored.append(str(rel))
                continue
            if should_skip_path(rel):
                ignored.append(str(rel))
                continue
            if path.is_dir():
                walk_dir(path)
                continue
            if path.is_file():
                files.append(rel)
                extensions[path.suffix.lower() or "[none]"] += 1
                if len(files) >= max_files:
                    ignored.append("max_files limit reached")
                    return

    walk_dir(root_path)

    important = [
        str(path) for path in files
        if path.name in IMPORTANT_NAMES or path.parts[0] in {"src", "app", "lib", "tests"}
    ][:80]
    tree_lines = [f"- {path}" for path in files[:max_files]]
    if with_summary:
        tree_lines.append("")
        tree_lines.append("Small file summaries:")
        for rel in files[:30]:
            full = root_path / rel
            if full.stat().st_size <= max_single_file_summary_size:
                tree_lines.append(f"- {rel}: {full.stat().st_size} bytes")

    return {
        "root": root_path,
        "file_tree_summary": "\n".join(tree_lines),
        "important_files": important,
        "ignored_paths": ignored[:120],
        "suggested_codex_scope": important[:20],
        "extension_counts": dict(extensions),
    }
