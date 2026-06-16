from typer.testing import CliRunner

from context_saver.cli import app


def test_doctor_reports_missing_key(monkeypatch):
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    runner = CliRunner()
    result = runner.invoke(app, ["doctor"])
    assert result.exit_code == 0
    assert "DeepSeek API key" in result.output


def test_configure_writes_env(tmp_path):
    runner = CliRunner()
    env_path = tmp_path / ".env"
    result = runner.invoke(
        app,
        ["configure", "--env-file", str(env_path)],
        input="sk-test\nsk-test\n\n\n\n",
    )
    assert result.exit_code == 0
    text = env_path.read_text(encoding="utf-8")
    assert "DEEPSEEK_API_KEY=sk-test" in text
    assert "DEEPSEEK_BASE_URL=https://api.deepseek.com" in text
