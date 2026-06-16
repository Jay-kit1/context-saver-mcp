from pathlib import Path

from context_saver.file_types import is_supported_archive, is_supported_file, should_skip_path


def test_supported_file_types():
    assert is_supported_file(Path("app.py"))
    assert is_supported_file(Path("doc.pdf"))
    assert is_supported_archive(Path("archive.zip"))
    assert is_supported_archive(Path("archive.7z"))


def test_unsupported_exe():
    assert not is_supported_file(Path("app.exe"))


def test_skipped_paths():
    assert should_skip_path(Path("node_modules/pkg/index.js"))
    assert should_skip_path(Path(".git/config"))
