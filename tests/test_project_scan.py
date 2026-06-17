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


def test_scan_skips_sensitive_env_but_keeps_example(tmp_path):
    (tmp_path / ".env").write_text("DEEPSEEK_API_KEY=secret")
    (tmp_path / ".env.example").write_text("DEEPSEEK_API_KEY=sk-your-key")
    (tmp_path / ".tools").mkdir()
    (tmp_path / ".tools" / "helper.txt").write_text("local tool")

    result = scan_project(tmp_path)

    assert "- .env\n" not in f'{result["file_tree_summary"]}\n'
    assert ".tools/helper.txt" not in result["file_tree_summary"]
    assert ".env.example" in result["file_tree_summary"]
    assert ".env" in result["ignored_paths"]
    assert ".tools" in result["ignored_paths"]


def test_scan_pack_contains_suggested_scope(tmp_path):
    result = scan_project(tmp_path)
    pack = build_project_scan_pack(tmp_path, result)
    assert "Suggested Codex Scope" in pack
