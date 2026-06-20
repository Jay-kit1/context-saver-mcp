from context_saver.mcp_server import context_saver_doctor, prepare_project_context


def test_prepare_project_context_without_deepseek(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hi')\n")

    result = prepare_project_context("Inspect demo project", str(tmp_path), use_deepseek=False)

    assert result["deepseek_used"] is False
    assert result["pack_tokens"] > 0
    assert "context_pack" in result
    assert "README.md" in result["context_pack"]


def test_context_saver_doctor_reports_env_status():
    result = context_saver_doctor()

    assert result["project_root"]
    assert result["env_file"].endswith(".env")
    assert "deepseek_api_key_configured" in result
