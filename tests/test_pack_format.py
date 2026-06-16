from context_saver.codex_pack import build_context_pack
from context_saver.config import load_settings
from context_saver.router import choose_model


def test_context_pack_fixed_headings_and_no_web_search():
    decision = choose_model("ordinary bug", settings=load_settings())
    pack = build_context_pack("ordinary bug", decision)
    for heading in [
        "Codex Context Pack",
        "Task",
        "Model And Budget",
        "Verified Context",
        "Recommended Implementation",
        "Files To Inspect",
        "Files To Avoid",
        "Constraints For Codex",
        "Minimal Verification",
        "Prompt To Paste Into Codex",
    ]:
        assert heading in pack
    assert "Do not use web search." in pack
