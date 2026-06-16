from __future__ import annotations

from pathlib import Path

TEXT_EXTENSIONS = {
    ".txt", ".md", ".log", ".json", ".yaml", ".yml", ".toml", ".ini", ".csv",
}
CODE_EXTENSIONS = {
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".cpp", ".c", ".h", ".cs",
    ".go", ".rs", ".php", ".html", ".css", ".scss", ".vue", ".svelte", ".sql",
    ".sh", ".bat", ".ps1",
}
DOCUMENT_EXTENSIONS = {".pdf", ".docx"}
ARCHIVE_EXTENSIONS = {".zip", ".tar", ".tar.gz", ".tgz", ".7z", ".rar"}
BINARY_EXTENSIONS = {
    ".exe", ".dll", ".so", ".dylib", ".png", ".jpg", ".jpeg", ".gif", ".webp",
    ".mp4", ".mov", ".mp3", ".wav", ".pdfa",
}
SKIP_PARTS = {
    ".git", "node_modules", "dist", "build", "coverage", ".next", ".nuxt",
    "target", ".venv", "venv", "__pycache__", "pycache", ".pytest_cache",
    "logs", "outputs", ".DS_Store",
}


def _archive_suffix(path: Path) -> str:
    name = path.name.lower()
    if name.endswith(".tar.gz"):
        return ".tar.gz"
    return path.suffix.lower()


def is_supported_archive(path: str | Path) -> bool:
    return _archive_suffix(Path(path)) in ARCHIVE_EXTENSIONS


def is_probably_binary(path: str | Path) -> bool:
    p = Path(path)
    if p.suffix.lower() in BINARY_EXTENSIONS:
        return True
    if p.exists() and p.is_file():
        try:
            return b"\0" in p.read_bytes()[:4096]
        except OSError:
            return True
    return False


def should_skip_path(path: str | Path) -> bool:
    p = Path(path)
    return any(part in SKIP_PARTS for part in p.parts)


def detect_file_type(path: str | Path) -> str:
    p = Path(path)
    suffix = _archive_suffix(p)
    if suffix in ARCHIVE_EXTENSIONS:
        return "archive"
    if p.suffix.lower() in DOCUMENT_EXTENSIONS:
        return "document"
    if p.suffix.lower() in CODE_EXTENSIONS:
        return "code"
    if p.suffix.lower() in TEXT_EXTENSIONS:
        return "text"
    if is_probably_binary(p):
        return "binary"
    return "unknown"


def is_supported_file(path: str | Path) -> bool:
    if should_skip_path(path):
        return False
    p = Path(path)
    return detect_file_type(p) in {"text", "code", "document", "archive"}
