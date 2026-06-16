import zipfile

from context_saver.codex_pack import build_review_pack
from context_saver.config import load_settings
from context_saver.models import ModelChoice
from context_saver.review import review_input
from context_saver.router import choose_model


def test_review_pack_contains_evidence_and_checked_scope(tmp_path):
    decision = choose_model("review", careful=True, settings=load_settings())
    pack = build_review_pack(tmp_path / "a.txt", decision, "goal", "checked", "content", evidence=["a.txt:1"])
    assert "Evidence" in pack
    assert "Checked Scope" in pack


def test_careful_and_no_compress_do_not_use_flash():
    assert choose_model("review", careful=True, settings=load_settings()).model_choice == ModelChoice.PRO
    assert choose_model("review", no_compress=True, settings=load_settings()).model_choice == ModelChoice.PRO


def test_review_zip_scope(tmp_path):
    archive = tmp_path / "sample.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("README.md", "hello")
        zf.writestr("node_modules/x.js", "ignored")
    scope, content, evidence = review_input(archive)
    assert "Fully or partially read" in scope
    assert "Skipped" in scope
    assert evidence
