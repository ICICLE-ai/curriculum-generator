import pytest

from digitalagedu.core.config import ExecutionModel
from digitalagedu.core.llm.ai_setup import llm_kwargs, nrp_api_key
from digitalagedu.core.llm.sandbox import run_in_sandbox


def _execution(**overrides):
    return ExecutionModel(device="cpu", batch_size=1, image_size=64, **overrides)


def test_llm_models_default_per_role_and_override_one_role():
    assert _execution().llm_models.model_dump() == {
        "planner": "deepseek-v4-flash", "coder": "glm-5", "arbiter": "deepseek-v4-flash", "slides": "qwen3-small",
    }
    models = _execution(llm_models={"coder": "kimi"}).llm_models
    assert (models.coder, models.planner, models.slides) == ("kimi", "deepseek-v4-flash", "qwen3-small")


def test_llm_kwargs_sets_reasoning_per_model_and_one_cache_salt():
    slides, coder = llm_kwargs("qwen3-small")["extra_body"], llm_kwargs("glm-5")["extra_body"]
    assert slides["chat_template_kwargs"] == {"enable_thinking": False}
    assert coder["chat_template_kwargs"] == {"reasoning_effort": "high"}
    assert llm_kwargs("unknown-model")["extra_body"]["chat_template_kwargs"] == {}
    assert slides["cache_salt"] == coder["cache_salt"]


def test_sandboxed_code_cannot_see_credentials(monkeypatch):
    monkeypatch.setenv("NRP_LLM_API", "secret-key")
    monkeypatch.setenv("TAPIS_REFRESH_TOKEN", "secret-token")
    test = "import os\ndef test_env():\n    assert 'NRP_LLM_API' not in os.environ and 'TAPIS_REFRESH_TOKEN' not in os.environ\n"
    ok, log = run_in_sandbox("x = 1\n", test, module_id="m")
    assert ok, log


def test_nrp_api_key_from_env_else_clear_error(monkeypatch):
    monkeypatch.setenv("NRP_LLM_API", " from-env\n")
    assert nrp_api_key() == "from-env"
    monkeypatch.delenv("NRP_LLM_API")
    with pytest.raises(RuntimeError, match="NRP_LLM_API"):
        nrp_api_key()
