from context_saver.config import load_settings
from context_saver.models import ModelChoice
from context_saver.router import choose_model


def test_ordinary_routes_flash():
    assert choose_model("simple error lookup", settings=load_settings()).model_choice == ModelChoice.FLASH


def test_high_risk_routes_pro():
    assert choose_model("production database migration", settings=load_settings()).model_choice == ModelChoice.PRO


def test_forced_flash():
    assert choose_model("production database migration", mode="flash", settings=load_settings()).model_choice == ModelChoice.FLASH


def test_forced_pro():
    assert choose_model("simple task", mode="pro", settings=load_settings()).model_choice == ModelChoice.PRO


def test_careful_forces_pro():
    assert choose_model("simple task", careful=True, settings=load_settings()).model_choice == ModelChoice.PRO


def test_chinese_careful_terms_force_pro():
    for text in ["认真读", "复查", "不要漏", "认真读压缩包"]:
        assert choose_model(text, settings=load_settings()).model_choice == ModelChoice.PRO
