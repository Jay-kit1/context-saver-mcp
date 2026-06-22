from context_saver.mcp_server import context_saver_prepare, prepare_project_context


def test_prepare_project_context_without_deepseek(tmp_path):
    (tmp_path / "README.md").write_text("# Demo\n")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "app.py").write_text("print('hi')\n")

    result = prepare_project_context("Inspect demo project", str(tmp_path), use_deepseek=False)

    assert result["deepseek_used"] is False
    assert result["pack_tokens"] > 0
    assert "context_pack" in result
    assert "README.md" in result["context_pack"]


def test_context_saver_prepare_doctor_mode_reports_env_status():
    result = context_saver_prepare(kind="doctor")

    assert result["project_root"]
    assert result["env_file"].endswith(".env")
    assert "deepseek_api_key_configured" in result
    assert "anysearch_api_key_configured" in result


def test_context_saver_prepare_search_falls_back_when_anysearch_fails(monkeypatch):
    class BrokenClient:
        def __init__(self, *args, **kwargs):
            pass

        def search(self, *args, **kwargs):
            raise RuntimeError("AnySearch unavailable")

    monkeypatch.setattr("context_saver.mcp_server.AnySearchClient", BrokenClient)

    result = context_saver_prepare(kind="search", query="hello", use_deepseek=False)

    assert result["anysearch_used"] is False
    assert "AnySearch unavailable" in result["anysearch_error"]
    assert result["deepseek_used"] is False
    assert "Search query recorded locally" in result["context_pack"]
