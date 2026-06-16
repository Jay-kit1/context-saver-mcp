from context_saver.codex_pack import build_project_scan_pack
from context_saver.project_scan import scan_project


def test_scan_skips_node_modules_and_limits(tmp_path):
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hi')")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "x.js").write_text("ignored")
    result = scan_project(tmp_path, max_files=1)
    assert all("node_modules/x.js" not in item for item in result["file_tree_summary"].splitlines())
    assert len(result["important_files"]) <= 1


def test_scan_pack_contains_suggested_scope(tmp_path):
    result = scan_project(tmp_path)
    pack = build_project_scan_pack(tmp_path, result)
    assert "Suggested Codex Scope" in pack
