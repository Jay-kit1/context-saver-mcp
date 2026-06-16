import zipfile
from pathlib import Path

import pytest

from context_saver.archive_extract import extract_archive_texts, prevent_path_traversal, safe_extract_archive
from context_saver.archive_scan import build_archive_manifest
from context_saver.codex_pack import build_archive_pack
from context_saver.config import load_settings
from context_saver.router import choose_model


def _make_zip(path: Path):
    with zipfile.ZipFile(path, "w") as zf:
        zf.writestr("README.md", "# Hello")
        zf.writestr("node_modules/pkg/index.js", "ignored")
        zf.writestr("large.txt", "x" * 1000)


def test_zip_manifest_and_skip_node_modules(tmp_path):
    archive = tmp_path / "sample.zip"
    _make_zip(archive)
    result = extract_archive_texts(archive)
    try:
        assert result.manifest.total_files >= 3
        assert any("node_modules" in key for key in result.skipped)
    finally:
        import shutil

        shutil.rmtree(result.extracted_dir, ignore_errors=True)


def test_limit_max_files(tmp_path):
    archive = tmp_path / "sample.zip"
    _make_zip(archive)
    result = extract_archive_texts(archive)
    try:
        assert result.manifest.total_files >= 1
    finally:
        import shutil

        shutil.rmtree(result.extracted_dir, ignore_errors=True)


def test_reject_path_traversal(tmp_path):
    archive = tmp_path / "bad.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("../escape.txt", "bad")
    assert not prevent_path_traversal("../escape.txt")
    with pytest.raises(ValueError):
        safe_extract_archive(archive, tmp_path / "out")


def test_archive_pack_contains_required_sections(tmp_path):
    decision = choose_model("archive", settings=load_settings())
    pack = build_archive_pack(tmp_path / "x.zip", decision, "manifest", ["README.md"], ["bin.dat"], "summary", "checked")
    assert "Archive Manifest" in pack
    assert "Checked Scope" in pack


def test_oversize_file_skipped(tmp_path):
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("huge.txt", "x" * 2048)
    from context_saver.archive_extract import ArchiveOptions

    result = extract_archive_texts(archive, ArchiveOptions(max_single_file_mb=0))
    try:
        assert "huge.txt" in result.skipped
    finally:
        import shutil

        shutil.rmtree(result.extracted_dir, ignore_errors=True)
